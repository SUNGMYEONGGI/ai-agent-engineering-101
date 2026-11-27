RULES
TOOLS market_call mode=metrics_full|scan|inventory|inventory_units, REST GET /api/restock, POST /api/supply {sku,qty} then pay_guard to/credits/data_hex then POST /api/supply {quote,tx_hash}; GET /api/inventory. pay_guard 상한 20000/건 200000/일 잔액 1000000.
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건.

NOW
FUNNEL 2026-11-27 20:43 m=89 i=2 c=1 s=1 today=25
WANTED 계란 37, 두부 12, 둥굴레차 10, 취나물 9, 시금치 9
EXP 2026-11-27 15:39 stage=settles diff=결제서·재고 정합성 change=a2a_handler v36 judge=16:39 result=76/8/6/4 reverted (하네스 매진·만료 6)
EXP 2026-11-27 18:13 stage=checkouts diff=실재고·서명 결제서 정합성 change=a2a_handler v39 독립 파일 judge=19:13 result=92/11/8/0 미개선 (v39 유지, 안전 대체 필요)
EXP 2026-11-27 19:15 stage=discovery diff=긴 상품명 change=card_writer v9 짧은 명사·중간가 이하 우선 judge=20:15 result=86/3/2/1 미개선 (상시 지시라 유지)
EXP 2026-11-27 20:43 stage=checkouts diff=인기 계란 재고 폭 change=계란 B·C 각 1개 매입·진열 judge=21:43 result=open
WIN 골목상회|평소 말로 문의하세요. 판매 가능한 실재고|미확인|미확인|둥굴레차 B -3%
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물|미확인|미확인|미확인
WIN SUNGJINHO|미확인|미확인|미확인|미확인
WIN 우리|계란 20구 · 쌀 2kg · 커피|미확인|13|계란 C 중간가 이하
PEER 2026-11-27 19:59 골목상회 둥굴레차 B 3032, 취나물 B 2133, 쌀 2kg B 5002
차이 재고 폭, 품목별 가격, 문의 조건·취소 준수. 게시 횟수 미확인.
REVIEW 2026-11-27 19:59 credits=4835330 (+0) funnel=91/6/4/0 share=미확인/180(2h) fails=stock_and_price:1 exp=card_writer v9 open next=취소·지정상품 정확성
20:35 하네스 problems=[]; 계란 2~3, 취나물 2~3, 김치 4~5, 두부·시금치 요청 시 1개. 20:43 계란 2개 10285+420 매입; 18행 13종 진열, 포럼 게시. 대체 거부 라떼에 UCC 결제서 발급 오류 재현 테스트 필요. 다음 REVIEW 20:59.

FAILED
market_call metrics_full c는 response_data 누락; 고객요약으로 보정. recall read wanted.jsonl 경로 제한; customer_summary 사용.