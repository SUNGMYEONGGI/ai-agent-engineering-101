RULES
TOOLS market_call mode=metrics_full|scan|inventory|inventory_units(sku)|a2a; GET /api/restock; POST /api/supply {sku,qty} → pay_guard(to,credits=total,data_hex=pay.data,role=shop) → POST /api/supply {quote,tx_hash}; inventory GET /api/inventory. 기본 송금한도 회당 20000, 일 200000, 잔액 1000000 이상.
LEARNED 11-26 포럼 게시 -> 5분 내 문의 3~4건.
LEARNED 11-28 커피 A·B 보충 -> 시간당 문의 3→6, 정산 1→3.

NOW
FUNNEL 2026-11-28 15:47 m=94 i=2 c=2 s=1 today=16
WANTED 두부 11, 두유 4, 둥굴레차 4, 생선 3, 요거트 3 (24h)
EXP 2026-11-28 12:26 stage=inquiries diff=재고 폭 change=커피 A·B 보충 judge=13:26 result=98/6/6/3 kept
EXP 2026-11-28 13:36 stage=settles diff=시세 대비 가격 change=취나물·계란·두부 가격 및 카드 갱신 judge=14:36 result=90/1/1/0 kept (개선 미확인)
EXP 2026-11-28 14:45 stage=settles diff=구매조건 준수 change=응답기 등급 제외·발급금지 수리 judge=15:45 result=94/2/2/1 kept (소표본)
EXP 2026-11-28 15:47 stage=inquiries diff=포럼 빈도 change=10분 간격 게시 유지 judge=16:47 result=open
WIN nocha12|동네 구멍가게입니다. 생수·우유·쌀·계란·면·과일 같은 먹을거리|151|61|시세차 미확인, 포럼 2회
WIN yms979|가전(72시간 보증, 등급은 답변에 그대로): 삼성 냉장고|316|83|시세차 미확인, 포럼 3회
WIN ddolcom 만물상|[식품 60여 종 · 시장가보다 싸게 · 다시 오시면 5% 할인|123|60|시세차 미확인, 포럼 3회
WIN 우리|[진열 18종] 계란 20구 · 고등어 · 국내산 부추|59|18|시세차 미확인, 포럼 1회(게시 직전)
차이 품목·재고 폭, 포럼 빈도, 표시 가격 폭.
PEER 2026-11-28 15:47 nocha12 재고 있으나 품목명 대신 SKU만 보여 가격 짝짓기 어렵다고 답변
REVIEW 2026-11-28 15:47 credits=4730974 (-8219) funnel=94/2/2/1 share=1/188 fails=stock_and_price:1,a2a_handler:0 exp=포럼 빈도 next=수익 가능한 신규 품목
15:47 harness problems 없음; 상담 2건 쌀 B·계란 B 결제서 정상. 포럼 게시 완료. 공급창 16:00:27~16:03:27. 앱 한도 응답 없음, 기본 한도 적용.

FAILED
