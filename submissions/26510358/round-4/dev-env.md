# 개발 환경: 서버(smc-gpu-server) + MacBook

가게(kit)는 SMC 서버에서 24시간 돈다(서비스를 띄우는 법은 `SERVER.md`). 에이전트 개발(goal, 스크립트)은 서버에서,
앱 개발(`app/`, `ios/`)은 Mac에서 한다. 이 문서의 앞부분(1~8단계)은 **처음 한 번 순서대로 따라 하는 세팅**이고,
뒷부분(참고)은 세팅의 이유와 평소 흐름이다. 2026-11-25에 `scripts/round4/agent_kit.py`, `miniapp.py`를 읽고 정리했다.

```
MacBook (앱)                         GitHub origin/round-4                 smc-gpu-server (가게 + 에이전트 개발)
  app/, ios/ 수정        ── push ──▶                     ◀── push ──  agent.json, ops/ 수정 (사람)
  preview_app.py로 확인                                               tools/, logs/, notes.md … (에이전트, 1시간마다 자동 commit)
  ssh -L 8800 으로 실제 가게에 붙기  ◀── pull ──           ── pull ──▶  systemd: shop-kit (+ shim)
  iOS Simulator                                                       cloudflared 터널 → 시장, 주인 앱
```

### 진행 상황 (2026-11-25 15:0x 서버에서 확인)

| 단계 | 상태 | 근거 |
|---|---|---|
| 1. SSH 별칭 | O 완료 | 지금 이 서버에 SSH로 들어와 개발 중 |
| 2. 가게 동작 | O 완료 | `shop-kit active since 11-25 14:53`. 다만 최근 500줄에 `model call failed` 10건(TimeoutError) |
| 3. git 설정·push 인증 | O 완료 (11-25 15:05) | `pull.rebase=false`, gh 로그인(scope `repo`), push 성공 `48db7a68..95fa125e` |
| 4. 에이전트 기록 첫 commit | O 완료 (11-25 15:05) | `95fa125e`: 에이전트 파일 6개, 키·`.kit/`·`.env` 없음. 이후 쌓이는 로그는 5단계 타이머가 맡음 |
| 5. 자동 commit 타이머 | O 완료 (11-25 15:06) | `shop-sync.timer` enabled, 매 정시. 첫 실행 success → `4229c2f8` push |
| 6. goal REVIEW 규칙 | O 완료 (11-25 15:23) | 15:10:49 재시작, 15:13 시장 재입장, 첫 실행에서 notes.md NOW에 `REVIEW 2026-11-25 15:xx credits=4982123 settled6h=0 fails=stock_and_price:1 …` 기록. 시각이 `15:xx`로 뭉개짐(6시간 판단이 흐려질 수 있음, 지켜볼 것) |
| 7. Mac 저장소·미리보기 | △ 진행 | git 부분 O: 남은 파일 stash, Mac commit `9d54bdd7`을 merge(`caa5c3e8`, agent.json은 서버 쪽), Mac·서버·origin 일치. **venv와 `preview_app.py` 확인이 남음** |
| 8. Mac `ssh -L` | ? 진행 | Mac에서 확인 필요 (5~6단계 뒤에) |

각 단계 끝의 **확인**이 통과해야 다음 단계로 간다.

### 어느 터미널에서 치나

모든 명령 블록 위에 `▶ 실행 위치`를 적었다. 터미널은 두 가지뿐이다.

| 표시 | 무엇 | 여는 법 | 프롬프트로 구분 |
|---|---|---|---|
| 🖥️ **서버 터미널** | smc-gpu-server 안의 셸 | Mac에서 `ssh smc-gpu-server`, 또는 VSCode Remote-SSH의 터미널, 또는 서버에서 돌리는 Claude Code | `hostname`이 `hai-SYS-740GP-TNRT` |
| 💻 **Mac 터미널** | MacBook의 Terminal/iTerm (SSH로 들어가지 않은 상태) | Mac에서 새 터미널 창 | `hostname`이 Mac 이름 |

