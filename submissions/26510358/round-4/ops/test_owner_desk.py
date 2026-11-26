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
print("owner_desk ok")
