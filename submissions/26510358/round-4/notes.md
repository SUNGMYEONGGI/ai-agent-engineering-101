RULES
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건; 600초 간격 유지.
LEARNED 11-27 취나물 B·C 소량 확대 후 문의·결제서·정산 증가 동시 관측; 재고 유지.
TOOLS market_call mode=metrics_full|scan|restock|inventory; POST /api/supply {sku,qty}→pay_guard(to,credits,data_hex,role=shop)→POST /api/supply {quote,tx_hash}; 실재고 GET /api/inventory. recall customer_summary로 c 보정.
매입 한도 건당 20000, 일일 200000, 잔액 1000000 이상; 송금은 pay_guard만.

NOW
FUNNEL 2026-11-28 04:31 m=85 i=2 c=2 s=1 today=7
WANTED 계란 24, 둥굴레차 10, 두부 9, 시금치 8, 우유 8 (24h)
EXP 2026-11-27 20:43 stage=checkouts diff=계란 재고 폭 change=B·C 각 1개 judge=21:43 result=88/3/1/0 미개선
EXP 2026-11-27 21:43 stage=checkouts diff=취나물 재고 폭 change=B·C 각 1개 judge=22:43 result=96/11/5/1 개선
EXP 2026-11-28 00:22 stage=settles diff=계란 B 가격 change=7340→7193 judge=01:22 result=97/6/4/2 미개선
EXP 2026-11-28 03:24 stage=checkouts diff=카탈로그 재고 누락 change=원가 초과 개체만 건너뛰기 judge=04:24 result=85/2/2/1 미개선 (기준 94/2/2/1)
WIN ddolcom 만물상|카드 미확인|미확인|미확인|미확인
WIN yms979|계란 20구 · 취나물 · 총각김치 2kg|미확인|미확인|미확인
WIN SUNGJINHO|카드 미확인|미확인|미확인|미확인
WIN 우리|계란 20구 · 취나물 · 콩나물|16|12종|취나물 B -2%
PEER 2026-11-28 03:55 ddolcom 만물상 포기김치·사과·장아찌·쌀·계란·생수, 가격 미답변.
REVIEW 2026-11-28 03:55 credits=4831645 (-5372) funnel=101/0/0/0 share=미확인/208(2h) fails=stock_and_price:1,a2a_handler:조건위반 exp=카탈로그 누락 next=handler 조건 회귀 재작성
04:31 포럼 게시. 다음 공급창 04:43:14 KST. 04:22 점검 problems=[]이나 고객 C등급 거부 무시 문제는 여전히 존재. 다음 실행 최우선: a2a_handler 전체 독립 재작성 및 실제 고객 조건·15건 서명 회귀. 공급창 verdict 취나물·김치 4~5, 계란 2~3, 우유 1~2 시험; 두부·시금치는 요청 시만.

FAILED
a2a_handler v39 조건 위반: C등급 거부 콩나물 checkout 04:10; 계란 10~15구에 20구, 대안 금지 무시, 생선 A/B 요청 C, 생수 330~500ml에 2L, 5kg 요청 2kg, 캔커피 거부에도 결제서. 전체 재작성·실고객 15건 회귀 필요. market_call metrics_full checkout 누락, customer_summary로 보정. market_call·recall 다음 수정시 전체 재작성.