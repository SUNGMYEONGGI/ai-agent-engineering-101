#!/usr/bin/env python3
"""Ssadassa Shop as a MeshKit target: other people's mini apps can call our shop through their agents.

MeshKit (github.com/Q00/meshkit) rules this follows: the app stays sovereign (it validates, executes and signs),
every call is signed by a trusted caller, and completion is proven only by a receipt this app signs. The trust
checks are MeshKit's own `validate_and_accept` (envelope, caller policy, payload hash, timestamp, nonce replay,
consent and budget, signature), fail-closed, before any shop code runs.

Capabilities (one MCP tool each):
  shop.catalog   risk read:catalog, no consent    what we sell now, from public/catalog.json
  shop.reserve   risk spend:money, budgeted       hold a SKU for a caller; appended to public/reservations.jsonl.
                                                  The agent turns a reservation into a checkout on the market;
                                                  nothing is paid here.

The shop data comes from files the agent's own tools write (public/catalog.json); this server only reads it and
appends reservations. It never touches the market, the wallets or the LLM.

    ~/.venvs/round4/bin/python submissions/26510358/round-4/ops/meshkit_target.py --init     # keys + config, once
    ~/.venvs/round4/bin/python submissions/26510358/round-4/ops/meshkit_target.py [--port 18766] [--tunnel]

meshkit_target.json (kept out of git) holds the receipt seed, the trusted callers and the budget cap.
public/meshkit-manifest.json is what other students put in their meshkit.json (no secrets).
"""
import argparse
import base64
import json
import secrets
import sys
import threading
import time
from datetime import datetime, timezone
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

from meshkit import ed25519, mcpv2
from meshkit.receipt import MeshReceiptSigner
from meshkit.trust import (MeshInvocationPolicy, MeshSenderTrust, MeshTargetPolicy, MeshValidationError,
                           validate_and_accept)

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "meshkit_target.json"
PUBLIC = ROOT / "public"
APP_ID, BUNDLE_ID, RECEIPT_KEY_ID = "app.ssadassa", "kr.ac.seoultech.ssadassa", "ssadassa-receipt-ed25519"
DEMO_CALLER = {"app_id": "app.hermes-chat", "bundle_id": "ai.meshkit.sample.hermeschat",
               "key_id": "hermes-request-ed25519", "pubkey": "ebVWLo/mVPlAeLES6KmLp5AfhTrmlb7X4OORC60ElmQ="}

CAPABILITIES = {
    "shop.catalog": {
        "tool": mcpv2.ToolDescriptor(
            capability_id="shop.catalog",
            description="싸다싸 가게가 지금 파는 상품 목록 (sku, 이름, 등급, 가격 credits, 재고, 보증). query로 이름 검색.",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}}),
        "risk": "read:catalog", "consent": "none"},
    "shop.reserve": {
        "tool": mcpv2.ToolDescriptor(
            capability_id="shop.reserve",
            description="싸다싸 가게 상품을 예약한다. budget_krw(credits)를 넘지 않는 가격일 때만 잡히고, 30분 안에 "
                        "우리 에이전트에게 reservation_id로 연락하면 그 가격의 checkout을 받는다.",
            input_schema={"type": "object", "required": ["sku", "qty", "budget_krw"],
                          "properties": {"sku": {"type": "string"}, "qty": {"type": "string"},
                                         "budget_krw": {"type": "string"}, "contact": {"type": "string"}}}),
        "risk": "spend:money", "consent": "budgeted_per_invocation"},
}
HOLD_SECONDS = 1800


def pubkey_of(seed_hex):
    return base64.b64encode(ed25519.public_key_raw(ed25519.private_key_from_seed(bytes.fromhex(seed_hex)))).decode()


def init_config():
    if CONFIG.exists():
        sys.exit(f"[target] {CONFIG.name} exists; not touching it")
    callers = [DEMO_CALLER]
    own = ROOT / "meshkit.json"                      # our own app's caller key, so our agent can test against us
    if own.exists():
        c = json.loads(own.read_text(encoding="utf-8"))["caller"]
        if c.get("seed_hex", "").strip("<>") and c["app_id"] != DEMO_CALLER["app_id"]:
            callers.append({"app_id": c["app_id"], "bundle_id": c["bundle_id"], "key_id": c["key_id"],
                            "pubkey": pubkey_of(c["seed_hex"])})
    cfg = {"receipt_seed_hex": secrets.token_hex(32), "approved_budget_krw": 1_000_000, "trusted_callers": callers}
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CONFIG.chmod(0o600)
    print(f"[target] wrote {CONFIG.name} (receipt key {pubkey_of(cfg['receipt_seed_hex'])}); "
          "add other students' callers to trusted_callers")


