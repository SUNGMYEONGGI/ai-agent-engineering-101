# 싸다싸 가게 iOS 앱 (SwiftUI)

Round 4 에이전트의 네이티브 iOS 앱. 에이전트와 kit의 미니앱 서버는 컴퓨터에서 돌고(`agent_kit.py run ... --app 8800`),
이 앱은 kit의 웹 페이지(`app/index.html`)가 쓰는 것과 같은 API(`/api/state`, `/api/chat`, `/api/offer`, `/api/answer`)로 붙는다.

| 화면 | 하는 일 |
|---|---|
| 연결 | kit이 출력한 `[app] open ...` 줄을 붙여 넣는다. 접근 코드가 든 링크는 Keychain에 저장 |
| 대화 | 에이전트와 채팅. 에이전트의 카드(`app_show_card`)와 질문(`app_ask_owner`)이 채팅 위에 뜬다 |
| 가게 | 최근 움직임, 에이전트가 만든 도구, MeshKit 앱 기능, 이 앱이 준 도구 |
| 설정 | 주인 한도: 한 번·하루 최대 송금, buyer 허용, 메모 (`app_owner_limits`가 이 값을 읽음) |
| 허락 시트 | MeshKit 호출이 오면 "에이전트가 허락을 구합니다". 허용/거절 |

## 실행

1. Mac에서 `Ssadassa.xcodeproj`를 Xcode로 연다 (iOS 16 이상).
2. 시뮬레이터: iPhone을 고르고 Run.
3. 내 아이폰: Signing & Capabilities에서 Team을 고르고(무료 Apple ID 가능), bundle identifier를 내 것으로 바꾼 뒤 Run.
   처음에는 설정 → 일반 → VPN 및 기기 관리에서 개발자를 신뢰한다. 무료 계정으로 서명한 앱은 7일 뒤 만료되니 다시 Run.
4. 연결 화면에 kit이 출력한 링크를 붙여 넣는다.
   - 에이전트가 이 Linux 서버에서 돌기 때문에 Mac 시뮬레이터에서도 `--app-tunnel`의 `https://...trycloudflare.com/?k=...` 링크를 쓴다.
     (`http://127.0.0.1:8800`은 에이전트가 같은 Mac에서 돌 때만 된다.)

## 구조

```
Ssadassa/Core/   Foundation만 쓰는 부분 (Linux에서도 빌드): API 클라이언트, 1.5초 polling, 주인 도구 3개, MeshKit 허락 응답
Ssadassa/UI/     SwiftUI 화면
CoreCheck/       Core를 실제 미니앱 서버에 붙여 확인하는 프로그램
Package.swift    Core와 CoreCheck만 빌드하는 SwiftPM 패키지 (Xcode 앱과 별개)
```

접근은 kit의 gate가 받는 쿠키 `miniapp_access=<접근 코드>`를 매 요청에 붙인다. 도구 제공·응답은 kit이 `/miniapp.js`에 넣는
page token이 필요해서, 접근 코드로 그 파일을 받아 token을 읽는다(웹 페이지와 같은 권한).

## 확인한 것 (2026-11-18, Linux, Swift 6.1.2)

- `swift run CoreCheck "<링크>"`를 `ops/preview_app.py`(kit의 `miniapp.app()` + 가짜 에이전트)에 붙여 11개 모두 통과:
  링크 파싱, 틀린 접근 코드 거절, polling, 도구 3개 등록, 에이전트의 한도 읽기·카드·질문, 주인 답이 에이전트 채팅에 도착,
  MeshKit 허락 → 서명 검증된 영수증 (`"source": "owner, in the iOS app"`으로 Swift가 답한 것 확인).
- SwiftUI 화면은 Linux에서 타입 검사를 할 수 없어 `swiftc -parse`(문법)까지만 확인했다. 빌드와 화면은 Xcode에서 확인할 것.
