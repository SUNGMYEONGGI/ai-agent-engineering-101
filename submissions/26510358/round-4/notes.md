RULES
TOOLS market_call mode=metrics_full|scan|inventory|inventory_units, REST GET /api/restock, POST /api/supply {sku,qty} then pay_guard to/credits/data_hex then POST /api/supply {quote,tx_hash}; GET /api/inventory. pay_guard 상한 20000/건 200000/일 잔액 1000000. LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건.

NOW
FUNNEL 2026-11-27 19:42 m=93 i=9 c=6 s=0 today=24
WANTED 계란 37, 두부 12, 취나물 9, 시금치 9, 둥굴레차 9
EXP 2026-11-27 14:23 stage=discovery diff=포럼 게시 change=card_writer v8 600초 judge=15:23 result=86/9/5/2 kept
EXP 2026-11-27 15:39 stage=settles diff=결제서·재고 정합성 change=a2a_handler v36 judge=16:39 result=76/8/6/4 reverted (하네스 매진·만료 6)
EXP 2026-11-27 18:13 stage=checkouts diff=실재고·서명 결제서 정합성 change=a2a_handler v39 독립 파일 judge=19:13 result=92/11/8/0 미개선 (v39 유지, 안전 대체 필요)
EXP 2026-11-27 19:15 stage=discovery diff=긴 상품명 change=card_writer v9 짧은 명사·중간가 이하 우선 judge=20:15 result=open
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물|미확인|미확인|미확인
WIN SUNGJINHO|미확인|미확인|미확인|미확인
WIN 골목상회|평소 말로 문의하세요. 판매 가능한 실재고|미확인|미확인|미확인
WIN 우리|계란 20구 · 둥굴레차 · 생수 · 스파게티|미확인|15|계란 B -2%
PEER 2026-11-27 18:57 yms979 유료 정보상품 가격 안내, 식품 가격 미응답; 송금 안 함
REVIEW 2026-11-27 18:57 credits=4835330 (+8862) funnel=83/12/7/1 share=미확인/164(2h) fails=stock_and_price:1 exp=v39 open next=요청 조건 일치·재고 폭 확대
19:42 고객 9문의 6결제서 0정산. market_call c=0 집계 오류 response_data 누락. 취소 요청에 결제서, 루카스나인 요청에 UCC 대체, 재서명 요청 미처리. harness 19:33 problems 없음. 취나물 A 2개 5525 견적 A중간가 미확인 보류. 포럼 게시 완료. 다음 REVIEW 19:57.

FAILED
market_call metrics_full c는 response_data 누락; 고객요약으로 보정. recall read wanted.jsonl 경로 제한; customer_summary 사용.