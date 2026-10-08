# Figma "Unreal Engine Target" → Motion page, applied to /Game/UI/Messaging/WBP_MessagingLayout (built by gen_layout.py).
# Needs the UMGAnimToolset plugin (messanger-app/PluginSource/UMGAnimToolset) and the component animations/functions
# made by gen_components_motion.py. Run after gen_layout.py; safe to rerun.
#   01 Collapse chat list   -> Anim_ListCollapse (ListToggleButton)
#   02 Attachment menu      -> Anim_AttachOpen / Anim_AttachClose + AttachMenu.PlayItemsIn (AddButton, OnItemPicked)
#   05 Voice message        -> Anim_RecordStart + RecordingBar.StartRecording/StopRecording, new WBP_VoiceMessage.PlayIntro
#   06 Details panel        -> Anim_DetailsOpen + DetailsPanel.PlayReveal (MoreButton, DetailsPanel.OnClose)
#   Chat: rows open their conversation (DA_MessagingFigma, gen_data_figma.py), suggestion chips and Enter send
#   messages; session messages (text, voice, incoming) survive switching conversations.
#   Demo: DemoButton in the list header runs DemoTick on a timer (incoming messages only, see DEMO_TEXTS).
#   03 New message to top   -> Anim_NewMessage + Row6.ShowIncoming, debug key N (OnKeyDown). The 6th row lifts 5 slots
#                              while rows 1-5 shift down 72px; then the rows' data rotates and offsets reset, so the
#                              key can be pressed again (the next conversation in slot 6 moves up).
# State / bAttachMenuOpen / bRecording stay instance-editable; ApplyState() snaps the tree to them (PreConstruct / designer).
# usage: python3 gen_layout_motion.py
import json
from ue_mcp import call, BP_TOOLS, ANIM_TOOLS, UMG_TOOLS, OBJ_TOOLS

L = "/Game/UI/Messaging/WBP_MessagingLayout"
REF = {"refPath": L + ".WBP_MessagingLayout"}
W = "/Game/UI/Messaging/Widgets/"
MSG_CLASS = "/Game/UI/Messaging/Data/BP_ChatMessage.BP_ChatMessage_C"
LIST_W, DETAILS_W, SUGGEST_H, ROW_H = 348, 314, 60, 72
E = "easeInOut"

ANIMS = {
    # 01: list slides 80px left and fades while its clip closes; chat takes the space. Icon crossfades 0.1-0.4s.
    "Anim_ListCollapse": (0.6, [
        ("ListClip", "WidthOverride", [(0, LIST_W, E), (0.6, 0)]),
        ("ConversationsColumn", "Translation.X", [(0, 0, E), (0.6, -80)]),
        ("ConversationsColumn", "RenderOpacity", [(0, 1, E), (0.6, 0)]),
        ("ListToggleGlyphClose", "RenderOpacity", [(0, 1, "constant"), (0.1, 1, E), (0.4, 0)]),
        ("ListToggleGlyphOpen", "RenderOpacity", [(0, 0, "constant"), (0.1, 0, E), (0.4, 1)]),
    ]),
    # 06: ⋮ fades out, then the 300px panel (+14 gap) slides in from the right; played in reverse to close.
    "Anim_DetailsOpen": (0.7, [
        ("MoreButtonBox", "RenderOpacity", [(0, 1, E), (0.3, 0)]),
        ("DetailsClip", "WidthOverride", [(0, 0, "constant"), (0.2, 0, E), (0.7, DETAILS_W)]),
    ]),
    # 02: grows out of the + button (pivot bottom-left, set in gen_layout.py), closes to 0.9 with ease-in.
    "Anim_AttachOpen": (0.3, [
        ("AttachMenu", "Scale.X", [(0, 0.8, "easeOut"), (0.3, 1)]),
        ("AttachMenu", "Scale.Y", [(0, 0.8, "easeOut"), (0.3, 1)]),
        ("AttachMenu", "RenderOpacity", [(0, 0, "easeOut"), (0.3, 1)]),
    ]),
    "Anim_AttachClose": (0.2, [
        ("AttachMenu", "Scale.X", [(0, 1, "easeIn"), (0.2, 0.9)]),
        ("AttachMenu", "Scale.Y", [(0, 1, "easeIn"), (0.2, 0.9)]),
        ("AttachMenu", "RenderOpacity", [(0, 1, "easeIn"), (0.2, 0)]),
    ]),
    # 03: row 6 rises 5 slots (5 x 72px) with a slight lift, rows above shift down one slot
    "Anim_NewMessage": (0.9, [("Row6", "Translation.Y", [(0, 0, "constant"), (0.3, 0, E), (0.9, -5 * ROW_H)]),
                              ("Row6", "Scale.X", [(0, 1, "constant"), (0.3, 1, E), (0.6, 1.03, E), (0.9, 1)]),
                              ("Row6", "Scale.Y", [(0, 1, "constant"), (0.3, 1, E), (0.6, 1.03, E), (0.9, 1)])]
                             + [("Row%d" % i, "Translation.Y", [(0, 0, "constant"), (0.3, 0, E), (0.9, ROW_H)]) for i in range(1, 6)]),
    # after a reply the conversation's suggestions fold away (inner box, independent of the recording animation)
    "Anim_SuggestionsOut": (0.35, [
        ("SuggestionsInner", "RenderOpacity", [(0, 1, "easeOut"), (0.2, 0)]),
        ("SuggestionsInner", "MaxDesiredHeight", [(0, SUGGEST_H, "constant"), (0.05, SUGGEST_H, E), (0.35, 0)]),
    ]),
    # 05: suggestions fade and collapse (messages drop into their space), recording bar fades in over the input.
    "Anim_RecordStart": (0.4, [
        ("SuggestionsBox", "RenderOpacity", [(0, 1, "easeOut"), (0.2, 0)]),
        ("SuggestionsBox", "MaxDesiredHeight", [(0, SUGGEST_H, "constant"), (0.05, SUGGEST_H, E), (0.35, 0)]),
        ("InputRow", "RenderOpacity", [(0, 1, "constant"), (0.15, 1, "easeOut"), (0.35, 0)]),
        ("RecordingBar", "RenderOpacity", [(0, 0, "constant"), (0.15, 0, "easeOut"), (0.35, 1)]),
    ]),
}

