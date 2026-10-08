# Generates an execute_tool_script payload that rebuilds Figma "Examples/Messaging-Web" (1:4600)
# inside /Game/WBP_Test using UMG widgets.
import json, sys

WBP_PATH = "/Game/WBP_Test.WBP_Test"
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


def rounded(hex_, radii, a=1.0):
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * 4
    tl, tr, br, bl = radii
    return {"drawAs": "RoundedBox", "tintColor": slate(hex_, a),
            "outlineSettings": {"cornerRadii": {"x": tl, "y": tr, "z": br, "w": bl},
                                "roundingType": "FixedRadius", "width": 0,
                                "color": slate(hex_, 0)}}


def solid(hex_, a=1.0, w=32, h=32):
    return {"drawAs": "Image", "tintColor": slate(hex_, a), "imageSize": {"x": w, "y": h}}


def tex_brush(tex, w, h, hex_="#ffffff", a=1.0):
    return {"drawAs": "Image", "resourceObject": {"refPath": ICONS + tex + "." + tex},
            "imageSize": {"x": w, "y": h}, "tintColor": slate(hex_, a)}


def font(size, spacing_px=0.0, face="Regular"):
    # UE letterSpacing is in 1/1000 em; stored font size is in points at 96 DPI, Figma px are 72 DPI
    return {"fontObject": {"refPath": FONT}, "typefaceFontName": face, "size": round(size * 0.75, 2),
            "letterSpacing": int(round(spacing_px / size * 1000))}


def N(cls, name, props=None, slot=None, children=()):
    return {"cls": cls, "name": name, "props": props or {}, "slot": slot or {}, "children": list(children)}


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


# ---------- browser bar ----------
nav_icons = N("HorizontalBox", "NavIcons", slot=S(pad=(0, 0, 16, 0), v="Center"), children=[
    icon("NavBack", "T_Icon_br_back", 16, 16, 24, "#79747e", S(pad=(0, 0, 12, 0))),
    icon("NavForward", "T_Icon_br_forward", 16, 16, 24, "#79747e", S(pad=(0, 0, 12, 0))),
    icon("NavRefresh", "T_Icon_br_refresh", 16, 16, 24, "#79747e"),
])
address = border("AddressBar", rounded("#f3edf7", 18), (16, 6, 16, 6), S(pad=(0, 0, 16, 0), v="Center", fill=True), [
    N("HorizontalBox", "AddressRow", children=[
        icon("LockIcon", "T_Icon_lock", 10.24, 13.44, 16, "#49454f", S(pad=(0, 0, 8, 0), v="Center"), a=0.65),
        text("UrlText", "www.url.com", 16, 0.5, "#1d1b20", S(v="Center", fill=True)),
        icon("StarIcon", "T_Icon_star", 16.67, 15.83, 20, "#79747e", S(v="Center")),
    ])])
profile = sizebox("ProfileAvatar", 28, 28, S(pad=(0, 0, 16, 0), v="Center"), [
    border("ProfileAvatarBg", rounded("#79747e", 14), h="Center", v="Center", children=[
        text("ProfileLetter", "M", 16, 0.5, "#ffffff")])])
browser_bar = sizebox("BrowserBar", h=68, slot=S(fill=False), children=[
    N("HorizontalBox", "BrowserBarRow", slot=S(pad=(16, 0, 16, 0)), children=[
        nav_icons, address, profile,
        icon("BrowserMore", "T_Icon_more_vert", 4, 16, 24, "#79747e", S(v="Center")),
    ])])
divider = N("Image", "BrowserBarDivider", {"brush": solid("#000000", 0.12, 1, 1)}, S(fill=False, h="Fill"))

# ---------- conversations list ----------
items = []
for i in range(1, 9):
    items.append(sizebox(f"Item{i}", h=72, children=[
        N("HorizontalBox", f"Item{i}Row", slot=S(pad=(16, 8, 16, 8)), children=[
            avatar(f"Item{i}Avatar", 40, S(pad=(0, 0, 16, 0), v="Center")),
            N("VerticalBox", f"Item{i}Text", {"clipping": "ClipToBounds"}, slot=S(pad=(0, 0, 16, 0), v="Center", fill=True), children=[
                text(f"Item{i}Name", "Name", 16, 0.5, "#1d1b20"),
                text(f"Item{i}Preview", "Supporting line text lorem ipsum dolor sit amet, consectetur.",
                     14, 0.25, "#4a4459", ellipsis=True),
            ]),
            text(f"Item{i}Time", "10 min", 11, 0.5, "#4a4459", S(v="Center")),
        ])]))
