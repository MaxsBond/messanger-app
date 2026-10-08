# usage: hook.py out.json NAME...  connects EventPreConstruct -> ApplyProps() in each WBP's EventGraph (idempotent)
import json,sys
W="/Game/UI/Messaging/Widgets/"
paths=[W+n+"."+n for n in sys.argv[2:]]
script='''
import json
PATHS=%r
BT="editor_toolset.toolsets.blueprint.BlueprintTools."
def T(n,a): return execute_tool(n, json.dumps(a))
def info(n): return T(BT+"get_node_infos",{"nodes":[n]})["returnValue"][0]
def run():
    out={}
    for path in PATHS:
        eg={"refPath":path+":EventGraph"}
        pre=None
        for n in T(BT+"find_nodes",{"graph":eg,"title":"","entry_points_only":True})["returnValue"]:
            i=info(n)
            if "PreConstruct" in json.dumps(i).replace(" ",""): pre=(n,i)
        if pre is None:
            out[path]="no PreConstruct"; continue
        n,i=pre
        thenpin=[p for p in i["output_pins"] if p["name"]=="then"][0]
        if thenpin.get("connected_pins"):
            out[path]="PreConstruct already connected: "+str(thenpin["connected_pins"])[:200]; continue
        c=T(BT+"create_node",{"graph":eg,"type_id":"CallFunction|ApplyProps","pos":{"x":400,"y":0}})["returnValue"]
        ci=info(c)
        ex=[p for p in ci["input_pins"] if p["name"]=="execute"][0]
        T(BT+"connect_pins",{"output_pin":thenpin["pin_id"],"input_pin":ex["pin_id"]})
        T(BT+"compile_blueprint",{"blueprint":{"refPath":path}})
        out[path]="hooked"
    return out
'''%(paths,)
json.dump({"name":"call_tool","arguments":{"toolset_name":"editor_toolset.toolsets.programmatic.ProgrammaticToolset","tool_name":"execute_tool_script","arguments":{"script":script}}},open(sys.argv[1],"w"))
