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

## 엔진(sdkjs) 패치: `patches/sdkjs/`
- 설치 트리가 아니라 **엔진 소스**(`external/sdkjs`, 태그 v10.0.0.169)에 적용한다. 경로는 sdkjs 루트 기준(예: `word/Drawing/DrawingDocument.js`), `git apply -p1`.
- `tools/build.ps1` 의 위 목록 단계는 이 폴더를 건너뛰고, 4f 단계(`tools/engine/build-sdk.ps1`)가 적용·빌드한 뒤 `editors/sdkjs/word/` 의 `sdk-all-min.js` 와 `sdk-all.js` 를 **함께** 교체한다. 패치가 하나도 없으면 엔진은 그대로(원본). 패치 없이 소스 빌드만 시험하려면 `toolsuild.ps1 -ForceEngine`.
- 확인: `tests\engine.ps1 [-ExpectEngine]` (화면 픽셀로 본문 글자·눈금자가 그려졌는지). 기능 패치마다 시험을 추가한다. 계획은 `docs/ENGINE-PLAN.md`.