conversations = sizebox("ConversationsColumn", w=313, slot=S(fill=False), children=[
    N("ScrollBox", "ConversationsList", {"scrollBarVisibility": "Collapsed"}, children=[
        sizebox("SectionHeader", h=56, children=[
            text("SectionTitle", "Conversations", 14, 0.1, "#49454f", S(pad=(16, 0, 16, 0), v="Center"))]),
        *items,
    ])])

# ---------- conversation ----------
def icon_btn(name, tex, gw, gh, color, slot=None):
    return icon(name, tex, gw, gh, 48, color, slot)

app_bar = sizebox("AppBar", h=64, slot=S(fill=False), children=[
    N("HorizontalBox", "AppBarRow", slot=S(pad=(12, 8, 12, 8)), children=[
        icon_btn("BackButton", "T_Icon_app_back", 16, 16, "#1d1b20", S(pad=(0, 0, 4, 0), v="Center")),
        text("ChatTitle", "Name", 22, 0, "#1d1b20", S(pad=(0, 0, 4, 0), v="Center", fill=True)),
        icon_btn("AttachButton", "T_Icon_attach", 12.5, 20, "#49454f", S(v="Center")),
        icon_btn("MoreButton", "T_Icon_more_vert", 4, 16, "#49454f", S(v="Center")),
    ])])
link_card = border("LinkCard", rounded("#ece6f0", 12), (12, 12, 12, 12), S(pad=(0, 0, 0, 4), h="Right", fill=False), [
    N("VerticalBox", "LinkCardLayout", children=[
        sizebox("LinkCardImage", 200, 176, S(pad=(0, 0, 0, 6)), [
            border("LinkCardImageBg", rounded("#ece6f0", 8), h="Center", v="Center", children=[
                N("Image", "LinkCardImageArt", {"brush": tex_brush("T_Placeholder", 176, 176)})])]),
        text("LinkTitle", "Homemade Dumplings", 14, 0.25, "#1d1b20"),
        text("LinkUrl", "everydumplingever.com", 14, 0.25, "#49454f"),
    ])])
message_area = N("VerticalBox", "MessageArea", slot=S(pad=(24, 8, 24, 8), fill=True), children=[
    N("Spacer", "MessageSpacer", slot=S(fill=True)),
    link_card,
    bubble("SentBubble", "or we could make this?", "#625b71", "#ffffff", (20, 20, 8, 20), S(h="Right", fill=False)),
])
reply_row = N("HorizontalBox", "ReplyRow", slot=S(pad=(24, 8, 24, 8), fill=False), children=[
    avatar("ReplyAvatar", 36, S(pad=(0, 0, 8, 0), v="Center")),
    bubble("ReplyBubble", "that looks so good!", "#ece6f0", "#49454f", (20, 20, 20, 8), S(v="Center")),
])
suggestions = N("HorizontalBox", "SuggestionsRow", slot=S(pad=(24, 16, 24, 0), h="Right", fill=False), children=[
    bubble("Suggestion1", "Let’s do it", "#e8def8", "#4a4459", (20, 20, 8, 20), S(pad=(0, 0, 8, 0))),
    bubble("Suggestion2", "Great!", "#e8def8", "#4a4459", (20, 20, 8, 20), S(pad=(0, 0, 8, 0))),
    bubble("Suggestion3", "Great!", "#e8def8", "#4a4459", (20, 20, 8, 20)),
])
input_row = N("HorizontalBox", "InputRow", slot=S(pad=(24, 12, 24, 12), fill=False), children=[
    icon("AddButton", "T_Icon_add_circle", 20, 20, 24, "#1d1b20", S(pad=(0, 0, 16, 0), v="Center")),
    icon("EmojiButton", "T_Icon_mood", 20, 20, 24, "#1d1b20", S(pad=(0, 0, 16, 0), v="Center")),
    sizebox("SearchBar", h=56, slot=S(v="Center", fill=True), children=[
        border("SearchBarBg", rounded("#ece6f0", 28), (4, 4, 4, 4), children=[
            N("HorizontalBox", "SearchBarRow", children=[
                icon_btn("MenuButton", "T_Icon_menu", 18, 12, "#49454f", S(v="Center")),
                N("Spacer", "SearchBarSpacer", slot=S(fill=True)),
                icon_btn("SearchButton", "T_Icon_search", 18, 18, "#49454f", S(v="Center")),
            ])])]),
])
conversation = border("Conversation", rounded("#ffffff", (28, 28, 0, 0)), (0, 0, 0, 16), S(pad=(24, 0, 0, 0), fill=True), [
    N("VerticalBox", "ConversationLayout", children=[app_bar, message_area, reply_row, suggestions, input_row])])

