# Component-side motion for the Figma "Unreal Engine Target" → Motion page (needs the UMGAnimToolset plugin).
# Run after gen_components.py and before gen_layout_motion.py; safe to rerun.
#   WBP_TypingIndicator  Anim_Typing (04, loops from Construct)
#   WBP_AttachMenu       Anim_ItemsIn + PlayItemsIn(), dispatcher OnItemPicked (File/Photo/Video buttons)
#   WBP_DetailsPanel     Anim_Reveal + PlayReveal(), dispatcher OnClose (CloseButton)
#   WBP_RecordingBar     Anim_RecBlink + StartRecording()/StopRecording() (timer + waveform), dispatcher OnStop (StopButton)
#   WBP_VoiceMessage     Anim_PopIn + PlayIntro() (pivot bottom-right is set in gen_components.py)
#   WBP_ConversationRow  Anim_Incoming + ShowIncoming(preview, time) (03: texts dip and swap, unread highlight),
#                        dispatcher OnRowClicked (RowButton; the old WBP_Test owner call stays)
#   WBP_SuggestionChip   dispatcher OnChipClicked (ChipButton; the old WBP_Test owner call stays)
#   WBP_ChatBubble       Anim_PopIn + PlayIntro(bOutgoing) (sent / received bubbles pop from their bottom corner)
# usage: python3 gen_components_motion.py
import json
from ue_mcp import call, BP_TOOLS, ANIM_TOOLS, UMG_TOOLS

W = "/Game/UI/Messaging/Widgets/"
PLAY = "UserInterface|Animation|PlayAnimation"


def ref(name):
    return {"refPath": "%s%s.%s" % (W, name, name)}


def staggered(widgets, start, step, dur, rise):
    """fade in + rise `rise` px, one widget after another"""
    tracks = []
    for i, w in enumerate(widgets):
        t0 = round(start + step * i, 3)
        t1 = round(t0 + dur, 3)
        tracks += [(w, "RenderOpacity", [(0, 0, "constant"), (t0, 0, "easeOut"), (t1, 1)]),
                   (w, "Translation.Y", [(0, rise, "constant"), (t0, rise, "easeOut"), (t1, 0)])]
    return tracks


def typing_dots():
    """04: dot rises 5px and brightens 40% -> 100%, next dot +150ms, 1.2s seamless loop"""
    tracks = []
    for i in range(3):
        t0 = round(0.1 + 0.15 * i, 3)
        for prop, rest, peak in (("Translation.Y", 0, -5), ("RenderOpacity", 0.4, 1)):
            tracks.append(("Dot%d" % (i + 1), prop, [(0, rest, "constant"), (t0, rest, "easeInOut"), (round(t0 + 0.18, 3), peak, "easeInOut"),
                                                      (round(t0 + 0.36, 3), rest, "constant"), (1.2, rest)]))
    return tracks


V_REC = "Variables|WBP_RecordingBar|Get"
REC_FUNCTIONS = {
    "TickRecClock": f'''(fn TickRecClock ()
  (Variables|Default|SetRecSeconds (+ (Variables|Default|GetRecSeconds) 1))
  (bind s (Variables|Default|GetRecSeconds))
  (bind sec (- s (* (/ s 60) 60)))
  (Widget|SetText(Text) ({V_REC}TimeText)
    (Utilities|Text|ToText(String) (Utilities|String|Append :A (Utilities|String|Append :A (Utilities|String|ToString(Integer) (/ s 60)) :B (select (< sec 10) ":0" ":")) :B (Utilities|String|ToString(Integer) sec)))))''',
    # waveform grows bar by bar
    "TickRecWave": f'''(fn TickRecWave ()
  (bind wf ({V_REC}Waveform))
  (bind i (Variables|Default|GetWaveIndex))
  (if (< i (Widget|Panel|GetChildrenCount wf))
    (Widget|SetRenderOpacity (Widget|Panel|GetChildAt wf i) 1.0)
    (Variables|Default|SetWaveIndex (+ i 1))))''',
    "StartRecording": f'''(fn StartRecording ()
  (Variables|Default|SetRecSeconds 0)
  (Variables|Default|SetWaveIndex 0)
  (Widget|SetText(Text) ({V_REC}TimeText) (Utilities|Text|ToText(String) "0:00"))
  (bind wf ({V_REC}Waveform))
  (for i (range (Widget|Panel|GetChildrenCount wf))
    (Widget|SetRenderOpacity (Widget|Panel|GetChildAt wf i) 0.15))
  ({PLAY} :InAnimation (Variables|Animations|GetAnim_RecBlink) :NumLoopsToPlay 0)
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "TickRecClock" :Time 1.0 :bLooping true)
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "TickRecWave" :Time 0.06 :bLooping true))''',
    "StopRecording": f'''(fn StopRecording ()
  (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "TickRecClock")
  (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "TickRecWave")
  (UserInterface|Animation|StopAnimation :InAnimation (Variables|Animations|GetAnim_RecBlink))
  (Widget|SetRenderOpacity ({V_REC}RecDot) 1.0))''',
}


