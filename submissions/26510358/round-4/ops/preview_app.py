#!/usr/bin/env python3
"""Preview the mini app before Round 4 opens, without the market and without the LLM.

`agent_kit.py run` exits until the market serves its Round 4 directory card, so the app cannot be seen through the
kit before 11-24 19:00 KST. This serves the kit's own miniapp.app() (same routes, miniapp.js, MeshKit tools and
consent sheet) with a stub agent in place of the ReAct loop:

  - a chat message is answered with the list of tools the app gave the agent,
  - "/tool <name> {json args}" calls that tool exactly as the agent would (app_* tools run in the page,
    mesh_* tools wait for the consent sheet, then return the verified receipt).

    ~/.venvs/round4/bin/python submissions/26510358/round-4/ops/preview_app.py --port 18800
    ... --tunnel        a public https link for a phone, gated by the same access code as the kit (.kit/app.key)

Development only: the real agent runs with `agent_kit.py run ... --app 8800`.
"""
import argparse
import json
import socket
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent                      # submissions/26510358/round-4
KIT = ROOT.parents[2] / "scripts" / "round4"
sys.path.insert(0, str(KIT))

import market_kit as mk  # noqa: E402
import miniapp  # noqa: E402  (the kit's module, unchanged)
from agent_kit import Event, serve  # noqa: E402


class StubMind:
    def __init__(self):
        self.app_tools = {}

    def deliver(self, ev):
        threading.Thread(target=self.answer, args=(ev,), daemon=True).start()
        return ev

    def answer(self, ev):
        text = ev.text.strip()
        if text.startswith("/tool "):
            name, _, raw = text[6:].strip().partition(" ")
            try:
                args = json.loads(raw) if raw.strip() else {}
            except ValueError as e:
                out = f"bad json args: {e}"
            else:
                tool = self.app_tools.get(name)
                out = tool[1](args) if tool else f"no tool {name!r}"
            reply = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, default=str)
        else:
            reply = ("(미리보기: 실제 에이전트가 아닙니다) 앱이 준 도구: "
                     + (", ".join(self.app_tools) or "없음") + "\n'/tool <이름> {json}'으로 호출해 볼 수 있습니다.")
        ev.answer = {"reply": reply[:4000], "state": "completed"}
        ev.done.set()


class StubToolbox:
    tools = {}


def free_port(start, tries=50):
    """The first port from `start` that nothing listens on. serve() binds in a background thread, so a busy port
    used to print the link, log "address already in use" and then hang (11-25: VS Code forwarded 18800 to the Mac)."""
    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    sys.exit(f"[preview] ports {start}-{start + tries - 1} are all taken; pass --port <another>")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", type=int, default=18800, help="first port to try; the next free one is used if taken")
    ap.add_argument("--name", default="myeonggi")
    ap.add_argument("--tunnel", action="store_true", help="also a public https link (needs the access code)")
    a = ap.parse_args()
    port = free_port(a.port)
    if port != a.port:
        print(f"[preview] port {a.port} is taken (lsof -nP -iTCP:{a.port} -sTCP:LISTEN shows by whom); using {port}",
              flush=True)
    a.port = port
    key = miniapp.access_key(ROOT) if a.tunnel else None
    web = miniapp.app(ROOT, StubMind(), StubToolbox(), Event, name=a.name, key=key)
    serve(web, a.port)
    print(f"[preview] http://127.0.0.1:{a.port}/" + (f"?k={key}" if key else "") + "  (Ctrl-C to stop)", flush=True)
    if a.tunnel:
        _proc, url = mk.open_tunnel(a.port)
        print(f"[preview] open {url}/?k={key}", flush=True)
    threading.Event().wait()


if __name__ == "__main__":
    main()