body = N("HorizontalBox", "Body", slot=S(pad=(24, 23, 15, 0), fill=True), children=[conversations, conversation])

TREE = N("Overlay", "Root", children=[
    sizebox("Window", 921, 696, S(h="Center", v="Center"), [
        border("WindowFrame", rounded("#cac4d0", 26), (8, 8, 8, 8), children=[
            border("WindowSurface", rounded("#fef7ff", 18), clip=True, children=[
                N("VerticalBox", "Layout", children=[browser_bar, divider, body])])])])])

TEXTURES = ["T_Icon_add_circle", "T_Icon_app_back", "T_Icon_attach", "T_Icon_br_back", "T_Icon_br_forward",
            "T_Icon_br_refresh", "T_Icon_lock", "T_Icon_menu", "T_Icon_mood", "T_Icon_more_vert",
            "T_Icon_search", "T_Icon_star", "T_Placeholder"]

SCRIPT = r'''
import json
WBP = {"refPath": "%(wbp)s"}
TREE = json.loads(%(tree)r)
TEXTURES = json.loads(%(tex)r)
errors = []
count = [0]

def tool(name, args):
    return execute_tool(name, json.dumps(args))

def setp(obj, values, where):
    for k, v in values.items():
        try:
            r = tool("editor_toolset.toolsets.object.ObjectTools.set_properties", {"instance": obj, "values": json.dumps({k: v})})
            if not r["returnValue"]:
                errors.append(where + "." + k + ": returned false")
        except Exception as e:
            errors.append(where + "." + k + ": " + str(e)[:200])

def build(node, parent):
    a = {"widgetBlueprint": WBP, "widgetClass": {"refPath": "/Script/UMG." + node["cls"]}, "widgetDisplayName": node["name"]}
    if parent is not None:
        a["parentWidget"] = parent
    info = tool("UMGToolSet.UMGToolSet.AddWidget", a)["returnValue"]
    count[0] += 1
    if node["props"]:
        setp(info["widget"], node["props"], node["name"])
    if node["slot"] and isinstance(info["slot"], dict):
        setp(info["slot"], node["slot"], node["name"] + ".slot")
    for c in node["children"]:
        build(c, info["widget"])

def run():
    for t in TEXTURES:
        setp({"refPath": "/Game/UI/Messaging/Icons/%%s.%%s" %% (t, t)},
             {"compressionSettings": "TC_EditorIcon", "mipGenSettings": "TMGS_NoMipmaps", "lODGroup": "TEXTUREGROUP_UI"}, t)
    tree = tool("UMGToolSet.UMGToolSet.GetWidgets", {"widgetBlueprint": WBP})["returnValue"]
    for w in tree["widgets"]:
        if isinstance(w["parent"], dict) or w["widgetName"] != "Root":
            continue
        tool("UMGToolSet.UMGToolSet.RemoveWidget", {"widgetBlueprint": WBP, "widget": w["widget"]})
    build(TREE, None)
    comp = tool("UMGToolSet.UMGToolSet.CompileWidgetBlueprint", {"widgetBlueprint": WBP})
    return {"widgets": count[0], "errors": errors, "compile": comp}
''' % {"wbp": WBP_PATH, "tree": json.dumps(TREE), "tex": json.dumps(TEXTURES)}

payload = {"name": "call_tool", "arguments": {
    "toolset_name": "editor_toolset.toolsets.programmatic.ProgrammaticToolset",
    "tool_name": "execute_tool_script", "arguments": {"script": SCRIPT}}}
json.dump(payload, open(sys.argv[1], "w"))

def cnt(n):
    return 1 + sum(cnt(c) for c in n["children"])
print("widgets:", cnt(TREE))