ROW_FUNCTIONS = {
    # 03: new message in this conversation — texts fade out, swap at 0.1s, fade back in; unread highlight comes up
    "ShowIncoming": f'''(fn ShowIncoming (InPreview InTime)
  (Variables|Content|SetRowPreview InPreview)
  (Variables|Content|SetRowTime InTime)
  (Variables|Content|SetUnread true)
  ({PLAY} :InAnimation (Variables|Animations|GetAnim_Incoming))
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "SwapIncomingText" :Time 0.1 :bLooping false))''',
    "SwapIncomingText": '''(fn SwapIncomingText ()
  (Widget|SetText(Text) (Variables|WBP_ConversationRow|GetPreviewText) (Variables|Content|GetRowPreview))
  (Widget|SetText(Text) (Variables|WBP_ConversationRow|GetTimeText) (Variables|Content|GetRowTime)))''',
}


def play_fn(fn, anim):
    return {fn: "(fn %s ()\n  (%s :InAnimation (Variables|Animations|Get%s)))" % (fn, PLAY, anim)}


COMPONENTS = {
    "WBP_TypingIndicator": {
        "anims": {"Anim_Typing": (1.2, typing_dots())},
        # header -> (marker already present when done, body)
        "events": {"(event UserInterface|EventConstruct": ("GetAnim_Typing", "(%s :InAnimation (Variables|Animations|GetAnim_Typing) :NumLoopsToPlay 0)" % PLAY)},
    },
    "WBP_AttachMenu": {
        # 02: File, Photo, Video fade in and rise 6px, 60ms apart
        "anims": {"Anim_ItemsIn": (0.4, staggered(["FileItem", "PhotoItem", "VideoItem"], 0.08, 0.06, 0.2, 6))},
        "fns": play_fn("PlayItemsIn", "Anim_ItemsIn"),
        "dispatchers": {"OnItemPicked": ["FileButton", "PhotoButton", "VideoButton"]},
    },
    "WBP_DetailsPanel": {
        # 06: header, profile, actions, media, files fade up in sequence once the panel has slid in
        "anims": {"Anim_Reveal": (0.9, staggered(["Header", "Profile", "Actions", "Divider", "SharedMedia", "Files"], 0.3, 0.07, 0.25, 8))},
        "fns": play_fn("PlayReveal", "Anim_Reveal"),
        "dispatchers": {"OnClose": ["CloseButton"]},
    },
    "WBP_RecordingBar": {
        # 05: red dot blinks every 0.5s
        "anims": {"Anim_RecBlink": (1.0, [("RecDot", "RenderOpacity", [(0, 1, "constant"), (0.5, 0.25, "constant"), (1.0, 1, "constant")])])},
        "vars": [("RecSeconds", "int"), ("WaveIndex", "int")],
        "fns": REC_FUNCTIONS,
        "dispatchers": {"OnStop": ["StopButton"]},
    },
    "WBP_VoiceMessage": {
        # 05: the sent note pops in from the bottom-right
        "anims": {"Anim_PopIn": (0.4, [("VoiceBubble", "Scale.X", [(0, 0.6, "easeOut"), (0.4, 1)]),
                                       ("VoiceBubble", "Scale.Y", [(0, 0.6, "easeOut"), (0.4, 1)]),
                                       ("VoiceBubble", "RenderOpacity", [(0, 0, "easeOut"), (0.2, 1)])])},
        "fns": play_fn("PlayIntro", "Anim_PopIn"),
    },
    "WBP_ConversationRow": {
        "anims": {"Anim_Incoming": (0.25, [
            ("PreviewText", "RenderOpacity", [(0, 1, "easeIn"), (0.1, 0, "easeOut"), (0.2, 1)]),
            ("TimeText", "RenderOpacity", [(0, 1, "easeIn"), (0.1, 0, "easeOut"), (0.2, 1)]),
            ("Highlight", "RenderOpacity", [(0, 0, "easeInOut"), (0.2, 1)])])},
        "fns": ROW_FUNCTIONS,
        "params": {"ShowIncoming": [("InPreview", "text"), ("InTime", "text")]},
        "dispatchers": {"OnRowClicked": ["RowButton"]},
    },
    "WBP_SuggestionChip": {
        "anims": {},
        # ChipButton already has a designer event (calls WBP_Test.SendText); fire the dispatcher before it
        "events": {"(event OnClicked(ChipButton)": ("CallOnChipClicked", """(Default|CallOnChipClicked)
  (bind _owner (Variables|Default|GetOwner))
  (Utilities|IsValid _owner
    (:"Is Valid"
      (Class|WBPTest|SendText _owner (Variables|Default|GetLabel))))""")},
        "dispatchers": {"OnChipClicked": []},
    },
    "WBP_ChatBubble": {
        "anims": {"Anim_PopIn": (0.35, [("Layout", "Scale.X", [(0, 0.6, "easeOut"), (0.35, 1)]),
                                        ("Layout", "Scale.Y", [(0, 0.6, "easeOut"), (0.35, 1)]),
                                        ("Layout", "RenderOpacity", [(0, 0, "easeOut"), (0.18, 1)])])},
        "fns": {"PlayIntro": f"""(fn PlayIntro (InOutgoing)
  (Widget|Transform|SetRenderTransformPivot (Variables|WBP_ChatBubble|GetLayout) (Math|Vector2D|MakeVector2D (select InOutgoing 1.0 0.0) 1.0))
  ({PLAY} :InAnimation (Variables|Animations|GetAnim_PopIn)))"""},
        "params": {"PlayIntro": [("InOutgoing", "bool")]},
    },
}


