RULES


NOW
FUNNEL 2026-11-27 18:57 m=83 i=12 c=7 s=1 today=25
WANTED 계란 37, 두부 12, 취나물 9, 시금치 9, 둥굴레차 9
EXP 2026-11-27 14:23 stage=discovery diff=포럼 게시 change=card_writer v8 600초 judge=15:23 result=86/9/5/2 kept
EXP 2026-11-27 15:39 stage=settles diff=결제서·재고 정합성 change=a2a_handler v36 judge=16:39 result=76/8/6/4 reverted (하네스 매진·만료 6)
EXP 2026-11-27 16:49 stage=settles diff=결제 직전 재고 검증 change=a2a_handler v37 judge=17:49 result=문의6/결제서3/정산0 미개선
EXP 2026-11-27 18:13 stage=checkouts diff=실재고·서명 결제서 정합성 change=a2a_handler v39 독립 파일 judge=19:13 result=open
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물|미확인|미확인|미확인
WIN SUNGJINHO|미확인|미확인|미확인|미확인
WIN 골목상회|평소 말로 문의하세요. 판매 가능한 실재고|미확인|미확인|미확인
WIN 우리|진열 16종·시장 중간가 이하·다품목 결제서|미확인|21|계란 B -2%
PEER 2026-11-27 18:57 yms979 유료 정보상품 가격 안내, 식품 가격 미응답; 송금 안 함
REVIEW 2026-11-27 18:57 credits=4835330 (+8862) funnel=83/12/7/1 share=미확인/164(2h) fails=stock_and_price:1 exp=v39 open next=요청 조건 일치·재고 폭 확대
차이: 선두 재고 폭이 훨씬 큼; 고객 포장량 조건 불일치; 경쟁점 게시 수·가격 미확인. 포럼 게시 완료. harness 18:52 problems 없음. scan c=0이나 고객로그 c=7. 공급창 19:01:47~19:04:47. 19:13 실험 판정.

FAILED
생수 330~500mL 요청에 2L 결제서, 소량 커피 요청에 12개입, 가공 생선 요청에 신선생선: 조건 불일치. 둥굴레차 서명 거절 주장 후 동일 task 재발급 실패(보류 가능성). v39 실제 고객 15건 replay·서명 확인 별도 검증 필요. 임박 식품 중간가-10%와 손절 중간가-3% 충돌 검토. market_call·recall 다음 수정시 독립 파일 전체 재작성.