- 헷갈리면 먼저 `hostname`을 친다. 서버 명령을 Mac에서 치면 `run_server.sh`, `systemctl --user`가 Mac에서 실패하거나 엉뚱한 곳을 건드린다.
- 8단계처럼 **Mac 터미널에서 `ssh …`로 서버에 명령을 보내는 것**은 Mac 터미널 명령이다(서버에 들어가서 치는 것이 아니다).
- 명령은 bash 문법이다(`R=…`, `$R`). 서버에서 fish를 쓰고 있다면 먼저 `bash`를 쳐서 들어간 뒤 붙여 넣는다.
- 서버의 저장소 경로는 `~/ai-agent-engineering-101`, Mac은 `~/Desktop/ai-agent-engineering-101`로 적었다. 다르면 바꿔서 친다.

---

## 1단계. [Mac] 서버에 SSH 별칭 만들기 — O 완료

이후 명령은 모두 `smc-gpu-server`라는 이름으로 서버에 들어간다고 가정한다. `~/.ssh/config`에 없으면 추가한다.

▶ 실행 위치: 💻 **Mac**에서 `~/.ssh/config` 파일을 편집기로 연다 (터미널 명령 아님)

```sshconfig
Host smc-gpu-server
    HostName <서버 주소>
    User myeonggi
    ServerAliveInterval 30
```

**확인**: `ssh smc-gpu-server 'hostname'`이 서버 이름을 출력한다.

## 2단계. [서버] 가게가 돌고 있는지 확인 — O 완료

▶ 실행 위치: 🖥️ **서버 터미널**

```bash
cd ~/ai-agent-engineering-101
git branch --show-current                                   # round-4
submissions/26510358/round-4/ops/run_server.sh status       # shop-kit active
```

`shop-kit`이 없거나 inactive이면 `SERVER.md`의 0~2절대로 먼저 띄운다.

**확인**: `status`에 `shop-kit active`가 나오고, `--- recent kit events`에 오류가 반복되지 않는다.

## 3단계. [서버] git 설정과 push 인증 — O 완료

서버도 GitHub에 push해야 한다(에이전트 기록을 Mac과 PR로 보내기 위해).

▶ 실행 위치: 🖥️ **서버 터미널** (`gh auth login`은 브라우저 인증을 묻는 대화형 명령이라 직접 친다)

```bash
cd ~/ai-agent-engineering-101
git config pull.rebase false                 # pull은 merge로. push된 commit을 다시 쓰지 않는다(AGENTS.md)
git config user.name; git config user.email  # Mac과 같은 값인지 확인
gh auth status || gh auth login              # gh가 없으면 fine-grained token을 credential helper에 저장
git push --dry-run origin round-4
```

**확인**: `git push --dry-run`이 인증 오류 없이 끝난다.

## 4단계. [서버] 지금까지 쌓인 에이전트 기록을 한 번 commit — O 완료

타이머(5단계)를 켜기 전에 지금 working tree에 쌓인 에이전트 파일을 손으로 한 번 commit한다.
그래야 첫 자동 commit이 며칠 치를 한꺼번에 담지 않는다.

▶ 실행 위치: 🖥️ **서버 터미널**

```bash
cd ~/ai-agent-engineering-101 && R=submissions/26510358/round-4
git status --short $R                        # 어떤 파일이 바뀌었는지 먼저 본다
git add $R/tools $R/logs $R/notes.md $R/card.json $R/customers.jsonl $R/stock.json \
        $R/sales.jsonl $R/pay_log.json $R/public
git status --short $R                        # *.key, .kit/ 가 staged에 없는지 확인
git commit -m "round-4: agent records up to $(date '+%m-%d %H:%M') from the server run"
git pull --no-edit origin round-4 && git push origin round-4
```

