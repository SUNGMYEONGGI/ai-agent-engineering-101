RULES
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건; 600초 간격 유지.
LEARNED 11-27 취나물 B·C 소량 확대 후 문의·결제서·정산 증가 동시 관측; 재고 유지.
TOOLS market_call mode=metrics_full|scan|restock|inventory; POST /api/supply {sku,qty}→pay_guard(to,credits,data_hex,role=shop)→POST /api/supply {quote,tx_hash}; 실재고 GET /api/inventory. recall customer_summary로 c 보정.
매입 한도 건당 20000, 일일 200000, 잔액 1000000 이상; 송금은 pay_guard만.

NOW
FUNNEL 2026-11-28 02:50 m=102 i=6 c=5 s=1 today=6
WANTED 계란 33, 취나물 11, 김치 9, 두부 8, 시금치 8 (harness 02:49)
EXP 2026-11-27 19:15 stage=discovery diff=긴 상품명 change=짧은 명사 judge=20:15 result=86/3/2/1 미개선 (상시 지시 유지)
EXP 2026-11-27 20:43 stage=checkouts diff=계란 재고 폭 change=B·C 각 1개 judge=21:43 result=88/3/1/0 미개선
EXP 2026-11-27 21:43 stage=checkouts diff=취나물 재고 폭 change=B·C 각 1개 judge=22:43 result=96/11/5/1 개선
EXP 2026-11-28 00:22 stage=settles diff=계란 B 가격 change=7340→7193 judge=01:22 result=97/6/4/2 미개선 (중간가 이하 유지)
WIN ddolcom 만물상|미확인|미확인|미확인|미확인
WIN 골목상회|평소 말로 문의하세요. 판매 가능한 실재고|미확인|미확인|미확인
WIN yms979|계란 20구 · 취나물 · 총각김치 2kg|미확인|미확인|미확인
WIN 우리|계란 20구 · 생수 · 취나물|28 전후|12종|미확인
PEER 2026-11-28 02:49 ddolcom 만물상 고등어·포천명가·간장고추장아찌·부추·쌀·계란, 가격 미답변.
REVIEW 2026-11-28 02:50 credits=4837017 (직전 잔액; 이후 1건 정산) funnel=102/6/5/1 share=미확인/201(2h) fails=stock_and_price:1,a2a_handler:조건위반 exp=없음 next=handler 단일파일 전면 재작성·실고객 회귀
02:49 harness problems=[]; 계란 10~15구·C 거절·대안 금지 조건 위반은 별도 실제 로그로 확인. 2h 선두 ddolcom 38 골목 35 yms979 26; 상점별 게시 수·가격 차·수량 미확인. 리뷰 카드와 한도 앱 미응답. 02:50 카탈로그·카드 갱신, 포럼 cooldown. 다음 공급창 03:04:37~03:07:37 취나물·김치 우선, 계란 2~3; 두부·시금치 문의시에만 1, 둥굴레차·우유 시험. 신규 품목 매입 원가/시세 확인. 실험 미시작.

FAILED
a2a_handler v39 조건 위반: 계란 10~15구에 20구 checkout, 국수 대안 금지에 대안 제안, C등급 거절에도 C checkout; 생선 A/B 요청 C, 생수 330~500ml에 2L. 전체 재작성·실고객 15건 회귀 필요; DECISIONS·키워드 조건 필터, 서명·정산 유지. market_call metrics_full checkout 누락, customer_summary로 보정. market_call·recall 다음 수정시 전체 재작성.