# 편집 엔진(sdkjs) 수정 계획서

작성일 2026-11-18. 상태: **계획만 있음, 착수 전.** 대상 기능 세 가지와, 그것을 위해 엔진 소스를 받아 고쳐 쓰는 방법을 정한다.

## 1. 목표 기능

| # | 기능 | 사용자 요구 | 수정 위치(추정) |
|---|---|---|---|
| F1 | 여백 경계 표시 | 문서 페이지의 상·하·좌·우 여백 안쪽 경계를 연한 선/모서리 표식으로 표시 (Word의 "텍스트 경계 표시"). 보기 메뉴에서 켜고 끔 | sdkjs `word/Drawing/DrawingDocument.js` 의 페이지 그리기 |
| F2 | 눈금선 | 보기 메뉴 "눈금자" 아래에 "눈금선" 체크 항목. 페이지 위에 격자선 표시 | 같은 파일 + `word/api.js` 에 `put_ShowGridlines` 류 추가 |
| F3 | 페이지 탐색 | 좌측 사이드 바의 탐색 패널에 "페이지" 탭(썸네일 목록, 클릭하면 해당 쪽으로 이동) | `common/` 의 `ThumbnailsControl`(슬라이드용)을 문서 편집기에 연결 + web-apps `documenteditor/main/app/view/Navigation.js` |

현재 설치본의 엔진은 Closure로 줄이고 이름을 뭉갠 `sdk-all-min.js` 라서 직접 고칠 수 없다. 그래서 **원본 소스를 받아 고친 뒤 다시 만들어 설치 트리의 엔진 파일을 바꾸는** 방식으로 한다.

## 2. 접근: 엔진도 "오버레이"로 (CLAUDE.md 원칙 유지)

- 저장소에는 소스를 넣지 않는다. `patches/sdkjs/*.patch`(git diff 형식, `-p1`, 업스트림 `sdkjs` 트리 기준)와 `tools/engine/` 스크립트만 둔다.
- 소스는 `external/sdkjs`(얕은 복제, `upstream.txt` 에 기록됨). **현재 복제본은 v10.0.0.167 인데 설치본은 169** → 첫 작업은 `git fetch` 로 태그 `v10.0.0.169` 에 맞추는 것(태그는 이미 존재).
- 새 단계 `tools/engine/build-sdk.ps1`: `external/sdkjs` 를 169 로 맞춤 → 패치 적용(`git apply`) → `python build/build.py`(Python 3.12 확인됨) → 결과를 `build\app\editors\sdkjs\{word,...}` 에 덮어씀. `tools/build.ps1` 이 이 단계를 호출하고 **엔진 패치가 없으면 건너뛴다**.
- 패치 하나 = 설명 + 시험 하나. 실패하면 빌드가 멈춘다(일치 개수 검사처럼).

## 3. 먼저 풀어야 할 위험 (0단계, 하루 이내 판단)

1. **`sdk-all.bin` 의 정체** (word 폴더에 5.9 MB). 데스크톱 앱이 `sdk-all-min.js` 가 아니라 이 `.bin`(컴파일된 캐시일 가능성)을 읽으면 JS 만 바꿔서는 반영되지 않는다. 확인: 파일 머리 구조, 엔진 파일을 바꿨을 때 실제로 반영되는지 시험(예: 제목에 문구 하나 넣어 보기). 반영 안 되면 `.bin` 생성 도구가 필요 → 계획 재검토.
2. **빌드 결과의 호환성.** `build.py` 는 이어 붙이기만 하고(Closure/Java 없음) 이름을 줄이지 않는다. 장점은 디버깅이 쉽고 결과가 설치본과 동작이 같다는 것, 단점은 크기(9 MB급)와 시작 시간. 시험: 소스 그대로(패치 0개) 빌드해 설치본과 같은 엔진으로 동작하는지, 시작·문서 열기 시간 차이 측정. 느리면 선택적으로 Closure 를 쓰는 방안(Java 필요)을 따로 검토.
3. **사용자 데이터(.docx 등)에는 영향 없음** 을 확인: 표시 전용 기능이라 저장 형식을 건드리지 않는다.
4. **라이선스.** 엔진도 AGPLv3. 수정 표시는 `docs/` 와 정보 화면의 기존 고지에 "엔진 일부 수정" 한 줄을 더한다.

