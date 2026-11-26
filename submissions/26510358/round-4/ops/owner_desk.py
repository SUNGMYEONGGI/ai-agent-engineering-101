"""Owner desk: the numbers the owner's app shows, and the two things the owner may change, served at /owner/*.

The kit's mini app (scripts/round4/miniapp.py, read-only) serves only app/ and its own /api/*, and keeps nothing the
owner sets on the server. This small server sits next to it on 127.0.0.1:8801; the named tunnel sends
app.hermes-market.shop/owner/* here (path rule in ~/.cloudflared/hermes-shop.yml), so the page and the iOS app reach it
on the same origin with the same access cookie (miniapp_access = .kit/app.key).

  GET  /owner/dash    funnel, experiments, winners, tokens, losses, limits, alerts (JSON)
  POST /owner/limits  {max_loss_per_day, max_pay_per_call, max_pay_per_day, daily_tokens, note} -> owner_limits.json
  POST /owner/veto    {exp, action: stop|revert} -> owner_vetoes.jsonl (the app also tells the agent in the chat)

Sources (all written by the agent through its memory tool, formats fixed in agent.json's goal):
  notes.md   FUNNEL <YYYY-MM-DD HH:MM> m=<n> i=<n> c=<n> s=<n> today=<n>   (last one wins)
             EXP <YYYY-MM-DD HH:MM> stage=.. diff=.. change=.. judge=<HH:MM> result=..
             WIN <shop>|<card start>|<units>|<lines>|<price gap %>       (top 3 shops, then one line for "우리")
             LOSS <YYYY-MM-DD HH:MM> <sku> <credits>
             LEARNED <date> <lever> -> <effect>   (in RULES; lessons an experiment proved)
             WANTED <items>                       (fallback when wanted.jsonl is missing)
  wanted.jsonl  {ts, item, buyer}: goods customers asked for that we lacked (written by a2a_handler)
  market     GET /api/board (our rank) and /api/forum?role=shop (posts per shop, last hour), every 5 min in tick()
  logs/llm-shim.jsonl  token usage per model call (the shim reads owner_limits.json's daily_tokens as its cap)
"""
import json
import os
import re
import secrets
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

R = Path(os.environ.get("DESK_ROOT") or Path(__file__).resolve().parent.parent)   # round-4; DESK_ROOT for a preview
PORT = int(os.environ.get("DESK_PORT", "8801"))
DEFAULT_LIMITS = {"max_loss_per_day": 30000, "max_pay_per_call": 20000, "max_pay_per_day": 200000,
                  "daily_tokens": 15_000_000, "note": "", "set_at": ""}
BOUNDS = {"max_loss_per_day": (0, 200_000), "max_pay_per_call": (0, 100_000), "max_pay_per_day": (0, 1_000_000),
          "daily_tokens": (0, 50_000_000)}
STAGES = [("m", "시장 정산"), ("i", "문의"), ("c", "결제서"), ("s", "정산")]
STUCK_ALERT_S = 2 * 3600

FUNNEL = re.compile(r"FUNNEL (\d{4}-\d\d-\d\d \d\d:\d\d) m=(\d+) i=(\d+) c=(\d+) s=(\d+)(?: today=(\d+))?")
REVIEW_FUNNEL = re.compile(r"REVIEW (\d{4}-\d\d-\d\d \d\d:\d\d).*?funnel=(\d+)/(\d+)/(\d+)/(\d+)")
EXP = re.compile(r"^EXP (\d{4}-\d\d-\d\d \d\d:\d\d) (.*)$", re.M)
EXP_KEYS = re.compile(r"(stage|diff|change|judge|result)=(.*?)(?=\s+(?:stage|diff|change|judge|result)=|$)")
WIN = re.compile(r"^WIN (.+)$", re.M)
LOSS = re.compile(r"LOSS (\d{4}-\d\d-\d\d) \d\d:\d\d \S+ (\d+)")
LEARNED = re.compile(r"^.*?LEARNED (.+)$", re.M)
WANTED_LINE = re.compile(r"^WANTED (.+)$", re.M)
MARKET = os.environ.get("MARKET", "https://market.ourolabs.ai").rstrip("/")
SHOP_NAME = os.environ.get("NAME", "Hermes Shop")


