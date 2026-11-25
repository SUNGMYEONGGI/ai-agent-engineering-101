# Hermes 가게 iOS 앱 (SwiftUI)

Round 4 에이전트의 네이티브 iOS 앱. 에이전트와 kit의 미니앱 서버는 컴퓨터에서 돌고(`agent_kit.py run ... --app 8800`),
이 앱은 kit의 웹 페이지(`app/index.html`)가 쓰는 것과 같은 API(`/api/state`, `/api/chat`, `/api/offer`, `/api/answer`)로 붙는다.

## 디자인

캐릭터가 이끄는 AI 동반자 앱 스타일. 캐릭터 기획안(`../asset/AI_Assistant_Character_Design_12.md`)의 기준을 따른다:
차가운 무채색 `#F5F6F8` 바탕에 검정 `#171717` 잉크(처음엔 아이보리 `#F8F7F3`였는데 누렇게 보여서 바꿈), 다크 모드에서는 반전,
상태가 실제로 바뀔 때만 대표 동작을 300–500ms 한 번 재생, 움직임 줄이기 설정에서는 정지.
대화 화면은 캐릭터가 상단 가운데에 떠 있다. 에이전트가 생각하는 동안 통통 뛰고, 주인이 입력하는 동안 귀 기울이듯 기울고,
답이 오면 한 번 튀며 물결이 퍼진다. 탭하면 반응한다.

앱에는 실제로 쓰는 캐릭터 3개만 둔다. 에이전트는 하나라서 캐릭터도 하나(호가)이고, 나머지 둘은 주인에게 묻는 일과 허락을 기다리는 일을 맡는다.
기획안의 나머지 9개는 `../asset/`에 그대로 있고, 에이전트나 화면이 늘어날 때 `Core/Characters.swift`의 enum과 `Assets.xcassets/Characters/`에 하나씩 추가한다.
`AgentCharacter.agents`에 두 번째 에이전트가 들어가면 설정 화면에 캐릭터 선택이 다시 나타난다.

| 캐릭터 | 맡은 일 | 나오는 곳 |
|---|---|---|
| 호가 | 가게 운영 에이전트 | 연결 화면, 대화 상단과 답변, 카드(`app_show_card`), 활동 피드의 시장 움직임, 만든 도구 |
| 엇갈림 | 주인에게 묻기 | 대화의 질문 카드(`app_ask_owner`) |
| 받침 | 확인 대기 | MeshKit 허락 시트, 활동 피드의 `mesh_`·`app_` 움직임, MeshKit 도구 |

캐릭터 이미지는 `Assets.xcassets/Characters/`에 template 이미지로 넣었다(몸은 불투명, 배경과 눈은 투명).
그래서 글자색을 따라 칠해지고, 다크 모드에서 흰 몸에 눈이 배경색으로 뚫려 보인다. 원본 12개는 `../asset/AI_Assistant_Character_Images_12/`.
앱 아이콘은 호가.

## 실행

### iOS 시뮬레이터 (Mac 한 줄)

```bash
cd submissions/26510358/round-4/ios
./run-simulator.sh                 # 데모 모드: 에이전트 없이 화면 확인
./run-simulator.sh "<[app] open 링크>"   # 실제 에이전트에 연결
```

가장 최신 iPhone 시뮬레이터를 켜고 빌드·설치·실행까지 한다. `DEVICE="iPhone 15"`로 기종을 고른다.
다크 모드는 `xcrun simctl ui <UDID> appearance dark`.
Xcode 27의 DeviceHub는 창을 열지 않아서 탭을 누를 수 없다. 대신 실행 인자 `-tab 0|1|2`로 시작 탭을 고르고,
Debug 빌드의 데모 모드에서는 `-demo-flow`가 `확인 → 요청 카드 → 허용 → 활동` 흐름을 혼자 진행한다. 단계마다 `xcrun simctl io <UDID> screenshot`으로 찍어서 확인한다.

### Xcode

1. Mac에서 `Ssadassa.xcodeproj`를 Xcode로 연다 (iOS 16 이상).
2. 시뮬레이터: iPhone을 고르고 Run.
3. 내 아이폰: Signing & Capabilities에서 Team을 고르고(무료 Apple ID 가능), bundle identifier를 내 것으로 바꾼 뒤 Run.
   처음에는 설정 → 일반 → VPN 및 기기 관리에서 개발자를 신뢰한다. 무료 계정으로 서명한 앱은 7일 뒤 만료되니 다시 Run.
