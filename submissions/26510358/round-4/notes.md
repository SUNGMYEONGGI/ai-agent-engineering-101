RULES
Round 4 공급 POST /api/supply {sku,qty}: 402 quote 후 120초 내 정확한 pay(to,wei,data), {quote,tx_hash}; 10초당 1 quote, 공급 창 180초. 판매 수령 P-floor(1%)-210, 정산 실제 inventory unit 필수. 보관료 0.5%/시간, 48시간마다 등급 하락. 미확인 송금·환불 금지.

NOW
2026-11-25 19:59 KST 최근 6시간 msgs=2/checkouts=1(테스트 오염 추정)/settled=0(원장 최근 500건). 잔고 4971947, 생수 C 2, 쌀 B/C 각1, 걸이 A4 B2. 공급 창 20:00:05~20:03:05 KST. 주인 한도 1회 20000, 일 200000. 원장 판매 후보 과자 Gc89e0a89, 둥굴레차 G0746760c, 김치 G02f9f99c; 소량 확대. REVIEW 2026-11-25 18:32 credits=4982123 (+0) settled6h=0 fails=stock_and_price:1 changed=실재고 기준 A/B 가격·카드 동기화 next=고객 문의 및 첫 정산 확인

FAILED
2시간 이상 재고 있으나 정산 0: SKU 부족, 쌀 추가 후에도 미판매; 생수 입고·카드 갱신으로 개선 시도, 다음 창 상품 다양화 필요. GET /api/supply 405: 공급 시간은 inventory.restock 확인. GET /api/balance 404: 잔고는 GET /api/inventory. 기존 handler unit null 및 테스트 오염: a2a_handler v8, stock_and_price v3, recall v2 수정. pay_guard v2 체인 구조 및 한도 오류: v3 수정 후 입고 성공. stock_and_price v4 상품명 상등급 삭제 및 유통기한 표시. 고객 파일 과거 테스트 데이터로 집계 왜곡. 정산 실패 환불 자동화, 동시 보류 경쟁 및 실제 서명 검증 추가 점검 필요.