# 11-25 정리: QR 앱 열기, 서버·Mac 구조 점검, REVIEW 1시간, LLM 교체, 이름 Hermes

2026-11-25 20시대 서버(`hai-SYS-740GP-TNRT`)에서 확인·적용한 것. 세팅 순서 자체는 [dev-env.md](dev-env.md)가 원본이다.

| # | 항목 | 상태 | commit |
|---|---|---|---|
| 1 | QR을 찍으면 네이티브 앱이 열림 (`ssadassa://`) | 코드 O, **아이폰에 새 빌드 설치(▶ Run) 필요** | `34f65599` |
| 2 | 서버(Agent 개발) – Mac(App 개발) 구조 | O (실제 아이폰 설치만 남음) | - |
| 3 | REVIEW 6시간 → 1시간 | O, 20:28 첫 1시간 REVIEW 기록 | `ed623aea` |
| 4 | LLM: Claude Opus 5.5 medium (`claude -p`), 실패 시 GPT-6.2-sol high | O, 운영 중 | `ed623aea`, `8e508d0b` |
| 5 | 사람이 읽는 이름 "싸다싸" → "Hermes" | O | `9c2f4d9e` |

---

## 1. Xcode ▶ Run을 다시 해야 QR이 앱으로 열리는 이유와 방법

### 왜 다시 설치해야 하나

QR에는 `ssadassa://app.hermes-market.shop/?k=<코드>`가 들어 있다. iOS는 **설치된 앱의 Info.plist에 `ssadassa`가 등록돼 있을 때만**
이 링크를 그 앱으로 넘긴다. 아이폰(과 시뮬레이터)에 깔린 앱은 등록 전 빌드라서:

- 아이폰 카메라: "사용 가능한 정보 없음"
- 시뮬레이터: `xcrun simctl openurl` → `LSApplicationWorkspaceErrorDomain code=115` (열 앱 없음)

