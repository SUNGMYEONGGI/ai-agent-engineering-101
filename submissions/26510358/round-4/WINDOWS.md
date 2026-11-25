# 서버와 Mac에서 함께 개발하기 (smc-gpu-server + MacBook)

가게(kit)는 SMC 서버에서 24시간 돈다(띄우는 법은 `SERVER.md`). 이 문서는 **어디서 무엇을 고치고, 고친 것이 어떻게
다른 쪽과 돌아가는 가게에 반영되는지**를 정한다. 2026-11-25에 `scripts/round4/agent_kit.py`, `miniapp.py`를 읽고 정리했다.

```
MacBook (앱)                         GitHub origin/round-4                 smc-gpu-server (가게 + 에이전트 개발)
  app/, ios/ 수정        ── push ──▶                     ◀── push ──  agent.json, ops/ 수정 (사람)
  preview_app.py로 확인                                               tools/, logs/, notes.md … (에이전트, 1시간마다 자동 commit)
  ssh -L 8800 으로 실제 가게에 붙기  ◀── pull ──           ── pull ──▶  systemd: shop-kit (+ shim)
  iOS Simulator                                                       cloudflared 터널 → 시장, 주인 앱
```

## 1. 원칙: 경로마다 쓰는 곳은 한 군데

두 곳이 같은 파일을 고치지 않으면 `git pull`이 충돌하지 않는다. 아래 표가 전부다.

| 경로 (`round-4/` 기준) | 쓰는 쪽 | 비고 |
|---|---|---|
| `app/`, `ios/` | **Mac** | 서버는 pull만 한다. 서버에서 앱을 고치고 싶으면 Mac에서 한다 |
| `agent.json`(persona, goal, llm), `ops/`, `PLAYBOOK.md`, `SERVER.md`, 이 문서 | **서버**(사람, Claude Code) | Mac은 pull만 한다 |
| `tools/`, `logs/`, `notes.md`, `card.json`, `customers.jsonl`, `stock.json`, `sales.jsonl`, `pay_log.json`, `public/` | **서버**(에이전트) | 사람이 손으로 고치지 않는다. kit은 forge 기록(`forge.json`의 sha256)과 맞지 않는 도구를 로드하지 않는다 |
| `*_wallet.key`, `.kit/`(owner.env, app.key, *.log), `submissions/26510358/.env` | 서버에만, git 밖 | `.gitignore`가 막는다. Mac에 남은 사본은 kit을 띄우지 않는 한 쓰이지 않는다 |

- **kit은 서버에서만 띄운다.** 지갑 키가 곧 가게라서 Mac에서 `agent_kit.py run`을 하면 같은 가게가 둘이 된다.
- 둘 다 `git config pull.rebase false`(merge)로 둔다. 이미 push된 commit을 다시 쓰지 않는다(AGENTS.md: history rewrite 금지).
- 경로가 겹치지 않으므로 merge commit이 생겨도 충돌은 없다. 충돌이 났다면 표를 어긴 것이니 누가 그 파일을 고쳤는지부터 본다.

## 2. 고친 것이 돌아가는 가게에 언제 반영되나

kit이 각 파일을 언제 읽는지에 따라 다르다.

| 바꾼 것 | 반영 시점 | 서버에서 할 일 |
|---|---|---|
| `app/index.html`과 그 옆 파일(js, css, 이미지) | **요청마다 디스크에서 읽음**(`miniapp.py`의 `index`) | `git pull`만. 앱 새로고침 |
| `ios/` (SwiftUI 앱) | 서버와 무관. 폰·시뮬레이터에 설치된 빌드가 앱 주소로 붙음 | 없음. Mac에서 빌드 |
| `agent.json`(goal, persona, `run_minutes`, `max_steps`) | **kit 시작 때 한 번 읽음** | `run_server.sh restart` |
| `tools/` | 시작 때 로드. 에이전트가 run 중 forge하면 바로 추가·교체됨 | 사람은 건드리지 않음 |
| `notes.md` | run마다 마지막 3000자를 읽음 | 사람은 건드리지 않음 |
| `ops/run_server.sh`, `llm_shim.py` | 다음 시작 때 | `restart`(shim은 `restart shim`), 유닛 설정이 바뀌면 `down` 후 `up` |

