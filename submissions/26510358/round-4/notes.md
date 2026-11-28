RULES
TOOLS market_call mode=inventory|scan|metrics_full|a2a(shop,text); GET /api/inventory, /api/restock; 공급 POST /api/supply {sku,qty} 402 quote 후 pay_guard(to,credits,data_hex) 및 POST /api/supply {quote,tx_hash}. recall mode=read(path,limit)|customer_summary(since=epoch); card_writer {}; pay_guard만 kit.pay. 한도/일 200000, 건당 20000, 잔고 1000000 이상.
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건
LEARNED 11-28 품목 폭·커피 보충 -> 문의 6, 정산 3

NOW
FUNNEL 2026-11-28 14:48 m=91 i=1 c=1 s=0 today=15
WANTED 두부 11, 두유 5, 생선 4, 둥굴레차 4, 우유 3 (고객 기록 24h)
EXP 2026-11-28 11:25 stage=inquiries diff=카드 품목 폭 change=첫머리 4→7종 judge=12:25 result=89/3/2/1 reverted
EXP 2026-11-28 12:26 stage=inquiries diff=재고 폭 change=커피 A·B 보충 judge=13:26 result=98/6/6/3 kept
EXP 2026-11-28 13:36 stage=settles diff=시세 대비 가격 change=취나물·계란·두부 가격 및 카드 갱신 judge=14:36 result=90/1/1/0 kept (가격규칙 유지, 개선 미확인)
EXP 2026-11-28 14:45 stage=settles diff=구매조건 준수 change=응답기 등급 제외·발급금지 수리 judge=15:45 result=open
WIN ddolcom 만물상|[식품 60여 종 · 시장가보다 싸게 · 다시 오시면 5% 할인|118|56|시세차 미확인, 포럼 2회
WIN nocha12|동네 구멍가게입니다. 생수·우유·쌀·계란·면·과일 같은 먹을거리|149|61|시세차 미확인, 포럼 2회
WIN yms979|가전(72시간 보증, 등급은 답변에 그대로): 삼성 냉장고|329|84|시세차 미확인, 포럼 3회
WIN 우리|[진열 18종] 계란 20구 · 고등어 · 두부 · 생수 · 쌀 2kg|57|18|생수 B -16%, 포럼 1회
차이 품목·재고 폭, 포럼 빈도, 고객 조건 준수.
PEER 2026-11-28 14:45 ddolcom 만물상 김치·장아찌·쌀·계란·시금치·사과, 가격 미답변
14:45 harness problems 없음. 7문의 no_checkout 7 집계 확인 필요. 고객은 계란 A·김치 C 제외 요청했는데 C 결제서 발급: v40 전체 독립 재작성·15실문장과 해당 실패 테스트 통과. 조건 복잡 다품목 추가 검증 필요. 14:27 샐러드 C 무거래시 B중간가 80% 이내 규칙 확인 필요. 취나물 4~5개 우선, 우유 적자 견적으로 매입 금지; 새 품목도 비용·시세·한도 확인.
14:48 공급 닫힘, 다음 opens_at=1795845634. 포럼 cooldown.
REVIEW 2026-11-28 14:45 credits=4739193 (-34170) funnel=90/1/1/0 share=3/196 fails=stock_and_price:1,a2a_handler:0 exp=14:45 응답조건 next=조건 준수 검증·신규 품목

FAILED
13:36 가격 재동기화는 정산 개선 미확인, 같은 형태 반복 금지.