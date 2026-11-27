#!/usr/bin/env python3
"""Harness checks the model cannot skip: measured by code every 5 minutes (ops/owner_desk.py tick) and written to
harness_check.json, which the agent reads at REVIEW (recall) and the owner's app shows.

Why (11-27): the agent's own "tool fails" count stayed 0 while a2a_handler called eggs we held missing, sent
checkouts for units sold minutes before, and grew into a 34-version exec chain. These checks look at what customers
got, not at whether code raised.

  replies      last 2 h of customers.jsonl: inquiries, replies with no checkout, empty "상품명을 알려" replies,
               checkouts naming a unit the ledger shows sold or expired before the reply
  tools        exec/.deprecated chains, kit.pay outside pay_guard, forges per tool in 24 h
  memory       notes.md size (the prompt shows only its last 3,000 characters)
  restock      what customers asked for and we lacked (wanted.jsonl, 24 h) against the market: settles and median
               price (12 h ledger), wholesale unit cost paid by shops, our net margin after fees, our expiries
"""
import json
import re
import statistics
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

R = Path(__file__).resolve().parent.parent
MARKET = "https://market.ourolabs.ai"
SHOP_URL = "https://shop.hermes-market.shop"
SHOP_NAME = "Hermes Shop"


def lines(p):
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue
    except OSError:
        return


def get(path):
    with urllib.request.urlopen(MARKET + path, timeout=15) as r:
        return json.loads(r.read())


def ledger_since(seconds, now):
    """Ledger entries of the last `seconds`, paged forward (one call returns at most 500)."""
    last = get("/api/ledger?after=-1")
    seq = (last[-1]["seq"] if last else 0) - 7000
    out = []
    for _ in range(30):
        page = get(f"/api/ledger?after={max(seq, 0)}")
        if not page:
            break
        out += [e for e in page if now - e.get("ts", 0) <= seconds]
        seq = page[-1]["seq"]
        if len(page) < 50:
            break
    return out


def jwt_body(tok):
    import base64
    try:
        b = tok.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)))
    except (IndexError, ValueError, AttributeError):
        return {}


def stocked_names(catalog):
    """Names of goods we hold now (GET /api/shops stock x catalog names)."""
    try:
        me = next(x for x in get("/api/shops")["shops"] if x.get("name") == SHOP_NAME)
    except (StopIteration, KeyError, OSError, ValueError):
        return []
    names = {x["sku"]: x.get("name", "") for x in catalog}
    return [names.get(s, "") for s, n in (me.get("stock") or {}).items() if n]


MISSING = re.compile(r"([가-힣A-Za-z0-9]{1,12})(?:\s*[ABC]등급)?(?:은\(는\)|은|는)?\s*없습니다")


def replies(now, ledger, held=()):
    gone = {}
    for e in ledger:
        d = e.get("data") or {}
        if e.get("kind") == "settle" and d.get("shop") == SHOP_URL and d.get("unit"):
            gone[d["unit"]] = e["ts"]
        if e.get("kind") == "expire" and d.get("shop") == SHOP_NAME:
            for u in d.get("units") or []:
                gone[u] = e["ts"]
    c, stale = Counter(), []
    for r in lines(R / "customers.jsonl"):
        t = r.get("at") or r.get("ts") or 0
        if now - t > 7200:
            continue
        rep = r.get("reply") if isinstance(r.get("reply"), dict) else {}
        text = str(rep.get("reply") or r.get("you") or "")
        cos = ((rep.get("data") or {}).get("checkouts") or []) if isinstance(rep.get("data"), dict) else []
        c["inquiries"] += 1
        c["no_checkout"] += not cos
        c["empty_reply"] += "원하시는 상품명" in text
        for m in MISSING.finditer(text):
            k = m.group(1)
            if len(k) >= 2 and any(k in n for n in held):
                c["said_missing_but_stocked"] += 1
                stale.append({"at": time.strftime("%H:%M", time.localtime(t)), "said_missing": k})
        for co in cos:
            u = jwt_body(co.get("checkout_jwt", "")).get("unit") if isinstance(co, dict) else None
            if not (isinstance(co, dict) and co.get("checkout_jwt")):
                c["unsigned_checkout"] += 1
            if u in gone and gone[u] < t:
                stale.append({"at": time.strftime("%H:%M", time.localtime(t)), "unit": u})
    c["checkout_for_gone_unit"] = sum(1 for x in stale if "unit" in x)
    return {**c, "examples": stale[-3:]}