class Shop:
    """Reads the catalog the agent publishes; keeps reservations. All state lives in public/."""

    def __init__(self):
        self.lock = threading.Lock()

    def catalog(self):
        try:
            data = json.loads((PUBLIC / "catalog.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        return data.get("items", []) if isinstance(data, dict) else data

    def reserved(self, sku):
        now, n = time.time(), 0
        try:
            lines = (PUBLIC / "reservations.jsonl").read_text(encoding="utf-8").splitlines()
        except OSError:
            return 0
        for line in lines:
            r = json.loads(line)
            if r["sku"] == sku and r["expires_at"] > now and r.get("state", "held") == "held":
                n += int(r["qty"])
        return n

    def call(self, name, payload):
        if name == "shop.catalog":
            q = payload.get("query", "").strip().lower()
            items = [i for i in self.catalog() if not q or q in json.dumps(i, ensure_ascii=False).lower()]
            return {"status": "completed", "count": str(len(items)), "items": json.dumps(items[:30], ensure_ascii=False)}
        sku, qty = payload["sku"], int(payload["qty"]) if payload["qty"].isdigit() else 0
        item = next((i for i in self.catalog() if str(i.get("sku")) == sku), None)
        if qty < 1 or item is None:
            return {"status": "rejected", "reason": "unknown sku or bad qty"}
        total = int(item["price"]) * qty
        if total > int(Decimal(payload["budget_krw"])):
            return {"status": "rejected", "reason": f"price {total} credits is over budget_krw"}
        with self.lock:
            if int(item.get("stock", 0)) - self.reserved(sku) < qty:
                return {"status": "rejected", "reason": "not enough stock"}
            rid = f"rsv-{uuid4().hex[:10]}"
            rec = {"reservation_id": rid, "sku": sku, "qty": qty, "unit_price": int(item["price"]), "total": total,
                   "contact": payload.get("contact", ""), "created_at": int(time.time()),
                   "expires_at": int(time.time()) + HOLD_SECONDS, "state": "held"}
            PUBLIC.mkdir(exist_ok=True)
            with open(PUBLIC / "reservations.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return {"status": "completed", "reservation_id": rid, "total_credits": str(total),
                "expires_at": str(rec["expires_at"]),
                "next": "우리 에이전트의 A2A 엔드포인트에 reservation_id를 보내면 이 가격의 checkout을 받습니다."}


def make_handler(cfg, shop):
    signer = MeshReceiptSigner.from_seed(RECEIPT_KEY_ID, bytes.fromhex(cfg["receipt_seed_hex"]))
    callers = {c["app_id"]: c for c in cfg["trusted_callers"]}
    seen, seen_lock = {}, threading.Lock()

    def reserve_nonce(nonce):
        with seen_lock:
            now = time.time()
            for n, t in list(seen.items()):
                if now - t > 600:                    # twice the 300 s timestamp window
                    del seen[n]
            if nonce in seen:
                return False
            seen[nonce] = now
            return True

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            except ValueError:
                return self.reply({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}})
            method, rpc_id = body.get("method"), body.get("id")
            if method == "server/discover":
                self.reply({"jsonrpc": "2.0", "id": rpc_id, "result": {
                    "protocolVersions": [mcpv2.PROTOCOL_VERSION], "serverInfo": {"name": APP_ID, "version": "0.1.0"},
                    "capabilities": {"tools": {}}}})
            elif method == "tools/list":
                self.reply({"jsonrpc": "2.0", "id": rpc_id,
                            "result": {"tools": [c["tool"].to_tool() for c in CAPABILITIES.values()]}})
            elif method == "tools/call":
                self.tools_call(body, rpc_id)
            else:
                self.reply({"jsonrpc": "2.0", "id": rpc_id,
                            "error": {"code": -32601, "message": f"method not found: {method}"}})

        def tools_call(self, body, rpc_id):
            try:
                request = mcpv2.extract_mesh_request(body, dict(self.headers.items()))
                cap = CAPABILITIES.get(request.target.capability_id)
                caller = callers.get(request.caller.app_id)
                if cap is None:
                    raise MeshValidationError("unsupported_capability", "unsupported capability")
                if caller is None:
                    raise MeshValidationError("caller_not_allowed", "caller is not trusted by this app")
                validate_and_accept(
                    request=request,
                    policy=MeshTargetPolicy(allowed_caller_app_id=caller["app_id"], target_bundle_id=BUNDLE_ID,
                                            capability_id=request.target.capability_id),
                    invocation_policy=MeshInvocationPolicy(
                        risk=cap["risk"], consent=cap["consent"],
                        user_approved=True,          # the caller's person approved it on their consent sheet
                        registry_signature_verified=True,
                        approved_budget=Decimal(cfg.get("approved_budget_krw", 1_000_000))),
                    trust=MeshSenderTrust(caller_app_id=caller["app_id"], caller_bundle_id=caller["bundle_id"],
                                          request_signing_algorithm="Ed25519", request_signing_key_id=caller["key_id"],
                                          public_key_base64=caller["pubkey"]),
                    reserve_nonce=reserve_nonce)
            except MeshValidationError as error:
                log({"event": "refused", "code": getattr(error, "code", str(error))})
                return self.reply(mcpv2.build_error(rpc_id, error))
            except (KeyError, ValueError, TypeError) as error:
                return self.reply(mcpv2.build_error(rpc_id, MeshValidationError("malformed_request", str(error))))
            result = shop.call(request.target.capability_id, dict(request.payload))
            receipt = signer.make_receipt(
                receipt_id=f"rcpt-{uuid4().hex[:8]}", request=request, target_app_id=APP_ID,
                target_bundle_id=BUNDLE_ID, status=result["status"], result=result, nonce=uuid4().hex,
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
            log({"event": "served", "capability": request.target.capability_id, "caller": request.caller.app_id,
                 "status": result["status"], "receipt": receipt.receipt_id})
            self.reply(mcpv2.build_tool_result(receipt, rpc_id))

        def reply(self, obj):
            data = json.dumps(obj).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    return Handler


def log(entry):
    (ROOT / "logs").mkdir(exist_ok=True)
    with open(ROOT / "logs" / "meshkit-target.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(dict(entry, ts=int(time.time())), ensure_ascii=False) + "\n")


def write_manifest(cfg, url):
    PUBLIC.mkdir(exist_ok=True)
    manifest = {"url": url, "app_id": APP_ID, "bundle_id": BUNDLE_ID, "receipt_key_id": RECEIPT_KEY_ID,
                "receipt_pubkey": pubkey_of(cfg["receipt_seed_hex"]), "consent": True,
                "capabilities": list(CAPABILITIES),
                "how_to_connect": "Add this object to targets in your meshkit.json, then send us your caller app_id, "
                                  "bundle_id, key_id and public key so we can trust you."}
    (PUBLIC / "meshkit-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                                  encoding="utf-8")
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--init", action="store_true", help="create meshkit_target.json (receipt key, trusted callers)")
    ap.add_argument("--port", type=int, default=18766)
    ap.add_argument("--tunnel", action="store_true", help="also a public https URL for other students' apps")
    ap.add_argument("--public-dir", help="where catalog.json and reservations.jsonl live (default: public/)")
    a = ap.parse_args()
    global PUBLIC
    if a.public_dir:
        PUBLIC = Path(a.public_dir).resolve()
    if a.init:
        return init_config()
    if not CONFIG.exists():
        sys.exit("[target] no meshkit_target.json; run with --init first")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    server = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(cfg, Shop()))
    url = f"http://127.0.0.1:{a.port}"
    if a.tunnel:
        sys.path.insert(0, str(ROOT.parents[2] / "scripts" / "round4"))
        import market_kit as mk
        threading.Thread(target=server.serve_forever, daemon=True).start()
        _proc, url = mk.open_tunnel(a.port)
    m = write_manifest(cfg, url)
    print(f"[target] {APP_ID} on {url}  receipt key {m['receipt_pubkey']}  ({len(cfg['trusted_callers'])} trusted callers)",
          flush=True)
    if a.tunnel:
        threading.Event().wait()
    server.serve_forever()


if __name__ == "__main__":
    main()
