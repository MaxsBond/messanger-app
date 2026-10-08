# Builds /Game/UI/Messaging/WBP_MessagingLayout from Figma "Unreal Engine Target" → Layouts page:
# the three base states (list open 1:4600 / list collapsed 15:343 / details open 15:6576) in one tree,
# made only of the WBP_* components. Everything that changes between states stays in the tree so the
# Motion page transitions can be animated (gen_layout_motion.py): the list and the details panel sit in
# clipping SizeBoxes (ListClip / DetailsClip) whose width is animated, with a CanvasPanel inside so the
# content keeps its width while the clip shrinks; the attach menu, recording bar and suggestions fade.
# usage: python3 gen_layout.py payload.json
import sys
from ui_lib import *

W = "/Game/UI/Messaging/Widgets/"
NODRAW = {"drawAs": "NoDrawType"}


def inst(cls, name, props=None, slot=None, var=True):
    return N("%s%s.%s_C" % (W, cls, cls), name, props, slot, var=var)


def clipbox(name, w=None, h=None, slot=None, children=()):
    box = sizebox(name, w, h, slot, children)
    box["props"]["clipping"] = "ClipToBounds"
    return box


def canvas_slot(left, width, anchor_x=0.0):
    # fixed width, stretched to the canvas height; anchor_x=1 pins it to the right edge
    return {"layoutData": {"offsets": m(left, 0, width, 0), "alignment": {"x": 0, "y": 0},
                           "anchors": {"minimum": {"x": anchor_x, "y": 0}, "maximum": {"x": anchor_x, "y": 1}}}}


def icon_button(name, tex, gw, gh, color, slot=None):
    style = {"normal": NODRAW, "hovered": rounded("#1d1b20", 20, 0.08), "pressed": rounded("#1d1b20", 20, 0.12),
             "disabled": NODRAW, "normalPadding": m(), "pressedPadding": m()}
    return sizebox(name + "Box", 48, 48, slot, [
        V(N("Button", name, {"widgetStyle": style, "isFocusable": False}, S(pad=(4, 4, 4, 4), h="Fill", v="Fill"), [
            V(N("Image", name + "Glyph", {"brush": tex_brush(tex, gw, gh, color)}, S(pad=(0, 0, 0, 0), h="Center", v="Center")))]))])


# ---------- conversation list ----------
ROWS = [("Emma Clarke", "Perfect, thanks!", "2 min"), ("Liam Porter", "Can you send the file?", "10 min"),
        ("Sofia Reyes", "Haha, love it", "25 min"), ("Noah Kim", "See you tomorrow", "1 h"),
        ("Ava Brooks", "Got it 👍", "2 h"), ("Mason Hill", "Let me check and get back", "3 h"),
        ("Mia Turner", "Sounds good", "5 h"), ("Lucas Ward", "Thanks for the update", "Yesterday")]

DEMO_BUTTON = {"isFocusable": False, "widgetStyle": {
    "normal": rounded("#e8def8", 14), "hovered": rounded("#ddd0f2", 14), "pressed": rounded("#d0c2ea", 14),
    "disabled": NODRAW, "normalPadding": m(12, 4, 12, 4), "pressedPadding": m(12, 4, 12, 4)}}
LIST_W, DETAILS_W = 348, 314  # list column 11 + 313 + 24; details panel 14 gap + 300
conversations = V(sizebox("ConversationsColumn", w=313, slot=canvas_slot(11, 313), children=[
    N("ScrollBox", "ConversationsList", {"scrollBarVisibility": "Collapsed"}, children=[
        sizebox("SectionHeader", h=56, children=[N("HorizontalBox", "SectionHeaderRow", children=[
            text("SectionTitle", "Conversations", 14, 0.1, "#49454f", S(pad=(16, 0, 8, 0), v="Center", fill=True)),
            # starts / stops the incoming-activity demo (gen_layout_motion.py ToggleDemo)
            V(N("Button", "DemoButton", DEMO_BUTTON, S(pad=(0, 0, 12, 0), v="Center"), [
                V(text("DemoLabel", "Demo", 12, 0.5, "#4a4458", S(h="Center", v="Center"), face="Bold"))]))])]),
        V(N("VerticalBox", "ConversationRows", children=[
            inst("WBP_ConversationRow", "Row%d" % (i + 1), {"RowName": n, "RowPreview": p, "RowTime": t})
            for i, (n, p, t) in enumerate(ROWS)])),
    ])]))

# ---------- chat ----------
# list toggle: two stacked glyphs so Motion 01 can crossfade left_panel_close -> left_panel_open
list_toggle = icon_button("ListToggleButton", "T_Icon_left_panel_close", 18, 18, "#1d1b20", S(pad=(0, 0, 4, 0), v="Center"))
list_toggle["children"][0]["children"] = [N("Overlay", "ListToggleGlyphs", slot=S(pad=(0, 0, 0, 0), h="Center", v="Center"), children=[
    V(N("Image", "ListToggleGlyphClose", {"brush": tex_brush("T_Icon_left_panel_close", 18, 18, "#1d1b20")}, S(h="Center", v="Center"))),
    V(N("Image", "ListToggleGlyphOpen", {"brush": tex_brush("T_Icon_left_panel_open", 18, 18, "#1d1b20"), "renderOpacity": 0},
        S(h="Center", v="Center"))),
])]
app_bar = sizebox("AppBar", h=64, slot=S(fill=False), children=[
    N("HorizontalBox", "AppBarRow", slot=S(pad=(12, 8, 12, 8)), children=[
        list_toggle,
        V(text("ChatTitle", "Emma Clarke", 22, 0, "#1d1b20", S(pad=(4, 0, 4, 0), v="Center", fill=True))),
        V(icon_button("MoreButton", "T_Icon_more_vert", 4, 16, "#49454f", S(v="Center"))),
    ])])

