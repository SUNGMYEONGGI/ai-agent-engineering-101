#!/usr/bin/env python3
"""Local OpenAI-compatible shim between the Round 4 kit and the OpenAI API.

Why: the kit (scripts/round4/agent_kit.py, read-only) sends `max_tokens`, which OpenAI's reasoning models
(gpt-5.4 and later, including gpt-6.1-sol) reject with 400 "use max_completion_tokens instead". The kit lets
agent.json point llm.base anywhere, so this shim sits on 127.0.0.1 and:
  - renames max_tokens to max_completion_tokens, raised to SHIM_MAX_COMPLETION (reasoning tokens count against it;
    the kit's 4000 would often leave no room for the answer),
  - adds reasoning_effort from AGENT_REASONING_EFFORT when set,
  - forwards to OPENAI_BASE_URL with OPENAI_API_KEY,
  - appends token usage (never message content) to logs/llm-shim.jsonl,
  - stops spending at the owner's daily_tokens (owner_limits.json, set in the app) or SHIM_DAILY_TOKENS total tokens per local day (default 15,000,000, a safety net above the ~6-8M a day expected after the 11-26 sleep rules; 0 = no cap): past the cap it
    answers the kit itself with a sleep move (no API call), so the agent rests until the next day instead of
    retrying. Customers are still answered by the a2a_handler tool, which needs no model.
  - FORGE ESCALATION (11-27): when the answer's move is forge_tool (the agent writing a tool's code and test, ~3% of
    steps but the ones that break sales when wrong), the same request goes again to SHIM_FORGE_MODEL (default
    gpt-6.2-sol, reasoning SHIM_FORGE_EFFORT, default medium) and that answer is returned instead. The kit gives up on
    a socket silent for 60 s, so the second call gets what is left of SHIM_FORGE_DEADLINE (55 s); if it fails or runs
    out, the first answer stands. SHIM_FORGE_MODEL= (empty) turns this off.
  - DECISIONS (11-27): POST /v1/decisions is passed to OpenAI's Decisions API with the key added here, so a forged
    tool can ask typed questions (choice/predicate/score) on 127.0.0.1:18790 without ever holding the key. The model
    defaults to SHIM_DECISIONS_MODEL (gpt-6-luna). Usage is logged like the rest and counts toward the daily cap.

SHIM_BACKEND=claude (run_server.sh LLM=claude) answers with Claude Code's CLI instead: `claude -p --model
$CLAUDE_MODEL --effort $CLAUDE_EFFORT` (default claude-opus-5-5, medium) on the server's claude.ai login, no
tools, no MCP, no settings, no CLAUDE.md. The kit only sends system/user/assistant text and parses one JSON
action from the answer, so the transcript goes in as tagged turns. If the CLI fails or runs past
CLAUDE_TIMEOUT (110 s), the same request goes to OpenAI as above, so the shop keeps moving.

    set -a; . submissions/26510358/.env; set +a
    python submissions/26510358/round-4/ops/llm_shim.py --port 18790

Stdlib only. Listens on 127.0.0.1 only.
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
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


CLAUDE_CWD = Path(tempfile.gettempdir()) / "round4-claude-shim"   # empty: no CLAUDE.md or project settings
LAST_CLAUDE_ERROR = {"why": ""}                                       # logged with the fallback answer


def claude_complete(body):
    """(status, OpenAI-shaped bytes, usage) from one `claude -p` call, or None to fall back to OpenAI."""
    exe = os.environ.get("CLAUDE_BIN") or shutil.which("claude") or str(Path.home() / ".local/bin/claude")
    system = "\n\n".join(m.get("content") or "" for m in body.get("messages", []) if m.get("role") == "system")
    turns = [m for m in body.get("messages", []) if m.get("role") != "system"]
    prompt = "\n\n".join(f'<turn role="{m.get("role")}">\n{m.get("content") or ""}\n</turn>' for m in turns)
    prompt += "\n\nWrite the next assistant turn only (no <turn> tag)."
    CLAUDE_CWD.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", dir=CLAUDE_CWD, delete=False, encoding="utf-8") as f:
        f.write(system or "You are a helpful agent.")
        sysfile = f.name
    cmd = [exe, "-p", "--model", os.environ.get("CLAUDE_MODEL", "claude-opus-5-5"),
           "--effort", os.environ.get("CLAUDE_EFFORT", "medium"), "--output-format", "json",
           "--no-session-persistence", "--tools", "", "--strict-mcp-config", "--setting-sources", "",
           "--disable-slash-commands", "--system-prompt-file", sysfile]
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDECODE", "CLAUDE_CODE_", "ANTHROPIC_"))}
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=CLAUDE_CWD, env=env,
                           timeout=float(os.environ.get("CLAUDE_TIMEOUT", "110")))
        d = json.loads(r.stdout)
    except (subprocess.TimeoutExpired, ValueError, OSError) as e:
        LAST_CLAUDE_ERROR["why"] = (f"{type(e).__name__}: {e}"[:120] + " | " + (locals().get("r") and r.stderr or "")[-200:]).strip()
        return None
    finally:
        os.unlink(sysfile)
    if d.get("is_error") or not d.get("result"):
        LAST_CLAUDE_ERROR["why"] = f"is_error {d.get('subtype', '')}: {str(d.get('result', ''))[:200]}"
        return None
    u = d.get("usage") or {}
    usage = {"prompt_tokens": (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
             + (u.get("cache_creation_input_tokens") or 0), "completion_tokens": u.get("output_tokens") or 0,
             "cache_read": u.get("cache_read_input_tokens") or 0, "cost_usd": d.get("total_cost_usd")}
    out = {"object": "chat.completion", "model": cmd[3], "usage": usage,
           "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": d["result"]}}]}
    return 200, json.dumps(out).encode(), usage


def tokens_today():
    """Total tokens logged today (local date), read once at start; do_POST keeps it current."""
    day, n = time.strftime("%F"), 0
    try:
        for line in open(USAGE_LOG, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if time.strftime("%F", time.localtime(r.get("ts", 0))) == day:
                n += (r.get("usage") or {}).get("total_tokens") or 0
    except OSError:
        pass
    return {"day": day, "tokens": n}


SPENT = tokens_today()


def daily_cap():
    """The owner's cap from the app (owner_limits.json, written by ops/owner_desk.py), read on every call so a change
    needs no restart; SHIM_DAILY_TOKENS when the owner has not set one."""
    try:
        return int(json.loads((ROOT / "owner_limits.json").read_text(encoding="utf-8"))["daily_tokens"])
    except (OSError, ValueError, KeyError, TypeError):
        return int(os.environ.get("SHIM_DAILY_TOKENS", "15000000"))


def over_budget():
    cap = daily_cap()
    if SPENT["day"] != time.strftime("%F"):
        SPENT.update(day=time.strftime("%F"), tokens=0)
    return cap > 0 and SPENT["tokens"] >= cap


def budget_sleep():
    """An OpenAI-shaped answer holding the kit's sleep move, used past the daily cap."""
    move = {"thought": "The owner's daily model budget is used up; customers are still served by a2a_handler.",
            "action": "sleep", "args": {"seconds": 3600, "why": "daily model budget reached (SHIM_DAILY_TOKENS)"}}
    out = {"object": "chat.completion", "model": "shim-budget", "usage": None,
           "choices": [{"index": 0, "finish_reason": "stop",
                        "message": {"role": "assistant", "content": json.dumps(move, ensure_ascii=False)}}]}
    return json.dumps(out).encode()


