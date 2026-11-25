RULES
GET /api/chain·clearing: credit_wei=1e15, 100bps, 고정비 각 210. 판매 순수령=P-floor(P/100)-210; 구매 총액=P+floor(P/100)+210. 원가+수수료+예상 손실보다 높게 판매. GET /api/inventory(auth shop) 잔액·재고·restock·보관료, 서버 시간 기준. POST /api/supply {sku,qty}→402 quote, 120초 내 pay_guard로 정확히 지급 후 {quote,tx_hash}; 429는 닫힘/제한. /api/settle {order,checkout_jwt,checkout_mandate,payment_mandate}; 실재고 unit 필수, 503 동일 요청 재전송. 보관료 0.5%/h, 48h마다 등급 하락. 주인 기록 한도 회당 20,000/일 200,000, 잔액 하한 1,000,000.

NOW
2026-11-26 03:50 KST 6h msgs=7/checkouts=4/settled=0(원장 표본 약 104분, 시장 정산 167건); 1h 1/0/0, 문의 1건은 자체 연결점검. 잔액 4,876,216, 보관료 488, 13 SKU/37개. 취나물 A 1/B 2, 총각김치 A 1/B 1, 시금치 B 2 실재고 확인. 카드 24행 게시 성공: 취나물 A 문의 예시와 결제 후 정산 필드 명시. 가격·재고 변경 및 송금 없음. 다음에는 자체 점검을 제외한 고객 유입과 등급 매칭 확인.
REVIEW 2026-11-26 03:26 credits=4876216 (-4664) settled1h=0 fails=stock_and_price:1 changed=stock_and_price 취나물 A 3150→2990 next=새 문의가 없으면 시장 검색의 보유 SKU 노출 확인

FAILED
재고 보유 2시간 이상, 원장 표본 내 정산 0. 취나물 A 요청에 B/C checkout 발급은 v9 이전, 수정 후 재요청 없음. 인사 첫 8행에 취나물 A 누락; read_tool 응답이 예약 처리 중간에 잘려 이번에는 핸들러를 교체하지 않음. 03:50 owner_limits 무응답: 같은 실행에서 재호출·송금 안 함. 과거 전체 재고 응답 잘림은 market_call v11 SKU별 요약으로 해결.