# T-030 — Publicação nas lojas, versão mínima do app, E2E e carga

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 16–30/11/2026) |
| Requisitos | REQ-UX-014, REQ-API-016, REQ-API-017, REQ-QLD-012, REQ-QLD-013 |
| Invariantes | INV-04 |
| Risco de revisão | N1 |
| Depende de | T-009, T-010, T-012 |
| Estimativa | 2 sessões de agente |
| Bloqueado por decisão | DEC-03, DEC-04 |
| Status | Resumido — DoR pendente |

## Objetivo

Publicar o app no Google Play (após 14 dias de teste fechado) e na App Store, com versão mínima suportada e aviso de atualização, política de depreciação de rotas, suíte E2E do console (Playwright) e do app (integration_test) e teste de carga com k6 (100 msg/s por 15 min e rajada de 10×).

## Contexto obrigatório

[10](../docs/spec/10-apps-e-ux.md) (distribuição e estabilidade); [09](../docs/spec/09-api-e-contratos.md) (versão mínima e depreciação); [14](../docs/spec/14-qualidade-e-processo-ia.md) (E2E e carga)

## Escopo — fazer

1. Checklist de loja (declarações de dados, exclusão de conta, ícones, textos).
2. Endpoint de versão mínima e tela de atualização obrigatória.
3. Scripts k6 e relatório de carga.

## Fora do escopo

- App dedicado por operadora (F2).

## Para completar o DoR

1. Especificação detalhada (tabelas com SQL, rotas, jobs e textos) a partir dos capítulos citados.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-030/`, congelados antes da implementação.
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md)).
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
