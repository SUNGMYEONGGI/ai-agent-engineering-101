#!/usr/bin/env python3
"""Local OpenAI-compatible shim between the Round 4 kit and the OpenAI API.

Why: the kit (scripts/round4/agent_kit.py, read-only) sends `max_tokens`, which OpenAI's reasoning models
(gpt-5.4 and later, including gpt-6.1-sol) reject with 400 "use max_completion_tokens instead". The kit lets
agent.json point llm.base anywhere, so this shim sits on 127.0.0.1 and:
  - renames max_tokens to max_completion_tokens, raised to SHIM_MAX_COMPLETION (reasoning tokens count against it;
    the kit's 4000 would often leave no room for the answer),
  - adds reasoning_effort from AGENT_REASONING_EFFORT when set,
  - forwards to OPENAI_BASE_URL with OPENAI_API_KEY,
  - appends token usage (never message content) to logs/llm-shim.jsonl.

    set -a; . submissions/26510358/.env; set +a
    python submissions/26510358/round-4/ops/llm_shim.py --port 18790

Stdlib only. Listens on 127.0.0.1 only.
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USAGE_LOG = ROOT / "logs" / "llm-shim.jsonl"


def rewrite(body):
    """The request the kit sent, made acceptable to a reasoning model."""
    body = dict(body)
    asked = body.pop("max_tokens", None)
    floor = int(os.environ.get("SHIM_MAX_COMPLETION", "16000"))
    body["max_completion_tokens"] = max(int(asked or 0), floor)
    effort = os.environ.get("AGENT_REASONING_EFFORT")
    if effort and "reasoning_effort" not in body:
        body["reasoning_effort"] = effort
    return body


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not self.path.rstrip("/").endswith("/chat/completions"):
            return self.send_error(404)
        raw = self.rfile.read(int(self.headers.get("content-length") or 0))
        try:
            body = rewrite(json.loads(raw))
        except (ValueError, TypeError) as e:
            return self.send_error(400, f"bad json: {e}")
        base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        req = urllib.request.Request(base + "/chat/completions", data=json.dumps(body).encode(),
                                     headers={"authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                                              "content-type": "application/json"})
        t = time.time()
        try:
            with urllib.request.urlopen(req, timeout=175) as r:
                status, out = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, out = e.code, e.read()
        except Exception as e:  # network trouble: let the kit retry
            status, out = 502, json.dumps({"error": {"message": f"{type(e).__name__}: {e}"}}).encode()
        try:
            usage = json.loads(out).get("usage") if status == 200 else None
        except ValueError:
            usage = None
        USAGE_LOG.parent.mkdir(exist_ok=True)
        with open(USAGE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": int(time.time()), "model": body.get("model"), "status": status,
                                "seconds": round(time.time() - t, 1), "usage": usage}) + "\n")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", type=int, default=18790)
    a = ap.parse_args()
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("[shim] OPENAI_API_KEY is not set; load submissions/26510358/.env first")
    print(f"[shim] http://127.0.0.1:{a.port}/v1 -> {os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')}",
          flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
