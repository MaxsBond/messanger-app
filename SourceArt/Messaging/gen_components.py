# Builds the widgets added to Figma "Unreal Engine Target" → Components page (section "UMG components"):
#   WBP_VoiceMessage, WBP_TypingIndicator, WBP_RecordingBar, WBP_AttachMenu, WBP_DetailsPanel
# usage: python3 gen_components.py payload.json [WBP_A,WBP_B]
import sys
from ui_lib import *

UI = "/Game/UI/Messaging/Widgets"
NODRAW = {"drawAs": "NoDrawType"}


def button_style(normal, radius, hover="#1d1b20"):
    # normal: brush or None (transparent); hover/pressed add a state layer like M3
    base = normal or NODRAW
    return {"normal": base,
            "hovered": rounded(hover, radius, 0.08) if normal is None else base,
            "pressed": rounded(hover, radius, 0.12) if normal is None else base,
            "disabled": base, "normalPadding": m(), "pressedPadding": m()}


def button(name, style, slot=None, children=(), pad=(0, 0, 0, 0)):
    b = N("Button", name, {"widgetStyle": style, "isFocusable": False}, slot, children)
    for c in b["children"]:
        c["slot"].setdefault("padding", m(*pad))
    return V(b)


def bars(name, heights, gap, color, played=None, slot=None):
    # waveform: one Image per bar, 3px wide, radius 1.5; bars after `played` are dimmed
    kids = []
    for i, h in enumerate(heights):
        a = 1.0 if played is None or i < played else 0.55
        kids.append(N("Image", "%sBar%d" % (name, i + 1), {"brush": pill(color, 3, h, 1.5, a)},
                      S(pad=(0 if i == 0 else gap, 0, 0, 0), v="Center")))
    return V(N("HorizontalBox", name, {"clipping": "ClipToBounds"}, slot, kids))


# ---------- WBP_VoiceMessage (Figma 15:6000) ----------
VOICE_BARS = [4, 8, 7, 5, 17, 11, 12, 10, 9, 6, 6, 11, 6, 10, 13, 17, 9, 5, 6, 10, 9, 10, 11, 8, 9, 15, 4, 6]
voice = V(border("Frame", NODRAW, (0, 4, 0, 4), h="Right", children=[
    V(border("VoiceBubble", rounded("#625b71", (20, 20, 8, 20)), (8, 8, 16, 8), children=[
        N("HorizontalBox", "VoiceRow", children=[
            sizebox("PlayBox", 32, 32, S(pad=(0, 0, 10, 0), v="Center"), [
                button("PlayButton", button_style(rounded("#ffffff", 16), 16), S(h="Fill", v="Fill"), [
                    V(N("Image", "PlayIcon", {"brush": tex_brush("T_Icon_play", 12, 14, "#625b71")},
                        S(pad=(3, 0, 0, 0), h="Center", v="Center")))])]),
            bars("Waveform", VOICE_BARS, 2, "#ffffff", played=9, slot=S(pad=(0, 0, 10, 0), v="Center")),
            V(text("DurationText", "0:03", 13, 0, "#ffffff", S(v="Center"))),
        ])]))]))
voice["children"][0]["props"]["renderTransformPivot"] = {"x": 1, "y": 1}  # Anim_PopIn grows from the bottom-right

# ---------- WBP_TypingIndicator (Figma 15:6032) ----------
typing = V(border("Frame", NODRAW, (0, 4, 0, 4), h="Left", children=[
    N("HorizontalBox", "TypingRow", children=[
        sizebox("Avatar", 36, 36, S(pad=(0, 0, 8, 0), v="Center"), [
            border("AvatarBg", rounded("#ece6f0", 18), h="Center", v="Center", children=[
                V(N("Image", "AvatarArt", {"brush": tex_brush("T_Placeholder", 36, 36)}))])]),
        border("TypingBubble", rounded("#ece6f0", (20, 20, 20, 8)), (16, 10, 16, 10), S(v="Center"), [
            sizebox("DotsBox", h=24, children=[
                N("HorizontalBox", "Dots", slot=S(v="Center"), children=[
                    V(N("Image", "Dot%d" % (i + 1), {"brush": pill("#49454f", 8, 8, 4), "renderOpacity": op},
                        S(pad=(0 if i == 0 else 5, 0, 0, 0), v="Center")))
                    for i, op in enumerate([1.0, 0.7, 0.4])])])]),
    ])]))

