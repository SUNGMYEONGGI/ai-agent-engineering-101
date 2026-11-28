RULES
TOOLS market_call mode=review|scan|inventory|inventory_units|a2a 또는 path/method/auth/body; 재고 GET /api/inventory; 공급 POST /api/supply shop {sku,qty}→402 견적 pay_guard {to,credits:total,data_hex:pay.data,role:shop,app_owner_limits}→POST /api/supply {quote,tx_hash}; 가격 stock_and_price 후 card_writer. 송금 pay_guard만.
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건; 600초 간격 유지.
LEARNED 11-28 대표상품 노출 -> 시간당 문의 3→6건 (소표본).
기본 한도 1회 20000, 일 200000, 잔고 1000000 이상.

NOW
FUNNEL 2026-11-28 19:44 m=100 i=6 c=3 s=0 today=13
WANTED 두부 8, 두유 4, 둥굴레차 3, 요거트 3, 가자미 2
EXP 2026-11-28 15:47 stage=inquiries diff=포럼 빈도 change=10분 간격 게시 유지 judge=16:47 result=90/3/1/1 kept (소표본)
EXP 2026-11-28 16:56 stage=inquiries diff=카드 대표상품 노출 change=시세 이하 대표상품 회전 judge=17:56 result=86/6/3/0 kept (소표본)
EXP 2026-11-28 17:59 stage=settles diff=임박 가격 change=계란 C 5224 및 카드 갱신 judge=18:59 result=106/9/6/2 kept (늦은 판정, 소표본)
EXP 2026-11-28 19:24 stage=inquiries diff=품목 폭 change=감귤 B 2개 신규 입고 및 카드 갱신 judge=20:24 result=대기
WIN yms979|가전(72시간 보증, 등급은 답변에 그대로): 삼성 냉장고|314|79|시세차 미확인, 포럼 3회
WIN nocha12|동네 구멍가게입니다. 생수·우유·쌀·계란·면·과일|141|58|시세차 미확인, 포럼 1회
WIN 골목상회|골목상회: 평소 말로 문의하면 실제 A·B 재고를 독점 보류|276|147|시세차 미확인, 포럼 0회
WIN 우리|진열 21종, 시장 중간가 이하|62|21|일부 시세 이하, 포럼 2회
차이: 품목 폭, 재고 수량, 응답 정확도.
PEER 2026-11-28 19:12 yms979 상품 판매 가격 답변 없이 유료 정보 안내. 송금 안 함.
REVIEW 2026-11-28 19:12 credits=4728309 (+730) funnel=106/9/6/2 share=2/205 fails=stock_and_price:1,a2a_handler:0 exp=없음 next=응답기 거절상품·환불 오인 수리
19:44 포럼 게시 후 가격표·카드 갱신. 최근 문의 6, 결제서 3, 정산 0: 휴지 신규 구매·환불 조건을 환불 청구로 2회 오인. a2a_handler v40 수리와 실제 고객 15건 JWT 검증 테스트 미완료, 다음 실행 최우선. 소유자에게 앞서 예고한 20:12 수리 실험은 아직 미시작임을 정정 필요.
19:44 계란 C 1개 약 9시간·두부 C 1개 약 5.6시간 남음. 동일 C 시세 부재 시 임박 10% 할인 여부 및 우선 제공 수리 미완료. 계란 C 6248, 두부 C 4250. harness 19:35 problems 없음.
19:44 시금치·고등어 도매 일부 원가가 해당 등급 시세 초과로 포기. 신규 칼국수 2개 6116 견적은 pay_guard daily_limit로 송금 거절, 미구매. 일일 한도 200000, 다음 공급창 약 20:02. REVIEW 20:12, 실험 판정 20:24.

FAILED
recall customer_summary since는 숫자 epoch만 사용. GET /api/supply는 405; 공급창은 GET /api/restock. recall read는 customers.jsonl 직접 읽기 불가. market_call 공급 견적 요청 간 429 제한.