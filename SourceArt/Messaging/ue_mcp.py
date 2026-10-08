# Tiny client for the Unreal MCP server (http://127.0.0.1:8000/mcp): call(toolset, tool, args) -> returnValue.
import json, urllib.request

URL = "http://127.0.0.1:8000/mcp"
BP_TOOLS = "editor_toolset.toolsets.blueprint.BlueprintTools"
OBJ_TOOLS = "editor_toolset.toolsets.object.ObjectTools"
ASSET_TOOLS = "editor_toolset.toolsets.asset.AssetTools"
UMG_TOOLS = "UMGToolSet.UMGToolSet"
ANIM_TOOLS = "UMGAnimToolset.UMGAnimToolset"
_session = [None]


def _post(body):
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if _session[0]:
        h["Mcp-Session-Id"] = _session[0]
    r = urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(), h), timeout=600)
    _session[0] = r.headers.get("Mcp-Session-Id") or _session[0]
    out = r.read().decode()
    for line in out.splitlines():
        if line.startswith("data:"):
            out = line[5:]
    return json.loads(out) if out.strip() else None


def _init():
    _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
           "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "sourceart", "version": "1"}}})
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"})


def call(toolset, tool, args):
    if not _session[0]:
        _init()
    res = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                 "params": {"name": "call_tool", "arguments": {"toolset_name": toolset, "tool_name": tool, "arguments": args}}})["result"]
    text = "".join(c.get("text", "") for c in res.get("content", []))
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if res.get("isError") or not isinstance(data, dict) or "returnValue" not in data:
        raise RuntimeError("%s.%s failed: %s" % (toolset.split(".")[-1], tool, text[:800]))
    return data["returnValue"]
