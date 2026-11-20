"""Import .camtools libraries through CamCraft's own MCP server.

Each library is imported in a FRESH `camcraft-cli mcp` session (one
document per file), via the `import_tool_library` tool, and the result
text is recorded. A refusal (isError) refuses the whole file and names
the tool, so on a refusal the file is also bisected tool by tool through
the same MCP tool to list every refused tool with its message.

Run: python3 -I mcp_import.py /path/to/camcraft-cli lib1.camtools [lib2 ...]
Writes ../import-results.json.
"""
import json
import os
import subprocess
import sys
import tempfile


class Mcp:
    def __init__(self, cli):
        self.p = subprocess.Popen([cli, "mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.n = 0
        self.call_raw("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                     "clientInfo": {"name": "toollib-import", "version": "1"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")

    def call_raw(self, method, params):
        self.n += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}) + "\n")
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("mcp server closed")
            msg = json.loads(line)
            if msg.get("id") == self.n:
                return msg

    def tool(self, name, args):
        r = self.call_raw("tools/call", {"name": name, "arguments": args})
        res = r.get("result", {})
        text = " ".join(c.get("text", "") for c in res.get("content", []))
        return bool(res.get("isError")) or "error" in r, text or json.dumps(r.get("error"))

    def close(self):
        self.p.stdin.close()
        self.p.wait(timeout=30)


def import_file(cli, path):
    m = Mcp(cli)
    err, text = m.tool("import_tool_library", {"path": path})
    job = None
    if not err:
        _, job = m.tool("get_job", {})
    m.close()
    return err, text, job


def main():
    cli, files = sys.argv[1], sys.argv[2:]
    results = {}
    for f in files:
        f = os.path.abspath(f)
        err, text, job = import_file(cli, f)
        entry = {"ok": not err, "message": text, "refused_tools": []}
        if job:
            try:
                entry["tools_in_document"] = len(json.loads(job).get("tools", []))
            except Exception:  # noqa: BLE001
                entry["tools_in_document"] = None
        if err:
            # Per-tool: import each tool alone to list every refusal.
            lib = json.load(open(f))
            with tempfile.TemporaryDirectory() as d:
                for t in lib["tools"]:
                    one = os.path.join(d, "one.camtools")
                    json.dump(dict(lib, tools=[t]), open(one, "w"))
                    e1, t1, _ = import_file(cli, one)
                    if e1:
                        entry["refused_tools"].append({"name": t["name"], "message": t1})
        results[os.path.basename(f)] = entry
        print(os.path.basename(f), "OK" if not err else "REFUSED", text[:300])
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "import-results.json")
    json.dump(results, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
