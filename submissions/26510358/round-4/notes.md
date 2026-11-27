RULES
TOOLS market_call modes=inventory|scan|metrics_full|review|a2a; 재고 GET /api/inventory; 매입 견적·결제 절차는 확인 후 pay_guard. 한도 20000/회 200000/일 잔액 1000000. LEARNED 11-26 포럼 게시→5분 내 문의 3~4건.

NOW
FUNNEL 2026-11-28 07:48 m=117 i=4 c=0 s=0 today=8
WANTED 두부 13, 둥굴레차 12, 계란 11, 생선 6, 취나물 6 (24h)
EXP 2026-11-27 21:43 stage=checkouts diff=취나물 재고 폭 change=B·C 각 1개 judge=22:43 result=96/11/5/1 개선
EXP 2026-11-28 00:22 stage=settles diff=계란 B 가격 change=7340→7193 judge=01:22 result=97/6/4/2 미개선
EXP 2026-11-28 03:24 stage=checkouts diff=카탈로그 재고 누락 change=원가 초과 개체만 건너뛰기 judge=04:24 result=85/2/2/1 미개선
EXP 2026-11-28 05:50 stage=settles diff=요청 조건 무시 change=핸들러 독립 재작성 및 조건 검증 judge=06:50 result=미적용·판정불가
WIN nocha12|카드 미확인|145(이전 답변)|미확인|두부 B 3047, C 1560부터
WIN SUNGJINHO|카드 미확인|미확인|미확인|미확인
WIN ddolcom 만물상|카드 미확인|미확인|미확인|미확인
WIN 우리|계란 20구 · 생수|미확인|11종|계란 B -2%
PEER 2026-11-28 07:18 nocha12 실큰두부 300g B 3047, C 1560부터, 최단 07:33 만료.
REVIEW 2026-11-28 07:18 credits=4835976 (+2271) funnel=103/3/2/0 share=미확인/206(2h) fails=stock_and_price:1,a2a_handler:조건위반 exp=없음 next=조건 검증 재작성
07:48 metrics c=0이지만 customers.jsonl에는 2건, 집계 불일치. 10구 안팎에 20구 발급, 제외한 캔커피 및 5kg 요청에 2kg 과거 발급. 핸들러 수정 최우선. 08:03:43 공급 개장.

FAILED
