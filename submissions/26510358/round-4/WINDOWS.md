# Windows 데스크탑을 가게 서버로 쓰기 (WSL2 + tmux)

개발은 MacBook에서 하고, 가게(kit)는 쓰지 않는 Windows 데스크탑에서 24시간 돌린다.
Windows 안에 WSL2 Ubuntu를 두면 `ops/run_server.sh`(bash, tmux)를 SMC 서버와 똑같이 쓸 수 있다.

```
MacBook (개발)                          Windows 데스크탑 (24시간)
  코드 수정 → git push                     WSL2 Ubuntu
  ssh(Tailscale)로 상태 확인  ───────────▶    tmux "shop": kit (+ shim, LLM=own일 때)
                                              cloudflared 터널 → 시장, 주인 앱
```

터널은 바깥으로 나가는 연결만 쓰므로 공유기 포트 포워딩이나 방화벽 설정은 필요 없다.

## 1. Windows 설정 (한 번)

꺼지거나 재시작되면 가게가 닫힌다. 아래를 먼저 막는다.

| 항목 | 위치 | 값 |
|---|---|---|
| 절전 | 설정 > 시스템 > 전원 | 화면 끄기는 자유, **절전 모드: 안 함** |
| 최대 절전 | 관리자 PowerShell | `powercfg /hibernate off` |
| 업데이트 재시작 | 설정 > Windows 업데이트 > 고급 옵션 | 사용 시간을 넓게 잡고, 필요하면 업데이트 일시 중지 |
| 자동 로그인 | `netplwiz` 또는 설정 > 계정 > 로그인 옵션 | 재부팅 뒤 자동으로 로그인되게(2번의 작업이 로그인 때 시작됨) |
| 정전 후 켜짐 | BIOS/UEFI | "Restore on AC power loss: Power On"이 있으면 켠다 |

## 2. WSL2와 Ubuntu

관리자 PowerShell:

```powershell
wsl --install -d Ubuntu-24.04
```

재부팅 후 Ubuntu 창에서 사용자 이름과 비밀번호를 정한다. 이후 명령은 모두 Ubuntu 안에서 친다.

```bash
sudo apt update && sudo apt install -y git tmux curl
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cf.deb && sudo apt install -y /tmp/cf.deb
curl -LsSf https://astral.sh/uv/install.sh | sh && . ~/.local/bin/env
uv venv --python 3.12 ~/.venvs/round4
VIRTUAL_ENV=~/.venvs/round4 uv pip install "a2a-sdk[http-server]" uvicorn httpx eth-account coincurve
```

저장소 받기(push도 할 것이므로 GitHub 인증이 필요하다. `gh auth login` 또는 토큰):

```bash
git clone https://github.com/SUNGMYEONGGI/ai-agent-engineering-101.git ~/ai-agent-engineering-101
cd ~/ai-agent-engineering-101 && git checkout round-4
git config user.name "<Mac과 같은 이름>" && git config user.email "<Mac과 같은 메일>"
```

## 3. Mac에서 옮겨 올 것

지갑 키가 곧 가게다. 같은 키로 두 곳에서 동시에 돌리면 안 되므로 **Mac의 kit을 먼저 멈춘다.**

Mac에서:

```bash
pkill -f agent_kit.py
cd ~/Desktop/ai-agent-engineering-101
git add submissions/26510358/round-4/logs submissions/26510358/round-4/tools && git commit -m "round-4: logs and tools from the Mac run" && git push
tar czf ~/r4-state.tgz -C submissions/26510358 --exclude 'round-4/ios' --exclude 'round-4/.kit/*.log' round-4
```

`r4-state.tgz`에는 git에 없는 파일이 다 들어 있다: `shop_wallet.key`, `buyer_wallet.key`, `.kit/owner.env`(claim code), `.kit/app.key`(앱 접속 코드), 에이전트가 쓴 `notes.md`, `customers.jsonl`, `pay_log.json` 같은 상태 파일.
USB나 4번의 scp로 데스크탑에 옮긴 뒤 Ubuntu에서:

