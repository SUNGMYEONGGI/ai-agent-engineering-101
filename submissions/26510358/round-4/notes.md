RULES
TOOLS market_call modes=inventory|scan|metrics_full|review|a2a; 재고 GET /api/inventory; 공급 GET /api/restock, POST /api/supply {sku,qty} 402 견적→pay_guard(to,credits=total,data_hex,role=shop)→POST /api/supply {quote,tx_hash}. 20000/회 200000/일 잔액 1000000. LEARNED 11-26 포럼 게시→5분 내 문의 3~4건.

NOW
FUNNEL 2026-11-28 08:42 m=102 i=0 c=0 s=0 today=8
WANTED 계란 14, 취나물 9, 둥굴레차 7, 우유 4, 생선 4 (harness 24h; 김치 4)
EXP 2026-11-28 00:22 stage=settles diff=계란 B 가격 change=7340→7193 judge=01:22 result=97/6/4/2 미개선
EXP 2026-11-28 03:24 stage=checkouts diff=카탈로그 재고 누락 change=원가 초과 개체만 건너뛰기 judge=04:24 result=85/2/2/1 미개선
EXP 2026-11-28 05:50 stage=settles diff=요청 조건 무시 change=핸들러 독립 재작성 및 조건 검증 judge=06:50 result=미적용·판정불가
EXP 2026-11-28 08:12 stage=inquiries diff=카드 품목 폭 change=첫머리 2→4종 judge=09:12 result=진행중
WIN nocha12|카드 미확인|미확인|미확인|두부 C 3047, 임박 1640
WIN ddolcom 만물상|카드 미확인|미확인|미확인|미확인
WIN SUNGJINHO|카드 미확인|미확인|미확인|미확인
WIN 우리|계란 20구 · 생수 · 취나물|미확인|11종|미확인
PEER 2026-11-28 08:11 nocha12 두부 300g C 11팩 일반 3047, 임박 1팩 1640
차이 재고 폭, 고객 요청 품목 누락, 포럼 비교 미확인. 08:42 harness problems 없음; 취나물 3개 견적 A 2개 동일등급 시세 미확인으로 미결제. 08:42 포럼 게시. 다음 공급 약 09:01.
REVIEW 2026-11-28 08:12 credits=4835976 (+0) funnel=111/1/0/0 share=미확인/223(2h) fails=stock_and_price:1,a2a_handler:0 exp=카드 4종 next=들기름 등 수요 품목 보충

FAILED
recall 고객 요약 시각은 유닉스 초; 날짜 문자열 사용 불가. scan 출력 과다로 상위 카드·포럼 통계 확인 불가.