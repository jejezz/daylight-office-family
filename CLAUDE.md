# CLAUDE.md — daylight-office-family

## 목표
가족·친지(비상업)가 Word/Excel/PowerPoint 대신 쓸 오피스. **ONLYOFFICE Desktop Editors(공식 설치본, 버전 고정)를 기반으로 UX/UI·이름·아이콘을 바꿔 배포**한다. 기능은 거의 전부 지원해야 한다.
이전 시도(Avalonia + LibreOfficeKit 직접 구현)는 `../OFFICE` 에 보관한다(삭제하지 않음). 이 저장소로는 옮기지 않는다.

## 확정된 결정
- 방식: **오버레이**. 저장소에는 업스트림 소스·바이너리를 넣지 않고 `patches/`, `overlay/`, `tools/`, `tests/`, `docs/` 만 둔다. `tools/build.ps1` 이 고정된 업스트림 설치 트리에 패치·덮어쓰기를 적용해 `build/app/` 을 만든다.
- 구조: **단일 앱 + 문서 탭**(Writer/Calc/Impress 3개 exe 분리는 폐기).
- 이용감: 메뉴 구성, 일반 용어, 표준 단축키 유지. 시각 스타일·정보 구조는 `../OFFICE/docs/UX-DESIGN.md` 를 사양으로 삼아 ONLYOFFICE 구조로 옮긴다(`docs/PLAN.md`).
- 이름·로고·아이콘: 독자 제작. **ONLYOFFICE 를 제품명·주 식별자로 쓰지 않는다**(상표). 저장소 이름·도메인에도 쓰지 않는다. 설명할 때만 "ONLYOFFICE 기반"이라고 쓴다.
- 라이선스: 코드 AGPLv3 + 추가 조건(고지 유지, 수정 표시, 정보 화면에 원 개발자 표시, 상표 권리 없음). 아이콘·삽화는 CC BY-SA 4.0. **정보(About) 화면의 원 개발자 표시와 수정본 고지는 지우거나 숨기지 않는다.** 자세한 것은 `docs/INVESTIGATION.md` 1절.
- 업스트림 버전은 `upstream.txt` 에 고정한다. 자동 업데이트는 막는다(수정이 덮어써짐). 올릴 때는 패치 충돌을 확인하고 `docs/PROGRESS.md` 에 기록한다.

## 작업 규칙
- 작업 시작 전 `git pull`, 끝나면 `docs/PROGRESS.md` 갱신 후 commit/push. (commit/push 는 사용자가 요청할 때)
- `external/`(업스트림 트리·소스), `build/`, `dist/` 는 git 에 넣지 않는다. 각 PC에서 `tools/` 로 재현한다.
- 패치 하나 = 설명 + 시험 하나. 패치는 `git diff` 형식, 경로는 업스트림 설치 트리 기준(`-p1`). `.patch` 는 줄바꿈 변환 금지(`.gitattributes`).
- 쉘 스크립트 LF, ps1/bat CRLF(`.gitattributes`). ps1 은 Windows PowerShell 5.1 에서 도니까 **ASCII 로만** 쓴다(한글 주석 금지, BOM 없는 UTF-8 은 깨짐).
- UI 시험 중에는 앱 창을 직접 건드리지 않는다(자동 입력과 겹침).

## 빌드·시험
```
tools\prepare-upstream.ps1        # 한 번: 공식 설치본의 설치 폴더를 external/ 에 복사하고 해시 검증
tools\build.ps1                   # external 의 업스트림 + patches + overlay + 브랜드 단계 → build\app (약 30 초)
tests\smoke.ps1                   # build\app 을 실행해 문서를 열고 창 제목·프로세스·스크린샷 확인
tests\brand.ps1                   # 아이콘·설정/데이터 위치 분리·정적 문자열 확인, 시작/정보 화면 스크린샷
tests\icons.ps1                   # 교체된 스프라이트 칸 328개 정적 검사 + 홈 탭 아이콘을 기대 글리프와 화면 비교
tests\theme.ps1                   # 밝게/어둡게 팔레트 색을 실제 화면 픽셀로 확인(사용자 상태를 초기화함, 영어 UI·기본 창 크기 전제)
tests\network-audit.ps1           # 앱이 여는 외부 TCP 연결 관찰(-NoDoc 이면 시작 화면만)
tests\icons-sheet.ps1             # 파일 형식 아이콘 73개를 한 장으로(눈으로 확인)
tools\dev\set-user-defaults.ps1   # 개발 PC 용: UI 언어 등 기본값을 레지스트리에(설치 프로그램이 나중에 대신함)
```
- 이름·아이콘·정리 목록은 `tools/brand/brand.json` 과 `assets/brand/`(덮어쓸 그림) 한 곳에서 정한다. 바이너리 문자열 규칙은 일치 개수를 검사하므로 업스트림 버전을 올리면 일부러 실패한다(`offsets.json`, `filetypes.json` 도 다시 뽑는다).
- 색·글꼴·모서리는 `tools/theme/palette.json` 한 곳(Saturn 팔레트). 기본 테마 두 개(`theme-night`/`theme-white`)에 덮어쓰며, 새 테마를 등록하지 않는다(데스크톱 앱이 설치 폴더의 테마 파일을 읽지 않기 때문). UI 시험은 View 탭 밑줄을 확인한 뒤에만 클릭한다(`Click-Tab`) — 아무 데나 클릭하면 시험 문서가 바뀐다.
- 툴바 아이콘은 Phosphor Duotone(MIT)을 모던 테마용 스프라이트 시트에 칠해 넣는다(`tools/icons`): 대응표 `mapping.json`(ONLYOFFICE 클래스 이름→Phosphor 이름)에 넣은 것만 바뀐다. **대응표에 새로 넣을 때는 화면으로 의미를 확인**한다(같은 모양이 두 기능에 겹치거나 뜻이 다르면 뺀다 — 예: goback, function). Phosphor SVG 원본은 저장소 안 `assets/phosphor-duotone/`(MIT, 이전 프로젝트에서 복사한 80개; 2단계에서 전체로 확대).
- **빌드·시험은 항상 저장소 루트에서 실행**한다. 셸의 현재 폴더가 `build\app` 안이면 교체가 막힌다. 빌드는 `build\app.new` 에서 만들어 성공 시에만 교체한다.

## 사용자 배경
C/C++/Java 고급, Python/JavaScript 초급. 이 프로젝트의 UI 코드는 JavaScript(ONLYOFFICE web-apps), 네이티브 껍데기는 C++/Qt 다. 코드는 이유를 짧게 설명한다.