`restart`하면 quick tunnel 주소가 바뀐다(`SERVER.md` 6절). 재시작 뒤 `run_server.sh link`로 새 주소를 앱에 넣는다.
goal을 자주 바꿀수록 앱 주소도 자주 바뀌므로, goal 수정은 모아서 한 번에 한다.

## 3. 24시간 스스로 개선하기

### 3-1. 에이전트가 스스로 하는 것 (이미 kit에 있음)

kit은 에이전트를 메시지가 오거나 타이머가 끝날 때 깨운다. 한 run은 최대 `run_minutes`(8분) 동안 모델 호출 `max_steps`(40)번이고,
`sleep`을 고르지 않으면 120초 뒤에 다시 깬다. 에이전트는 `forge_tool`로 도구를 새로 만들거나 **같은 이름으로 다시 forge해서
코드와 description을 고친다**(버전이 오르고 `logs/forge.jsonl`에 남는다). 그러니 별도 스케줄러 없이도 24시간 돈다.
빠진 것은 "n시간마다 멈춰서 돌아보기"인데, 이것은 goal에 규칙으로 넣는다. kit은 goal을 매 run 프롬프트에 그대로 넣는다.

goal에 붙일 문단(예시, 서버에서 `agent.json`에 넣고 `restart`):

```text
REVIEW every 6 hours (check the REVIEW line in notes.md; if it is older than 6 h, do this before anything else):
1. Read tools/index.json (uses, fails per tool) and the last forge results in logs/forge.jsonl.
2. A tool with fails > 0 since the last review: read its code with read_tool and re-forge it under the same name.
3. A tool you called with wrong args or misread: rewrite its description so the args and the result are unambiguous.
4. Something you did by hand three times in the last 6 h: forge one tool for it. Reuse before you forge.
5. Compare credits now with the last REVIEW line. Write one line in notes.md:
   REVIEW <time> credits=<n> (<+/- since last>) changed=<tools or none> next=<one thing to try>.
Change one thing per review, so the next review can tell whether it helped.
```

- `notes.md`는 마지막 3000자만 보이므로 REVIEW 줄을 맨 뒤에 남기라고 쓴다. 너무 길어지면 에이전트가 정리한다.
- 6시간은 시작값이다. 하루 동안 `logs/forge.jsonl`의 re-forge 수와 credits 변화를 보고 줄이거나 늘린다.

### 3-2. 사람(+ Claude Code)이 서버에서 하는 것: 하루 1~2번

에이전트는 goal을 고칠 수 없다. goal은 사람이 기록을 보고 고친다.

```bash
cd ~/ai-agent-engineering-101 && R=submissions/26510358/round-4
$R/ops/run_server.sh status                                   # 살아 있는지, 모델 실패, 오늘 토큰
grep REVIEW $R/notes.md | tail -5                             # 에이전트의 자기 점검 기록
tail -20 $R/logs/forge.jsonl | cut -c1-200                    # 최근 forge와 테스트 결과
```

goal을 고쳤으면 commit 메시지에 무엇을 왜 바꿨는지 한 줄로 쓰고(채점이 과정을 본다) push한 뒤 `run_server.sh restart`.

## 4. 에이전트 기록을 자동으로 commit하기 (서버)

