# 개발 환경: 서버(smc-gpu-server) + MacBook

가게(kit)와 에이전트 개발은 SMC 서버에서, 앱 개발(`app/`, `ios/`)은 Mac에서 한다. 앞부분 1~10단계는 **처음 세팅(또는 다시 세팅)할 때
위에서부터 붙여 넣는 순서**이고, 뒷부분 "참고"는 이유와 평소 흐름이다. `scripts/round4/agent_kit.py`, `miniapp.py`를 읽고 정리했다.

```
MacBook (앱 개발)                     GitHub origin/round-4               smc-gpu-server (가게 24시간 + 에이전트 개발)
  app/, ios/ 수정         ── push ──▶                    ◀── push ──  agent.json, ops/ 수정 (사람)
  preview_app.py, Xcode                                              tools/, logs/, notes.md … (에이전트, 매시 자동 commit)
  ssh -L 8800 → 실제 가게  ◀── pull ──          ── pull ──▶  systemd --user:
                                                                       shop-kit         가게 (시장 A2A + 앱 8800)
아이폰 ──https://app.hermes-market.shop──▶ Cloudflare ──▶          shop-tunnel      Cloudflare named tunnel → 앱 8800
                                                                       shop-sync.timer  매시 에이전트 기록 commit·push
```

### 진행 상황 (2026-11-25 16:5x 서버에서 확인)

| 단계 | 상태 | 근거 |
|---|---|---|
| 1. SSH 별칭 | O 완료 | 이 서버에 SSH로 들어와 개발 중 |
| 2. 가게 동작 | O 완료 | `shop-kit` active (11-25 15:10:49부터) |
| 3. git 설정·push 인증 | O 완료 | `pull.rebase=false`, gh 로그인, push 성공 |
| 4. 에이전트 기록 첫 commit | O 완료 | `95fa125e` |
| 5. 자동 commit 타이머 | O 완료 | `shop-sync.timer` 15:06, 16:00 성공 |
| 6. goal REVIEW 규칙 | O 완료 | `notes.md`에 REVIEW 줄. 시각을 `15:xx`로 뭉개 적어 1시간 만에 다시 돔(참고 C) |
| 7. Mac 저장소·미리보기 | O 완료 | Mac commit merge(`caa5c3e8`), `preview_app.py` 응답 |
| 8. Mac에서 실제 가게 | O 완료 | `ssh -L` 터널로 웹 앱·시뮬레이터가 붙고 에이전트가 답함(15:49) |
| 9. 고정 앱 주소 (Cloudflare + hermes-market.shop) | △ 진행 | 11-25 17시대: 가비아 Active, 네임서버를 `daisy`/`michael.ns.cloudflare.com`으로 변경, DNSSEC 없음. Cloudflare "이름 서버 전파 대기 중". **아래 "금요일에 이어서 하기"의 F1부터** |
| 10. 실제 아이폰에 앱 설치 | △ 진행 | Xcode 서명 Team 선택까지. 아이폰 연결부터 남음 |
| 세팅 끝. 웹 앱 한 바퀴 | O 완료 | Mac `8e87a978`(표시 추가) → 서버가 재시작 없이 표시를 내줌 → Mac `70980208`(revert) → 서버 pull 뒤 표시 사라짐 |
| 정리 대상 | - | `shop-ngrok`(월 20,000요청 한도), `shop-tailscaled`(개인 Tailscale, 쓰지 않기로 함)는 9-7에서 끈다 |

### 금요일(11-27)에 이어서 하기

11-25에 9단계 중 가비아 쪽(9-1, 9-2의 네임서버 변경)까지 했다. 금요일에는 **F0 → F5 순서로 위에서부터** 붙여 넣는다.
F0에서 1~8단계가 그대로 살아 있는지 한 번에 보고, F1에서 도메인이 Cloudflare로 넘어갔는지 확인한 뒤 9-3부터 진행한다.

#### F0. 🖥️ 서버 터미널 — 1~8단계 건강 검진 (한 블록)

```bash
cd ~/ai-agent-engineering-101 && R=submissions/26510358/round-4
hostname                                                     # hai-SYS-740GP-TNRT 여야 한다 (Mac이면 ssh smc-gpu-server 부터)
echo "== 서비스";  for u in shop-kit shop-sync.timer shop-tunnel shop-ngrok shop-tailscaled; do printf "%-16s %-9s %s\n" $u "$(systemctl --user is-active $u)" "$(systemctl --user is-enabled $u 2>/dev/null)"; done
echo "== 가게";    $R/ops/run_server.sh status | head -12
echo "== git";     git fetch -q origin; git status -sb | head -1; git --no-pager log --oneline -3 | cut -c1-90
echo "== 타이머";  journalctl --user -u shop-sync --since "-3h" --no-pager | grep -cE "Finished"; journalctl --user -u shop-sync --since "-3h" --no-pager | grep -E "Failed|error" | tail -2
echo "== REVIEW";  grep -o "REVIEW 20[^ ]* [^ ]*" $R/notes.md | tail -3
echo "== 앱 8800"; K=$(cat $R/.kit/app.key); curl -s -o /dev/null -w "local 코드없이 %{http_code}\n" http://127.0.0.1:8800/; curl -s -o /dev/null -w "local 코드와함께 %{http_code}\n" "http://127.0.0.1:8800/?k=$K"
```

