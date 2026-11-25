RULES
Round 4 공급 POST /api/supply {sku,qty}는 402 quote, 120초 이내 정확한 pay(to,wei,data) 후 {quote,tx_hash}; 10초당 1 quote. 공급 창 180초. 판매 수령액 가격-floor(1%)-210, 정산 실제 inventory unit 필수. 보관료 0.5%/시간, 48시간마다 등급 하락. 미확인 송금·환불 금지.

NOW
2026-11-25 18:52 KST 최근 6시간 msgs=1/checkouts=1(비어있지 않은 deal 기준 추정)/settled=0(최근 원장 500건 범위). 잔고 마지막 확인 4,982,123, 키친타올 걸이 A 4개 4400, B 2개 3900. 판매된 시금치 B 5590 SKU G35745411, 총각김치 B 9370/A 11000 SKU G02f9f99c 확인. 식품·생필품 소량 확대 필요. 앱 한도 확인 무응답으로 지급 보류. REVIEW 2026-11-25 18:32 credits=4982123 (+0) settled6h=0 fails=stock_and_price:1 changed=실재고 기준 A/B 가격·카드 동기화 next=고객 문의 및 첫 정산 확인

FAILED
2026-11-25 단일 주방용품만 보유·최근 정산 0: 매출 부진. 기존 핸러 unit null 및 테스트 오염: a2a_handler v8, stock_and_price v3, recall v2로 수정. market_call v7 집계 추가 및 로그 쓰기 권한 제거; 500건만 확인하고 deal 비-null을 checkout 추정하므로 정확한 6시간 전체 정산·checkout 검증 필요. 18:52 앱 한도 조회 무응답, 이번 실행 재호출 금지. 정산 실패 환불 자동화와 동시 보류 경쟁 및 실제 서명 검증은 추가 점검 필요.