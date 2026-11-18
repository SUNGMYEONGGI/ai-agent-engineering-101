#!/bin/bash
# Build 싸다싸 가게 and open it in the iOS Simulator (macOS + Xcode only).
#   ./run-simulator.sh              demo mode (no agent needed)
#   ./run-simulator.sh "<link>"     connect to the agent's mini app ([app] open https://...?k=...)
#   DEVICE="iPhone 15" ./run-simulator.sh
set -euo pipefail
cd "$(dirname "$0")"
LINK="${1:-}"
DEVICE="${DEVICE:-}"
BUNDLE=kr.ac.seoultech.s26510358.ssadassa

command -v xcodebuild >/dev/null || { echo "Xcode가 필요합니다 (macOS)."; exit 1; }
if [ -z "$DEVICE" ]; then   # the newest available iPhone simulator
  DEVICE=$(xcrun simctl list devices available | grep -E '^\s+iPhone' | tail -1 | sed -E 's/^ +//; s/ \(.*//')
fi
UDID=$(xcrun simctl list devices available | grep -F "    $DEVICE (" | head -1 | grep -oE '[0-9A-F-]{36}')
[ -n "$UDID" ] || { echo "시뮬레이터 '$DEVICE'를 찾지 못했습니다: xcrun simctl list devices available"; exit 1; }
echo "[sim] $DEVICE ($UDID)"
xcrun simctl boot "$UDID" 2>/dev/null || true
open -a Simulator
xcodebuild -project Ssadassa.xcodeproj -target Ssadassa -configuration Debug -sdk iphonesimulator \
  -arch "$(uname -m | sed 's/x86_64/x86_64/; s/arm64/arm64/')" SYMROOT="$PWD/build" CODE_SIGNING_ALLOWED=NO \
  -quiet build
xcrun simctl install "$UDID" build/Debug-iphonesimulator/Ssadassa.app
xcrun simctl terminate "$UDID" "$BUNDLE" 2>/dev/null || true
if [ -n "$LINK" ]; then
  xcrun simctl launch "$UDID" "$BUNDLE" -link "$LINK"
else
  xcrun simctl launch "$UDID" "$BUNDLE" -demo
fi
echo "[sim] 실행했습니다. 다크 모드: xcrun simctl ui $UDID appearance dark"
