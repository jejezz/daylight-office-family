# 진행 기록

## 2026-11-17 — M1 정체성·고지 (완료, 임시 이름 "Daylight")
**한 일** (`tools/brand/` + `tools/build.ps1`, 전체 빌드 약 30 초)
- 이름·설정: 바이너리의 `ONLYOFFICE` 를 **통째 문자열 단위**로만 바꾼다(앞뒤가 NUL 인 문자열, 규칙마다 일치 개수를 검사 — 업스트림이 바뀌어 어긋나면 빌드가 실패한다). 조직 이름 문자열 하나가 **창 제목 접미사와 설정 키(`HKCU\Software\<이름>`)를 동시에** 정하므로 설정이 원본 ONLYOFFICE 와 분리된다. 사용자 데이터 폴더(`%LOCALAPPDATA%\<dataDir>\DesktopEditors`), 파일 연결 등록 경로, 버전 정보(ProductName/FileDescription)도 같은 방식. 원본 ONLYOFFICE 의 데이터는 건드리지 않음(시험으로 확인).
- 로고·아이콘: 탭 바 로고 PNG 8종(바이트 오프셋 표 `offsets.json`), 창·작업 표시줄 아이콘(zlib 압축 Qt 리소스 `:/app.ico`, 자동 탐지), 실행 파일 아이콘(PE 그룹 101), **파일 형식 연결 아이콘 72개**(그룹 102~173, 문서 파랑·표 초록·슬라이드 주황·PDF 빨강·기타 회색 + 확장자 글자, 대응표 `filetypes.json`). 모두 임시 그림이며 `assets/brand/` 에 같은 이름 파일을 두면 덮어쓴다.
- 정보(About) 화면: 이름·로고 교체, **수정본 고지 한 줄 추가**(원 개발자 표시 "© Ascensio System SIA"·AGPL 링크는 그대로). 편집기 쪽 About 은 데스크톱에서 숨겨져 있어 쓰이지 않음.
- 진입점 정리: 시작 화면 왼쪽 레일에서 AI Chat·AI Tools·Clouds·Templates 숨김(`index.html` 압축 코드의 고정 위치 문자열 치환), About 의 업데이트 줄 숨김(CSS 주입), 시작 문구의 제품 이름 교체(영어·한국어).
- 외부 통신 차단: 업데이트 서버 주소(`appcast*.json`)·온라인 템플릿·온라인 도움말 주소를 `127.0.0.1:9`/`about:blank` 로 바꾸고 `updatesvc.exe`, 인터넷이 필요한 플러그인 4개(AI Tools, YouTube, Translator, Plugin Manager)를 제거.
- 시험: `tests/brand.ps1`(17개 항목: 아이콘들, 설정·데이터 위치 분리, 정적 문자열, 정보 화면 스크린샷), `tests/smoke.ps1`(11개), `tests/network-audit.ps1`, `tests/icons-sheet.ps1`(아이콘 73개 한눈에 보기). **모두 통과.**
- 빌드 안전장치: `build\app.new` 에서 만들고 성공했을 때만 `build\app` 으로 교체(실패해도 반쯤 지워진 트리를 남기지 않음). 셸의 현재 폴더가 `build\app` 안이면 삭제가 막히므로 항상 저장소 루트에서 실행할 것.

**외부 통신 점검 결과** (`tests/network-audit.ps1`, 문서를 연 채 50~60 초 관찰)
- 처음: ONLYOFFICE 계열 서버(`templates/download.onlyoffice.com` 이 가리키는 CDN 주소)로 연결 1개 — 시작 화면만 띄우면 없고 **문서를 열 때 편집기가 온라인 도움말을 미리 불러오는 것**이 원인이었다(주소를 바꾸자 사라짐).
- 지금: `8.8.4.4:443`(구글 DNS) 하나만 남음 — 내장 크로미움이 PC 의 DNS 공급자로 하는 암호화 DNS(DoH) 조회로 추정. 앱이 접속하는 서버가 아니다. 끄려면 크로미움 기능 플래그를 바꿔야 해서 미처리.
- 한계: 1 초 간격 관찰이라 아주 짧은 연결, UDP·DNS 조회 내용은 못 본다. 사용자가 도움말·링크를 누르면 브라우저로 vendor 사이트가 열린다(의도된 동작, M4 에서 정리).

**알게 된 것**
- 앱이 저장하는 설정 키 목록이 실행 파일 안에 있다: `locale`, `uiscaling`, `usegpu`, `useai`, `autoupdatemode`, `docopenmode`, `editorwindowmode`, `spellcheckdetect`, `macrosDisabled`, `pluginsDisabled`, `username` 등. 명령줄에는 `--keeplang=ko`(언어 고정), `--lang=ko`(이번 실행만), `--lock-portals`(클라우드 연결 버튼 숨김), `--updates-*` 가 있다. → 가족용 기본값(한국어 등)은 설치 프로그램(M6)이 레지스트리에 써 주면 된다. 개발 PC 에서는 `tools/dev/set-user-defaults.ps1`.
- **HWP/HWPX 지원이 있다**: 파일 연결에 `.hwp`·`.hwpx` 가 등록돼 있고 변환기 폴더에 `HWPFile.dll` 이 있다. 이전의 "지원하지 않을 것"이라는 가정은 틀렸다. 실제 문서의 표시·편집 품질은 샘플 파일로 시험해야 한다(미시험).
- 설정은 값이 바뀔 때만 `DesktopEditors` 하위 키에 쓰이고, 시작할 때마다 `Updates` 그룹이 쓰인다. 시험이 앱을 강제 종료하면 설정이 저장되지 않으므로 `Close-App`(정상 종료)을 쓴다.

**남은 것 / 다음**
- 임시 항목: 이름 "Daylight"(정식 이름은 `brand.json` 한 곳), 로고·아이콘 그림, 설치 프로그램·바로가기의 이름(M6), 파일 형식 설명 문자열(길이가 앞에 붙는 리소스라 다른 방식이 필요 — 보류), 2배율 로고(위치 미확인).
- 서명이 깨짐(바이너리 수정): 다른 PC 에서 SmartScreen 경고 가능(미확인) → M6.
- 이전 수동 시험이 `%LOCALAPPDATA%\DAYLIGHTOF` 폴더를 만들어 둠(지워도 됨).
- 다음 **M2 외형**(테마·글꼴·치수). 결정 대기: 아이콘 교체 범위, 앱 표시 이름, HWP 시험용 샘플 파일.

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