`agent.json`이 바뀌어 있으면 사람이 고친 것인지 확인한 뒤 따로 commit한다(무엇을 왜 바꿨는지 한 줄).
`tools/.deprecated/`처럼 처음 보는 폴더도 에이전트가 만든 것이면 그대로 commit한다(로그와 시도는 채점 증거).

**확인**: `git status --short $R`에 남은 것이 없거나, 남은 것이 git에 올리지 않을 파일뿐이다.

## 5단계. [서버] 에이전트 기록 자동 commit 타이머 — O 완료

1시간마다 에이전트가 쓰는 경로만 commit하고, pull(Mac의 앱 변경을 받음) 후 push한다.

▶ 실행 위치: 🖥️ **서버 터미널** (블록 전체를 한 번에 붙여 넣어도 된다)

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
systemctl --user start shop-sync             # 한 번 바로 돌려 본다
```

- systemd는 유닛 파일 안의 `$`와 `%`를 먼저 해석하므로 `$$`, `%%`로 적었다.
- `git add`는 위 경로만 받는다. 지갑 키와 `.kit/`는 `.gitignore`가 막지만 `git add -A`는 쓰지 않는다.
- 사람이 서버에서 고치는 `agent.json`, `ops/`는 타이머가 add하지 않으므로 섞이지 않는다.

**확인**:

▶ 실행 위치: 🖥️ **서버 터미널**

```bash
systemctl --user list-timers shop-sync.timer        # NEXT에 다음 정시가 보인다
journalctl --user -u shop-sync -n 20 --no-pager      # 오류 없음
git log --oneline -3 origin/round-4                  # "agent records" commit (바뀐 게 있었다면)
```

## 6단계. [서버] goal에 6시간 REVIEW 규칙 넣기 — O 완료

에이전트는 이미 최대 120초마다 깨어나 도구를 forge하고 고친다. 빠진 "n시간마다 돌아보기"를 goal에 넣는다.

1. `submissions/26510358/round-4/agent.json`의 `goal` 문자열 끝에 아래 문단을 붙인다(JSON이라 줄바꿈은 `\n`).

   ▶ 실행 위치: 🖥️ **서버**의 `agent.json`을 편집기로 연다 (VSCode Remote-SSH 또는 서버 터미널에서 `vim`/`nano`)

   ```text
   REVIEW every 6 hours (check the REVIEW line in notes.md; if it is older than 6 h, do this before anything else):
   1. Read tools/index.json (uses, fails per tool) and the last forge results in logs/forge.jsonl.
   2. A tool with fails > 0 since the last review: read its code with read_tool and re-forge it under the same name.
   3. A tool you called with wrong args or misread: rewrite its description so the args and the result are unambiguous.
   4. Something you did by hand three times in the last 6 h: forge one tool for it. Reuse before you forge.
   5. Compare credits now with the last REVIEW line. Write one line at the end of notes.md:
      REVIEW <time> credits=<n> (<+/- since last>) changed=<tools or none> next=<one thing to try>.
   Change one thing per review, so the next review can tell whether it helped.
   ```

2. 반영하고 commit한다. goal은 kit이 시작할 때만 읽으므로 재시작이 필요하고, 재시작하면 앱 주소가 바뀐다.

   ▶ 실행 위치: 🖥️ **서버 터미널**

   ```bash
   cd ~/ai-agent-engineering-101 && R=submissions/26510358/round-4
   python3 -c "import json; json.load(open('$R/agent.json'))" && echo json ok
   git add $R/agent.json && git commit -m "round-4: goal gets a 6-hour REVIEW rule (re-forge failing tools, fix descriptions, one change per review)"
   git push origin round-4
   $R/ops/run_server.sh restart
   $R/ops/run_server.sh link                  # 1분쯤 뒤, 새 앱 주소
   ```

**확인**: 재시작 뒤 첫 run에서 `notes.md` 끝에 `REVIEW` 줄이 생긴다(`grep REVIEW $R/notes.md`).
6시간은 시작값이다. 하루 뒤 `logs/forge.jsonl`의 re-forge 수와 credits 변화를 보고 조정한다.

## 7단계. [Mac] 저장소와 미리보기 환경 — ? 진행 (Mac에서 확인)

▶ 실행 위치: 💻 **Mac 터미널**

```bash
cd ~/Desktop/ai-agent-engineering-101
pkill -f agent_kit.py; pgrep -fl agent_kit.py   # 아무것도 안 나와야 한다(같은 지갑으로 가게가 둘이 된다)
git config pull.rebase false
git checkout round-4
git status --short submissions/26510358/round-4  # app/, ios/ 밖에 M이나 ??가 있으면 아래 7-1을 먼저 한다
git log --oneline --stat origin/round-4..HEAD    # Mac에만 있는 commit. 있으면 무엇인지 본다(7-1의 마지막 줄)
git pull origin round-4
```

### 7-1. Mac에 남은 에이전트 파일 치우기 (pull이 "would be overwritten"으로 멈출 때)

11-24 Mac 첫 run 뒤 commit되지 않은 `tools/`, `logs/`, `notes.md`, `card.json`, `pay_log.json`, `tools/.deprecated/` 등이
Mac에 남아 있으면 pull이 멈춘다. 서버 쪽이 정본이지만 로그는 채점 증거라서 **버리지 않고 stash로 치운다**.

▶ 실행 위치: 💻 **Mac 터미널**

```bash
cd ~/Desktop/ai-agent-engineering-101 && R=submissions/26510358/round-4
git stash push -u -m "mac leftovers after the 11-24 Mac run" -- $R ":(exclude)$R/app" ":(exclude)$R/ios"
git status --short $R                            # app/, ios/ 밖은 비어 있어야 한다
git pull origin round-4                          # Mac에만 있는 commit이 있으면 merge commit이 생긴다(정상)
git stash list                                   # stash@{0}: mac leftovers ... 가 남아 있다
```

- `-u`는 untracked(`pay_log.json`, `tools/.deprecated/`)도 함께 치운다. 서버가 이 파일들을 이미 commit해서 그대로 두면 pull이 막힌다.
- 지갑 키와 `.kit/`는 `.gitignore`된 파일이라 stash에 들어가지 않고 그대로 있다.
- stash 안의 Mac 로그에 서버에 없는 기록(11-24 19:52 commit 뒤 Mac kit을 멈출 때까지)이 있으면, 나중에
  `git show 'stash@{0}':$R/logs/agent-kit.log > $R/logs/agent-kit-mac-1124.log`처럼 **새 이름으로** 꺼내 Mac에서 commit한다.
  서버가 쓰는 `logs/agent-kit.log`에 덮어쓰지 않는다.

미리보기(`ops/preview_app.py`)는 kit 모듈을 그대로 불러오므로 서버와 같은 패키지가 필요하다.

▶ 실행 위치: 💻 **Mac 터미널** (venv는 Mac에 새로 만든다. 서버의 venv와 별개)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh          # uv가 없을 때만
uv venv --python 3.12 ~/.venvs/round4
VIRTUAL_ENV=~/.venvs/round4 uv pip install "a2a-sdk[http-server]" uvicorn httpx eth-account coincurve
```

