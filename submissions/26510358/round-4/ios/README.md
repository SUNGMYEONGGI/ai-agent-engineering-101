# 싸다싸 가게 iOS 앱 (SwiftUI)

Round 4 에이전트의 네이티브 iOS 앱. 에이전트와 kit의 미니앱 서버는 컴퓨터에서 돌고(`agent_kit.py run ... --app 8800`),
이 앱은 kit의 웹 페이지(`app/index.html`)가 쓰는 것과 같은 API(`/api/state`, `/api/chat`, `/api/offer`, `/api/answer`)로 붙는다.

## 디자인

캐릭터가 이끄는 AI 동반자 앱 스타일. 캐릭터 기획안(`../asset/AI_Assistant_Character_Design_12.md`)의 기준을 따른다:
아이보리 `#F8F7F3` 바탕에 검정 `#171717` 잉크, 다크 모드에서는 반전, 상태가 실제로 바뀔 때만 대표 동작을 300–500ms 한 번 재생,
움직임 줄이기 설정에서는 정지.

| 화면 | 캐릭터 | 하는 일 |
|---|---|---|
| 연결 | 호가·들창·맞표·견본 | 링크 붙여넣기, 또는 데모로 둘러보기 |
| 대화 | 내가 고른 캐릭터 | 빈 화면엔 큰 캐릭터와 추천 질문, 에이전트 말은 아바타 옆 본문으로, 입력창은 떠 있는 캡슐 |
| 대화 · 질문 카드 | 엇갈림 (두 선택지 비교) | `app_ask_owner` 질문을 선택지 버튼과 직접 답하기로 |
| 대화 · 카드 | 삐침 (알림) | `app_show_card` |
| 활동 | 움직임마다 역할에 맞는 캐릭터 | reply→호가, forge_tool→층층, read_tool→꿰미, write_note·memory→되감, sleep→틈, pay·settle→맞표, stock·price→들창, market·catalog→견본, mesh_·app_→받침 |
| 나 | 12종 선택 | 내 에이전트 캐릭터, 주인 한도(`app_owner_limits`), 연결 정보 |
| 허락 시트 | 받침 (확인 대기) | MeshKit 호출 허용/거절 |

캐릭터 이미지는 `Assets.xcassets/Characters/`에 template 이미지로 넣었다(몸은 불투명, 배경과 눈은 투명).
그래서 글자색을 따라 칠해지고, 다크 모드에서 흰 몸에 눈이 배경색으로 뚫려 보인다. 원본은 `../asset/AI_Assistant_Character_Images_12/`.
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
