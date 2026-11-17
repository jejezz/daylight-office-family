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
tools\build.ps1                   # external 의 업스트림 + patches + overlay → build\app
tests\smoke.ps1                   # build\app 을 실행해 문서를 열고 창 제목·프로세스·스크린샷 확인
```

## 사용자 배경
C/C++/Java 고급, Python/JavaScript 초급. 이 프로젝트의 UI 코드는 JavaScript(ONLYOFFICE web-apps), 네이티브 껍데기는 C++/Qt 다. 코드는 이유를 짧게 설명한다.
