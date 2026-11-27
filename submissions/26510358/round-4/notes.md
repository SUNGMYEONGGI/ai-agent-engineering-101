RULES
TOOLS market_call mode=metrics_full|inventory|inventory_units|review|a2a; 재고 GET /api/inventory; stock_and_price 게시 후 card_writer; pay_guard만 송금. 공급 POST /api/supply auth=true {sku,qty} 402 견적 후 pay_guard, POST {quote,tx_hash}. 손실 30000/일, 송금 20000/회 200000/일, 잔고 1000000 이상. 실험 한 번에 하나.
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건.
LEARNED 11-27 포럼 600초 게시 -> 시간당 문의 6→9, 정산 1→2; 유지.

NOW
FUNNEL 2026-11-27 16:49 m=76 i=8 c=6 s=4 today=24
WANTED 계란 42, 취나물 12, 두부 9, 김치 9, 시금치 8 (16:47 harness)
EXP 2026-11-27 10:30 stage=checkouts diff=checkout 재고 정합성 change=v35 단일 파일 judge=11:30 result=reverted (owner: unsigned/list price)
EXP 2026-11-27 14:23 stage=discovery diff=포럼 게시 change=card_writer v8 600초 judge=15:23 result=86/9/5/2 kept
EXP 2026-11-27 15:39 stage=settles diff=결제서·재고 정합성 change=a2a_handler v36 judge=16:39 result=76/8/6/4 reverted (하네스 매진·만료 6)
EXP 2026-11-27 16:49 stage=settles diff=결제 직전 재고 검증 change=a2a_handler v37 재고 재조회·카탈로그 단위 일치 judge=17:49 result=open
WIN 골목상회|평소 말로 문의하세요. 판매 가능한 실재고|191|98|미확인
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물|331|82|미확인
WIN SUNGJINHO|미확인|미확인|미확인|미확인
WIN 우리|진열 17종·시장 중간가 이하·다품목 결제서|미확인|22|계란 B -2%
PEER 2026-11-27 16:37 골목상회 김치 B 7294, 취나물 B 2478, 둥굴레차 A 3706
REVIEW 2026-11-27 15:21 credits=4805752 (-10144) funnel=85/6/1/1 share=1/157(2h) fails=stock_and_price:1 exp=포럼 judge 15:23 next=핸들러 등급·실재고 정합성
16:49 잔고 4826468; 다음 공급 opens_at=1795766686. REVIEW 미완료, 2h 선두 31/23/18, 시장 169. 포럼 게시 호출 완료.

FAILED
16:47 harness 매진·만료 결제서 6, v37 적용 전; 사라질 때까지 실패. v37 실시간 재조회·카탈로그 단위 일치, 15건 테스트 통과하나 일부 문구가 실제 전체 원문 아닌 축약이고 JWT 검사는 동일 서명 재생 비교(복구 검증 아님). DECISIONS 0.6 이상 선택보다 키워드가 우선하는 결함, 낮은 확률 대안 처리 개선 필요. 재고 12h 이내 자동 중간가-10% 최우선 누락 가능. 다음 REVIEW 하네스·고객 전수·WIN 포럼 수·앱 카드; market_call과 recall은 다음 수정 시 전체 재작성.