# ---------- WBP_RecordingBar (Figma 15:6428) ----------
REC_BARS = [4, 17, 10, 9, 19, 17, 13, 21, 20, 15, 16, 14, 15, 8, 11, 16, 18, 6, 20, 16, 24, 21, 7, 13, 17,
            14, 14, 14, 20, 22, 13, 13, 23, 13, 8, 10, 11, 9, 17, 13, 16, 20, 6, 12, 18, 16, 14, 9, 19, 5]
recording = sizebox("Root", h=56, children=[
    border("RecordingBg", rounded("#ece6f0", 28), (20, 0, 8, 0), v="Center", children=[
        N("HorizontalBox", "RecordingRow", children=[
            V(N("Image", "RecDot", {"brush": pill("#b3261e", 10, 10, 5)}, S(pad=(0, 0, 12, 0), v="Center"))),
            sizebox("Timer", w=40, slot=S(pad=(0, 0, 12, 0), v="Center"), children=[
                V(text("TimeText", "0:03", 14, 0, "#49454f", S(v="Center")))]),
            bars("Waveform", REC_BARS, 3, "#49454f", slot=S(pad=(0, 0, 12, 0), v="Center", fill=True)),
            sizebox("StopBox", 40, 40, S(v="Center"), [
                button("StopButton", button_style(rounded("#b3261e", 20), 20), S(h="Fill", v="Fill"), [
                    N("Image", "StopIcon", {"brush": pill("#ffffff", 12, 12, 2)}, S(h="Center", v="Center"))])]),
        ])])])


# ---------- WBP_AttachMenu (Figma 15:5949) ----------
def menu_item(name, tex, gw, gh, label, last=False):
    return sizebox(name + "Item", h=36, slot=S(pad=(0, 0, 0, 0 if last else 4)), children=[
        button(name + "Button", button_style(None, 12), S(h="Fill", v="Fill"), [
            N("HorizontalBox", name + "Row", slot=S(pad=(12, 0, 12, 0), h="Fill", v="Center"), children=[
                icon(name + "Icon", tex, gw, gh, 20, "#49454f", S(pad=(0, 0, 12, 0), v="Center")),
                text(name + "Label", label, 14, 0.25, "#1d1b20", S(v="Center", fill=True)),
            ])])])


attach = sizebox("Root", w=160, children=[
    border("MenuSurface", rounded("#ffffff", 16, outline="#cac4d0"), (8, 8, 8, 8), children=[
        N("VerticalBox", "MenuItems", children=[
            menu_item("File", "T_Icon_description", 13.33, 16.67, "File"),
            menu_item("Photo", "T_Icon_image", 15, 15, "Photo"),
            menu_item("Video", "T_Icon_videocam", 15, 10, "Video", last=True),
        ])])])


# ---------- WBP_DetailsPanel (Figma 15:8346) ----------
def action(name, tex, gw, gh, label):
    return N("VerticalBox", name + "Action", slot=S(pad=(0 if name == "Call" else 8, 0, 0, 0), fill=True), children=[
        sizebox(name + "Box", 48, 48, S(h="Center"), [
            button(name + "Button", button_style(rounded("#ece6f0", 24), 24), S(h="Fill", v="Fill"), [
                N("Image", name + "Icon", {"brush": tex_brush(tex, gw, gh, "#49454f")}, S(h="Center", v="Center"))])]),
        text(name + "Label", label, 12, 0, "#49454f", S(pad=(0, 6, 0, 0), h="Center")),
    ])


def file_row(name, title, meta):
    return N("HorizontalBox", name, slot=S(pad=(0, 8, 0, 8)), children=[
        sizebox(name + "IconBox", 40, 40, S(pad=(0, 0, 12, 0), v="Center"), [
            border(name + "IconBg", rounded("#ece6f0", 12), h="Center", v="Center", children=[
                N("Image", name + "Icon", {"brush": tex_brush("T_Icon_description", 13.33, 16.67, "#49454f")})])]),
        N("VerticalBox", name + "Text", slot=S(v="Center", fill=True), children=[
            text(name + "Title", title, 14, 0, "#1d1b20", ellipsis=True),
            text(name + "Meta", meta, 12, 0, "#49454f"),
        ])])


