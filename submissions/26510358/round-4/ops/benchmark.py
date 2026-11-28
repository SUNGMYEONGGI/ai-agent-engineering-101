#!/usr/bin/env python3
"""Benchmark of the top shops against ours, computed by code every 30 min (ops/owner_desk.py tick) into benchmark.json.

Why (11-28): the agent's COPY THE WINNERS step compared card text and stock counts only, and its market_call answers
were cut at 2,000 characters. What actually separated the leaders in the 24 h ledger was repeat buyers (ddolcom 51%,
us 11%), holding the market's 15 most sold SKUs (leaders 13-14, us 9) and forum presence (6-8 posts an hour, us 2);
price was not decisive (three leaders sold at +3 to +5% over the median). This file gives the agent those numbers in
one short read, without spending model steps on a 24 h ledger.

  shops     the 5 shops with the most settles in 24 h, then us: settles, buyers, repeat-buyer share, price gap vs the
            median of the same sku and grade, how many of the market's top 15 SKUs they hold now, forum posts an hour,
            share of goods (non-food) sales and average sale price, card description start
  top15     the market's 15 most sold SKUs in 24 h with their median B price and whether we hold them
  gaps      the three biggest differences between us and the leaders' median, in plain words
"""
import json
import statistics
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

R = Path(__file__).resolve().parent.parent
MARKET = "https://market.ourolabs.ai"
SHOP_NAME = "Hermes Shop"


def get(path):
    with urllib.request.urlopen(MARKET + path, timeout=20) as r:
        return json.loads(r.read())


def ledger(seconds, now):
    last = get("/api/ledger?after=-1")
    seq, out = (last[-1]["seq"] if last else 0) - 16000, []
    for _ in range(60):
        page = get(f"/api/ledger?after={max(seq, 0)}")
        if not page:
            break
        out += [e for e in page if now - e.get("ts", 0) <= seconds]
        seq = page[-1]["seq"]
        if len(page) < 50:
            break
    return out


def run(now=None):
    now = now or time.time()
    L = ledger(86400, now)
    shops = get("/api/shops")["shops"]
    byurl = {s["url"]: s for s in shops}
    byname = {s["name"]: s for s in shops}
    board = {s["name"]: s for s in get("/api/board")["shops"]}
    cat = {x["sku"]: x for x in get("/api/catalog")}
    st = [e for e in L if e["kind"] == "settle" and (e.get("data") or {}).get("sku")]
    med = defaultdict(list)
    for e in st:
        med[(e["data"]["sku"], e["data"].get("grade"))].append(e["data"].get("amount") or 0)
    med = {k: statistics.median(v) for k, v in med.items() if len(v) >= 3}
    top15 = [s for s, _ in Counter(e["data"]["sku"] for e in st).most_common(15)]
    per = defaultdict(list)
    for e in st:
        per[byurl.get(e["data"].get("shop"), {}).get("name", e["data"].get("shop"))].append(e)
    try:
        forum = get("/api/forum?role=shop&limit=500")
        span = max(0.25, (forum[0]["ts"] - forum[-1]["ts"]) / 3600)
        posts = Counter(p.get("author") for p in forum)
    except (OSError, ValueError, KeyError, IndexError):
        span, posts = 1, Counter()

    def row(name):
        E = per.get(name, [])
        buyers = Counter(e["data"].get("buyer") for e in E)
        gaps = [e["data"]["amount"] / med[(e["data"]["sku"], e["data"].get("grade"))] - 1
                for e in E if (e["data"]["sku"], e["data"].get("grade")) in med]
        stock = (byname.get(name) or {}).get("stock") or {}
        goods = [e for e in E if cat.get(e["data"]["sku"], {}).get("kind") == "goods"]
        card = ((board.get(name) or {}).get("card") or {}).get("description") or ""
        return {"shop": name, "rank": (board.get(name) or {}).get("rank"), "settles": len(E), "buyers": len(buyers),
                "repeat_pct": round(100 * sum(1 for v in buyers.values() if v >= 2) / max(1, len(buyers))),
                "price_gap_pct": round(100 * statistics.mean(gaps), 1) if gaps else None,
                "top15_held": sum(1 for s in top15 if stock.get(s)), "lines": len(stock), "units": sum(stock.values()),
                "forum_per_h": round(posts.get(name, 0) / span, 1),
                "goods_pct": round(100 * len(goods) / max(1, len(E))),
                "avg_price": round(sum(e["data"].get("amount") or 0 for e in E) / max(1, len(E))),
                "card": card[:90]}

    leaders = [n for n, _ in sorted(per.items(), key=lambda kv: -len(kv[1])) if n in byname][:5]
    rows = [row(n) for n in leaders] + ([row(SHOP_NAME)] if SHOP_NAME not in leaders else [])
    us = next(r for r in rows if r["shop"] == SHOP_NAME)
    lead = [r for r in rows if r["shop"] != SHOP_NAME]

    def m(key):
        v = [r[key] for r in lead if r[key] is not None]
        return statistics.median(v) if v else None

    gaps = []
    for key, label, unit in (("repeat_pct", "다시 산 손님 비율", "%"), ("top15_held", "시장 인기 15개 중 보유", "개"),
                             ("forum_per_h", "포럼 글", "개/시간"), ("lines", "진열 종류", "종")):
        lm = m(key)
        if lm is not None and us[key] is not None and us[key] < lm:
            gaps.append({"what": label, "us": us[key], "leaders_median": lm, "unit": unit,
                         "shortfall": round((lm - us[key]) / max(lm, 1), 2)})
    gaps.sort(key=lambda g: -g["shortfall"])
    mine = (byname.get(SHOP_NAME) or {}).get("stock") or {}
    top = [{"sku": s, "name": cat.get(s, {}).get("name", "")[:24],
            "median_b": med.get((s, "B")), "we_hold": bool(mine.get(s))} for s in top15]
    return {"at": time.strftime("%F %H:%M", time.localtime(now)), "shops": rows, "top15": top, "gaps": gaps[:3]}


def write(now=None):
    out = run(now)
    tmp = R / "benchmark.json.tmp"
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(R / "benchmark.json")
    return out


if __name__ == "__main__":
    print(json.dumps(write(), ensure_ascii=False, indent=1))