def read(p, default=""):
    try:
        return (R / p).read_text(encoding="utf-8")
    except OSError:
        return default


def limits():
    try:
        saved = json.loads(read("owner_limits.json", "{}"))
    except ValueError:
        saved = {}
    return {k: saved.get(k, v) for k, v in DEFAULT_LIMITS.items()}


def clean_limits(body):
    """Owner input at a trust boundary: whole numbers inside BOUNDS, a short note. Raises ValueError."""
    out = limits()
    for k, (lo, hi) in BOUNDS.items():
        if k in body:
            v = int(body[k])
            if not lo <= v <= hi:
                raise ValueError(f"{k} must be {lo}..{hi}")
            out[k] = v
    if "note" in body:
        out["note"] = str(body["note"]).strip()[:500]
    out["set_at"] = time.strftime("%Y-%m-%d %H:%M")
    return out


def parse_funnel(notes):
    found = list(FUNNEL.finditer(notes))
    if found:
        at, m, i, c, s, today = found[-1].groups()
        return {"at": at, "m": int(m), "i": int(i), "c": int(c), "s": int(s),
                "today": int(today) if today is not None else None}
    found = list(REVIEW_FUNNEL.finditer(notes))
    if found:
        at, m, i, c, s = found[-1].groups()
        return {"at": at, "m": int(m), "i": int(i), "c": int(c), "s": int(s), "today": None}
    return None


def blocked_stage(f):
    """The first stage that is 0 while the one before it is not: the funnel's problem (agent.json goal, FUNNEL)."""
    if not f:
        return None
    for (prev, _), (key, _) in zip(STAGES, STAGES[1:]):
        if f[prev] > 0 and f[key] == 0:
            return key
    return None


def parse_experiments(notes, vetoes):
    out = []
    for at, rest in EXP.findall(notes):
        e = {"at": at, **{k: v.strip() for k, v in EXP_KEYS.findall(rest)}}
        res = e.get("result", "")
        e["state"] = "kept" if "kept" in res else "reverted" if "reverted" in res else "open"
        if at in vetoes:
            e["veto"] = vetoes[at]
        out.append(e)
    return out[-4:]


def parse_winners(notes):
    rows = []
    for line in WIN.findall(notes)[-4:]:
        p = [x.strip() for x in line.split("|")]
        if len(p) >= 5:
            rows.append({"shop": p[0], "card": p[1][:80], "units": p[2], "lines": p[3], "gap": p[4]})
    return rows


def parse_learned(notes):
    return [x.strip() for x in LEARNED.findall(notes)][-6:]


def wanted(now, notes):
    """Top 5 goods customers asked for in the last 24 h that we lacked: wanted.jsonl, else the agent's WANTED line."""
    n = {}
    for line in read("wanted.jsonl").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r, dict) and now - float(r.get("ts") or 0) <= 86400 and str(r.get("item") or "").strip():
            k = str(r["item"]).strip()[:40]
            n[k] = n.get(k, 0) + 1
    if n:
        return {"source": "wanted.jsonl", "items": [{"item": k, "n": v} for k, v in sorted(n.items(), key=lambda kv: -kv[1])[:5]]}
    lines = WANTED_LINE.findall(notes)
    return {"source": "notes.md", "items": [{"item": lines[-1].strip()[:200], "n": None}]} if lines else {"source": None, "items": []}


RANKS = R / ".kit" / "desk_rank.json"
_mkt = {"at": 0, "rank": None, "of": None, "forum": None, "error": ""}


def get_json(path):
    import urllib.request
    with urllib.request.urlopen(MARKET + path, timeout=10) as r:
        return json.loads(r.read())


