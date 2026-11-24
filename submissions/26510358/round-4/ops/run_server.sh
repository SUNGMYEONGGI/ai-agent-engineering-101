#!/usr/bin/env bash
# Keep the shop running on the server, independent of any SSH/VSCode session.
#   ops/run_server.sh up        open tmux session "shop": windows shim, kit (and mesh if ~/meshkit exists)
#   ops/run_server.sh link      print the latest owner-app link (https://...trycloudflare.com/?k=...)
#   ops/run_server.sh restart   restart the kit (after git pull); "restart shim" for the shim
#   ops/run_server.sh down      stop everything
#   ops/run_server.sh status    windows alive, recent kit events, model failures, today's tokens, disk
# Env: LLM=market (default) uses the market's model desk (no shim, no key), LLM=own the shim, KIT_FLAGS="--with-buyer" adds kit flags.
# Each window restarts its process 10 s after it exits. Output goes to round-4/.kit/<name>.log,
# which is git-ignored on purpose: the kit prints the app link with its access code there.
set -uo pipefail
SELF=$(cd "$(dirname "$0")" && pwd)/$(basename "$0")
R=$(cd "$(dirname "$SELF")/.." && pwd)          # submissions/26510358/round-4
ROOT=$(cd "$R/../../.." && pwd)                 # repository root
S=$ROOT/submissions/26510358
PY=${PY:-$HOME/.venvs/round4/bin/python}
NAME=${NAME:-Hermes Shop}
LLM=${LLM:-market}                              # market = the model desk; LLM=own uses ops/llm_shim.py and the key in .env
MARKET=${MARKET:-https://market.ourolabs.ai}
SESSION=${SESSION:-shop}
read -r -a APP <<< "${APP_FLAGS:---app 8800 --app-tunnel}"
read -r -a EXTRA <<< "${KIT_FLAGS:-}"
export PATH="$HOME/.local/bin:$PATH"            # cloudflared/tmux installed without root; cron has no login PATH
export PYTHONUNBUFFERED=1                      # logs reach .kit/*.log at once, not when a buffer fills
mkdir -p "$R/.kit"
cd "$ROOT"

forever() {                                     # name, command...
  local name=$1; shift
  while true; do
    echo "[$(date '+%F %T')] start $name" | tee -a "$R/.kit/$name.log"
    "$@" 2>&1 | tee -a "$R/.kit/$name.log"
    echo "[$(date '+%F %T')] $name exited, restart in 10 s" | tee -a "$R/.kit/$name.log"
    sleep 10
  done
}

case "${1:-}" in
  up)
    if tmux has-session -t "$SESSION" 2>/dev/null; then echo "already up: tmux attach -t $SESSION"; exit 0; fi
    KIT=$(printf "LLM=%q NAME=%q %q kit" "$LLM" "$NAME" "$SELF")   # tmux windows do not see this shell's env; respawn reuses it
    if [ "${LLM:-}" = market ]; then            # the market's model desk needs no shim
      tmux new-session -d -s "$SESSION" -n kit "$KIT"
    else
      tmux new-session -d -s "$SESSION" -n shim "$SELF shim"
      sleep 3                                   # the shim must answer before the agent's first model call
      tmux new-window -d -t "$SESSION" -n kit "$KIT"
    fi
    [ -d "$HOME/meshkit/meshkit-py" ] && tmux new-window -d -t "$SESSION" -n mesh "$SELF mesh"
    echo "up. watch: tmux attach -t $SESSION   app link (after ~1 min): $SELF link" ;;
  shim)
    set -a; . "$S/.env"; set +a
    forever shim "$PY" "$R/ops/llm_shim.py" ;;
  mesh)
    export PORT=18765; cd "$HOME/meshkit/meshkit-py" && forever mesh "$PY" -I examples/miniapp_server.py ;;
  kit)
    set -a; . "$S/.env"; . "$S/week-08/.market/owner.env"; set +a
    [ "${LLM:-}" = market ] && export AGENT_LLM_BASE=market
    forever kit "$PY" scripts/round4/agent_kit.py run --dir "$R" --market "$MARKET" --name "$NAME" --tunnel \
      "${APP[@]}" ${EXTRA[@]+"${EXTRA[@]}"} ;;
  link)
    grep -o 'https://[^ ]*?k=[^ ]*' "$R/.kit/kit.log" 2>/dev/null | tail -1 || echo "no link yet: is the kit up?" ;;
  status)
    tmux list-windows -t "$SESSION" -F '#{window_name} #{?pane_dead,DEAD,alive}' 2>/dev/null || echo "tmux session $SESSION is not up"
    echo "--- recent kit events"
    grep -E '\[(tunnel|market|kit|mind|maroo)\]' "$R/.kit/kit.log" 2>/dev/null | grep -v '?k=' | tail -8
    echo "--- model failures in the last 500 kit lines: $(tail -500 "$R/.kit/kit.log" 2>/dev/null | grep -c 'model call failed')"
    "$PY" - "$R/logs/llm-shim.jsonl" <<'PY' 2>/dev/null
import json, sys, time
day = time.strftime("%F"); n = tok = bad = 0
for line in open(sys.argv[1]):
    r = json.loads(line)
    if time.strftime("%F", time.localtime(r["ts"])) == day:
        n += 1; bad += r.get("status") != 200; tok += (r.get("usage") or {}).get("total_tokens", 0)
print(f"--- shim today: {n} calls, {bad} not 200, {tok:,} tokens")
PY
    echo "--- disk: $(du -sh "$R/.kit" "$R/logs" 2>/dev/null | tr '\n' ' ')  free: $(df -h "$R" | awk 'NR==2{print $4}')" ;;
  restart)
    tmux respawn-window -k -t "$SESSION:${2:-kit}" ;;
  down)
    tmux kill-session -t "$SESSION" ;;
  *)
    echo "usage: $0 up|link|status|restart [kit|shim|mesh]|down"; exit 2 ;;
esac
