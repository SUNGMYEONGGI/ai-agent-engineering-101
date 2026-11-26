RULES
GET /api/chain·clearing: credit_wei=1e15, 100bps, 고정 210. 순수령=P-floor(P/100)-210. GET /api/inventory(auth shop): balance, restock, units[].unit/sku/grade/expires_at/supplied_at/cert. POST /api/supply {sku,qty}→402 quote, 120초 내 pay_guard 지급 후 {quote,tx_hash}; 429 닫힘. POST /api/settle {order,checkout_jwt,checkout_mandate,payment_mandate}; JWT id/shop/shop_url/item(SKU)/price/task/currency(credits)/iat/unit, claim=grade, warranty_hours. shop 서명, 503 동일 재전송. 보관료 0.5%/h, 48h마다 등급 하락. 마지막 주인 한도 회당 20,000/일 200,000, 잔액 하한 1,000,000. stock_and_price v6 원자 공시, floor=ceil((cost+210)*100/99).

NOW
2026-11-26 08:49 KST 6h msgs=5/checkouts=2/settled=0; 1h 0/0/0. 원장 500행, 약 104분 범위에서 시장 정산 168건. 마지막 확인 잔액 4,876,216, 13 SKU·37개. 취나물 C 1개 원가 1,479, 수수료 포함 보수적 하한 1,707(보관·폐기위험 별도), 시장 C 관측가 300으로 추격 금지. 취나물 B 2개·A 1개, 조회한 두부 SKU 재고 없음.
REVIEW 2026-11-26 08:23 credits=4876216 (+0, 마지막 확인값) settled1h=0 fails=stock_and_price:1 changed=none next=a2a_handler 문의/주문 분리
다음: 대기 응답·집계 후 v10 직접 재배포. 온전한 단어+허용 조사만 검색하고, 단일품목 명시 구매/확정 SKU/유효 예약에만 서명. 조건 확인 선행·다품목은 견적만. 정산·실재고 확인·180초 보류·고객 로그 유지. tmp/test/에서 오발급 2건과 정상 JWT 필드·shop 서명·실 unit 검증. 이후 C 요거트·취나물 만료/가격 점검.

FAILED
08:49 재고 보유 중 2h 이상 무정산 지속(이전 관측 포함, 현 단일 원장 범위 약 104분). 냉장고·소포장 우유 문의에 요거트 C, 단단한 두부·차 문의에 총각김치 B checkout 오발급. 일반 수식어·부분문자열 매칭 및 문의/구매 구분 누락. read_tool은 v9 앞부분만 반환, recall sign_jwt는 같은 앞부분, recover_address는 0건: 반복 조회 금지. 종료 요청으로 v10 미배포; 송금·실파일 테스트 쓰기 없음.