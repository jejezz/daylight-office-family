# 다른 PC 에서 이어 하기 (2026-11-18 기준)

이 문서는 작업을 다른 PC 로 옮겨 이어 할 때의 순서다. 무엇을 했는지는 `PROGRESS.md`, 빌드·시험 명령은 `CLAUDE.md`.

## 1. 지금 PC 에서 마무리

- 변경을 commit 하고 push 한다(다른 PC 는 GitHub 의 `main` 을 받는다).
  - 이번 변경: `patches/sdkjs/0004-frozen-pane-origin.patch`(틀 고정 저장 오류), `tools/engine/build-sdk.ps1`(cell 엔진 빌드·`sdk-all.bin` 삭제), `tests/frozen-pane.ps1`, `tests/make-frozen-xlsx.py`, 문서.
- **업무 파일은 저장소에 넣지 않는다**: `macro_enabled_spreadsheet1.xlsm`(VBA 가 든 실제 업무 문서)은 저장소 루트에 있지만 `.gitignore` 로 제외했다(루트의 `*.xls*`). 다른 PC 에서 시험하려면 USB·클라우드 등으로 **따로** 옮긴다.
- `../daylight-office-engine` 폴더는 **옮기지 않는다.** 엔진 작업용 worktree 를 정리하고 남은 껍데기다(`.git` 없음, 1 MB). 들어 있는 것은 모두 `main` 에 합쳐졌고(`engine-sdk` 브랜치는 `main` 에 병합됨), `main` 쪽이 더 새롭다. 지워도 된다.
- `build/`, `dist/`, `external/` 은 옮기지 않는다(각 PC 에서 다시 만든다).

## 2. 새 PC 준비 (한 번)

필요한 것: Windows 10/11 x64, git, Python 3.12 이상(PATH), Windows PowerShell 5.1(기본 내장). 확인용으로 Excel 이 있으면 좋다.

1. 저장소 받기
   ```
   git clone https://github.com/jejezz/daylight-office-family.git
   ```
2. **준비 스크립트 한 번** (저장소 루트에서)
   ```
   powershell -ExecutionPolicy Bypass -File tools\bootstrap.ps1
   ```
   git·Python·Pillow/numpy 를 확인하고(없는 파이썬 패키지는 pip 로 설치), 공식 설치 파일(10.0.0.169, `upstream.txt`)을 내려받아 크기·SHA-256·서명을 확인한 뒤 `external\` 안에 조용히 설치 → `external\upstream-10.0.0.169` 로 복사(`prepare-upstream.ps1`) → 임시 설치 제거, 그리고 `external\sdkjs`(태그 v10.0.0.169)를 얕게 복제한다. 이미 된 단계는 건너뛰므로 다시 돌려도 된다. 이 PC 에 같은 버전이 `C:\Program Files\ONLYOFFICE\DesktopEditors` 로 설치돼 있으면 내려받지 않고 그것을 복사한다(`-IgnoreInstalled` 로 끔).
   - 다운로드 주소는 "항상 최신"이라 다른 버전이 오면 해시 불일치로 멈춘다. 그때는 보관해 둔 설치 파일로 `-Installer <경로>`.
   - `-CheckOnly`: 아무것도 바꾸지 않고 빠진 것만 보고. `-WithInstaller`: Inno Setup 6.7.4 를 `external\innosetup\` 에(설치 파일 만들 때만). `-Build`: 끝나고 `build.ps1` 까지. `-FullVerify`: 업스트림 전체 해시 검사(약 150 초, `unins000.dat` 하나만 달라도 정상).
   - 수동으로 하려면: 공식 설치 파일 설치 → `tools\prepare-upstream.ps1` → `git clone --depth 1 --branch v10.0.0.169 -c core.autocrlf=false https://github.com/ONLYOFFICE/sdkjs external/sdkjs`. 화면 코드 읽기용 `web-apps` 등은 선택(빌드는 쓰지 않음).
3. 선택: 개발 PC 기본값(UI 언어 등)
   ```
   powershell -ExecutionPolicy Bypass -File tools\dev\set-user-defaults.ps1
   ```
4. 빌드
   ```
   powershell -ExecutionPolicy Bypass -File tools\build.ps1
   ```
   `engine: ... -> word` 와 `-> cell` 두 줄, `OK: build\app ready` 가 나오면 된다.

## 3. 시험 전에 꼭 지킬 것

