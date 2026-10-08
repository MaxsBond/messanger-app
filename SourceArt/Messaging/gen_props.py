# usage: props.py out.json NAME...   builds a script that adds instance-editable "Content" props + ApplyProps() + PreConstruct call
import json,sys
W="/Game/UI/Messaging/Widgets/"
SPECS={
 "WBP_SuggestionChip": ([("ChipLabel","text")],
  '''(fn ApplyProps ()
  (if (not (Utilities|Text|TextIsEmpty (Variables|Content|GetChipLabel)))
    (CallFunction|SetData :InLabel (Variables|Content|GetChipLabel))))'''),
 "WBP_ConversationRow": ([("RowName","text"),("RowPreview","text"),("RowTime","text"),("bUnread","bool")],
  '''(fn ApplyProps ()
  (if (not (Utilities|Text|TextIsEmpty (Variables|Content|GetRowName)))
    (CallFunction|SetData :InName (Variables|Content|GetRowName) :InPreview (Variables|Content|GetRowPreview) :InTime (Variables|Content|GetRowTime))
    (CallFunction|SetSelected :InSelected (Variables|Content|GetUnread))))'''),
 "WBP_ChatBubble": ([("MessageText","text"),("bOutgoing","bool")],
  '''(fn ApplyProps ()
  (if (not (Utilities|Text|TextIsEmpty (Variables|Content|GetMessageText)))
    (CallFunction|ApplyData :InText (Variables|Content|GetMessageText) :InOutgoing (Variables|Content|GetOutgoing))))'''),
 "WBP_LinkCard": ([("CardTitle","text"),("CardUrl","text"),("bOutgoing","bool")],
  '''(fn ApplyProps ()
  (if (not (Utilities|Text|TextIsEmpty (Variables|Content|GetCardTitle)))
    (CallFunction|ApplyData :InTitle (Variables|Content|GetCardTitle) :InUrl (Variables|Content|GetCardUrl) :InOutgoing (Variables|Content|GetOutgoing))))'''),
 "WBP_VoiceMessage": ([("Duration","text")],
  '''(fn ApplyProps ()
  (if (not (Utilities|Text|TextIsEmpty (Variables|Content|GetDuration)))
    (Widget|SetText(Text) (Variables|WBP_VoiceMessage|GetDurationText) (Variables|Content|GetDuration))))'''),
 "WBP_RecordingBar": ([("RecTime","text")],
  '''(fn ApplyProps ()
  (if (not (Utilities|Text|TextIsEmpty (Variables|Content|GetRecTime)))
    (Widget|SetText(Text) (Variables|WBP_RecordingBar|GetTimeText) (Variables|Content|GetRecTime))))'''),
 "WBP_DetailsPanel": ([("ContactName","text"),("Status","text")],
  '''(fn ApplyProps ()
  (if (not (Utilities|Text|TextIsEmpty (Variables|Content|GetContactName)))
    (Widget|SetText(Text) (Variables|WBP_DetailsPanel|GetNameText) (Variables|Content|GetContactName))
    (Widget|SetText(Text) (Variables|WBP_DetailsPanel|GetStatusText) (Variables|Content|GetStatus))))'''),
}
names=sys.argv[2:]
targets=[(W+n+"."+n,SPECS[n][0],SPECS[n][1]) for n in names]
script='''
import json
TARGETS=%r
BT="editor_toolset.toolsets.blueprint.BlueprintTools."
log=[]
def T(n,a): return execute_tool(n, json.dumps(a))
def run():
    for path,vars_,dsl in TARGETS:
        bp={"refPath":path}
        have=[str(v) for v in T(BT+"list_variables",{"blueprint":bp})["returnValue"]]
        for name,typ in vars_:
            if not any(("'"+name+"'") in h or ('"'+name+'"') in h or h==name for h in have):
                T(BT+"add_variable",{"blueprint":bp,"name":name,"type_name":typ})
            T(BT+"set_variable_instance_editable",{"blueprint":bp,"variable_name":name,"instance_editable":True})
            T(BT+"set_variable_category",{"blueprint":bp,"variable_name":name,"category":"Content"})
        g=T(BT+"add_function_graph",{"blueprint":bp,"graph_name":"ApplyProps"})["returnValue"]
        T(BT+"write_graph_dsl",{"graph":g,"code":dsl})
        eg={"refPath":path+":EventGraph"}
        pre=T(BT+"find_nodes",{"graph":eg,"title":"Pre Construct"})["returnValue"]
        called=T(BT+"find_nodes",{"graph":eg,"title":"Apply Props"})["returnValue"]
        if pre and not called:
            types=T(BT+"find_node_types",{"graph":eg,"search":"ApplyProps"})["returnValue"]
            log.append([path,"types",str(types)[:300]])
        log.append([path,"pre",str(pre)[:200],"called",str(called)[:200],"vars",have])
    return {"log":log}
'''%(targets,)
json.dump({"name":"call_tool","arguments":{"toolset_name":"editor_toolset.toolsets.programmatic.ProgrammaticToolset","tool_name":"execute_tool_script","arguments":{"script":script}}},open(sys.argv[1],"w"))