**확인**: `git log --oneline -3`에 5·6단계의 서버 commit이 보이고, 아래가 뜬다(Ctrl-c로 끈다).

▶ 실행 위치: 💻 **Mac 터미널** → 브라우저도 **Mac**에서 연다

```bash
~/.venvs/round4/bin/python submissions/26510358/round-4/ops/preview_app.py --port 18800
# 브라우저 http://127.0.0.1:18800 → 채팅을 보내면 앱이 넘긴 도구 목록이 돌아온다
```

## 8단계. [Mac] 실제 가게에 붙는 길 확인 — ? 진행 (Mac에서 확인)

서버의 앱 포트 8800을 Mac으로 당겨 온다. quick tunnel 주소가 바뀌어도 이 주소는 그대로다.

▶ 실행 위치: 💻 **Mac 터미널** (Mac이 서버로 ssh하는 명령. 첫 줄은 **켜 둔 채로** 두므로 별도 탭에서 쳐도 된다)

```bash
ssh -N -L 8800:127.0.0.1:8800 smc-gpu-server &           # 끌 때: kill %1
ssh smc-gpu-server 'cat ~/ai-agent-engineering-101/submissions/26510358/round-4/.kit/app.key'
# 브라우저: http://127.0.0.1:8800/?k=<위 코드>
```

