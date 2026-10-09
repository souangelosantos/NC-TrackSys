# ADR-009 — Retenção quente/frio: 90 dias Postgres + Parquet mensal com DuckDB; compactação de heartbeat parado; sem Timescale

**Status:** Aceito em 07/10/2026

## Contexto

- A Lider guarda histórico por 1 ano e a polícia já pediu histórico. Retenção canônica de posições: 12 meses.
- Com 3.000 veículos: ~1,47 milhão de posições/dia sem compactação (~537 milhões/ano). A ~300 bytes por linha seriam ~161 GB/ano, que não cabem com folga no volume de 100 GB da VM.
- Consulta a histórico com mais de 90 dias é rara (polícia, disputa). Mapa e histórico do app usam dias recentes.
- A v1.1 usava TimescaleDB para compressão, o que amarra hospedagem e licença.

## Decisão

1. **Compactação de parado:** posição parada só é gravada se o deslocamento for > 50 m ou a cada 30 min; os demais heartbeats só atualizam `device_state.last_contact_at` ([05](../spec/05-ingestao-e-telemetria.md)).
2. **Linha compacta** em `position`: lat/lon em `int4` × 10⁷, velocidade em `int2` (km/h × 10), sem JSONB por linha além de `extra` opcional. ~100 bytes por linha com índice → ~27–40 GB/ano no mês 12.
3. **Quente (90 dias):** `position` particionada por dia em `fix_time`, com partições criadas 7 dias à frente e sem partição DEFAULT (posição fora da janela aceita vai para quarentena). DDL de partição só por função SECURITY DEFINER do `tracksys_owner`, chamada pelo `worker` ([04](../spec/04-dominio-e-dados.md)).
4. **Frio (9 meses):** Parquet mensal com compressão zstd no Oracle Object Storage, chave `cold/positions/operator_id=<uuid>/year=AAAA/month=MM/positions.parquet`, mais manifesto JSON (linhas, SHA-256, intervalo de `fix_time`). As colunas `operator_id` e `tenant_id` são mantidas (INV-06).
5. **Exportação:** job do `worker` no dia 5 de M+2, às 06:00 UTC, exporta o mês M por operadora com DuckDB (`memory_limit=256MB`, `threads=1`, extensões instaladas na imagem). O prazo fica ≥ 35 dias após o fim do mês, além da janela de 30 dias de atraso aceito. Verificação: contagem de linhas do Parquet igual à do Postgres e hash gravado no manifesto.
6. **Expurgo quente:** uma partição diária só é removida quando tem mais de 90 dias **e** o mês dela foi exportado e verificado.
7. **Expurgo frio:** o arquivo do mês M é apagado quando o último dia do mês completa 12 meses. Se um `legal_hold` cobrir a operadora e o mês, o `worker` grava antes `cold/holds/<legal_hold_id>/positions.parquet` só com o veículo e o período retidos e então apaga o arquivo do mês.
8. **Consulta fria:** "solicitar relatório" no app ou no console cria um pedido sob RLS. O `worker` lê com DuckDB só o prefixo `operator_id=` do pedido e filtra `tenant_id`, `vehicle_id` e intervalo; o resultado (CSV ou PDF com hash) vai para o object storage com link temporário ([08](../spec/08-identidade-e-seguranca.md)).
9. O Traccar guarda só 7 dias ([ADR-003](ADR-003-traccar-borda-de-protocolos.md)). Envelope bruto da inbox: 7 dias; identidade de dedupe e `payload_sha256`: 90 dias ([05](../spec/05-ingestao-e-telemetria.md)). [ADOTADO NA v2.0: o job de retenção é da T-027 (F1); no F0 o envelope bruto fica além de 7 dias, risco aceito R-21 de [15](../spec/15-decisoes-riscos-premissas.md) §3.]
10. Primeiro ciclo completo (export, verificação e expurgo) operando até 31/01/2027 (F1).

## Alternativas consideradas

- **TimescaleDB com compressão.** Por que não: compressão sob licença TSL, ausente em parte dos Postgres gerenciados; amarra a hospedagem (achado da v1.1).
- **Citus columnar.** Por que não: mais uma extensão na imagem ARM, com ganho só perto do gatilho de 150 GB.
- **Tudo quente por 12 meses.** Por que não: cabe no início, mas WAL, backup, réplica e restore crescem 4×, e o RTO piora.
- **Histórico só no Traccar.** Por que não: schema alheio, sem RLS e sem dono por cliente.
- **Data warehouse gerenciado (BigQuery, Athena).** Por que não: custo por consulta e dados fora da infra; DuckDB lê Parquet localmente sem custo.

## Consequências

**Positivas**
- ~7–10 GB de posições quentes no mês 12; backup e restore rápidos.
- Histórico antigo barato; nenhuma extensão de licença restrita.
- Exportação por operadora facilita portabilidade e encerramento de contrato.

**Negativas**
- Histórico com mais de 90 dias não é instantâneo: vira relatório assíncrono.
- DuckDB não aplica RLS: o caminho frio é N0 e tem teste com 2 operadoras ([04](../spec/04-dominio-e-dados.md), [08](../spec/08-identidade-e-seguranca.md)).
- Retenção efetiva do frio fica entre 12 e 13 meses, porque o arquivo é mensal.
- O object storage passa do limite gratuito ([ADR-005](ADR-005-infra-oracle-always-free.md)).
- A compactação reduz a resolução de veículo parado a um ponto a cada 30 min sem deslocamento.

## Gatilho de revisão

- Posições quentes > 150 GB ([ADR-002](ADR-002-postgres-unico-fila-barramento.md)) ou disco do volume > 70%.
- Mais de 5% das consultas de histórico pedindo dados com mais de 90 dias durante 1 mês [PREMISSA] → ampliar a janela quente.
- p95 do relatório frio de 1 veículo por 30 dias > 60 s [PREMISSA].
- Mudança legal ou contratual de retenção (DEC-08, DEC-15).

## Relacionados

- INV-03, INV-05, INV-06, INV-07.
- [04](../spec/04-dominio-e-dados.md) (particionamento, funções de partição); [05](../spec/05-ingestao-e-telemetria.md) (compactação, janela); [08](../spec/08-identidade-e-seguranca.md) e [Anexo B](../anexos/B-juridico.md) (retenção, legal hold, evidências); [13](../spec/13-infra-e-operacao.md) (object storage).
- [ADR-002](ADR-002-postgres-unico-fila-barramento.md), [ADR-005](ADR-005-infra-oracle-always-free.md).
