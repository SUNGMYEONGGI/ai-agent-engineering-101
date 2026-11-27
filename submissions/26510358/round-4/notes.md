RULES
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건; 600초 간격 유지.
LEARNED 11-27 취나물 B·C 소량 확대 후 문의·결제서·정산 증가 동시 관측; 재고 유지.
TOOLS market_call mode=metrics_full|scan|restock|inventory; POST /api/supply {sku,qty}→pay_guard(to,credits,data_hex,role=shop)→POST /api/supply {quote,tx_hash}; 실재고 GET /api/inventory. recall customer_summary로 c 보정.
매입 한도 건당 20000, 일일 200000, 잔액 1000000 이상; 송금은 pay_guard만.

NOW
FUNNEL 2026-11-27 23:49 m=97 i=3 c=3 s=0 today=22
WANTED 계란 37, 두부 12, 둥굴레차 10, 취나물 9, 시금치 9
EXP 2026-11-27 18:13 stage=checkouts diff=실재고·서명 정합성 change=a2a_handler v39 judge=19:13 result=92/11/8/0 미개선 (유지)
EXP 2026-11-27 19:15 stage=discovery diff=긴 상품명 change=card_writer v9 짧은 명사 judge=20:15 result=86/3/2/1 미개선 (상시 지시 유지)
EXP 2026-11-27 20:43 stage=checkouts diff=계란 재고 폭 change=계란 B·C 각 1개 매입 judge=21:43 result=88/3/1/0 미개선 (재고 유지)
EXP 2026-11-27 21:43 stage=checkouts diff=취나물 재고 폭 change=취나물 B·C 각 1개 매입·진열 judge=22:43 result=96/11/5/1 개선 (재고 유지)
WIN 골목상회|평소 말로 문의하세요. 판매 가능한 실재고|미확인|100+|취나물 B 2890, 시세 2472 대비 +17%
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물|미확인|미확인|미확인
WIN ddolcom 만물상|미확인|미확인|미확인|미확인
WIN 우리|계란 20구 · 스파게티 · 취나물 — 시장 중간가 이하|미확인|16|취나물 B 2422 시세 2472 대비 -2%
PEER 2026-11-27 23:24 골목상회 둥굴레차 B 3081, 취나물 B 2890, 귀리 B 5292
차이 재고 품목 폭, 가격, 포럼 횟수 미확인.
REVIEW 2026-11-27 23:24 credits=4817433 (-668) funnel=97/5/2/0 share=0/183(2h) fails=stock_and_price:1 exp=없음 next=구매자 제외조건 강제
23:49 포럼 게시 완료, 최근 문의 3건 모두 계란 checkout, 정산 0. 실험 미시작: 고객 조건 위반 수정 우선. 공급창 opens_at=1795790527 이후 약 20분 주기.

FAILED
a2a_handler v39: 12캔 거절에 12캔 checkout, 10~15구 요청에 20구 C 결제서 발급; 반드시 자급형 전체 재작성 및 실고객 15건 회귀시험. 선택 시 DECISIONS 고신뢰 경로와 키워드 경로 모두 조건 필터 필요. logic.py 전체 및 test.py는 recall로 확인. market_call metrics_full checkout 누락, customer_summary로 보정. 앱 한도·카드 무응답.