0단계 통과 조건: 패치 0개로 만든 엔진이 현재 앱에서 `tests\smoke.ps1`, `tests\edit-latency.ps1` 을 통과.

## 4. 단계별 계획

### 단계 A — 기반 (0단계 통과 후)
- A1. `external/sdkjs` 를 169 로 맞추고 `upstream.txt` 의 설명과 일치시킴.
- A2. `tools/engine/build-sdk.ps1`, `patches/sdkjs/` 구조, `tools/build.ps1` 연결, `.gitattributes`(패치 줄바꿈 변환 금지) 확인.
- A3. 시험 `tests\engine.ps1`: 패치 0개 빌드의 동작 확인 + 엔진 파일 해시가 기대와 같은지.

### 단계 B — F1 여백 경계 (가장 쉬움, 먼저)
- B1. `DrawingDocument.js` 에서 페이지 하나를 그리는 곳(`OnRepaintPage` 계열, 페이지 배경을 그린 직후)을 찾아 본문 영역(페이지 여백 안쪽)의 네 모서리에 ㄱ자 표식(Word 방식) 또는 점선 사각형을 그린다. 좌표는 구역 속성(여백, 페이지 크기)에서 가져온다.
- B2. 켜고 끄는 변수 `ShowMarginBoundaries` 와 공개 함수 `put_ShowMarginBoundaries/get_...` 를 `word/api.js` 에 추가(`put_ShowParaMarks` 를 본뜸). 인쇄·PDF 내보내기·썸네일에는 그리지 않는다.
- B3. web-apps 쪽: 보기 탭에 체크 항목 "텍스트 경계"를 추가하고 `Common.localStorage` 로 기억(기존 `눈금자`, `Rulers` 항목 패턴). 한국어 문구는 `tools/ko/terms.json`.
- B4. 시험: 새 문서에서 켜고 화면 캡처 → 네 모서리 표식 픽셀이 여백 좌표에 있는지, 끄면 사라지는지, 확대 비율 50/100/200 %에서 어긋나지 않는지, 여백을 바꾸면 따라 움직이는지.

### 단계 C — F2 눈금선
- C1. 같은 곳에서 본문 위에 가는 격자선(간격은 1 cm 또는 눈금자 단위에 맞춤, 색은 연한 회색 알파)을 그린다. 문서 편집기만 대상(스프레드시트는 이미 눈금선 있음, 프레젠테이션은 별도 항목이 있는지 확인 후 결정).
- C2. 공개 함수 `put_ShowGridlines`, 보기 탭 "눈금선" 항목(눈금자 아래, F1 과 같은 패턴).
- C3. 시험: B4 와 같은 방식. 그리기 비용 측정(`edit-latency.ps1` 로 켠 상태 입력 지연이 기준 이내인지).
- (선택) 개체를 격자에 맞추는 기능은 이번 범위 밖.

