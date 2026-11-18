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
| buyer 역할은 credits를 늘릴 때만 쓴다 | 순위는 credits만 반영하고 buyer 비용은 `P + m + 210`. orders card로 확인할 것 |
| 원가/정가 비율 food 0.51, A 0.62, B 0.56, C 0.50 | week-08 72시간 ledger 분석 (11-13) |
| 같은 등급 시장가보다 4% 이상 높게 부르지 않는다 | 11-07 호가 상한 +0.12 → +0.04: 점유율 0.019→0.026, 체결률 0.37→0.41 |
| 첫 호가 뒤 한 번은 양보한다 | 11-15 haggle canary 채택: 마진 점유율 0.890 vs 0.872 |
| C등급 파손 약 35% | 11-09 saved 분석: C등급 보증 없을 때 거래당 saved −0.104 |
| 프리미엄 가구는 수요가 상한 | 11-09, 11-11: 재고를 5배·2배로 늘려도 판매 그대로 |
| 버려진 협상이 잡은 재고는 3분 안에 푼다 | 11-07: 재고 없음(no_stock) 35건 중 28건이 버려진 협상이 잡고 있던 재고 |
| 공급은 약 15분마다 짧게 열림, 시간당 50개 넘으면 가격 급등 | Round 3 패치 3.2, restock 로그 |
| 마감 전 재고 정리 | Round 3는 남은 재고를 원가로 쳤다. Round 4에서도 그런지는 `/rules`에서 확인할 것 |

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
claim code는 Round 3 것(`week-08/.market/owner.env`의 `MARKET_OWNER`)을 먼저 써 보고, join이 거절되면 https://market.ourolabs.ai/join 에서 새로 받는다.

```bash
cd ~/ai-agent-engineering-101
set -a; . submissions/26510358/.env; . submissions/26510358/week-08/.market/owner.env; set +a
PY=~/.venvs/round4/bin/python
$PY submissions/26510358/round-4/ops/llm_shim.py &                                   # 모델 shim (127.0.0.1:18790)
(cd ~/meshkit/meshkit-py && PORT=18765 $PY -I examples/miniapp_server.py &)          # MeshKit DailyMart (8765는 다른 사용자가 씀)
$PY scripts/round4/agent_kit.py run --dir submissions/26510358/round-4 \
    --market https://market.ourolabs.ai --name myeonggi --tunnel --app 8800 --app-tunnel
```

kit이 출력한 buyer 지갑 주소로 https://faucet.maroo.io 에서 tOKRW를 받는다(5,000씩, 10,000까지).

## 미니앱 (`app/`)

starter 페이지에 세 가지를 더했다. 페이지 도구는 kit이 polling 루프 안에서 답을 기다리므로 모두 즉시 반환한다.

| 페이지 도구 | 하는 일 |
|---|---|
| `app_show_card` | 채팅에 카드 표시 (거래, 요약, 경고) |
| `app_owner_limits` | 주인이 설정 시트에서 정한 한도: 1회·하루 최대 송금, buyer 허용 여부, 메모 (이 기기의 localStorage) |
| `app_ask_owner` | 질문 시트를 띄우고 바로 반환. 주인의 답은 `[주인 답변]`으로 시작하는 채팅 메시지로 에이전트에게 감 |

Round 4 전 미리보기: `$PY submissions/26510358/round-4/ops/preview_app.py --port 18800` 후 http://127.0.0.1:18800/ 을 연다.
가짜 에이전트가 답하고, `/tool <이름> {json}`으로 도구를 직접 불러 볼 수 있다.
11-18 headless Chrome에서 확인한 것: 도구 4개 등록, 한도 읽기·저장, 질문과 답, DailyMart 허용(검증된 영수증)·거절, 페이지 오류 0.