| 봐야 할 것 | 정상 | 아니면 |
|---|---|---|
| `shop-kit`, `shop-sync.timer` | `active enabled` | `LLM=claude run_server.sh up` (2단계) / 5단계 블록 |
| `run_server.sh status` | `shop-kit active`, 최근 `[mind]` 줄 | `tail -50 $R/.kit/kit.log`로 원인 |
| git | `## round-4...origin/round-4` (ahead/behind 없음) | `git pull --no-edit origin round-4 && git push origin round-4` |
| 타이머 | `Finished`가 2 이상, 오류 없음 | `journalctl --user -u shop-sync -n 30` (참고 E) |
| 앱 8800 | 코드없이 `401`, 코드와함께 `303` | kit이 꺼져 있거나 재시작 중 |

`shop-tunnel`은 아직 없으니 `inactive`가 정상이다(9-4에서 만든다).

#### F1. 💻 Mac 터미널 — 도메인이 Cloudflare로 넘어갔는지

```bash
dig +short NS hermes-market.shop
```

- `daisy.ns.cloudflare.com.` / `michael.ns.cloudflare.com.` 두 줄 → 🌐 Cloudflare 대시보드 `hermes-market.shop` 개요가 **활성(Active)**인지 보고 F2로.
  "전파 대기 중"이면 그 화면의 **이름 서버 확인(Check nameservers)**을 한 번 누른다.
- 빈 칸 또는 `ns.gabia…` → 🌐 가비아 도메인 상세 → 네임서버/DNS호스트/DNSSEC 탭의 1차·2차가 `daisy…`, `michael…`인지
  다시 확인(아니면 **설정** 버튼으로 적용). 맞는데도 48시간이 지나도 그대로면 가비아 고객센터.

#### F2. 9-3 → 9-4 (서버) — 아래 9단계 본문의 블록을 그대로

1. 🖥️ 9-3: `cloudflared tunnel login` → 출력된 주소를 🌐 Mac 브라우저에서 열고 `hermes-market.shop` **Authorize** → 나머지 세 줄.
2. 🖥️ 9-4: 블록 통째로. 끝에 `active`와 1 이상의 숫자.

#### F3. 💻 Mac 터미널 — 9-5 보안 확인

9-5 블록을 그대로. **401 / 401 / 401 / 303**이고 마지막 줄에 `아이폰에 넣을 주소: https://app.hermes-market.shop/?k=…`가 나오면 성공.

#### F4. 📱 앱에서 작동 확인 (이것이 최종 확인)

| 순서 | 어디서 | 할 일 | 성공 기준 |
|---|---|---|---|
| 1 | 🌐 Mac 브라우저 | F3 마지막 줄의 주소를 연다 | Hermes Shop 웹 앱이 뜨고 "시장에서 거래 중" |
| 2 | 🌐 같은 화면 | **지금 잔고와 순위는?** 버튼 | 1~2분 안에 에이전트가 숫자로 답함 |
| 3 | 💻 Mac 시뮬레이터 | 아래 명령 (ssh 터널 없이 공개 주소로) | 싸다싸 가게 앱이 연결되고 대화가 보임 |
| 4 | 📱 실제 아이폰 | 앱(10단계로 설치) → **링크 붙여넣기** → 같은 주소 → **연결** | 대화 화면, 질문에 답이 옴 |
| 5 | 📱 실제 아이폰 | **와이파이 끄고 LTE**로 다시 | 그래도 붙음 (= 밖에서도 됨) |
| 6 | 🖥️ 서버 | `run_server.sh restart` → 3분 뒤 아이폰 앱 새로고침 | 주소를 다시 넣지 않아도 다시 붙음 (= 고정 주소) |

3번 명령 (💻 **Mac 터미널**):

```bash
K=$(ssh smc-gpu-server 'cat ~/ai-agent-engineering-101/submissions/26510358/round-4/.kit/app.key')
cd ~/Desktop/ai-agent-engineering-101/submissions/26510358/round-4/ios
DEVICE="iPhone 18 Pro" ./run-simulator.sh "https://app.hermes-market.shop/?k=$K"
```

서버에서 앱이 실제로 붙었는지 보기 (🖥️ **서버 터미널**, 아이폰 앱을 켜 둔 채로):

```bash
journalctl --user -u shop-tunnel --since "-5min" --no-pager | tail -5     # 오류 없으면 됨
grep -E "\[mind\] reply" ~/ai-agent-engineering-101/submissions/26510358/round-4/.kit/kit.log | tail -3   # 방금 질문에 대한 에이전트 답
```

4번에서 앱이 아직 폰에 없으면 10단계(Xcode로 설치)를 먼저 한다.

#### F5. 정리

1. 🖥️ 9-7: `systemctl --user disable --now shop-ngrok shop-tailscaled` (예전 시험 주소 끄기).
2. 이 문서의 진행 상황 표에서 9단계(와 10단계)를 O로 바꾸고 commit·push.

### 어느 터미널에서 치나

