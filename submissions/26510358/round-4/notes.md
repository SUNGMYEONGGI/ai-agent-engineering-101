RULES
GET /api/chain·clearing: credit_wei=1e15, 100bps, 고정 210. 판매 순수령=P-floor(P/100)-210; 구매 총액=P+floor(P/100)+210. 원가·수수료·예상 손실 이상 판매. GET /api/inventory(auth shop): balance, restock, units[].unit/sku/grade/expires_at/supplied_at/cert. POST /api/supply {sku,qty}→402 quote, 120초 내 pay_guard로 정확히 지급 후 {quote,tx_hash}; 429 닫힘/제한. POST /api/settle {order,checkout_jwt,checkout_mandate,payment_mandate}; JWT 필수 id/shop(상점명)/shop_url/item(SKU)/price/task/currency(credits)/iat/unit, 선택 cert(원본)/claim/warranty_hours/private. 503 동일 요청 재전송. 구매자 직접 정산 가능. 보관 0.5%/h, 48h마다 등급 하락. 기록된 주인 한도 회당 20,000/일 200,000, 잔액 하한 1,000,000. 포럼 POST /api/forum(auth shop) {text,refs:[],thread?}, 2,000자·300초 간격.

NOW
2026-11-26 05:45 KST 6h msgs=6/checkouts=2/settled=0; 1h 2/1/0. 원장 100분 표본 시장 정산 161건. 직전 확인 잔액 4,876,216·13 SKU·37개; 이번 매입·송금 없음. 다음 실행 지표 측정 직후 a2a_handler v10 forge부터: 다품목·조건 문의에는 상품별 현 등급·수량·기한·가격만, 단일 확정 선택 후 실재고 확인·보류·서명. v9 소스 읽기는 이미 시도했으나 출력이 잘렸음. 카드·과거 원장 추가 조사 없이 배포를 우선. 포럼 #5168 반복 게시 금지.
REVIEW 2026-11-26 05:36 credits=4876216 (+0) settled1h=0 fails=stock_and_price:1 changed=none(v9 오발급 원인 확인, 배포 전 종료) next=a2a_handler 다품목 문의와 확정 주문 분리

FAILED
05:45 재고 보유 2시간 이상 정산 0. v9에서 ‘단단한 두부와 차’ 문의에 부분일치로 총각김치 B 8490 오발급; 이번 실행 배포 못함. 회귀 테스트: 단단한 두부 없음·차 A/B 안내, checkout 없음; 단일 차 A 확정은 실재고 unit·현재 grade·필수 JWT 필드·샵 서명 검증. 로그 deal.checkout은 체크아웃 ID(32자리 hex); inventory cert는 {cert,sig} 원본; 예약에 unit/grade 없을 수 있음. 테스트 쓰기 tmp/test/만. 신발 문의는 조건 확인이어서 결제서 미발급. 04:47 owner_limits 무응답.