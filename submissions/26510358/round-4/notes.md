RULES
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건; 600초 간격 유지.
LEARNED 11-27 취나물 B·C 소량 확대 후 문의·결제서·정산 증가 동시 관측; 재고 유지.
TOOLS market_call mode=metrics_full|scan|restock|inventory; POST /api/supply {sku,qty}→pay_guard(to,credits,data_hex,role=shop)→POST /api/supply {quote,tx_hash}; 실재고 GET /api/inventory. recall customer_summary로 c 보정.
매입 한도 건당 20000, 일일 200000, 잔액 1000000 이상; 송금은 pay_guard만.

NOW
FUNNEL 2026-11-27 22:43 m=96 i=11 c=5 s=1 today=22
WANTED 계란 37, 두부 12, 둥굴레차 10, 취나물 9, 시금치 9
EXP 2026-11-27 18:13 stage=checkouts diff=실재고·서명 정합성 change=a2a_handler v39 judge=19:13 result=92/11/8/0 미개선 (유지)
EXP 2026-11-27 19:15 stage=discovery diff=긴 상품명 change=card_writer v9 짧은 명사 judge=20:15 result=86/3/2/1 미개선 (상시 지시 유지)
EXP 2026-11-27 20:43 stage=checkouts diff=계란 재고 폭 change=계란 B·C 각 1개 매입 judge=21:43 result=88/3/1/0 미개선 (재고 유지)
EXP 2026-11-27 21:43 stage=checkouts diff=취나물 재고 폭 change=취나물 B·C 각 1개 매입·진열 judge=22:43 result=96/11/5/1 개선 (재고 유지)
WIN 골목상회|평소 말로 문의하세요. 판매 가능한 실재고|미확인|미확인|둥굴레차 B 3081, 시세차 미확인
WIN ddolcom 만물상|미확인|미확인|미확인|미확인
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물|미확인|미확인|미확인
WIN 우리|계란 20구 · 취나물 — 시장 중간가 이하|21|16|계란 B 시세 이하
PEER 2026-11-27 22:20 골목상회 둥굴레차 B 3081, 생수 B 3601, 총각김치 A 10361
차이 재고 폭, 품목별 가격, 게시 횟수 미확인.
REVIEW 2026-11-27 22:20 credits=4823504 (-3992) funnel=85/4/2/1 share=미확인/190(2h) fails=stock_and_price:1 exp=취나물 확대 open next=등급 거부 위반 수정
22:43 계란 B 1개 5866 매입·진열, 포럼 게시. 둥굴레차 B 2410은 시세 미확인이라 미매입, 공급창 닫힘. harness 22:40 problems=[]; 계란 폐기 이력 2~3, 김치 4~5, 둥굴레차 1~2 시험 권고. 다음 공급 23:03경.
다음 실험 대기: 조건 거부·포장 위반 핸들러 수정. C 거부에도 C, 12캔 제외에도 12캔, 10~15구에도 20구 C. 미수정. 오늘 집계 22와 이전 23 불일치.

FAILED
market_call metrics_full c는 response_data 누락; 고객요약으로 보정. recall read wanted.jsonl 경로 제한. a2a_handler v39 C등급 거부 및 계란 포장·등급 조건 위반; read_tool 소스 응답 잘림. 둥굴레차 B 시장 중간가 미확인.