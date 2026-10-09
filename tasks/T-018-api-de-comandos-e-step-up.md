# T-018 — API de comandos com step-up, chave do aparelho e termo de ciência

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/11/2026) |
| Requisitos | REQ-CMD-001, REQ-CMD-004, REQ-CMD-006, REQ-CMD-007, REQ-CMD-008, REQ-CMD-010, REQ-CMD-016, REQ-CMD-017, REQ-CMD-019, REQ-CMD-024, REQ-DAD-025, REQ-SEG-012, REQ-SEG-013, REQ-SEG-014, REQ-SEG-015, REQ-SEG-016, REQ-SEG-029, REQ-API-014 |
| Invariantes | INV-01, INV-07, INV-08, INV-09, INV-10, INV-11 |
| Risco de revisão | N0 — comandos, step-up e autenticação; revisão adversarial de outro fornecedor + leitura humana linha a linha |
| Depende de | T-016 (domínio), T-017 (tabelas, helpers, `device_key_self` e `app.revoke_device_keys`), T-006 (Better Auth, contexto RLS com `userId`, harness HTTP de teste, `audit_log`, `memberships_for_user`), T-004 (registro de rotas e Problem Details), T-007 (handlers de vínculo e de cliente que recebem a guarda `RELAY_NOT_UNBLOCKED`) |
| Estimativa | 3 sessões de agente |
| Bloqueado por decisão | Nenhuma para o código. Bloqueio real continua travado por `COMMAND_BLOCK_SCOPE=none` e perfil `draft` até o G-CMD (REQ-NEG-011) |

## Objetivo