V = "Variables|WBP_MessagingLayout|Get"
A = "Variables|Animations|Get"
FWD, REV, PLAY, STOP = ("UserInterface|Animation|PlayAnimationForward", "UserInterface|Animation|PlayAnimationReverse",
                        "UserInterface|Animation|PlayAnimation", "UserInterface|Animation|StopAnimation")
TIMER = "Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName"

FUNCTIONS = {
    "ApplyState": f'''(fn ApplyState ()
  (bind st (Variables|State|GetState))
  (bind listOpen (== st 0))
  (bind att (Variables|State|GetAttachMenuOpen))
  (bind rec (Variables|State|GetRecording))
  (Layout|SizeBox|SetWidthOverride ({V}ListClip) (select listOpen {LIST_W}.0 0.0))
  (Widget|SetRenderOpacity ({V}ConversationsColumn) (select listOpen 1.0 0.0))
  (Widget|Transform|SetRenderTranslation ({V}ConversationsColumn) (Math|Vector2D|MakeVector2D (select listOpen 0.0 -80.0) 0.0))
  (Widget|SetRenderOpacity ({V}ListToggleGlyphClose) (select listOpen 1.0 0.0))
  (Widget|SetRenderOpacity ({V}ListToggleGlyphOpen) (select listOpen 0.0 1.0))
  (Layout|SizeBox|SetWidthOverride ({V}DetailsClip) (select (== st 2) {DETAILS_W}.0 0.0))
  (Widget|SetRenderOpacity ({V}MoreButtonBox) (select (== st 2) 0.0 1.0))
  (Widget|SetRenderOpacity ({V}AttachMenu) (select att 1.0 0.0))
  (Widget|Transform|SetRenderScale ({V}AttachMenu) (Math|Vector2D|MakeVector2D 1.0 1.0))
  (Widget|SetRenderOpacity ({V}SuggestionsBox) (select rec 0.0 1.0))
  (Layout|SizeBox|SetMaxDesiredHeight ({V}SuggestionsBox) (select rec 0.0 {SUGGEST_H}.0))
  (Widget|SetRenderOpacity ({V}InputRow) (select rec 0.0 1.0))
  (Widget|SetRenderOpacity ({V}RecordingBar) (select rec 1.0 0.0))
  (if att
    (Widget|SetVisibility ({V}AttachMenu) "Visible")
    (else
      (Widget|SetVisibility ({V}AttachMenu) "Collapsed")))
  (if rec
    (Widget|SetVisibility ({V}RecordingBar) "Visible")
    (else
      (Widget|SetVisibility ({V}RecordingBar) "Collapsed"))))''',

    # 01 — list toggle: open <-> collapsed; from details (state 2) it closes the panel and reopens the list
    "ToggleList": f'''(fn ToggleList ()
  (bind st (Variables|State|GetState))
  (if (== st 0)
    ({FWD} :InAnimation ({A}Anim_ListCollapse))
    (Variables|State|SetState 1)
    (elif (== st 1)
      ({REV} :InAnimation ({A}Anim_ListCollapse))
      (Variables|State|SetState 0)
      (else
        ({REV} :InAnimation ({A}Anim_DetailsOpen))
        ({REV} :InAnimation ({A}Anim_ListCollapse))
        (Variables|State|SetState 0)))))''',

    # 06 — details panel (the list collapses too when it was open)
    "ShowDetails": f'''(fn ShowDetails ()
  ({FWD} :InAnimation ({A}Anim_DetailsOpen))
  (Class|WBPDetailsPanel|PlayReveal :self ({V}DetailsPanel))
  (Variables|State|SetState 2))''',
    "OpenDetails": f'''(fn OpenDetails ()
  (bind st (Variables|State|GetState))
  (if (== st 0)
    ({FWD} :InAnimation ({A}Anim_ListCollapse))
    (CallFunction|ShowDetails)
    (elif (== st 1)
      (CallFunction|ShowDetails))))''',
    "CloseDetails": f'''(fn CloseDetails ()
  (if (== (Variables|State|GetState) 2)
    ({REV} :InAnimation ({A}Anim_DetailsOpen))
    (Variables|State|SetState 1)))''',

    # 02 — attach menu
    "OpenAttach": f'''(fn OpenAttach ()
  (Variables|State|SetAttachMenuOpen true)
  ({STOP} :InAnimation ({A}Anim_AttachClose))
  (Widget|SetVisibility ({V}AttachMenu) "Visible")
  ({PLAY} :InAnimation ({A}Anim_AttachOpen))
  (Class|WBPAttachMenu|PlayItemsIn :self ({V}AttachMenu)))''',
    "CloseAttach": f'''(fn CloseAttach ()
  (if (Variables|State|GetAttachMenuOpen)
    (Variables|State|SetAttachMenuOpen false)
    ({STOP} :InAnimation ({A}Anim_AttachOpen))
    ({PLAY} :InAnimation ({A}Anim_AttachClose))
    ({TIMER} "HideClosedOverlays" :Time 0.25 :bLooping false)))''',
    "ToggleAttach": f'''(fn ToggleAttach ()
  (if (Variables|State|GetAttachMenuOpen)
    (CallFunction|CloseAttach)
    (else
      (CallFunction|OpenAttach))))''',
    # collapses overlays once their fade-out finished (unless they were reopened meanwhile)
    "HideClosedOverlays": f'''(fn HideClosedOverlays ()
  (if (not (Variables|State|GetAttachMenuOpen))
    (Widget|SetVisibility ({V}AttachMenu) "Collapsed"))
  (if (not (Variables|State|GetRecording))
    (Widget|SetVisibility ({V}RecordingBar) "Collapsed")))''',

    # 05 — voice message
    "StartVoice": f'''(fn StartVoice ()
  (if (not (Variables|State|GetRecording))
    (CallFunction|CloseAttach)
    (Variables|State|SetRecording true)
    (Widget|SetVisibility ({V}RecordingBar) "Visible")
    ({FWD} :InAnimation ({A}Anim_RecordStart))
    (Class|WBPRecordingBar|StartRecording :self ({V}RecordingBar))))''',
    "StopVoice": f'''(fn StopVoice ()
  (if (Variables|State|GetRecording)
    (Variables|State|SetRecording false)
    (Class|WBPRecordingBar|StopRecording :self ({V}RecordingBar))
    ({REV} :InAnimation ({A}Anim_RecordStart))
    ({TIMER} "HideClosedOverlays" :Time 0.45 :bLooping false)
    ({TIMER} "SendVoice" :Time 0.2 :bLooping false)))''',
    # the note lands in the chat as a session message (kept when switching conversations)
    "SendVoice": f'''(fn SendVoice ()
  (CallFunction|RemoveTyping)
  (bind secs (Class|WBPRecordingBar|GetRecSeconds :self ({V}RecordingBar)))
  (bind m (Game|ConstructObjectfromClass "{MSG_CLASS}" self))
  (Class|BPChatMessage|InitMessage :self m :InText (Utilities|Text|ToText(String) (Utilities|String|Append :A (select (< secs 10) "0:0" "0:") :B (Utilities|String|ToString(Integer) secs))) :InOutgoing true)
  (Class|BPChatMessage|SetKind :self m :Kind 2)
  (Utilities|Array|Add (Variables|Default|GetSessionMessages) m)
  (Utilities|Array|Add (Variables|Default|GetSessionConv) (Variables|Default|GetSelectedConv))
  (CallFunction|AddMessage :Msg m :bAnimate true)
  (CallFunction|UpdateSelectedRow :InPreview (Utilities|Text|ToText(String) "Voice message"))
  (CallFunction|RefreshHighlights)
  (CallFunction|HideSuggestions)
  (Widget|ScrolltoEnd ({V}MessageScroll)))''',
}