에이전트가 쓴 파일은 사람이 commit하지 않으면 서버 working tree에만 쌓이고, Mac이나 PR에서는 안 보인다.
1시간마다 그 경로만 commit하고 push하는 systemd 타이머를 둔다(서버에서 한 번).

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
```

- systemd는 유닛 파일 안의 `$`와 `%`를 먼저 해석하므로 `$$`, `%%`로 적었다.
- `git add`는 위 경로만 받는다. 지갑 키와 `.kit/`는 `.gitignore`가 막지만 `git add -A`는 쓰지 않는다.
- 서버의 `git push`는 GitHub 인증(토큰 또는 `gh auth`)이 저장돼 있어야 한다. 실패는 `journalctl --user -u shop-sync -n 20`에 남는다.
- 사람이 서버에서 `agent.json`이나 `ops/`를 고치는 중이어도 타이머는 그 파일을 add하지 않으므로 섞이지 않는다.
- 이 타이머는 `app/`, `ios/`를 고치지 않고 pull만 하므로 Mac의 앱 변경이 1시간 안에 서버로 들어온다. 급하면 서버에서 직접 `git pull`.

## 5. Mac에서 앱 개발하기

Mac은 `app/`, `ios/`만 고친다. 시작 전에 항상 `git pull`(서버의 에이전트 기록과 goal 변경을 받는다).

### 5-1. 웹 앱(`app/index.html`)

1. **가짜 에이전트로 화면 확인**: 시장과 모델 없이 kit의 `miniapp`을 그대로 띄운다. 지갑을 쓰지 않으므로 Mac에서 돌려도 된다.

   ```bash
   ~/.venvs/round4/bin/python submissions/26510358/round-4/ops/preview_app.py --port 18800
   ```

   채팅을 보내면 앱이 넘긴 도구 목록이 돌아오고, `/tool <이름> {json}`으로 앱 도구를 직접 불러 볼 수 있다.
2. **진짜 가게에 붙여 보기**: 서버의 앱 포트를 Mac으로 당겨 온다. 서버는 서버에 pull된 `app/`을 내주므로, 이 단계는 push 뒤에 한다.

   ```bash
   ssh -N -L 8800:127.0.0.1:8800 smc-gpu-server
   # 브라우저: http://127.0.0.1:8800/?k=<서버 .kit/app.key 내용>
   ```

   quick tunnel 주소가 바뀌어도 이 주소는 그대로다.
3. 확인이 끝나면 commit → push → 서버에서 `git pull`(또는 타이머를 기다림) → 앱 새로고침. kit 재시작은 필요 없다.

### 5-2. iOS 앱(`ios/`)

- 빌드와 시뮬레이터는 Mac에서만 된다(서버에는 Xcode가 없다. 서버에서는 `ios/Ssadassa/Core`의 CoreCheck만 빌드된다).
- 시뮬레이터는 5-1의 `ssh -L` 주소(`http://127.0.0.1:8800/?k=…`)에 붙는다(Info.plist의 로컬 네트워크 예외). 실제 아이폰은 https만 되므로 `run_server.sh link`의 주소를 쓴다.
- iOS 앱은 서버에 배포할 것이 없다. commit은 기록용이다.

## 6. 평소 흐름 한눈에

| 할 일 | 어디서 | 명령 |
|---|---|---|
| goal, persona, 스크립트 수정 | 서버 | 수정 → commit → push → `run_server.sh restart` → `link` |
| 웹 앱 수정 | Mac | `git pull` → 수정 → `preview_app.py` → commit → push → 서버 `git pull` |
| iOS 앱 수정 | Mac | `git pull` → 수정 → 시뮬레이터(`ssh -L`) → commit → push |
| 에이전트 기록 commit | 서버(자동) | `shop-sync.timer`, 수동이면 `systemctl --user start shop-sync` |
| 상태 보기 | 서버 | `run_server.sh status`, `tail -f round-4/.kit/kit.log` |
| 개선 점검 | 서버 | `grep REVIEW round-4/notes.md`, `logs/forge.jsonl` |

하지 않는 것:

- Mac에서 kit 실행(가게가 둘이 된다). 시험은 `preview_app.py`로.
- Mac에서 `tools/`, `logs/`, `notes.md` 등 에이전트 파일 수정, 서버에서 `app/`, `ios/` 수정.
- 서버의 앱 파일을 scp로 덮어써서 미리 보기. working tree가 더러워져 다음 pull이 막힌다.
