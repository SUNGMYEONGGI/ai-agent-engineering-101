RULES
GET /api/chain·clearing: credit_wei=1e15, 100bps, 고정 210. 순수령=P-floor(P/100)-210. GET /api/inventory(auth shop): balance, restock, units[].unit/sku/category/grade/cost/expires_at/supplied_at/cert. POST /api/supply {sku,qty}→402 quote, 120초 내 pay_guard 지급 후 {quote,tx_hash}; 429 닫힘. POST /api/settle {order,checkout_jwt,checkout_mandate,payment_mandate}; JWT id/shop/shop_url/item(SKU)/price/task/currency(credits)/iat/unit, claim=grade, warranty_hours. shop 서명, 503 동일 재전송. 보관료 0.5%/h, 48h 등급 하락. 마지막 주인 한도 회당 20,000/일 200,000, 잔액 하한 1,000,000. stock_and_price v6 원자 공시, floor=ceil((cost+210)*100/99).

NOW
2026-11-26 09:43 KST 6h msgs=4/checkouts=2/settled=0; 1h 0/0/0. 원장 표본 약 110분에 시장 정산 157건. 마지막 확인 잔액 4,876,216, 13 SKU·37개. 취나물 C 시장가 300<원가·수수료 하한 1,707; C 요거트 2개 4,990(중앙가 4,960, 하한 최대 4,705). 두부 재고 없음.
REVIEW 2026-11-26 09:25 credits=4876216 (+0, 마지막 확인값) settled1h=0 fails=stock_and_price:1 changed=none next=a2a_handler 문의/구매 확정 분리
다음 실행: 대기 응답과 지표 후 즉시 a2a_handler v10 forge. read_tool·recall·카드 추가 조회 금지(이미 확인). 상품명·카테고리 토큰 전체+명시 조사만 매칭, 일반 형용사 제외. 조건 문의·다품목은 견적, 단일 구매 확정·유효 예약만 서명. GET 실재고 unit/sku/grade/cost/expiry 확인, 180초 보류, 기존 JWT 정산·고객 로그 유지. 테스트 tmp/test/만 사용; 실제 오발급 2건, JWT 필수 필드·실 unit·shop 서명 검증.

FAILED
09:43 보유 재고 2h 이상 무정산 지속. v9 냉장고·소포장 우유 문의→요거트 C, 단단한 두부·차 문의→총각김치 B 결제서 오발급. 임의 끝 글자 제거·부분 일치와 구매 확정 미확인이 원인. 예약 로그 검색은 옛 카드 문구만 반환하여 도움 없었음. 종료 요청으로 v10 미배포; 송금 없음.