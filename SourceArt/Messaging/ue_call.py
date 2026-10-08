# usage: python3 ue_call.py payload.json  -> posts {"name","arguments"} as tools/call to Unreal MCP
import json, sys, urllib.request
U = "http://127.0.0.1:8000/mcp"
H = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
def post(body, sid=None):
    h = dict(H)
    if sid: h["Mcp-Session-Id"] = sid
    r = urllib.request.urlopen(urllib.request.Request(U, json.dumps(body).encode(), h), timeout=600)
    return r.headers.get("Mcp-Session-Id"), r.read().decode()
sid, _ = post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "cli", "version": "1"}}})
post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
_, out = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": json.load(open(sys.argv[1]))}, sid)
for line in out.splitlines():
    if line.startswith("data:"): out = line[5:]
try:
    res = json.loads(out)["result"]
    for c in res.get("content", []): print(c.get("text", c))
    if res.get("isError"): sys.exit(1)
except Exception:
    print(out)
