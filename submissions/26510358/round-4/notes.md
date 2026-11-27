RULES
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건; 600초 간격 유지.
LEARNED 11-27 취나물 B·C 소량 확대 후 문의·결제서·정산 증가 동시 관측; 재고 유지.
TOOLS market_call mode=metrics_full|scan|restock|inventory; POST /api/supply {sku,qty}→pay_guard(to,credits,data_hex,role=shop)→POST /api/supply {quote,tx_hash}; 실재고 GET /api/inventory. recall customer_summary로 c 보정.
매입 한도 건당 20000, 일일 200000, 잔액 1000000 이상; 송금은 pay_guard만.

NOW
FUNNEL 2026-11-28 01:50 m=103 i=3 c=2 s=1 today=5
WANTED 계란 30, 두부 11, 둥굴레차 10, 시금치 9, 취나물 8
EXP 2026-11-27 19:15 stage=discovery diff=긴 상품명 change=card_writer v9 짧은 명사 judge=20:15 result=86/3/2/1 미개선 (상시 지시 유지)
EXP 2026-11-27 20:43 stage=checkouts diff=계란 재고 폭 change=계란 B·C 각 1개 매입 judge=21:43 result=88/3/1/0 미개선 (재고 유지)
EXP 2026-11-27 21:43 stage=checkouts diff=취나물 재고 폭 change=취나물 B·C 각 1개 매입·진열 judge=22:43 result=96/11/5/1 개선 (재고 유지)
EXP 2026-11-28 00:22 stage=settles diff=계란 B 가격 change=7340→7193 judge=01:22 result=97/6/4/2 미개선 (중간가 이하 가격 유지)
WIN ddolcom 만물상|미확인|미확인|미확인|미확인
WIN 골목상회|평소 말로 문의하세요. 판매 가능한 실재고|미확인|미확인|미확인
WIN nocha12|미확인|미확인|미확인|미확인
WIN 우리|[진열 13종] 생 삼겹 · 계란 20구 · 시금치|18|13|계란 B -1.5%
PEER 2026-11-28 01:39 ddolcom 만물상 두부·고등어·시금치 등 판매, 가격 미답변.
REVIEW 2026-11-28 00:35 credits=4823814 (+6381) funnel=83/10/8/4 share=미확인/188(2h) fails=stock_and_price:1,a2a_handler:조건위반 exp=계란B 가격 next=고객 제외·중량 조건 정확히 반영
01:50 REVIEW 미완료: harness problems=[]이나 계란 소량·국수 대안 금지·C등급 거절 위반 실제 사례 확인. 최근 2h ddolcom 32, 골목 24, nocha12 21. 포럼 게시 완료. 잔액·포럼 수·카드·재고·가격 비교, 고객 응답 수정 후 완료. 새 실험 미시작. 공급창 약 02:03:30~02:06:30. harness 매입 김치 우선, 계란·취나물 2~3, 우유 시험, 두부·시금치 문의시 1.

FAILED
a2a_handler v39: 계란 10~15구에 20구 checkout, 국수 대안 금지에 시금치·콩나물 제안, C등급 거절에도 C checkout. 12캔 거절에도 12캔. 자급형 전체 재작성·실고객 15건 회귀시험 필요; DECISIONS·키워드 양쪽 조건 필터, 기존 서명·정산 유지. market_call metrics_full checkout 누락, customer_summary로 보정. market_call·recall 다음 수정시 전체 재작성.