"""Owner desk: the numbers the owner's app shows, and the two things the owner may change, served at /owner/*.

The kit's mini app (scripts/round4/miniapp.py, read-only) serves only app/ and its own /api/*, and keeps nothing the
owner sets on the server. This small server sits next to it on 127.0.0.1:8801; the named tunnel sends
app.hermes-market.shop/owner/* here (path rule in ~/.cloudflared/hermes-shop.yml), so the page and the iOS app reach it
on the same origin with the same access cookie (miniapp_access = .kit/app.key).

  GET  /owner/dash    funnel, experiments, winners, tokens, losses, limits, alerts (JSON)
  POST /owner/limits  {max_loss_per_day, max_pay_per_call, max_pay_per_day, daily_tokens, note} -> owner_limits.json
  POST /owner/veto    {exp, action: stop|revert} -> owner_vetoes.jsonl (the app also tells the agent in the chat)
  GET  /owner/chatlog  the owner chat kept across kit restarts and page reloads (.kit/chatlog.jsonl; the kit keeps
                      only 200 messages in memory and the page's cards live only in the page)
  POST /owner/chatlog  {items: [{who, text, ts, id?, title?}]}: the page sends what it shows; duplicates are dropped
  GET  /owner/activity what the shop did that the owner cares about, newest first: customers' messages, the agent
                      speaking first (app_say) and its cards, experiments, tools it made, the owner's limit changes
  GET  /owner/harness is the harness running: loop, model, customers' A2A, memory, tools, market (each ok/warn/fail),
                      the last ReAct steps, and a timeline of what changed: tools (forge.jsonl), memory (notes.md),
                      skills (card.json), goal (git log of agent.json)

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
import subprocess
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


def count_talks(talks, now):
    """Messages customers' agents sent each shop in the last hour (GET /api/talks: who wrote to whom, no words)."""
    n = {}
    for t in talks if isinstance(talks, list) else []:
        if isinstance(t, dict) and t.get("from_role") == "buyer" and now - float(t.get("ts") or 0) <= 3600:
            n[str(t.get("to"))] = n.get(str(t.get("to")), 0) + 1
    top = sorted(n.items(), key=lambda kv: -kv[1])[:3]
    return {"ours": n.get(SHOP_NAME, 0), "top": [{"shop": k, "n": v} for k, v in top], "shops": len(n)}


def refresh_market(now=None, board=None, forum=None, talks=None):
    """Our board rank (with a history of changes) and shop forum posts in the last hour. Network only here."""
    now = now or time.time()
    board_given = board is not None
    try:
        talks = talks if talks is not None else [] if board_given else get_json("/api/talks")   # given board: a test
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
    _mkt.update(at=int(now), rank=me and me["rank"], of=len(ranked), history=hist[-12:], error="", talks=count_talks(talks, now),
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


def jsonl(name, last=None):
    rows = []
    for line in read(name).splitlines()[-last if last else 0:]:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r, dict):
            rows.append(r)
    return rows


def ago(ts, now):
    if not ts:
        return "기록 없음"
    s = max(0, int(now - ts))
    return f"{s}초 전" if s < 90 else f"{s // 60}분 전" if s < 5400 else f"{s // 3600}시간 전"


def card_lines(text):
    try:
        c = json.loads(text)
    except ValueError:
        return []
    return [f"설명: {str(c.get('description', ''))[:120]}"] + [
        f"스킬: {k.get('name')}: {str(k.get('description', ''))[:80]}" for k in c.get("skills") or [] if isinstance(k, dict)]


SNAPS = {"memory": ("notes.md", lambda t: [x for x in t.splitlines() if x.strip()]), "skill": ("card.json", card_lines)}