ROW = "Class|WBPConversationRow|"
ROWS = range(1, 9)
DATA_ASSET = "/Game/UI/Messaging/Data/Figma/DA_MessagingFigma.DA_MessagingFigma"


def rotate_rows():
    """slot 6 -> slot 1, slots 1-5 -> 2-6 (data only), then clear the animation offsets"""
    fields = [("RowName", "RowName"), ("RowPreview", "RowPreview"), ("RowTime", "RowTime"), ("Unread", "bUnread"),
              ("RowIndex", "RowIndex")]
    # the finished animation keeps its end state (KeepState) and may evaluate once more after a timer that fires
    # right at its end, so stop it explicitly before clearing the offsets
    lines = ["(fn FinishIncoming ()", "  (%s :InAnimation (%sAnim_NewMessage))" % (STOP, A)]
    # pure getters re-evaluate at every use, so park slot 6 in member variables before overwriting it
    lines += ["  (Variables|Default|SetTmp%s (%sGet%s :self (%sRow6)))" % (f, ROW, f, V) for f, _ in fields]
    for k in range(6, 1, -1):
        for f, pin in fields:
            lines.append("  (%sSet%s :self (%sRow%d) :%s (%sGet%s :self (%sRow%d)))" % (ROW, f, V, k, pin, ROW, f, V, k - 1))
    lines += ["  (%sSet%s :self (%sRow1) :%s (Variables|Default|GetTmp%s))" % (ROW, f, V, pin, f) for f, pin in fields]
    for k in range(1, 7):
        lines.append("  (%sApplyProps :self (%sRow%d))" % (ROW, V, k))
        lines.append("  (Widget|Transform|SetRenderTranslation (%sRow%d) (Math|Vector2D|MakeVector2D 0.0 0.0))" % (V, k))
        lines.append("  (Widget|Transform|SetRenderScale (%sRow%d) (Math|Vector2D|MakeVector2D 1.0 1.0))" % (V, k))
    lines.append("  (Variables|Default|SetMovingRow false)")
    lines.append("  (CallFunction|RefreshHighlights))")
    return "\n".join(lines)