messages = V(N("ScrollBox", "MessageScroll", {"scrollBarVisibility": "Collapsed", "clipping": "ClipToBounds"},
               S(pad=(24, 8, 24, 8), fill=True), [
    V(N("VerticalBox", "MessageList", children=[
        inst("WBP_LinkCard", "LinkCard", {"CardTitle": "Homemade Dumplings", "CardUrl": "everydumplingever.com",
                                          "bOutgoing": True}, var=False),
        inst("WBP_ChatBubble", "OutgoingBubble", {"MessageText": "or we could make this?", "bOutgoing": True}, var=False),
        inst("WBP_ChatBubble", "IncomingBubble", {"MessageText": "that looks so good!"}, var=False),
        inst("WBP_VoiceMessage", "VoiceMessage", {"Duration": "0:03"}, var=False),
        inst("WBP_TypingIndicator", "TypingIndicator"),
    ])),
]))

# MaxDesiredHeight is animated to 0 when recording starts (Motion 05); 80 is above the row's natural height
# SuggestionsInner collapses the same way once the user replied (Anim_SuggestionsOut); kept separate so the
# recording animation on the outer box can still play in reverse without bringing used suggestions back
suggestions_inner = V(clipbox("SuggestionsInner", slot=S(h="Fill"), children=[
    V(N("HorizontalBox", "SuggestionsRow", slot=S(pad=(24, 16, 24, 0), h="Right"), children=[
        inst("WBP_SuggestionChip", "Chip%d" % (i + 1), {"ChipLabel": s})
        for i, s in enumerate(["Let's do it", "Great!", "Great!"])]))]))
suggestions = V(clipbox("SuggestionsBox", slot=S(fill=False), children=[suggestions_inner]))
for box in (suggestions, suggestions_inner):
    box["props"].update({"bOverride_MaxDesiredHeight": True, "maxDesiredHeight": 80})

input_row = V(N("HorizontalBox", "InputRow", slot=S(h="Fill", v="Center"), children=[
    icon_button("AddButton", "T_Icon_add_circle", 20, 20, "#1d1b20", S(pad=(0, 0, 8, 0), v="Center")),
    sizebox("MessageField", h=56, slot=S(v="Center", fill=True), children=[
        border("MessageFieldBg", rounded("#ece6f0", 28), (24, 4, 4, 4), children=[
            N("HorizontalBox", "MessageFieldRow", children=[
                V(N("EditableText", "MessageInput", {
                    "hintText": "Message",
                    "clearKeyboardFocusOnCommit": False,
                    "widgetStyle": {"font": font(16, 0.5), "colorAndOpacity": slate("#1d1b20")},
                }, S(pad=(0, 0, 8, 0), v="Center", fill=True))),
                icon_button("MicButton", "T_Icon_mic", 14, 19, "#49454f", S(v="Center")),
            ])])]),
]))
HIDDEN = {"renderOpacity": 0, "visibility": "Collapsed"}
composer = V(N("Overlay", "ComposerOverlay", slot=S(pad=(16, 12, 24, 12), fill=False), children=[
    input_row,
    inst("WBP_RecordingBar", "RecordingBar", dict(HIDDEN, RecTime="0:00"), S(pad=(48, 0, 0, 0), h="Fill", v="Center")),
]))

chat_column = N("VerticalBox", "ChatLayout", slot=S(h="Fill", v="Fill"),
                children=[app_bar, messages, suggestions, composer])
attach_menu = inst("WBP_AttachMenu", "AttachMenu", dict(HIDDEN, renderTransformPivot={"x": 0, "y": 1}),
                   S(pad=(24, 0, 0, 76), h="Left", v="Bottom"))

content = V(border("Content", rounded("#ffffff", 28), (0, 0, 0, 4), S(fill=True), clip=True, children=[
    N("Overlay", "ContentOverlay", children=[
        chat_column,
        attach_menu,
    ])]))

list_clip = V(clipbox("ListClip", w=LIST_W, slot=S(fill=False), children=[
    N("CanvasPanel", "ListCanvas", children=[conversations])]))
details = V(clipbox("DetailsClip", w=0, slot=S(fill=False), children=[
    N("CanvasPanel", "DetailsCanvas", children=[
        inst("WBP_DetailsPanel", "DetailsPanel", {"ContactName": "Emma Clarke", "Status": "Active now"}, canvas_slot(-300, 300, 1.0))])]))

body = N("HorizontalBox", "Body", slot=S(pad=(13, 12, 15, 17), h="Fill", v="Fill"),
         children=[list_clip, content, details])
# the app window is the Figma frame: fills the viewport (the packaged game opens a 905x744 resizable window, see
# Config/DefaultGameUserSettings.ini) and never shrinks below the frame size; the chat column takes the extra space
screen = N("Overlay", "Root", children=[
    N("SizeBox", "Window", {"bOverride_MinDesiredWidth": True, "minDesiredWidth": 905,
                            "bOverride_MinDesiredHeight": True, "minDesiredHeight": 744}, S(h="Fill", v="Fill"), [
        border("WindowSurface", rounded("#fef7ff", 0), clip=True, children=[body])])])

TARGETS = [("/Game/UI/Messaging", "WBP_MessagingLayout", screen)]
if __name__ == "__main__":
    write_payload(TARGETS, sys.argv[1])
