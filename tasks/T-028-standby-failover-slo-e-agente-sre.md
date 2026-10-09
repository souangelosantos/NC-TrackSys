# T-028 — Standby, failover com fencing, SLO, status page e agente SRE de diagnóstico

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/11/2026; SLO medido desde 01/12/2026) |
| Requisitos | REQ-NEG-012 (itens G1-3 e G1-6 do gate G1; G1-2 vem da T-024), REQ-OPS-010 a REQ-OPS-015, REQ-OPS-018, REQ-OPS-019, REQ-OPS-021, REQ-OPS-022, REQ-OPS-024, REQ-SEG-028, REQ-QLD-017, REQ-ARQ-015, REQ-DAD-012 (só o teste de desempenho CT-DAD-012; os índices nascem na T-005 e na T-008), REQ-ING-016 (backfill automático; a reconciliação é da T-015), REQ-ING-021 (métricas Prometheus; a sonda de atraso da ingestão é da T-013) |
| Invariantes | INV-01, INV-05, INV-11 |
| Risco de revisão | N0 |
| Depende de | T-003, T-013, T-005 e T-015 (backfill, métricas e CT-DAD-012) |
| Estimativa | 3 sessões de agente |
| Bloqueado por decisão | DEC-12, DEC-13 |
| Status | Resumido — DoR pendente |

## Objetivo

Levar a operação ao nível do contrato: VM standby com réplica por streaming, failover com fencing (parar a primária pela API da OCI antes de promover), ex-primária que nunca volta como primária, minuto ruim medido por sonda externa e latência de alerta, status page, gateway de incidentes fora das VMs, agente SRE de IA só com diagnóstico de leitura no F1, auditoria de operação e runbook do plantonista ensaiado.

## Contexto obrigatório

[13 — Infra e operação](../docs/spec/13-infra-e-operacao.md); [05 §12 e §17](../docs/spec/05-ingestao-e-telemetria.md) (backfill e métricas da ingestão); [04 §7.3](../docs/spec/04-dominio-e-dados.md) (consulta canônica do histórico); [ADR-005](../docs/adr/ADR-005-infra-oracle-always-free.md); [ADR-010](../docs/adr/ADR-010-operacao-assistida-por-ia.md); [Anexo C](../docs/anexos/C-operacional.md)

## Escopo — fazer

1. Script de failover com pré-condições e fencing.
2. Uptime Kuma na standby, UptimeRobot e cálculo de minuto ruim.
3. Gateway de incidentes (Cloudflare Worker) e agente SRE somente leitura, com avaliação antes de ligar (REQ-QLD-017).
4. Ensaio de contingência com o plantonista.
5. Backfill automático da ingestão (REQ-ING-016, parte F1) [ADOTADO NA v2.0]: o job `ingest.reconcile` projeta em modo `backfill` o que faltar na inbox (flag 8, sem push nem efeito, INV-05) e o CLI de backfill aceita até 7 dias; a reconciliação, as consultas e o relatório ficam com a T-015.
6. Métricas Prometheus da ingestão (REQ-ING-021, parte F1): exposição da porta `Metrics` no `api` e no `worker` com as métricas e limiares de aviso e page de [05 §17](../docs/spec/05-ingestao-e-telemetria.md) (CT-ING-021); a sonda de atraso no Uptime Kuma/Pushover já vem da T-013.
7. Teste de desempenho CT-DAD-012 [ADOTADO NA v2.0]: 30 dias sintéticos de 300 veículos (~2,5 M posições), `EXPLAIN` da consulta canônica de [04 §7.3](../docs/spec/04-dominio-e-dados.md) com varredura do `*_pkey` em no máximo 2 partições e ≤ 100 ms.

## Fora do escopo

- Cardápio de ações automáticas do agente SRE (F2).
- Agente de suporte (F2).

## Para completar o DoR

1. Especificação detalhada (tabelas com SQL, rotas, jobs e textos) a partir dos capítulos citados.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-028/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 6 respostas.
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
5. Com os itens 5 a 7 do escopo (acrescentados na v2.0), a estimativa pode passar de 3 sessões: se passar, dividir o cartão ([14 §4](../docs/spec/14-qualidade-e-processo-ia.md)) antes do DoR, com backfill, métricas e CT-DAD-012 num cartão próprio.
