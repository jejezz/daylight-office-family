# ONLYOFFICE Desktop Editors 조사 (2026-11-17)

> **폴더 안내(2026-11-17)**: 이 문서는 `onlyoffice-analysis` 시절의 조사 기록이다. 본문의 경로는 다음처럼 바뀌었다 — `src/web-apps`·`src/sdkjs` → `external/web-apps`·`external/sdkjs`, `test-install/` → `external/legacy-test-install/`(수동 시험 사본, 지워도 됨), `shots/` → `docs/shots/`. 개발 계획은 `PLAN.md`, 이후 진행은 `PROGRESS.md`.

목적: "쓸 수 있는 오피스 + 가족이 불편한 부분을 고칠 수 있는가"를 ONLYOFFICE 로 만족하는지 본다.
출처는 공식 블로그·문서와 검색 결과이며, 아래에서 **확인함 / 미확인** 을 구분했다.

## 지금까지 알게 된 것
- 설치: `DesktopEditors_x64.exe` 약 286 MB, 서명 유효(Ascensio System SIA), `C:\Program Files\ONLYOFFICE\DesktopEditors` 에 설치함.
- 속도: 사용자가 직접 써 보고 만족(수치 측정은 하지 않음).

## 1. 라이선스·상표 (확인함: 공식 블로그 요약 / 미확인: 라이선스·상표 정책 원문)
- 코드는 AGPLv3, 아이콘·삽화·문서는 CC BY-SA 4.0.
- 추가 조건: 저작권·라이선스 고지 유지, 수정본임을 표시(수정일 포함), ONLYOFFICE(Ascensio System SIA) 기반임을 UI 에서 밝히고 라이선스 정보 링크 제공.
- 상표: 수정하면 **자기만의 브랜드 이름**을 써야 한다. ONLYOFFICE 를 제품명으로 쓰거나 로고·시각 정체성을 비슷하게 흉내 내면 안 된다. "ONLYOFFICE is a trademark of Ascensio System SIA." 문구를 눈에 띄는 곳에 둔다. "based on ONLYOFFICE" 같은 설명은 허용.
- 로고 유지 요구는 FSF 와 ONLYOFFICE 사이에 분쟁 중(Euro-Office 포크 사건). 판결 없음. **→ 아래 원문 확인에서 정정: 받은 v10.0.0.169 의 LICENSE 에는 로고 유지 조항이 없다.**

### 원문 확인 (2026-11-17, 법률 자문 아님)
근거: `src/web-apps/LICENSE`, `src/sdkjs/LICENSE`(둘이 동일, 728 줄) — AGPLv3 전문 + "Additional Terms" 5개. 소스 파일 머리말도 같은 취지.
1. 모든 고지 유지: 저작권·라이선스·보증 면책·출처 표시(AGPL 4·5·7(b)).
2. **수정본은 수정했다는 사실과 수정 날짜를 눈에 띄게 표시**하고, **ONLYOFFICE(Ascensio System SIA)의 원본에 기반함**을 분명히 해야 한다.
3. 대화형 UI 가 있으면 눈에 띄는 UI 기능(예: 정보 창)으로 (i) ONLYOFFICE 가 원 개발자임, (ii) 수정본일 수 있음, (iii) 라이선스 정보 접근을 보여 줘야 한다. → **정보(About)·법적 고지 화면은 지우거나 숨기면 안 된다.**
4. 상표·로고·브랜드에 대한 권리는 주지 않는다. 사용은 상표 정책(onlyoffice.com/trademark-policy)을 따른다. **정책 페이지 본문은 가져오지 못했다**(내비게이션만 반환). 아래 상표 항목은 2026-05 블로그 요약에 근거.
5. 일러스트·**아이콘 세트**·기술 문서는 CC BY-SA 4.0(코드는 AGPLv3 그대로). 그 아이콘을 가져다 고치면 같은 조건으로 공개해야 한다. 이 프로젝트 규칙(아이콘은 직접 제작)과 일치하면 문제없음.

