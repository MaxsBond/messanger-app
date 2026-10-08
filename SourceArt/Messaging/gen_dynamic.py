# Builds the data-driven version of the Messaging-Web screen:
#   sub-widgets WBP_ConversationRow / WBP_ChatBubble / WBP_LinkCard / WBP_SuggestionChip
#   and the screen WBP_Test with empty containers that Blueprint logic fills from data assets.
import json, sys
from ui_lib import *

UI = "/Game/UI/Messaging/Widgets"

# ---------- sub-widgets ----------
def button_style(radius):
    return {"normal": NODRAW_B, "hovered": rounded("#1d1b20", radius, 0.08), "pressed": rounded("#1d1b20", radius, 0.12),
            "disabled": NODRAW_B, "normalPadding": m(), "pressedPadding": m()}


NODRAW_B = {"drawAs": "NoDrawType"}

row = sizebox("Row", h=72, children=[
    N("Overlay", "RowOverlay", children=[
        V(border("Highlight", rounded("#e8def8", 16), slot=S(h="Fill", v="Fill"))),
        V(N("Button", "RowButton", {"widgetStyle": button_style(16), "isFocusable": False},
            S(h="Fill", v="Fill"), [
            N("HorizontalBox", "RowContent", slot=S(pad=(16, 8, 16, 8), h="Fill", v="Fill"), children=[
                sizebox("Avatar", 40, 40, S(pad=(0, 0, 16, 0), v="Center"), [
                    border("AvatarBg", rounded("#ece6f0", 20), h="Center", v="Center", children=[
                        V(N("Image", "AvatarArt", {"brush": tex_brush("T_Placeholder", 40, 40)}))])]),
                N("VerticalBox", "TextColumn", {"clipping": "ClipToBounds"}, S(pad=(0, 0, 16, 0), v="Center", fill=True), [
                    V(text("NameText", "Name", 16, 0.5, "#1d1b20")),
                    V(text("PreviewText", "Supporting line text lorem ipsum dolor sit amet, consectetur.",
                           14, 0.25, "#4a4459", ellipsis=True)),
                ]),
                V(text("TimeText", "10 min", 11, 0.5, "#4a4459", S(v="Center"))),
            ])])),
    ])])
row["children"][0]["children"][0]["props"]["renderOpacity"] = 0.0

NODRAW = {"drawAs": "NoDrawType"}
chat_bubble = V(border("Frame", NODRAW, (0, 4, 0, 4), h="Left", children=[
    V(N("WidgetSwitcher", "Layout", children=[
        N("HorizontalBox", "IncomingRow", slot=S(h="Left"), children=[
            sizebox("ReplyAvatar", 36, 36, S(pad=(0, 0, 8, 0), v="Center"), [
                border("ReplyAvatarBg", rounded("#ece6f0", 18), h="Center", v="Center", children=[
                    V(N("Image", "AvatarArt", {"brush": tex_brush("T_Placeholder", 36, 36)}))])]),
            border("IncomingBubble", rounded("#ece6f0", (20, 20, 20, 8)), (16, 10, 16, 10), S(v="Center"),
                   [V(text("IncomingText", "Incoming message", 16, 0.5, "#49454f"))]),
        ]),
        border("OutgoingBubble", rounded("#625b71", (20, 20, 8, 20)), (16, 10, 16, 10), S(h="Right"),
               [V(text("OutgoingText", "Outgoing message", 16, 0.5, "#ffffff"))]),
    ]))]))

link_card = V(border("Frame", NODRAW, (0, 4, 0, 4), h="Left", children=[
    border("Card", rounded("#ece6f0", 12), (12, 12, 12, 12), children=[
        N("VerticalBox", "CardLayout", children=[
            sizebox("ImageBox", 200, 176, S(pad=(0, 0, 0, 6)), [
                border("ImageBg", rounded("#ece6f0", 8), h="Center", v="Center", children=[
                    V(N("Image", "LinkImage", {"brush": tex_brush("T_Placeholder", 176, 176)}))])]),
            V(text("TitleText", "Link title", 14, 0.25, "#1d1b20")),
            V(text("UrlText", "example.com", 14, 0.25, "#49454f")),
        ])])]))

chip = border("Root", NODRAW, (8, 0, 0, 0), children=[
    border("Chip", rounded("#e8def8", (20, 20, 8, 20)), (16, 10, 16, 10),
           children=[V(text("LabelText", "Great!", 16, 0.5, "#4a4459"))])])

# ---------- screen ----------
nav_icons = N("HorizontalBox", "NavIcons", slot=S(pad=(0, 0, 16, 0), v="Center"), children=[
    icon("NavBack", "T_Icon_br_back", 16, 16, 24, "#79747e", S(pad=(0, 0, 12, 0))),
    icon("NavForward", "T_Icon_br_forward", 16, 16, 24, "#79747e", S(pad=(0, 0, 12, 0))),
    icon("NavRefresh", "T_Icon_br_refresh", 16, 16, 24, "#79747e"),
])
address = border("AddressBar", rounded("#f3edf7", 18), (16, 6, 16, 6), S(pad=(0, 0, 16, 0), v="Center", fill=True), [
    N("HorizontalBox", "AddressRow", children=[
        icon("LockIcon", "T_Icon_lock", 10.24, 13.44, 16, "#49454f", S(pad=(0, 0, 8, 0), v="Center"), a=0.65),
        V(text("UrlText", "www.url.com", 16, 0.5, "#1d1b20", S(v="Center", fill=True))),
        icon("StarIcon", "T_Icon_star", 16.67, 15.83, 20, "#79747e", S(v="Center")),
    ])])
