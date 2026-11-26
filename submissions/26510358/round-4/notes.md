RULES
GET /api/chain·clearing: credit_wei=1e15, 100bps, 고정 210; 순수령=P-floor(P/100)-210. GET /api/inventory(shop): balance/restock/units[].unit/sku/category/grade/cost/expires_at/supplied_at/cert. POST /api/supply {sku,qty}→402 quote, 120초 내 pay_guard 송금 후 {quote,tx_hash}; 429 닫힘/요청 간격. POST /api/settle {order,checkout_jwt,checkout_mandate,payment_mandate}; JWT 필수 id/shop/shop_url/item/price/task/currency/iat/unit. shop 서명, 503 동일 본문 재전송. 보관 0.5%/h, 48h 등급 하락. 앱 한도 도구 없을 때 상시 승인: 회당 20,000/일 200,000, 잔액 하한 1,000,000. 하한 ceil((cost+210)*100/99); 시장 중간가 아래 무손실 매입만.

NOW
2026-11-26 13:55 KST 6h msgs=1/checkouts=0/settled=0; 1h 0/0/0. 잔액 4860580, 실재고 43개, 진열 13종 20라인. scan 상위 계란 B 16건 중간 7490, 둥굴레차 B 13건 2720, 총각김치 B 10건 8930, 취나물 B 9건 2510. 원가상 계란 B 9085, 차 B 3267, 김치 B 9164 불가피; 취나물 B 2459. C 계란·시금치는 B 중앙가 80% 상한과 원가 충돌로 제외. 재가격·카드 동기화. 공급 닫힘, opens_at=1795669336 약 14:02:16 KST. 정산 0일 때 300초 이내 재확인.
REVIEW 2026-11-26 13:55 credits=4860580 (-15636) settled1h=0 share=0/153(최근표본) fails=stock_and_price:1,market_call:0 changed=가격·카드 동기화 next=공급장 개장 후 원가와 중간가 검증해 상위 상품 2~5개 매입; v11 고객 실적 표본 부족이라 이전 오결제 v9/v10으로 복귀 금지.

FAILED
v9 냉장고·우유→요거트, 두부·차→김치 오발급; v10 복수 주문 결제서 없음. v11 회귀 통과, 실제 정산 미검증. scan v12 null rank 실패 v13 수정 테스트 통과. stock_and_price v7 수정 테스트 통과; 이전 실호출 실패 1, 이전 REVIEW 대비 실패 증가 없음. 경쟁가가 원가 하한 미만이면 할인 금지. 공급 요청 auth=true/role=shop은 401: 일반 호출 auth="shop". SKU 대신 한글 상품명 전송 400 수정. memory 호출은 rules,now,failed 전부 지정해야 기존 내용 유지.