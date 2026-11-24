# Round 4 준비 기록

`agent.json`의 goal에 넣은 규칙이 어디서 왔는지 남겨 둔다. 2026-11-18 작성. Round 4 시작 11-24 19:00 KST.

## 사람이 정하는 것과 에이전트가 하는 것

kit v5에서 사람이 정하는 것은 `agent.json`(persona, goal, llm, `run_minutes`, `max_steps`), `app/`, `meshkit.json`뿐이다.
시장 도구는 에이전트가 `forge_tool`로 직접 만들고, 손으로 쓴 도구는 로드되지 않는다. 그래서 Round 3의 경험은 goal 텍스트로만 넘긴다.
goal은 run마다 프롬프트에 그대로 들어가고, `notes.md`는 마지막 3000자만 보인다(`scripts/round4/agent_kit.py`의 `Mind.context`, `Mind.notes`).

## goal 규칙의 근거

| 규칙 | 근거 |
|---|---|
| 수수료: shop은 `P − 1% − 210`을 받고 buyer는 `P + 1% + 210`을 낸다 | ROUND4.md "Fees" 표 |
| 수수료 숫자는 `/api/chain`과 clearing card에서 읽는다 | week-11 강의: 11-15 첫 시험 운행에서 420을 빼서 `paid_on_chain: false`, 818 credits 손실 |
| a2a handler 도구를 먼저 만든다 | ROUND4.md: handler가 없으면 메시지가 다음 턴까지 최대 80초 대기 |
| 가게로만 들어간다(buyer 없음). 재고 대금은 가게 지갑에서 송금 | kit v5.1이 기본으로 가게만 join, 시장 /rules: 새 가게에 5,000 tOKRW, 재고는 송금으로 산다. 순위는 credits만 보고 buyer는 `P + 1% + 210`을 낸다 |
| 원가/정가 비율 food 0.51, A 0.62, B 0.56, C 0.50 | week-08 72시간 ledger 분석 (11-13) |
| 같은 등급 시장가보다 4% 이상 높게 부르지 않는다 | 11-07 호가 상한 +0.12 → +0.04: 점유율 0.019→0.026, 체결률 0.37→0.41 |
| 첫 호가 뒤 한 번은 양보한다 | 11-15 haggle canary 채택: 마진 점유율 0.890 vs 0.872 |
| (삭제, 11-24) C등급 파손 약 35%, 파손 시 환불 | Round 4는 파손 확률을 공개하지 않고 시장이 환불하지 않는다(ROUND4.md). 환불은 가게가 원장의 `broken`과 보증 기간을 보고 직접 송금 |
| 프리미엄 가구는 수요가 상한 | 11-09, 11-11: 재고를 5배·2배로 늘려도 판매 그대로 |
| 버려진 협상이 잡은 재고는 3분 안에 푼다 | 11-07: 재고 없음(no_stock) 35건 중 28건이 버려진 협상이 잡고 있던 재고 |
| 공급 창은 약 20분마다 3분, 여는 분은 매번 다름. 402 견적 후 120초 안에 송금 | 시장 홈페이지, ROUND4.md (11-24). Round 3의 15분 주기와 가격 급등 규칙은 뺌 |
| 재고는 하루이틀 안에 팔 만큼만 | 보관료 시간당 0.5%(다음 재고 값에 더함), 48시간마다 한 등급 하락(ROUND4.md "Stock ages") |
| 손님에게는 지금 등급을 말한다 | 시장이 등급 주장을 검사하지 않는다(`claim_honest` 없음). 지금 등급은 `GET /api/inventory` |
| 거래는 `/api/settle`을 통과해야 인정 | 손님이 송금 후 보낸 mandate를 가게가 `/api/settle`로 넘긴다(ROUND4.md "Paying for a deal") |

## 운영에서 배운 것 (goal 밖, 사람이 챙길 것)

- Round 3 장애의 대부분은 터널이었다: URL이 하루 33번 바뀌었고, 카드 URL과 ACP URL이 어긋난 사고로 영수증 113건(17.3M)이 정산되지 않았다.
  Round 4에서는 agent endpoint가 바뀌면 `card.json`과 손님 기억이 모두 영향을 받는다.
- 하루 275분(19%) 동안 가게가 닫혀 있던 날이 있었다. 재시작, 감시, 로그 확인을 사람이 챙겨야 한다.

## 모델

`gpt-6.1-sol` (`submissions/26510358/.env`의 모델과 키). kit은 `max_tokens`를 보내는데 이 모델은 400 오류로 거부한다
(gpt-5.4 이후 모델 모두 같음, 11-18 확인). `scripts/`는 고칠 수 없어서 `ops/llm_shim.py`가 127.0.0.1:18790에서
`max_completion_tokens`(기본 16000)로 바꾸고 `reasoning_effort`를 붙여 OpenAI로 보낸다. 토큰 사용량은 `logs/llm-shim.jsonl`에 남긴다.

## 실행 (Round 4 열린 뒤)

meshkit-py가 Python 3.11 이상을 요구해서 Round 4는 `~/.venvs/round4`(Python 3.12; kit 의존성, meshkit, playwright)로 돌린다.
claim code는 <https://market.ourolabs.ai/join>에서 받은 Round 4 코드를 `round-4/.kit/owner.env`에 `MARKET_OWNER=mk-...`로 둔다(11-24). `.kit/`은 git에서 빠진다. 예전 위치 `week-08/.market/`는 ignore 규칙이 없어 옮겼다.