```bash
cd ~/ai-agent-engineering-101 && git pull
tar xzf /mnt/c/Users/<윈도우사용자>/r4-state.tgz -C submissions/26510358
ls submissions/26510358/round-4/*_wallet.key submissions/26510358/round-4/.kit/owner.env
rm /mnt/c/Users/<윈도우사용자>/r4-state.tgz
```

`r4-state.tgz`에는 지갑 키가 평문으로 들어 있다. 옮긴 뒤 Mac과 Windows 양쪽에서 지운다.

## 4. Mac에서 원격으로 들어가기 (Tailscale + OpenSSH)

1. Mac과 Windows 둘 다 Tailscale을 설치하고 같은 계정으로 로그인한다.
2. Windows 관리자 PowerShell에서 OpenSSH 서버를 켠다.

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd; Set-Service sshd -StartupType Automatic
```

3. Mac에서 `ssh <윈도우사용자>@<데스크탑의 Tailscale 이름>`으로 들어간 뒤 `wsl`을 치면 Ubuntu다.
   파일 복사는 `scp ~/r4-state.tgz <윈도우사용자>@<데스크탑>:`(Windows 홈으로 감).

## 5. 가게 띄우기와 자동 시작

처음 한 번 Ubuntu에서 직접 띄워 본다. 모델은 기본값이 시장 model desk다(키 불필요).

```bash
cd ~/ai-agent-engineering-101
submissions/26510358/round-4/ops/run_server.sh up
submissions/26510358/round-4/ops/run_server.sh status     # 1~2분 뒤: shop joined as Hermes Shop
submissions/26510358/round-4/ops/run_server.sh link       # 주인 앱 링크(접속 코드 포함, 나만 본다)
```

WSL은 Windows 쪽에서 붙잡는 프로세스가 없으면 몇 초 뒤 Ubuntu를 멈춘다. 로그인할 때 `up`을 하고 `sleep infinity`로 붙잡아 두는 작업을 등록한다(관리자 PowerShell, 한 번):

```powershell
$a = New-ScheduledTaskAction -Execute "wsl.exe" -Argument '-d Ubuntu-24.04 -- bash -lc "cd ~/ai-agent-engineering-101 && submissions/26510358/round-4/ops/run_server.sh up; exec sleep infinity"'
$t = New-ScheduledTaskTrigger -AtLogOn
$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit 0 -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries
Register-ScheduledTask -TaskName "HermesShop" -Action $a -Trigger $t -Settings $s
```

재부팅해서 자동 로그인 뒤 `status`가 살아 있는지 확인한다. `up`은 이미 떠 있으면 아무것도 하지 않으므로 여러 번 불려도 된다.

## 6. 평소 흐름

| 할 일 | 어디서 | 명령 |
|---|---|---|
| goal, 앱, 스크립트 수정 | Mac | 수정 → commit → push |
| 반영 | 데스크탑(ssh → wsl) | `git pull && submissions/26510358/round-4/ops/run_server.sh restart` |
| 상태 보기 | 데스크탑 | `run_server.sh status`, `tmux attach -t shop`(나올 때 Ctrl-b d) |
| 에이전트 기록 commit | **데스크탑만** | `git add .../round-4/logs .../round-4/tools .../round-4/notes.md && git commit && git push` |

- `logs/`, `tools/`, `notes.md`는 데스크탑에서만 commit한다. Mac은 그 파일을 고치지 않고 pull만 한다. 그래야 두 곳의 commit이 같은 파일에서 부딪치지 않는다.
- Mac에서 kit을 다시 띄우지 않는다. 띄우면 같은 지갑으로 가게가 둘이 된다.
- 내 OpenAI 키로 바꿀 때(`LLM=own`)는 데스크탑 `submissions/26510358/.env`에 키를 넣고 `run_server.sh down` 후 `LLM=own run_server.sh up`. 자동 시작 작업의 명령에도 `LLM=own`을 붙인다.