### 단계 D — F3 페이지 탐색
- D1. 먼저 범위 확정: 탐색 패널(`Navigation.js`)에 "제목 / 페이지" 두 탭을 둔다. "페이지"는 썸네일 목록.
- D2. 엔진: 문서용 썸네일 공급. 슬라이드 쪽 `ThumbnailsControl`(`common/`)이 문서 페이지 그리기 경로와 맞는지 조사하고, 안 맞으면 `DrawingDocument` 가 이미 가진 페이지 렌더(`DrawPage`)를 작은 캔버스에 쓰는 별도 간단 구현으로 간다(가상 스크롤, 보이는 것만 그림, 편집 시 해당 쪽만 갱신).
- D3. 이동: 썸네일 클릭 → `GoToPage`. 현재 쪽 강조는 `OnCurrentPage` 이벤트에 연동.
- D4. web-apps UI: 좌측 사이드 바에 별도 아이콘을 둘지(요구 문구: "아이콘 추가") 탐색 패널 탭으로 둘지는 D1 에서 결정. 아이콘은 Phosphor(`mapping.json`)로 추가하고 `tests\icons.ps1` 에 포함.
- D5. 시험: 100쪽 문서를 열어 썸네일 열기 시간·메모리·입력 지연 측정, 클릭 이동, 쪽 추가/삭제 반영.
- 가장 크고 위험한 단계다. 성능이 기준(입력 지연 증가 20 % 이내)을 넘으면 최초 버전은 "보이는 쪽 근처만 그림"으로 제한한다.

### 단계 E — 마무리
- E1. 전체 시험: `smoke`, `brand`, `icons`, `theme`, `edit-latency`, `engine`, 설치 파일(`installer.ps1`).
- E2. 문서: `docs/PROGRESS.md`(결정·측정값), 정보 화면 수정 고지, `docs/KOREAN.md` 에 새 문구.
- E3. 업스트림 버전을 올릴 때의 절차: 패치 충돌 확인 → 3개 패치만 다시 맞추면 되도록 패치를 기능별로 작게 유지.

## 5. 순서와 일정(대략)

0단계(위험 확인) → A → B → C → D → E. B·C 는 구조가 같아 연달아 진행, D 는 별도 판단점(0단계 + B 가 잘 되면 착수).
각 단계 끝에서 사용자가 화면으로 확인(앱 조작 중 자동 시험과 겹치지 않게, 확인 요청 후 시험 정지).

## 6. 결정이 필요한 것

1. 0단계 결과가 나쁘면(`.bin` 문제 등) 중단하고 "화면 덮개" 방식(웹 계층에서 투명 캔버스)으로 전환할지.
2. F3 를 좌측 사이드 바의 **별도 아이콘**으로 할지 **탐색 패널 탭**으로 할지(권장: 탐색 패널 탭 + 필요하면 아이콘 추가).
3. F1 표식 모양: Word 방식 ㄱ자 모서리 / 점선 사각형(권장: 모서리 표식).

## 7. 0단계 결과 (2026-11-18)

- **소스 버전:** `external/sdkjs` 를 태그 `v10.0.0.169` 로 맞춤. 이 커밋에 167~170 태그가 모두 붙어 있어 169 와 같은 소스다(계획 2절의 "167 이라 어긋남" 우려는 해소).
- **빌드:** `PYTHONUTF8=1 python build/build.py --product word --desktop` (Windows 기본 코드 페이지 cp949 때문에 `PYTHONUTF8=1` 필요). 결과 `deploy/sdkjs/word/` 의 `sdk-all-min.js`(3.7 MB), `sdk-all.js`(30.9 MB). 설치본은 1.3 MB / 9.4 MB(줄이고 이름을 뭉갠 것).
- **어느 파일을 쓰나:** 화면(그리기·UI)은 `sdk-all-min.js`(web-apps `app.js` 의 `sdk` 경로), 문서 열기·변환 쪽 네이티브는 `sdk-all.js`(+ V8 코드 캐시 `sdk-all.bin`, 버전 문자열 8.9.255.25). **두 파일을 반드시 함께 바꿔야 한다.** `min` 만 바꾸면 문서가 "Loading document" 에서 멈췄다. 둘 다 바꾸면 정상(문서 표시, 눈금자, 글꼴 목록, 커서 모두 정상). `.bin` 은 그대로 둬도 동작(캐시는 맞지 않으면 무시되는 것으로 보임; 시작 시간 영향은 E단계에서 측정).
- **시험의 한계:** `tests\smoke.ps1` 은 문서가 실제로 그려졌는지 보지 않아 엔진이 고장 나도 통과한다(`min` 을 지워도 통과). **단계 A 에서 `tests\engine.ps1` 로 화면 픽셀(눈금자·본문 글자)을 검사해야 한다.**
- **입력 지연(`tests\edit-latency.ps1`, 30타):** 원본 엔진 중앙값 67 ms / 최대 82 ms, 줄이지 않은 새 엔진 100 ms / 121 ms(+약 50%). 기준 3000 ms 대비 매우 작지만 계획 3절의 "20% 이내" 기준은 넘는다. 다만 이 수치는 시험 도구의 입력·캡처 시간을 포함한다. 시작 시간은 둘 다 3 초대로 눈에 띄는 차이 없음.
- **결론:** 0단계 통과(엔진 교체 가능). 걸림돌은 두 가지: ① 줄이지 않은 엔진의 약간의 지연·용량 증가(필요하면 Closure+Java 로 줄이는 방안을 후속 검토), ② `.bin` 캐시 불일치(동작에는 문제 없음, 시작 시간 확인 필요). `build\app` 은 원본 엔진으로 되돌려 놓았다(`build\sdk-orig` 에 백업).

