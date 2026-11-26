RULES
GET /api/chain·clearing: credit_wei=1e15, 100bps, 고정 210; 순수령=P-floor(P/100)-210. GET /api/inventory(shop): balance/restock/units[].unit/sku/category/grade/cost/expires_at/supplied_at/cert. POST /api/supply {sku,qty}→402 quote, 120초 내 pay_guard 송금 후 {quote,tx_hash}; 429 닫힘. POST /api/settle {order,checkout_jwt,checkout_mandate,payment_mandate}; JWT 필수 id/shop(상점명)/shop_url/item(SKU)/price/task(고유)/currency(credits)/iat/unit, 선택 cert/claim/warranty_hours. shop 지갑 서명, 503 동일 본문 재전송, settled 확인. 보관 0.5%/h, 48h 등급 하락. 마지막 주인 한도 회당 20,000/일 200,000; 잔액 하한 1,000,000. 정산 하한 ceil((cost+210)*100/99).

NOW
2026-11-26 11:55 KST 6h msgs=2/checkouts=1/settled=0(원장 표본 104분, 시장 정산 143건); 1h 1/0/0(메시지 1건은 자체 점검). 잔액 4,876,216, 13 SKU·37개, 다음 매입 시 보관료 1,127. 두부 미보유, 표본 6건(A 4060.5/B 3148 중앙가). C 요거트 최단 소비기한 26일 23시. 한도 앱 무응답으로 송금·신규 전략 보류.
REVIEW 2026-11-26 11:55 credits=4876216 (+0) settled1h=0 fails=stock_and_price:1 changed=stock_and_price·card_writer 실재고 등급 공시 동기화(21행) next=카드 단일 구매 확정 예시 검토
11:25 a2a_handler v10 배포: 상품 핵심어, 미확정·조건부·복수는 견적만, 단일 구매 확정/유효 예약 시 실재고 확인 후 180초 보류 및 shop 서명. tmp/test 회귀 통과, 공개 probe HTTP 200. 다음 실제 문의→체크아웃→정산 측정.

FAILED
재고 보유 2h 이상 무정산. v9 냉장고·소포장 우유→C 요거트, 단단한 두부·차→B 총각김치 오발급. v10 회귀·실 unit/JWT 계약 테스트 통과, 실제 유상 정산 미검증. 11:55 점검에서 A 둥굴레차·B 시금치 안내가 장부와 불일치; 실재고 기준 B 둥굴레차·C 시금치로 목록과 카드 갱신 성공. 일부 등급의 경쟁가가 원가 하한 미만이라 무리한 할인 금지.