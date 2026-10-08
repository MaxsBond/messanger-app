# One-off migration for an existing WBP_MessagingLayout: swaps the "Conversations" header for the one in gen_layout.py
# (title + Demo button) without rebuilding the whole tree. A full gen_layout.py rebuild already contains it.
# Then run gen_layout_motion.py to wire DemoButton -> ToggleDemo.
# usage: python3 add_demo_button.py
import json
from ue_mcp import call, UMG_TOOLS, OBJ_TOOLS
from gen_layout import conversations

REF = {"refPath": "/Game/UI/Messaging/WBP_MessagingLayout.WBP_MessagingLayout"}


def find(node, name):
    if node["name"] == name:
        return node
    for c in node["children"]:
        hit = find(c, name)
        if hit:
            return hit


def setp(obj, values, where):
    for k, v in values.items():
        if not call(OBJ_TOOLS, "set_properties", {"instance": obj, "values": json.dumps({k: v})}):
            print("warn: %s.%s not set" % (where, k))


def build(node, parent):
    cls = node["cls"] if node["cls"].startswith("/") else "/Script/UMG." + node["cls"]
    info = call(UMG_TOOLS, "AddWidget", {"widgetBlueprint": REF, "widgetClass": {"refPath": cls},
                                         "widgetDisplayName": node["name"], "parentWidget": parent})
    if node["var"]:
        call(UMG_TOOLS, "ToggleWidgetAsVariable", {"widgetBlueprint": REF, "widget": info["widget"], "bIsVariable": True})
    setp(info["widget"], node["props"], node["name"])
    if node["slot"] and isinstance(info["slot"], dict):
        setp(info["slot"], node["slot"], node["name"] + ".slot")
    for c in node["children"]:
        build(c, info["widget"])


def main():
    widgets = {w["widgetName"]: w for w in call(UMG_TOOLS, "GetWidgets", {"widgetBlueprint": REF})["widgets"]}
    if "DemoButton" in widgets:
        print("DemoButton already there")
        return
    header = widgets["SectionHeader"]["widget"]
    for name in ("SectionHeaderRow", "SectionTitle"):
        if name in widgets:
            call(UMG_TOOLS, "RemoveWidget", {"widgetBlueprint": REF, "widget": widgets[name]["widget"]})
    build(find(conversations, "SectionHeaderRow"), header)
    print("compile:", call(UMG_TOOLS, "CompileWidgetBlueprint", {"widgetBlueprint": REF}))


if __name__ == "__main__":
    main()
