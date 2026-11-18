# patches/

업스트림 설치 트리(`external/upstream-<버전>`)에 적용하는 수정. `tools/build.ps1` 이 `patches/**/*.patch` 를 **파일 이름 순서**로 `git apply -p1` 한다. 경로는 설치 트리 기준(예: `editors/web-apps/apps/...`).

## 규칙
- 패치 하나 = 목적 하나. 이 표에 한 줄을 추가하고, `tests/` 에 확인하는 시험을 둔다(최소한 `tests/smoke.ps1` 의 표식 확인).
- 만드는 법: 설치 트리 파일을 `a/`, 고친 것을 `b/` 에 두고
  `git -c core.autocrlf=false diff --no-index --no-prefix a b > patches/web-apps/NNNN-이름.patch`
  (`a/`·`b/` 아래에 `editors/...` 경로를 그대로 둔다. 업스트림 파일은 LF 줄바꿈이다.)
- 번호는 적용 순서. 새 업스트림 버전으로 올릴 때는 충돌 나는 패치부터 고친다.
- `.patch` 는 줄바꿈 변환 금지(`.gitattributes`).
- 정보(About) 화면의 원 개발자 표시·수정본 고지를 지우는 패치는 만들지 않는다(라이선스 추가 조건).

## 목록
| 번호 | 파일 | 목적 | 확인 |
|---|---|---|---|
| 0001 | `web-apps/0001-layoutmanager-hidden-elements.patch` | `LayoutManager.js` 에 "누구에게나 숨길 요소" 목록(`_daylightHidden`)을 추가. 지금은 그리기·보호·플러그인 탭(`toolbar-draw`, `toolbar-protect`, `toolbar-plugins`)을 숨김. 더 숨길 후보는 `docs/M4-LAYOUT.md` | 스모크의 표식 확인 + 화면에서 "그리기" 탭 없음 |
| 0002 | `web-apps/0002-view-margin-boundaries.patch` | 보기 탭에 "텍스트 경계" 체크 항목(엔진 패치 `sdkjs/0001` 의 `put_ShowMarginBoundaries` 호출, 설정 저장). 한국어 문구는 `tools/ko/terms.json` 의 `add` | `tests/margin-marks.ps1` (직접 눈으로도 확인) |
| 0003 | `web-apps/0003-normal-page-margins.patch` | 레이아웃 > 여백 > "표준" 을 지역과 상관없이 상하좌우 25.4mm 로(업스트림은 미국·캐나다 밖에서 20/30/20/15, 좌우 비대칭). Word 와 같은 값 | 화면에서 표준 선택 후 눈금자 좌우 같은지 확인 |
| 0004 | `web-apps/0004-view-gridlines.patch` | 보기 탭 "눈금자" 아래에 "눈금선" 체크 항목(엔진 패치 `sdkjs/0002` 의 `put_ShowGridlines`, 설정 저장). 한국어는 `terms.json` `add` | 화면에서 확인 |

## 엔진(sdkjs) 패치: `patches/sdkjs/`
- 설치 트리가 아니라 **엔진 소스**(`external/sdkjs`, 태그 v10.0.0.169)에 적용한다. 경로는 sdkjs 루트 기준(예: `word/Drawing/DrawingDocument.js`), `git apply -p1`.
- `tools/build.ps1` 의 위 목록 단계는 이 폴더를 건너뛰고, 4f 단계(`tools/engine/build-sdk.ps1`)가 적용·빌드한 뒤 `editors/sdkjs/word/` 의 `sdk-all-min.js` 와 `sdk-all.js` 를 **함께** 교체한다. 패치가 하나도 없으면 엔진은 그대로(원본). 패치 없이 소스 빌드만 시험하려면 `tools\build.ps1 -ForceEngine`.
- 확인: `tests\engine.ps1 [-ExpectEngine]` (화면 픽셀로 본문 글자·눈금자가 그려졌는지). 기능 패치마다 시험을 추가한다. 계획은 `docs/ENGINE-PLAN.md`.
- 엔진 패치는 번호 순서로 쌓인다: `sdkjs/0001` 여백 경계 표식, `sdkjs/0002` 눈금선(0001 위에 만든 증분).