def per_row(template):
    return "\n".join(template.format(r="(%sRow%d)" % (V, k), i=k - 1) for k in ROWS)


SEL = "(Variables|Default|GetSelectedConv)"
IDX = ROW + "GetRowIndex :self {r}"
IN_SESSION = "(== (Utilities|Array|Get(acopy) (Variables|Default|GetSessionConv) {i}) " + SEL + ")"

DEMO_EVERY = 2.2
DEMO_TEXTS = ["Are we still on for tonight?", "Just sent you the photos", "Call me when you're free",
              "Running 10 min late, sorry!", "Did you see the news?", "Thanks, that really helps"]


def demo_tick():
    """next demo text by DemoStep (mod len), skipped while the previous row is still moving"""
    n = len(DEMO_TEXTS)
    chain = "\n".join("    %s(== k %d)\n      (Variables|Default|SetIncomingText (Utilities|Text|ToText(String) \"%s\"))"
                      % ("(if " if i == 0 else "(elif ", i, t) for i, t in enumerate(DEMO_TEXTS))
    return ("(fn DemoTick ()\n  (if (not (Variables|Default|GetMovingRow))\n"
            "    (bind s (Variables|Default|GetDemoStep))\n    (bind k (- s (* (/ s %d) %d)))\n%s%s\n"
            "    (CallFunction|SimulateIncoming)\n    (Variables|Default|SetDemoStep (+ s 1))))" % (n, n, chain, ")" * n))


DEMO_TICK = demo_tick()


