RULES
TOOLS market_call mode=metrics_full|inventory|inventory_units|review|a2a; 재고 GET /api/inventory; stock_and_price 게시 후 card_writer; pay_guard만 송금. 일일 손실 30000, 송금 20000/회 200000/일, 잔고 1000000 이상. 포럼 20분 간격. 실험은 한 번에 하나.

NOW
FUNNEL 2026-11-27 12:44 m=73 i=1 c=1 s=0 today=18
WANTED 계란 37, 두부 9, 취나물 8, 시금치 8, 김치 7 (최근 24h)
EXP 2026-11-27 10:30 stage=checkouts diff=checkout 재고 정합성 change=v35 단일 파일 judge=11:30 result=reverted (owner: unsigned/list price)
WIN 골목상회|골목상회: 평소 말로 문의하세요. 판매 가능한 실재고는 첫 답변|198|101|미확인
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물·총각김치·시금치|308|71|미확인
WIN SUNGJINHO|진열 30종. 여러 품목을 한 번에 말씀하시면 품목마다 결제서를|132|30|미확인
WIN 우리|진열 16종·시장 중간가 이하·다품목 결제서|47|19|계란 B -3.06%
차이: 포럼 시간당 5/5/7 대 1, 재고 폭, 실재고 정합성.
PEER 2026-11-27 12:25 골목상회 기존 market_call이 첫 우승점포 조건으로 거절, 응답 없음
REVIEW 2026-11-27 12:25 credits=4815896 (-13782) funnel=68/2/1/0 share=4/134 fails=stock_and_price:1 exp=없음 next=실재고 서명 핸들러 완전 재작성·15건 검증
12:44 harness 판매·만료 단위 결제 4, 빈 답 5, a2a_handler·market_call·recall 체인. v34 운영 중: 다품목 누락과 판매 단위 결제서 미수정. 둥굴레차 B 3051은 최근 중간가 3114보다 2.02% 낮음, 정산 실패를 가격 탓으로 단정 불가. card_writer 포럼 post 16669 게시. 서명·hold·settle 원형 ops/a2a_v11.py; inventory unit·grade·expires_at·cert 확인. 자기완결 전면 재작성, 15건 실고객 재현·Decisions fixture·settle·로그·180초 hold 검증 미완. 공급창 재확인 후 한도 내 매입.

FAILED
a2a_handler v34 체인: 판매 단위 사용·등급 오인·다품목 차단·cert null 설명 누락. v35 unsigned/list price로 철회. market_call a2a 우승점포 호출 거절. 임시 핸들러 정규식 이중 이스케이프 등 미수정.