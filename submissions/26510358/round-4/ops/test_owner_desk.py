"""python ops/test_owner_desk.py : the owner desk's parsing, stuck clock, alerts and limit bounds, on a temp dir."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import owner_desk as d  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="owner-desk-"))
d.R, d.STATE = tmp, tmp / ".kit" / "desk_state.json"
(tmp / "logs").mkdir()
NOTES = """NOW
FUNNEL 2026-11-26 14:30 m=81 i=0 c=0 s=0 today=0
EXP 2026-11-26 13:00 stage=i diff=card nouns change=short nouns card judge=14:00 result=81/0/0/0 reverted
EXP 2026-11-26 14:20 stage=i diff=price gap change=eggs to median judge=15:20 result=
WIN yms979|계란 20구 · 취나물 · 총각김치|350|30|-5%
WIN 우리|계란 B 특란 20구 신선|43|13|+14%
LOSS 2026-11-26 14:10 egg-b 12000
LOSS 2026-11-26 14:12 tea-b 13000
LOSS 2026-11-25 09:00 old 99999
"""
day0 = 1795671000.0                                          # 2026-11-26 local, any fixed time
(tmp / "owner_vetoes.jsonl").write_text(json.dumps({"exp": "2026-11-26 14:20", "action": "stop"}) + "\n")

a = d.dash(now=day0, notes=NOTES)
f = a["funnel"]
assert (f["m"], f["i"], f["blocked"]) == (81, 0, "i"), f
assert [e["state"] for e in a["experiments"]] == ["reverted", "open"], a["experiments"]
assert a["experiments"][1]["change"] == "eggs to median" and a["experiments"][1]["veto"] == "stop"
assert a["winners"][1] == {"shop": "우리", "card": "계란 B 특란 20구 신선", "units": "43", "lines": "13", "gap": "+14%"}
import time  # noqa: E402
if time.strftime("%F", time.localtime(day0)) == "2026-11-26":   # LOSS dates are local; skip off-timezone hosts
    assert a["loss_today"] == 25000 and any(x["kind"] == "loss" for x in a["alerts"]), a
assert not any(x["kind"] == "stuck" for x in a["alerts"])        # just started
b = d.dash(now=day0 + 2 * 3600 + 1, notes=NOTES)                  # same stage two hours later
assert any(x["kind"] == "stuck" for x in b["alerts"]), b["alerts"]
c = d.dash(now=day0 + 3 * 3600, notes=NOTES.replace("i=0 c=0", "i=3 c=0"))   # moved on: clock restarts
assert c["funnel"]["blocked"] == "c" and not any(x["kind"] == "stuck" for x in c["alerts"])
assert c["tokens"]["per_settle"] is None                          # no settle today: no ratio

v = d.clean_limits({"max_loss_per_day": "40000", "daily_tokens": 8000000, "note": " x "})
assert v["max_loss_per_day"] == 40000 and v["daily_tokens"] == 8000000 and v["note"] == "x"
for bad in ({"max_pay_per_call": -1}, {"daily_tokens": 10**9}, {"max_pay_per_day": "lots"}):
    try:
        d.clean_limits(bad)
        raise AssertionError(f"accepted {bad}")
    except ValueError:
        pass
assert d.parse_funnel("REVIEW 2026-11-26 13:55 credits=1 funnel=153/1/0/0 share=0")["i"] == 1
# LEARNED, WANTED, market (rank history, forum posts per shop)
d.RANKS = tmp / ".kit" / "desk_rank.json"
n2 = NOTES.replace("NOW", "RULES\nLEARNED 2026-11-26 포럼 목록 글 -> 5분 안 문의 3~4건\nNOW") + "WANTED 현미 2kg, 냉장고\n"
e = d.dash(now=day0, notes=n2)
assert e["learned"] == ["2026-11-26 포럼 목록 글 -> 5분 안 문의 3~4건"], e["learned"]
assert e["wanted"] == {"source": "notes.md", "items": [{"item": "현미 2kg, 냉장고", "n": None}]}, e["wanted"]
(tmp / "wanted.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [
    {"ts": day0 - 60, "item": "현미 2kg"}, {"ts": day0 - 120, "item": "현미 2kg"}, {"ts": day0 - 90000, "item": "old"},
    {"ts": day0 - 30, "item": "냉장고"}]) + "\nnot json\n")
assert d.dash(now=day0, notes=n2)["wanted"]["items"] == [{"item": "현미 2kg", "n": 2}, {"item": "냉장고", "n": 1}]
board = {"shops": [{"name": "yms979", "rank": 3}, {"name": "Hermes Shop", "rank": 11}, {"name": "gone", "rank": None}]}
forum = [{"ts": day0 - 60, "author": "yms979"}, {"ts": day0 - 120, "author": "yms979"},
         {"ts": day0 - 30, "author": "Hermes Shop"}, {"ts": day0 - 7200, "author": "Hermes Shop"}]
m = d.refresh_market(now=day0, board=board, forum=forum)
assert (m["rank"], m["of"]) == (11, 2) and m["forum"] == {"ours": 1, "top": [{"shop": "yms979", "n": 2}, {"shop": "Hermes Shop", "n": 1}]}, m
board["shops"][1]["rank"] = 9
assert [r for _, r in d.refresh_market(now=day0 + 60, board=board, forum=[])["history"]] == [11, 9]
assert d.refresh_market(now=day0 + 120, board=board, forum=[])["history"][-1][1] == 9   # unchanged rank: no new point
assert d.dash(now=day0, notes=n2)["market"]["rank"] == 9
print("owner_desk ok")

# harness: health rows, a memory change is logged between two snapshots, forge rows join the timeline
(tmp / "notes.md").write_text("RULES\nA\n", encoding="utf-8")
(tmp / "logs" / "react.jsonl").write_text(json.dumps({"ts": day0, "action": "sleep", "args": {"seconds": 600}}) + "\n")
(tmp / "logs" / "forge.jsonl").write_text(json.dumps({"ts": day0, "tool": "recall", "version": 2, "passed": False, "error": "x"}) + "\n")
d.track_changes(day0)
(tmp / "notes.md").write_text("RULES\nB\n", encoding="utf-8")
d.track_changes(day0 + 60)
h = d.harness(now=day0 + 120)
assert [r["name"] for r in h["health"]][0] == "ReAct 루프" and h["health"][0]["state"] == "ok", h["health"][0]
assert h["health"][4]["state"] == "warn"                          # the last forge failed its test
mem = [c for c in h["changes"] if c["kind"] == "memory"]
assert mem and mem[0]["added"] == ["B"] and mem[0]["removed"] == ["A"], h["changes"]
assert any(c["kind"] == "tool" and c["title"] == "recall v2" for c in h["changes"])
print("harness ok")
