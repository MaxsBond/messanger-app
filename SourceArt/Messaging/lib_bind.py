import json
BT="editor_toolset.toolsets.blueprint.BlueprintTools."
def T(n,a): return execute_tool(n, json.dumps(a))
def info(node): return T(BT+"get_node_infos",{"nodes":[node]})["returnValue"][0]
def pin(node,name,dirn):
    i=info(node)
    for p in i["output_pins" if dirn=="out" else "input_pins"]:
        if p["name"]==name: return p["pin_id"]
    raise Exception("no pin %s: %s"%(name,[p["name"] for p in i["output_pins"]+i["input_pins"]]))
def cleanup(G, keep):
    for n in T(BT+"find_nodes",{"graph":{"refPath":G},"title":""})["returnValue"]:
        if n["refPath"].split(".")[-1] not in keep:
            T(BT+"delete_node",{"node":n})
def assign(G, exec_from, assign_type, getter_type, y):
    g={"refPath":G}
    a=T(BT+"create_node",{"graph":g,"type_id":assign_type,"pos":{"x":400,"y":y}})["returnValue"]
    gt=T(BT+"create_node",{"graph":g,"type_id":getter_type,"pos":{"x":150,"y":y+120}})["returnValue"]
    T(BT+"connect_pins",{"output_pin":exec_from,"input_pin":pin(a,"execute","in")})
    T(BT+"connect_pins",{"output_pin":info(gt)["output_pins"][0]["pin_id"],"input_pin":pin(a,"self","in")})
    ce=None
    for p in info(a)["input_pins"]:
        if p["name"]=="Delegate": ce=p["connected_pins"][0]["node"]
    return pin(a,"then","out"), ce