- **다른 Daylight 를 모두 닫는다**(설치본 포함). 설치된 Daylight 가 떠 있으면 `build\app` 으로 연 문서가 그 창으로 넘어가서, 시험이 엉뚱한 앱을 조작한다.
- 화면 시험(`tests\*.ps1` 중 키·마우스를 쓰는 것)은 도는 동안 **아무것도 건드리지 않는다.** 이 시험들은 Windows 전체에 키를 보낸다(SendKeys). 앱 창이 앞에 없으면 그 키가 다른 창이나 **바탕 화면**으로 간다 — 바탕 화면에서는 글자로 아이콘이 선택되고 Enter 로 실행된다(2026-11-18 에 `shutdown_…` 배치 파일이 실행된 원인).
- **시험을 중간에 멈췄으면 남은 시험 프로세스를 꼭 끈다.** 도구에서 명령을 중단해도 그 명령이 띄운 PowerShell 시험은 계속 돌았다. PowerShell 창에서:
  ```
  Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -match 'tests' } | Select-Object ProcessId, CommandLine
  ```
  나오는 것을 `Stop-Process -Id <번호> -Force` 로 끈다.
- Claude 에게 맡길 때: 화면을 조작하는 시험은 사람이 직접 돌리기로 했다(아래 4절의 자동화 개선 전까지).

## 4. 이어서 확인할 것 (아직 안 끝남)

1. **틀 고정 저장 시험**(직접 실행, 손대지 말 것)
   ```
   powershell -ExecutionPolicy Bypass -File tests\frozen-pane.ps1
   ```
   기대: 모든 항목 PASS. 마지막 실행 결과는 통과였지만 한 번 입력이 빠져 4개 실패한 적이 있다(키 입력 방식이 불안정 — 5절).
2. **실제 업무 파일로 Excel 확인**: 업무 xlsx 사본을 `build\real-check.xlsx` 로 두고
   ```
   build\app\DesktopEditors.exe build\real-check.xlsx
   ```
   빈 셀에 입력 → Ctrl+S → 앱 닫기 → Excel 로 열기. 확인: "내용에 문제가 있습니다"(복구) 경고가 **없어야** 한다(전에는 틀 고정 때문에 나왔다). xlsm 저장은 지원하지 않으므로 매크로 문서는 시험 대상이 아니다.
3. **회귀 확인**: `sdk-all.bin`(엔진 V8 스냅숏) 삭제로 **docx 저장도 이제 고친 Word 엔진(JS)을 쓴다.** 문서 저장이 그대로 되는지 본다.
   ```
   powershell -ExecutionPolicy Bypass -File tests\smoke.ps1
   powershell -ExecutionPolicy Bypass -File tests\engine.ps1
   ```
   그리고 docx 하나를 열어 고치고 Ctrl+S → Word 로 열어 경고가 없는지.
4. 선택(대조 시험): `external\upstream-10.0.0.169\editors\sdkjs\cell\sdk-all.bin` 을 `build\app\editors\sdkjs\cell\` 에 다시 넣고 1번을 돌리면 틀 고정 검사가 **실패해야** 한다(시험이 이 오류를 잡는지 확인). 끝나면 그 파일을 지운다. 주의: `tests\frozen-pane.ps1` 은 시작할 때 `build\frozen-test` 를 지우므로 백업을 거기에 두지 않는다.

## 5. 다음 할 일

- `tests\frozen-pane.ps1` 를 **키보드·마우스 없이** 바꾼다: 셀 입력과 저장은 DevTools 연결(`tests\lib\cdp.py`, 포트 9333)로 엔진 API 를 직접 부르고, 저장 대화상자는 UI Automation 으로 그 창만 찾아 값을 넣는다. 다른 화면 시험(`smoke`, `theme`, `icons`, `hanja` 등)도 같은 위험이 있으니 순서대로 점검.
- 저장 때 빠지는 부분(ONLYOFFICE 일반): 프린터 설정, `calcChain.xml`, `featurePropertyBag.xml`(Excel 의 셀 안 체크박스). 가족 문서에서 문제가 되는지 지켜본다.

## 6. 알아 둘 것 (이번에 새로 안 것)

- **`editors\sdkjs\<제품>\sdk-all.bin` 은 업스트림 엔진의 V8 스냅숏**이다. 저장할 때 변환기(x2t 의 doctrenderer)가 `sdk-all.js` 대신 이것을 읽는다. 그래서 엔진 패치는 화면에는 보여도 **저장에는 반영되지 않았다.** `build-sdk.ps1` 이 다시 빌드한 제품(word, cell)의 `.bin` 을 지운다(저장 속도 차이 없음: 28개 시트 파일 2.6 초 vs 2.8 초).
- 엔진 패치가 건드리는 최상위 폴더(`word`/`cell`/`slide`, `common` 이면 전부)만 빌드한다.
- xlsm 저장은 지원하지 않기로 했다(`PROGRESS.md` 2026-11-19). VBA 는 열 때 보존만 될 뿐 이 앱에서 실행되지 않는다(ONLYOFFICE 는 JavaScript 매크로만 지원).
