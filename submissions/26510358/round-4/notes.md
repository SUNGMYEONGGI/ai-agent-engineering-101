RULES
2026-11-24: /api/chain은 credit_wei=1000000000000000, market_fee_bps=100, network_fee_credits=420을 반환. clearing 카드의 판매자 수령 공식은 price-floor(price*1%)-210, 구매자는 shop에 그 금액을 보내고 시장에 2m을 별도 송금. 공급은 POST /api/supply에서 quote 후 정확한 pay transfer, 120초 내 quote 제출. 재고 storage는 시간당 원가 0.5%, goods는 48시간마다 등급 하락.

NOW
2026-11-24: 시장 가입은 GitHub /join 및 claim code가 필요해 401. 현재 공개 catalog에는 커튼 G000f6cda와 소파 G00327e80을 재고 0으로 게시. 도매 공급창은 현재 닫힘; 다음 opens_at 1795518201, closes_at 1795518381. 수요 중앙값은 소파 568080, 침대 344640, 커튼류 34740.

FAILED
상점 토큰 없이 /api/inventory는 401. /api/join shop은 GitHub 선행 인증 요구로 실패. 실제 restock·settlement·pay는 인증과 재고 확인 전 보류. clearing 503이면 동일 settlement body 재전송.