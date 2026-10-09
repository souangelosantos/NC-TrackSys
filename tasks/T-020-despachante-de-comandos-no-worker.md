# T-020 — Despachante de comandos no worker

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/11/2026) |
| Requisitos | REQ-CMD-011, REQ-CMD-013, REQ-CMD-014, REQ-CMD-023, REQ-ARQ-016, REQ-ALR-025, REQ-DAD-027 (`episode_key` único para tipos `command_%`) |
| Invariantes | INV-05, INV-08, INV-10, INV-11 |
| Risco de revisão | N0 |
| Depende de | T-016, T-017, T-018, T-005 |
| Estimativa | 2–3 sessões de agente |
| Bloqueado por decisão | DEC-01 (só o SMS automático de desbloqueio; sem ela, SMS manual) |
| Status | Resumido — DoR pendente |

## Objetivo

Executar no `worker` os comandos aceitos pela API: gravar `command_attempt` antes de qualquer I/O, enviar ao Traccar (`POST /api/commands/send`, `noQueue` quando suportado), correlacionar a resposta, confirmar pelo ack homologado e pelo `relay_state` observado, levar a `UNKNOWN` sem repetir bloqueio, reconciliar após reinício e aplicar a assimetria do desbloqueio (retentativa GPRS a cada 60 s, até 5; SMS via emnify após 2 min sem confirmação).

## Contexto obrigatório

[06 — Comandos](../docs/spec/06-comandos-e-bloqueio.md) §§7–12; [03 §4](../docs/spec/03-arquitetura.md#4-módulos-do-monólito-e-donos-de-tabelas); [T-016](T-016-dominio-de-comandos.md) (regras puras que este cartão só executa)

## Escopo — fazer

1. Jobs pg-boss `commands.dispatch` (`singletonKey` = id do comando) e `commands.armed.tick` (+ filho `position_request`), nomes de [06 §3 e §7](../docs/spec/06-comandos-e-bloqueio.md#3-política-de-bloqueio), com lock por dispositivo e atualização condicional por `state_version`. O job nasce do publicador da outbox (`outbox-publisher`, `runPublisherOnce`, T-005) a partir de `command.state.changed.v1` (T-017/T-018); o `api` nunca enfileira.
2. Adaptador do Traccar com timeout de 10 s e mapeamento de resposta para eventos do domínio (T-016).
3. Correlação de `commandResult` e `relay_state` ([06 §8.1](../docs/spec/06-comandos-e-bloqueio.md#81-confirmação)); evidência tardia ao vivo leva UNKNOWN a CONFIRMED/FAILED com ator `system:reconcile` ([06 §8.3](../docs/spec/06-comandos-e-bloqueio.md#83-evidência-tardia), CT-CMD-013); evidência não ao vivo só anota `command_event`; `commandResult` sem comando de relé ativo ou em UNKNOWN abre `command_outside_platform` ([06 §8.3](../docs/spec/06-comandos-e-bloqueio.md#83-evidência-tardia) item 4).
4. Reconciliação no boot e a cada 1 min pela tabela de [06 §8.4](../docs/spec/06-comandos-e-bloqueio.md#84-reconciliação-após-reinício): block, `position_request` e `set_interval` em `DISPATCHING` com tentativa `pending` viram `UNKNOWN` (`worker_restart`); unblock segue o §9; `READY` é reenfileirado; `AWAITING_CONFIRMATION` no prazo é reagendado; `ARMED` vencido → `EXPIRED`, ou `FAILED` (`ARMED>FAILED`) se o block já tem tentativa.
5. Desbloqueio: retentativas e fallback SMS (adaptador emnify com driver nulo enquanto DEC-01 estiver aberta).
6. `COMMAND_DISPATCH_ENABLED` e `COMMAND_BLOCK_SCOPE` respeitados (REQ-ARQ-016). Ao avaliador (T-016) passam `vehicleKind`, `motionSource` e `ProfileFacts.movingIntervalS`, lidos do perfil e do `device_state`.
7. Alertas `command_unknown` (critical, não desativável) e `command_failed` (warning) em transição ao vivo (REQ-ALR-025) e `command_outside_platform` (critical, com page ao fundador) quando chega `commandResult` sem comando da plataforma ([13](../docs/spec/13-infra-e-operacao.md), REQ-OPS-025).
8. Consumidor da outbox `security.step_up_failures.v1` (a T-018 só grava o evento): job de e-mail ao usuário e item `step_up_failures` na fila da central.
9. Consumidor de `security.device_key_registered.v1`: push ao aparelho da chave anterior e e-mail "Novo aparelho autorizado a bloquear" com token `device_key_not_me` de 72 h em `auth.email_token` (T-017, T-018).

## Fora do escopo

- Regras de política e máquina de estados (T-016).
- Rotas HTTP e step-up (T-018).
- UX no app e no console (T-021).

## Para completar o DoR

1. Lacunas a fechar: nomes e payload Zod dos jobs `commands.dispatch` e `commands.armed.tick`; campos de `POST /api/commands/send` e de `commandResult` no Traccar [VALIDAR na bancada da T-002]; a tabela de reconciliação de 06 §8.4 e a de retentativa do unblock (06 §9) convertidas em CT-CMD com relógio injetado; emnify com driver nulo (DEC-01); textos de alerta de `command_unknown`, `command_failed` e `command_outside_platform`.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-020/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md#5-dor-e-dod)).
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
