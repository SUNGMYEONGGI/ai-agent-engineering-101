# 개발 환경: 서버(smc-gpu-server) + MacBook

가게(kit)와 에이전트 개발은 SMC 서버에서, 앱 개발(`app/`, `ios/`)은 Mac에서 한다. 앞부분 1~10단계는 **처음 세팅(또는 다시 세팅)할 때
위에서부터 붙여 넣는 순서**이고, 뒷부분 "참고"는 이유와 평소 흐름이다. `scripts/round4/agent_kit.py`, `miniapp.py`를 읽고 정리했다.

```
MacBook (앱 개발)                     GitHub origin/round-4               smc-gpu-server (가게 24시간 + 에이전트 개발)
  app/, ios/ 수정         ── push ──▶                    ◀── push ──  agent.json, ops/ 수정 (사람)
  preview_app.py, Xcode                                              tools/, logs/, notes.md … (에이전트, 매시 자동 commit)
  ssh -L 8800 → 실제 가게  ◀── pull ──          ── pull ──▶  systemd --user:
                                                                       shop-kit         가게 (시장 A2A + 앱 8800)
아이폰 (Tailscale 앱 ON) ──https://hermes-shop.<tailnet>.ts.net──▶     shop-tailscaled  개인 Tailscale → 앱 8800
                                                                       shop-sync.timer  매시 에이전트 기록 commit·push
                                                                       shop-ngrok       (예비) ngrok 고정 주소
```

### 진행 상황 (2026-11-25 16:4x 서버에서 확인)

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
| 9. 고정 앱 주소 (개인 Tailscale) | △ 진행 | 서버 `shop-tailscaled` active, **로그인(9-2)부터 남음** |
| 10. 실제 아이폰에 앱 설치 | △ 진행 | Xcode 서명 Team 선택까지. 아이폰 연결부터 남음 |
| 세팅 끝. 웹 앱 한 바퀴 | O 완료 | Mac `8e87a978`(표시 추가) → 서버가 재시작 없이 표시를 내줌 → Mac `70980208`(revert) → 서버 pull 뒤 표시 사라짐 |
| 예비. ngrok 고정 주소 | O 완료 | `shop-ngrok` active. 월 20,000요청 한도라 9단계가 되면 끈다(9-6) |

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
$R/ops/run_server.sh up                          # 이미 떠 있으면 "already up"
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

확인: 몇 분 뒤 `grep REVIEW $R/notes.md`. 고정 주소(9단계)로 붙은 앱은 재시작 뒤에도 주소를 바꿀 필요가 없다.

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

## 9단계. 고정 앱 주소: 개인 Tailscale (무료, 한도 없음) — △ 진행

아이폰이 어디서든(LTE 포함) `https://hermes-shop.<내-tailnet>.ts.net/?k=<코드>`로 가게 앱에 붙는다. 주소는 kit 재시작·서버 재부팅 뒤에도 그대로.
연구실 Tailscale(`seoultech.hailab`)은 건드리지 않고, **내 개인 Tailscale을 root 없이 사용자 권한(userspace)으로 하나 더** 띄운다
(소켓·상태 `~/.local/share/tailscale-personal/`, UDP 포트 자동). 내 계정에 로그인한 기기만 이 주소에 닿는다.

### 9-1. 🌐 브라우저: 개인 Tailscale 계정 (한 번)

1. login.tailscale.com 에서 **개인 계정**(개인 Google/GitHub/Apple)으로 가입·로그인한다. **연구실 계정(seoultech.hailab)이 아니다.**
2. 관리 콘솔 **DNS** 탭: **MagicDNS**가 켜져 있는지 보고, 아래 **HTTPS Certificates → Enable HTTPS**를 누른다.
   상단에 보이는 tailnet 이름(`tailXXXX.ts.net`)을 적어 둔다.

### 9-2. 🖥️ 서버: 개인 tailscaled 서비스와 로그인

서비스 파일은 11-25에 만들어 켜 두었다(`shop-tailscaled` active). 다시 세팅할 때는 블록 전체를 붙여 넣는다.

▶ 🖥️ **서버 터미널**

