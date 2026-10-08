# Adds the Figma base-state props to WBP_MessagingLayout and an ApplyState() run from PreConstruct:
#   State: 0 = chat list open, 1 = chat list collapsed, 2 = details open (list collapsed, ⋮ hidden)
#   bAttachMenuOpen, bRecording (recording also hides the suggestions, like Motion 05)
# usage: python3 gen_layout_state.py payload.json
import json, sys

BP = "/Game/UI/Messaging/WBP_MessagingLayout.WBP_MessagingLayout"
ICONS = "/Game/UI/Messaging/Icons/"
VARS = [("State", "int"), ("bAttachMenuOpen", "bool"), ("bRecording", "bool")]
L = "Variables|WBP_MessagingLayout|Get"
DSL = '''(fn ApplyState ()
  (bind _state (Variables|State|GetState))
  (Switcher|SetActiveWidgetIndex (%(L)sListSwitcher) (select (== _state 0) 0 1))
  (Switcher|SetActiveWidgetIndex (%(L)sDetailsSwitcher) (select (== _state 2) 1 0))
  (Switcher|SetActiveWidgetIndex (%(L)sAttachSwitcher) (select (Variables|State|GetAttachMenuOpen) 1 0))
  (Switcher|SetActiveWidgetIndex (%(L)sComposerSwitcher) (select (Variables|State|GetRecording) 1 0))
  (Widget|SetRenderOpacity (%(L)sMoreButton) (select (== _state 2) 0.0 1.0))
  (Widget|SetRenderOpacity (%(L)sSuggestionsRow) (select (Variables|State|GetRecording) 0.0 1.0))
  (if (Variables|State|GetRecording)
    (Widget|SetVisibility (%(L)sSuggestionsRow) "Collapsed")
    (else
      (Widget|SetVisibility (%(L)sSuggestionsRow) "Visible")))
  (if (== _state 0)
    (Appearance|SetBrushResourceObject (%(L)sListToggleButtonGlyph) "%(I)sT_Icon_left_panel_close.T_Icon_left_panel_close")
    (else
      (Appearance|SetBrushResourceObject (%(L)sListToggleButtonGlyph) "%(I)sT_Icon_left_panel_open.T_Icon_left_panel_open"))))''' % {"L": L, "I": ICONS}

script = '''
import json
BP=%r; VARS=%r; DSL=%r
BT="editor_toolset.toolsets.blueprint.BlueprintTools."
def T(n,a): return execute_tool(n, json.dumps(a))
def info(n): return T(BT+"get_node_infos",{"nodes":[n]})["returnValue"][0]
def run():
    bp={"refPath":BP}
    have=[str(v) for v in T(BT+"list_variables",{"blueprint":bp})["returnValue"]]
    for name,typ in VARS:
        if name not in have:
            T(BT+"add_variable",{"blueprint":bp,"name":name,"type_name":typ})
        T(BT+"set_variable_instance_editable",{"blueprint":bp,"variable_name":name,"instance_editable":True})
        T(BT+"set_variable_category",{"blueprint":bp,"variable_name":name,"category":"State"})
    g=T(BT+"add_function_graph",{"blueprint":bp,"graph_name":"ApplyState"})["returnValue"]
    T(BT+"write_graph_dsl",{"graph":g,"code":DSL})
    eg={"refPath":BP+":EventGraph"}
    res="no PreConstruct"
    for n in T(BT+"find_nodes",{"graph":eg,"title":"","entry_points_only":True})["returnValue"]:
        i=info(n)
        if "PreConstruct" not in json.dumps(i).replace(" ",""): continue
        then=[p for p in i["output_pins"] if p["name"]=="then"][0]
        if then.get("connected_pins"):
            res="already hooked"; break
        c=T(BT+"create_node",{"graph":eg,"type_id":"CallFunction|ApplyState","pos":{"x":400,"y":0}})["returnValue"]
        ex=[p for p in info(c)["input_pins"] if p["name"]=="execute"][0]
        T(BT+"connect_pins",{"output_pin":then["pin_id"],"input_pin":ex["pin_id"]})
        res="hooked"
    comp=T("UMGToolSet.UMGToolSet.CompileWidgetBlueprint",{"widgetBlueprint":bp})
    return {"hook":res,"compile":str(comp),"vars":have}
''' % (BP, VARS, DSL)
json.dump({"name": "call_tool", "arguments": {"toolset_name": "editor_toolset.toolsets.programmatic.ProgrammaticToolset",
           "tool_name": "execute_tool_script", "arguments": {"script": script}}}, open(sys.argv[1], "w"))
