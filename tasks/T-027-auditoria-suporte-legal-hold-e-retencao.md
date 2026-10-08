# T-027 — Auditoria, acesso de suporte, legal hold e retenção quente/frio

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/12/2026 (retenção operando até 31/01/2027)) |
| Requisitos | REQ-DAD-014, REQ-DAD-015, REQ-DAD-016, REQ-DAD-019, REQ-DAD-023, REQ-SEG-011, REQ-SEG-027 |
| Invariantes | INV-05, INV-06, INV-07 |
| Risco de revisão | N0 |
| Depende de | T-005, T-006 |
| Estimativa | 3 sessões de agente |
| Bloqueado por decisão | DEC-15 (anonimização) |
| Status | Resumido — DoR pendente |

## Objetivo

Fechar a base jurídica no código: acesso de suporte da Versix só por `platform_support_grant` temporário e auditado, legal hold que congela o expurgo, pacote de evidências (PDF + CSV com SHA-256), exportação mensal das partições de posição com mais de 90 dias para Parquet verificado no object storage, consulta fria sob demanda com DuckDB e encerramento de cliente com tombstone e anonimização.

## Contexto obrigatório

[04 §8–9](../docs/spec/04-dominio-e-dados.md); [08](../docs/spec/08-identidade-e-seguranca.md) (autoridades, Marco Civil); [ADR-009](../docs/adr/ADR-009-retencao-quente-frio.md); [Anexo B §12](../docs/anexos/B-juridico.md)

## Escopo — fazer

1. Tabelas `legal_hold` e `platform_support_grant`.
2. Job de exportação com contagem e hash antes do DROP PARTITION, respeitando legal hold.
3. Pacote de evidências gerado pelo worker, com registro de quem exportou.

## Fora do escopo

- Texto jurídico final (DEC-08).

## Para completar o DoR

1. Especificação detalhada (tabelas com SQL, rotas, jobs e textos) a partir dos capítulos citados.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-027/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 6 respostas.
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