Expor no `api` todas as rotas de pedido de comando físico e de step-up: disponibilidade, desafio, pedido com assinatura da chave do aparelho (app) ou TOTP recente (console), consulta, cancelamento, registro de contingência, versão de política, termo de ciência, cadastro e revogação da chave do aparelho e step-up do console. Toda recusa síncrona sai com o `code` do catálogo de [09 §3](../docs/spec/09-api-e-contratos.md#3-erros-problem-details), grava `audit_log` `denied` e não cria linha em `command`. Todo pedido aceito sai 202 só depois do commit, já em READY ou ARMED, e emite `command.state` por SSE. Nenhum caminho de agente de IA, suporte ou cobrança chega a estas rotas com efeito.

## Contexto obrigatório

- [06 §2–§4, §10, §12, §14, §15](../docs/spec/06-comandos-e-bloqueio.md#2-disponibilidade); REQ-CMD-001, 004, 006–008, 010, 016, 017, 019.
- [08 §2 (TOTP, revogação), §3 (matriz), §6 (step-up), §11 (consentimento)](../docs/spec/08-identidade-e-seguranca.md#2-autenticação-better-auth); REQ-SEG-012 a 016, 029.
- [09 §3, §4, §5, §7, §9.2](../docs/spec/09-api-e-contratos.md#3-erros-problem-details); REQ-API-014.
- [Anexo B §10](../docs/anexos/B-juridico.md#10-rascunho-6--termo-de-ciência-do-bloqueio-uso-antes-da-revisão) (texto `block-terms-v1`).
- [T-016](T-016-dominio-de-comandos.md) (API do domínio) e [T-017](T-017-migration-f1-comandos.md) (tabelas, helpers).

## Escopo — fazer

1. Contratos Zod e entradas no registro de rotas para as 17 rotas da seção 1; códigos novos no catálogo (seção 4).
2. `packages/domain/src/commands/authorization.ts`: autorização pura por papel (seção 2).
3. `packages/domain/src/consent/render.ts` + texto `block-terms-v1.md` + `consent/manifest.json` + checagem do manifesto no `contracts:check`.
4. Módulo `commands` do `api`: handlers, `step-up.ts`, mapeamento de erros, leitura de evidência e enfileiramento via outbox.
5. Módulo `identity`: chave do aparelho, `/me/step-up`, revogação de sessões e ganchos de revogação da chave.
6. Serviço de consentimento (`apps/api/src/sva/consent.service.ts`): termo de ciência e revogação.
7. SSE `command.state` no hub de tempo real.
8. Variáveis `COMMAND_DISPATCH_ENABLED`, `COMMAND_BLOCK_SCOPE` e `COMMAND_BENCH_OPERATOR_ID` no `apps/api/src/config/env.ts` e no `.env.example`.
9. Guarda `RELAY_NOT_UNBLOCKED` (seção 3.10) nos handlers de encerramento de cliente, de fechamento de vínculo e de troca de rastreador.
10. Carência de 24 h da chave nova, aviso ao aparelho anterior e e-mail "Não fui eu" (seção 3.7).
11. Testes congelados em `tests/acceptance/T-018/`.

## Fora do escopo

- Despacho, confirmação, ARMED tick, retentativa e SMS (T-020). Telas (T-021).
- `POST /api/v1/me/consents` para `sva_referral` (T-026). Registro do termo pela central para titular sem app ([06 §12](../docs/spec/06-comandos-e-bloqueio.md#12-termo-de-ciência-do-bloqueio) item 4, proposta não aprovada).
- Rotas de ocorrência (T-025); aqui só se **lê** se há ocorrência `open` no veículo.
- Recusa imediata com `TELEMETRY_STALE` para rastreador `offline` ([09 §9.3](../docs/spec/09-api-e-contratos.md#93-erro-telemetry_stale-formato-reservado), proposta): o pedido segue a política de 06 (ARMED).

## Arquivos a criar/alterar

```
packages/contracts/src/routes/commands.ts
packages/contracts/src/routes/identity-step-up.ts
packages/contracts/src/routes/registry.ts                  (entradas novas)
packages/contracts/src/http/problem-codes.ts               (códigos e reasons novos)
packages/contracts/src/sse/command-state.ts
packages/contracts/src/consent/texts/block-terms-v1.md
packages/contracts/src/consent/manifest.json
packages/contracts/scripts/check-consent-manifest.ts       (chamado por contracts:check)
packages/domain/src/commands/authorization.ts
packages/domain/src/consent/render.ts
apps/api/src/commands/commands.module.ts
apps/api/src/commands/availability.handler.ts
apps/api/src/commands/challenges.handler.ts
apps/api/src/commands/create.handler.ts
apps/api/src/commands/read.handler.ts
apps/api/src/commands/cancel.handler.ts
apps/api/src/commands/contingency.handler.ts
apps/api/src/commands/policies.handler.ts
apps/api/src/commands/step-up.ts
apps/api/src/commands/evidence.repository.ts
apps/api/src/commands/problems.ts
apps/api/src/commands/relay-guard.ts                     (guarda RELAY_NOT_UNBLOCKED; chamada pelos handlers de frota da T-007: encerramento de cliente, device-assignments.close, troca de rastreador)
apps/api/src/identity/device-keys.handler.ts
apps/api/src/identity/step-up.handler.ts
apps/api/src/identity/revoke-sessions.handler.ts
apps/api/src/identity/device-key-revocation.ts            (ganchos de logout e senha)
apps/api/src/identity/device-key-not-me.handler.ts
apps/api/src/sva/consent.service.ts
apps/api/src/sva/block-terms.handler.ts
apps/api/src/stream/stream.hub.ts                          (evento command.state)
apps/api/src/config/env.ts
.env.example
tests/acceptance/T-018/world.ts
tests/acceptance/T-018/*.e2e.test.ts                       (9 arquivos, seção "Testes de aceite")
```

## Especificação detalhada

### 1. Rotas

Todas no registro de [09 §1](../docs/spec/09-api-e-contratos.md#1-contrato-primeiro), `auth: 'session'`, `aiTool` ausente (falso), validação estrita de entrada e saída.

| operationId | Método e caminho | Permissão | Corpo → resposta |
|---|---|---|---|
| `commands.availability` | `GET /api/v1/vehicles/{vehicleId}/command-availability` | `command.read` | → 200 seção 3.1 |
| `commands.challenge` | `POST /api/v1/vehicles/{vehicleId}/commands/challenges` | `command.execute` | `{ type: 'block'\|'unblock', reasonCode }` → 201 `{ challengeId, nonce, expiresAt, deviceKeyId, vehicleId, type, reasonCode }` |
| `commands.create` | `POST /api/v1/vehicles/{vehicleId}/commands` | `command.execute` | `Idempotency-Key` (UUID); `{ type, reasonCode, reason, stepUp }` → 202 `Command` + `Location` + `ETag: "<stateVersion>"` |
| `commands.get` | `GET /api/v1/commands/{commandId}` | `command.read` | → 200 `Command` + `events[]` + `attempts[]` + `ETag`; `rawResponse` só no escopo `operator` |
| `commands.list` | `GET /api/v1/vehicles/{vehicleId}/commands?cursor=&limit=` | `command.read` | → coleção por `created_at DESC, id` |
| `commands.cancel` | `POST /api/v1/commands/{commandId}/cancel` | `command.execute` | `If-Match: "<stateVersion>"` → 200 `Command` |
| `commands.contingency` | `POST /api/v1/vehicles/{vehicleId}/commands/contingency` | `command.execute` + equipe | `Idempotency-Key`; `{ type, reasonCode, sentAt, reason }` → 201 |
| `command-policies.list` | `GET /api/v1/command-policies` | `command_policy.manage` | → coleção de versões (maior primeiro) |
| `command-policies.create` | `POST /api/v1/command-policies` | `command_policy.manage` | `{ maxMovingCutKmh, evidenceMaxAgeS, armedTtlS, occurrenceArmedTtlS, allowAppBlock }` → 201 `{ version, … }` |
| `block-terms.get` | `GET /api/v1/tenants/{tenantId}/block-terms` | `consent.manage` | → 200 `{ currentTextVersion, text, accepted: { consentId, textVersion, grantedAt } \| null }` |
| `block-terms.accept` | `POST /api/v1/tenants/{tenantId}/block-terms` | `consent.manage` (só `tenant_owner` do tenant) | `{ textVersion }` → 201 `{ consentId, textVersion, grantedAt }` |
| `me.consents.list` / `me.consents.revoke` | `GET /api/v1/me/consents` · `DELETE /api/v1/me/consents/{consentId}` | sessão | → coleção · → 204 |
| `device-keys.create` | `POST /api/v1/device-keys` | `device_key.manage` | `{ publicKey, platform, label, userVerification }` → 201 `{ id, platform, label, createdAt }` |
| `device-keys.not-me` | `POST /api/v1/device-keys/not-me` | pública (token do e-mail) | `{ token }` → 204 (seção 3.7) |
| `device-keys.list` / `device-keys.revoke` | `GET /api/v1/me/device-keys` · `DELETE /api/v1/device-keys/{id}` | `device_key.manage` | → coleção · → 204 |
| `me.step-up` | `POST /api/v1/me/step-up` | sessão `console` | `{ code }` → 204 |
| `users.revoke-sessions` | `POST /api/v1/users/{userId}/revoke-sessions` | `user.manage_customer` ou `user.manage_staff` | → 204 |

`Command` (resposta) = campos de [09 §9.2](../docs/spec/09-api-e-contratos.md#92-post-apiv1vehiclesvehicleidcommands-f1): `id`, `vehicleId`, `deviceId`, `type`, `state`, `stateVersion`, `stateReason`, `cutPoint`, `ceilingKmh`, `policyVersion`, `requestedVia`, `requestedBy`, `reasonCode`, `createdAt`, `expiresAt`, `evidence: { evaluatedAt, lastFixAt, speedKmh }` (resumo de `evidence_snapshot`; `lastFixAt`/`speedKmh` `null` sem fix), mais `title` e `subtitle` de `stateTitle` (T-016) e `relay: { state, observedAt, badge }`.

### 2. Autorização por papel (`packages/domain/src/commands/authorization.ts`)

```ts
export type Role = 'operator_admin' | 'operator_agent' | 'installer' | 'search_team' | 'tenant_owner' | 'tenant_member'
export type ForbiddenReason = 'actor_not_human' | 'role_not_allowed' | 'app_block_disabled' | 'can_command_missing'
  | 'occurrence_required' | 'installer_window_expired' | 'reason_code_not_allowed' | 'wrong_channel'
export function authorizeCommandRequest(i: {
  actorType: 'user' | 'support' | 'ai_agent'; userId: string; roles: readonly Role[]; canCommand: boolean
  type: 'block' | 'unblock'; reasonCode: string; clientKind: 'app' | 'console'
  occurrenceOpen: boolean; assignment: { installedBy: string | null; validFrom: Date }; now: Date; allowAppBlock: boolean
}): { ok: true; stepUp: 'device_key' | 'console_totp' } | { ok: false; reason: ForbiddenReason }
export function authorizeCancel(i: { actorType: 'user' | 'support' | 'ai_agent'; userId: string; roles: readonly Role[];
  requestedBy: string; requestedByStaff: boolean }): boolean
```

Regras (06 §4.1, com a adoção de [10 §10](../docs/spec/10-apps-e-ux.md#10--apps-e-ux) item 5); o usuário com vários papéis passa se **algum** papel passar:

| Papel | Canal e step-up | Condição |
|---|---|---|
| `operator_admin`, `operator_agent` | `console` + `console_totp` | Sempre |
| `search_team` | `console` + `console_totp` | `occurrenceOpen` |
| `installer` | `app` + `device_key` | `reasonCode = 'installation_test'`, `assignment.installedBy = userId` e `now − validFrom ≤ 7.200 s` |
| `tenant_owner` | `app` + `device_key` | `allowAppBlock` |
| `tenant_member` | `app` + `device_key` | `allowAppBlock` e `canCommand` |
| `actorType ≠ 'user'` (suporte com grant, agente de IA) | — | Nunca (`actor_not_human`) |

`reasonCode` aceito do usuário: `theft_suspected`, `preventive`, `customer_request`, `recovered`, `other` e `installation_test` (só instalador). `pre_dispatch_fix` e `occurrence_interval` são do sistema → `reason_code_not_allowed`. Canal diferente do da linha → `wrong_channel`. `authorizeCancel`: equipe cancela qualquer comando; pedido da equipe (`requestedByStaff`) só é cancelado pela equipe; `tenant_owner` cancela pedidos de usuários do próprio cliente; demais só os próprios.

### 3. Fluxos

#### 3.1 Disponibilidade

Resposta: `{ block: { available, code, reason, cutPoint, ceilingKmh, effectText, warning }, unblock: { available, code, reason }, activeCommandId, relay: { state, observedAt, badge } }`. `code`/`reason` `null` quando disponível; senão o par do catálogo (seção 4). `effectText` = `effectText({ cutPoint, ceilingKmh, ttlMin })` com o TTL de ocorrência quando há ocorrência `open`. `warning` = "Um SMS de desbloqueio enviado às {HH:mm} ainda pode chegar e desfazer este bloqueio." quando existe `unblock` do veículo nas últimas 24 h com tentativa `sms` `sms_accepted` e estado final ≠ CONFIRMED ([06 §9](../docs/spec/06-comandos-e-bloqueio.md#9-desbloqueio-assimétrico) item 5). A disponibilidade inclui a autorização do usuário que pergunta: papel sem permissão → `available: false`, `code: 'FORBIDDEN'`, `reason` = `ForbiddenReason`. Pedida pelo app, usa o `created_at` da chave ativa do usuário como `deviceKeyCreatedAt`: chave com menos de 24 h → `block.available = false`, `code: 'DEVICE_KEY_COOLDOWN'`, `reason: 'device_key_cooldown'`, e `unblock` segue disponível.

#### 3.2 Desafio

1. Veículo visível no contexto (senão 404). Autorização (seção 2) com `clientKind = 'app'`; recusa → 403 `FORBIDDEN`.
2. Chave ativa do usuário (`device_key` com `revoked_at IS NULL`); sem chave → 403 `STEP_UP_REQUIRED`, `requiredMethod: 'device_key_registration'`.
3. INSERT em `command_challenge` com `nonce = randomBytes(32)`, `expires_at = now() + 60 s` (relógio do banco). Resposta com `nonce` base64url sem padding (43 caracteres). Limite: 10 desafios/min por usuário.

#### 3.3 Pedido (`POST /api/v1/vehicles/{vehicleId}/commands`)

Ordem fixa, numa transação `withContext` do usuário:

| # | Passo | Falha |
|---|---|---|
| 1 | `Idempotency-Key` UUID | 400 `IDEMPOTENCY_KEY_REQUIRED` |
| 2 | Veículo visível; vínculo primário aberto (`device_assignment` com `valid_to IS NULL`, `is_primary`) com rastreador | 404 / segue para a disponibilidade |
| 3 | `request_sha256` = SHA-256 do JSON canônico (RFC 8785) de `{ vehicleId, type, reasonCode, reason }`. Busca `command` por `(operator_id, tenant_id, idempotency_key)`: mesmo hash **e** mesmo `requested_by` → 202 com a representação atual e `Idempotent-Replayed: true`, sem consumir desafio | Hash ou usuário diferentes → 409 `IDEMPOTENCY_CONFLICT` |
| 4 | `authorizeCommandRequest` | 403 `FORBIDDEN` + `reason` |
| 5 | Step-up (seção 3.4). Recusa: consumo do desafio e `audit_log` `command.step_up` `denied` **commitados**; resposta 403 | 403 `STEP_UP_REQUIRED` / `STEP_UP_INVALID` |
| 6 | Console: `reason` com 10 a 500 caracteres | 422 `VALIDATION_FAILED`, `errors[0] = { path: 'reason', rule: 'min_length' }` |
| 7 | `checkBlockAvailability` / `checkUnblockAvailability` (T-016) com os dados do banco e do ambiente. `deviceKeyCreatedAt` = `created_at` da chave usada no step-up (`null` no console); `ceilingKmh` = `effectiveCeilingKmh(política, vehicle.kind)`; cliente encerrado: `tenantClosedAt` e `requestedByStaff` conforme a seção 3.9 | Seção 4 |
| 8 | Concorrência: comando de relé ativo do rastreador ([06 §4.3](../docs/spec/06-comandos-e-bloqueio.md#43-idempotência-e-concorrência) tabela) — `block` ativo antes de DISPATCHING + novo `unblock` → `transitionCommand` do `block` para CANCELLED `superseded_by_unblock` na mesma transação | 409 `COMMAND_ALREADY_ACTIVE` (`activeCommandId`) ou 409 `COMMAND_IN_FLIGHT` com `Retry-After` = segundos até `started_at + confirm_timeout_s` da tentativa em voo (mínimo 1) |
| 9 | Avaliação: `block` → `evaluateBlock` (seção 3.5); `unblock` → READY | — |
| 10 | `insertCommand` (T-017) com `policy_snapshot` (política vigente de `currentPolicy`), `evidence_snapshot`, `expires_at = computeExpiresAt(...)`, `occurrence_id` da ocorrência `open` (se houver) e `assignment_id`; `transitionCommand` REQUESTED → READY/ARMED com `actor = user:<id>`; `audit_log` `command.request` `success` com `correlation_id` | 23505 em `command_active_relay_key` (corrida) → 409 `COMMAND_ALREADY_ACTIVE` |
| 11 | COMMIT → 202 | — |

Toda recusa dos passos 4–9 grava `audit_log` `command.request` com `result = 'denied'` e `reason` = código, numa transação que commita, e não cria linha em `command`. O `api` não chama pg-boss nem o Traccar: o evento `command.state.changed.v1` da outbox (T-017) é o gatilho do despacho (T-020).

#### 3.4 Step-up

- **App (`stepUp.kind = 'device_key'`)**: sessão `clientKind = 'app'`; trecho normativo de [08 §6.3](../docs/spec/08-identidade-e-seguranca.md#63-assinatura-e-verificação): `SELECT … FROM app.command_challenge WHERE id = $1 FOR UPDATE`; confere `user_id` = sessão, `consumed_at IS NULL`, `expires_at ≥ now()`, `vehicle_id`/`type`/`reason_code` iguais ao caminho e ao corpo, `device_key_id` = `stepUp.deviceKeyId`, chave ativa do mesmo usuário; marca `consumed_at = now()` **antes** de verificar a assinatura; verifica ECDSA P-256/SHA-256 (DER, base64url) de `tracksys-cmd-v1|{challengeId}|{nonce}|{vehicleId}|{type}|{reasonCode}` (uuids minúsculos, nonce base64url). Motivos de 403 `STEP_UP_INVALID`: `challenge_expired`, `challenge_used`, `intent_mismatch`, `key_revoked`, `signature_invalid`. Desafio inexistente ou de outro usuário → `intent_mismatch`. Sucesso atualiza `device_key.last_used_at`.
- **Console (`stepUp.kind = 'console_totp'`)**: sessão `clientKind = 'console'`, 2FA ativo do usuário e `session.stepUpAt ≥ now() − 300 s`; senão 403 `STEP_UP_REQUIRED`, `requiredMethod: 'totp'`.
- 5 falhas de step-up do mesmo usuário em 10 min → job de e-mail ao usuário e item `step_up_failures` na fila da central (via outbox `security.step_up_failures.v1`, consumidor em T-020; aqui só o evento).

#### 3.5 Evidência no pedido (`evidence.repository.ts`)

```sql
SELECT p.source_event_id, p.assignment_id, p.fix_time, p.received_at, p.valid, p.lat_e7, p.lon_e7, p.speed_kmh_x10, p.flags
  FROM app.position p
 WHERE p.assignment_id = $1 AND p.fix_time >= now() - make_interval(secs => $2) AND p.fix_time <= now() + interval '120 seconds'
 ORDER BY p.fix_time DESC LIMIT 20;
```

`flags` decodificado pelo decodificador de bits de [05 §4.1](../docs/spec/05-ingestao-e-telemetria.md#41-flags-de-positionflags) (T-005). `processingMode`: `BACKFILL` → `backfill`; `REPROCESSED` → `reprocess`; senão `live`. Ignição e movimento vêm de `device_state` (`ignition`, `aux.statusAt`, `motion`, `last_contact_at`). `now` = `SELECT now()` da mesma transação. Perfil: `capability_profile` do rastreador lido com `parseCapabilityProfile` (T-016); `ProfileFacts` a partir de `capabilities.ignition`, `commands.stopped_speed_max_kmh_x10` (padrão 0), `normalization.stopped_interval_s` (padrão 300), `normalization.moving_interval_s` (padrão 30), `commands.position_request_type`. `vehicleKind` = `vehicle.kind` e `motionSource` = `device_state.aux.motionSource` (IGN_OFF só vale com `motionSource = 'fix'`, T-016).

#### 3.6 Cancelamento, contingência, política e termo

- **Cancelar**: sem `If-Match` → 428 `PRECONDITION_REQUIRED`; diferente de `state_version` → 412 `PRECONDITION_FAILED`; `authorizeCancel` falso → 403 `FORBIDDEN`; `reduceCommand(cancel)` sem transição → 409 `COMMAND_NOT_CANCELLABLE`; senão `transitionCommand` → CANCELLED `cancelled_by_user`, `audit_log` `command.cancel`.
- **Contingência**: só `operator_admin`/`operator_agent`, step-up `console_totp`, `reason` 10–500; `sentAt` > agora → 422 `VALIDATION_FAILED`; `sentAt < now() − 72 h` → 422 `CONTINGENCY_TOO_OLD`. Efeito ([06 §10](../docs/spec/06-comandos-e-bloqueio.md#10-contingência-por-sms-manual)): `insertCommand` com `state = 'UNKNOWN'`, `requested_via = 'contingency'`, `state_reason = 'contingency'`, `expires_at = created_at`; `insertAttempt` (`sms`, `seq = 1`, `started_at = sentAt`) e `finishAttempt` com `outside_platform`; `audit_log` `command.contingency`. O corpo nunca aceita texto de SMS (campo desconhecido → 422).
- **Política**: só `operator_admin` com `console_totp`; INSERT com `version = coalesce(max, 0) + 1` (23505 → relê e tenta 1 vez); campos fora das faixas de 06 §3.3 → 422 `VALIDATION_FAILED` (antes do banco); `audit_log` `command_policy.create`.
- **Termo**: `textVersion` casa `^block-terms-v(\d+)/(\d+)kmh$` com N = `CURRENT_BLOCK_TERMS_VERSION` e `kmh ≥` teto vigente e `≤ 40`; senão 422. Revoga o aceite ativo anterior do mesmo usuário e cliente e grava o novo (`text_sha256` do manifesto) na mesma transação; `audit_log` `command.block_terms.accept`. `GET` devolve o texto de `block-terms-v1.md` renderizado por `renderBlockTerms` com operadora, `kmh`, `armedTtlMin`, `occurrenceTtlMin` e a lista de veículos do cliente com o efeito de cada `cut_point` (`effectText`). Só o `tenant_owner` do tenant aceita; outro papel → 403. Revogação por `DELETE /api/v1/me/consents/{id}` (só o dono do consentimento) → `revoked_at`, 204.

#### 3.7 Chave do aparelho e sessões (módulo `identity`)

- `POST /api/v1/device-keys`: sessão `app` criada há ≤ 300 s, senão 403 `STEP_UP_REQUIRED` `requiredMethod: 'password'`. Valida com `createPublicKey({ key, format: 'der', type: 'spki' })`, `asymmetricKeyType === 'ec'`, `asymmetricKeyDetails.namedCurve === 'prime256v1'` e 91 bytes; senão 422 `VALIDATION_FAILED`. Todas as operações em `device_key` passam o `userId` da sessão a `withContext` (política `device_key_self`). Na mesma transação:
  - revoga a chave ativa anterior, insere a nova e grava `audit_log` `device_key.register`;
  - grava o evento `security.device_key_registered.v1` na outbox (`userId`, `previousKeyId`, `keyId`, `label`), cujo consumidor (T-020) envia push ao aparelho da chave anterior e enfileira o e-mail "Novo aparelho autorizado a bloquear" com o link "Não fui eu" (o token nasce no worker, em `auth.email_token`, `purpose = 'device_key_not_me'`, validade 72 h);
  - `pg_notify('auth_changed', '{"u":"<userId>"}')`.
- **Carência:** chave com `created_at` há menos de 24 h autoriza só `unblock`; `block` por essa chave responde 422 `COMMAND_NOT_ALLOWED` com `reason = device_key_cooldown`. A central bloqueia pelo console (TOTP) nesse período.
- `POST /api/v1/device-keys/not-me` (sem sessão; 5 tentativas/15 min por IP): confere o token por `token_sha256` (`purpose = 'device_key_not_me'`, `used_at IS NULL`, não vencido; senão 403 `STEP_UP_INVALID` `token_invalid`), marca `used_at`, revoga as sessões do usuário e a chave ativa por `app.revoke_device_keys` num contexto `operator` da operadora da membership ativa dele (`memberships_for_user`, T-006), com `audit_log` `device_key.not_me`; responde 204.
- `DELETE /api/v1/device-keys/{id}`: só a própria chave (`device_key_self`); `revoked_at = now()` onde `revoked_at IS NULL`, `audit_log` `device_key.revoke`, NOTIFY.
- `POST /api/v1/me/step-up`: verifica o TOTP pelo plugin `twoFactor` do Better Auth sem criar sessão nova [VALIDAR — T-006: função de verificação do plugin na versão fixada]; código de recuperação não vale; mesmo passo de 30 s reutilizado → 403 `STEP_UP_INVALID` `totp_reused`; grava `stepUpAt` na sessão; `audit_log` `auth.step_up`; 5 tentativas/15 min.
- `POST /api/v1/users/{userId}/revoke-sessions`: o alvo precisa ter membership na operadora do contexto (senão 404); revoga todas as sessões (Better Auth) e as chaves ativas por `app.revoke_device_keys(userId)`; NOTIFY; `audit_log` `auth.sessions_revoke` e `device_key.revoke`.
- Ganchos (`device-key-revocation.ts`): `sign-out` de sessão `app`, `change-password` e `reset-password` revogam as chaves do usuário com NOTIFY ([08 §6.5](../docs/spec/08-identidade-e-seguranca.md#65-revogação-da-chave)).

#### 3.8 SSE `command.state`

O hub ([07 §11](../docs/spec/07-alertas-e-tempo-real.md#11-tempo-real-get-apiv1stream-sse)) mantém `LISTEN command_changed` na conexão dedicada. Ao receber `{c, o, t, v}`, para cada conexão cujo escopo contém o veículo `v`, relê o comando sob o contexto RLS da conexão e envia `event: command.state` sem `id`, `data = { commandId, vehicleId, type, state, stateVersion, stateReason, at, title, subtitle }` ([09 §9.2](../docs/spec/09-api-e-contratos.md#92-post-apiv1vehiclesvehicleidcommands-f1)).

#### 3.9 Cliente encerrado e desbloqueio pela equipe

Com `tenant.status = 'closed'`, `checkUnblockAvailability` (T-016) recebe `tenantClosedAt = tenant.closed_at` e `requestedByStaff = true` só para `operator_admin` e `operator_agent` com `console_totp`. O vínculo primário elegível é o aberto ou o fechado com `valid_to ≥ now() − 30 dias` (a API passa `hasOpenPrimaryAssignment = true` nesse caso). Mais de 30 dias → 422 `COMMAND_NOT_ALLOWED` `tenant_closed`; `tenant_owner` e `search_team` → 403 (CT-CMD-024).

#### 3.10 Guarda `RELAY_NOT_UNBLOCKED` (`apps/api/src/commands/relay-guard.ts`)

`assertRelayUnblocked(client, { tenantId } | { assignmentId })` lança 409 `RELAY_NOT_UNBLOCKED` (nada muda, nenhum `audit_log` de sucesso) quando, para o vínculo ou para algum vínculo aberto do cliente:
- `device_state.relay_state ≠ 'unblocked'` (`unknown` conta como não desbloqueado, INV-03); ou
- o `block` mais recente do rastreador está em CONFIRMED, UNKNOWN ou em estado ativo.

Os handlers chamam a guarda **antes** de qualquer escrita: encerramento de cliente (04 §9.2), `device-assignments.close` e a troca de rastreador no mesmo veículo (T-007). O console mostra "Desbloquear antes" (T-021). A guarda só lê, sob a RLS do contexto.

### 4. Catálogo de erros usado (dono: [09 §3](../docs/spec/09-api-e-contratos.md#3-erros-problem-details))

| Condição (domínio) | HTTP | `code` | Extensão |
|---|---|---|---|
| `CUT_POINT_MISSING` | 422 | `CUT_POINT_MISSING` | — |
| `PROFILE_NOT_HOMOLOGATED` | 422 | `PROFILE_NOT_HOMOLOGATED` | — |
| `RELAY_UNSUPPORTED`, `BLOCK_SCOPE_DISABLED`, `BLOCK_TERMS_MISSING`, `TENANT_CLOSED`, `NO_PRIMARY_DEVICE` (veículo sem vínculo primário aberto), `DEVICE_KEY_COOLDOWN` | 422 | `COMMAND_NOT_ALLOWED` | `reason`: `relay_unsupported`, `block_scope_disabled`, `block_terms_missing`, `tenant_closed`, `no_primary_device`, `device_key_cooldown` |
| Encerrar cliente ou fechar vínculo com relé não desbloqueado (seção 3.10) | 409 | `RELAY_NOT_UNBLOCKED` | — |
| `COMMAND_DISPATCH_DISABLED` (só `block`) | 503 | `COMMAND_DISPATCH_DISABLED` | — |
| `TELEMETRY_STALE` (reservado, 09 §9.3) | — | — | Não adotado nesta tarefa. |
| Autorização | 403 | `FORBIDDEN` | `reason` = `ForbiddenReason` |
| Contingência > 72 h | 422 | `CONTINGENCY_TOO_OLD` | `maxAgeS: 259200` |

Acrescente ao `problem-codes.ts` os códigos e `reason`s da tabela acima; a tabela de 09 §3 já os lista, e o PR confere a igualdade.

### 5. Variáveis de ambiente (`apps/api/src/config/env.ts`)

| Variável | Regra | Padrão no `.env.example` |
|---|---|---|
| `COMMAND_DISPATCH_ENABLED` | `true` \| `false` | `true` |
| `COMMAND_BLOCK_SCOPE` | `parseBlockScope` (T-016): `none` \| `all` \| `pilot:<uuid>[,<uuid>]` | `none` |
| `COMMAND_BENCH_OPERATOR_ID` | uuid ou vazio | vazio |

Mudança de `COMMAND_BLOCK_SCOPE` em produção só por deploy com revisão N0 ([06 §2](../docs/spec/06-comandos-e-bloqueio.md#2-disponibilidade) item 1).

## Testes de aceite (congelados)

Harness HTTP da T-006 (`api` em processo, `inject`), Postgres real, sem `vi.mock` de banco. Chaves P-256 geradas no teste com `generateKeyPairSync('ec', { namedCurve: 'prime256v1' })` e assinatura `sign('sha256', …, { key, dsaEncoding: 'der' })`. Desafio vencido = linha inserida pelo teste com `created_at = now() − 61 s` e `expires_at = now() − 1 s`; TOTP antigo = `stepUpAt` ajustado em `auth.session` pelo `DATABASE_URL_ADMIN`. Os blocos completos são escritos no PR do cartão a partir deste plano; nomes e asserções abaixo são normativos.

`tests/acceptance/T-018/world.ts` reaproveita `seedCommandWorld` da T-017 e acrescenta: perfil `j16-gt06` v2 `homologated` (relay `yes`, seção `commands` completa, `relay_state_reported = 'yes'`, `homologation_ref` e `evidence_ref` de teste) em R1; política v1 da Alfa com teto 40 e `allow_app_block = true`; aceite `block-terms-v1/40kmh` de `dono.a1`; fixes `live` de V1 a 23,5 km/h com `fix_time = now() − 9 s`; usuários `busca.alfa` (`search_team`) e `inst.alfa` (`installer`) com 2FA; variáveis `COMMAND_BLOCK_SCOPE=all`, `COMMAND_DISPATCH_ENABLED=true`.

`availability.e2e.test.ts` — `describe('T-018 disponibilidade — CT-CMD-001, CT-CMD-019')`:
- `cut_point NULL: block 422 CUT_POINT_MISSING, 0 linhas em command, 1 audit_log denied` (V3 de A2 com `dono.a2`).
- `perfil draft fora da bancada → 422 PROFILE_NOT_HOMOLOGATED`; `homologated com relay unknown → 422 COMMAND_NOT_ALLOWED reason relay_unsupported`.
- `COMMAND_BLOCK_SCOPE=none → 422 COMMAND_NOT_ALLOWED reason block_scope_disabled`.
- `perfil suspended com relay yes: unblock → 202`.
- `sem block_terms → 422 COMMAND_NOT_ALLOWED reason block_terms_missing; aceite v1/20kmh e política nova de 40 → 422 até novo aceite; política nova de 10 → disponível; aceite revogado → block 422 e unblock 202`.
- `GET command-availability devolve effectText com 'inclusive em movimento até 40 km/h', cutPoint fuel_pump, ceilingKmh 40, activeCommandId null`.
- `moto (vehicle.kind motorcycle) com política de 40 km/h: ceilingKmh 0 e effectText com 'só é enviado com a moto parada'`.
- `chave K2 cadastrada às 10:00Z: block às 11:00Z → 422 COMMAND_NOT_ALLOWED reason device_key_cooldown (0 linhas em command, 1 audit_log denied); unblock às 11:00Z → 202; block no console com TOTP → 202; block a partir de 10:00Z do dia seguinte → disponível`.
- `A1 encerrado há 20 dias com relé blocked: operator_agent com TOTP e motivo pede unblock → 202; há 31 dias → 422 reason tenant_closed; tenant_owner e search_team → 403` (CT-CMD-024).

`create.e2e.test.ts` — `describe('T-018 pedido com step-up e idempotência — CT-CMD-008, CT-SEG-013, CT-SEG-014, CT-API-014')`:
- `desafio 201: nonce de 43 caracteres base64url e expiresAt = createdAt + 60 s`; `dono.a2 pede desafio para V1 → 404`; `sem chave ativa → 403 STEP_UP_REQUIRED device_key_registration`.
- `assinatura válida: 202, Location /api/v1/commands/{id}, ETag "2", state READY, command_event REQUESTED→READY, evidence.speedKmh 23.5`.
- `desafio vencido → 403 STEP_UP_INVALID challenge_expired e 0 linhas em command`.
- `desafio usado com outra Idempotency-Key → 403 challenge_used`.
- `assinatura feita para V2 enviada para V1 → 403 STEP_UP_INVALID (intent_mismatch ou signature_invalid) e o desafio fica consumido`.
- `assinatura com a chave de dono.a2 → 403`.
- `mesmo pedido 3 vezes com a mesma Idempotency-Key → 202, 202, 202 (2 últimos com Idempotent-Replayed: true), mesmo id, 1 desafio consumido`.
- `mesma chave com type diferente → 409 IDEMPOTENCY_CONFLICT`.
- `sem Idempotency-Key → 400 IDEMPOTENCY_KEY_REQUIRED`.
- `block ARMED em V1 e novo block → 409 COMMAND_ALREADY_ACTIVE com activeCommandId`.
- `console: TOTP há 5 min 01 s → 403 STEP_UP_REQUIRED totp; reason "furto" → 422; reason de 49 caracteres com TOTP há 4 min 59 s → 202` (CT-SEG-015).

`authorization.e2e.test.ts` — `describe('T-018 autorização por papel — CT-CMD-007, CT-CMD-017')`:
- `tenant_member sem can_command → 403 FORBIDDEN can_command_missing; com can_command e allow_app_block = false → 403 app_block_disabled`.
- `installer em vínculo aberto por ele há 2 h 01 min → 403 installer_window_expired; há 1 h 59 min com installation_test → 202`.
- `search_team sem ocorrência open → 403 occurrence_required; com ocorrência → 202 e expires_at = created_at + 1.800 s`.
- `platform_admin com grant de suporte → 403; ator ai_agent → 403; em ambos 0 linhas em command`.
- `tenant_owner cancelando comando pedido pela central → 403`.
- `rota de comando com aiTool: true faz o boot do api falhar` (teste do registro).

`concurrency.e2e.test.ts` — `describe('T-018 concorrência — CT-CMD-010')`:
- `2 pedidos block simultâneos com chaves diferentes: exatamente 1 → 202 e o outro → 409 COMMAND_ALREADY_ACTIVE com o id do primeiro`.
- `block ARMED + unblock: o block vira CANCELLED superseded_by_unblock e o unblock READY na mesma transação (mesmo xmin ou mesmo created_at de transação)`.
- `block AWAITING_CONFIRMATION com tentativa iniciada há 20 s e confirm_timeout_s 60 + unblock → 409 COMMAND_IN_FLIGHT com Retry-After: 40`.
- `cancelar ARMED com If-Match "2" → 200 CANCELLED; If-Match "1" → 412; sem If-Match → 428; READY com tentativa → 409 COMMAND_NOT_CANCELLABLE`.

`contingency-policy.e2e.test.ts` — `describe('T-018 contingência e política — CT-CMD-016, CT-CMD-004')`:
- `operator_agent registra SMS de bloqueio enviado às 02:10:00Z (sentAt 50 min antes): command UNKNOWN contingency, command_attempt sms/outside_platform com started_at = sentAt, audit_log command.contingency`.
- `tenant_owner → 403; sentAt de 4 dias antes → 422 CONTINGENCY_TOO_OLD; corpo com campo smsText → 422`.
- `política: maxMovingCutKmh 41 → 422; 40 com TOTP → 201 version 2; o próximo comando tem policy_snapshot.version = 2; operator_agent → 403`.

`device-keys.e2e.test.ts` — `describe('T-018 chave do aparelho e step-up — CT-SEG-012, CT-SEG-015, CT-SEG-016')`:
- `sessão app de 3 min: cadastra K2, K1 recebe revoked_at, audit_log device_key.register e o evento security.device_key_registered.v1 na outbox (com previousKeyId = K1)`.
- `link "Não fui eu" (token válido): 204, sessões e K2 revogadas, audit_log device_key.not_me; o mesmo token de novo → 403 STEP_UP_INVALID token_invalid; token vencido (72 h + 1 s) → 403`.
- `contexto da Beta com userId de admin.beta não revoga nem reativa K1 (0 linhas; revoked_at preenchido não muda: 23514)`.
- `sessão de 6 min → 403 STEP_UP_REQUIRED password; chave P-384 → 422`.
- `/me/step-up com código válido → 204 e stepUpAt gravado; o mesmo código no mesmo passo → 403 STEP_UP_INVALID totp_reused`.
- `revoke-sessions pela central às 21:10:10: chave revogada; assinatura de desafio anterior com a sessão antiga → 401; com sessão nova → 403 STEP_UP_INVALID`.
- `logout do app revoga a chave nova`.

`relay-guard.e2e.test.ts` — `describe('T-018 desbloqueio nunca fica sem caminho — CT-CMD-024, CT-DAD-025')`:
- `V1 com block CONFIRMED: operator_admin encerra A1 → 409 RELAY_NOT_UNBLOCKED, tenant.status e vínculo inalterados; fecha o vínculo de V1 para trocar o rastreador → 409`.
- `V1 com relay_state unknown (sem observação) → 409; com unblock CONFIRMED e relay_state unblocked → encerramento segue`.
- `block em REQUESTED, ARMED ou DISPATCHING de V1 → 409`.

`terms-consent.e2e.test.ts` — `describe('T-018 termo de ciência — CT-SEG-029 (parte do termo)')`:
- `GET block-terms traz o texto com 'Lider' substituído, '40 km/h', '5 minutos' e a lista de veículos com o efeito de cada cut_point`.
- `POST com block-terms-v1/40kmh → 201; consent com text_sha256 igual ao do manifesto`.
- `textVersion block-terms-v2/40kmh (inexistente) → 422; agente.alfa → 403`.
- `alterar block-terms-v1.md faz o check do manifesto falhar` (roda o script com arquivo temporário).

`sse.e2e.test.ts` — `describe('T-018 SSE command.state')`:
- `pedido aceito em V1 gera event command.state para a conexão de dono.a1 em ≤ 2 s, com state READY e stateVersion 2`.
- `conexões de dono.a2 e admin.beta não recebem o evento em 5 s`.

## Comandos de verificação

```bash
pnpm db:up && pnpm db:migrate
pnpm --filter @tracksys/domain test
pnpm --filter @tracksys/domain mutation          # authorization.ts entra no escopo do Stryker
pnpm contracts:check                             # OpenAPI, clientes e manifesto de consentimento
pnpm test:acceptance tests/acceptance/T-018
pnpm verify
```

## Definição de pronto

- [ ] 17 rotas no registro, com permissão, validação de entrada e saída e caso de isolamento em `scope-fixtures.ts` (REQ-API-018).
- [ ] Nenhuma recusa síncrona cria linha em `command`; toda recusa grava `audit_log` `denied`.
- [ ] Desafio consumido antes de verificar a assinatura e mesmo na falha.
- [ ] Nenhuma chamada a Traccar, emnify, pg-boss ou e-mail dentro do handler (REQ-ARQ-008): e-mail e despacho saem por outbox/job.
- [ ] `pnpm check:boundaries` verde (`billing` e `commands` sem import mútuo).
- [ ] Códigos novos documentados em 09 §3 no mesmo PR; `RELAY_NOT_UNBLOCKED` aplicado nos 3 handlers de frota da T-007.
- [ ] Operações em `device_key` sempre com `userId` no `withContext`.
- [ ] PR `feat(commands): api de comandos com step-up (T-018)`, N0, plano no PR, revisão cruzada registrada.

## Decisões já tomadas

| Dúvida provável | Resposta |
|---|---|
| 1. Rota do desafio: `/command-challenges` (06 §14) ou `/commands/challenges` (08, 09, 10)? | `/api/v1/vehicles/{vehicleId}/commands/challenges` (três capítulos, incluindo o dono do contrato). |
| 2. Pedido aceito responde 201 (06) ou 202 (09, 08)? | 202, com `Idempotent-Replayed: true` na repetição ([09 §9.2](../docs/spec/09-api-e-contratos.md#92-post-apiv1vehiclesvehicleidcommands-f1), REQ-API-014, CT-SEG-014). |
| 3. Códigos com prefixo `COMMAND_` (ex.: `COMMAND_CUT_POINT_MISSING`), `STEP_UP_CHALLENGE_EXPIRED`, `IDEMPOTENCY_KEY_REUSED`… de 06? | Valem os de 09 §3 (tabela da seção 4 deste cartão): `CUT_POINT_MISSING` e `PROFILE_NOT_HOMOLOGATED` sem prefixo, `STEP_UP_INVALID` com `reason`, `IDEMPOTENCY_CONFLICT` (409). Veículo sem vínculo primário aberto: `COMMAND_NOT_ALLOWED` com `reason` `no_primary_device` (o domínio devolve `NO_PRIMARY_DEVICE`, nome de 09 §9.1). O app e o console decidem pelo `code` + `reason`. |
| 4. O hash de idempotência inclui o veículo? | Sim: `{ vehicleId, type, reasonCode, reason }`. Sem o veículo, a mesma chave em V1 e V3 do mesmo cliente devolveria o comando errado. |
| 5. Indisponível depois de step-up válido consome o desafio? | Sim. A ordem é idempotência → autorização → step-up → disponibilidade. O app checa a disponibilidade antes de pedir o desafio. |
| 6. `search_team` usa chave do aparelho (06) ou TOTP (10)? | TOTP do console: a equipe de busca usa o console responsivo ([10 §10](../docs/spec/10-apps-e-ux.md#10--apps-e-ux) item 5); exige 2FA ativo. |
| 7. `tenant_owner` desbloqueia pelo app com `allow_app_block = false`? | Não. 06 §4.1 condiciona bloquear e desbloquear pelo app a `allow_app_block`; nesse caso o desbloqueio é pela central. |
| 8. `COMMAND_BLOCK_SCOPE` e `COMMAND_BENCH_OPERATOR_ID` são propostas de 06 §2. Implemento? | Sim: CT-CMD-001 depende de `COMMAND_BLOCK_SCOPE=none`, e o G-CMD depende de `pilot:` e da operadora de bancada. Padrão seguro: `none` e vazio. O fundador aprova a adoção no PR do cartão. |
| 9. Evidência no pedido usa o fix de `device_state`? | Não. Só linhas de `position` do vínculo (têm `received_at` e flags de modo). Veículo parado com compactação fica ARMED e o worker junta fixes ao vivo dos eventos (06 §3.1, T-020). |
| 10. De onde vem `processingMode` de uma linha de `position`? | Das flags: `BACKFILL` → `backfill`, `REPROCESSED` → `reprocess`, demais `live`. |
| 11. O `api` enfileira o despacho no pg-boss? | Não. O `transitionCommand` grava `command.state.changed.v1` na outbox; o relay cria o job do consumidor `commands.dispatch` (T-020). Assim o job só existe se o commit existir. |
| 12. Recusa grava `audit_log` mesmo com rollback do pedido? | Sim: o handler encerra a transação do pedido sem gravar `command` e commita só `audit_log` (e o consumo do desafio, se houver). |
| 13. Como a carência de 24 h da chave nova se aplica? | `checkBlockAvailability` (T-016) recebe `deviceKeyCreatedAt`; chave com menos de 24 h autoriza só `unblock` (422 `COMMAND_NOT_ALLOWED` `device_key_cooldown`). O console (TOTP) não tem chave de aparelho e não tem carência. |
| 14. O que o link "Não fui eu" faz? | Revoga as sessões do usuário e a chave ativa, grava `audit_log` e consome o token (uso único, 72 h, só o hash no banco). O token nasce no worker, em `auth.email_token` com `purpose = 'device_key_not_me'` (a T-017 amplia o CHECK). |
| 15. Quem aplica `RELAY_NOT_UNBLOCKED`? | Esta tarefa: `relay-guard.ts` é chamada pelos handlers de encerramento de cliente, fechamento de vínculo e troca de rastreador (T-007). A guarda só lê e roda antes de qualquer escrita. |
| 16. Como a equipe desbloqueia veículo de cliente encerrado? | `operator_admin` ou `operator_agent` com TOTP e motivo, em até 30 dias do encerramento (`tenantClosedAt`); depois disso, 422 `tenant_closed`. `tenant_owner` e `search_team` recebem 403. |
| 17. Qual teto vale para moto? | O efetivo, 0 (`effectiveCeilingKmh`, T-016): a disponibilidade, o `policy_snapshot` e o termo mostram o teto efetivo, não o da política. |