def track_changes(now):
    """notes.md (memory) and card.json (skills) keep no history: snapshot both and log the lines that came and went."""
    changes = R / ".kit" / "desk_changes.jsonl"
    with _lock:
        try:
            snap = json.loads((R / ".kit" / "desk_snap.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            snap = {}
        logged = False
        for kind, (name, lines_of) in SNAPS.items():
            new = lines_of(read(name))
            old = snap.get(kind)
            if old is not None and new != old:
                added = [x for x in new if x not in old]
                removed = [x for x in old if x not in new]
                if added or removed:
                    changes.parent.mkdir(exist_ok=True)
                    with changes.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps({"ts": int(now), "kind": kind, "file": name, "added": added[:8],
                                             "removed": removed[:8]}, ensure_ascii=False) + "\n")
                    logged = True
            snap[kind] = new
        (R / ".kit").mkdir(exist_ok=True)
        (R / ".kit" / "desk_snap.json").write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
        if logged and changes.stat().st_size > 2_000_000:                 # ponytail: crude cap, keep the newest half
            lines = changes.read_text(encoding="utf-8").splitlines()
            changes.write_text("\n".join(lines[len(lines) // 2:]) + "\n", encoding="utf-8")


def goal_changes():
    try:
        out = subprocess.run(["git", "log", "-12", "--format=%ct|%h|%s", "--", "agent.json"], cwd=R, capture_output=True,
                             text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    rows = []
    for line in out.splitlines():
        ts, h, subj = (line.split("|", 2) + ["", ""])[:3]
        rows.append({"ts": int(ts or 0), "kind": "goal", "title": f"goal {h}", "added": [subj[:200]], "removed": []})
    return rows


def harness(now=None):
    now = now or time.time()
    lim = limits()
    steps = jsonl("logs/react.jsonl", 400)
    last = steps[-1] if steps else {}
    wake = last.get("ts", 0) + float((last.get("args") or {}).get("seconds") or 0) if last.get("action") == "sleep" else 0
    loop_age = now - last.get("ts", 0)
    hour = [x for x in steps if now - x.get("ts", 0) <= 3600]
    shim = jsonl("logs/llm-shim.jsonl", 60)
    m = shim[-1] if shim else {}
    errs = sum(1 for x in shim if x.get("status") != 200)
    tools = {}
    try:
        tools = json.loads(read("tools/index.json", "{}"))
    except ValueError:
        pass
    forges = jsonl("logs/forge.jsonl")
    cust = jsonl("customers.jsonl")
    notes = read("notes.md")
    day = time.strftime("%F", time.localtime(now))
    tok = tokens_today(day)

    def row(key, name, state, value, detail, meter=None, **extra):
        """One part of the harness: a short value the page shows big, an optional 0..1 meter, the rest on tap."""
        return {"key": key, "name": name, "state": state, "value": value, "detail": detail, "meter": meter, **extra}

    a2a_last = (tools.get("a2a_handler") or {}).get("last", 0)
    ours_hour = sum(1 for c in cust if now - c.get("ts", 0) <= 3600)
    talks = _mkt.get("talks") or {}
    fails = sum((v or {}).get("fails", 0) for v in tools.values())
    lf = forges[-1] if forges else {}
    health = [
        row("loop", "ReAct 루프", "ok" if loop_age < 1500 or now < wake + 300 else "fail",
            "잠자는 중" if wake > now else "깨어 있음",
            f"마지막 행동 {last.get('action', '-')} ({ago(last.get('ts'), now)}), 지난 1시간 {len(hour)}걸음"
            + (f", {int((wake - now) // 60) + 1}분 뒤 깨어남" if wake > now else ""), wake=int(wake) if wake > now else None),
        row("model", "모델", "fail" if not m else "warn" if m.get("status") != 200 or errs >= 10 or tok >= lim["daily_tokens"] else "ok",
            m.get("model", "-"), f"마지막 호출 {ago(m.get('ts'), now)}, 최근 60회 중 오류 {errs}회. 오늘 토큰 {tok:,} / {lim['daily_tokens']:,}",
            min(1, tok / lim["daily_tokens"]) if lim["daily_tokens"] else None),
        row("talks", "손님 대화", "ok" if ours_hour else "warn", f"1시간 {max(talks.get('ours', 0), ours_hour)}건",
            f"손님 에이전트가 A2A로 보낸 메시지. 우리 응답 도구 a2a_handler 마지막 {ago(a2a_last, now)}, 누적 {len(cust)}건. "
            "다른 가게 수는 시장 집계(/api/talks)", bars=[{"shop": "우리", "n": max(talks.get("ours", 0), ours_hour)}] + talks.get("top", [])),
        row("memory", "메모리", "ok" if len(notes) <= 3000 else "warn", f"{len(notes):,}자",
            f"notes.md, 매 실행 프롬프트에 들어가는 마지막 3,000자. 마지막 수정 "
            f"{ago((R / 'notes.md').stat().st_mtime if (R / 'notes.md').exists() else 0, now)}", min(1, len(notes) / 3000)),
        row("tools", "도구", "ok" if not any(not f.get("passed") for f in forges[-3:]) else "warn", f"{len(tools)}개",
            f"실패 누적 {fails}회. 마지막 제작 {lf.get('tool', '-')} v{lf.get('version', '-')}, 테스트 "
            f"{'통과' if lf.get('passed') else '실패'} ({ago(lf.get('ts'), now)})" if lf else f"실패 누적 {fails}회"),
        row("market", "시장 순위", "fail" if _mkt.get("error") else "ok",
            f"{_mkt.get('rank') or '-'}위 / {_mkt.get('of') or '-'}", _mkt.get("error") or f"{ago(_mkt.get('at'), now)} 확인"),
    ]
    changes = [{"ts": f.get("ts", 0), "kind": "tool", "title": f"{f.get('tool')} v{f.get('version')}",
                "added": ["테스트 통과" if f.get("passed") else f"테스트 실패: {str(f.get('error'))[:160]}",
                          "network: " + ", ".join((f.get("permission") or {}).get("network") or [])], "removed": []}
               for f in forges[-30:]]
    changes += [dict(c, title=c.get("file", c["kind"])) for c in jsonl(".kit/desk_changes.jsonl", 60)]
    changes += goal_changes()
    changes.sort(key=lambda c: -c.get("ts", 0))
    return {"ts": int(now), "health": health,
            "pulse": [[int(x.get("ts", 0)), x.get("action")] for x in hour],
            "steps": [{"ts": x.get("ts"), "action": x.get("action"), "thought": str(x.get("thought", ""))[:200],
                       "why": str((x.get("args") or {}).get("why", ""))[:120]} for x in steps[-15:][::-1]],
            "tools": [{"name": k, **(v or {})} for k, v in sorted(tools.items(), key=lambda kv: -(kv[1] or {}).get("uses", 0))],
            "changes": changes[:60]}


CHATLOG_MAX = 3000


def chat_key(m):
    return f"card|{m.get('title')}" if m.get("who") == "card" else f"{m.get('who')}|{int(float(m.get('ts') or 0))}|{str(m.get('text'))[:80]}"


def agent_spoke():
    """What the agent said first (logs/app.jsonl) and the cards it sent (logs/react.jsonl): written by the kit even when
    no page was open, so the chat shows them after a kit restart wiped its memory or a card's page was closed."""
    out = [{"who": "agent", "text": r.get("said_first", ""), "ts": r.get("ts", 0), "first": True}
           for r in jsonl("logs/app.jsonl", 200) if r.get("said_first")]
    for r in jsonl("logs/react.jsonl", 3000):
        a = r.get("args") or {}
        if r.get("action") == "app_show_card" and a.get("title"):
            out.append({"who": "card", "id": "r" + str(int(r.get("ts", 0))), "title": str(a["title"]),
                        "text": str(a.get("body", "")), "ts": r.get("ts", 0)})
    return out


def chatlog(last=300):
    seen, out = set(), []
    for m in sorted(jsonl(".kit/chatlog.jsonl", last) + agent_spoke(), key=lambda m: float(m.get("ts") or 0)):
        k = chat_key(m)
        if k not in seen:
            seen.add(k)
            out.append(m)
    return out[-last:]


def chatlog_add(items):
    """Owner input at a trust boundary: at most 200 small messages, strings only, appended once each."""
    if not isinstance(items, list) or len(items) > 200:
        raise ValueError("items must be a list of at most 200 messages")
    clean = []
    for m in items:
        if not isinstance(m, dict):
            raise ValueError("each item must be an object")
        c = {"who": str(m.get("who", ""))[:40], "text": str(m.get("text", ""))[:4000], "ts": float(m.get("ts") or 0)}
        if c["who"] == "card":
            c.update(id=str(m.get("id", ""))[:20], title=str(m.get("title", ""))[:200])
        clean.append(c)
    f = R / ".kit" / "chatlog.jsonl"
    with _lock:
        seen = {chat_key(m) for m in jsonl(".kit/chatlog.jsonl", CHATLOG_MAX)}
        new = [c for c in clean if chat_key(c) not in seen and not seen.add(chat_key(c))]
        if new:
            f.parent.mkdir(exist_ok=True)
            with f.open("a", encoding="utf-8") as fh:
                fh.writelines(json.dumps(c, ensure_ascii=False) + "\n" for c in new)
            lines = f.read_text(encoding="utf-8").splitlines()
            if len(lines) > CHATLOG_MAX:
                f.write_text("\n".join(lines[-CHATLOG_MAX:]) + "\n", encoding="utf-8")
    return len(new)


def activity(now=None, notes=None):
    now = now or time.time()
    notes = read("notes.md") if notes is None else notes
    ev = []
    for c in jsonl("customers.jsonl", 300):
        rep_ = c.get("reply") or {}
        ev.append({"ts": c.get("at") or c.get("ts") or 0, "kind": "customer", "title": f"{c.get('claimed_from') or '손님'}의 문의",
                   "text": str(c.get("text", ""))[:300], "more": str(rep_.get("reply", "") if isinstance(rep_, dict) else rep_)[:300]})
    for m in agent_spoke():
        ev.append({"ts": m["ts"], "kind": "say" if m["who"] == "agent" else "card",
                   "title": "에이전트가 먼저 말함" if m["who"] == "agent" else m["title"], "text": m["text"][:300]})
    for e in parse_experiments(notes, vetoes()):
        try:
            ts = time.mktime(time.strptime(e["at"], "%Y-%m-%d %H:%M"))
        except ValueError:
            continue
        ev.append({"ts": ts, "kind": "exp", "title": f"실험: {e.get('change', '')[:60]}",
                   "text": f"가설 {e.get('diff', '')}. 판정 {e.get('judge', '')}" + (f", 결과 {e['result']}" if e.get("result") else ""),
                   "state": e["state"]})
    for f in jsonl("logs/forge.jsonl", 100):
        ev.append({"ts": f.get("ts", 0), "kind": "tool", "title": f"도구 {'제작' if f.get('version') == 1 else '개선'}: {f.get('tool')} v{f.get('version')}",
                   "text": "테스트 통과" if f.get("passed") else f"테스트 실패: {str(f.get('error'))[:200]}"})
    lim = limits()
    if lim.get("set_at"):
        try:
            ev.append({"ts": time.mktime(time.strptime(lim["set_at"], "%Y-%m-%d %H:%M")), "kind": "owner", "title": "한도를 바꿈",
                       "text": lim.get("note") or ""})
        except ValueError:
            pass
    ev = [e for e in ev if now - float(e["ts"] or 0) <= 2 * 86400]
    ev.sort(key=lambda e: -float(e["ts"] or 0))
    return {"ts": int(now), "events": ev[:80]}


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
        if self.path.split("?")[0] == "/owner/chatlog":
            return self.reply(200, {"items": chatlog()})
        if self.path.split("?")[0] == "/owner/activity":
            return self.reply(200, activity())
        if self.path.split("?")[0] == "/owner/harness":
            return self.reply(200, harness())
        self.reply(404, {"error": "not found"})

    def do_POST(self):
        if not self.allowed():
            return self.reply(401, {"error": "this app needs its access code"})
        try:
            n = int(self.headers.get("content-length") or 0)
            body = json.loads(self.rfile.read(min(n, 1_000_000)) or b"{}")
            if not isinstance(body, dict):
                raise ValueError("body must be an object")
            if self.path == "/owner/limits":
                v = clean_limits(body)
                tmp = R / "owner_limits.json.tmp"
                tmp.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
                tmp.replace(R / "owner_limits.json")
                return self.reply(200, v)
            if self.path == "/owner/chatlog":
                return self.reply(200, {"added": chatlog_add(body.get("items"))})
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
            track_changes(time.time())
        except Exception as e:                            # a bad notes line must not stop the clock
            print(f"[desk] tick: {type(e).__name__}: {e}", flush=True)
        time.sleep(60)


if __name__ == "__main__":
    if sys.argv[1:] == ["--harness"]:
        track_changes(time.time())
        print(json.dumps(harness(), ensure_ascii=False, indent=1)[:4000])
        sys.exit()
    if sys.argv[1:] == ["--once"]:
        print(json.dumps(dash(), ensure_ascii=False, indent=1))
        sys.exit()
    threading.Thread(target=tick, daemon=True).start()
    print(f"[desk] owner desk on 127.0.0.1:{PORT} for {R}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