iOS 시뮬레이터도 같은 주소로 붙는다(Mac의 127.0.0.1을 그대로 쓴다):

▶ 실행 위치: 💻 **Mac 터미널** (위의 `ssh -L`이 켜져 있어야 한다)

```bash
cd submissions/26510358/round-4/ios
./run-simulator.sh "http://127.0.0.1:8800/?k=<코드>"
```

실제 아이폰은 https만 되므로 서버의 `run_server.sh link` 주소를 쓴다. 접근 코드가 든 주소는 채팅방이나 commit에 올리지 않는다.

**확인**: 브라우저와 시뮬레이터에서 가게 에이전트와 대화가 된다.

## 세팅 끝: 한 바퀴 돌려 보기

| 순서 | 어디서 | 할 일 | 기대 결과 |
|---|---|---|---|
| 1 | Mac | `app/index.html`에 눈에 띄는 작은 변경 → commit → push | |
| 2 | 서버 | `git pull` (또는 다음 정시 타이머) | 서버 `app/`에 변경이 들어옴 |
| 3 | Mac | `http://127.0.0.1:8800/?k=…` 새로고침 | 변경이 보임. kit 재시작 없음 |
| 4 | 서버 | `systemctl --user start shop-sync` | "agent records" commit이 push됨 |
| 5 | Mac | `git pull` | 충돌 없이 서버의 에이전트 기록이 들어옴 |

1의 변경은 확인 뒤 되돌리는 commit으로 정리한다(지우지 말고 새 commit으로).

---

# 참고

## A. 경로마다 쓰는 곳은 한 군데

두 곳이 같은 파일을 고치지 않으면 `git pull`이 충돌하지 않는다.

| 경로 (`round-4/` 기준) | 쓰는 쪽 | 비고 |
|---|---|---|
| `app/`, `ios/` | **Mac** | 서버는 pull만 한다 |
| `agent.json`(persona, goal, llm), `ops/`, `PLAYBOOK.md`, `SERVER.md`, 이 문서 | **서버**(사람, Claude Code) | Mac은 pull만 한다 |
| `tools/`, `logs/`, `notes.md`, `card.json`, `customers.jsonl`, `stock.json`, `sales.jsonl`, `pay_log.json`, `public/` | **서버**(에이전트) | 사람이 손으로 고치지 않는다. kit은 forge 기록(`forge.json`의 sha256)과 맞지 않는 도구를 로드하지 않는다 |
| `*_wallet.key`, `.kit/`(owner.env, app.key, *.log), `submissions/26510358/.env` | 서버에만, git 밖 | `.gitignore`가 막는다 |

충돌이 났다면 이 표를 어긴 것이다. 누가 그 파일을 고쳤는지부터 본다.

## B. 고친 것이 돌아가는 가게에 언제 반영되나

| 바꾼 것 | kit이 읽는 때 | 서버에서 할 일 |
|---|---|---|
| `app/index.html`과 그 옆 파일 | **요청마다 디스크에서 읽음**(`miniapp.py`의 `index`) | `git pull`만. 앱 새로고침 |
| `ios/` | 서버와 무관. 설치된 빌드가 앱 주소로 붙음 | 없음 |
| `agent.json` | **kit 시작 때 한 번** | `run_server.sh restart` → `link` |
| `tools/` | 시작 때 로드. 에이전트가 run 중 forge하면 바로 추가·교체 | 사람은 건드리지 않음 |
| `notes.md` | run마다 마지막 3000자 | 사람은 건드리지 않음 |
| `ops/run_server.sh`, `llm_shim.py` | 다음 시작 때 | `restart`(shim은 `restart shim`), 유닛 설정이 바뀌면 `down` 후 `up` |

