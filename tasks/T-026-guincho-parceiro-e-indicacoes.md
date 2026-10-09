# T-026 — Guincho parceiro: botão no app, indicação, consentimento e relatório mensal

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 16–30/11/2026) |
| Requisitos | REQ-SVA-001 a REQ-SVA-009, REQ-UX-022 |
| Invariantes | INV-05, INV-07, INV-11, INV-12 |
| Risco de revisão | N0 |
| Depende de | T-009, T-017 (tabela `consent`), T-023 |
| Estimativa | 2 sessões de agente |
| Bloqueado por decisão | DEC-05 (repartição; enquanto aberta, vale a proposta do capítulo 12) |
| Status | Resumido — DoR pendente |

## Objetivo

Validar o modelo de receita com o parceiro que a Lider já tem: botão "Chamar guincho" que abre o WhatsApp ou o telefone do parceiro com localização e placa, registro da indicação só por ação humana, consentimento por parceiro e finalidade, transparência de indicação remunerada, antifraude, conversão confirmada manualmente e relatório mensal com repartição congelada em snapshot.

## Contexto obrigatório

[12 — Cobrança e SVAs](../docs/spec/12-cobranca-e-svas.md) (parte de SVA); [Anexo B §11](../docs/anexos/B-juridico.md#11-rascunho-7--consentimento-por-parceiro-e-finalidade) (consentimento)

## Escopo — fazer

1. Tabelas `partner` e `referral`, e a FK composta de `consent.partner_id` para `partner` (a `consent` nasce na T-017 sem essa FK).
2. Botão no app que nunca bloqueia o contato, mesmo com a API fora do ar.
3. Relatório mensal por operadora e consolidado para a Versix.

## Fora do escopo

- Portal ou API do parceiro (F2).
- Assistência 24h, revisões e gestão de custos (F2).

## Para completar o DoR

1. Lacunas a fechar: DDL de `partner` e `referral` e a FK composta de `consent.partner_id`; rotas e telas (botão "Chamar guincho", relatório mensal); regra de antifraude e de conversão manual; snapshot da repartição (aguarda a DEC-05: proposta de 75% para quem fecha a parceria, pendente); CT-SVA em blocos.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-026/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md#5-dor-e-dod)).
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
