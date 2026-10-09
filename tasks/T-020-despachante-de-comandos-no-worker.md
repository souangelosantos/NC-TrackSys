# T-020 — Despachante de comandos no worker

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/11/2026) |
| Requisitos | REQ-CMD-011, REQ-CMD-013, REQ-CMD-014, REQ-ARQ-016 |
| Invariantes | INV-05, INV-08, INV-10, INV-11 |
| Risco de revisão | N0 |
| Depende de | T-016, T-017, T-018, T-005 |
| Estimativa | 2–3 sessões de agente |
| Bloqueado por decisão | DEC-01 (só o SMS automático de desbloqueio; sem ela, SMS manual) |
| Status | Resumido — DoR pendente |

## Objetivo

Executar no `worker` os comandos aceitos pela API: gravar `command_attempt` antes de qualquer I/O, enviar ao Traccar (`POST /api/commands/send`, `noQueue` quando suportado), correlacionar a resposta, confirmar pelo ack homologado e pelo `relay_state` observado, levar a `UNKNOWN` sem repetir bloqueio, reconciliar após reinício e aplicar a assimetria do desbloqueio (retentativa GPRS a cada 60 s, até 5; SMS via emnify após 2 min sem confirmação).

## Contexto obrigatório

[06 — Comandos](../docs/spec/06-comandos-e-bloqueio.md) §§7–12; [03 §4](../docs/spec/03-arquitetura.md); [T-016](T-016-dominio-de-comandos.md) (regras puras que este cartão só executa)

## Escopo — fazer

1. Jobs pg-boss `commands.dispatch` (`singletonKey` = id do comando) e `commands.armed.tick` (+ filho `position_request`), nomes de [06 §3 e §7](../docs/spec/06-comandos-e-bloqueio.md), com lock por dispositivo e atualização condicional por `state_version`. O job nasce do relay da outbox (`command.state.changed.v1`, T-017/T-018); o `api` nunca enfileira.
2. Adaptador do Traccar com timeout de 10 s e mapeamento de resposta para eventos do domínio (T-016).
3. Correlação de `commandResult` e de `relay_state`; resposta tardia anexada como evidência sem mudar estado final.
4. Reconciliação no boot: `DISPATCHING`/`AWAITING_CONFIRMATION` sem resposta viram `UNKNOWN` com alerta ao operador.
5. Desbloqueio: retentativas e fallback SMS (adaptador emnify com driver nulo enquanto DEC-01 estiver aberta).
6. `COMMAND_DISPATCH_ENABLED` e `COMMAND_BLOCK_SCOPE` respeitados (REQ-ARQ-016).
7. Consumidor da outbox `security.step_up_failures.v1` (a T-018 só grava o evento): job de e-mail ao usuário e item `step_up_failures` na fila da central.

## Fora do escopo

- Regras de política e máquina de estados (T-016).
- Rotas HTTP e step-up (T-018).
- UX no app e no console (T-021).

## Para completar o DoR

1. Especificação detalhada (tabelas com SQL, rotas, jobs e textos) a partir dos capítulos citados.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-020/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 6 respostas.
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
