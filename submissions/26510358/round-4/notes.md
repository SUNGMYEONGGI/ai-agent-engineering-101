RULES
GET /api/chain·clearing: credit_wei=1e15, 100bps, 고정 210; 순수령=P-floor(P/100)-210. GET /api/inventory(shop): balance/restock/units[].unit/sku/category/grade/cost/expires_at/supplied_at/cert. POST /api/supply {sku,qty}→402 quote, 120초 내 pay_guard 송금 후 {quote,tx_hash}; 429 닫힘. POST /api/settle {order,checkout_jwt,checkout_mandate,payment_mandate}; JWT 필수 id/shop/shop_url/item/price/task/currency/iat/unit. shop 서명, 503 동일 본문 재전송. 보관 0.5%/h, 48h 등급 하락. 마지막 주인 한도 회당 20,000/일 200,000; 잔액 하한 1,000,000. 하한 ceil((cost+210)*100/99). memory 갱신시 세 섹션 모두 전달.

NOW
2026-11-26 12:55 KST 6h msgs=1/checkouts=0/settled=0 (원장 표본 약 97분, 시장 145); 1h 0/0/0, 유일 메시지는 자체 점검. 잔액 4,876,216; 재고 13 SKU 37개, 보관료 1212; 공급 13:04:03~13:07:03. 앱 한도 조회 도구 없음·이전 미응답으로 실제 송금·가격 변경 보류.
card_writer v5 게시 13종·21행·4 skills, catalog 가격·품목별 결제 안내. a2a_handler v11 테스트 배포, 품목별 최대 3 JWT, 등급·실재고, 180초 보류, 503 재전송. 유상 정산 미검증.
market_call v13 scan 성공: 표본 144건 yms979 56 SUNGJINHO 36. 상위 B 중앙가 계란 7482.5, 차 2733.5, 취나물 2470, 쌈채소 5953, 김치 8802.5, 시금치 6431, 쌀 4709, 두부 3019.5.
stock_and_price v7 테스트 통과·preview만: 취나물 B 2420, 쌀 B 4614; 계란 B 9085·차 B 3267은 원가하한으로 경쟁가 불가. 계란 C·시금치 C 하한이 B 시장가 80%보다 높아 제외 필요. 기존 C 고가 주의.
REVIEW 2026-11-26 12:55 credits=4876216 (+0) settled1h=0 share=0/145(표본) fails=stock_and_price:1,market_call:1 changed=card_writer v5·a2a_handler v11·scan·가격안 next=주인 한도 확인 후 가격 공시 및 상위 재고 매입; v10 고객 복수 결제 미지원은 v11로 되돌림

FAILED
v9 냉장고·우유→요거트, 두부·차→김치 오발급; v10 복수 주문 결제서 없음. v11 회귀 통과, 실제 정산 미검증. scan v12 null rank 실패 v13 수정 테스트 통과. stock_and_price 새 테스트의 임시 절대경로 실패 후 v7 수정 통과; 이전 stock_and_price 실호출 실패 1. 경쟁가가 원가 하한 미만이면 할인 금지. 앱 한도 응답 없으면 매입하지 않음.