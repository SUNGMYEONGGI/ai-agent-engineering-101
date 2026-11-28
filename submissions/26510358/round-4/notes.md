RULES
TOOLS market_call mode=review|scan|inventory|inventory_units|a2a 또는 path/method/auth/body; 재고 GET /api/inventory; 공급 POST /api/supply shop {sku,qty}→402 견적 pay_guard {to,credits:total,data_hex:pay.data,role:shop,app_owner_limits}→POST /api/supply {quote,tx_hash}; 가격 stock_and_price 후 card_writer. 송금 pay_guard만.
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건; 600초 간격 유지.
LEARNED 11-28 대표상품 노출 -> 시간당 문의 3→6건 (소표본).
기본 상한 1회 20000, 일 200000, 잔고 1000000 이상.

NOW
FUNNEL 2026-11-28 21:50 m=99 i=1 c=1 s=0 today=11
WANTED 두부 8, 두유 4, 요거트 3, 커피 2, 생선 2
EXP 2026-11-28 17:59 stage=settles diff=임박 가격 change=계란 C 5224 및 카드 갱신 judge=18:59 result=106/9/6/2 kept (소표본)
EXP 2026-11-28 19:24 stage=inquiries diff=품목 폭 change=감귤 B 2개 입고 judge=20:24 result=102/3/1/0 kept (개선 불명)
EXP 2026-11-28 20:34 stage=settles diff=임박 두부 가격 change=두부 C 4250→2480 및 카드 갱신 judge=21:34 result=100/3/2/0 판정 불가(중간 가격 변경)
EXP 2026-11-28 21:40 stage=settles diff=임박 계란 가격 change=계란 C 5960→4375 및 카드 갱신 judge=22:40 result=대기
WIN SUNGJINHO|[최근 3시간 거래 1위] 진열 42종. 여러 품목을 한 번에|160|42|가격차 미확인, 포럼 2회
WIN yms979|가전(72시간 보증, 등급은 답변에 그대로): 삼성 냉장고|312|79|가격차 미확인, 포럼 2회
WIN ddolcom 만물상|[식품 60여 종 · 시장가보다 싸게 · 다시 오시면|89|49|가격차 미확인, 포럼 2회
WIN 우리|진열 21종, 시장 중간가 이하|62|21|일부 시세 이하, 포럼 1회
차이: 품목 폭, 재고 수량, 문의 응답 정확도.
PEER 2026-11-28 21:20 SUNGJINHO 취나물·총각김치·고등어·두부·쌈채소; 가격 미답변.
REVIEW 2026-11-28 21:23 credits=4721802 (+0) book=-64622 funnel=94/2/1/0 share=0/200 fails=stock_and_price:1,a2a_handler:0 exp=두부 가격 judge=21:34 next=응답기 무관한 대안·거절·등급·다품목 수정
21:49 harness 빈 답 2건 미해결 최우선. a2a_handler v40 끝부분은 recall read tools/a2a_handler/logic.py offset=3500 또는 6500으로 확인 가능. 거절이 앞의 복수 품목에 적용 안 됨, 일반 대안 무관. 테스트도 recall로 확인 가능. 21:50 포럼 게시. 앱 한도 도구 없음. 운영 한도 손실 25041/일 지급 72944/회 0; 두부·커피 과잉 매입 금지.

FAILED
recall customer_summary since는 숫자 epoch만 사용. GET /api/supply는 405; 공급창 GET /api/restock. recall read customers.jsonl·loss_reservations.json 직접 불가. market_call 공급 견적 429 제한. memory는 모든 섹션 전달 필수; mode=read도 쓰기이므로 금지. read_tool a2a_handler 출력 잘림; 검증 없는 교체 금지.