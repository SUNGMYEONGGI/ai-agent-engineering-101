#!/usr/bin/env bash
# Keep the shop running on the server, independent of any SSH/VSCode session.
#   ops/run_server.sh up        open tmux session "shop": windows shim, kit (and mesh if ~/meshkit exists)
#   ops/run_server.sh link      print the latest owner-app link (https://...trycloudflare.com/?k=...)
#   ops/run_server.sh restart   restart the kit (after git pull); "restart shim" for the shim
#   ops/run_server.sh down      stop everything
# Each window restarts its process 10 s after it exits. Output goes to round-4/.kit/<name>.log,
# which is git-ignored on purpose: the kit prints the app link with its access code there.
set -uo pipefail
SELF=$(cd "$(dirname "$0")" && pwd)/$(basename "$0")
R=$(cd "$(dirname "$SELF")/.." && pwd)          # submissions/26510358/round-4
ROOT=$(cd "$R/../../.." && pwd)                 # repository root
S=$ROOT/submissions/26510358
PY=${PY:-$HOME/.venvs/round4/bin/python}
NAME=${NAME:-myeonggi}
MARKET=${MARKET:-https://market.ourolabs.ai}
SESSION=${SESSION:-shop}
read -r -a APP <<< "${APP_FLAGS:---app 8800 --app-tunnel}"
export PYTHONUNBUFFERED=1                       # logs reach .kit/*.log at once, not when a buffer fills
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
    tmux new-session -d -s "$SESSION" -n shim "$SELF shim"
    [ -d "$HOME/meshkit/meshkit-py" ] && tmux new-window -d -t "$SESSION" -n mesh "$SELF mesh"
    sleep 3                                     # the shim must answer before the agent's first model call
    tmux new-window -d -t "$SESSION" -n kit "$SELF kit"
    echo "up. watch: tmux attach -t $SESSION   app link (after ~1 min): $SELF link" ;;
  shim)
    set -a; . "$S/.env"; set +a
    forever shim "$PY" "$R/ops/llm_shim.py" ;;
  mesh)
    export PORT=18765; cd "$HOME/meshkit/meshkit-py" && forever mesh "$PY" -I examples/miniapp_server.py ;;
  kit)
    set -a; . "$S/.env"; . "$S/week-08/.market/owner.env"; set +a
    forever kit "$PY" scripts/round4/agent_kit.py run --dir "$R" --market "$MARKET" --name "$NAME" --tunnel "${APP[@]}" ;;
  link)
    grep -o 'https://[^ ]*?k=[^ ]*' "$R/.kit/kit.log" 2>/dev/null | tail -1 || echo "no link yet: is the kit up?" ;;
  restart)
    tmux respawn-window -k -t "$SESSION:${2:-kit}" ;;
  down)
    tmux kill-session -t "$SESSION" ;;
  *)
    echo "usage: $0 up|link|restart [kit|shim|mesh]|down"; exit 2 ;;
esac
