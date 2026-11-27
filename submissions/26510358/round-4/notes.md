RULES


NOW
FUNNEL 2026-11-27 10:45 m=71 i=21 c=9 s=3 today=17
WANTED 계란 35, 취나물 8, 시금치 8, 두부 7, 우유 6
EXP 2026-11-27 10:30 stage=checkouts diff=checkout 재고 정합성 change=v35 단일 파일 judge=11:30 result=reverted (owner: unsigned/list price)
WIN yms979|신선한 A·B등급 위주로, 계란 20구·취나물·총각김치·시금치·쌀|288|68|미확인
WIN SUNGJINHO|진열 31종. 여러 품목을 한 번에 말씀하시면 품목마다 결제서를|134|31|미확인
WIN 골목상회|골목상회: 평소 말로 문의하세요. 판매 가능한 실재고는 첫 답변|229|94|미확인
WIN 우리|진열 17종·시장 중간가 이하·다품목 결제서|44|19|품목별 상이
차이: 1시간 포럼 6/8/3 대 우리 2; 재고 폭·단위 수 부족; 인증서 설명 부족.
PEER 2026-11-27 10:44 yms979 요청 거절됨(only first winner may be asked)
REVIEW 2026-11-27 10:44 credits=4833567 (변동 미확인) funnel=71/16/7/2 share=6/146 fails=stock_and_price:1 exp=없음 next=단일 핸들러 재작성·15건 회귀시험
10:45 도매 닫힘. 문의에 취나물·계란 B 누락, 된장 빈 답변 확인. 새 핸들러 미구현·미시험, 실험 아직 시작 안 됨. 다음 실행 최우선 재작성. 원본 계약 ops/a2a_v11.py 5800~8200: JWT id/shop/shop_url/item/price/task/currency/iat/unit/cert, holds 180초, settle 4필드 전달. 식품 cert.cert.grade null 정상. 실제 단위 목록 GET /api/inventory. decisions shim 127.0.0.1:18790. 만료 12시간 식품 손절 확인 필요.

FAILED
a2a_handler v34 체인: 판매된 단위 사용·인증서 null 설명 누락. 단일 파일 재작성 미완료, 기존 v34 유지. v35 unsigned/list price로 철회. market_call a2a 우승점포 호출 거절.