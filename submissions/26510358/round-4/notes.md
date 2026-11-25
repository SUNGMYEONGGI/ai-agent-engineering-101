RULES
2026-11-25 /api/chain: credit_wei=1e15, market_fee_bps=100, network_fee_credits=420(거래 전체). 원장 확인: shop_fee=floor(P*1%)+210 (P=3550→245), 판매 수령 P-1%-210. 하한=원가+1%+210+손실여유. 공급: GET /api/restock {now,open,opens_at,closes_at}(서버 now 기준, 3분, 약 20분 간격), POST /api/supply {sku,qty}→402 quote{total,pay{to,wei,data},units}, pay_guard로 정확히 송금, 120초 내 POST {quote,tx_hash}. 정산 clearing /api/settle, 실제 inventory unit 필수, 503이면 같은 body 재전송. 보관 0.5%/시간, 48h마다 등급 하락. 주인 한도 1회 20000, 일 200000. 원장 체결가: 계란 Gab7c8b3d B 8390, A 9497; 김치 3kg B 10440; 취나물 B 2666; 허브차 G11a4a7fe B 3550; 크래커 G31fa8ab6 B 3510; 옛날과자 G527d0404 B 5310; 총각김치2kg G02f9f99c A 11000.

NOW
2026-11-25 20:47 KST 6h msgs=2/checkouts=1/settled=0. 잔액 약 4,946,433. 보유: 계란 A/B, 걸이 A4 B2 4500, 생수 C2 5400, 쌀 B1 C1 7700, 과자 B2 3800, 둥굴레차 A1 B1 4580. 오늘 지급 16009/200000. 20:44 공급창은 마감 직전이라 건너뜀. 다음 공급창 매입 후보: G31fa8ab6, G527d0404, G11a4a7fe(각 3~5개), G02f9f99c 김치(2~3개). 1회 지급 20000 한도 안에서 SKU별로 나누어 매입. 목표 10~20 SKU.
REVIEW 2026-11-25 20:28 credits=4946433 (-35690) settled1h=0 fails=stock_and_price:1 changed=재고 확대(계란 A/B, 원장 체결가로 가격 설정) next=원장 판매 상위 SKU 추가와 customers.jsonl 문의 확인

FAILED
재고를 보유했지만 6시간 넘게 정산 0. 원인은 SKU 부족과 비인기 품목(걸이 6개). 20:28 계란을 추가했고, 다음 공급창에서 저가 과자·차·김치를 매입할 예정. handler unit null 및 테스트 오염은 a2a_handler v8, stock_and_price v4, recall v2로 수정함. 수령은 P-1%-210(420 아님). 공급창 마감 판단은 /api/restock의 now 기준으로 할 것. 정산 실패 시 자동 환불은 아직 검증하지 않음.