## 8. 단계 A 결과 (2026-11-18)

- A1: 소스는 `v10.0.0.169` 로 맞춤(0단계). `build-sdk.ps1` 이 빌드 전후에 태그 체크아웃·`git clean` 으로 소스를 깨끗이 되돌린다.
- A2: `tools/engine/build-sdk.ps1`, `patches/sdkjs/`(비어 있음), `tools/build.ps1` 4f 단계(`-ForceEngine` 옵션), 앱 패치 목록에서 `patches/sdkjs/` 제외(`build.ps1`, `smoke.ps1`). 패치가 없으면 엔진 단계는 건너뛰고 설치본 엔진을 그대로 둔다. BUILD-INFO 에 `engine=...`, `engine-patch=...` 줄을 남긴다.
- A3: `tests/engine.ps1`. 본문 글자(검은 픽셀 수)·눈금자(명암 변화)·"Loading document" 상자 부재를 2 초마다 최대 60 초 확인. 확인: 소스 빌드 엔진(0패치)에서 8/8 통과(글자 3 초 안에 그려짐), `sdk-all-min.js` 만 원본으로 되돌리면 3개 실패(시험이 실제로 고장을 잡음), 패치 없는 일반 빌드에서도 통과, `smoke` 11/11.
- 작업 위치: worktree `../daylight-office-engine`(브랜치 `engine-sdk`). `external/` 은 메인 저장소 것을 junction 으로 공유하므로 두 작업 트리가 같은 `external/sdkjs` 를 쓴다(빌드 때만 건드리고 끝에 원복).

## 9. 단계 B 결과 (2026-11-18)

- 엔진 패치 `patches/sdkjs/0001-margin-boundaries.patch`: `DrawingDocument.DrawMarginBoundaries`(본문 영역 네 모서리 ㄱ자 표식, 팔은 여백 쪽, 14px), `HtmlPage.OnUpdateOverlay` 에서 호출, `api.put/get_ShowMarginBoundaries`. 화면 전용(인쇄·내보내기는 다른 경로).
- 알게 된 것: ① 페이지의 `margin_right`/`margin_bottom` 은 너비가 아니라 **페이지 위의 위치(mm)**. ② `COverlay.Clear()` 는 기록된 사각형만 지우므로 표식을 그릴 때 `ClearAll` 과 전체 경계를 표시해야 해제 시 바로 지워진다. ③ `--remote-debugging-port=9333` 으로 시험 앱의 DevTools 에 접속해 엔진을 직접 조회할 수 있다(`tests/lib/cdp.py`).
- 앱 패치 `web-apps/0002`: 보기 탭 "텍스트 경계" 체크(설정 저장, 시작 시 복원). `0003`: 여백 "표준"을 25.4mm 4면으로(Word 값).
- 사용자가 화면에서 확인함(동작 양호). 자동 시험 `tests/margin-marks.ps1` 은 아직 끝까지 돌려 보지 못함(사용자가 PC 를 쓰는 중이라 중단) — 다음에 입력 가능할 때 한 번 실행해 확정한다.