```bash
cd ~/ai-agent-engineering-101
set -a; . submissions/26510358/.env; . submissions/26510358/round-4/.kit/owner.env; set +a
PY=~/.venvs/round4/bin/python
$PY submissions/26510358/round-4/ops/llm_shim.py &                                   # 모델 shim (127.0.0.1:18790)
(cd ~/meshkit/meshkit-py && PORT=18765 $PY -I examples/miniapp_server.py &)          # MeshKit DailyMart (8765는 다른 사용자가 씀)
$PY scripts/round4/agent_kit.py run --dir submissions/26510358/round-4 \
    --market https://market.ourolabs.ai --name "Hermes Shop" --tunnel --app 8800 --app-tunnel
```

가게로만 들어가므로 faucet은 쓰지 않는다. 시장이 가게 지갑에 시작 자금 5,000 tOKRW를 보낸다(ROUND4.md). buyer를 켤 때만(`KIT_FLAGS=--with-buyer`) buyer 지갑 주소로 <https://faucet.maroo.io>에서 tOKRW를 받는다(5,000씩, 10,000까지).

## 미니앱 (`app/`)

starter 페이지에 세 가지를 더했다. 페이지 도구는 kit이 polling 루프 안에서 답을 기다리므로 모두 즉시 반환한다.

| 페이지 도구 | 하는 일 |
|---|---|
| `app_show_card` | 채팅에 카드 표시 (거래, 요약, 경고) |
| `app_owner_limits` | 주인이 설정 시트에서 정한 한도: 1회·하루 최대 송금, 메모. buyer 허용 여부는 11-24에 뺐다(가게 전용) (이 기기의 localStorage) |
| `app_ask_owner` | 질문 시트를 띄우고 바로 반환. 주인의 답은 `[주인 답변]`으로 시작하는 채팅 메시지로 에이전트에게 감 |

Round 4 전 미리보기: `$PY submissions/26510358/round-4/ops/preview_app.py --port 18800` 후 http://127.0.0.1:18800/ 을 연다.
가짜 에이전트가 답하고, `/tool <이름> {json}`으로 도구를 직접 불러 볼 수 있다.
11-18 headless Chrome에서 확인한 것: 도구 4개 등록, 한도 읽기·저장, 질문과 답, DailyMart 허용(검증된 영수증)·거절, 페이지 오류 0.

## 우리 가게를 MeshKit 앱으로 (`ops/meshkit_target.py`)

[MeshKit](https://github.com/Q00/meshkit)의 DailyMart 예제와 같은 구조로, 다른 학생의 에이전트가 자기 `meshkit.json`에 우리를 넣으면
`mesh_shop_catalog`, `mesh_shop_reserve` 도구가 생긴다. 앱이 직접 검증하고 실행하고 영수증에 서명한다(app sovereignty).

| 기능 | 위험 등급 | 하는 일 |
|---|---|---|
| `shop.catalog` | read:catalog, 동의 없음 | 에이전트가 쓴 `public/catalog.json`에서 상품을 찾아 줌 |
| `shop.reserve` | spend:money, 건당 예산 | 상대 예산 안의 가격일 때만 30분 예약. `public/reservations.jsonl`에 쌓이고, 결제는 시장에서 에이전트가 한다 |

- 신뢰 검사는 MeshKit 라이브러리의 `validate_and_accept`(fail-closed)를 그대로 쓰고, 기능마다 정책을 따로 둔다.
- `meshkit_target.json`(git 제외)에 영수증 서명 키, 신뢰하는 caller 목록, 건당 예산 상한(기본 1,000,000)이 있다.
  다른 학생과 연결하려면 그쪽 caller의 app_id, bundle_id, key_id, 공개키를 `trusted_callers`에 넣고, 우리 `public/meshkit-manifest.json`을 건넨다.
- `ops/test_meshkit_target.py`: MeshKit grader가 하는 공격을 HTTP로 재현한다. 11-18 결과는 13/13 통과
  (정상 카탈로그·예약 영수증 검증, 예산 아래·재고 초과·없는 SKU 거절, budget_exceeded, replay_detected,
  payload_hash_mismatch, signature_mismatch, caller_not_allowed, stale_timestamp, signature_required).
- 우리 미니앱의 kit 경로로도 확인했다: `mesh_shop_catalog`, `mesh_shop_reserve` → 허락 시트 → 검증된 영수증.

```bash
$PY submissions/26510358/round-4/ops/meshkit_target.py --init        # 한 번만
$PY submissions/26510358/round-4/ops/meshkit_target.py --tunnel      # 다른 학생용 공개 URL, manifest 갱신
```

미리보기를 휴대폰에서 보려면 `ops/preview_app.py --tunnel`을 쓴다(접근 코드 필요). 그 전에 같은 포트에서 돌고 있는
미리보기가 없는지 꼭 확인한다. 11-18에 코드 없는 이전 미리보기가 남아 있었고, 터널이 그쪽을 약 10분 동안 공개했다
(가짜 에이전트와 데모 데이터뿐, 키 없음).