FUNCTIONS.update({
    # rows <-> conversations: RowIndex is the conversation index (Motion 03 rotates it with the row data)
    "LoadData": f'''(fn LoadData ()
  (bind d (Variables|Default|GetData))
  (Utilities|IsValid d
    (:"Is Valid"
      (Variables|Default|SetConversations (Class|BPMessagingData|GetConversations :self d))
{per_row("      (" + ROW + "SetRowIndex :self {r} :RowIndex {i})")}
      (CallFunction|SelectConversation :Index (Class|BPMessagingData|GetSelectedConversation :self d)))))''',
    "SelectConversation": '''(fn SelectConversation (Index)
  (Variables|Default|SetSelectedConv Index)
  (CallFunction|RefreshHighlights)
  (CallFunction|ShowConversation))''',
    # highlight = selected or unread; opening a conversation marks it read
    "RefreshHighlights": "(fn RefreshHighlights ()\n" + per_row(
        "  (" + ROW + "SetUnread :self {r} :bUnread (and (" + ROW + "GetUnread :self {r}) (!= (" + IDX + ") " + SEL + ")))\n"
        "  (" + ROW + "SetSelected :self {r} :InSelected (or (== (" + IDX + ") " + SEL + ") (" + ROW + "GetUnread :self {r})))") + ")",
    "ShowConversation": f'''(fn ShowConversation ()
  (Variables|Default|SetCurrentConv (Utilities|Array|Get(acopy) (Variables|Default|GetConversations) {SEL}))
  (bind conv (Variables|Default|GetCurrentConv))
  (Widget|Panel|ClearChildren ({V}MessageList))
  (Widget|SetText(Text) ({V}ChatTitle) (Class|BPConversation|GetName :self conv))
  (Class|WBPDetailsPanel|SetContactName :self ({V}DetailsPanel) :ContactName (Class|BPConversation|GetName :self conv))
  (Class|WBPDetailsPanel|ApplyProps :self ({V}DetailsPanel))
  (Variables|Default|SetTmpReplied false)
  (for i (range (Utilities|Array|Length (Variables|Default|GetSessionConv)))
    (if (and {IN_SESSION.format(i="i")} (Class|BPChatMessage|GetOutgoing :self (Utilities|Array|Get(acopy) (Variables|Default|GetSessionMessages) i)))
      (Variables|Default|SetTmpReplied true)))
  (for m (Class|BPConversation|GetMessages :self conv)
    (if (or (not (Variables|Default|GetTmpReplied)) (!= (Class|BPChatMessage|GetKind :self m) 3))
      (CallFunction|AddMessage :Msg m :bAnimate false)))
  (for j (range (Utilities|Array|Length (Variables|Default|GetSessionConv)))
    (if {IN_SESSION.format(i="j")}
      (CallFunction|AddMessage :Msg (Utilities|Array|Get(acopy) (Variables|Default|GetSessionMessages) j) :bAnimate false)))
  (CallFunction|ShowSuggestions :bShow (not (Variables|Default|GetTmpReplied)))
  (Widget|ScrolltoEnd ({V}MessageScroll)))''',
    "ShowSuggestions": f'''(fn ShowSuggestions (bShow)
  (bind labels (Class|BPConversation|GetSuggestions :self (Variables|Default|GetCurrentConv)))
  (bind n (Utilities|Array|Length labels))
  ({STOP} :InAnimation ({A}Anim_SuggestionsOut))
  (Widget|SetRenderOpacity ({V}SuggestionsInner) (select (and bShow (> n 0)) 1.0 0.0))
  (Layout|SizeBox|SetMaxDesiredHeight ({V}SuggestionsInner) (select (and bShow (> n 0)) {SUGGEST_H}.0 0.0))
''' + "\n".join(f'''  (if (> n {k})
    (Class|WBPSuggestionChip|SetChipLabel :self ({V}Chip{k + 1}) :ChipLabel (Utilities|Text|ToText(String) (Utilities|Array|Get(acopy) labels {k})))
    (Class|WBPSuggestionChip|ApplyProps :self ({V}Chip{k + 1}))
    (Widget|SetVisibility ({V}Chip{k + 1}) "Visible")
    (else
      (Widget|SetVisibility ({V}Chip{k + 1}) "Collapsed")))''' for k in range(3)) + ")",
    "HideSuggestions": f'''(fn HideSuggestions ()
  (if (> (Widget|GetRenderOpacity ({V}SuggestionsInner)) 0.5)
    ({PLAY} :InAnimation ({A}Anim_SuggestionsOut))))''',
    # one message -> widget; Kind 2 voice note, 3 typing indicator, else link card / bubble
    "AddMessage": f'''(fn AddMessage (Msg bAnimate)
  (bind kind (Class|BPChatMessage|GetKind :self Msg))
  (bind out (Class|BPChatMessage|GetOutgoing :self Msg))
  (bind list ({V}MessageList))
  (bind pc (Widget|GetOwningPlayer self))
  (if (== kind 2)
    (bind v (UserInterface|CreateWidget "{W}WBP_VoiceMessage.WBP_VoiceMessage_C" pc))
    (Class|WBPVoiceMessage|SetDuration :self v :Duration (Class|BPChatMessage|GetText :self Msg))
    (Panel|AddChildtoVerticalBox list v)
    (if bAnimate
      (Class|WBPVoiceMessage|PlayIntro :self v))
    (elif (== kind 3)
      (Panel|AddChildtoVerticalBox list (UserInterface|CreateWidget "{W}WBP_TypingIndicator.WBP_TypingIndicator_C" pc))
      (elif (Class|BPChatMessage|GetIsLink :self Msg)
        (bind card (UserInterface|CreateWidget "{W}WBP_LinkCard.WBP_LinkCard_C" pc))
        (Class|WBPLinkCard|ApplyData :self card :InTitle (Class|BPChatMessage|GetLinkTitle :self Msg) :InUrl (Class|BPChatMessage|GetLinkUrl :self Msg) :InImage (Class|BPChatMessage|GetLinkImage :self Msg) :InOutgoing out)
        (Panel|AddChildtoVerticalBox list card)
        (else
          (bind bubble (UserInterface|CreateWidget "{W}WBP_ChatBubble.WBP_ChatBubble_C" pc))
          (Class|WBPChatBubble|ApplyData :self bubble :InText (Class|BPChatMessage|GetText :self Msg) :InOutgoing out :InAvatar (Class|BPConversation|GetAvatar :self (Variables|Default|GetCurrentConv)))
          (Panel|AddChildtoVerticalBox list bubble)
          (if bAnimate
            (Class|WBPChatBubble|PlayIntro :self bubble :InOutgoing out)))))))''',
    # the other side stops "typing" once we reply
    "RemoveTyping": f'''(fn RemoveTyping ()
  (bind list ({V}MessageList))
  (bind n (Widget|Panel|GetChildrenCount list))
  (if (> n 0)
    (bind t (Utilities|Casting|CastToWBP_TypingIndicator :Object (Widget|Panel|GetChildAt list (- n 1)))
      (:then
        (Widget|RemovefromParent t))
      (:CastFailed))))''',
    "SendText": f'''(fn SendText (InText)
  (if (not (Utilities|Text|TextIsEmpty InText))
    (bind m (Game|ConstructObjectfromClass "{MSG_CLASS}" self))
    (Class|BPChatMessage|InitMessage :self m :InText InText :InOutgoing true)
    (Utilities|Array|Add (Variables|Default|GetSessionMessages) m)
    (Utilities|Array|Add (Variables|Default|GetSessionConv) {SEL})
    (CallFunction|RemoveTyping)
    (CallFunction|AddMessage :Msg m :bAnimate true)
    (CallFunction|UpdateSelectedRow :InPreview InText)
    (CallFunction|RefreshHighlights)
    (CallFunction|HideSuggestions)
    (Widget|ScrolltoEnd ({V}MessageScroll))))''',
    "SendFromInput": f'''(fn SendFromInput ()
  (CallFunction|SendText :InText (Widget|GetText(EditableText) ({V}MessageInput)))
  (Widget|SetText(EditableText) ({V}MessageInput) (Utilities|Text|ToText(String) "")))''',
    "UpdateSelectedRow": "(fn UpdateSelectedRow (InPreview)\n" + per_row(
        "  (if (== (" + IDX + ") " + SEL + ")\n"
        "    (" + ROW + "SetRowPreview :self {r} :RowPreview InPreview)\n"
        "    (" + ROW + "SetRowTime :self {r} :RowTime (Utilities|Text|ToText(String) \"now\"))\n"
        "    (" + ROW + "ApplyProps :self {r}))") + ")",
    # 03: the new message also goes into the session (and into the open chat if it is this conversation)
    "SimulateIncoming": f'''(fn SimulateIncoming ()
  (if (not (Variables|Default|GetMovingRow))
    (Variables|Default|SetMovingRow true)
    (bind m (Game|ConstructObjectfromClass "{MSG_CLASS}" self))
    (Class|BPChatMessage|InitMessage :self m :InText (Variables|Default|GetIncomingText) :InOutgoing false)
    (Utilities|Array|Add (Variables|Default|GetSessionMessages) m)
    (Utilities|Array|Add (Variables|Default|GetSessionConv) ({ROW}GetRowIndex :self ({V}Row6)))
    ({ROW}ShowIncoming :self ({V}Row6) :InPreview (Variables|Default|GetIncomingText) :InTime (Utilities|Text|ToText(String) "now"))
    ({PLAY} :InAnimation ({A}Anim_NewMessage))
    ({TIMER} "FinishIncoming" :Time 1.1 :bLooping false)
    (if (== ({ROW}GetRowIndex :self ({V}Row6)) {SEL})
      (CallFunction|AddMessage :Msg m :bAnimate true)
      (Widget|ScrolltoEnd ({V}MessageScroll)))))''',
    "FinishIncoming": rotate_rows(),
    # debug trigger for Motion 03: N = incoming message
    "OnKeyDown": '''(fn OnKeyDown (MyGeometry InKeyEvent)
  (if (Utilities|String|Equal,CaseInsensitive(String) :A (Utilities|String|ToString(Text) (Input|Key|GetKeyDisplayName (Input|KeyEvent|GetKey InKeyEvent))) :B "N")
    (Variables|Default|SetIncomingText (Utilities|Text|ToText(String) "Are we still on for tonight?"))
    (CallFunction|SimulateIncoming)
    (return (Widget|EventReply|Handled))
    (else
      (return (Widget|EventReply|Unhandled)))))''',
    # Demo button (conversation list header): incoming activity only. Every DEMO_EVERY s the conversation in slot 6
    # gets a new message and moves to the top (Motion 03); texts cycle through DEMO_TEXTS. The button toggles it.
    "DemoTick": DEMO_TICK,
    "ToggleDemo": f'''(fn ToggleDemo ()
  (if (Variables|Default|GetDemoRunning)
    (Variables|Default|SetDemoRunning false)
    (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "DemoTick")
    (Widget|SetText(Text) ({V}DemoLabel) (Utilities|Text|ToText(String) "Demo"))
    (else
      (Variables|Default|SetDemoRunning true)
      (Widget|SetText(Text) ({V}DemoLabel) (Utilities|Text|ToText(String) "Stop"))
      (CallFunction|DemoTick)
      ({TIMER} "DemoTick" :Time {DEMO_EVERY} :bLooping true))))''',
})
DATA_BP = "/Game/UI/Messaging/Data/"
PARAMS = {
    "SelectConversation": [("Index", "int")],
    "ShowSuggestions": [("bShow", "bool")],
    "AddMessage": [("Msg", DATA_BP + "BP_ChatMessage.BP_ChatMessage_C"), ("bAnimate", "bool")],
    "SendText": [("InText", "text")],
    "UpdateSelectedRow": [("InPreview", "text")],
}
EXTRA_VARS = [("bMovingRow", "bool"), ("TmpRowName", "text"), ("TmpRowPreview", "text"), ("TmpRowTime", "text"),
              ("TmpUnread", "bool"), ("TmpRowIndex", "int"), ("TmpReplied", "bool"), ("SelectedConv", "int"),
              ("SessionConv", "int", "ARRAY"), ("IncomingText", "text"), ("DemoStep", "int"), ("bDemoRunning", "bool"),
              ("Data", DATA_BP + "BP_MessagingData.BP_MessagingData_C"),
              ("Conversations", DATA_BP + "BP_Conversation.BP_Conversation_C", "ARRAY"),
              ("CurrentConv", DATA_BP + "BP_Conversation.BP_Conversation_C"),
              ("SessionMessages", DATA_BP + "BP_ChatMessage.BP_ChatMessage_C", "ARRAY")]
