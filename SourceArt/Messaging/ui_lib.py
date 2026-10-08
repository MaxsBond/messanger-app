# Generates an execute_tool_script payload that rebuilds Figma "Examples/Messaging-Web" (1:4600)
# inside /Game/WBP_Test using UMG widgets.
import json, sys

ICONS = "/Game/UI/Messaging/Icons/"
FONT = "/Engine/EngineFonts/Roboto.Roboto"


def lin(hex_, a=1.0):
    h = hex_.lstrip("#")
    def c(x):
        x = int(x, 16) / 255
        return round(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4, 6)
    return {"r": c(h[0:2]), "g": c(h[2:4]), "b": c(h[4:6]), "a": a}


def slate(hex_, a=1.0):
    return {"specifiedColor": lin(hex_, a), "colorUseRule": "UseColor_Specified"}


def m(l=0, t=0, r=0, b=0):
    return {"left": l, "top": t, "right": r, "bottom": b}


def rounded(hex_, radii, a=1.0, outline=None, outline_w=1):
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * 4
    tl, tr, br, bl = radii
    return {"drawAs": "RoundedBox", "tintColor": slate(hex_, a),
            "outlineSettings": {"cornerRadii": {"x": tl, "y": tr, "z": br, "w": bl},
                                "roundingType": "FixedRadius", "width": outline_w if outline else 0,
                                "color": slate(outline or hex_, 1 if outline else 0)}}


def pill(hex_, w, h, radius, a=1.0):
    # rounded brush with its own size, for Image widgets (waveform bars, dots)
    b = rounded(hex_, radius, a)
    b["imageSize"] = {"x": w, "y": h}
    return b


def solid(hex_, a=1.0, w=32, h=32):
    return {"drawAs": "Image", "tintColor": slate(hex_, a), "imageSize": {"x": w, "y": h}}


def tex_brush(tex, w, h, hex_="#ffffff", a=1.0):
    return {"drawAs": "Image", "resourceObject": {"refPath": ICONS + tex + "." + tex},
            "imageSize": {"x": w, "y": h}, "tintColor": slate(hex_, a)}


def font(size, spacing_px=0.0, face="Regular"):
    # UE letterSpacing is in 1/1000 em; stored font size is in points at 96 DPI, Figma px are 72 DPI
    return {"fontObject": {"refPath": FONT}, "typefaceFontName": face, "size": round(size * 0.75, 2),
            "letterSpacing": int(round(spacing_px / size * 1000))}


def N(cls, name, props=None, slot=None, children=(), var=False):
    return {"cls": cls, "name": name, "props": props or {}, "slot": slot or {}, "children": list(children), "var": var}


def V(node):
    node["var"] = True
    return node


def S(pad=None, h=None, v=None, fill=None):
    s = {}
    if pad is not None:
        s["padding"] = m(*pad)
    if h:
        s["horizontalAlignment"] = "HAlign_" + h
    if v:
        s["verticalAlignment"] = "VAlign_" + v
    if fill is not None:
        s["size"] = {"sizeRule": "Fill" if fill else "Automatic", "value": 1}
    return s


def text(name, s, size, spacing, color, slot=None, face="Regular", ellipsis=False):
    p = {"text": s, "font": font(size, spacing, face), "colorAndOpacity": slate(color)}
    if ellipsis:
        p["textOverflowPolicy"] = "Ellipsis"
        p["clipping"] = "ClipToBounds"
    return N("TextBlock", name, p, slot)


def sizebox(name, w=None, h=None, slot=None, children=()):
    p = {}
    if w is not None:
        p.update({"bOverride_WidthOverride": True, "widthOverride": w})
    if h is not None:
        p.update({"bOverride_HeightOverride": True, "heightOverride": h})
    return N("SizeBox", name, p, slot, children)


def border(name, brush, pad=(0, 0, 0, 0), slot=None, children=(), h=None, v=None, clip=False):
    p = {"background": brush, "padding": m(*pad)}
    if h:
        p["horizontalAlignment"] = "HAlign_" + h
    if v:
        p["verticalAlignment"] = "VAlign_" + v
    if clip:
        p["clipping"] = "ClipToBounds"
    return N("Border", name, p, slot, children)