def openai_post(path, body, timeout):
    """(status, bytes) from OPENAI_BASE_URL + path with the key; never raises."""
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(),
                                 headers={"authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                                          "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=max(1.0, timeout)) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # network trouble or our own deadline
        return 502, json.dumps({"error": {"message": f"{type(e).__name__}: {e}"}}).encode()


def move_action(out):
    """The action named by the first JSON object in a chat completion's answer (like the kit's parse), or None."""
    try:
        text = json.loads(out)["choices"][0]["message"].get("content") or ""
    except (ValueError, KeyError, IndexError, TypeError):
        return None
    dec, i = json.JSONDecoder(), text.find("{")
    while i >= 0:
        try:
            obj, _ = dec.raw_decode(text, i)
            if isinstance(obj, dict) and "action" in obj:
                return str(obj["action"])
        except ValueError:
            pass
        i = text.find("{", i + 1)
    return None


def usage_of(status, out):
    try:
        return json.loads(out).get("usage") if status == 200 else None
    except (ValueError, AttributeError):
        return None


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.rstrip("/").endswith("/decisions"):
            return self.decisions()
        if not self.path.rstrip("/").endswith("/chat/completions"):
            return self.send_error(404)
        raw = self.rfile.read(int(self.headers.get("content-length") or 0))
        try:
            body = rewrite(json.loads(raw))
        except (ValueError, TypeError) as e:
            return self.send_error(400, f"bad json: {e}")
        t = time.time()
        if over_budget():
            self.log_usage("budget-sleep", 200, t, None)
            return self.answer(200, budget_sleep())
        got = claude_complete(body) if os.environ.get("SHIM_BACKEND") == "claude" else None
        if got:
            status, out, usage = got
            self.log_usage(os.environ.get("CLAUDE_MODEL", "claude-opus-5-5"), status, t, usage)
            return self.answer(status, out)
        fell_back = os.environ.get("SHIM_BACKEND") == "claude"
        status, out = openai_post("/chat/completions", body, 60 if fell_back else 175)
        tag = f" (claude fallback: {LAST_CLAUDE_ERROR['why']})" if fell_back else ""
        self.log_usage(body.get("model") + tag, status, t, usage_of(status, out))
        forge_model = os.environ.get("SHIM_FORGE_MODEL", "gpt-6.2-sol")
        if status == 200 and forge_model and forge_model != body.get("model") and move_action(out) == "forge_tool":
            left = float(os.environ.get("SHIM_FORGE_DEADLINE", "55")) - (time.time() - t)
            if left > 8:
                t2 = time.time()
                b2 = dict(body, model=forge_model, reasoning_effort=os.environ.get("SHIM_FORGE_EFFORT", "medium"))
                s2, o2 = openai_post("/chat/completions", b2, left)
                ok = s2 == 200 and move_action(o2) is not None
                self.log_usage(f"{forge_model} (forge{'' if ok else ' failed, first answer kept'})", s2, t2, usage_of(s2, o2))
                if ok:
                    status, out = s2, o2
        self.answer(status, out)

    def decisions(self):
        raw = self.rfile.read(int(self.headers.get("content-length") or 0))
        try:
            body = json.loads(raw)
            assert isinstance(body, dict)
        except (ValueError, AssertionError):
            return self.send_error(400, "bad json")
        t = time.time()
        if over_budget():
            return self.answer(429, json.dumps({"error": {"message": "daily model budget reached"}}).encode())
        body.setdefault("model", os.environ.get("SHIM_DECISIONS_MODEL", "gpt-6-luna"))
        status, out = openai_post("/decisions", body, 30)
        self.log_usage(body["model"] + " (decisions)", status, t, usage_of(status, out))
        self.answer(status, out)

    def log_usage(self, model, status, t, usage):
        SPENT["tokens"] += (usage or {}).get("total_tokens") or 0
        USAGE_LOG.parent.mkdir(exist_ok=True)
        with open(USAGE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": int(time.time()), "model": model, "status": status,
                                "seconds": round(time.time() - t, 1), "usage": usage}) + "\n")

    def answer(self, status, out):
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
    to = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    if os.environ.get("SHIM_BACKEND") == "claude":
        to = (f"claude -p {os.environ.get('CLAUDE_MODEL', 'claude-opus-5-5')} "
              f"effort {os.environ.get('CLAUDE_EFFORT', 'medium')}, fallback {to}")
    print(f"[shim] http://127.0.0.1:{a.port}/v1 -> {to}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
