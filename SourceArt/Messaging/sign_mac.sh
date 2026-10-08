#!/bin/bash
# Signs MyProject/Packaged/Messanger.app with Developer ID (hardened runtime, sandbox entitlement only), notarizes it
# and staples the ticket. Output: MyProject/Packaged/Messanger.zip, ready to share. Run after package_mac.sh.
# Needs the "Developer ID Application: Maksym Bondar (P8F3YS69A4)" cert and the notarytool keychain profile ff-notary.
# usage: ./sign_mac.sh
set -e
PROJ="$(cd "$(dirname "$0")/../.." && pwd)"
APP="$PROJ/Packaged/Messanger.app"
ZIP="$PROJ/Packaged/Messanger.zip"
ID="Developer ID Application: Maksym Bondar (P8F3YS69A4)"
ENT="$(mktemp -t messanger).entitlements"
cat > "$ENT" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>com.apple.security.app-sandbox</key><true/></dict></plist>
PLIST

plutil -replace CFBundleIdentifier -string "com.maxbondar.messanger" "$APP/Contents/Info.plist"
plutil -replace CFBundleName -string "Messanger" "$APP/Contents/Info.plist"
plutil -replace CFBundleDisplayName -string "Messanger" "$APP/Contents/Info.plist"

# inner code first (real files only, symlinks follow their targets), then the app itself with the entitlements
find "$APP/Contents/UE" -type f \( -name "*.dylib" -o -perm -u+x \) | while read -r f; do
  codesign --force --timestamp --options runtime --sign "$ID" "$f"
done
codesign --force --timestamp --options runtime --entitlements "$ENT" --sign "$ID" "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"

rm -f "$ZIP" && ditto -c -k --keepParent "$APP" "$ZIP"
xcrun notarytool submit "$ZIP" --keychain-profile ff-notary --wait
xcrun stapler staple "$APP"
rm -f "$ZIP" && ditto -c -k --keepParent "$APP" "$ZIP"   # re-zip so the shared copy carries the stapled ticket
spctl --assess --type execute --verbose=2 "$APP"
du -h "$ZIP"