def tools(now):
    out = {"chains": [], "pay_outside_guard": [], "forges_24h": {}}
    for d in sorted((R / "tools").glob("*/logic.py")):
        src = d.read_text(encoding="utf-8", errors="replace")
        name = d.parent.name
        if re.search(r"\bexec\(|\.deprecated", src):
            out["chains"].append(name)
        if name != "pay_guard" and re.search(r"kit\.pay\(", src):
            out["pay_outside_guard"].append(name)
    n = Counter(r.get("tool") for r in lines(R / "logs" / "forge.jsonl") if now - (r.get("ts") or 0) <= 86400)
    out["forges_24h"] = dict(n.most_common(6))
    return out


KEYS = ["계란", "두부", "취나물", "시금치", "김치", "우유", "콩나물", "쌀", "돼지고기", "삼겹살", "고등어", "커피", "생수", "과일", "빵"]


def restock(now, ledger, catalog):
    asks = Counter()
    for r in lines(R / "wanted.jsonl"):
        if now - float(r.get("ts") or 0) <= 86400:
            item = str(r.get("item") or "")
            k = next((k for k in KEYS if k in item or (k == "계란" and ("달걀" in item or "유정란" in item))), None)
            asks[k or item[:12]] += 1
    names = {x["sku"]: x.get("name", "") for x in catalog}
    price, cost, ours_exp = defaultdict(list), defaultdict(list), Counter()
    for e in ledger:
        d = e.get("data") or {}
        n = d.get("name") or names.get(d.get("sku"), "")
        k = next((k for k in KEYS if k in n), None)
        if e.get("kind") == "settle" and k and d.get("grade") == "B" and now - e["ts"] <= 43200:
            price[k].append(d.get("amount") or 0)
        if e.get("kind") == "supply" and d.get("qty"):
            k = next((k for k in KEYS if k in names.get(d.get("sku"), "")), None)
            if k:
                cost[k].append(d["total"] / d["qty"])
        if e.get("kind") == "expire" and d.get("shop") == SHOP_NAME and now - e["ts"] <= 86400:
            for s in d.get("skus") or []:
                k = next((k for k in KEYS if k in names.get(s, "")), None)
                ours_exp[k or s] += 1
    rows = []
    for k, n in asks.most_common(8):
        p = int(statistics.median(price[k])) if price.get(k) else None
        c = int(statistics.median(cost[k])) if cost.get(k) else None
        net = p - p // 100 - 210 - c if p and c else None
        if net is None or len(price.get(k, [])) < 5:
            verdict = "시세 표본이 적음(5건 미만): 1~2개 시험 매입"
        elif net < 150:
            verdict = "이윤이 얇음: 문의가 올 때만 1개"
        elif ours_exp.get(k):
            verdict = "이윤은 있지만 폐기 이력: 하루 안에 팔 만큼(2~3개)"
        else:
            verdict = "매입 우선: 공급창마다 4~5개"
        rows.append({"item": k, "asks_24h": n, "market_b_settles_12h": len(price.get(k, [])), "median_b": p,
                     "unit_cost": c, "net_margin": net, "our_expired_24h": ours_exp.get(k, 0), "verdict": verdict})
    return rows


def memory():
    try:
        n = len((R / "notes.md").read_text(encoding="utf-8"))
    except OSError:
        n = 0
    return {"notes_chars": n, "over_3000": n > 3000}


def run(now=None, ledger=None, catalog=None):
    now = now or time.time()
    ledger = ledger if ledger is not None else ledger_since(86400, now)
    catalog = catalog if catalog is not None else get("/api/catalog")
    held = stocked_names(catalog) if catalog else []
    out = {"at": time.strftime("%F %H:%M", time.localtime(now)), "replies": replies(now, ledger, held),
           "tools": tools(now), "memory": memory(), "restock": restock(now, ledger, catalog)}
    p = out["replies"]
    out["problems"] = [x for x in [
        p.get("checkout_for_gone_unit") and f"팔렸거나 상한 상품으로 결제서 {p['checkout_for_gone_unit']}건",
        p.get("unsigned_checkout") and f"서명 없는 결제서 {p['unsigned_checkout']}건",
        p.get("empty_reply") and f"빈 답('상품명을 알려 주세요') {p['empty_reply']}건",
        p.get("said_missing_but_stocked") and f"가진 상품을 없다고 답함 {p['said_missing_but_stocked']}건",
        out["tools"]["chains"] and "도구가 이전 버전을 불러 씀: " + ", ".join(out["tools"]["chains"]),
        out["tools"]["pay_outside_guard"] and "pay_guard 밖 송금 코드: " + ", ".join(out["tools"]["pay_outside_guard"]),
        out["memory"]["over_3000"] and f"notes.md {out['memory']['notes_chars']}자 (3,000자 넘으면 앞부분이 잘림)",
    ] if x]
    return out


def write(now=None):
    out = run(now)
    tmp = R / "harness_check.json.tmp"
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(R / "harness_check.json")
    return out


if __name__ == "__main__":
    print(json.dumps(write() if sys.argv[1:] != ["--dry"] else run(), ensure_ascii=False, indent=1))
