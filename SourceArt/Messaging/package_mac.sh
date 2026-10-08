#!/bin/bash
# Builds the Mac app: messanger-app/Packaged/Messanger.app (Shipping, self-contained, arm64 only, ad-hoc signed).
# Window size: Config/DefaultGameUserSettings.ini (905x744 physical px). UAT's -archive step doesn't find the app of a
# Blueprint-only project, so the staged .app is copied instead.
# usage: ./package_mac.sh [Shipping|Development]
set -e
CONFIG=${1:-Shipping}
PROJ="$(cd "$(dirname "$0")/../.." && pwd)"
/Volumes/Unreal/UE_5.8/Engine/Build/BatchFiles/RunUAT.sh BuildCookRun -project="$PROJ/MessangerApp.uproject" -platform=Mac \
  -clientconfig=$CONFIG -build -cook -stage -pak -nop4 -utf8output
APP="$PROJ/Saved/StagedBuilds/Mac/MessangerApp-Mac-$CONFIG.app"
[ -d "$APP" ] || APP="$PROJ/Saved/StagedBuilds/Mac/MessangerApp.app"
OUT="$PROJ/Packaged/Messanger.app"
rm -rf "$OUT" && mkdir -p "$PROJ/Packaged" && ditto "$APP" "$OUT"
# Apple Silicon only: the prebuilt engine binaries are universal, drop the x86_64 slices (~half the size), then re-sign
find "$OUT" -type f \( -perm -u+x -o -name "*.dylib" \) | while read -r f; do
  if lipo -archs "$f" 2>/dev/null | grep -q x86_64 && lipo -archs "$f" | grep -q arm64; then lipo -thin arm64 "$f" -output "$f.arm64" && mv "$f.arm64" "$f"; fi
done
codesign --force --deep --sign - "$OUT"
du -sh "$OUT"
echo "built $PROJ/Packaged/Messanger.app"
