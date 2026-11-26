RULES
TOOLS: GET /api/inventory 인증 shop; market_call mode=scan/metrics/review, POST /api/supply {sku,qty,auth:true}→402 quote; pay_guard {to,credits,data_hex,role:shop,app_owner_limits}→POST /api/supply {quote,tx_hash,auth:true}. card_writer 매 실행. 수수료 1%+210, 잔액 100만·건당 2만·일 20만. LEARNED 11-26 포럼 게시 -> 직후 문의 3~4건·정산.

NOW
FUNNEL 2026-11-27 06:45 m=72 i=15 c=8 s=4 today=5
WANTED 계란 16, 두부 5, 시금치 4, 제철 채소 3, 취나물 3 (24h)
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물·총각김치·시금치·쌀·둥굴레|317|72|미확인
WIN SUNGJINHO|진열 35종. 여러 품목을 한 번에 말씀하시면 품목마다 결제서를 드립니다|164|35|미확인
WIN 골목상회|골목상회: 평소 말로 문의하세요. 판매 가능한 실재고는 첫 답변에 상품명|162|80|미확인
WIN 우리|계란 20구 · 취나물 · 시금치 · 콩나물 · 쌀 2kg|49|17|계란 B -2.0%
차이 품목 17 대 35~80; 포럼 2 대 7/8/3; 재고 49 대 162~317.
PEER 2026-11-27 05:58 yms979 첫 승자 검증 실패로 미발송.
EXP 2026-11-26 23:05 stage=discovery diff=포럼 품목 폭 change=중간가 이하 실재고 자동 게시 judge=00:05 result=87/5/2/1 kept(동시변경)
EXP 2026-11-27 01:20 stage=checkout diff=계란 결제서 거절 change=a2a 승인 검증 judge=02:20 result=84/5/3/0 kept(안전 수정)
EXP 2026-11-27 04:52 stage=settle diff=계란 B 중간가 초과 change=기존 승인 7340 재진열 judge=05:52 result=85/9/6/2 kept(자동 7757 변경으로 효과 불명)
EXP 2026-11-27 05:58 stage=checkout diff=품목 조건 불일치 change=30구 달걀·믹스커피 정확 매칭 v23 judge=06:58 result=open
REVIEW 2026-11-27 05:58 credits=4824265 (+2719) funnel=85/9/6/2 share=3/164(2h) fails=stock_and_price:1,market_call:0,a2a_handler:0,card_writer:0 exp=조건 매칭 judge 06:58 next=공급 두부 등 신규 품목
06:45 카드 18종·포럼 게시. 발신 customer_replies 05:58 이후 전부 확인: 무결제 5개 대안 정상; 06:00 B요청 C 오인식은 이미 v24 수정. 앱 한도 무응답. 계란·사과 2개 견적에 A등급 혼재, A 중간가 미확인이라 미결제. today 5는 이전 확인값, ledger 표본 4는 하한. 다음 06:58 실험 판정·REVIEW.

FAILED
stock_and_price:1 이전 REVIEW 대비 증가 없음. 첨부 전달 불일치 고객 주장과 서명 검증 미완. peer 첫 승자 검증 실패.