## 10. 단계 C 결과 (2026-11-18)

- 엔진 패치 `patches/sdkjs/0002-gridlines.patch`(0001 위의 증분): `CDocument.Draw` 에서 쪽 배경 직후 `private_DrawGridlines` 로 격자를 **쪽 그림에 직접** 그린다(글자·그림·도형이 위). 간격 0.13인치(3.302mm, Word 기본), `rgba(120,120,120,0.3)`. 편집 기능을 지원하는 화면용 그래픽에만(`isSupportEditFeatures`) 그리므로 인쇄·내보내기에는 없다. `api.put/get_ShowGridlines`(켜고 끌 때 `OnRePaintAttack` 으로 전체 쪽 다시 그림).
- 앱 패치 `web-apps/0004-view-gridlines.patch`: 보기 탭 "눈금자" 아래 "눈금선"(설정 저장·시작 시 복원). 한국어 "눈금선"(`terms.json` `add`).
- 시행착오: 처음엔 여백 표식처럼 오버레이 캔버스에 그렸으나 글자 위로 덮여 Word 와 달랐다 → 쪽 그림 방식으로 변경. 농도는 Word 캡처와 비교해 조정(최종 밝기 약 214). 사용자가 화면에서 확인함(양호).
- 소스 줄바꿈 주의: `external/sdkjs` 는 처음 복제 때 CRLF 로 풀린 파일이 있어 패치 생성 때 전체 파일 diff 가 났다. `git checkout -f` + `git reset --hard` 로 LF 로 맞춘 뒤 생성해야 한다(저장소 blob 은 LF).

## 11. 단계 D 결과 (2026-11-18)

- 방식: 왼쪽 "탐색"(제목 목록) 패널 머리글에 "제목 / 페이지" 탭(별도 사이드 바 아이콘은 만들지 않음). 선택한 탭은 `de-navigation-tab` 에 저장.
- 엔진 패치 `patches/sdkjs/0003-page-thumbnail.patch`: `asc_getPageThumbnail(쪽, 너비px)` — 쪽 하나를 새 캔버스에 `LogicDocument.DrawPage` 로 그려 돌려줌(문단 표식·눈금선은 잠시 끔, 다시 계산 중이면 null). 새 엔진 이벤트는 만들지 않고 기존 `asc_onCountPages`(쪽 수), `asc_onEndCalculate`(편집 후 전체 재계산), `asc_onCurrentPage`(현재 쪽)를 썼다.
- 앱 패치 `web-apps/0005-navigation-pages.patch`: 탭, 썸네일 목록(보이는 것만 한 장씩 그림, 편집 후 700ms·스크롤 60ms 디바운스), 클릭 → `goToPage`, 현재 쪽 강조·자동 스크롤. 한국어 "페이지".
- 시행착오: 휠 스크롤이 안 됐다 — 편집기가 자체 스크롤러 밖의 휠을 가로채서였고, 제목 목록과 같은 `Common.UI.Scroller`(perfect-scrollbar)로 해결. 이 스크롤러는 자식 요소로 레일을 넣으므로 썸네일은 안쪽 `.dl-pages-in` 에만 다시 그린다.
- 사용자가 화면에서 확인함(썸네일·이동·스크롤 양호). 남은 것: 사이드 바 아이콘 도움말 이름이 여전히 "제목"(이름·아이콘을 "탐색"으로 바꿀지 미정), 큰 문서(수십 쪽 이상) 성능은 사용자 사용 중 관찰.