def icon(name, tex, gw, gh, box, color, slot=None, a=1.0):
    return sizebox(name, box, box, slot, [
        N("Image", name + "Glyph", {"brush": tex_brush(tex, gw, gh, color, a)}, S(h="Center", v="Center"))])


def avatar(name, size, slot=None):
    return sizebox(name, size, size, slot, [
        border(name + "Bg", rounded("#ece6f0", size / 2), h="Center", v="Center", children=[
            N("Image", name + "Art", {"brush": tex_brush("T_Placeholder", size, size)})])])


def bubble(name, s, bg, fg, radii, slot=None):
    return border(name, rounded(bg, radii), (16, 10, 16, 10), slot,
                  [text(name + "Text", s, 16, 0.5, fg)])




# execute_tool_script body: (re)creates each WBP in TARGETS, clears its root and rebuilds the tree.
BUILD_SCRIPT = r'''
import json
TARGETS = json.loads(%(targets)r)
errors = []
count = [0]

def tool(name, args):
    return execute_tool(name, json.dumps(args))

def setp(obj, values, where):
    for k, v in values.items():
        r = tool("editor_toolset.toolsets.object.ObjectTools.set_properties", {"instance": obj, "values": json.dumps({k: v})})
        if not r["returnValue"]:
            errors.append(where + "." + k + ": returned false")

def build(wbp, node, parent):
    a = {"widgetBlueprint": wbp, "widgetClass": {"refPath": node["cls"] if node["cls"].startswith("/") else "/Script/UMG." + node["cls"]}, "widgetDisplayName": node["name"]}
    if parent is not None:
        a["parentWidget"] = parent
    info = tool("UMGToolSet.UMGToolSet.AddWidget", a)["returnValue"]
    count[0] += 1
    if node["var"]:
        tool("UMGToolSet.UMGToolSet.ToggleWidgetAsVariable", {"widgetBlueprint": wbp, "widget": info["widget"], "bIsVariable": True})
    if node["props"]:
        setp(info["widget"], node["props"], node["name"])
    if node["slot"] and isinstance(info["slot"], dict):
        setp(info["slot"], node["slot"], node["name"] + ".slot")
    for c in node["children"]:
        build(wbp, c, info["widget"])

def run():
    compiled = {}
    for folder, name, tree in TARGETS:
        path = folder + "/" + name
        exists = tool("editor_toolset.toolsets.asset.AssetTools.exists", {"path": path})["returnValue"]
        if not exists:
            tool("UMGToolSet.UMGToolSet.CreateWidgetBlueprint", {"folderPath": folder, "assetName": name, "parentClass": {"refPath": "/Script/UMG.UserWidget"}})
        wbp = {"refPath": path + "." + name}
        for w in tool("UMGToolSet.UMGToolSet.GetWidgets", {"widgetBlueprint": wbp})["returnValue"]["widgets"]:
            if not isinstance(w["parent"], dict) and not isinstance(w["namedSlotHost"], dict):
                tool("UMGToolSet.UMGToolSet.RemoveWidget", {"widgetBlueprint": wbp, "widget": w["widget"]})
        build(wbp, tree, None)
        try:
            compiled[name] = tool("UMGToolSet.UMGToolSet.CompileWidgetBlueprint", {"widgetBlueprint": wbp})
        except Exception as e:
            compiled[name] = "compile failed (graphs need rewrite): " + str(e)[:200]
    return {"widgets": count[0], "errors": errors, "compile": compiled}
'''


def write_payload(targets, out_path, only=None):
    targets = [t for t in targets if not only or t[1] in only]
    script = BUILD_SCRIPT % {"targets": json.dumps(targets)}
    payload = {"name": "call_tool", "arguments": {
        "toolset_name": "editor_toolset.toolsets.programmatic.ProgrammaticToolset",
        "tool_name": "execute_tool_script", "arguments": {"script": script}}}
    json.dump(payload, open(out_path, "w"))
    print("targets:", [t[1] for t in targets])
