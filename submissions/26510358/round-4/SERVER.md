# 서버에서 24시간 돌리기 (SMC 서버 + systemd)

에이전트는 SMC 서버의 systemd 사용자 서비스(`shop-kit` 등)로 돈다. 노트북을 덮거나 SSH·VSCode를 닫아도, 서버가 재부팅돼도 다시 켜진다
(linger가 켜져 있어야 함: `loginctl show-user $USER -p Linger`가 `Linger=yes`, 11-24 확인). systemd가 없는 곳(WSL 등)에서는 예전처럼 tmux를 쓴다(`BACKEND=tmux`).
주인 앱(iOS, 웹)은 kit이 내주는 `https://….trycloudflare.com/?k=…` 주소로 붙는다.

```
[SMC 서버] systemd --user
  ├─ shop-shim  ops/llm_shim.py        127.0.0.1:18790 → OpenAI (LLM=own일 때만)
  ├─ shop-mesh  MeshKit DailyMart      127.0.0.1:18765 (~/meshkit 있을 때만)
  └─ shop-kit   agent_kit.py run       가게 A2A(--tunnel) + 주인 앱 8800(--app-tunnel)
                                      │
               https://xxx.trycloudflare.com/?k=코드
                                      │
                 아이폰 앱 / Windows·Mac 브라우저
```

## 0. 처음 한 번: 서버에 있어야 하는 것

SSH로 서버에 들어가서 확인한다.

```bash
cd ~/ai-agent-engineering-101
which cloudflared                            # 경로가 나와야 함 (tmux는 BACKEND=tmux일 때만)
~/.venvs/round4/bin/python --version         # 3.11 이상
ls submissions/26510358/.env \
   submissions/26510358/round-4/.kit/owner.env \
   submissions/26510358/round-4/*_wallet.key  # git에 없는 파일: 지갑 키, 모델 키, claim code
```

둘 다 없으면 root 없이 설치한다(11-19 SMC 서버에 둘 다 없었음). `cloudflared`는 kit이 PATH에서 직접 찾아 실행하므로
tmux를 안 써도 필요하다. `run_server.sh`는 `~/.local/bin`을 PATH 앞에 넣는다.

```bash
uname -m                                     # x86_64 → amd64, aarch64 → arm64
mkdir -p ~/.local/bin
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o ~/.local/bin/cloudflared && chmod +x ~/.local/bin/cloudflared
sudo apt install -y tmux || conda install -y -c conda-forge tmux   # 되는 쪽 하나
fish_add_path ~/.local/bin                   # fish. bash면 ~/.bashrc에 export PATH=$HOME/.local/bin:$PATH
```

conda로 설치한 tmux는 conda 환경의 bin에 있으므로 `ln -s "$(which tmux)" ~/.local/bin/tmux`로 cron에서도 보이게 한다.
- 지갑 키(`shop_wallet.key`, `buyer_wallet.key`)가 바뀌면 다른 가게가 된다. 지우지 말 것.
- 11-24 19:27에 Mac에서 처음 join해서 지갑 키는 Mac의 `round-4/`에 있다. 서버로 옮길 때는 Mac의 kit을 멈춘 뒤 `scp round-4/*_wallet.key round-4/.kit/owner.env 서버:~/ai-agent-engineering-101/submissions/26510358/round-4/`(owner.env는 `.kit/` 안에)로 복사하고 서버에서 `up`한다. 두 곳에서 동시에 돌리지 않는다.

## 1. 최신 코드 받기

Mac에서 push한 뒤 서버에서:

```bash
cd ~/ai-agent-engineering-101 && git pull
```

## 2. 켜기

```bash
submissions/26510358/round-4/ops/run_server.sh up
```

`~/.config/systemd/user/shop-*.service`를 만들고 `enable --now`한다. 프로세스가 죽으면 10초 뒤 systemd가 다시 켜고,
서버 재부팅 뒤에도 자동으로 켜진다. 유닛 파일은 `up`할 때마다 그때의 `LLM`, `NAME`, `MARKET`, `APP_FLAGS`, `KIT_FLAGS`로 다시 쓴다.
출력은 `round-4/.kit/{shim,kit,mesh}.log`에 쌓인다. `.kit/`는 git에 올라가지 않는다(접근 코드가 찍히기 때문).

이름이나 시장을 바꾸려면 환경변수로 넘긴다: `NAME=다른이름 MARKET=https://... ops/run_server.sh up`.

## 3. 앱 주소 받기

1분쯤 뒤:

```bash
submissions/26510358/round-4/ops/run_server.sh link
# https://abc-def.trycloudflare.com/?k=XXXXXXXX
```

- **아이폰 앱**: 첫 화면 입력칸에 이 주소를 통째로 붙여 넣는다.
- **브라우저**(Windows, Mac 어디든): 주소창에 붙여 넣는다. 설치 없이 열린다. "앱 설치"로 PWA로 둘 수도 있다.
- 이 주소는 접근 코드가 들어간 열쇠다. 채팅방이나 커밋에 올리지 않는다.