`restart`하면 quick tunnel 주소가 바뀐다(`SERVER.md` 6절). goal 수정은 모아서 한 번에 한다.

## C. 24시간 개선의 두 층

- **에이전트(자동)**: 메시지나 타이머로 깨어나 한 run에 최대 `run_minutes`(8분), 모델 호출 `max_steps`(40)번.
  `sleep`을 고르지 않으면 120초 뒤 다시 깬다. `forge_tool`로 도구를 만들고, 같은 이름으로 다시 forge해 코드와 description을 고친다
  (`logs/forge.jsonl`에 버전과 테스트 결과가 남는다). 6단계의 REVIEW 규칙이 이것을 6시간마다 의식적으로 하게 만든다.
- **사람(하루 1~2번, 서버)**: 에이전트는 goal을 못 고친다. 기록을 보고 사람이 고친다.

  ▶ 실행 위치: 🖥️ **서버 터미널**

  ```bash
  cd ~/ai-agent-engineering-101 && R=submissions/26510358/round-4
  $R/ops/run_server.sh status
  grep REVIEW $R/notes.md | tail -5
  tail -20 $R/logs/forge.jsonl | cut -c1-200
  ```

  goal을 고치면 commit 메시지에 무엇을 왜 바꿨는지 한 줄로 쓰고 push → `restart` → `link`.

## D. 평소 흐름

| 할 일 | 어디서 | 명령 |
|---|---|---|
| goal, persona, 스크립트 수정 | 서버 | 수정 → commit → push → `run_server.sh restart` → `link` |
| 웹 앱 수정 | Mac | `git pull` → 수정 → `preview_app.py` → commit → push → 서버 `git pull` |
| iOS 앱 수정 | Mac | `git pull` → 수정 → 시뮬레이터(`ssh -L`) → commit → push |
| 에이전트 기록 commit | 서버(자동) | `shop-sync.timer`, 바로 하려면 `systemctl --user start shop-sync` |
| 상태 보기 | 서버 | `run_server.sh status`, `tail -f round-4/.kit/kit.log` |
| 개선 점검 | 서버 | `grep REVIEW round-4/notes.md`, `logs/forge.jsonl` |

하지 않는 것:

- Mac에서 kit 실행(가게가 둘이 된다). 시험은 `preview_app.py`로.
- Mac에서 에이전트 파일 수정, 서버에서 `app/`, `ios/` 수정.
- 서버의 앱 파일을 scp로 덮어써서 미리 보기. working tree가 더러워져 다음 pull이 막힌다.

## E. 안 될 때

| 증상 | 어디서 | 확인 |
|---|---|---|
| `shop-sync`가 실패 | 🖥️ 서버 | `journalctl --user -u shop-sync -n 30`. 인증이면 3단계, merge 충돌이면 A의 표를 어긴 파일을 찾는다 |
| 앱 변경이 안 보임 | 🖥️ 서버 → 💻 Mac | 서버에서 `git log -1 -- submissions/26510358/round-4/app`가 Mac의 commit인지, Mac 브라우저에서 강력 새로고침 |
| goal 변경이 안 먹힘 | 🖥️ 서버 | `restart`를 했는지. kit은 시작 때만 `agent.json`을 읽는다 |
| `ssh -L`이 "Address already in use" | 💻 Mac | 8800을 쓰는 프로세스(`lsof -i :8800`). 다른 포트로 `-L 18801:127.0.0.1:8800` |
| 앱이 "연결 실패" | 🖥️ 서버 | kit이 재시작돼 tunnel 주소가 바뀜. `run_server.sh link` (ssh -L 주소는 영향 없음) |