```bash
mkdir -p ~/.config/systemd/user ~/.local/share/tailscale-personal
cat > ~/.config/systemd/user/shop-tailscaled.service <<'EOF'
[Unit]
Description=round-4: personal Tailscale (userspace, separate from the lab's tailscaled) serving the shop app at https://<host>.<tailnet>.ts.net
After=network-online.target
StartLimitIntervalSec=0
[Service]
ExecStartPre=/bin/mkdir -p %h/.local/share/tailscale-personal
ExecStart=/usr/sbin/tailscaled --tun=userspace-networking --statedir=%h/.local/share/tailscale-personal --socket=%h/.local/share/tailscale-personal/tailscaled.sock --port=0
Restart=always
RestartSec=10
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload && systemctl --user enable --now shop-tailscaled
sleep 3; systemctl --user is-active shop-tailscaled
```

로그인 (출력된 `https://login.tailscale.com/a/…`를 🌐 **Mac 브라우저**에서 열고 **9-1의 개인 계정**으로 Connect):

```bash
TS="tailscale --socket=$HOME/.local/share/tailscale-personal/tailscaled.sock"
$TS up --hostname=hermes-shop                    # 브라우저에서 승인하면 "Success."가 나오고 끝난다
$TS status | head -3                             # 100.x.y.z  hermes-shop  <내 계정>  linux
tailscale status | head -1                       # 연구실 쪽은 그대로 smc-gpu-server  seoultech.hailab@
```

### 9-3. 🖥️ 서버: 가게 앱(8800)을 https로 내보내기

```bash
TS="tailscale --socket=$HOME/.local/share/tailscale-personal/tailscaled.sock"
$TS serve --bg http://127.0.0.1:8800             # "Serve is not enabled…"가 나오면 그 URL을 브라우저에서 열어 허용하고 다시
$TS serve status                                 # https://hermes-shop.tailXXXX.ts.net (tailnet only) → proxy http://127.0.0.1:8800
echo "https://$($TS status --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))')/?k=$(cat ~/ai-agent-engineering-101/submissions/26510358/round-4/.kit/app.key)"
```

- 마지막 줄이 아이폰에 넣을 주소다. `tailnet only`라 인터넷에는 공개되지 않는다(`funnel`은 쓰지 않는다).
- serve 설정은 tailscaled 상태에 저장돼 재부팅 뒤에도 유지된다.
- kit은 `--app-tunnel`(기본 `APP_FLAGS`)로 떠 있어야 접근 코드가 켜진다(`agent_kit.py` 846–847행). 이것은 바꾸지 않는다.

### 9-4. 📱 아이폰: Tailscale 앱과 확인

1. App Store에서 **Tailscale** 설치 → **9-1의 개인 계정**으로 로그인 → VPN 구성 허용 → 토글 **켜짐**.
2. Safari에서 9-3의 주소를 `?k=` **없이** 먼저 연다: 접근 코드를 묻는 잠금 화면(401)이면 정상.
3. 코드를 붙인 주소 전체로 열면 가게 웹 앱이 열린다.
4. 와이파이를 끄고 LTE로도 열리는지 본다.

- 아이폰에서 다른 VPN을 쓰는 중이면 Tailscale과 동시에 켤 수 없다.
- Mac에서도 쓰려면 Mac용 Tailscale에 같은 개인 계정으로 로그인한다(Mac이 연구실 tailnet에 들어가 있으면 계정 전환이 필요. 개발은 8단계 `ssh -L`이면 충분).

### 9-5. 📱 아이폰 앱에 넣기

싸다싸 가게 앱(10단계로 설치) 첫 화면 → **링크 붙여넣기** → 9-3의 주소 → **연결**. 이후 kit이 재시작돼도 다시 넣을 필요가 없다.

### 9-6. 🖥️ 서버: 예비 ngrok 정리 (9-4가 된 뒤)

ngrok 고정 주소(`https://scallion-retiree-unfazed.ngrok-free.dev`)는 인터넷에 공개돼 있고 월 20,000요청 한도가 있다. Tailscale이 되면 끈다.

```bash
systemctl --user disable --now shop-ngrok
systemctl --user is-active shop-ngrok            # inactive
```

