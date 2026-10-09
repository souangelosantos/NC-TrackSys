# T-029 — Console do F1: carteira completa, atendimento, marca, cercas e alertas novos

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–30/11/2026; REQ-ALR-024 na quinzena 01–15/11) |
| Requisitos | REQ-UX-024, REQ-UX-027, REQ-UX-028, REQ-ALR-020, REQ-ALR-021, REQ-ALR-022, REQ-ALR-023, REQ-ALR-024, REQ-UX-032 |
| Invariantes | INV-03, INV-07 |
| Risco de revisão | N1; trechos N0: a migration das tabelas de cerca e `ticket` (RLS, FK composta, `catalog-allowlist.json`) segue o rito N0 (AGENTS.md) |
| Depende de | T-007, T-008, T-011, T-012, T-013 (Pushover) |
| Estimativa | 3 sessões de agente |
| Bloqueado por decisão | nenhuma |
| Status | Resumido — DoR pendente |

## Objetivo

Completar a paridade da central com o tracker-net: carteira (clientes, veículos, rastreadores, chips, instalações, usuários), marca dinâmica editável com checagem de contraste, registro de atendimento com contexto, fila de alertas com reconhecimento e os alertas do F1 (bateria baixa, excesso de velocidade, cerca virtual e crítico sem reconhecimento), com as telas de cerca no app.

## Contexto obrigatório

[10 — Apps e UX](../docs/spec/10-apps-e-ux.md) (console F1); [07 — Alertas](../docs/spec/07-alertas-e-tempo-real.md) (alertas do F1)

## Escopo — fazer

1. Tabelas de cerca e `ticket`.
2. Telas do console por papel.
3. Regras dos novos alertas no motor (T-011).
4. Crítico chega à central (REQ-ALR-024): `sos`, `power_cut` e `signal_lost_moving` ao vivo disparam Pushover de emergência (`retry = 60`, `expire = 1800`) para todo membro com `membership.on_call = true` e chave Pushover cadastrada (segredo cifrado), além do push ao titular; o recibo do Pushover vira `alert.ack` com o ator; a C08 toca alarme contínuo até o reconhecimento.
5. Filtros da C02 "Sem comunicação há > 24 h" e "> 7 dias", ordenados pelo contato mais antigo, com exportação CSV e `audit_log` `export.create` (REQ-UX-032).

## Fora do escopo

- Cobrança (T-023).
- Importador (T-024).

## Para completar o DoR

1. Lacunas a fechar: DDL de `geofence`, regras de cerca e `ticket` (RLS forçada, FK composta); coluna `membership.on_call` e cadastro da chave Pushover (rota, cifra); contrato do webhook de recibo do Pushover e mapeamento para `alert.ack`; regras de `battery_low`, `speeding` e `geofence` com limiares e CT em blocos; wireframes da C02, C07 e C08; texto do termo de participação do F0 (pânico avisa só o titular).
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-029/`, congelados antes da implementação.
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md#5-dor-e-dod)).
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
