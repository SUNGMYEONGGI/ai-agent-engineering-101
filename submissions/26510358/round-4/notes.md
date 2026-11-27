RULES
TOOLS market_call mode=metrics_full|inventory|inventory_units|review|a2a; 재고 GET /api/inventory; stock_and_price 게시 후 card_writer; pay_guard만 송금. 일일 손실 30000, 송금 20000/회 200000/일, 잔고 1000000 이상. 포럼 20분 간격. 실험은 한 번에 하나.

NOW
FUNNEL 2026-11-27 11:45 m=68 i=17 c=9 s=1 today=18
WANTED 계란 37, 두부 9, 취나물 8, 시금치 8, 김치 6
EXP 2026-11-27 10:30 stage=checkouts diff=checkout 재고 정합성 change=v35 단일 파일 judge=11:30 result=reverted (owner: unsigned/list price)
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물·총각김치·시금치·쌀|292|70|미확인
WIN SUNGJINHO|진열 31종. 여러 품목을 한 번에 말씀하시면 품목마다 결제서를|135|31|미확인
WIN 골목상회|골목상회: 평소 말로 문의하세요. 판매 가능한 실재고는 첫 답변|221|100|미확인
WIN 우리|진열 17종·시장 중간가 이하·다품목 결제서|45|19|품목별 상이
차이: 포럼 7/8/3 대 2, 재고 폭, 재고·고객조건 정합성.
PEER 2026-11-27 11:30 yms979 도구가 첫 우승점포 조건으로 거절
REVIEW 2026-11-27 11:30 credits=4829678 (-3889) funnel=66/35/16/4 share=4/142 fails=stock_and_price:1 exp=없음 next=live 재고 단일 핸들러 15건 회귀 검증
11:42 harness: 소진·상한 단위 결제서 4, 빈 응답 5, 체인 a2a_handler·market_call·recall. recall v12 단일파일 교체했으나 다음 harness 갱신 전까지 실패 유지. 핸들러 임시 초안 tmp/test/stage_78710c2b091142c0b5d0b4b7907811f4: 최초 15문의 시험 통과는 불충분, regex 이중 이스케이프·고객 조건·JWT payload 검증 실패. 배포 금지, 단일 파일 수정 후 실제 15건 재시험. v34 계속 운영 중. 12시간 임박 식품 할인 미적용. 계란 42회·김치 8회 수요, 공급창 닫힘. 카드 게시 확인.

FAILED
a2a_handler v34 체인: 판매 단위 사용·등급 오인·다품목 차단·cert null 설명 누락. v35 unsigned/list price로 철회. market_call a2a 우승점포 호출 거절. 임시 핸들러의 정규식 이중 이스케이프 등 미수정.