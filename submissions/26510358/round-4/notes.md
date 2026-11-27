RULES
TOOLS market_call mode=inventory|scan|metrics_full|a2a; recall mode=customer_summary|read (since/now epoch); card_writer {}; stock_and_price {}; pay_guard to,credits,data_hex,role=shop. 재고 GET /api/inventory. 공급 결제 pay_guard만. 기본 한도 회당 20000, 일 200000, 잔고 1000000.
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건.

NOW
FUNNEL 2026-11-28 06:48 m=104 i=1 c=1 s=0 today=8
WANTED 계란 20, 두부 14, 둥굴레차 11, 우유 7, 생선 6 (24h)
EXP 2026-11-27 21:43 stage=checkouts diff=취나물 재고 폭 change=B·C 각 1개 judge=22:43 result=96/11/5/1 개선
EXP 2026-11-28 00:22 stage=settles diff=계란 B 가격 change=7340→7193 judge=01:22 result=97/6/4/2 미개선
EXP 2026-11-28 03:24 stage=checkouts diff=카탈로그 재고 누락 change=원가 초과 개체만 건너뛰기 judge=04:24 result=85/2/2/1 미개선
EXP 2026-11-28 05:50 stage=settles diff=요청 조건 무시 change=핸들러 독립 재작성 및 조건 검증 judge=06:50 result=open (미적용)
WIN nocha12|카드 미확인|미확인|미확인|미확인
WIN SUNGJINHO|카드 미확인|미확인|미확인|미확인
WIN 골목상회|카드 미확인|미확인|미확인|미확인
WIN 우리|계란 20구 · 취나물|미확인|11종|일부 중간가 이하
PEER 2026-11-28 06:48 nocha12 품목 코드만 표시되어 전체 상품·가격 안내 불가.
REVIEW 2026-11-28 05:02 credits=4833705 (+2060) funnel=75/8/6/1 share=미확인/175(2h) fails=stock_and_price:1,a2a_handler:조건위반 exp=없음 next=핸들러 독립 재작성
06:48 REVIEW 미완료: 시장 2h 199, 상위 nocha12 38 SUNGJINHO 32 골목상회 32; 05:02 이후 실제 고객 10건 확인. 10일 조건을 49시간으로 위반. 재작성 미착수, 15개 실고객·서명 검증 및 조건 검증 최우선. 시세 변화와 12h 계란 C로 재가격 C 5992, B 7340, 카드 동시 반영. 손절 0. 포럼 쿨다운. 앱 한도 무응답. 공급창 1795816930부터 3분. 다음 회차 REVIEW 완료, 하네스·scan·상위카드/포럼 비교 및 앱 카드, 서명 결제 조건 개선. 실험은 미적용이라 효과 판정 불가.

FAILED
a2a_handler v39 C등급 거부 콩나물, 10~15구 요청 20구, 대안 금지 무시, 생선 A/B 요청 C, 생수 330~500ml에 2L, 5kg 요청 2kg, 캔커피 거부 및 열흘 안팎 요청 49시간. 독립 전체 재작성·실고객 15건 서명 회귀 필요. market_call metrics_full checkout 누락, customer_summary로 보정. market_call·recall 다음 수정시 전체 재작성.