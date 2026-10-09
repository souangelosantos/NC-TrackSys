# T-028 — Standby, failover com fencing, SLO e status page

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/11/2026; SLO medido desde 01/12/2026; gateway de incidentes e agente SRE na T-034, 01–15/12) |
| Requisitos | REQ-NEG-012 (itens G1-3 e G1-6 do gate G1; G1-2 vem da T-024), REQ-OPS-010 a REQ-OPS-015, REQ-OPS-021, REQ-OPS-022, REQ-OPS-024, REQ-OPS-025, REQ-SEG-028, REQ-SEG-030, REQ-ARQ-015, REQ-ING-016 (backfill automático; a reconciliação é da T-015), REQ-ING-021 (métricas Prometheus; a sonda de atraso da ingestão é da T-013) |
| Invariantes | INV-01, INV-05, INV-11 |
| Risco de revisão | N0 |
| Depende de | T-003, T-013, T-005 e T-015 (backfill e métricas) |
| Estimativa | 3 sessões de agente |
| Bloqueado por decisão | DEC-12 |
| Status | Resumido — DoR pendente |

## Objetivo

Levar a operação ao nível do contrato: VM standby com réplica por streaming, failover com fencing (parar a primária pela API da OCI antes de promover), ex-primária que nunca volta como primária, minuto ruim medido por sonda externa e latência de alerta, status page, monitor de DNS, auditoria de operação e runbook do plantonista ensaiado. O gateway de incidentes e o agente SRE de diagnóstico são da [T-034](T-034-gateway-de-incidentes-e-agente-sre.md).

## Contexto obrigatório

[13 — Infra e operação](../docs/spec/13-infra-e-operacao.md); [05 §12 e §17](../docs/spec/05-ingestao-e-telemetria.md#12-queda-prolongada-reconciliação-e-backfill) (backfill e métricas da ingestão); [ADR-005](../docs/adr/ADR-005-infra-oracle-always-free.md); [Anexo C](../docs/anexos/C-operacional.md)

## Escopo — fazer

1. Script de failover com pré-condições e fencing.
2. Uptime Kuma na standby, UptimeRobot e cálculo de minuto ruim.
3. Monitor `dns-gps` no Kuma (REQ-OPS-025, REQ-SEG-030): resolve `gps.<domínio>` a cada 60 s e faz page de prioridade 2 se o A não for `ip-svc` nem `ip-sby`; Traccar com `registration=false` e só `TRACCAR_API_USER` comandando; token de DNS da Cloudflare restrito a `gps`, `api` e `app`.
4. Ensaio de contingência com o plantonista.
5. Backfill automático da ingestão (REQ-ING-016, parte F1): o job `ingest.reconcile` projeta em modo `backfill` o que faltar na inbox (flag 8, sem push nem efeito, INV-05) e o CLI de backfill aceita até 7 dias; a reconciliação, as consultas e o relatório ficam com a T-015.
6. Métricas Prometheus da ingestão (REQ-ING-021, parte F1): exposição da porta `Metrics` no `api` e no `worker` com as métricas e limiares de aviso e page de [05 §17](../docs/spec/05-ingestao-e-telemetria.md#17-métricas-de-ingestão) (CT-ING-021); a sonda de atraso no Uptime Kuma/Pushover já vem da T-013. Quando o `api` passar a emitir `ingest_pending_count`, `ingest_pending_oldest_age_seconds` e `ingest_last_received_age_seconds`, tirá-las do textfile da sonda `tracksys-ingest-lag` (T-013) e levar a sonda para o Uptime Kuma da standby. O modo `--recent` da T-015 continua como conferência manual.

7. Checklist do fundador (08 §10 ameaça 13, REQ-SEG-030): FIDO2 na conta Cloudflare, DNSSEC e bloqueio de transferência do domínio; token de DNS restrito a `gps`, `api` e `app`.

## Fora do escopo

- Gateway de incidentes, agente SRE e CT-DAD-012 (T-034).
- Cardápio de ações automáticas do agente SRE (F2).
- Agente de suporte (F2).

## Para completar o DoR

1. Lacunas a fechar: script de failover com as pré-condições e a chamada de fencing da OCI [VALIDAR flags]; configuração da réplica e do limite de WAL; fórmula do minuto ruim e da latência de alerta com CT em blocos; página de status; monitor `dns-gps` e a lista de IPs permitidos; nomes das métricas e limiares de 05 §17; runbook do plantonista; respostas da DEC-12 e da DEC-13.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-028/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md#5-dor-e-dod)).
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).