# load the conversations; keyboard focus for the debug key (buttons are not focusable, so clicks leave focus here)
CONSTRUCT = ("LoadData", """(event UserInterface|EventConstruct
  (CallFunction|LoadData)
  (Variables|Interaction|SetIsFocusable true)
  (Widget|SetKeyboardFocus self))""")

ROW_CLASS = W + "WBP_ConversationRow.WBP_ConversationRow_C"
CHIP_CLASS = W + "WBP_SuggestionChip.WBP_SuggestionChip_C"
# (widget variable, event, class declaring it, handler: function name or DSL body, event params)
BINDINGS = [
    ("ListToggleButton", "OnClicked", "/Script/UMG.Button", "ToggleList"),
    ("MoreButton", "OnClicked", "/Script/UMG.Button", "OpenDetails"),
    ("AddButton", "OnClicked", "/Script/UMG.Button", "ToggleAttach"),
    ("MicButton", "OnClicked", "/Script/UMG.Button", "StartVoice"),
    ("DetailsPanel", "OnClose", W + "WBP_DetailsPanel.WBP_DetailsPanel_C", "CloseDetails"),
    ("RecordingBar", "OnStop", W + "WBP_RecordingBar.WBP_RecordingBar_C", "StopVoice"),
    ("AttachMenu", "OnItemPicked", W + "WBP_AttachMenu.WBP_AttachMenu_C", "CloseAttach"),
    ("DemoButton", "OnClicked", "/Script/UMG.Button", "ToggleDemo"),
    ("MessageInput", "OnTextCommitted", "/Script/UMG.EditableText", "WIRE_ENTER"),
] + [("Row%d" % k, "OnRowClicked", ROW_CLASS,
      "(CallFunction|SelectConversation :Index (%sGetRowIndex :self (%sRow%d)))" % (ROW, V, k)) for k in ROWS] \
  + [("Chip%d" % k, "OnChipClicked", CHIP_CLASS,
      "(CallFunction|SendText :InText (Class|WBPSuggestionChip|GetChipLabel :self (%sChip%d)))" % (V, k)) for k in range(1, 4)]