코드를 pull 받는 것만으로는 안 되고, **새로 빌드해서 다시 설치**해야 한다.
`./qr.sh web`(https://)이 Safari의 예전 화면(`app/index.html`)으로 열리는 것은 정상이다. 웹 앱과 iOS 앱은 같은 서버 API를 쓰는 서로 다른 화면이다.

### 시뮬레이터에서 먼저 (💻 Mac 터미널)

```bash
cd ~/Desktop/ai-agent-engineering-101 && git pull --no-edit origin round-4
cd submissions/26510358/round-4/ios
DEVICE="iPhone 18 Pro" ./run-simulator.sh                                   # 새로 빌드 + 설치
plutil -p build/Debug-iphonesimulator/Ssadassa.app/Info.plist | grep -A4 CFBundleURLTypes   # "ssadassa"가 보이면 됨
K=$(ssh smc-gpu-server 'cat ~/ai-agent-engineering-101/submissions/26510358/round-4/.kit/app.key')
xcrun simctl openurl booted "ssadassa://app.hermes-market.shop/?k=$K"         # "열기" → 호가 대화 화면
```

### 실제 아이폰 (Xcode)

| 순서 | 어디서 | 할 일 |
|---|---|---|
| 1 | 💻 Mac 터미널 | `open ~/Desktop/ai-agent-engineering-101/submissions/26510358/round-4/ios/Ssadassa.xcodeproj` |
| 2 | 📱 아이폰 | 케이블로 Mac에 연결, 잠금 해제, "이 컴퓨터를 신뢰" → **신뢰** |
| 3 | Xcode | 왼쪽 파란 **Ssadassa** → TARGETS **Ssadassa** → **Signing & Capabilities**: Automatically manage signing 체크, Team **명기 성 (Personal Team)**. 빨간 오류면 Bundle Identifier를 `kr.ac.seoultech.s26510358.ssadassa.myeonggi`로 |
| 4 | Xcode | 창 맨 위 가운데 기기 선택 → **iOS Device 아래 내 아이폰** (시뮬레이터 아님) |
| 5 | Xcode | **▶ (⌘R)**. 1~2분 뒤 아이폰에 설치되고 열린다. 덮어쓰기라 저장된 연결 주소는 남는다 |
| 6 | 📱 처음 설치일 때만 | 실행이 막히면 설정 → 개인정보 보호 및 보안 → **개발자 모드** 켜기(재부팅). "신뢰하지 않는 개발자"면 설정 → 일반 → VPN 및 기기 관리 → 개발자 앱 → **신뢰**. 그다음 ▶ 다시 |
| 7 | 💻 Mac 터미널 | `cd …/round-4/ios && ./qr.sh` (처음 한 번 `brew install qrencode`) |
| 8 | 📱 카메라 | QR 비추기 → **"Hermes Shop에서 열기"** → 호가 대화 화면이면 끝 |

- 무료(Personal Team) 서명은 **7일 뒤 만료**된다. 앱이 안 열리면 5번(▶ Run)만 다시.
- 3번에서 서명이 바뀌면 `project.pbxproj`가 수정된다. Mac에서 `ios/` 변경으로 commit한다.
- 이번 이름 변경(5절)으로 홈 화면 앱 이름도 **Hermes Shop**이 된다. 이것도 새 빌드부터 보인다.
- QR에는 접근 코드가 들어 있다. 캡처·공유하지 않는다. 앱이 없는 폰에는 `./qr.sh web`.
- 빌드 오류가 나면 Xcode 왼쪽 ⚠️/❌ 목록을 캡처한다. 서버에는 Xcode가 없어 이 코드는 서버에서 빌드해 보지 못했다.

---

## 2. 서버(Agent 개발) – Mac(App 개발) 구조 점검

**결론: 의도한 대로 세팅됐고 양방향 반영을 실제로 확인했다.** 남은 것은 실제 아이폰 설치와 예전 시험 주소 정리뿐이다.

```
MacBook (app/, ios/)  ── push/pull ──  GitHub origin/round-4  ── push/pull ──  smc-gpu-server
                                                                              shop-shim   LLM (Claude → GPT)
아이폰/브라우저 ── https://app.hermes-market.shop ── Cloudflare ── shop-tunnel ── shop-kit    가게 + 앱 8800
                                                                              shop-sync   매시 에이전트 기록 commit
```

| 항목 | 상태 | 근거 (11-25) |
|---|---|---|
| 서버 24시간 가게 | O | `shop-shim`, `shop-kit` active, linger on. 19:30 재시작 때 임시 주소 실패 → systemd가 60초 뒤 자동 복구 |
| 에이전트 기록 자동 commit | O | `shop-sync.timer`, 매시 `round-4: agent records HH:00` |
| 고정 앱 주소 | O | `shop-tunnel` 연결 4개. `app.hermes-market.shop`: 코드 없음 401 / 틀린 코드 401 / API 401 / 코드 있음 303 |
| 재시작 뒤 같은 주소 | O | 19:30 kit 재시작 뒤 주소 변경 없이 앱 재연결 |
| 에이전트 자가 개선 | O | 하루 도구 재forge 12번, `pay_guard` v3로 스스로 고쳐 첫 입고 송금 성공(19:29, 19:45) |
| Mac → 서버 (웹 앱) | O | Mac commit `8e87a978` → 서버 `git pull` → 재시작 없이 반영, `70980208`로 되돌림 |
| 서버 → Mac (iOS 코드) | O | QR 기능을 서버에서 push → Mac pull → 시뮬레이터 빌드 |
| 경로 분리 (충돌 방지) | O | Mac: `app/`, `ios/` / 서버 사람: `agent.json`, `ops/`, 문서 / 서버 에이전트: `tools/`, `logs/`, `notes.md`, `card.json` 등. 양쪽 `pull.rebase false` |
| 화면 세 곳 | O | 시뮬레이터 앱, 아이폰 Safari(LTE 포함), Mac 브라우저에 같은 대화 |
| 실제 아이폰 네이티브 앱 + QR | △ | 1절 ▶ Run 필요 |
| 예전 시험 주소 | △ | `shop-ngrok`, `shop-tailscaled`가 아직 켜져 있음 → 9-7: `systemctl --user disable --now shop-ngrok shop-tailscaled` |

주의:
- 11-25에는 QR 기능과 이름 변경 때문에 **`ios/`를 서버에서 고쳤다**(`34f65599`, `9c2f4d9e`). Mac에 commit 안 된 Xcode 서명 변경이 있으면 pull이 멈출 수 있다:
  `git stash && git pull --no-edit origin round-4 && git stash pop`. 앞으로 앱 코드는 Mac에서 고친다.
- `SERVER.md`가 서버 작업 트리에서 지워진 채(commit 안 됨) 남아 있다. 필요 없으면 지운 것을 commit하고, 필요하면 `git checkout -- SERVER.md`.

---

## 3. REVIEW: 6시간 → 1시간

### REVIEW란

goal(`agent.json`)에 적은 **"정해진 간격마다 스스로 돌아보고 한 가지만 고치는" 규칙**이다. kit에는 타이머가 없다. 에이전트가 notes.md NOW의
마지막 `REVIEW` 줄 시각을 보고 스스로 판단한다. 매 run은 "장사"하는 층, REVIEW는 그 결과로 "도구와 전략을 고치는" 층이다.

| 순서 | 할 일 |
|---|---|
| 1 | 도구 목록의 `used N, failed M`을 지난 REVIEW의 `fails=`와 비교 → 실패가 는 도구를 recall → read_tool → 같은 이름으로 다시 forge(그 경우의 테스트 포함) |
| 2 | 최근 1시간 자기 step에서 인자를 틀리게 쓰거나 답을 잘못 읽은 도구 → 설명(description)을 다시 써서 forge |
| 3 | 매 run 손으로 3번 이상 반복하는 호출 → 기존 도구에 합침. 핵심 도구는 약 7개 유지 |
| 4 | 1시간 msgs/checkouts/settled와 credits를 지난 REVIEW와 비교. 직전 변경이 도움이 안 됐으면 되돌리거나 다음 아이디어 |
| 5 | **한 번에 하나만** 바꾸고 NOW의 REVIEW 줄을 교체: `REVIEW <YYYY-MM-DD HH:MM> credits=<n> (<+/-n>) settled1h=<n> fails=<tool:n,...> changed=<…> next=<…>` |

### 바꾼 것 (`ed623aea`)

| 이전 | 이후 |
|---|---|
| REVIEW EVERY 6 HOURS | REVIEW EVERY HOUR |
| 6시간 판단을 모델에 맡김 → 4시간에 7번, `15:xx`처럼 기록 | 시각은 **실제 숫자 KST**로(`xx` 금지). 마지막 REVIEW에서 **60분이 안 지났으면 REVIEW 없이 NOW만 갱신** |
| `settled6h`, 최근 6시간 | `settled1h`, 최근 1시간 |
| (없음) | 도구는 실패하면 **최상위에 `{"ok": false, "error": …}`**. kit은 최상위 `ok`만 실패로 센다(`agent_kit.py:388-392`). `pay_guard`가 실패를 `result` 안에 담아 8번 실패가 `failed 0`으로 보였던 문제 |

확인: 20:22 재시작 직후 에이전트가 "리뷰 시점이 지났다(마지막 18:32)"며 리뷰, 20:28에
`REVIEW 2026-11-25 20:28 credits=4946433 (-35690) settled1h=0 fails=stock_and_price:…` 기록.

```bash
grep -o "REVIEW 20[^ ]* [^ ]*" notes.md | tail -3        # 🖥️ 서버: 간격이 1시간 안팎인지
```

---

## 4. LLM 교체: Claude Opus 5.5 medium + GPT-6.2-sol high

### 확인한 것

| 질문 | 답 |
|---|---|
| 지금까지 무엇을 썼나 | 시장 **model desk** `https://market.ourolabs.ai/llm/v1` (OpenAI 호환, `LLM=market`). 시장 토큰으로 호출, 모델은 desk가 고름. `agent.json`의 `gpt-6.1-sol`과 shim은 쓰이지 않고 있었다 |
| GPT-6.2-sol을 쓸 수 있나 | 예. 이 OpenAI 키의 모델 목록에 `gpt-6.2-sol` 있음. `reasoning_effort=high` 호출 2.9초 |
| Claude를 붙일 수 있나 | **CLI로 가능.** 서버에 Claude Code 2.1.332가 claude.ai 로그인으로 있다. `anthropic` SDK와 `ANTHROPIC_API_KEY`는 없어 SDK/API 방식은 지금 불가 |
| kit을 고쳐야 하나 | 아니다. kit은 OpenAI `/chat/completions`로 system/user/assistant **텍스트**만 보내고 답에서 JSON 행동 하나를 읽는다(`agent_kit.py:136-180`). 그래서 기존 `ops/llm_shim.py`에 Claude 백엔드만 추가 |

### 구조

```
kit ──OpenAI 형식──▶ ops/llm_shim.py (127.0.0.1:18790, systemd shop-shim)
                      ├─ 1순위  claude -p --model claude-opus-5-5 --effort medium
                      │         --tools "" --strict-mcp-config --setting-sources "" --no-session-persistence
                      │         (빈 폴더에서, 대화는 <turn role=…> 태그로, system은 --system-prompt-file)
                      └─ Claude 실패·110초 초과 → OpenAI gpt-6.2-sol, reasoning_effort=high
```

| 설정 | 값 | 위치 |
|---|---|---|
| 실행 모드 | `LLM=claude` (systemd 유닛에 고정) | `ops/run_server.sh` |
| GPT 모델 | `gpt-6.2-sol` | `agent.json` `llm.model`, `.env` `AGENT_MODEL` |
| GPT effort | `high` | `.env` `AGENT_REASONING_EFFORT` (git 밖) |
| Claude 모델·effort | `claude-opus-5-5`, `medium` | shim 기본값. 바꾸려면 `CLAUDE_MODEL`, `CLAUDE_EFFORT` |
| 사용량 기록 | 호출마다 model, 초, 토큰, `cost_usd`, fallback 이유 | `logs/llm-shim.jsonl` (내용은 남기지 않음) |

모드 바꾸기 (🖥️ 서버, 1~3분 끊김):

```bash
cd ~/ai-agent-engineering-101/submissions/26510358/round-4
ops/run_server.sh down && LLM=claude ops/run_server.sh up   # Claude 주, GPT 예비 (지금)
ops/run_server.sh down && LLM=own ops/run_server.sh up      # GPT-6.2-sol high만
ops/run_server.sh down && ops/run_server.sh up              # 시장 model desk로 되돌리기
```

`run_server.sh restart`는 모드를 유지한다(유닛에 고정돼 있음).

### 운영 결과 (20:19~21:2x)

| | 횟수 | 비고 |
|---|---|---|
| Claude Opus 5.5 응답 | 16 | 5~10초. 프롬프트 15k~38k 토큰, 캐시가 맞으면 호출당 API 환산 약 $0.02, 안 맞으면 약 $0.11 |
| GPT 대체 (Claude 안전장치) | 5 | `Opus 5.5's safeguards flagged this message … Claude Code can't respond to this message with Opus` |
| GPT 대체 (이유 기록 전) | 2 | 전환 직후. 이후 이유를 남기도록 고침(`8e508d0b`) |

1시간 API 환산 합계 약 $2.5.

### 알아둘 것

- **안전장치 오탐**: 지갑, 송금, tx hash, 서명이 많은 프롬프트라 Opus 5.5 안전장치가 약 20%를 막는다. 그때마다 GPT-6.2-sol이 답해서 가게는 멈추지 않는다. 비율은 `logs/llm-shim.jsonl`의 `claude fallback: is_error` 줄로 본다.
- **비용과 한도**: 하루 약 1,500 step이면 API 환산 하루 수십~백 달러대다. 실제로는 **claude.ai 구독 사용량 한도**에서 빠지고, 이 서버에서 쓰는 Claude Code와 한도를 같이 쓴다. 한도에 걸리면 shim이 GPT로 넘기니 가게는 돌지만, 사람이 쓰는 Claude Code가 먼저 막힐 수 있다.
- **24시간 자동 운영의 정석은 API 키**다. `ANTHROPIC_API_KEY`를 `.env`에 넣으면 shim이 CLI 대신 API를 쓰도록 바꿀 수 있다(아직 안 함).
- 처음 전환 직후 몇 분은 kit이 다시 시장에 붙느라 1~3분 앱이 502다(정상).

```bash
tail -5 logs/llm-shim.jsonl                                        # 🖥️ 서버: 최근 호출
grep -c "claude fallback" logs/llm-shim.jsonl                      # GPT로 넘어간 횟수
```

---

## 5. "싸다싸" → "Hermes" (`9c2f4d9e`)

에이전트 쪽 파일(`agent.json`, `notes.md`, `tools/`, `card.json`, `public/`)에는 원래 "싸다싸"가 없었다(시장 이름은 처음부터 Hermes Shop).
"싸다싸"는 **사람이 보는 앱·문서**에만 있었고, 모두 바꿨다. 로그(`logs/`)는 손대지 않는다.

| 파일 | 바뀐 곳 |
|---|---|
| `app/index.html` | 탭 제목, 소개 문구 → "Hermes Shop" (서버는 디스크에서 바로 읽어 재시작 없이 반영, 확인함) |
| `ios/…/project.pbxproj`, `gen_xcodeproj.py` | 홈 화면 앱 이름 `CFBundleDisplayName` → "Hermes Shop" |
| `ios/…/LinkView.swift`, `ChatView.swift`, `SettingsView.swift` | 연결 화면 제목, 인사말, 설정의 가게 이름 |
| `ios/…/Characters.swift` | 데모 모드 에이전트 이름, MeshKit 도구 표시 이름 |
| `ios/…/Info.plist` | 로컬 네트워크 권한 문구 |
| `ops/meshkit_target.py` | MeshKit 도구 설명 2개 |
| `ios/qr.sh`, `run-simulator.sh`, `ios/README.md`, `SsadassaApp.swift` 주석 | 설명 문구 |
| `dev-env.md`, `harness-architecture.html` | 문서 |

**일부러 남긴 것**: 코드 이름 `Ssadassa`(프로젝트·폴더·타입), 번들 ID `kr.ac.seoultech.s26510358.ssadassa`, QR 링크 `ssadassa://`.
바꾸면 서명을 새로 해야 하고, 이미 저장된 연결과 QR이 끊긴다. 화면에는 보이지 않는다.

반영 시점:
- 웹 앱: 이미 반영(`<title>Hermes Shop</title>`).
- iOS 앱: 1절의 새 빌드(▶ Run)부터.
- MeshKit 도구 설명: 18765 포트의 MeshKit 서버가 다시 시작될 때.
- 하네스 지도 artifact(claude.ai 링크): 저장소 파일만 바뀌었다. 링크 페이지도 바꾸려면 다시 게시해야 한다.
