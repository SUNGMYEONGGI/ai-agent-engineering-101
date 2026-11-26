RULES
GET /api/chain·clearing: credit_wei=1e15, 100bps, 고정 210; 순수령=P-floor(P/100)-210. GET /api/inventory(shop): balance/restock/units[].unit/sku/category/grade/cost/expires_at/supplied_at/cert. POST /api/supply {sku,qty}→402 quote, 120초 내 pay_guard 송금 후 {quote,tx_hash}; 429 닫힘. POST /api/settle {order,checkout_jwt,checkout_mandate,payment_mandate}; JWT 필수 id/shop(상점명)/shop_url/item(SKU)/price/task(고유)/currency(credits)/iat/unit, 선택 cert/claim/warranty_hours. shop 지갑 서명, 503 동일 본문 재전송, 응답 settled 확인. 보관 0.5%/h, 48h 등급 하락. 마지막 주인 한도 회당 20,000/일 200,000; 잔액 하한 1,000,000. 가격 정산 하한 ceil((cost+210)*100/99).

NOW
2026-11-26 10:50 KST 6h msgs=3/checkouts=2/settled=0; 1h 0/0/0. 원장 106분 시장 정산 155건. 잔액 4,876,216, 13 SKU·37개, 다음 로트 보관료 1,044. 공급 1795658572~1795658752(11:02:52~11:05:52 KST). 두부 없음; 시장 두부 6건(A 3928.5/B 3011 중앙가). C 요거트 가장 빠른 소비기한 26일 23시.
REVIEW 2026-11-26 10:50 credits=4876216 (+0) settled1h=0 fails=stock_and_price:1 changed=none next=a2a_handler 문의와 구매 확정 분리
다음 실행 첫 변경은 v10: 상품 단어·명시 조사 매칭, 일반 형용사 제외, 조건·복수품목은 견적만, 단일 구매 확정·유효 예약만 서명. 현 재고 unit/sku/grade/cost/expiry 확인 후 180초 보류. 정산·로그 유지. tmp/test/ 회귀 테스트에 오발급 2건·JWT 필수 필드·실 unit·shop 서명 검증 포함.

FAILED
재고 보유 2h 이상 무정산. v9 냉장고·소포장 우유 문의→C 요거트, 단단한 두부·차 문의→B 총각김치 결제서 오발급. 원인: 임의 마지막 글자 제거와 부분일치, 구매 확정 검사 없음. read_tool 출력은 unit 선택 직전에서 잘렸고 clearing 카드에서 JWT shop=상점명 및 정산 필드를 확인. holds.json은 unit 키/값 expires; reservations JSONL은 unit 또는 unit_id, held·expires_at으로 보호. 종료 요청으로 v10 미배포, 송금·가격 변경 없음.