RULES
Round 4: 판매 수령액은 P-1%-네트워크 수수료이며 실제 chain/clearing 값을 확인한다. 공급은 POST /api/supply에서 quote를 받고 정확한 pay를 120초 내 실행한 뒤 quote와 tx_hash를 제출한다. 재고 unit·grade만 checkout에 사용하고 48시간마다 등급 하락, 보관료가 발생한다.

NOW
2026-11-25 15:xx KST: 최근 원장에서 Hermes Shop 정산 0건. 잔액 4,982,123 credits. 기존 키친타올 홀더 6개(A 4/B 2). 생수 G00b8acf0 2개 quote(q-de6635ec49928285) 총 6091을 시도했으나 아직 매입하지 못함.

FAILED
공급 API에 SKU 없이 요청해 400 unknown sku. 생수 quote를 받은 뒤 pay_guard가 chain_unavailable을 두 번 반환해 송금·공급 제출을 하지 못함. 같은 quote 재시도에도 실패했으므로 chain 복구 전 추가 송금은 중단한다.