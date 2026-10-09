# T-031 — Relatório de unidade econômica e conta de armazenamento

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/12/2026) |
| Requisitos | REQ-NEG-003, REQ-NEG-004, REQ-DAD-024, REQ-QLD-019 |
| Invariantes | INV-07, INV-12 |
| Risco de revisão | N1; trechos N0: a migration da tabela de custos (RLS, `catalog-allowlist.json`) segue o rito N0 (AGENTS.md) |
| Depende de | T-023, T-027 |
| Estimativa | 1–2 sessões de agente |
| Bloqueado por decisão | nenhuma |
| Status | Resumido — DoR pendente |

## Objetivo

Medir se o negócio fecha: relatório mensal em CSV por operadora e consolidado (assinaturas, split, indicações, custos de infraestrutura e de IA), alerta quando a infraestrutura passar de 10% da receita por 2 meses, conta de armazenamento medida (bytes por posição) e métricas do processo de desenvolvimento.

## Contexto obrigatório

[01 §5–8](../docs/spec/01-visao-e-negocio.md#5-modelo-de-receita); [04 §8](../docs/spec/04-dominio-e-dados.md#8-retenção-e-armazenamento); [14](../docs/spec/14-qualidade-e-processo-ia.md) (métricas do processo)

## Escopo — fazer

1. Tabela de custos da plataforma e job mensal idempotente.
2. Consulta de `pg_total_relation_size` por partição.

## Fora do escopo

- Contabilidade e emissão fiscal.

## Para completar o DoR

1. Lacunas a fechar: DDL da tabela de custos da plataforma (RLS forçada, entrada na allowlist, migration N0), de `operator_price` e `platform_cost` conforme 04 §8, ou o motivo de não existirem; colunas e fórmulas do CSV mensal; limiar de 10% da receita por 2 meses; consulta de `pg_total_relation_size` por partição; métricas do `process:report` (REQ-QLD-019); CT em blocos.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-031/`, congelados antes da implementação.
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md#5-dor-e-dod)).
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
