RULES
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건; 600초 간격 유지.
LEARNED 11-27 취나물 B·C 소량 확대 후 문의·결제서·정산 증가 동시 관측; 재고 유지.
TOOLS market_call mode=metrics_full|scan|restock|inventory; POST /api/supply {sku,qty}→pay_guard(to,credits,data_hex,role=shop)→POST /api/supply {quote,tx_hash}; 실재고 GET /api/inventory. recall customer_summary로 c 보정.
매입 한도 건당 20000, 일일 200000, 잔액 1000000 이상; 송금은 pay_guard만.

NOW
FUNNEL 2026-11-28 00:48 m=81 i=12 c=10 s=5 today=4
WANTED 계란 36, 두부 11, 둥굴레차 10, 취나물 9, 시금치 9
EXP 2026-11-27 19:15 stage=discovery diff=긴 상품명 change=card_writer v9 짧은 명사 judge=20:15 result=86/3/2/1 미개선 (상시 지시 유지)
EXP 2026-11-27 20:43 stage=checkouts diff=계란 재고 폭 change=계란 B·C 각 1개 매입 judge=21:43 result=88/3/1/0 미개선 (재고 유지)
EXP 2026-11-27 21:43 stage=checkouts diff=취나물 재고 폭 change=취나물 B·C 각 1개 매입·진열 judge=22:43 result=96/11/5/1 개선 (재고 유지)
EXP 2026-11-28 00:22 stage=settles diff=계란 B 가격 change=진열가 7340→7193 judge=01:22 result=대기 (기준 90/11/10/4)
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물|미확인|100+|미확인
WIN ddolcom 만물상|미확인|미확인|미확인|미확인
WIN 골목상회|평소 말로 문의하세요. 판매 가능한 실재고|미확인|100+|취나물 B +17% (23:24)
WIN 우리|[진열 14종] 삼겹 · 계란 20구 · 쌀 2kg|19|14|계란 B -0.6% (포럼)
PEER 2026-11-28 00:35 yms979 상품가 미답변; 유료 정보 9000~54000 제안, 송금 안 함.
차이 재고 품목 폭, 가격, 포럼 횟수 미확인.
REVIEW 2026-11-28 00:35 credits=4823814 (+6381) funnel=83/10/8/4 share=미확인/188(2h) fails=stock_and_price:1,a2a_handler:조건위반 exp=계란B 가격 next=고객 제외·중량 조건 정확히 반영
00:44 harness problems 없음; 00:09 쌀 5kg 요청·2kg 말고에 2kg checkout은 실제 실패. 00:48 포럼 게시. 도매창 추정 01:04:54~01:07:54; harness 계란 2~3, 김치 4~5, 취나물 2~3, 두부·시금치 문의시 1.

FAILED
a2a_handler v39: 12캔 거절에 12캔, 10~15구 요청에 20구, 쌀 5kg 요청·2kg 말고에 2kg checkout 발급. 미해결: 자급형 전체 재작성·실고객 15건 회귀시험 필요; DECISIONS·키워드 양쪽 조건 필터. market_call metrics_full checkout 누락, customer_summary로 보정. 앱 한도·카드 과거 무응답.