**이 프로젝트에 대입한 결론**
- **코드 수정 자체는 허용**된다(AGPL). 시험한 "그리기 탭 숨김"처럼 `_licensed` 검사 근처를 고치는 것도 추가 조건 어디에도 금지돼 있지 않다. 단 3번 때문에 정보 창은 건드리지 말 것.
- **본인만 쓰는 경우**: 배포가 아니므로 소스 제공 의무는 생기지 않는다.
- **가족에게 설치본을 주는 경우(= 복제본 전달)**: AGPL 의 배포에 해당할 가능성이 높다. 받는 사람에게 대응 소스를 제공해야 한다 → 수정 패치와 기반 버전 태그(`v10.0.0.169`)를 담은 GitHub 저장소를 알려 주면 실무상 충족될 것으로 보인다(확정 아님). 위 2·3번의 표시도 필요.
- **이름·상표**: ONLYOFFICE 를 제품명·주 식별자로 쓰면 안 되고, 로고·시각 정체성을 비슷하게 흉내 내도 안 된다. "ONLYOFFICE 기반"이라는 설명과 "ONLYOFFICE is a trademark of Ascensio System SIA." 문구는 눈에 띄는 곳에 둬야 한다. 블로그는 비공개·비상업 배포를 따로 다루지 않는다 → 면제 근거 없음.
- **실무 걸림돌(미검증)**: 창 제목 표시줄의 로고·앱 이름·설치 프로그램·exe 아이콘은 네이티브 셸(C++/Qt) 쪽일 가능성이 높아서, 이름을 바꾸려면 데스크톱 셸 빌드나 리소스 수정이 필요할 수 있다. JS 수정만으로는 안 될 수 있다.
- **확정되지 않은 것**: 상표 정책 원문, 가족 배포 시 상표 쪽 위험의 실제 크기. 확실히 하려면 info@onlyoffice.com 에 문의(보내는 것은 사용자가 직접).
- 가족·친지에게 수정본을 나눠 주는 것이 "배포"인지 문서에 없다(모호). 배포로 보면 AGPL 에 따라 수정한 소스를 받는 사람에게 제공해야 한다.
- 유료 화이트라벨은 Docs Developer(서버) 옵션으로만 언급되고 Desktop Editors 용은 언급 없음.

## 2. 빌드 없이 바꾸는 변경: 플러그인 (확인함: 공식 문서)
- 플러그인 = HTML/CSS/JS 웹앱. Desktop Editors 에서 동작.
- 할 수 있는 것: 자기 툴바 탭·버튼 추가, 기본 탭(home, ins, layout 등)에 버튼 추가, 문맥 메뉴 항목 추가, 문서를 Office JavaScript API 로 읽고 수정(10.0+ 는 `Editor.RunMacro` 등).
- 문서에서 확인되지 않은 것(= 없다고 확정된 것은 아님): **기본 리본 항목 숨기기·순서 바꾸기·제거**, 기본 설정 변경. 문서는 "추가"만 설명한다.
- 제한: 플러그인은 편집기 내부 DOM·파일 시스템에 접근 불가.
- 설치(Windows): 플러그인 관리자에서 `.plugin`(zip 이름 바꾼 것) 설치, 또는 `%UserProfile%\AppData\Local\ONLYOFFICE\DesktopEditors\data\sdkjs-plugins\{GUID}` 폴더에 복사. 기본 플러그인은 폴더 삭제로 제거 가능하나 업데이트 시 복원됨.

## 3. 소스 빌드 (확인함: README / 미확인: Windows 절차)
- 저장소: `desktop-apps`(OS 별 네이티브 UI 셸), `web-apps`(편집기 UI), `sdkjs`(편집 로직 JS), `core`(변환 등 C++ 코어), `desktop-sdk`, `dictionaries`. 어느 저장소에 리본 UI 가 있는지는 추정(web-apps)이며 확인 필요.
- 공식 README 의 빌드 안내는 **Linux 전용**: `build_tools/tools/linux` 에서 `python3 ./automate.py desktop`. 검증 환경 Ubuntu 24.04, 4코어, RAM 8 GB, SSD 100 GB. 빌드 시간은 문서에 없음.
- Windows: 공식 절차를 못 찾음. 포럼 사례는 VS 2019 + Windows 10 SDK + Qt 5.15.2 MSVC2019 64bit + Python 3, `build_tools` 의 `configure.py --module desktop` 후 `make.py`. 그 사용자가 빌드한 sdkjs 에서 PDF 텍스트 편집이 안 되는 문제를 겪었다. 공식 절차인지 불명 → `build_tools/tools/` 아래 Windows 폴더를 직접 확인해야 한다.