def refresh_market(now=None, board=None, forum=None):
    """Our board rank (with a history of changes) and shop forum posts in the last hour. Network only here."""
    now = now or time.time()
    try:
        board = board if board is not None else get_json("/api/board")
        forum = forum if forum is not None else get_json("/api/forum?role=shop")
    except Exception as e:                                 # the market being slow must not break the desk
        _mkt["error"] = f"{type(e).__name__}: {e}"[:120]
        return _mkt
    shops = board.get("shops", board) if isinstance(board, dict) else board
    ranked = [x for x in shops if isinstance(x, dict) and x.get("rank")]
    me = next((x for x in ranked if x.get("name") == SHOP_NAME), None)
    posts = {}
    for p in forum if isinstance(forum, list) else []:
        if isinstance(p, dict) and now - float(p.get("ts") or 0) <= 3600:
            a = str(p.get("author") or "?")
            posts[a] = posts.get(a, 0) + 1
    top = sorted(posts.items(), key=lambda kv: -kv[1])[:3]
    with _lock:
        try:
            hist = json.loads(RANKS.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            hist = []
        if me and (not hist or hist[-1][1] != me["rank"]):
            hist = (hist + [[int(now), me["rank"]]])[-50:]
            RANKS.parent.mkdir(exist_ok=True)
            RANKS.write_text(json.dumps(hist), encoding="utf-8")
    _mkt.update(at=int(now), rank=me and me["rank"], of=len(ranked), history=hist[-12:], error="",
                forum={"ours": posts.get(SHOP_NAME, 0), "top": [{"shop": k, "n": v} for k, v in top]})
    return _mkt


def loss_today(notes, day):
    return sum(int(n) for d, n in LOSS.findall(notes) if d == day)


_tok = {"key": None, "val": 0}


def tokens_today(day):
    """Total tokens in logs/llm-shim.jsonl for the local day; re-read only when the file changed."""
    f = R / "logs" / "llm-shim.jsonl"
    try:
        st = f.stat()
    except OSError:
        return 0
    key = (day, st.st_mtime, st.st_size)
    if _tok["key"] != key:
        n = 0
        with f.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if time.strftime("%F", time.localtime(r.get("ts", 0))) == day:
                    n += (r.get("usage") or {}).get("total_tokens") or 0
        _tok.update(key=key, val=n)
    return _tok["val"]


def vetoes():
    out = {}
    for line in read("owner_vetoes.jsonl").splitlines():
        try:
            v = json.loads(line)
            out[v["exp"]] = v["action"]
        except (ValueError, KeyError):
            continue
    return out


STATE = R / ".kit" / "desk_state.json"
_lock = threading.Lock()


def track_stuck(stage, now):
    """Remember since when the funnel has been blocked at the same stage (the agent keeps only the last FUNNEL line)."""
    with _lock:
        try:
            st = json.loads(STATE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            st = {}
        if st.get("stage") != stage or "since" not in st:
            st = {"stage": stage, "since": now}
            STATE.parent.mkdir(exist_ok=True)
            STATE.write_text(json.dumps(st), encoding="utf-8")
        return st["since"]


def dash(now=None, notes=None):
    now = now or time.time()
    day = time.strftime("%F", time.localtime(now))
    notes = read("notes.md") if notes is None else notes
    lim = limits()
    f = parse_funnel(notes)
    stage = blocked_stage(f)
    since = track_stuck(stage, now)
    tok, loss = tokens_today(day), loss_today(notes, day)
    settles = f["today"] if f else None
    alerts = []
    if stage and now - since >= STUCK_ALERT_S:
        name = dict(STAGES)[stage]
        alerts.append({"kind": "stuck", "key": f"stuck-{stage}-{int(since)}",
                       "text": f"FUNNEL이 {int((now - since) // 3600)}시간째 '{name}' 단계에서 멈춰 있습니다."})
    if lim["max_loss_per_day"] and loss >= 0.8 * lim["max_loss_per_day"]:
        alerts.append({"kind": "loss", "key": f"loss-{day}",
                       "text": f"오늘 처분 손실 {loss:,} / 한도 {lim['max_loss_per_day']:,} credits (80% 이상)."})
    if lim["daily_tokens"] and tok >= lim["daily_tokens"]:
        alerts.append({"kind": "tokens", "key": f"tokens-{day}",
                       "text": f"오늘 토큰 {tok:,}개로 상한에 닿았습니다. 에이전트는 내일까지 잡니다(손님 응대는 계속)."})
    return {"ts": int(now), "funnel": f and dict(f, blocked=stage, blocked_since=int(since) if stage else None),
            "stages": STAGES, "experiments": parse_experiments(notes, vetoes()), "winners": parse_winners(notes),
            "tokens": {"today": tok, "cap": lim["daily_tokens"],
                       "per_settle": round(tok / settles) if settles else None, "settles_today": settles},
            "loss_today": loss, "limits": lim, "alerts": alerts,
            "learned": parse_learned(notes), "wanted": wanted(now, notes),
            "market": {k: _mkt.get(k) for k in ("at", "rank", "of", "history", "forum", "error")}}


def app_key():
    try:
        return (R / ".kit" / "app.key").read_text(encoding="utf-8").strip()
    except OSError:
        return None


class Handler(BaseHTTPRequestHandler):
    def allowed(self):
        # A plain split: SimpleCookie drops every cookie when one other cookie on the host is malformed.
        key = app_key()
        jar = dict(p.strip().split("=", 1) for p in self.headers.get("Cookie", "").split(";") if "=" in p)
        got = jar.get("miniapp_access", "")
        return bool(key) and secrets.compare_digest(got, key)

    def reply(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.allowed():
            return self.reply(401, {"error": "this app needs its access code"})
        if self.path.split("?")[0] == "/owner/dash":
            return self.reply(200, dash())
        self.reply(404, {"error": "not found"})

    def do_POST(self):
        if not self.allowed():
            return self.reply(401, {"error": "this app needs its access code"})
        try:
            n = int(self.headers.get("content-length") or 0)
            body = json.loads(self.rfile.read(min(n, 4096)) or b"{}")
            if not isinstance(body, dict):
                raise ValueError("body must be an object")
            if self.path == "/owner/limits":
                v = clean_limits(body)
                tmp = R / "owner_limits.json.tmp"
                tmp.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
                tmp.replace(R / "owner_limits.json")
                return self.reply(200, v)
            if self.path == "/owner/veto":
                exp, action = str(body.get("exp", ""))[:20], body.get("action")
                if not re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d", exp) or action not in ("stop", "revert"):
                    raise ValueError("exp must be 'YYYY-MM-DD HH:MM' and action stop or revert")
                with open(R / "owner_vetoes.jsonl", "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"ts": int(time.time()), "exp": exp, "action": action}) + "\n")
                return self.reply(200, {"ok": True, "exp": exp, "action": action})
            self.reply(404, {"error": "not found"})
        except (ValueError, TypeError) as e:
            self.reply(400, {"error": str(e)})

    def log_message(self, fmt, *a):
        pass


def tick():
    """Keep the stuck clock honest while nobody has the app open."""
    while True:
        if time.time() - _mkt["at"] >= 300:
            refresh_market()
        try:
            dash()
        except Exception as e:                            # a bad notes line must not stop the clock
            print(f"[desk] tick: {type(e).__name__}: {e}", flush=True)
        time.sleep(60)


if __name__ == "__main__":
    if sys.argv[1:] == ["--once"]:
        print(json.dumps(dash(), ensure_ascii=False, indent=1))
        sys.exit()
    threading.Thread(target=tick, daemon=True).start()
    print(f"[desk] owner desk on 127.0.0.1:{PORT} for {R}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