details = sizebox("Root", w=300, children=[
    border("PanelSurface", rounded("#ffffff", 28), (24, 16, 24, 24), children=[
        N("VerticalBox", "PanelLayout", children=[
            sizebox("Header", h=48, children=[
                N("HorizontalBox", "HeaderRow", children=[
                    text("HeaderTitle", "Details", 22, 0, "#1d1b20", S(v="Center", fill=True)),
                    sizebox("CloseBox", 40, 40, S(v="Center"), [
                        button("CloseButton", button_style(None, 20), S(h="Fill", v="Fill"), [
                            N("Image", "CloseIcon", {"brush": tex_brush("T_Icon_close", 14, 14, "#49454f")},
                              S(h="Center", v="Center"))])]),
                ])]),
            N("VerticalBox", "Profile", slot=S(pad=(0, 12, 0, 20)), children=[
                sizebox("Avatar", 80, 80, S(h="Center"), [
                    border("AvatarBg", rounded("#ece6f0", 40), h="Center", v="Center", children=[
                        V(N("Image", "AvatarArt", {"brush": tex_brush("T_Placeholder", 80, 80)}))])]),
                V(text("NameText", "Name", 22, 0, "#1d1b20", S(pad=(0, 16, 0, 0), h="Center"))),
                V(text("StatusText", "Active now", 14, 0, "#49454f", S(pad=(0, 4, 0, 0), h="Center"))),
            ]),
            N("HorizontalBox", "Actions", slot=S(pad=(0, 0, 0, 20)), children=[
                action("Call", "T_Icon_call", 18, 18, "Call"),
                action("Video", "T_Icon_videocam", 18, 12, "Video"),
                action("Mute", "T_Icon_mute", 17, 19.5, "Mute"),
            ]),
            N("Image", "Divider", {"brush": solid("#ece6f0", 1, 1, 1)}, S(h="Fill")),
            N("VerticalBox", "SharedMedia", slot=S(pad=(0, 20, 0, 20)), children=[
                N("HorizontalBox", "SharedMediaTitle", children=[
                    text("SharedMediaLabel", "Shared media", 14, 0, "#1d1b20", S(v="Center", fill=True)),
                    V(N("Button", "SeeAllButton", {"widgetStyle": button_style(None, 8), "isFocusable": False},
                        S(v="Center"), [text("SeeAllLabel", "See all", 14, 0, "#49454f", S(pad=(4, 0, 4, 0)))])),
                ]),
                V(N("HorizontalBox", "MediaGrid", slot=S(pad=(0, 12, 0, 0)), children=[
                    sizebox("Media%d" % i, h=76, slot=S(pad=(0 if i == 1 else 8, 0, 0, 0), fill=True), children=[
                        V(border("Media%dBg" % i, rounded("#ece6f0", 12)))])
                    for i in (1, 2, 3)])),
            ]),
            N("VerticalBox", "Files", children=[
                text("FilesLabel", "Files", 14, 0, "#1d1b20", S(pad=(0, 0, 0, 4))),
                V(N("VerticalBox", "FileList", children=[
                    file_row("FileMenu", "Menu.pdf", "1.2 MB · Yesterday"),
                    file_row("FileRecipe", "Recipe.docx", "320 KB · Mon"),
                ])),
            ]),
        ])])])

# dev-only gallery with one instance of each widget, to eyeball them against Figma
def inst(name, slot=None):
    return N("%s/%s.%s_C" % (UI, name, name), name, slot=slot or S(pad=(0, 0, 0, 16)))


preview = border("Root", rounded("#fef7ff", 0), (24, 24, 24, 24), children=[
    N("HorizontalBox", "Columns", children=[
        sizebox("MessagesColumn", w=481, slot=S(pad=(0, 0, 24, 0)), children=[
            N("VerticalBox", "Messages", children=[
                inst("WBP_VoiceMessage"), inst("WBP_TypingIndicator"), inst("WBP_AttachMenu", S(pad=(0, 0, 0, 16), h="Left")),
                inst("WBP_RecordingBar")])]),
        inst("WBP_DetailsPanel", S(v="Top")),
    ])])

TARGETS = [
    (UI, "WBP_VoiceMessage", voice),
    (UI, "WBP_TypingIndicator", typing),
    (UI, "WBP_RecordingBar", recording),
    (UI, "WBP_AttachMenu", attach),
    (UI, "WBP_DetailsPanel", details),
    ("/Game/UI/Messaging/Dev", "WBP_ComponentsPreview", preview),
]
write_payload(TARGETS, sys.argv[1], sys.argv[2].split(",") if len(sys.argv) > 2 else None)