## 4. 열린 질문 (다음에 확인할 것)
1. 설치본에서 리본/툴바 UI 가 어느 파일에 있고, 빌드 없이 수정(숨김·재배치)이 되는지. (설치 폴더는 읽기 전용으로만 볼 것)
2. 최소 플러그인 하나로 "자주 쓰는 동작을 기본 탭에 버튼 추가"가 되는지.
3. `build_tools` 의 Windows 빌드 절차와 소요 디스크·시간.
4. 라이선스·상표 정책 원문(onlyoffice.com/trademark-policy, 라이선스 파일).
5. 한글 입력(IME), 한글 글꼴, 가족이 쓰는 docx/xlsx/pptx 호환성.

## 4-1. 설치본 폴더 확인 결과 (읽기 전용, 수정하지 않음)
- 구조: `editors/{sdkjs, web-apps, sdkjs-plugins, webext}`(약 324 MB), `converter`(123 MB, C++ 변환 코어), `dictionaries`(219 MB), `plugins`(Qt 플러그인).
- 편집기 UI 는 `editors/web-apps/apps/{documenteditor,spreadsheeteditor,presentationeditor,pdfeditor,visioeditor}/main/`. 문서 편집기는 `code.js`(2.3 MB, 43,809 줄, 번들이지만 한 줄로 압축되진 않음), `index.html`, `locale/ko.json`(306 KB, **한국어 UI 이미 있음**), `resources`(css 1, svg 10, png 30).
- 즉 리본 UI 는 웹 코드라 원리적으로는 설치본 파일 수정으로도 바꿀 수 있어 보이나, 번들 결과물이라 유지보수가 어렵고 업데이트 때 덮어써진다. 실제로 고쳐 보지는 않았다(미검증).
- 기본 플러그인 10개가 `editors/sdkjs-plugins` 에 있음. 사용자 데이터는 `%LOCALAPPDATA%\ONLYOFFICE\DesktopEditors\data`.

## 4-2. SDK 조사 (공식 문서 기준, 2026-11-17)
| 종류 | 내용 | 이 프로젝트에 대한 의미 |
|---|---|---|
| Plugin API | 편집기 안 JS. 버튼·메뉴 추가, 문서 수정 | 추가형 변경에 사용 가능 |
| Document Builder | 편집기 없이 docx/xlsx/pptx/pdf 생성·수정·변환하는 SDK. Python, C++, COM, Java, **.NET(Windows 전용, `docbuilder_net`)** | 화면 렌더링 API 없음(썸네일 JPG/PNG만, 타일·쪽 지정 문서 없음). **무료판은 생성 문서에 워터마크, 제거에는 상업 라이선스 필요** → 우리 UI 의 엔진으로는 부적합 |
| Docs 편집기 설정(`customization`) | 임베드된 Document Server 용 설정. `compactToolbar`, `features` 등 | **탭·항목 숨김(`layout.*`)은 유료 Developer 의 확장 화이트라벨 라이선스 전용.** Desktop Editors 에 적용된다는 문서 없음 |
| Document Server 자체 호스팅 | Windows 용 있음. Community 는 AGPLv3 | 서버를 같이 돌려야 해서 무거움 |
| Desktop Editors | 명령줄 플래그(`--view`, `--review`, `--new:word` 등), 테마 JSON(설치 폴더 `web-apps/apps/common/main/resources/themes` 에 복사), DMS 제공자(`providers/` 폴더 + `config.json`), JS 브리지 `window.AscDesktopEditor` | UI 숨김·기본값 변경 설정은 문서에 없음. 브랜딩 문서 없음 |
| `desktop-sdk` 저장소 | "Desktop Editors 의 핵심부"(AGPL). README 에 공개 API·C#·임베딩 안내 없음 | 제3자 임베딩용 SDK 로 보이지 않음(소스는 읽지 않음) |

미확인: Document Builder 의 NuGet 패키지 유무·크기·정확한 라이선스 조건, `desktop-sdk` 소스 내용, Desktop 용 플러그인 문서의 세부.