## 4. 평소에 쓰는 명령

| 하고 싶은 것 | 명령 |
|---|---|
| 서비스 상태 | `systemctl --user status shop-kit` |
| 로그 보기 | `tail -f submissions/26510358/round-4/.kit/kit.log` |
| 코드 바꾼 뒤 반영 | `git pull` 후 `ops/run_server.sh restart` |
| shim만 재시작 | `ops/run_server.sh restart shim` |
| 다 끄기 | `ops/run_server.sh down` |
| 상태 한눈에 (창, 최근 이벤트, 모델 실패, 오늘 토큰, 디스크) | `ops/run_server.sh status` |
| OpenAI 장애 때 시장 모델로 전환 | `ops/run_server.sh down && LLM=market ops/run_server.sh up` |

`tail -f`는 `Ctrl-c`로 빠져나와도 kit에 영향이 없다. 설정(LLM, NAME 등)을 바꾸려면 `down` 후 새 환경변수로 `up`.

## 5. 서버 재부팅 대비

systemd 서비스는 `enable`돼 있어 재부팅 뒤 자동으로 켜진다(linger 필요). crontab `@reboot`는 필요 없다.
`BACKEND=tmux`로 돌릴 때만 `@reboot …/ops/run_server.sh up`을 crontab에 넣는다.

재부팅 뒤에는 앱 주소가 바뀌므로 `run_server.sh link`로 새 주소를 받아 앱에 다시 넣는다.

## 6. 주소가 바뀌는 때와 고정하는 법

`--app-tunnel`은 Cloudflare quick tunnel이라 **kit이 다시 켜질 때마다 주소가 바뀐다**
(재시작, 크래시 후 자동 재시작, 서버 재부팅). kit은 가게 A2A 터널은 스스로 다시 열지만 앱 터널은 다시 열지 않는다
(`scripts/round4/agent_kit.py` 862–877행에는 `--tunnel`만 있다). 앱이 갑자기 안 붙으면 먼저 `run_server.sh link`.

자주 바뀌어 번거로우면 앱만 고정 주소로 바꾼다. kit은 `--app-host 0.0.0.0`으로 띄워 접근 코드를 유지하고,
그 앞에 고정 터널을 하나 둔다.

```bash
APP_FLAGS="--app 8800 --app-host 0.0.0.0" ops/run_server.sh up
```

- Cloudflare 계정에 도메인이 있으면: named tunnel(`cloudflared tunnel create ssadassa`, `cloudflared tunnel route dns ssadassa ssadassa.<도메인>`, `cloudflared tunnel run --url http://127.0.0.1:8800 ssadassa`)을 서비스 하나로 더 띄운다(`shop-kit.service`를 본떠 `~/.config/systemd/user/`에). 주소는 `https://ssadassa.<도메인>/?k=<.kit/app.key 내용>`으로 고정.
- 도메인이 없으면: Tailscale(`tailscale serve --bg 8800`), 주소는 `https://<서버>.<tailnet>.ts.net/?k=…`. 폰과 노트북에도 Tailscale 앱이 필요하고, 서버에 tailscaled를 띄울 수 있어야 한다.
- `0.0.0.0`은 학교망에도 8800 포트를 연다. 접근 코드가 막아 주지만 서버 정책을 먼저 확인한다.
- iOS 앱은 https 주소만 쓴다(Info.plist에는 로컬 네트워크 예외만 있음). Tailscale IP(`http://100.x…`)를 직접 넣으면 막힌다.

## 7. 안 될 때

| 증상 | 확인 |
|---|---|
| `link`가 "no link yet" | `tail -50 .kit/kit.log`. join 거절이면 claim code(`owner.env`) 문제, `cloudflared` 오류면 cloudflared 설치·네트워크 |
| 앱이 "연결 실패" | kit이 재시작돼 주소가 바뀜. `link`로 새 주소 |
| 에이전트가 말을 안 함 | `tail .kit/shim.log`. `OPENAI_API_KEY is not set`이면 `.env` 경로, 400이면 모델 설정 |
| 같은 오류로 10초마다 재시작 | `grep exited .kit/kit.log`로 반복 확인 후 `run_server.sh down`, 원인 고치고 다시 `up` |
| 서비스가 inactive | `systemctl --user status shop-kit`, `journalctl --user -u shop-kit -n 50`. 로그아웃 뒤 꺼졌으면 linger 확인 |

## 비용

에이전트는 최대 120초마다 깨어나고 한 번에 모델 호출이 최대 40번이다(`agent.json`의 `max_steps`).
첫날은 `logs/llm-shim.jsonl`의 토큰 사용량을 보고 `max_steps`, `run_minutes`를 조정한다.
