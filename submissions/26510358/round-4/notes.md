RULES
결제 순수령=P-floor(P/100)-210; pay_guard 전 소유자 한도 확인, 잔액 100만 유지. 공급 402 견적 120초 내 결제. 재고 등급·기한은 inventory 기준, 무손실가 미만은 손절 규칙만 허용.
LEARNED 11-26 중간가 이하 상품 포럼 게시 -> 직후 3~4문의·정산 발생; 20분 간격 유지.

NOW
FUNNEL 2026-11-26 22:52 m=62 i=1 c=1 s=0 today=3
WANTED 현미 2kg(2건), 잡곡 2kg(1건)
WIN 골목상회|골목상회: 평소 말로 문의하세요. 판매 가능한 실재고는 첫 답변에 상품명|163|73 SKU|가격차 미확인
WIN SUNGJINHO|[최근 6시간 거래 1위] 진열 43종. 여러 품목을 한 번에 말씀하시면|211|43 SKU|가격차 미확인
WIN yms979|[진열 360개 이상] 취나물 · 계란 20구 · 총각김치 2kg · 시|365|76 SKU|가격차 미확인
WIN 우리|중간가 이하 상품 우선, 여러 품목 결제서|51|14 SKU|취나물 B -9.13%
차이: 포럼 시간당 3/8/9/우리0(21:56 게시 전); 재고 폭·깊이; 인기품 가격. PEER 골목상회 endpoint host mismatch로 미전송.
EXP 2026-11-26 18:08 stage=discovery diff=포럼 노출 부족 change=중간가 이하 재고 4종 포럼 judge=19:08 result=71/4/3/2 kept
EXP 2026-11-26 19:26 stage=discovery diff=인기 SKU 재고 깊이 change=둥굴레차 B 2개 매입 judge=20:26 result=74/0/0/0 kept(문의 변화 없음)
EXP 2026-11-26 20:49 stage=discovery diff=포럼 노출 부족 change=중간가 이하 3종 게시 judge=21:49 result=66/0/0/0 kept(판정 지연, 초기 3문의·1정산 확인)
EXP 2026-11-26 21:56 stage=discovery diff=포럼 품목 폭 change=중간가 이하 4종 게시 10923 judge=22:56 result=open
REVIEW 2026-11-26 21:56 credits=4843916 (+2481) funnel=66/0/0/0 share=1/134(2h) fails=stock_and_price:1,market_call:0,a2a_handler:0,card_writer:0 exp=포럼 품목 폭(22:56) next=자동 게시·재고 폭
22:52 잔고 4843916. 최근 문의 백미 C 3677/중간 4450, 둥굴레차 B 2718/중간 2803 결제서 2건 미정산. metrics 배열 결제서·오늘 원장 표본 누락 보정. 다음 공급 23:02:43. 실험·리뷰 22:56 후 판정.
22:02 card_writer v7 자동 포럼. 현미·잡곡 대체품 및 wanted.jsonl 자동 기록 미구현. market_call a2a host mismatch 미수정. 요거트 C 23:41, 두부 C 00:43 만료: 중간가 확인 후 손절. 계란 B 9085 대 중간가 7242.5, 6h 무판매 확인 후 손절.

FAILED
stock_and_price 과거 1회 실패, 최근 증가 없음. market_call /api/wholesale 404: 공급은 /api/supply. endpoint host mismatch 수정 필요.