## 4-3. 수정 시험 결과 (2026-11-17, 성공)
- 소스: `src/web-apps`, `src/sdkjs` 를 설치본과 같은 태그 `v10.0.0.169` 로 얕은 복제(각 837 MB / 178 MB, 전체 이력은 1.3 / 1.2 GB 라 피함). 설치본 사본은 `test-install/`(1.0 GB). 원본 설치 폴더는 건드리지 않음.
- 빌드: sdkjs 는 `python build.py --desktop --product word` 로 끝남(컴파일러 없이 이어붙이기, 몇 초). web-apps 는 `npm install --ignore-scripts` + `npx grunt deploy-documenteditor-component --desktop=true --force`; imagemin(이미지 최적화) 단계만 실패해 `--force` 로 넘김. 빌드한 `code.js` 를 사본에 바꿔 넣어도 앱이 정상 실행됨.
- **핵심 발견: 설치본의 UI 코드가 평문 JS 로 그대로 들어 있어 빌드 없이 파일만 고쳐도 반영된다.** 편집기 UI 는 `editors/web-apps/apps/*/main/app/{controller,view}/*.js` 와 `apps/common/main/lib/**` 의 개별 파일(예: Toolbar.js 4,331 줄)이고, 번들(`code.js`)에는 들어 있지 않다.
- 시험: 사본의 `apps/common/main/lib/controller/LayoutManager.js` 에 한 줄(`if (value === 'toolbar-draw') return false;`)을 넣고 실행 → 리본에서 "그리기" 탭이 사라짐(캡처로 확인, `shots/patched2.png`). `Toolbar.js` 의 `setVisible('draw', false)` 만 고친 첫 시도는 `common/main/lib/view/Draw.js` 가 다시 덮어써서 실패 → 숨김은 판정 함수 쪽에서 해야 한다.
- 알게 된 것: 항목 숨김 판정 `isElementVisible` 은 `_licensed` 일 때만 설정(`layout`)을 따른다. 즉 유료 화이트라벨 기능이 이 한 곳의 런타임 검사로 막혀 있는데, 소스를 직접 고치는 것은 AGPL 이 허용하는 수정이다. 다만 이름·로고 등 브랜딩 조건은 별개이며(1절), 이 방식이 라이선스상 문제없는지는 **원문 확인 전까지 미확정**.
- 남은 위험: 업데이트하면 수정이 덮어써짐(버전 고정 + 자체 배포로 대응), 항목마다 의존 코드가 있어 숨김이 다른 코드와 충돌할 수 있음(위 Draw.js 사례), 시험은 문서 편집기 한 곳·한 항목뿐.

## 4-4. 이름·아이콘 교체 시험 (2026-11-17, 사본 `test-install/` 에서만)
- 브랜드 문자열 위치: 최상위 `index.html`(977 KB, 시작 화면·셸 UI 번들, `ONLYOFFICE` 414 곳)·`addon.html`, 네이티브 `editors.exe`(UTF-16 0 곳·ASCII 35 곳), `DesktopEditors.exe`(UTF-16 44 곳), `ascdocumentscore.dll`(UTF-16 4 곳·ASCII 4 곳). exe 버전 정보의 ProductName 도 `ONLYOFFICE`.
- 방법: 같은 길이(10 글자)의 문자열로 바이트 치환(`ONLYOFFICE` → `DAYLIGHTOF`).
- 결과 1차: `editors.exe` UTF-16 과 `index.html` 만 치환 → 변화 없음(제목은 ASCII 쪽 문자열이었음).
- 결과 2차: 세 바이너리의 ASCII·UTF-16 모두 치환 → **창 제목이 `multipage.docx (Read only) - DAYLIGHTOF` 로 바뀌고 앱은 정상 동작**(`shots/renamed2.png`).
- 부작용: 설정 저장 위치가 조직/앱 이름으로 정해지는 듯, **UI 언어가 영어로, 단위가 바뀌어 설정이 초기화**됨(사용자 데이터 위치 변경으로 추정). 앞서의 "그리기 탭 숨김"(JS 수정)은 유지됨.
- 그대로인 것: **탭 바 왼쪽의 ONLYOFFICE 로고**(텍스트가 아니라 이미지로 보임, 위치 미확인), exe·작업 표시줄 아이콘(리소스), 설치 프로그램(`unins000.exe` 등, 미시험), About 화면의 이름·로고(웹 쪽 `FileMenuPanels.js` 로 보이나 미시험).
- 한계: ① 같은 길이 이내의 이름만 가능(더 길면 셸 재빌드 필요). ② 바이너리를 고치면 서명(Authenticode)이 깨져 다른 PC 에서 SmartScreen 경고가 뜰 수 있음(미확인). ③ 업데이트 때 덮어써짐. ④ 사용자 설정 이전·초기화를 감안해야 함.
- 판단: **텍스트 이름 교체는 빌드 없이 가능**. 로고·아이콘 교체는 이미지 위치를 더 찾아야 하며, 가능하더라도 정보 창의 원 개발자 표시(1절 3번)는 유지해야 한다.