profile = sizebox("ProfileAvatar", 28, 28, S(pad=(0, 0, 16, 0), v="Center"), [
    border("ProfileAvatarBg", rounded("#79747e", 14), h="Center", v="Center", children=[
        V(text("ProfileLetter", "M", 16, 0.5, "#ffffff"))])])
browser_bar = sizebox("BrowserBar", h=68, slot=S(fill=False), children=[
    N("HorizontalBox", "BrowserBarRow", slot=S(pad=(16, 0, 16, 0)), children=[
        nav_icons, address, profile,
        icon("BrowserMore", "T_Icon_more_vert", 4, 16, 24, "#79747e", S(v="Center")),
    ])])
divider = N("Image", "BrowserBarDivider", {"brush": solid("#000000", 0.12, 1, 1)}, S(fill=False, h="Fill"))

conversations = sizebox("ConversationsColumn", w=313, slot=S(fill=False), children=[
    N("ScrollBox", "ConversationsList", {"scrollBarVisibility": "Collapsed"}, children=[
        sizebox("SectionHeader", h=56, children=[
            text("SectionTitle", "Conversations", 14, 0.1, "#49454f", S(pad=(16, 0, 16, 0), v="Center"))]),
        V(N("VerticalBox", "ConversationRows")),
    ])])


def icon_btn(name, tex, gw, gh, color, slot=None):
    return icon(name, tex, gw, gh, 48, color, slot)


app_bar = sizebox("AppBar", h=64, slot=S(fill=False), children=[
    N("HorizontalBox", "AppBarRow", slot=S(pad=(12, 8, 12, 8)), children=[
        icon_btn("BackButton", "T_Icon_app_back", 16, 16, "#1d1b20", S(pad=(0, 0, 4, 0), v="Center")),
        V(text("ChatTitle", "Name", 22, 0, "#1d1b20", S(pad=(0, 0, 4, 0), v="Center", fill=True))),
        icon_btn("AttachButton", "T_Icon_attach", 12.5, 20, "#49454f", S(v="Center")),
        icon_btn("MoreButton", "T_Icon_more_vert", 4, 16, "#49454f", S(v="Center")),
    ])])
message_area = V(N("ScrollBox", "MessageScroll", {"scrollBarVisibility": "Collapsed", "clipping": "ClipToBounds"},
                   S(pad=(24, 8, 24, 8), fill=True), [
    V(N("VerticalBox", "MessageList")),
]))
suggestions = V(N("HorizontalBox", "SuggestionsRow", slot=S(pad=(24, 16, 24, 0), h="Right", fill=False)))
input_row = N("HorizontalBox", "InputRow", slot=S(pad=(24, 12, 24, 12), fill=False), children=[
    icon("AddButton", "T_Icon_add_circle", 20, 20, 24, "#1d1b20", S(pad=(0, 0, 16, 0), v="Center")),
    icon("EmojiButton", "T_Icon_mood", 20, 20, 24, "#1d1b20", S(pad=(0, 0, 16, 0), v="Center")),
    sizebox("SearchBar", h=56, slot=S(v="Center", fill=True), children=[
        border("SearchBarBg", rounded("#ece6f0", 28), (4, 4, 4, 4), children=[
            N("HorizontalBox", "SearchBarRow", children=[
                icon_btn("MenuButton", "T_Icon_menu", 18, 12, "#49454f", S(v="Center")),
                V(N("EditableText", "MessageInput", {
                    "hintText": "Message",
                    "clearKeyboardFocusOnCommit": False,
                    "widgetStyle": {"font": font(16, 0.5), "colorAndOpacity": slate("#1d1b20")},
                }, S(pad=(4, 0, 8, 0), v="Center", fill=True))),
                V(N("Button", "SendButton", {"widgetStyle": button_style(24), "isFocusable": False}, S(v="Center"), [
                    icon("SendIcon", "T_Icon_search", 18, 18, 48, "#49454f", S(h="Center", v="Center"))])),
            ])])]),
])
conversation = border("Conversation", rounded("#ffffff", (28, 28, 0, 0)), (0, 0, 0, 16), S(pad=(24, 0, 0, 0), fill=True), [
    N("VerticalBox", "ConversationLayout", children=[app_bar, message_area, suggestions, input_row])])
body = N("HorizontalBox", "Body", slot=S(pad=(24, 23, 15, 0), fill=True), children=[conversations, conversation])
screen = N("Overlay", "Root", children=[
    sizebox("Window", 921, 696, S(h="Center", v="Center"), [
        border("WindowFrame", rounded("#cac4d0", 26), (8, 8, 8, 8), children=[
            border("WindowSurface", rounded("#fef7ff", 18), clip=True, children=[
                N("VerticalBox", "Layout", children=[browser_bar, divider, body])])])])])

TARGETS = [
    (UI, "WBP_ConversationRow", row),
    (UI, "WBP_ChatBubble", chat_bubble),
    (UI, "WBP_LinkCard", link_card),
    (UI, "WBP_SuggestionChip", chip),
    ("/Game", "WBP_Test", screen),
]
write_payload(TARGETS, sys.argv[1], sys.argv[2].split(",") if len(sys.argv) > 2 else None)