| 표시 | 무엇 | 여는 법 | 구분 |
|---|---|---|---|
| 🖥️ **서버 터미널** | smc-gpu-server 안의 셸 | Mac에서 `ssh smc-gpu-server`, VSCode Remote-SSH 터미널, 서버의 Claude Code | `hostname` → `hai-SYS-740GP-TNRT` |
| 💻 **Mac 터미널** | Mac 자체의 Terminal/iTerm (SSH로 들어가지 않은 상태) | Mac에서 새 터미널 | `hostname` → Mac 이름 |
| 🌐 **브라우저** / 📱 **아이폰** | 명령 없이 화면에서 하는 일 | | |

- 블록은 통째로 붙여 넣어도 된다. 바꿔야 하는 값은 블록 첫 줄에 `# ← 바꾸기`로 표시했다.
- 명령은 bash 문법이다(서버 기본 셸 bash, Mac zsh 모두 동작). 서버에서 fish를 쓰고 있으면 먼저 `bash`.
- 저장소 경로: 서버 `~/ai-agent-engineering-101`, Mac `~/Desktop/ai-agent-engineering-101`.
- 접근 코드(`.kit/app.key`, 주소의 `?k=`)와 토큰은 채팅방·이슈·commit·스크린샷에 올리지 않는다.

---

## 1단계. 💻 Mac: 서버 SSH 별칭 — O 완료

`~/.ssh/config`에 아래가 있으면 끝이다(없으면 편집기로 추가).

```sshconfig
Host smc-gpu-server
    HostName <서버 주소>
    User myeonggi
    ServerAliveInterval 30
```

▶ 💻 **Mac 터미널** — 확인

```bash
ssh smc-gpu-server hostname          # hai-SYS-740GP-TNRT
```

## 2단계. 🖥️ 서버: 가게 켜기·확인 — O 완료

처음 세팅이면 git 밖에 있어야 하는 파일(지갑 키, claim code)과 도구를 먼저 확인한다. 이미 돌고 있으면 `status`만 본다.

▶ 🖥️ **서버 터미널**

```bash
cd ~/ai-agent-engineering-101 && R=submissions/26510358/round-4
git checkout round-4
ls $R/*_wallet.key $R/.kit/owner.env             # 둘 다 있어야 한다(없으면 Mac에서 옮겨 온다. 지갑 키가 곧 가게)
command -v cloudflared && ~/.venvs/round4/bin/python --version
loginctl show-user $USER -p Linger               # Linger=yes 여야 로그아웃·재부팅 뒤에도 돈다
LLM=claude $R/ops/run_server.sh up               # 이미 떠 있으면 "already up". 두뇌: Claude Opus 5.5 medium(claude -p), 실패 시 gpt-6.2-sol high. LLM=own 이면 GPT만, 생략하면 시장 model desk
$R/ops/run_server.sh status                      # shop-kit active
```

- `Linger=no`면 `loginctl enable-linger $USER`. `cloudflared`가 없으면
  `mkdir -p ~/.local/bin && curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o ~/.local/bin/cloudflared && chmod +x ~/.local/bin/cloudflared`.
- 같은 지갑 키로 두 곳에서 kit을 띄우지 않는다(Mac에서는 절대 `agent_kit.py run` 하지 않는다).

## 3단계. 🖥️ 서버: git 설정과 push 인증 — O 완료

▶ 🖥️ **서버 터미널**

```bash
cd ~/ai-agent-engineering-101
git config pull.rebase false                     # pull은 merge. push된 commit을 다시 쓰지 않는다(AGENTS.md)
gh auth status || gh auth login                  # 대화형. 브라우저 인증
git push --dry-run origin round-4                # 오류 없이 끝나면 OK
```

## 4단계. 🖥️ 서버: 쌓인 에이전트 기록 한 번 commit — O 완료

5단계 타이머를 처음 켜기 전에만 한다(첫 자동 commit이 며칠 치를 몰아 담지 않게).

▶ 🖥️ **서버 터미널**

```bash
cd ~/ai-agent-engineering-101 && R=submissions/26510358/round-4
git add $R/tools $R/logs $R/notes.md $R/card.json $R/customers.jsonl $R/stock.json $R/sales.jsonl $R/pay_log.json $R/public
git status --short $R                            # staged(초록)에 *.key, .kit/ 가 없는지 눈으로 확인
git commit -m "round-4: agent records up to $(date '+%m-%d %H:%M') from the server run"
git pull --no-edit origin round-4 && git push origin round-4
```

## 5단계. 🖥️ 서버: 에이전트 기록 자동 commit 타이머 — O 완료

매시 정각에 에이전트가 쓰는 경로만 commit → pull(Mac의 앱 변경을 받음) → push.

▶ 🖥️ **서버 터미널** (블록 전체)

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/shop-sync.service <<'EOF'
[Unit]
Description=round-4: commit and push the agent's records
[Service]
Type=oneshot
WorkingDirectory=%h/ai-agent-engineering-101
ExecStart=/bin/bash -c 'R=submissions/26510358/round-4; \
  git add $$R/tools $$R/logs $$R/notes.md $$R/card.json $$R/customers.jsonl $$R/stock.json $$R/sales.jsonl $$R/pay_log.json $$R/public; \
  git diff --cached --quiet || git commit -q -m "round-4: agent records $$(date "+%%m-%%d %%H:%%M")"; \
  git pull -q --no-rebase --no-edit origin round-4 && git push -q origin round-4'
