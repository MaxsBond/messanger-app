#!/bin/zsh
# Rebuilds the UMGAnimToolset editor plugin into MyProject/Plugins (Unreal Editor must be closed to load the new dylib).
set -e
HERE=${0:A:h}
PROJ=${HERE:h:h}
/Volumes/Unreal/UE_5.8/Engine/Build/BatchFiles/RunUAT.sh BuildPlugin -Plugin="$HERE/UMGAnimToolset.uplugin" \
  -Package="$PROJ/Plugins/UMGAnimToolset" -TargetPlatforms=Mac -Rocket
