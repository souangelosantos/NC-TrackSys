# T-023 — Cobrança Asaas: vínculo, webhooks, inadimplência, PIX no app e split

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/11/2026) |
| Requisitos | REQ-COB-001 a REQ-COB-016, REQ-SEG-022, REQ-UX-021, REQ-NEG-001, REQ-NEG-002 |
| Invariantes | INV-05, INV-07, INV-09, INV-11, INV-12 |
| Risco de revisão | N0 |
| Depende de | T-006, T-007, T-017 (`operator_secret` e cifra) |
| Estimativa | 3 sessões de agente |
| Bloqueado por decisão | DEC-06, DEC-14 |
| Status | Resumido — DoR pendente |

## Objetivo

Integrar a conta Asaas da operadora sem migrar a cobrança: chave cifrada, webhook autenticado e idempotente, sincronização e reconciliação diária, inadimplência como `suspended_commercial` (nunca bloqueio), fatura com PIX copia-e-cola e QR no app, split de R$ 3,90 por cobrança de rastreamento para a carteira da Versix e fechamento mensal em `platform_fee`.

## Contexto obrigatório

[12 — Cobrança e SVAs](../docs/spec/12-cobranca-e-svas.md) (parte de cobrança); [01 §5](../docs/spec/01-visao-e-negocio.md) (preço e veículo ativo); [08](../docs/spec/08-identidade-e-seguranca.md) (segredos e webhook)

## Escopo — fazer

1. Tabelas `billing_account`, `billing_customer`, `invoice`, `platform_fee` e preço por operadora, com RLS forçada e FK composta.
2. Adaptador Asaas com fake em `packages/testkit` e nomes de eventos marcados [VALIDAR] até o teste em sandbox.
3. Telas de fatura e PIX no app; lista de inadimplência no console.
4. Dinheiro sempre em centavos inteiros na fronteira.
5. Rota da chave Asaas da operadora e job `secrets.rewrap` sobre `operator_secret` (tabela e cifra AES-256-GCM entregues pela T-017, que deixa os dois para este cartão).

## Fora do escopo

- Emissão de NFS-e própria (só a opção do Asaas, REQ-COB-015).
- Cobrança de parceiros de SVA (T-026).

## Para completar o DoR

1. Especificação detalhada (tabelas com SQL, rotas, jobs e textos) a partir dos capítulos citados.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-023/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md)).
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
