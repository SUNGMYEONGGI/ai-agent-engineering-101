#!/usr/bin/env python3
"""Attack and use ops/meshkit_target.py over HTTP, the way MeshKit's grader does (tests/test_trust.py cases).

Starts the target on a free port with a temporary public dir and a sample catalog, then checks:
valid catalog and reserve calls come back with a receipt that verifies under our receipt key; tampered payload,
wrong signer, unsigned, untrusted caller, stale timestamp, replayed nonce and over-budget spends are refused;
a price over the caller's budget, unknown SKU and too little stock are refused by the shop.

    ~/.venvs/round4/bin/python submissions/26510358/round-4/ops/test_meshkit_target.py
"""
import copy
import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from meshkit import ed25519, mcpv2
from meshkit.models import MeshCapability, MeshIdentity
from meshkit.receipt import MeshReceiptTrust, verify_receipt
from meshkit.request import MeshRequest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ops"))
import meshkit_target as T  # noqa: E402

CFG = json.loads(T.CONFIG.read_text(encoding="utf-8"))
DEMO_SEED = bytes(range(1, 33))                     # the demo caller the config trusts (app.hermes-chat)
CATALOG = {"items": [{"sku": "G1", "name": "원목 의자", "grade": "A", "price": 50000, "stock": 2, "warranty_hours": 72},
                     {"sku": "F1", "name": "우유 1L", "grade": "A", "price": 2500, "stock": 5, "warranty_hours": 0}]}


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def request(cap, payload, app_id="app.hermes-chat", seed=DEMO_SEED, ts=None, nonce=None):
    caller = MeshIdentity(app_id=app_id, install_id="install-test", bundle_id="ai.meshkit.sample.hermeschat",
                          public_key_id="hermes-request-ed25519")
    r = MeshRequest.create(
        request_id=f"req-{uuid4().hex[:8]}", caller=caller,
        target=MeshCapability(target_bundle_id=T.BUNDLE_ID, capability_id=cap, version="1.0"),
        payload=payload, nonce=nonce or uuid4().hex,
        timestamp=(ts or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    return r.signed(ed25519.private_key_from_seed(seed), "hermes-request-ed25519")


def post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def call(url, req, mutate=None):
    body = mcpv2.build_tool_call(req, rpc_id=2, client_name="test", client_version="1")
    if mutate:
        body = mutate(copy.deepcopy(body))
    return post(url, body, mcpv2.request_headers(req.target.capability_id)), req


def verified(resp, req):
    receipt = mcpv2.extract_mesh_receipt(resp)
    verify_receipt(receipt, MeshReceiptTrust(
        target_app_id=T.APP_ID, target_bundle_id=T.BUNDLE_ID, receipt_signing_algorithm="Ed25519",
        receipt_signing_key_id=T.RECEIPT_KEY_ID, public_key_base64=T.pubkey_of(CFG["receipt_seed_hex"])), request=req)
    return receipt.result


def main():
    tmp = Path(tempfile.mkdtemp(prefix="ssadassa-target-"))
    (tmp / "catalog.json").write_text(json.dumps(CATALOG, ensure_ascii=False), encoding="utf-8")
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen([sys.executable, str(ROOT / "ops" / "meshkit_target.py"), "--port", str(port),
                             "--public-dir", str(tmp)], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    fails = []

    def check(name, ok, detail=""):
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")
        if not ok:
            fails.append(name)

    def refused(name, resp, code=None):
        err = resp.get("error")
        got = ((err or {}).get("data") or {}).get("meshkit", {}).get("code") if err else None
        check(name, err is not None and (code is None or got == code), f"code={got}")

    try:
        for _ in range(50):
            try:
                tools = post(url, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                             {"content-type": "application/json", "MCP-Protocol-Version": mcpv2.PROTOCOL_VERSION,
                              "Mcp-Method": "tools/list"})
                break
            except OSError:
                time.sleep(0.2)
        names = [t["name"] for t in tools["result"]["tools"]]
        check("tools/list", names == ["shop.catalog", "shop.reserve"], str(names))

        resp, req = call(url, request("shop.catalog", {"query": "의자"}))
        res = verified(resp, req)
        check("catalog: verified receipt, search works", res["count"] == "1" and "G1" in res["items"], res["count"])

        resp, req = call(url, request("shop.reserve", {"sku": "G1", "qty": "1", "budget_krw": "60000", "contact": "t"}))
        res = verified(resp, req)
        held = (tmp / "reservations.jsonl").read_text(encoding="utf-8").splitlines()
        check("reserve: verified receipt and one held line", res["status"] == "completed" and len(held) == 1,
              res.get("reservation_id", ""))

        resp, req = call(url, request("shop.reserve", {"sku": "G1", "qty": "1", "budget_krw": "40000"}))
        check("reserve under price: shop refuses", verified(resp, req)["status"] == "rejected")
        resp, req = call(url, request("shop.reserve", {"sku": "G1", "qty": "2", "budget_krw": "200000"}))
        check("reserve beyond stock (1 left after hold): refused", verified(resp, req)["status"] == "rejected")
        resp, req = call(url, request("shop.reserve", {"sku": "X9", "qty": "1", "budget_krw": "1000"}))
        check("unknown sku: refused", verified(resp, req)["status"] == "rejected")

        refused("over approved budget", call(url, request("shop.reserve", {"sku": "F1", "qty": "1",
                                                                           "budget_krw": "2000000"}))[0], "budget_exceeded")
        r = request("shop.catalog", {"query": ""})
        call(url, r)
        refused("replayed nonce", call(url, r)[0], "replay_detected")

        def tamper(body):
            body["params"]["arguments"]["query"] = "changed"
            return body
        refused("tampered payload", call(url, request("shop.catalog", {"query": "a"}), tamper)[0])
        refused("wrong signer key", call(url, request("shop.catalog", {"query": ""}, seed=bytes(range(2, 34))))[0])
        refused("untrusted caller", call(url, request("shop.catalog", {"query": ""}, app_id="app.stranger"))[0],
                "caller_not_allowed")
        refused("stale timestamp", call(url, request("shop.catalog", {"query": ""},
                                                     ts=datetime.now(timezone.utc) - timedelta(minutes=30)))[0])
        unsigned = replace(request("shop.catalog", {"query": ""}), signature=replace(
            request("shop.catalog", {"query": ""}).signature, value=""))
        refused("unsigned request", call(url, unsigned)[0])
    finally:
        proc.terminate()
    print(f"\n{'ALL PASS' if not fails else 'FAILED: ' + ', '.join(fails)}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