다시 필요하면 `systemctl --user enable --now shop-ngrok`(서비스 파일과 `~/.config/ngrok/ngrok.yml`은 남아 있다).

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
7. 앱이 뜨면 9-5대로 주소를 넣는다.

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
| `~/.config/systemd/user/shop-*`, `~/.local/share/tailscale-personal/`, `~/.config/ngrok/` | 서버에만, 저장소 밖 | 내용은 이 문서의 블록이 원본 |

## B. 고친 것이 돌아가는 가게에 언제 반영되나

| 바꾼 것 | kit이 읽는 때 | 서버에서 할 일 |
|---|---|---|
| `app/index.html`과 그 옆 파일 | **요청마다 디스크에서 읽음**(`miniapp.py`의 `index`) | `git pull`만(또는 매시 타이머). 앱 새로고침 |
| `ios/` | 서버와 무관 | 없음. Xcode로 다시 설치 |
| `agent.json` | **kit 시작 때 한 번** | `run_server.sh restart` (6단계 블록) |
| `tools/` | 시작 때 로드, run 중 forge하면 바로 교체 | 사람은 건드리지 않음 |
| `notes.md` | run마다 마지막 3000자 | 사람은 건드리지 않음 |
| `ops/run_server.sh`, `llm_shim.py` | 다음 시작 때 | `restart`(shim은 `restart shim`), 유닛 설정이 바뀌면 `down` 후 `up` |

kit이 재시작하는 1~3분은 모든 앱 주소가 끊긴다. 고정 주소(9단계, 8단계 `ssh -L`)는 그 뒤 그대로 다시 붙고,
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
| 밖에서 가게 보기 | 📱 아이폰 | Tailscale 켜기 → 싸다싸 가게 앱(9단계 주소) |

하지 않는 것:

- Mac에서 kit 실행(가게가 둘이 된다). 시험은 `preview_app.py`로.
- Mac에서 에이전트 파일 수정, 서버에서 `app/`, `ios/` 수정.
- 서버의 앱 파일을 scp로 덮어써서 미리 보기(working tree가 더러워져 pull이 막힌다).
- 서버의 연구실 Tailscale(`tailscale` 기본 소켓)에 `up`/`serve`/`funnel`. 개인 것은 항상 `--socket=~/.local/share/tailscale-personal/tailscaled.sock`.

## E. 안 될 때

| 증상 | 어디서 | 확인 |
|---|---|---|
| `shop-sync` 실패 | 🖥️ 서버 | `journalctl --user -u shop-sync -n 30`. 인증이면 3단계, merge 충돌이면 A 표를 어긴 파일 |
| 앱 변경이 안 보임 | 🖥️ 서버 → 💻 Mac | 서버 `git log -1 -- submissions/26510358/round-4/app`가 Mac commit인지, 브라우저 강력 새로고침 |
| goal 변경이 안 먹힘 | 🖥️ 서버 | `systemctl --user show shop-kit -p ActiveEnterTimestamp`가 수정 뒤인지. 아니면 `run_server.sh restart` |
| `restart`를 쳤는데 시각이 안 바뀜 | 🖥️ 서버 | Mac에서 쳤거나(`hostname` 확인), systemd 세션이 안 보이는 셸. 서버 터미널에서 다시 |
| `ssh -L`이 Address already in use | 💻 Mac | `lsof -nP -iTCP:8800 -sTCP:LISTEN`. 다른 포트로 `-L 18880:127.0.0.1:8800` 후 `http://127.0.0.1:18880/?k=…` |
| 아이폰 앱 "연결 실패"(Tailscale 주소) | 📱 → 🖥️ | 아이폰 Tailscale 토글이 켜져 있는지 → 서버 `systemctl --user is-active shop-tailscaled shop-kit` → `$TS serve status` |
| Tailscale 주소가 401 화면 | 📱 | 정상(코드 없이 연 것). `?k=` 포함 주소로 다시 |
| 미리보기가 포트 오류 | 💻 Mac | `preview_app.py`는 빈 포트를 자동으로 고른다. 출력된 주소를 연다 |
| ngrok 주소가 안 열림 | 📱 | 월 20,000요청 한도 초과일 수 있다(dashboard.ngrok.com Usage). 9단계 Tailscale 주소를 쓴다 |