def wire_enter(eg):
    """Enter in MessageInput -> SendFromInput. The DSL can't address this event (its name carries the class:
    OnTextCommitted(EditableText)(MessageInput)), so the switch and call nodes are placed and wired directly."""
    ev = call(BP_TOOLS, "find_nodes", {"graph": eg, "title": "OnTextCommitted", "entry_points_only": True})[0]
    info = lambda n: call(BP_TOOLS, "get_node_infos", {"nodes": [n]})[0]
    pin = lambda i, side, name: [p for p in i[side] if p["name"] == name][0]["pin_id"]
    evi = info(ev)
    sw = call(BP_TOOLS, "create_node", {"graph": eg, "type_id": "Utilities|FlowControl|Switch|SwitchonETextCommit", "pos": {"x": 600, "y": 1400}})
    fn = call(BP_TOOLS, "create_node", {"graph": eg, "type_id": "CallFunction|SendFromInput", "pos": {"x": 900, "y": 1400}})
    swi, fni = info(sw), info(fn)
    call(BP_TOOLS, "connect_pins", {"output_pin": pin(evi, "output_pins", "then"), "input_pin": pin(swi, "input_pins", "execute")})
    call(BP_TOOLS, "connect_pins", {"output_pin": pin(evi, "output_pins", "CommitMethod"), "input_pin": pin(swi, "input_pins", "Selection")})
    call(BP_TOOLS, "connect_pins", {"output_pin": pin(swi, "output_pins", "OnEnter"), "input_pin": pin(fni, "input_pins", "execute")})