EOF
cat > ~/.config/systemd/user/shop-sync.timer <<'EOF'
[Timer]
OnCalendar=hourly
Persistent=true
[Install]
WantedBy=timers.target
EOF
systemctl --user daemon-reload && systemctl --user enable --now shop-sync.timer
systemctl --user start shop-sync && journalctl --user -u shop-sync -n 3 --no-pager
```

- 유닛 파일 안에서는 systemd가 `$`, `%`를 먼저 해석하므로 `$$`, `%%`로 적었다.
- 사람이 고치는 `agent.json`, `ops/`는 타이머가 add하지 않는다(사람이 직접 commit).

## 6단계. 🖥️ 서버: goal에 6시간 REVIEW 규칙 — O 완료

`agent.json` goal의 `EVERY RUN` 문단 뒤에 `REVIEW EVERY 6 HOURS` 문단이 들어 있다(commit `fa4385e0`). goal은 kit 시작 때만 읽으므로
goal을 고칠 때마다 아래로 반영한다.

▶ 🖥️ **서버 터미널**

```bash
cd ~/ai-agent-engineering-101 && R=submissions/26510358/round-4
python3 -c "import json; json.load(open('$R/agent.json'))" && echo "json ok"
git add $R/agent.json && git commit -m "round-4: goal - <무엇을 왜 바꿨는지 한 줄>"   # ← 메시지 바꾸기
git push origin round-4
$R/ops/run_server.sh restart
systemctl --user show shop-kit -p ActiveEnterTimestamp     # 시각이 방금으로 바뀌었으면 재시작된 것
```

확인: 몇 분 뒤 `grep REVIEW $R/notes.md`. 아이폰 앱은 `app.hermes-market.shop`(9단계)이라 재시작 뒤에도 주소를 바꿀 필요가 없다.

## 7단계. 💻 Mac: 저장소와 미리보기 — O 완료

▶ 💻 **Mac 터미널**

```bash
cd ~/Desktop/ai-agent-engineering-101
pkill -f agent_kit.py; pgrep -fl agent_kit.py    # 아무것도 안 나와야 한다
git config pull.rebase false
git checkout round-4 && git pull origin round-4
```

pull이 `would be overwritten by merge`로 멈추면(Mac에 남은 에이전트 파일) 버리지 말고 stash로 치운 뒤 다시 pull한다.

```bash
cd ~/Desktop/ai-agent-engineering-101 && R=submissions/26510358/round-4
git stash push -u -m "mac leftovers" -- $R ":(exclude)$R/app" ":(exclude)$R/ios"
git pull origin round-4                          # agent.json 충돌이면 아래 세 줄
# git checkout --theirs $R/agent.json && git add $R/agent.json && git commit --no-edit
git push origin round-4
```

미리보기 환경(처음 한 번)과 실행:

```bash
command -v uv || { curl -LsSf https://astral.sh/uv/install.sh | sh; }
[ -x ~/.venvs/round4/bin/python ] || uv venv --python 3.12 ~/.venvs/round4
VIRTUAL_ENV=~/.venvs/round4 uv pip install "a2a-sdk[http-server]" uvicorn httpx eth-account coincurve
~/.venvs/round4/bin/python submissions/26510358/round-4/ops/preview_app.py
```

출력된 주소(`[preview] http://127.0.0.1:188xx/`)를 브라우저로 연다. 18800이 쓰이고 있으면 다음 빈 포트를 쓴다
(VSCode Remote-SSH가 서버 포트를 Mac으로 자동 전달해 18800, 18801이 차 있을 수 있다). 채팅을 보내면 도구 목록이 돌아오면 정상. 끌 때 `Ctrl-c`.

## 8단계. 💻 Mac: 실제 가게에 붙기 (개발용, 한도 없음) — O 완료

▶ 💻 **Mac 터미널 — 탭 A** (출력 없이 멈춘 상태가 정상. 개발하는 동안 켜 둔다. 끌 때 `Ctrl-c`)

```bash
ssh -N -L 8800:127.0.0.1:8800 smc-gpu-server
```

▶ 💻 **Mac 터미널 — 탭 B**

```bash
K=$(ssh smc-gpu-server 'cat ~/ai-agent-engineering-101/submissions/26510358/round-4/.kit/app.key')
open "http://127.0.0.1:8800/?k=$K"                                       # 웹 앱
cd ~/Desktop/ai-agent-engineering-101/submissions/26510358/round-4/ios
DEVICE="iPhone 18 Pro" ./run-simulator.sh "http://127.0.0.1:8800/?k=$K"  # iOS 시뮬레이터 (기종 목록: xcrun simctl list devices available | grep iPhone)
```

- 탭 A가 `Address already in use`면 Mac에서 8800을 쓰는 것이 있다(`lsof -nP -iTCP:8800 -sTCP:LISTEN`). VSCode 포트 탭에 8800이 이미
  있으면 탭 A 없이 탭 B만 쳐도 된다.
- 터널을 닫아도 가게에는 영향이 없다. Mac의 `127.0.0.1:8800`만 끊긴다.
- Xcode 콘솔에 쏟아지는 `UIKBDynamicRenderFactory`, `CHHapticPattern`, `TUIPredictionViewCell` 줄은 시뮬레이터 키보드·햅틱 소음이다(앱 문제 아님).

## 9단계. 고정 앱 주소: Cloudflare tunnel + `hermes-market.shop` — △ 진행

아이폰이 어디서든(LTE 포함) **`https://app.hermes-market.shop/?k=<코드>`**로 가게 앱에 붙는다. 한도가 없고, kit 재시작·서버 재부팅 뒤에도
주소가 그대로다. 아이폰에 다른 앱(VPN 등)은 필요 없다.

```
아이폰 ──https──▶ Cloudflare (app.hermes-market.shop) ──named tunnel──▶ 서버 cloudflared (shop-tunnel) ──▶ 127.0.0.1:8800 kit
```

- 도메인: 가비아에서 구매(11-25, 첫해 2,200원). 네임서버만 Cloudflare로 넘긴다.
- **kit의 `--app-tunnel`은 끄지 않는다.** kit은 `--app-tunnel`이나 `--app-host 0.0.0.0`일 때만 접근 코드를 켠다(`agent_kit.py` 846–847행).
  `run_server.sh`의 기본 `APP_FLAGS`(`--app 8800 --app-tunnel`)를 그대로 둔다.

### 9-1. 🌐 가비아: 자동 연장 끄기, 개인정보 보호

1. My가비아 → **도메인 관리** → `hermes-market.shop`.
2. **자동 연장**을 끈다(2년째는 할인 없이 약 65,000원. Round 4는 그 전에 끝난다).
3. **Whois 정보 보호(개인정보 보호)** 항목이 있으면 켠다. 이름·전화가 공개 조회되지 않게.
4. **DNSSEC**이 켜져 있으면 끈다(켜져 있으면 9-2의 네임서버 변경이 막힌다).

### 9-2. 🌐 Cloudflare에 도메인 추가 → 🌐 가비아에서 네임서버 변경

1. dash.cloudflare.com → **도메인 → 도메인 추가(Add a domain)** → `hermes-market.shop` → **Free** 플랜 → DNS 레코드 화면은 **계속(Continue)**.
2. 마지막 화면의 **Cloudflare 네임서버 2개**(`○○○.ns.cloudflare.com`)를 복사한다.
3. My가비아 → `hermes-market.shop` → **네임서버 설정** → 1차·2차에 위 2개를 넣고 3차 이하는 비운 뒤 저장.
4. Cloudflare 대시보드에서 **Check nameservers** → 상태가 **활성(Active)**이 될 때까지 기다린다(몇 분~몇 시간, 메일이 온다).

▶ 💻 **Mac 터미널** — 넘어갔는지 확인 (Cloudflare 네임서버 2개가 나오면 다음으로)

```bash
dig +short NS hermes-market.shop
```

아무것도 안 나오면 아직이다. 구매 직후에는 .shop 등록소에 반영되기까지 시간이 걸린다(11-25 16:5x 확인 시 아직 미반영).

### 9-3. 🖥️ 서버: tunnel 만들기 (한 번)

▶ 🖥️ **서버 터미널** — 첫 줄이 출력하는 `https://dash.cloudflare.com/argotunnel?...` 주소를 🌐 **Mac 브라우저**에서 열고
**`hermes-market.shop`**을 골라 **Authorize**. 그러면 서버 터미널이 저절로 다음 줄로 넘어간다.

```bash
cloudflared tunnel login                                         # ~/.cloudflared/cert.pem 생성
cloudflared tunnel create hermes-shop                            # ~/.cloudflared/<UUID>.json 생성 (tunnel 비밀키)
cloudflared tunnel route dns hermes-shop app.hermes-market.shop  # Cloudflare DNS에 app CNAME 생성
cloudflared tunnel list
```

- 목록에 `hermes-shop`이 보이면 성공. Cloudflare 대시보드 **DNS**에 `app` CNAME(`<UUID>.cfargotunnel.com`)이 생긴다.
- `~/.cloudflared/`의 `cert.pem`, `<UUID>.json`은 비밀이다. 저장소 밖이라 git에 올라가지 않는다. 지우지 않는다.
- Authorize 화면에 도메인이 안 보이면 9-2의 Active가 아직이다.

### 9-4. 🖥️ 서버: 설정 파일과 상시 실행 서비스

▶ 🖥️ **서버 터미널** (블록 전체)

```bash
CRED=$(ls ~/.cloudflared/*.json | head -1); echo "credentials: $CRED"
cat > ~/.cloudflared/hermes-shop.yml <<EOF
tunnel: hermes-shop
credentials-file: $CRED
ingress:
  - hostname: app.hermes-market.shop
    service: http://127.0.0.1:8800
  - service: http_status:404
EOF
cloudflared tunnel --config ~/.cloudflared/hermes-shop.yml ingress validate

mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/shop-tunnel.service <<'EOF'
[Unit]
Description=round-4: https://app.hermes-market.shop for the shop app (Cloudflare named tunnel to 127.0.0.1:8800)
After=network-online.target
StartLimitIntervalSec=0
[Service]
ExecStart=%h/.local/bin/cloudflared tunnel --no-autoupdate --config %h/.cloudflared/hermes-shop.yml run
Restart=always
RestartSec=10
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload && systemctl --user enable --now shop-tunnel
sleep 8; systemctl --user is-active shop-tunnel
journalctl --user -u shop-tunnel -n 30 --no-pager | grep -c "Registered tunnel connection"   # 1 이상이면 연결됨
```

- `ingress validate`가 `OK`, `is-active`가 `active`여야 한다.
- `run_server.sh up/down/restart`는 이 서비스를 건드리지 않는다. kit이 재시작하는 1~3분은 이 주소가 502를 낸다(정상).

### 9-5. 💻 Mac: 보안 확인 (코드 없으면 막히는지)

서버의 로컬 DNS는 새 도메인을 늦게 알 수 있어서(`run_server.sh` 주석 참고) 확인은 Mac에서 한다.

▶ 💻 **Mac 터미널**

```bash
K=$(ssh smc-gpu-server 'cat ~/ai-agent-engineering-101/submissions/26510358/round-4/.kit/app.key')
curl -s -o /dev/null -w "코드 없이:   %{http_code}  (401이어야 함)\n" https://app.hermes-market.shop/
curl -s -o /dev/null -w "틀린 코드:   %{http_code}  (401이어야 함)\n" "https://app.hermes-market.shop/?k=wrong"
curl -s -o /dev/null -w "API 코드없이: %{http_code}  (401이어야 함)\n" https://app.hermes-market.shop/api/state
curl -s -o /dev/null -w "코드와 함께: %{http_code}  (303이어야 함)\n" "https://app.hermes-market.shop/?k=$K"
echo "아이폰에 넣을 주소: https://app.hermes-market.shop/?k=$K"
```

- **코드 없이 200이 나오면 즉시 서버에서 `systemctl --user disable --now shop-tunnel`** 하고 kit이 `--app-tunnel`로 떠 있는지 본다.
- `000`이면 DNS가 아직 퍼지는 중이다. 몇 분 뒤 다시.
- `502`면 kit이 재시작 중이거나 꺼져 있다(서버 `run_server.sh status`).

### 9-6. 📱 아이폰에 넣기

1. 마지막 줄의 주소를 아이폰으로 보낸다(같은 Apple ID면 Mac에서 복사 → 아이폰에서 붙여넣기).
2. 싸다싸 가게 앱 → **링크 붙여넣기** → **연결**. (Safari로 열면 가게 웹 앱이 열린다.)
3. 와이파이를 끄고 LTE로도 붙는지 본다.

**QR로 넣기** (앱에 `ssadassa://` 링크 처리가 들어간 빌드부터, 11-25 추가): 💻 Mac 터미널에서

```bash
cd ~/Desktop/ai-agent-engineering-101/submissions/26510358/round-4/ios
./qr.sh        # ssadassa://app.hermes-market.shop/?k=… → 아이폰 카메라 "싸다싸 가게에서 열기" → 바로 연결
./qr.sh web    # https://… → Safari 웹 앱(app/index.html)
```

QR에는 접근 코드가 들어 있다. 캡처하거나 공유하지 않는다. 시뮬레이터에서는 `xcrun simctl openurl booted "ssadassa://app.hermes-market.shop/?k=$K"`로 같은 동작을 시험한다.

이후 kit 재시작·goal 수정·서버 재부팅 뒤에도 주소를 다시 넣을 필요가 없다.

### 9-7. 🖥️ 서버: 이전에 시험한 주소 정리 (9-6이 된 뒤)

ngrok(월 20,000요청 한도, 공개 주소)과 로그인하지 않은 개인 Tailscale을 끈다. 파일은 남겨 두어 필요하면 다시 켤 수 있다.

▶ 🖥️ **서버 터미널**

```bash
systemctl --user disable --now shop-ngrok shop-tailscaled
for u in shop-kit shop-tunnel shop-sync.timer shop-ngrok shop-tailscaled; do printf "%-16s %s\n" $u "$(systemctl --user is-active $u)"; done
```

`shop-kit`, `shop-tunnel`, `shop-sync.timer`이 active, 나머지 둘이 inactive면 끝.

## 10단계. 💻 Mac + 📱 아이폰: 실제 폰에 앱 설치 (Xcode) — △ 진행

▶ 💻 **Mac 터미널**

```bash
open ~/Desktop/ai-agent-engineering-101/submissions/26510358/round-4/ios/Ssadassa.xcodeproj
```

1. 아이폰을 **케이블로 Mac에 연결**, 잠금 해제, "이 컴퓨터를 신뢰" → **신뢰**.
2. Xcode **Settings → Accounts**에 Apple ID(무료 가능)가 있는지 확인.
3. TARGETS **Ssadassa → Signing & Capabilities**: Automatically manage signing ✔, Team `명기 성 (Personal Team)`.
4. 위쪽 실행 대상을 시뮬레이터에서 **내 아이폰**으로 바꾼다("Preparing…"이면 끝날 때까지 대기) → Signing 화면의 **Try Again**.
   - `Failed to register bundle identifier`면 Bundle Identifier를 `kr.ac.seoultech.s26510358.ssadassa.myeonggi`로 바꾸고 Try Again.
5. 아이폰 **설정 → 개인정보 보호 및 보안 → 개발자 모드** 켜기 → 재시작 후 **켜기**.
6. Xcode **▶ Run**(`Cmd+R`). "신뢰하지 않는 개발자"면 아이폰 **설정 → 일반 → VPN 및 기기 관리 → Apple Development: …** → **신뢰** → 다시 Run.
7. 앱이 뜨면 9-6대로 주소(`https://app.hermes-market.shop/?k=…`)를 넣는다.

- 무료 Apple ID로 설치한 앱은 **7일 뒤 실행이 막힌다**. 아이폰을 연결하고 Run 하면 다시 7일.
- 케이블 없이: 한 번 연결한 뒤 Xcode **Window → Devices and Simulators** → 아이폰 → **Connect via network**.
- Team·Bundle ID를 바꾸면 프로젝트 파일이 바뀐다. Mac에서 commit한다.

▶ 💻 **Mac 터미널**

```bash
cd ~/Desktop/ai-agent-engineering-101 && git pull origin round-4
git add submissions/26510358/round-4/ios && git commit -m "round-4: iOS signing with my Personal Team for my iPhone" && git push origin round-4
```

## 세팅 끝: 웹 앱 한 바퀴 (Mac 수정 → 서버 반영, 재시작 없음)

▶ 💻 **Mac 터미널** — 표시 한 줄 넣고 올리기

```bash
cd ~/Desktop/ai-agent-engineering-101 && git pull origin round-4
echo '<!-- dev-loop test from the Mac -->' >> submissions/26510358/round-4/app/index.html
git add submissions/26510358/round-4/app/index.html
git commit -m "round-4: app dev-loop test marker from the Mac (reverted next)" && git push origin round-4
```

▶ 🖥️ **서버 터미널** — 받아서 가게가 내주는지 확인

```bash
cd ~/ai-agent-engineering-101 && git pull --no-edit origin round-4
K=$(cat submissions/26510358/round-4/.kit/app.key)
curl -s -b "miniapp_access=$K" http://127.0.0.1:8800/ | tail -1          # <!-- dev-loop test from the Mac --> 가 보이면 성공
```

▶ 💻 **Mac 터미널** — 되돌리기(지우지 않고 되돌리는 commit)

```bash
cd ~/Desktop/ai-agent-engineering-101 && git pull origin round-4 && git revert --no-edit HEAD && git push origin round-4
```

Mac의 `git push`가 `rejected`면 서버 타이머가 그 사이 push한 것이다. `git pull origin round-4` 후 다시 push.

---

# 참고

## A. 경로마다 쓰는 곳은 한 군데

두 곳이 같은 파일을 고치지 않으면 `git pull`이 충돌하지 않는다.

| 경로 (`round-4/` 기준) | 쓰는 쪽 | 비고 |
|---|---|---|
| `app/`, `ios/` | **Mac** | 서버는 pull만 한다 |
| `agent.json`(persona, goal, llm), `ops/`, `PLAYBOOK.md`, 이 문서 | **서버**(사람, Claude Code) | Mac은 pull만 한다 |
| `tools/`, `logs/`, `notes.md`, `card.json`, `customers.jsonl`, `stock.json`, `sales.jsonl`, `pay_log.json`, `public/` | **서버**(에이전트) | 사람이 손으로 고치지 않는다. kit은 forge 기록(`forge.json`의 sha256)과 맞지 않는 도구를 로드하지 않는다 |
| `*_wallet.key`, `.kit/`(owner.env, app.key, *.log), `submissions/26510358/.env` | 서버에만, git 밖 | `.gitignore`가 막는다 |
| `~/.config/systemd/user/shop-*`, `~/.cloudflared/`(tunnel 비밀키), `~/.config/ngrok/`, `~/.local/share/tailscale-personal/` | 서버에만, 저장소 밖 | 유닛·설정 내용은 이 문서의 블록이 원본. 비밀키는 지우지 않는다 |

## B. 고친 것이 돌아가는 가게에 언제 반영되나

| 바꾼 것 | kit이 읽는 때 | 서버에서 할 일 |
|---|---|---|
| `app/index.html`과 그 옆 파일 | **요청마다 디스크에서 읽음**(`miniapp.py`의 `index`) | `git pull`만(또는 매시 타이머). 앱 새로고침 |
| `ios/` | 서버와 무관 | 없음. Xcode로 다시 설치 |
| `agent.json` | **kit 시작 때 한 번** | `run_server.sh restart` (6단계 블록) |
| `tools/` | 시작 때 로드, run 중 forge하면 바로 교체 | 사람은 건드리지 않음 |
| `notes.md` | run마다 마지막 3000자 | 사람은 건드리지 않음 |
| `ops/run_server.sh`, `llm_shim.py` | 다음 시작 때 | `restart`(shim은 `restart shim`), 유닛 설정이 바뀌면 `down` 후 `up` |

kit이 재시작하는 1~3분은 모든 앱 주소가 끊긴다. `app.hermes-market.shop`(9단계)과 8단계 `ssh -L`은 그 뒤 그대로 다시 붙고,
kit 자체의 quick tunnel 주소(`run_server.sh link`)만 바뀐다.

## C. 24시간 개선의 두 층

- **에이전트(자동)**: 메시지나 타이머로 깨어나 한 run에 최대 `run_minutes`(8분), 모델 호출 `max_steps`(40)번. `forge_tool`로 도구를 만들고
  같은 이름으로 다시 forge해 코드와 description을 고친다(`logs/forge.jsonl`). REVIEW 규칙이 6시간마다 돌아보게 한다.
  - 11-25 현재 REVIEW 줄의 시각이 `15:xx`, `16:xx`처럼 분이 뭉개져 6시간 판단을 못 하고 매시간 돈다. 다음 goal 수정 때
    "REVIEW 시각은 Time now의 숫자(`YYYY-MM-DD HH:MM`) 그대로 쓴다"를 한 줄 넣는다.
- **사람(하루 1~2번, 서버)**: 에이전트는 goal을 못 고친다. 아래를 보고 goal을 고친 뒤 6단계 블록으로 반영한다.

▶ 🖥️ **서버 터미널**

```bash
cd ~/ai-agent-engineering-101 && R=submissions/26510358/round-4
$R/ops/run_server.sh status
grep REVIEW $R/notes.md | tail -5
tail -20 $R/logs/forge.jsonl | cut -c1-200
```

## D. 평소 흐름

| 할 일 | 어디서 | 명령 |
|---|---|---|
| goal, persona, 스크립트 수정 | 🖥️ 서버 | 수정 → 6단계 블록 |
| 웹 앱 수정 | 💻 Mac | `git pull` → 수정 → `preview_app.py`(7단계) 또는 `ssh -L`(8단계) → commit → push. 서버는 매시 타이머가 pull(급하면 서버에서 `git pull`) |
| iOS 앱 수정 | 💻 Mac | `git pull` → 수정 → 시뮬레이터(8단계) → 실제 폰(10단계) → commit → push |
| 에이전트 기록 commit | 🖥️ 서버(자동) | `shop-sync.timer`, 바로 하려면 `systemctl --user start shop-sync` |
| 상태 보기 | 🖥️ 서버 | `run_server.sh status`, `tail -f round-4/.kit/kit.log` |
| 밖에서 가게 보기 | 📱 아이폰 | 싸다싸 가게 앱 또는 Safari: `https://app.hermes-market.shop/?k=…` |

하지 않는 것:

- Mac에서 kit 실행(가게가 둘이 된다). 시험은 `preview_app.py`로.
- Mac에서 에이전트 파일 수정, 서버에서 `app/`, `ios/` 수정.
- 서버의 앱 파일을 scp로 덮어써서 미리 보기(working tree가 더러워져 pull이 막힌다).
- 서버의 연구실 Tailscale(`tailscale` 명령)에 `up`/`serve`/`funnel`/`set`. 연구실 공용 설정이다.
- kit을 `--app-tunnel` 없이 띄우기(`APP_FLAGS` 변경). 접근 코드가 꺼져 `app.hermes-market.shop`이 누구에게나 열린다.

## E. 안 될 때

| 증상 | 어디서 | 확인 |
|---|---|---|
| `shop-sync` 실패 | 🖥️ 서버 | `journalctl --user -u shop-sync -n 30`. 인증이면 3단계, merge 충돌이면 A 표를 어긴 파일 |
| 앱 변경이 안 보임 | 🖥️ 서버 → 💻 Mac | 서버 `git log -1 -- submissions/26510358/round-4/app`가 Mac commit인지, 브라우저 강력 새로고침 |
| goal 변경이 안 먹힘 | 🖥️ 서버 | `systemctl --user show shop-kit -p ActiveEnterTimestamp`가 수정 뒤인지. 아니면 `run_server.sh restart` |
| `restart`를 쳤는데 시각이 안 바뀜 | 🖥️ 서버 | Mac에서 쳤거나(`hostname` 확인), systemd 세션이 안 보이는 셸. 서버 터미널에서 다시 |
| `ssh -L`이 Address already in use | 💻 Mac | `lsof -nP -iTCP:8800 -sTCP:LISTEN`. 다른 포트로 `-L 18880:127.0.0.1:8800` 후 `http://127.0.0.1:18880/?k=…` |
| 아이폰 앱 "연결 실패" | 🖥️ 서버 | `systemctl --user is-active shop-kit shop-tunnel` → `journalctl --user -u shop-tunnel -n 30`. kit 재시작 중이면 1~3분 뒤 |
| `app.hermes-market.shop`이 502 | 🖥️ 서버 | tunnel은 살아 있고 kit(8800)이 응답하지 않음. `run_server.sh status` |
| `app.hermes-market.shop`이 401 화면 | 📱 | 정상(코드 없이 연 것). `?k=` 포함 주소로 다시 |
| 주소가 아예 안 열림(`000`, DNS 오류) | 💻 Mac | `dig +short NS hermes-market.shop`이 Cloudflare 네임서버인지(9-2), Cloudflare DNS에 `app` CNAME이 있는지(9-3) |
| 미리보기가 포트 오류 | 💻 Mac | `preview_app.py`는 빈 포트를 자동으로 고른다. 출력된 주소를 연다 |
| 1년 뒤 도메인 | 🌐 가비아 | 자동 연장을 꺼 두었으면 만료되고 끝(9-1). 계속 쓰려면 약 65,000원 |