### 4-4a. 로고 위치 찾기와 교체 (2026-11-17, 사본에서 성공)
- **탭 바 왼쪽 로고 = `editors.exe` 안에 박힌 Qt 리소스의 PNG**. 리소스 이름은 `logo_dark.png`, `logo_light.png` 와 해상도별 `_1.25x/_1.5x/_1.75x` 변형(같은 이름의 `.svg` 도 있으나 SVG 를 바꿔서는 화면이 변하지 않았음 — 100% 배율에서는 PNG 를 쓰는 것으로 보임).
- 위치(편집 전 `editors.exe` 기준 바이트 오프셋): 85×20 PNG 가 878451(561 B)·883113(499 B), 106×25 가 869875·924314, 128×30 이 896250·896999, 149×35 가 919292·947154. 테마별(밝음/어두움) 구분은 확인하지 않음. 2배율용은 이 가로세로 비율 검색에 걸리지 않아 위치 미확인.
- 방법: Qt 리소스는 압축 없이 평문으로 들어 있고 앞 4바이트가 길이이므로, **같은 크기 이하의 PNG 를 만들어 넣고 남는 길이를 0 으로 채우면** 길이 필드를 건드리지 않고 교체된다(IEND 뒤 여분은 무시됨).
- 결과: 85×20 두 개를 임시 로고(초록 사각형+막대, 130 B)로 바꾸자 **탭 바 로고가 바뀌었다**(`shots/logo2.png`). 앱 정상 동작.
- 남은 것: 다른 배율용 PNG(106/128/149 와 2배율), exe·작업 표시줄 아이콘(`app.ico` 가 `editors.exe` 안 리소스와 최상위 파일 양쪽에 있음), 셸 정보 화면 로고(`index.html` 의 `idx-logo` 심볼, 52×45), 편집기 About(웹 쪽), 설치 프로그램. `appLogoOverride` 는 윈도우 알림(토스트) 문자열이라 로고 설정과 무관.
- 새 로고는 압축 PNG 로 원본 크기(499~561 B 등) 안에 들어가야 하므로 단순한 그림이어야 한다(팔레트 PNG 권장). 더 크면 리소스 재빌드가 필요.

### 4-4b. 로고·아이콘 교체 이어서 (2026-11-17, 사본에서)
브랜드 임시 이름은 "Daylight", 로고는 임시 그림(해바라기 + 픽셀 글자). 모든 작업은 `test-install/` 사본에서만 했고 원본은 그대로다.
| 대상 | 위치 | 결과 |
|---|---|---|
| 탭 바 로고 8종(85×20, 106×25, 128×30, 149×35 × 밝음/어두움) | `editors.exe` 안 Qt 리소스 PNG(길이 필드 유지, 남는 길이 0 채움) | **성공**. 어두운 테마용은 평균 밝기 255(흰 글자), 밝은 테마용은 약 70(어두운 글자)으로 구분함 |
| 셸 정보(About) 화면 로고 | `index.html` 의 `<symbol id="idx-logo">` 를 직접 만든 SVG 로 교체(길이 제약 없음) | **성공, 화면 확인함**(`shots/shell-about2.png`) |
| 셸 About 의 수정본 고지 | `index.html` 의 About 템플릿(`about-appinfo`)에 "수정본·기반 버전·수정일·상표 문구" 한 줄 추가. 원 개발자 표시("© Ascensio System SIA 2026", "Licensed under GNU AGPL v3", onlyoffice.com 링크)는 **그대로 둠**(LICENSE 추가 조건 2·3) | **성공, 화면 확인함** |
| 편집기 쪽 About(`common/main/lib/view/About.js`) | 같은 고지를 넣어 뒀지만 **데스크톱 앱에서는 `Main.js` 가 `customization.about = false` 로 이 화면을 숨긴다 → 쓰이지 않음**. 고지는 셸 About 에 둬야 한다 | 화면에 안 나옴(확인함) |
| exe 파일 아이콘 | PE 리소스 그룹 101(`editors.exe`, `DesktopEditors.exe`) → Windows `UpdateResource` API 로 교체 | **성공**(탐색기용 아이콘이 해바라기) |
| 실행 중 창·작업 표시줄 아이콘 | `editors.exe` 안 **zlib 압축된 Qt 리소스 `:/app.ico`**(176,785 B → 압축 16,094 B 칸에 새 ico 6,898 B 를 넣고 해제 크기 필드 갱신) | **성공**(`WM_GETICON` 으로 해바라기 확인). 최상위 `app.ico` 파일은 쓰이지 않았음 |
시행착오: ① 작은 크기 아이콘을 PNG 로 넣으면 인식 실패 → **작은 크기는 BMP(DIB), 256 만 PNG**. ② 그룹 아이콘 항목은 14바이트(제 버그로 16바이트로 만들어 깨졌다가 수정). ③ `DesktopEditors.exe` 에는 아이콘 그룹이 73개(파일 형식별 연결 아이콘)라 한꺼번에 덮어쓰면 모두 같은 그림이 됨 → 그룹 101(앱 아이콘)만 교체해야 함.
화면 확인 중 알게 된 것: ① 이름은 같은 길이 치환이라 "DAYLIGHTOF Desktop Editors" 로 표시됨(임시, 10 글자 이내로만 가능). ② About 에 "Check for updates"가 있어 공식 서버로 업데이트를 확인한다 — 업데이트되면 수정이 덮어써지므로 자동 업데이트(`updatesvc.exe`)·확인 기능을 막아야 한다(미시험). ③ 창 제목 표시줄은 "- DAYLIGHTOF".
남은 것: 파일 형식 연결 아이콘(73개, 여전히 ONLYOFFICE 그림), 설치 프로그램(`unins000.exe`, 원본 설치 파일 `DesktopEditors_x64.exe` 는 Inno Setup 이라 별도 작업), 2배율 로고, 바이너리 수정으로 서명이 깨지는 문제.
도구: `replace-exe-icon.ps1`(UpdateResource 로 그룹 지정 교체)은 스크래치 폴더에 있고 저장소 밖이다 — 쓸 가치가 있으면 `scripts/` 로 옮길 것.