def build(name, spec):
    r = ref(name)
    eg = {"refPath": r["refPath"] + ":EventGraph"}
    for anim, (duration, tracks) in spec["anims"].items():
        call(ANIM_TOOLS, "CreateAnimation", {"widgetBlueprint": r, "name": anim, "duration": duration, "bReplaceExisting": True})
        for widget, prop, keys in tracks:
            call(ANIM_TOOLS, "SetKeys", {"widgetBlueprint": r, "animationName": anim, "widgetName": widget, "property": prop,
                                         "keys": [{"time": k[0], "value": k[1], "ease": k[2] if len(k) > 2 else "easeInOut"} for k in keys]})
    have_vars = json.dumps(call(BP_TOOLS, "list_variables", {"blueprint": r}))
    for var, typ in spec.get("vars", []):
        if '"%s"' % var not in have_vars:
            call(BP_TOOLS, "add_variable", {"blueprint": r, "name": var, "type_name": typ})
    have_disp = json.dumps(call(BP_TOOLS, "list_event_dispatchers", {"blueprint": r}))
    for disp in spec.get("dispatchers", {}):
        if ":%s\"" % disp not in have_disp:
            call(BP_TOOLS, "add_event_dispatcher", {"blueprint": r, "name": disp})
    call(UMG_TOOLS, "CompileWidgetBlueprint", {"widgetBlueprint": r})  # makes anim getters / dispatcher calls available

    have_fns = json.dumps(call(BP_TOOLS, "list_functions", {"blueprint": r}))
    for fn, code in spec.get("fns", {}).items():
        if ":%s\"" % fn not in have_fns and '"%s"' % fn not in have_fns:
            g = call(BP_TOOLS, "add_function_graph", {"blueprint": r, "graph_name": fn})
            for pname, ptype in spec.get("params", {}).get(fn, []):
                call(BP_TOOLS, "add_function_param", {"graph": g, "param_name": pname, "param_type": ptype, "input_param": True})
        call(BP_TOOLS, "write_graph_dsl", {"graph": {"refPath": r["refPath"] + ":" + fn}, "code": code})

    graph = call(BP_TOOLS, "read_graph_dsl", {"graph": eg})
    for header, (marker, body) in spec.get("events", {}).items():
        if marker not in graph:
            call(BP_TOOLS, "write_graph_dsl", {"graph": eg, "code": "%s\n  %s)" % (header, body)})
    for disp, buttons in spec.get("dispatchers", {}).items():
        for button in buttons:
            header = "(event OnClicked(%s)" % button
            if header not in graph:
                call(UMG_TOOLS, "BindToEventProperty", {"widgetBlueprint": r, "eventName": "OnClicked", "propertyName": button,
                                                       "propertyClass": {"refPath": "/Script/UMG.Button"}})
                call(BP_TOOLS, "write_graph_dsl", {"graph": eg, "code": "%s\n  (Default|Call%s))" % (header, disp)})
    print(name, "compile:", call(UMG_TOOLS, "CompileWidgetBlueprint", {"widgetBlueprint": r}))


if __name__ == "__main__":
    import sys
    for component, spec in COMPONENTS.items():
        if len(sys.argv) < 2 or component in sys.argv[1:]:
            build(component, spec)
