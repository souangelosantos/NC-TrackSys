# T-027 — Auditoria, acesso de suporte, legal hold e retenção quente/frio

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/12/2026; retenção quente/frio operando até 31/01/2027) |
| Requisitos | REQ-DAD-013, REQ-DAD-014, REQ-DAD-015, REQ-DAD-016, REQ-DAD-019, REQ-DAD-023, REQ-ING-018, REQ-SEG-011, REQ-SEG-027 |
| Invariantes | INV-01, INV-05, INV-06, INV-07 |
| Risco de revisão | N0 |
| Depende de | T-005, T-006, T-012 (tipo `push_token` da retenção) |
| Estimativa | 3 sessões de agente |
| Bloqueado por decisão | DEC-15 (anonimização) |
| Status | Resumido — DoR pendente |

## Objetivo

Fechar a base jurídica no código: acesso de suporte da Versix só por `platform_support_grant` temporário e auditado, legal hold que congela o expurgo, pacote de evidências (PDF + CSV com SHA-256), exportação mensal das partições de posição com mais de 90 dias para Parquet verificado no object storage, consulta fria sob demanda com DuckDB e encerramento de cliente com tombstone e anonimização.

## Contexto obrigatório

[04 §4.4, §8–9](../docs/spec/04-dominio-e-dados.md) (`app.retention_purge` e prazos da §8.1); [05 §14](../docs/spec/05-ingestao-e-telemetria.md) (retenção da inbox); [08](../docs/spec/08-identidade-e-seguranca.md) (autoridades, Marco Civil); [ADR-009](../docs/adr/ADR-009-retencao-quente-frio.md); [Anexo B §12](../docs/anexos/B-juridico.md)

## Escopo — fazer

1. Tabelas `legal_hold` e `platform_support_grant`.
2. Job de exportação com contagem e hash antes do DROP PARTITION, respeitando legal hold.
3. Pacote de evidências gerado pelo worker, com registro de quem exportou.
4. Retenção da inbox, da outbox e das filas (REQ-ING-018, REQ-DAD-013) [ADOTADO NA v2.0: adiado do F0; até lá o payload da inbox fica além de 7 dias]: função `app.retention_purge(p_kind, p_batch)` de [04 §4.4](../docs/spec/04-dominio-e-dados.md) (`SECURITY DEFINER`, entrada na chave `securityDefiner` da allowlist, CAT-07) com os tipos `outbox`, `push_token`, `access_log` e `idempotency_record` (este com a política tipo G `idempotency_record_owner_all`); job diário `ingest.retention` da inbox (payload NULL após 7 dias com `payload_sha256` mantido, linha apagada após 90 dias, `pending` nunca sai; CT-ING-018 e CT-DAD-013); jobs de expurgo de outbox publicada (3 dias), tokens sem uso (60 dias), `idempotency_record` vencido (de hora em hora) e jobs concluídos do pg-boss (2 dias). Os tipos `billing_event_payload` e `referral_location` ([12](../docs/spec/12-cobranca-e-svas.md)) entram com a T-023 e a T-026, que estendem a função.

## Fora do escopo

- Texto jurídico final (DEC-08).

## Para completar o DoR

1. Especificação detalhada (tabelas com SQL, rotas, jobs e textos) a partir dos capítulos citados.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-027/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md)).
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
5. Com a retenção (item 4 do escopo, acrescentado na v2.0), a estimativa pode passar de 3 sessões: se passar, dividir o cartão ([14 §4](../docs/spec/14-qualidade-e-processo-ia.md)) antes do DoR, com a retenção num cartão próprio.
