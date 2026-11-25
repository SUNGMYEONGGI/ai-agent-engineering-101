RULES
수수료는 GET /api/chain과 clearing 카드 기준: credit_wei=1e15, 100 bps, 고정비 양측 각 210. 판매 순수령=P-floor(P*1%)-210, 구매 총액=P+floor(P*1%)+210. 판매 하한=원가+1%+210+손실 여유. GET /api/inventory(auth shop): balance, units(cost 포함), restock{open,opens_at,closes_at}, storage_due_with_next_lot. POST /api/supply {sku,qty}: 닫힘 429, 열림 402 quote, pay_guard 지급 후 120초 안에 {quote,tx_hash} POST. 공급 등급은 무작위. /api/settle {order,checkout_jwt,checkout_mandate,payment_mandate}: unit 필수, 503이면 재전송. 보관료 0.5%/h, 48h마다 등급 하락. 주인 한도(11-25 기록): 회당 20,000, 일 200,000, 최소 잔액 1,000,000. 앱이 응답하지 않으면 이 한도를 적용.

NOW
2026-11-26 02:47 KST 6h msgs=6/checkouts=4/settled=0; 1h 0/0/0. 잔액 4,876,216, 다음 lot 보관료 399. 24개 품목 공시. 가격 변경: 요거트C 5690→4990(원가 4249, 만료 1795704077), 계란C 7990→7590(원가 7237, 하한 7519). 계란B 9041 유지(원가 8740, 하한 9037). 인기(원장): 취나물 23건(A3112/B2610), 계란20구 21건(A9746/B8090/C4902), 총각김치 14건(B8390), 콩나물 13건(3500), 시금치 10건(B7190), 쌈채소 7건. 다음: 총각김치B(9190) 원가를 recall로 확인한 뒤 시세 8390 근처로 인하 검토. 다음 공급 창에서 원가가 하한보다 낮은 인기 식품만 2개씩 매입.
REVIEW 2026-11-26 02:24 credits=4880880 (+0) settled1h=0 fails=stock_and_price:1 changed=재고(취나물 A 추가) next=만료 임박 요거트C·시금치B 가격 인하

FAILED
재고를 보유한 채 2시간 넘게 정산 0건. 02:12 a2a_handler v9로 등급 무시와 오매칭을 수정함. 이후 checkout은 나갔지만 결제 없음(서명 검증을 요구한 고객). 계란·김치 가격이 시세보다 높았던 것이 원인일 수 있어 02:47에 인하함. 02:42 앱 owner_limits 무응답. 콩나물 A는 원가 4081이 순수령 4031보다 높아 매입하지 않음. 11im 유료 제안은 무시함.