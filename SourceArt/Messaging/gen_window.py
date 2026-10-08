# Shipping window = the Figma frame, 905x744 pt = 1810x1488 physical px on Retina (the Mac build is Retina-aware:
# NSHighResolutionCapable in Build/Mac/Resources/Info.Template.plist + bAllowHighDPIInGameMode; UI scale 2.0 in
# Config/DefaultEngine.ini). The startup size can't be that big: the engine clamps it to the display size measured in
# points (1710x1107), and -ForceRes can't be passed (the Mac app doesn't read UECommandLine.txt). So BP_UIGameMode
# re-applies it on BeginPlay without the clamp pass (bCheckForCommandLineOverrides = false). Shipping only
# (IsPackagedForDistribution), so PIE and Development builds keep their window.
# usage: python3 gen_window.py
from ue_mcp import call, BP_TOOLS, ASSET_TOOLS

GM = "/Game/UI/Messaging/BP_UIGameMode"
REF = {"refPath": GM + ".BP_UIGameMode"}
W, H = 1810, 1488

BEGIN_PLAY = f'''(event EventBeginPlay
  (if (Development|IsPackagedforDistribution)
    (bind s (Settings|GetGameUserSettings))
    (Settings|SetFullscreenMode :self s :InFullscreenMode "Windowed")
    (Settings|SetScreenResolution :self s :Resolution (Utilities|Struct|MakeIntPoint :X {W} :Y {H}))
    (Settings|ApplyResolutionSettings :self s :bCheckForCommandLineOverrides false)))'''


def main():
    eg = {"refPath": REF["refPath"] + ":EventGraph"}
    begin = call(BP_TOOLS, "find_nodes", {"graph": eg, "title": "BeginPlay", "entry_points_only": True})[0]
    for info in call(BP_TOOLS, "get_connected_subgraph", {"node": begin}):  # clear the old body, then rewrite
        node = (info["output_pins"] or info["input_pins"])[0]["pin_id"]["node"]
        if node != begin:
            call(BP_TOOLS, "delete_node", {"node": node})
    call(BP_TOOLS, "write_graph_dsl", {"graph": eg, "code": BEGIN_PLAY})
    print("compile:", call(BP_TOOLS, "compile_blueprint", {"blueprint": REF}))
    print(call(BP_TOOLS, "read_graph_dsl", {"graph": eg}))
    print("saved:", call(ASSET_TOOLS, "save_assets", {"asset_paths": [REF["refPath"]]}))


if __name__ == "__main__":
    main()
