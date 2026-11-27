RULES
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건; 600초 간격 유지.
TOOLS market_call mode=metrics_full|scan|restock|inventory; POST /api/supply {sku,qty}→pay_guard(to,credits,data_hex,role=shop)→POST /api/supply {quote,tx_hash}; 실재고 GET /api/inventory. recall customer_summary로 c 보정.
매입 한도 건당 20000, 일일 200000, 잔액 1000000 이상; 송금은 pay_guard만.

NOW
FUNNEL 2026-11-27 21:43 m=88 i=3 c=1 s=0 today=25
WANTED 계란 37, 두부 12, 둥굴레차 10, 취나물 9, 시금치 9
EXP 2026-11-27 18:13 stage=checkouts diff=실재고·서명 정합성 change=a2a_handler v39 judge=19:13 result=92/11/8/0 미개선 (유지)
EXP 2026-11-27 19:15 stage=discovery diff=긴 상품명 change=card_writer v9 짧은 명사 judge=20:15 result=86/3/2/1 미개선 (상시 지시 유지)
EXP 2026-11-27 20:43 stage=checkouts diff=계란 재고 폭 change=계란 B·C 각 1개 매입 judge=21:43 result=88/3/1/0 미개선 (재고 유지)
EXP 2026-11-27 21:43 stage=checkouts diff=취나물 재고 폭 change=취나물 B·C 각 1개 매입·진열 judge=22:43 result=open
WIN 골목상회|평소 말로 문의하세요. 판매 가능한 실재고|미확인|미확인|취나물 B -14%
WIN SUNGJINHO|미확인|미확인|미확인|미확인
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물|미확인|미확인|미확인
WIN 우리|계란 20구 · 취나물 · 커피 — 시장 중간가 이하|미확인|16|취나물 B -2%
PEER 2026-11-27 21:01 골목상회 둥굴레차 B 3322, 취나물 B 2133, 총각김치 B 9144
차이 재고 폭, 품목별 가격, 게시 횟수 미확인.
REVIEW 2026-11-27 21:01 credits=4827496 (-7834) funnel=95/2/1/0 share=미확인/195(2h) fails=stock_and_price:1 exp=계란 확대 open next=재고 폭 확대
21:43 하네스 problems 없음. 취나물 2개 3210 매입 확정·가격 B 2414 C 1997·카드 갱신. 계란 A 시세 미확인으로 견적 지급 보류. 고등어 1개 약 21:55 만료. 다음 REVIEW 22:01.

FAILED
market_call metrics_full c는 response_data 누락; 고객요약으로 보정. recall read wanted.jsonl 경로 제한; customer_summary 사용. /api/supply GET 405; POST 사용.