4. 연결 화면에 kit이 출력한 링크를 붙여 넣는다.
   - 에이전트가 이 Linux 서버에서 돌기 때문에 Mac 시뮬레이터에서도 `--app-tunnel`의 `https://...trycloudflare.com/?k=...` 링크를 쓴다.
     (`http://127.0.0.1:8800`은 에이전트가 같은 Mac에서 돌 때만 된다.)

## 구조

```
Ssadassa/Core/   Foundation만 쓰는 부분 (캐릭터 목록, 데모 데이터 포함) (Linux에서도 빌드): API 클라이언트, 1.5초 polling, 주인 도구 3개, MeshKit 허락 응답
Ssadassa/UI/     SwiftUI 화면
CoreCheck/       Core를 실제 미니앱 서버에 붙여 확인하는 프로그램
Package.swift    Core와 CoreCheck만 빌드하는 SwiftPM 패키지 (Xcode 앱과 별개)
gen_xcodeproj.py Swift 파일을 추가·삭제한 뒤 Xcode 프로젝트를 다시 만든다
run-simulator.sh Mac에서 시뮬레이터 실행
```

접근은 kit의 gate가 받는 쿠키 `miniapp_access=<접근 코드>`를 매 요청에 붙인다. 도구 제공·응답은 kit이 `/miniapp.js`에 넣는
page token이 필요해서, 접근 코드로 그 파일을 받아 token을 읽는다(웹 페이지와 같은 권한).

## 확인한 것 (2026-11-18, Linux, Swift 6.1.2)

- `swift run CoreCheck "<링크>"`를 `ops/preview_app.py`(kit의 `miniapp.app()` + 가짜 에이전트)에 붙여 11개 모두 통과:
  링크 파싱, 틀린 접근 코드 거절, polling, 도구 3개 등록, 에이전트의 한도 읽기·카드·질문, 주인 답이 에이전트 채팅에 도착,
  MeshKit 허락 → 서명 검증된 영수증 (`"source": "owner, in the iOS app"`으로 Swift가 답한 것 확인).
- SwiftUI 화면은 Linux에서 타입 검사를 할 수 없어 `swiftc -parse`(문법)까지만 확인했다. 빌드와 화면은 Xcode에서 확인할 것.

### 11-18 UI 개편 후

- CoreCheck 13개 통과 (데모 데이터, 캐릭터 12종과 움직임 매핑 추가). 아무도 붙어 있지 않은 미리보기 서버로 확인했다.
- 웹 앱과 iOS 앱을 동시에 열면 같은 이름의 주인 도구를 둘 다 제공해서, 먼저 polling한 쪽이 답한다(실제로 한 번 겹쳤다).
  한도는 기기마다 따로 저장되니 주인 앱은 하나만 열어 둔다.
- SwiftUI 화면은 여전히 Linux에서 문법 검사까지만 했다. 시뮬레이터에서 처음 빌드할 때 오류가 나면 그 메시지로 고친다.

### 11-19 요청 흐름 개편

- MeshKit 허락을 시트 대신 대화 안의 요청 카드로 바꿨다. 카드에는 실행할 작업, 적용 범위(이번 1회), 인자를 보여 주고, 버튼은 `이번 1회 허용`과 `이번 요청 거절`이다.
  상단의 `확인 N건`을 누르면 그 카드로 이동한다.
- `app_ask_owner`의 선택지는 에이전트가 쓴다. 그래서 앱이 라벨을 바꾸지 않고, 도구 설명에 "품목과 수량이 드러나는 행동으로 써라(예: `소파 5개까지 매입 승인`)"를 넣었다.
- 활동 탭은 `확인 필요`를 맨 위에 두고, 주인이 내린 결정과 한도 변경을 `진행 중 / 완료 / 실패 / 거절함`으로 보여 준다. 한도 변경은 바뀌기 전과 후의 값, 그리고 바꾼 사람을 함께 남긴다.
  kit은 MeshKit 영수증을 에이전트에게만 넘긴다. 그래서 허용한 뒤 에이전트가 처음 보내는 대화를 결과로 보고, 거기에 실패를 뜻하는 말이 있으면 `실패`로 표시한다. 이 기록은 앱을 켜 둔 동안만 남는다.
- 반영하지 않은 것: `거래 내역 보기`. `/api/state`에는 거래 원장이 없고, 거래 기록은 에이전트의 notes와 장부에만 있다. 오늘 요약 카드의 `답장`으로 에이전트에게 물어보면 된다.
- 확인: 시뮬레이터(iPhone 17, Xcode 27.2)에서 `-demo-flow`로 확인 2건 → 허락 카드 → 허용 → 활동 `진행 중` → `완료`까지 스크린샷으로 확인했다. 실제 에이전트에 연결한 상태로는 아직 확인하지 않았다.
