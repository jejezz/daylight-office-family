# 진행 기록

## 2026-11-17 — M0 기반 (완료)
**한 일**
- 저장소 구조 확정: `patches/`, `overlay/`, `tools/`, `tests/`, `docs/`, `upstream/`(해시 목록). 업스트림 소스·트리·빌드 결과는 `external/`, `build/` 에 두고 git 제외.
- 업스트림 고정(`upstream.txt`): ONLYOFFICE Desktop Editors **10.0.0.169**, 공식 설치 파일 SHA-256 기록, 설치 폴더 4,185 파일의 파일별 SHA-256(`upstream/10.0.0.169.sha256`).
- `tools/prepare-upstream.ps1`: 설치된 공식 폴더를 `external/upstream-<버전>` 으로 복사하고 해시 검증(기본은 핵심 7개, `-Full` 이면 전체 — 전체는 약 150 초).
- `tools/build.ps1`: 업스트림 트리 → `build/app`(복사 → `patches/**/*.patch` 적용 → `overlay/` 덮어쓰기 → `tools/brand/apply.ps1`(M1) → `BUILD-INFO.txt`). 약 10 초. 업스트림 트리는 건드리지 않음을 확인.
- 첫 패치 `0001`(숨길 요소 목록) 적용, 화면에서 "그리기" 탭이 없음을 확인.
- `tests/smoke.ps1`: 빌드 산출물·패치 표식, 실행 → 문서 제목(`hello.docx - ONLYOFFICE`), 시작 시간, 프로세스, UI 로딩 안정, 스크린샷 → **11개 항목 모두 통과**(창이 약 2 초에 뜸).
- 시험 도구 `tests/lib/ui.ps1`(창 찾기·캡처·키 입력·아이콘 읽기), `tests/make-testdoc.py`(`tests/data/hello.docx`), `tools/win/replace-exe-icon.ps1`(PE 아이콘 그룹 교체, M1용).
- 폴더 이름을 `onlyoffice-analysis` → `daylight-office-family` 로 바꾸고 조사 문서를 `docs/` 로 옮김(`INVESTIGATION.md`, `PLAN.md`). 이전 수동 시험 사본은 `external/legacy-test-install`(지워도 됨).

**알아 둘 것**
- 업스트림 설치 파일 주소는 "항상 최신"이라 나중에는 다른 버전을 준다. 고정 버전의 설치 파일은 **각자 보관**해야 한다(sha256 으로 확인). 다른 PC 에서는 고정 설치 파일을 설치한 뒤 `prepare-upstream.ps1` 을 돌린다.
- `git apply --directory` 로 패치를 적용하므로 git 이 필요하다(저장소 안·밖 모두 시험함).
- ps1 은 ASCII 로만 쓴다(Windows PowerShell 5.1).
- 시험이 앱을 직접 띄우고 키·마우스를 쓰는 경우(다음 단계의 입력기 시험)는 실행 중 손대지 말 것.

**다음(M1 정체성·고지)**
- `tools/brand/apply.ps1`: 표시 문자열만 이름 치환(설정 저장 위치는 바꾸지 않기), 로고 8종+2배율, 창·exe 아이콘, 연결 아이콘 73개, About 고지, 업데이트·AI·클라우드 진입점 차단, 외부 통신 점검.
- 이전 수동 시험의 스크립트 조각(Qt 리소스 PNG·압축 ico 교체)을 `tools/brand/` 로 정식화.
- 결정 대기: 아이콘 교체 범위, 앱 표시 이름(10자 이내), HWP 대응.
