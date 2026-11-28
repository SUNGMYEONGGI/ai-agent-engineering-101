RULES
TOOLS market_call mode=review|scan|inventory|inventory_units|a2a 또는 path/method/auth/body; 재고 GET /api/inventory; 공급 POST /api/supply shop {sku,qty}→402 견적 pay_guard {to,credits:total,data_hex:pay.data,role:shop,app_owner_limits}→POST /api/supply {quote,tx_hash}; 가격 stock_and_price 후 card_writer. 송금 pay_guard만.
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건; 600초 간격 유지.
LEARNED 11-28 대표상품 노출 -> 시간당 문의 3→6건 (소표본).
기본 한도 1회 20000, 일 200000, 잔고 1000000 이상.

NOW
FUNNEL 2026-11-28 18:50 m=101 i=11 c=6 s=2 today=14
WANTED 두부 8, 둥굴레차 4, 두유 4, 커피 3, 요거트 3 (24h 최근 요약)
EXP 2026-11-28 14:45 stage=settles diff=구매조건 준수 change=응답기 등급 제외·발급금지 수리 judge=15:45 result=94/2/2/1 kept (소표본)
EXP 2026-11-28 15:47 stage=inquiries diff=포럼 빈도 change=10분 간격 게시 유지 judge=16:47 result=90/3/1/1 kept (소표본)
EXP 2026-11-28 16:56 stage=inquiries diff=카드 대표상품 노출 change=시세 이하 대표상품 회전 judge=17:56 result=86/6/3/0 kept (소표본)
EXP 2026-11-28 17:59 stage=settles diff=임박 가격 change=계란 C 5224 및 카드 갱신 judge=18:59 result=open
WIN ddolcom 만물상|식품 60여 종 · 시장가보다 싸게|84|51|시세차 미확인, 포럼 3회
WIN yms979|가전 72시간 보증|321|81|시세차 미확인, 포럼 3회
WIN nocha12|동네 구멍가게입니다|151|60|시세차 미확인, 포럼 3회
WIN 우리|진열 19종|60|19|일부 시세 이하, 포럼 1회
차이: 품목 폭, 재고 수량, 포럼 빈도.
PEER 2026-11-28 17:59 ddolcom 만물상 포천명가·장아찌·햅쌀·계란 등 판매, 가격 미제시
REVIEW 2026-11-28 17:59 credits=4727579 (+0) funnel=86/6/3/0 share=1/177 fails=stock_and_price:1,a2a_handler:0 exp=임박 계란 가격 judge=18:59 next=응답기 오발급 수리
18:43 harness problems 없음, restock 빈 목록. 18:46 포럼 게시, 20종 60개, 잔고 4728309. 다음 공급창 19:04:30~19:07:30; 앱 한도 1회 20000 일 200000 손실 30000.
실제 문의: 차·빵 등에 무관 두부·계란 추천, 거절한 두부 결제서 발급, 복수 품목 누락. 11-28 14:08 김치 C 제외·계란 A 요청에 둘 다 C 발급했던 과거 사례도 있음. a2a_handler v40 수리 및 실제 메시지 15건·JWT 검증 테스트 미완료. 다음 REVIEW 18:59에 harness 확인하고 우선 처리. 주인에게 목록 답변함.

FAILED
recall customer_summary since는 숫자 epoch만 사용. GET /api/supply는 405; 공급창은 GET /api/restock.