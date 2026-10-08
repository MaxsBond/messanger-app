# Demo data matching the Figma "Unreal Engine Target" conversation list (Emma Clarke ... Lucas Ward), for
# WBP_MessagingLayout: /Game/UI/Messaging/Data/Figma/DA_MessagingFigma + one DA_Conv_* / DA_Msg_* per conversation.
# Order and names follow the layout rows (gen_layout.py ROWS). The old /Data/Demo set (WBP_Test) is left alone.
# BP_ChatMessage.Kind: 0 = text (or link when bIsLink), 2 = voice note (Text = duration), 3 = typing indicator.
# usage: python3 gen_data_figma.py   (safe to rerun: assets are updated in place)
import json, time
from ue_mcp import call, BP_TOOLS, OBJ_TOOLS, ASSET_TOOLS

DATA = "/Game/UI/Messaging/Data"
FOLDER = DATA + "/Figma"
MSG_CLASS = DATA + "/BP_ChatMessage.BP_ChatMessage_C"
CONV_CLASS = DATA + "/BP_Conversation.BP_Conversation_C"
SCREEN_CLASS = DATA + "/BP_MessagingData.BP_MessagingData_C"
AVATAR = {"refPath": "/Game/UI/Messaging/Icons/T_Placeholder.T_Placeholder"}
PLACEHOLDER_IMG = {"refPath": "/Game/UI/Messaging/Icons/T_Placeholder.T_Placeholder"}

IN, OUT = False, True
# (name, time, messages, suggestions); message = (text, outgoing) | ("link", title, url) | ("voice", duration) | ("typing",)
CONVERSATIONS = [
    ("Emma Clarke", "2 min", [("link", "Homemade Dumplings", "everydumplingever.com"), ("or we could make this?", OUT),
                              ("that looks so good!", IN), ("voice", "0:03"), ("typing",)],
     ["Let's do it", "Great!", "I'm in"]),
    ("Liam Porter", "10 min", [("Hey, did you finish the slides?", IN), ("Almost, just polishing them", OUT),
                               ("Can you send the file?", IN)], ["Sending now", "In 5 min", "Sure!"]),
    ("Sofia Reyes", "25 min", [("Look what my cat did", OUT), ("Haha, love it", IN)], ["Right?", "She's a menace", "More soon"]),
    ("Noah Kim", "1 h", [("Lunch was great today", IN), ("Same, let's do it again", OUT), ("See you tomorrow", IN)],
     ["See you!", "Bye!", "Sounds good"]),
    ("Ava Brooks", "2 h", [("I moved the meeting to 3pm", OUT), ("Got it 👍", IN)], ["Thanks!", "Perfect", "See you there"]),
    ("Mason Hill", "3 h", [("Are you free on Friday?", OUT), ("Let me check and get back", IN)], ["No rush", "Thanks!", "Ok"]),
    ("Mia Turner", "5 h", [("Dinner at 7?", OUT), ("Sounds good", IN)], ["Great!", "See you", "I'll book it"]),
    ("Lucas Ward", "Yesterday", [("Deploy is done", OUT), ("Thanks for the update", IN)], ["Anytime", "No problem", "Will do"]),
]


def asset(name, cls):
    # AssetTools.exists lags behind for freshly created assets; the asset registry query does not
    path = "%s/%s" % (FOLDER, name)
    if path not in call(ASSET_TOOLS, "find_assets", {"folder_path": FOLDER, "name": name}):
        call("editor_toolset.toolsets.data_asset.DataAssetTools", "create",
             {"folder_path": FOLDER, "asset_name": name, "asset_type": {"refPath": cls}})
    return {"refPath": "%s.%s" % (path, name)}


def setp(obj, values):
    for k, v in values.items():
        if not call(OBJ_TOOLS, "set_properties", {"instance": obj, "values": json.dumps({k: v})}):
            raise RuntimeError("set %s on %s failed" % (k, obj["refPath"]))


def message_values(m):
    base = {"Text": "", "bOutgoing": True, "bIsLink": False, "LinkTitle": "", "LinkUrl": "", "Kind": 0}
    if m[0] == "link":
        base.update(bIsLink=True, LinkTitle=m[1], LinkUrl=m[2], LinkImage=PLACEHOLDER_IMG, Text=m[1])
    elif m[0] == "voice":
        base.update(Kind=2, Text=m[1])
    elif m[0] == "typing":
        base.update(Kind=3, bOutgoing=False)
    else:
        base.update(Text=m[0], bOutgoing=m[1])
    return base


def main():
    msg_bp = {"refPath": DATA + "/BP_ChatMessage.BP_ChatMessage"}
    if '"Kind"' not in json.dumps(call(BP_TOOLS, "list_variables", {"blueprint": msg_bp})):
        call(BP_TOOLS, "add_variable", {"blueprint": msg_bp, "name": "Kind", "type_name": "int"})
    call(BP_TOOLS, "set_variable_instance_editable", {"blueprint": msg_bp, "variable_name": "Kind", "instance_editable": True})
    call(BP_TOOLS, "compile_blueprint", {"blueprint": msg_bp})

    convs, saved = [], []
    for name, time, msgs, suggestions in CONVERSATIONS:
        key = name.replace(" ", "")
        refs = []
        for i, m in enumerate(msgs):
            ref = asset("DA_Msg_%s_%02d" % (key, i + 1), MSG_CLASS)
            setp(ref, message_values(m))
            refs.append(ref)
        conv = asset("DA_Conv_" + key, CONV_CLASS)
        setp(conv, {"Name": name, "Time": time, "Avatar": AVATAR, "Messages": refs, "Suggestions": suggestions})
        convs.append(conv)
        saved += [r["refPath"].split(".")[0] for r in refs + [conv]]
    screen = asset("DA_MessagingFigma", SCREEN_CLASS)
    setp(screen, {"Url": "www.url.com", "ProfileInitial": "M", "Conversations": convs, "SelectedConversation": 0})
    saved += [screen["refPath"].split(".")[0], DATA + "/BP_ChatMessage"]
    for attempt in range(10):  # save_assets refuses paths that AssetTools.exists doesn't see yet
        try:
            print("saved:", call(ASSET_TOOLS, "save_assets", {"asset_paths": saved}), len(saved), "assets")
            break
        except RuntimeError as e:
            if "does not exist" not in str(e) or attempt == 9:
                raise
            time.sleep(3)


if __name__ == "__main__":
    main()