def compile_bp():
    return call(UMG_TOOLS, "CompileWidgetBlueprint", {"widgetBlueprint": REF})


def add_vars():
    have = json.dumps(call(BP_TOOLS, "list_variables", {"blueprint": REF}))
    for var in EXTRA_VARS:
        name, typ = var[0], var[1]
        if '"%s"' % name in have:
            continue
        args = {"blueprint": REF, "name": name}
        if len(var) > 2:
            args["container_type"] = var[2]
        if typ.startswith("/"):
            call(BP_TOOLS, "add_object_variable", dict(args, object_class={"refPath": typ}))
        else:
            call(BP_TOOLS, "add_variable", dict(args, type_name=typ))


def add_functions():
    have = [g["refPath"].split(":")[-1] for g in call(BP_TOOLS, "list_graphs", {"blueprint": REF})]
    for fn in FUNCTIONS:
        if fn in have:
            continue
        g = call(BP_TOOLS, "add_function_graph", {"blueprint": REF, "graph_name": fn})
        for pname, ptype in PARAMS.get(fn, []):
            if ptype.startswith("/"):
                call(BP_TOOLS, "add_object_function_param", {"graph": g, "param_name": pname, "object_class": {"refPath": ptype},
                                                             "input_param": True})
            else:
                call(BP_TOOLS, "add_function_param", {"graph": g, "param_name": pname, "param_type": ptype, "input_param": True})


def main():
    for name, (duration, tracks) in ANIMS.items():
        call(ANIM_TOOLS, "CreateAnimation", {"widgetBlueprint": REF, "name": name, "duration": duration, "bReplaceExisting": True})
        for widget, prop, keys in tracks:
            call(ANIM_TOOLS, "SetKeys", {"widgetBlueprint": REF, "animationName": name, "widgetName": widget, "property": prop,
                                         "keys": [{"time": k[0], "value": k[1], "ease": k[2] if len(k) > 2 else E} for k in keys]})
    print("animations:", [a["name"] for a in call(ANIM_TOOLS, "ListAnimations", {"widgetBlueprint": REF})])

    add_vars()
    add_functions()
    # After gen_layout.py rebuilt the tree every function still referencing the old widget variables has dangling
    # Target pins, and write_graph_dsl compiles after each write — so tolerate compile errors until all are rewritten.
    for fn, code in FUNCTIONS.items():
        try:
            call(BP_TOOLS, "write_graph_dsl", {"graph": {"refPath": REF["refPath"] + ":" + fn}, "code": code})
        except RuntimeError as e:
            if "failed to compile" not in str(e):
                raise RuntimeError("%s: %s" % (fn, e))
    print("compile after functions:", compile_bp())

    eg = {"refPath": REF["refPath"] + ":EventGraph"}
    graph = call(BP_TOOLS, "read_graph_dsl", {"graph": eg})
    if CONSTRUCT[0] not in graph:
        call(BP_TOOLS, "write_graph_dsl", {"graph": eg, "code": CONSTRUCT[1]})
    # DSL names some bound events after the declaring class too, e.g. OnTextCommitted(EditableText)(MessageInput)
    labels = {"OnTextCommitted": "OnTextCommitted(EditableText)"}
    for var, event, cls, handler, *params in BINDINGS:
        header = "(event %s(%s)" % (labels.get(event, event), var)
        body = handler if handler.startswith("(") else "(CallFunction|%s)" % handler
        pos = graph.find(header)
        block = graph[pos:graph.find("\n\n", pos)] if pos >= 0 else ""
        marker = "SendFromInput" if handler == "WIRE_ENTER" else body.split("(CallFunction|")[-1].split(")")[0]
        if marker.lower() in block.lower():
            continue  # already bound with this handler; rewriting would spawn duplicate event nodes
        if pos < 0:
            call(UMG_TOOLS, "BindToEventProperty", {"widgetBlueprint": REF, "eventName": event, "propertyName": var,
                                                   "propertyClass": {"refPath": cls}})
        if handler == "WIRE_ENTER":
            wire_enter(eg)
            continue
        call(BP_TOOLS, "write_graph_dsl", {"graph": eg, "code": "%s%s\n  %s)" % (header, (" " + params[0]) if params else "", body)})
    print("compile after bindings:", compile_bp())
    # default conversation data for the layout (class default)
    call(OBJ_TOOLS, "set_properties", {"instance": {"refPath": "/Game/UI/Messaging/WBP_MessagingLayout.Default__WBP_MessagingLayout_C"},
                                      "values": json.dumps({"Data": {"refPath": DATA_ASSET}})})
    print(call(BP_TOOLS, "read_graph_dsl", {"graph": eg}))


if __name__ == "__main__":
    main()
