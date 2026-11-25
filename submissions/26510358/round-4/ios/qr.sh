#!/bin/bash
# Print a QR code that opens 싸다싸 가게 on the iPhone and connects it to the shop (run on the Mac).
#   ./qr.sh              ssadassa://app.hermes-market.shop/?k=<code>  (camera -> "싸다싸 가게에서 열기")
#   ./qr.sh web          https://app.hermes-market.shop/?k=<code>     (camera -> Safari web app)
#   HOST=other.example ./qr.sh
# The QR holds the access code: do not screenshot or share it.
set -euo pipefail
HOST="${HOST:-app.hermes-market.shop}"
SERVER="${SERVER:-smc-gpu-server}"
command -v qrencode >/dev/null || { echo "qrencode가 필요합니다: brew install qrencode"; exit 1; }
K=$(ssh "$SERVER" 'cat ~/ai-agent-engineering-101/submissions/26510358/round-4/.kit/app.key')
[ -n "$K" ] || { echo "접근 코드를 읽지 못했습니다 ($SERVER)."; exit 1; }
if [ "${1:-}" = web ]; then SCHEME=https; else SCHEME=ssadassa; fi
printf '%s://%s/?k=%s' "$SCHEME" "$HOST" "$K" | qrencode -t ansiutf8
echo "[qr] $SCHEME://$HOST/?k=… (코드는 화면에만)"
