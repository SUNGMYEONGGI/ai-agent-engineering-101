RULES
Round 4 최신 체인 기준 수수료는 market_fee 1%와 network_fee 420 credits이다. 판매자 수령액은 P-1%-420, 구매자 부담은 P+1%+420으로 계산한다. 구매자 tx_hash·fee_tx_hash를 clearing /api/settle에 제출하고 503이면 동일 요청을 재시도한다. 공급 quote는 정확히 송금하고 120초 내 제출한다. 보관료는 원가 시간당 0.5%, 48시간마다 등급 하락. 실제 inventory 등급만 표시하고 확인된 환불만 처리한다.

NOW
2026-11-25: G0026722f B 2개 4200 credits, A 3개 4500 credits, 48시간 보증. B 우선 판매. 잔액 약 4,985,554 credits, 다음 lot storage_due 199. 추가 매입은 24시간 판매량 확인 후 결정. 최신 chain은 credit_wei 1000000000000000, network_fee 420, market_fee 1%를 공시했다.

FAILED
이전 메모의 고정 네트워크 수수료 210은 최신 /api/chain과 불일치하여 폐기했다. 앞으로 pay_guard와 가격 산정은 매번 최신 체인·clearing 수수료를 확인한다.