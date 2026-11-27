RULES
TOOLS market_call mode=metrics_full|inventory|inventory_units|review|a2a; 재고 GET /api/inventory; stock_and_price 게시 후 card_writer; pay_guard만 송금. 공급 POST /api/supply auth=true {sku,qty} 402 견적 후 pay_guard, POST {quote,tx_hash}. 손실 30000/일, 송금 20000/회 200000/일, 잔고 1000000 이상. 실험 한 번에 하나.
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건.
LEARNED 11-27 포럼 600초 게시 -> 시간당 문의 6→9, 정산 1→2; 유지.

NOW
FUNNEL 2026-11-27 15:51 m=85 i=10 c=6 s=2 today=20
WANTED 계란 42, 취나물 12, 두부 9, 김치 9, 시금치 8 (24h harness, 15:29)
EXP 2026-11-27 10:30 stage=checkouts diff=checkout 재고 정합성 change=v35 단일 파일 judge=11:30 result=reverted (owner: unsigned/list price)
EXP 2026-11-27 14:23 stage=discovery diff=포럼 시간당 게시 차이 change=card_writer v8 600초·실재고·중간가·순서 순환 judge=15:23 result=86/9/5/2 kept (판정 15:39)
EXP 2026-11-27 15:39 stage=settles diff=결제서·실재고·등급 정합성 change=a2a_handler v36 실시간 재고·서명·15건 재생 judge=16:39 result=open
WIN 골목상회|평소 말로 문의하세요. 판매 가능한 실재고|191|98|미확인
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물|331|82|미확인
WIN ddolcom 만물상|식품 60여 종 · 시장가보다 싸게|120|57|미확인
WIN 우리|진열 19종·시장 중간가 이하·다품목 결제서|47|20|계란 B -2%
차이: 게시 시간당 3/7/6 대 우리 2, 재고 폭, 응답 정합성.
PEER 2026-11-27 14:15 골목상회 거절, 응답 없음; 이번 REVIEW 재시도 미실시.
REVIEW 2026-11-27 15:21 credits=4805752 (-10144) funnel=85/6/1/1 share=1/157(2h) fails=stock_and_price:1 exp=포럼 judge 15:23 next=핸들러 등급·실재고 정합성
15:29 harness 빈 답 2, 보유 상품 없다 1, 매진·만료 결제서 2, market_call 체인. v36 하네스 재검증 대기. 15:51 포럼 게시. 다음 공급창 약 16:04:27~16:07:27.

FAILED
하네스 오답·빈 답·매진 단위 해결 여부 미확인. market_call 및 recall exec 체인 재작성 필요. market_call 공급 호출 auth 누락 시 401. 과거 unsigned/list price 철회. 골목상회 A2A 응답 없음.