## 4-5. 한글 입력·한자 전환 시험 (2026-11-17, 수정한 사본 `test-install/`, Microsoft 한국어 IME)
방법: 새 문서(`--new:word`)에서 실제 키 입력(`keybd_event`)을 보내고 화면을 캡처(`shots/kr-*.png`). 입력기는 0412(한국어) + 0409(영어) 두 개.
| 시험 | 결과 | 비고 |
|---|---|---|
| 한글 조합("한글", 사용자가 직접 입력한 "한글이 잘 써지고"도 정상) | **정상** | `kr-1`, `kr-2` |
| 한/영 키 전환(영문 `hello` → 전환 → 한글 자모) | **정상** | 같은 키로 양방향 전환됨 (`kr-7-b`). 창 하단 언어 표시는 한국어↔영어로 바뀜 |
| **한자 전환**(조합 중 "한" + 한자 키) | **정상** | 후보창(1 韓 나라이름 한, 2 漢 한수 한, 3 限 …)이 뜨고 선택한 글자(韓)가 문서에 들어감 (`kr-3`, `kr-4`) |
| 이미 입력된 글자를 선택하고 한자 키(재변환) | **동작 안 함** | 선택(하이라이트)은 확인했으나 후보창이 뜨지 않음 (`kr-8`, `kr-9`). 웹 기반 편집기의 한계로 추정하나 **수정하지 않은 원본 ONLYOFFICE 와 비교하지 않았음** |
시험 중 시행착오: Esc 키를 누르면 편집기에서 포커스가 빠져 이후 입력이 문서에 안 들어갔다(앱 문제가 아니라 시험 방법 문제). 입력 모드 판독(`ImmGetConversionMode`)은 믿을 수 없어 화면 결과로만 판단.
미시험: 대형 문서·표 안에서의 한글 입력, 글꼴(맑은 고딕 등) 표시, 한글 맞춤법/자동 고침, 한자→한글 변환, 단어 단위 한자(예: "대한민국" 전체), 엑셀·파워포인트 편집기.

## 5. 임시 판단
- 속도는 합격. "추가형 변경"(버튼·매크로)은 플러그인으로 빌드 없이 가능.
- "제거·재배치형 변경"과 이름·로고 교체는 소스 빌드가 필요할 가능성이 크고, Windows 빌드는 문서가 빈약해 위험이 크다.
- SDK 조사 결과 C#/Avalonia 에서 ONLYOFFICE 편집 UI 를 끼워 쓰는 길은 사실상 없다(Document Builder 는 렌더링 UI 용이 아니고 무료판 워터마크). Desktop Editors 는 완제품으로 쓰고 플러그인·테마·파일 수정·소스 빌드로 손보는 구조다.
- 따라서 가족 불편 사항이 "추가·자동화"로 풀리는 정도면 ONLYOFFICE 채택이 맞고, "UI 구조를 덜어 내야" 한다면 4-1·4-3 을 먼저 확인해야 한다.
