# T-016 — Domínio de comandos puro: avaliador, máquina de estados e textos

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/11/2026) |
| Requisitos | REQ-CMD-002, REQ-CMD-003, REQ-CMD-005, REQ-CMD-009, REQ-CMD-012, REQ-CMD-015, REQ-CMD-018, REQ-CMD-021, REQ-QLD-010 |
| Invariantes | INV-03, INV-05, INV-08, INV-09, INV-10, INV-12 |
| Risco de revisão | N0 — revisão adversarial por agente de outro fornecedor + leitura humana linha a linha |
| Depende de | T-002 (perfil J16 `draft` e capturas), T-004 (`packages/contracts`, `packages/domain`, `packages/testkit`) |
| Estimativa | 3 sessões de agente |
| Bloqueado por decisão | DEC-02 (padrão: perfil sem seção `commands` completa = bloqueio indisponível); DEC-07 (padrão: teto 0 km/h até a Lider gravar a versão com 40) |

## Objetivo

Criar em `packages/domain/src/commands/` toda a regra de comando físico como código puro (sem IO, relógio por parâmetro): validação de evidência, avaliação por `cut_point`, disponibilidade do bloqueio, máquina de estados com redutor de eventos e efeitos, assimetria de desbloqueio, decisão de confirmação e textos obrigatórios. API (T-018) e worker (T-020) só executam o que este pacote decide. Ao final, as propriedades P-CMD-1 e P-CMD-2 rodam com 1.000 execuções em todo PR e o Stryker barra score de mutação abaixo de 80%.

## Contexto obrigatório

- [06 — Comandos e bloqueio](../docs/spec/06-comandos-e-bloqueio.md) §2, §3, §5, §7, §8, §9, §13.4, §15, §16 (REQ-CMD-002, 003, 005, 009, 012, 015, 018, 021) e §17.
- [10 — Apps e UX](../docs/spec/10-apps-e-ux.md) §7 (títulos por estado e motivos do ARMED).
- [14 — Qualidade](../docs/spec/14-qualidade-e-processo-ia.md) §9 (propriedades e mutação) e REQ-QLD-010.
- [03 §12](../docs/spec/03-arquitetura.md) (regras de dependência de `packages/domain`).

## Escopo — fazer

1. Tipos e constantes de comando em `packages/contracts/src/commands/enums.ts` e o schema do evento `command.state.changed.v1`.
2. Schema de armazenamento da seção `capabilities.commands` do perfil e a função `parseCapabilityProfile` (§13.4 de 06).
3. Em `packages/domain/src/commands/`: `types.ts`, `evidence.ts`, `policy.ts`, `state-machine.ts`, `texts.ts`, `index.ts`, com a API exata da "Especificação detalhada".
4. Testes unitários e de propriedade (P-CMD-1, P-CMD-2) em `packages/domain/test/` e os testes congelados em `tests/acceptance/T-016/`.
5. Stryker (runner Vitest) em `packages/domain`, script `mutation`, job `mutation` no CI de PR e no noturno.

## Fora do escopo

- Migration, tabelas e qualquer SQL (T-017). Rotas HTTP (T-018). Jobs, Traccar, emnify, push (T-020). Telas (T-021).
- Kit de bancada `homologation:check` e runbook do G-CMD (T-022).
- Implementar trava no dispositivo (`block_type_gated`): o campo existe no schema, o uso fica para depois do S07 [VALIDAR — DEC-02].
- Qualquer leitura de cobrança, `invoice` ou `tenant.status = 'suspended_commercial'` como critério (INV-09).

## Arquivos a criar/alterar

```
packages/contracts/src/commands/enums.ts
packages/contracts/src/events/command-state-changed.v1.ts
packages/contracts/src/fleet/capability-commands.ts
packages/contracts/src/index.ts                      (exportar os três acima)
packages/domain/src/commands/types.ts
packages/domain/src/commands/evidence.ts
packages/domain/src/commands/policy.ts
packages/domain/src/commands/state-machine.ts
packages/domain/src/commands/texts.ts
packages/domain/src/commands/index.ts
packages/domain/src/index.ts                         (export * from './commands/index.ts')
packages/domain/test/commands.unit.test.ts
packages/domain/test/commands.property.test.ts
packages/domain/stryker.config.json
packages/domain/package.json                         (scripts test, mutation; devDependencies abaixo)
.github/workflows/ci.yml                             (job mutation)
.github/workflows/nightly.yml                        (criar se não existir: só o job mutation completo)
package.json                                         (devDependencies @tracksys/domain e @tracksys/contracts, se faltarem)
tests/acceptance/T-016/fixtures.ts
tests/acceptance/T-016/evaluate-block.test.ts
tests/acceptance/T-016/availability.test.ts
tests/acceptance/T-016/state-machine.test.ts
tests/acceptance/T-016/texts.test.ts
tests/acceptance/T-016/commands.property.test.ts
tests/acceptance/T-016/profiles.test.ts
```

Dependências novas (só em `packages/domain`, devDependencies): `fast-check@^4`, `@stryker-mutator/core@^9`, `@stryker-mutator/vitest-runner@^9`. Justificativa: [14 §9](../docs/spec/14-qualidade-e-processo-ia.md) exige propriedades e mutação neste caminho.

## Especificação detalhada

### 1. Contratos (`packages/contracts`)

`src/commands/enums.ts`:

```ts
import { z } from 'zod'
export const CommandTypeSchema = z.enum(['block', 'unblock', 'position_request', 'set_interval'])
export const CommandStateSchema = z.enum(['REQUESTED', 'ARMED', 'READY', 'DISPATCHING', 'AWAITING_CONFIRMATION',
  'CONFIRMED', 'UNKNOWN', 'FAILED', 'REJECTED', 'CANCELLED', 'EXPIRED'])
export const ReasonCodeSchema = z.enum(['theft_suspected', 'preventive', 'customer_request', 'installation_test',
  'recovered', 'pre_dispatch_fix', 'occurrence_interval', 'other'])
export const CutPointSchema = z.enum(['fuel_pump', 'ignition', 'starter'])
export const RequestedViaSchema = z.enum(['app', 'console', 'contingency'])
export const StateReasonSchema = z.string().regex(/^[a-z_]{3,40}$/)
```

`src/events/command-state-changed.v1.ts`: `CommandStateChangedV1 = z.strictObject({ type: z.literal('command.state.changed.v1'), eventId: z.uuid(), occurredAt: z.iso.datetime(), commandId: z.uuid(), operatorId: z.uuid(), tenantId: z.uuid(), vehicleId: z.uuid(), deviceId: z.uuid(), commandType: CommandTypeSchema, fromState: CommandStateSchema.nullable(), toState: CommandStateSchema, stateVersion: z.number().int().min(1), stateReason: StateReasonSchema.nullable(), at: z.iso.datetime(), requestedVia: RequestedViaSchema, processingMode: z.enum(['live', 'reprocess', 'backfill', 'replay']) })`. O campo é `commandType` (não `type`) porque `type` já é o nome do evento na outbox; [06 §14](../docs/spec/06-comandos-e-bloqueio.md) chama de `type` o mesmo dado.

`src/fleet/capability-commands.ts` (schema de **armazenamento**, snake_case, fora do OpenAPI):

```ts
const Tri = z.enum(['yes', 'no', 'unknown'])
const Regex = z.string().min(1).max(200).refine((s) => { try { new RegExp(s, 'i'); return true } catch { return false } }, 'regex inválida')
const AckPair = z.strictObject({ success: Regex, failure: Regex })
export const CapabilityCommandsSchema = z.strictObject({
  version: z.literal(1),
  block_type: z.string().min(1).nullable(), unblock_type: z.string().min(1).nullable(),
  block_type_gated: z.string().min(1).nullable(), position_request_type: z.string().min(1).nullable(),
  set_interval_type: z.string().min(1).nullable(), no_queue: Tri,
  send_timeout_s: z.number().int().min(1).max(30), confirm_timeout_s: z.number().int().min(10).max(300),
  confirmation: z.enum(['ack_and_relay_state', 'ack_only']).nullable(), offline_error_pattern: Regex.nullable(),
  stopped_speed_max_kmh_x10: z.number().int().min(0).max(50),
  ack_patterns: z.strictObject({ block: AckPair.nullable(), unblock: AckPair.nullable() }),
  relay_persists_power_cycle: Tri,
  sms: z.strictObject({ unblock_template_ref: z.string().min(1).nullable(), block_template_ref: z.string().min(1).nullable() }),
  homologation_ref: z.string().min(1).nullable(),
})
export type CapabilityCommands = z.infer<typeof CapabilityCommandsSchema>
export function isCommandsComplete(c: CapabilityCommands, opts: { requireHomologationRef: boolean }): boolean
export function parseCapabilityProfile(row: { status: 'draft' | 'homologated' | 'suspended'; evidenceRef: string | null;
  capabilities: unknown }): { ok: true; commands: CapabilityCommands | null } | { ok: false; errors: string[] }
```

`isCommandsComplete` = `block_type`, `unblock_type`, `confirmation`, `offline_error_pattern`, `ack_patterns.block`, `ack_patterns.unblock` não nulos, `no_queue = 'yes'`, `relay_persists_power_cycle ∈ {yes, no}` e, com `requireHomologationRef`, `homologation_ref` não nulo.

`parseCapabilityProfile` aplica o schema base do perfil já existente (T-002/T-005; capacidades `yes|no|unknown`) e acrescenta, nesta ordem, cada regra com mensagem própria:
1. `capabilities.relay = 'yes'` → `capabilities.commands` presente e `isCommandsComplete(c, { requireHomologationRef: false })`; senão `relay=yes exige seção commands completa`.
2. `commands.confirmation = 'ack_and_relay_state'` → `capabilities.relay_state_reported = 'yes'`; senão `ack_and_relay_state exige relay_state_reported=yes`.
3. `status = 'homologated'` → `evidenceRef` não nulo e `commands.homologation_ref` não nulo; senão `homologated exige homologation_ref`.

### 2. Tipos (`packages/domain/src/commands/types.ts`)

```ts
export type CutPoint = 'fuel_pump' | 'ignition' | 'starter'
export type Tri = 'yes' | 'no' | 'unknown'
export type ProcessingMode = 'live' | 'reprocess' | 'backfill' | 'replay'
export type CommandType = 'block' | 'unblock' | 'position_request' | 'set_interval'
export type CommandState = 'REQUESTED' | 'ARMED' | 'READY' | 'DISPATCHING' | 'AWAITING_CONFIRMATION' | 'CONFIRMED'
  | 'UNKNOWN' | 'FAILED' | 'REJECTED' | 'CANCELLED' | 'EXPIRED'
export type ArmedReason = 'awaiting_speed' | 'awaiting_stop' | 'awaiting_evidence' | 'awaiting_contact' | 'awaiting_on_demand_fix'
export type RejectReason = 'authorization_revoked' | 'profile_not_homologated' | 'cut_point_missing' | 'block_terms_missing'
  | 'block_scope_disabled' | 'relay_unsupported' | 'tenant_closed'
export type AttemptResult = 'pending' | 'sent' | 'queued' | 'not_sent' | 'device_offline' | 'rejected' | 'timeout' | 'error'
  | 'unknown' | 'sms_accepted' | 'sms_rejected' | 'outside_platform'
export interface EvidenceFix {
  sourceEventId: string; assignmentId: string; fixTime: Date; receivedAt: Date; valid: boolean
  latE7: number | null; lonE7: number | null; speedKmhX10: number | null; flags: readonly string[]; processingMode: ProcessingMode
}
export interface CommandPolicyValues {
  version: number; maxMovingCutKmh: number; evidenceMaxAgeS: number; armedTtlS: number; occurrenceArmedTtlS: number; allowAppBlock: boolean
}
export interface ProfileFacts {
  ref: string                 // '<model>/<version>', ex.: 'j16-gt06/2'
  ignition: Tri               // capabilities.ignition
  stoppedSpeedMaxKmhX10: number   // commands.stopped_speed_max_kmh_x10 (padrão 0)
  stoppedIntervalS: number    // normalization.stopped_interval_s (J16: 300)
  positionRequestType: string | null
}
export interface BlockEvaluationInput {
  now: Date; cutPoint: CutPoint; assignmentId: string; policy: CommandPolicyValues; profile: ProfileFacts
  fixes: readonly EvidenceFix[]
  ignition: { value: boolean | null; observedAt: Date | null }   // device_state.ignition e aux.statusAt
  motion: 'moving' | 'stopped' | 'unknown'
  lastContactAt: Date | null
  onDemandSince: Date | null  // started_at da tentativa do filho position_request; null fora do fluxo sob demanda
}
export interface EvidenceSnapshot {
  evaluatedAt: string; rule: string; decision: 'READY' | 'ARMED'; cutPoint: CutPoint; ceilingKmh: number
  evidenceMaxAgeS: number; profile: string; ignOff: boolean; onDemandFix: boolean; policyVersion: number
  fixes: { sourceEventId: string; fixTime: string; receivedAt: string; speedKmh: number }[]   // até 5, mais recentes primeiro
}
export interface BlockDecision { decision: 'READY' | 'ARMED'; reason: ArmedReason | null; rule: string; evidence: EvidenceSnapshot }
```

Todas as datas entram como `Date`; o snapshot sai em RFC 3339 UTC com milissegundos (`toISOString()`), velocidade em km/h com 1 casa (`speedKmhX10 / 10`, INV-12).

### 3. Evidência e avaliação (`evidence.ts`, `policy.ts`)

`selectEvidence(fixes, { now, evidenceMaxAgeS: E, assignmentId, onDemandSince })` devolve o conjunto **S** em ordem decrescente de `fixTime`:
1. Candidato = `processingMode === 'live'` **e** `valid` **e** `latE7` e `lonE7` não nulos **e** sem flag `JUMP_SUSPECT` **e** `assignmentId` igual **e** `speedKmhX10 !== null` **e** `fixTime ∈ [now − E s, now + 120 s]` **e** (com `onDemandSince`) `fixTime ≥ onDemandSince − 5 s`.
2. Sem candidato → `[]`.
3. O candidato de maior `fixTime` precisa de `receivedAt ≥ now − E s`; se falhar, **S = []** (não se usa um fix mais antigo no lugar: o fix mais novo pode mostrar velocidade maior — INV-08).

`computeIgnOff(input, S)` = `profile.ignition === 'yes'` **e** `ignition.value === false` **e** `ignition.observedAt ∈ [now − E s, now]` **e** `motion !== 'moving'` **e** todo fix de S com `speedKmhX10 ≤ profile.stoppedSpeedMaxKmhX10`.

"Parado" = `speedKmhX10 ≤ profile.stoppedSpeedMaxKmhX10`. "Dois parados" = os **2 fixes mais recentes de S** são parados e têm `fixTime` distintos (um fix novo em movimento desfaz a condição).

`evaluateBlock(input): BlockDecision`, nesta ordem:

| # | Condição | Resultado (`decision`, `reason`, `rule`) |
|---|---|---|
| 1 | `cutPoint ≠ 'starter'` e `profile.positionRequestType ≠ null` e `onDemandSince === null` | ARMED, `awaiting_on_demand_fix`, `<cut>.awaiting_on_demand_fix` |
| 2 | `starter` e `lastContactAt ≥ now − (stoppedIntervalS + 60) s` | READY, null, `starter.contact_online` |
| 3 | `starter` (senão) | ARMED, `awaiting_contact`, `starter.awaiting_contact` |
| 4 | `ignition` e dois parados | READY, null, `ignition.two_stopped_fixes` |
| 5 | `ignition` e IGN_OFF | READY, null, `ignition.ign_off` |
| 6 | `ignition` (senão) | ARMED, `awaiting_stop`, `ignition.awaiting_stop` |
| 7 | `fuel_pump` com `maxMovingCutKmh = 0` e dois parados | READY, null, `fuel_pump.stopped_ceiling_zero` |
| 8 | `fuel_pump` com teto > 0, S não vazio e todo fix de S com `speedKmhX10 ≤ maxMovingCutKmh × 10` | READY, null, `fuel_pump.moving_under_ceiling` |
| 9 | `fuel_pump` e IGN_OFF | READY, null, `fuel_pump.ign_off` |
| 10 | `fuel_pump`, S vazio | ARMED: `awaiting_on_demand_fix` se `positionRequestType ≠ null`, senão `awaiting_evidence`; rule `fuel_pump.awaiting_evidence` |
| 11 | `fuel_pump`, teto 0 (senão) | ARMED, `awaiting_stop`, `fuel_pump.awaiting_stop` |
| 12 | `fuel_pump` (senão) | ARMED, `awaiting_speed`, `fuel_pump.awaiting_speed` |

Na regra 6, com `positionRequestType ≠ null` e S vazio, o motivo é `awaiting_on_demand_fix`. `evaluateBlock` lança `RangeError` se `maxMovingCutKmh ∉ [0, 40]` ou `evidenceMaxAgeS ∉ [15, 60]` (defesa em profundidade do CHECK de T-017).

Outras funções de `policy.ts`:

```ts
export const PLATFORM_DEFAULT_POLICY: CommandPolicyValues = { version: 0, maxMovingCutKmh: 0, evidenceMaxAgeS: 60,
  armedTtlS: 300, occurrenceArmedTtlS: 1800, allowAppBlock: false }
export const CURRENT_BLOCK_TERMS_VERSION = 1
export type BlockScope = { kind: 'none' } | { kind: 'all' } | { kind: 'pilot'; vehicleIds: readonly string[] }
export function parseBlockScope(raw: string): BlockScope        // 'none' | 'all' | 'pilot:<uuid>[,<uuid>]'; outro → Error
export function isBlockTermsValid(textVersion: string | null, currentVersion: number, ceilingKmh: number): boolean
export function computeExpiresAt(createdAt: Date, policy: CommandPolicyValues, occurrenceOpen: boolean, requestedVia: 'app' | 'console' | 'contingency'): Date
export type BlockUnavailable = 'TENANT_CLOSED' | 'COMMAND_DISPATCH_DISABLED' | 'BLOCK_SCOPE_DISABLED' | 'NO_PRIMARY_DEVICE'
  | 'CUT_POINT_MISSING' | 'PROFILE_NOT_HOMOLOGATED' | 'RELAY_UNSUPPORTED' | 'BLOCK_TERMS_MISSING'
export interface AvailabilityInput {
  tenantStatus: 'active' | 'suspended_commercial' | 'closed'; dispatchEnabled: boolean; blockScope: BlockScope
  benchOperatorId: string | null; operatorId: string; vehicleId: string; hasOpenPrimaryAssignment: boolean
  cutPoint: CutPoint | null
  profile: { status: 'draft' | 'homologated' | 'suspended'; relay: Tri; commandsComplete: boolean; hasHomologationRef: boolean } | null
  blockTermsTextVersion: string | null; currentTermsVersion: number; ceilingKmh: number
}
export function checkBlockAvailability(i: AvailabilityInput): { available: true } | { available: false; code: BlockUnavailable }
export function checkUnblockAvailability(i: AvailabilityInput): { available: true } | { available: false; code: 'TENANT_CLOSED' | 'NO_PRIMARY_DEVICE' | 'PROFILE_NOT_HOMOLOGATED' | 'RELAY_UNSUPPORTED' }
```

- `isBlockTermsValid`: casa `^block-terms-v(\d+)/(\d+)kmh$`; válido se `N = currentVersion` e `kmh ≥ ceilingKmh`.
- `computeExpiresAt`: `contingency` → `createdAt`; ocorrência aberta → `+ occurrenceArmedTtlS`; senão `+ armedTtlS` (vale para todos os tipos).
- `checkBlockAvailability`, primeira falha na ordem: `tenantStatus = 'closed'` → `TENANT_CLOSED`; `!dispatchEnabled` → `COMMAND_DISPATCH_DISABLED`; escopo `none`, ou `pilot` sem `vehicleId` → `BLOCK_SCOPE_DISABLED`; `!hasOpenPrimaryAssignment` → `NO_PRIMARY_DEVICE` (veículo sem vínculo primário aberto, nome de [09 §9.1](../docs/spec/09-api-e-contratos.md)); `cutPoint === null` → `CUT_POINT_MISSING`; perfil nulo, ou perfil não "aceito" → `PROFILE_NOT_HOMOLOGATED`, onde aceito = (`status = 'homologated'` e `commandsComplete` e `hasHomologationRef`) **ou** (`operatorId === benchOperatorId` e `status = 'draft'` e `relay = 'yes'` e `commandsComplete`); `relay ≠ 'yes'` → `RELAY_UNSUPPORTED`; termo inválido → `BLOCK_TERMS_MISSING`. `suspended_commercial` não altera nada (INV-09).
- `checkUnblockAvailability`: `closed` → `TENANT_CLOSED`; sem vínculo primário aberto → `NO_PRIMARY_DEVICE`; perfil nulo ou `status = 'draft'` fora da operadora de bancada → `PROFILE_NOT_HOMOLOGATED`; `relay ≠ 'yes'` → `RELAY_UNSUPPORTED`. Escopo, `cut_point`, termo e despacho desligado **não** impedem desbloqueio (06 §2).

### 4. Máquina de estados (`state-machine.ts`)

`TRANSITIONS` = os 22 pares do gatilho de [06 §6](../docs/spec/06-comandos-e-bloqueio.md) **mais** `ARMED>FAILED` (ver "Decisões já tomadas"). `isAllowedTransition(type, from, to, { hasAttempts })` replica o gatilho: par na lista; `READY>ARMED` e `DISPATCHING>ARMED` só `block`; `DISPATCHING>READY` e `AWAITING_CONFIRMATION>READY` só `unblock`; `ARMED>FAILED` só `block` com `hasAttempts`; `CANCELLED` e `EXPIRED` só sem tentativas.

```ts
export type TraccarOutcome = { kind: 'http'; status: number; body: string } | { kind: 'not_sent' } | { kind: 'timeout' } | { kind: 'connection_lost' }
export function mapDispatchOutcome(i: { type: CommandType; outcome: TraccarOutcome; offlineErrorPattern: string; now: Date;
  expiresAt: Date; gprsAttemptsIncludingThis: number; priorResults: readonly AttemptResult[] }):
  { attemptResult: AttemptResult; to: CommandState; stateReason: string | null }
export function unblockFinalState(results: readonly AttemptResult[]): { to: 'UNKNOWN' | 'FAILED'; stateReason: 'unblock_unconfirmed' | 'not_delivered' }
export type ConfirmationResult = { kind: 'confirmed' } | { kind: 'failed'; reason: 'ack_failure' }
  | { kind: 'contradictory' } | { kind: 'evidence_only' } | { kind: 'pending' } | { kind: 'deadline_passed' }
export function confirmationDecision(i: { type: CommandType; confirmation: 'ack_and_relay_state' | 'ack_only';
  patterns: { success: string; failure: string } | null; attemptStartedAt: Date; now: Date; confirmTimeoutS: number; lateMode: boolean;
  ack: { text: string; eventTime: Date; processingMode: ProcessingMode } | null
  relay: { state: 'blocked' | 'unblocked' | 'unknown'; observedAt: Date | null } | null
  fix: { fixTime: Date; processingMode: ProcessingMode } | null }): ConfirmationResult
export function attributeEvidence(attempts: readonly { id: string; type: 'block' | 'unblock'; startedAt: Date }[],
  fact: { type: 'block' | 'unblock'; at: Date }): string | null   // id da tentativa ou null (detail.unattributed)
```

`mapDispatchOutcome` (06 §7): `200` → `sent`, AWAITING_CONFIRMATION. `202` → `queued`, UNKNOWN `queued_by_traccar`. `4xx` com `new RegExp(offlineErrorPattern, 'i').test(body)` → `device_offline`; `not_sent` → `not_sent`; nos dois: `block` → ARMED `awaiting_evidence` se `now < expiresAt` e `gprsAttemptsIncludingThis < 5`, senão FAILED `device_offline`; `unblock` → READY `device_offline` se `gprsAttemptsIncludingThis < 5`, senão `unblockFinalState`; `position_request`/`set_interval` → FAILED `device_offline`. Outro `4xx` → `rejected`, FAILED `traccar_rejected`. `5xx` e `connection_lost` → `error`; `timeout` → `timeout`; nos três: `unblock` → AWAITING_CONFIRMATION; demais → UNKNOWN `transport_unknown`.

`unblockFinalState`: algum resultado em `sent`, `queued`, `timeout`, `error`, `unknown`, `sms_accepted` → UNKNOWN `unblock_unconfirmed`; senão FAILED `not_delivered`.

`confirmationDecision` (06 §8.1, §8.3): texto do ack normalizado com `trim().toLowerCase()`; evidência com `processingMode ≠ 'live'` → `evidence_only` (INV-05); `failure` casado → `failed`; relé observado com `observedAt ≥ attemptStartedAt` no estado oposto ao esperado (`block` → `blocked`, `unblock` → `unblocked`) → `contradictory`; `ack_only` com `success` casado → `confirmed`; `ack_and_relay_state` com `success` casado **e** relé esperado com `observedAt ≥ attemptStartedAt` → `confirmed`; `position_request` → `confirmed` com fix `live` de `fixTime ≥ attemptStartedAt − 5 s`; `set_interval` segue `ack_only`. Fora do prazo (`ack.eventTime` ou `relay.observedAt` > `attemptStartedAt + confirmTimeoutS`) só confirma com `lateMode = true`. Nada casou e `now ≥ attemptStartedAt + confirmTimeoutS` → `deadline_passed`; nada casou antes do prazo → `pending` (texto sem padrão → `evidence_only`).

`attributeEvidence` (06 §8.3): última tentativa do mesmo tipo com `startedAt ≤ fact.at`, desde que nenhuma tentativa do tipo oposto tenha `startedAt` posterior a ela; senão `null`.

**Redutor** — o worker (T-020) e a API (T-018) não decidem transição fora dele:

```ts
export interface AttemptView { seq: number; channel: 'gprs' | 'sms'; startedAt: Date; result: AttemptResult }
export interface CommandView { type: CommandType; state: CommandState; createdAt: Date; expiresAt: Date;
  attempts: readonly AttemptView[]; manualSmsTaskEmitted: boolean }
export type CommandEvent =
  | { kind: 'evaluated'; now: Date; decision: 'READY' | 'ARMED'; reason: ArmedReason | null }
  | { kind: 'revalidation_failed'; now: Date; reason: RejectReason }
  | { kind: 'dispatch_requested'; now: Date }
  | { kind: 'dispatch_outcome'; now: Date; outcome: TraccarOutcome; offlineErrorPattern: string; confirmTimeoutS: number }
  | { kind: 'confirmation'; now: Date; result: ConfirmationResult }
  | { kind: 'tick'; now: Date; smsEnabled: boolean; confirmTimeoutS: number }
  | { kind: 'sms_outcome'; now: Date; accepted: boolean }
  | { kind: 'cancel'; now: Date; reason: 'cancelled_by_user' | 'superseded_by_unblock' | 'occurrence_closed' }
  | { kind: 'worker_restart'; now: Date; confirmTimeoutS: number }
  | { kind: 'failover'; now: Date }
export type Effect =
  | { kind: 'create_attempt'; channel: 'gprs' | 'sms'; seq: number }
  | { kind: 'finish_attempt'; seq: number; result: AttemptResult }
  | { kind: 'schedule_dispatch'; at: Date } | { kind: 'schedule_tick'; at: Date }
  | { kind: 'manual_sms_task' } | { kind: 'notify'; to: CommandState }
  | { kind: 'open_unknown_alert' } | { kind: 'close_unknown_alert' }
export interface Reduction { to: CommandState | null; stateReason: string | null; effects: Effect[] }
export function reduceCommand(cmd: CommandView, ev: CommandEvent): Reduction
```

Evento sem efeito no estado atual devolve `{ to: null, stateReason: null, effects: [] }` (job atrasado ou duplicado não faz nada). `seq` = `attempts.length + 1`. "Incerta" = tentativa com resultado `pending`, `sent`, `queued`, `timeout`, `error` ou `unknown`. `gprs(n)` = número de tentativas `gprs`. `t0` = `startedAt` da 1ª tentativa `gprs`.

| Evento | Estado | Resultado |
|---|---|---|
| `evaluated` | REQUESTED | `decision` com `reason`; READY → `schedule_dispatch(now)`; ARMED → `schedule_tick(now + 15 s)` |
| `evaluated` READY | ARMED | READY + `schedule_dispatch(now)` |
| `evaluated` ARMED | READY, só `block` | ARMED com `reason` + `schedule_tick(now + 15 s)` |
| `revalidation_failed` | ARMED, READY | REJECTED com `reason` + `notify` |
| `dispatch_requested` | READY | `block` com `now ≥ expiresAt`: sem tentativa → EXPIRED + `notify`; com tentativa → ARMED `awaiting_evidence` + `schedule_tick(now)`. `block` com tentativa incerta ou `gprs = 5` → nada. `unblock` com `gprs = 5` → nada. Senão DISPATCHING + `create_attempt(gprs, seq)` |
| `dispatch_outcome` | DISPATCHING | `finish_attempt(último seq, attemptResult)` + transição de `mapDispatchOutcome`. AWAITING → `schedule_tick(startedAt + confirmTimeoutS)`; ARMED → `schedule_tick(now + 15 s)`; READY (`unblock`) → `schedule_dispatch(t0 + gprs × 60 s)`; UNKNOWN → `open_unknown_alert` + `notify`; FAILED → `notify` |
| `confirmation` `confirmed` | AWAITING_CONFIRMATION | CONFIRMED + `notify` |
| `confirmation` `confirmed` | UNKNOWN | CONFIRMED `late_evidence` + `close_unknown_alert` + `notify` |
| `confirmation` `failed` | AWAITING, UNKNOWN | FAILED `ack_failure` (+ `close_unknown_alert` se vinha de UNKNOWN) + `notify` |
| `confirmation` `contradictory` | AWAITING_CONFIRMATION | UNKNOWN `contradictory_evidence` + `open_unknown_alert` + `notify` |
| `tick` | ARMED | `now ≥ expiresAt`: sem tentativa → EXPIRED + `notify`; com tentativa (`block`) → FAILED `device_offline` + `notify`. Senão `schedule_tick(now + 15 s)` |
| `tick` | READY sem tentativa | `now ≥ expiresAt` → EXPIRED + `notify` |
| `tick` | AWAITING_CONFIRMATION | Antes de `startedAt + confirmTimeoutS` (última tentativa gprs): nada. Depois: `block`, `position_request`, `set_interval` → UNKNOWN `confirmation_timeout` + `open_unknown_alert` + `notify`; `unblock` com `gprs < 5` → READY `retry_scheduled` + `schedule_dispatch(t0 + gprs × 60 s)`; `unblock` com `gprs = 5` → `unblockFinalState` + `open_unknown_alert` (se UNKNOWN) + `notify` |
| `tick` (qualquer estado ativo) | `unblock` | Se `now ≥ t0 + 120 s`, sem tentativa `sms`, não confirmado: `smsEnabled` → `create_attempt(sms, seq)` (sem mudar estado); senão, se `!manualSmsTaskEmitted` → `manual_sms_task` |
| `sms_outcome` | qualquer | `finish_attempt(seq da tentativa sms, accepted ? 'sms_accepted' : 'sms_rejected')`; estado não muda |
| `cancel` | ARMED, READY sem tentativa | CANCELLED com `reason` |
| `worker_restart` | DISPATCHING | `finish_attempt(seq pendente, 'unknown')`; `unblock` → READY `worker_restart` + `schedule_dispatch(startedAt + 60 s)`; demais → UNKNOWN `worker_restart` + `open_unknown_alert` + `notify` |
| `worker_restart` | READY / ARMED / AWAITING | READY → `schedule_dispatch(now)`; ARMED → regra do `tick`; AWAITING → regra do `tick` |
| `failover` | DISPATCHING, AWAITING | `finish_attempt(pendente, 'unknown')` se houver; UNKNOWN `failover` (todos os tipos, inclusive `unblock`) + `open_unknown_alert` + `notify` |

`block` nunca gera `create_attempt` de canal `sms` nem nova tentativa depois de tentativa incerta (INV-08). UNKNOWN nunca volta a DISPATCHING.

### 5. Textos (`texts.ts`)

Hora em BRT = UTC − 3 h, `HH:mm` ([10 §2](../docs/spec/10-apps-e-ux.md)). Idade com `formatAge` de `packages/domain/src/ux/age-format.ts` (F0, REQ-UX-005).

| Função | Saída exata |
|---|---|
| `effectText({ cutPoint: 'starter' })` | `Bloqueio de partida: o veículo não dará nova partida. Se estiver ligado, continua funcionando até ser desligado.` |
| `effectText({ cutPoint: 'ignition', ttlMin })` | `Corte de ignição: desliga o motor. Só é enviado com o veículo parado; em movimento, o pedido aguarda até {ttlMin} min.` |
| `effectText({ cutPoint: 'fuel_pump', ceilingKmh > 0, ttlMin })` | `Corte de combustível: o motor apaga em alguns segundos, inclusive em movimento até {teto} km/h. Acima disso, o pedido aguarda até {ttlMin} min.` |
| `effectText({ cutPoint: 'fuel_pump', ceilingKmh: 0 })` | `Corte de combustível: o motor apaga em alguns segundos. Só é enviado com o veículo parado.` |
| `armedReasonText` | `awaiting_speed` → `veículo acima de {teto} km/h`; `awaiting_stop` → `o veículo precisa parar`; `awaiting_evidence` → `aguardando posição atual do rastreador`; `awaiting_contact` → `aguardando sinal do rastreador`; `awaiting_on_demand_fix` → `pedindo posição ao rastreador` |
| `stateTitle({ type, state, stateReason, ceilingKmh, at, expiresAt })` | `{ title, subtitle }` pela tabela de [10 §7](../docs/spec/10-apps-e-ux.md): REQUESTED `Pedido registrado` / `Verificando condições de segurança`; ARMED `Aguardando condição segura — {motivo}` / `Expira às {HH:mm}`; READY e DISPATCHING `Enviando ao rastreador`; AWAITING_CONFIRMATION `Aguardando confirmação do rastreador`; CONFIRMED `Bloqueio confirmado às {HH:mm}` ou `Desbloqueio confirmado às {HH:mm}`; UNKNOWN `Não foi possível confirmar. O veículo pode ou não estar bloqueado`; FAILED `O rastreador não executou`; REJECTED `Recusado: {motivo}`; EXPIRED `Expirou sem condição segura. Nada foi enviado`; CANCELLED `Cancelado. Nada foi enviado` |
| `rejectReasonText` | `authorization_revoked` → `permissão revogada`; `profile_not_homologated` → `rastreador sem homologação de bloqueio`; `cut_point_missing` → `veículo sem ponto de corte registrado`; `block_terms_missing` → `termo de ciência não aceito`; `block_scope_disabled` → `bloqueio desligado na plataforma`; `relay_unsupported` → `rastreador sem relé`; `tenant_closed` → `cliente encerrado` |
| `relayBadgeText(state, observedAt, now)` | `Relé: bloqueado · observado {formatAge}`, `Relé: desbloqueado · observado {formatAge}`, ou `Relé: estado desconhecido` (estado `unknown` ou `observedAt` nulo) |

### 6. Stryker e CI

`packages/domain/stryker.config.json`:

```json
{
  "$schema": "../../node_modules/@stryker-mutator/core/schema/stryker-schema.json",
  "testRunner": "vitest",
  "vitest": { "configFile": "vitest.config.ts" },
  "mutate": ["src/commands/**/*.ts", "!src/commands/index.ts", "!src/commands/types.ts"],
  "thresholds": { "high": 90, "low": 80, "break": 80 },
  "incremental": true,
  "incrementalFile": "reports/stryker-incremental.json",
  "reporters": ["clear-text", "progress", "json"],
  "coverageAnalysis": "perTest"
}
```

Scripts em `packages/domain/package.json`: `"test": "vitest run"`, `"mutation": "stryker run"`. Job `mutation` no `ci.yml` (PR): checkout com `fetch-depth: 0`, `pnpm install --frozen-lockfile`, passo que sai 0 se `git diff --name-only origin/${{ github.base_ref }}...HEAD` não tiver `^packages/domain/src/commands/`, senão `pnpm --filter @tracksys/domain mutation`. `nightly.yml` (`cron: '17 6 * * *'`) roda `pnpm --filter @tracksys/domain mutation` sem filtro. `reports/` entra no `.gitignore` do pacote.

## Testes de aceite (congelados)

Os arquivos abaixo são o aceite desta tarefa. Copie sem alterar nada para `tests/acceptance/T-016/`. Eles só importam `@tracksys/domain`, `@tracksys/contracts`, `@tracksys/db` (no teste de perfis) e `fast-check`.

`tests/acceptance/T-016/fixtures.ts`

```ts
import { type BlockEvaluationInput, type EvidenceFix, PLATFORM_DEFAULT_POLICY } from '@tracksys/domain'

export const T = new Date('2026-11-20T14:00:00Z')
export const ASSIGNMENT = '0192a1b2-0000-7000-8000-0000000000b1'
export const at = (hms: string) => new Date(`2026-11-20T${hms}Z`)
let seq = 900000

export function fix(hms: string, kmh: number | null, over: Partial<EvidenceFix> = {}): EvidenceFix {
  seq += 1
  return {
    sourceEventId: String(seq),
    assignmentId: ASSIGNMENT,
    fixTime: at(hms),
    receivedAt: at(hms),
    valid: true,
    latE7: -50892110,
    lonE7: -428018920,
    speedKmhX10: kmh === null ? null : Math.round(kmh * 10),
    flags: [],
    processingMode: 'live',
    ...over,
  }
}

export const POLICY_40 = { ...PLATFORM_DEFAULT_POLICY, version: 2, maxMovingCutKmh: 40, allowAppBlock: true }
export const PROFILE = {
  ref: 'j16-gt06/2',
  ignition: 'yes' as const,
  stoppedSpeedMaxKmhX10: 0,
  stoppedIntervalS: 300,
  positionRequestType: null,
}

export function input(over: Partial<BlockEvaluationInput> = {}): BlockEvaluationInput {
  return {
    now: T,
    cutPoint: 'fuel_pump',
    assignmentId: ASSIGNMENT,
    policy: POLICY_40,
    profile: PROFILE,
    fixes: [],
    ignition: { value: null, observedAt: null },
    motion: 'unknown',
    lastContactAt: null,
    onDemandSince: null,
    ...over,
  }
}
```

`tests/acceptance/T-016/evaluate-block.test.ts`

```ts
import { computeExpiresAt, type EvidenceFix, evaluateBlock, PLATFORM_DEFAULT_POLICY } from '@tracksys/domain'
import { describe, expect, it } from 'vitest'
import { at, fix, input, POLICY_40, PROFILE, T } from './fixtures.ts'

describe('T-016 evaluateBlock — CT-CMD-002 regra por cut_point', () => {
  it('starter com contato há 270 s e último fix a 80 km/h fica READY', () => {
    const d = evaluateBlock(input({ cutPoint: 'starter', lastContactAt: at('13:55:30'), fixes: [fix('13:55:30', 80)] }))
    expect(d).toMatchObject({ decision: 'READY', reason: null, rule: 'starter.contact_online' })
  })

  it('starter sem contato há 361 s fica ARMED awaiting_contact', () => {
    const d = evaluateBlock(input({ cutPoint: 'starter', lastContactAt: at('13:53:59') }))
    expect(d).toMatchObject({ decision: 'ARMED', reason: 'awaiting_contact' })
  })

  it('fuel_pump com 38 e 35 km/h dentro de 60 s fica READY', () => {
    const d = evaluateBlock(input({ fixes: [fix('13:59:20', 38), fix('13:59:50', 35)] }))
    expect(d).toMatchObject({ decision: 'READY', rule: 'fuel_pump.moving_under_ceiling' })
    expect(d.evidence.fixes.map((f) => f.speedKmh)).toEqual([35, 38])
    expect(d.evidence).toMatchObject({ ceilingKmh: 40, evidenceMaxAgeS: 60, profile: 'j16-gt06/2', policyVersion: 2 })
  })

  it('fuel_pump com um fix a 45 km/h na janela fica ARMED awaiting_speed', () => {
    const d = evaluateBlock(input({ fixes: [fix('13:59:20', 45), fix('13:59:50', 35)] }))
    expect(d).toMatchObject({ decision: 'ARMED', reason: 'awaiting_speed' })
  })

  it('fuel_pump com fix a 40,0 km/h e teto 40 fica READY (mata o mutante <= → <)', () => {
    expect(evaluateBlock(input({ fixes: [fix('13:59:50', 40)] })).decision).toBe('READY')
    expect(evaluateBlock(input({ fixes: [fix('13:59:50', 40.1)] })).decision).toBe('ARMED')
  })

  it('ignition com 1 fix parado e ignição desconhecida fica ARMED awaiting_stop', () => {
    const d = evaluateBlock(input({ cutPoint: 'ignition', fixes: [fix('13:59:50', 0)] }))
    expect(d).toMatchObject({ decision: 'ARMED', reason: 'awaiting_stop' })
  })

  it('ignition com 2 fixes parados de fix_time distintos fica READY', () => {
    const d = evaluateBlock(input({ cutPoint: 'ignition', fixes: [fix('13:59:20', 0), fix('13:59:50', 0)] }))
    expect(d).toMatchObject({ decision: 'READY', rule: 'ignition.two_stopped_fixes' })
  })

  it('ignition com 2 parados seguidos de 1 fix em movimento fica ARMED', () => {
    const fixes = [fix('13:59:10', 0), fix('13:59:20', 0), fix('13:59:50', 12)]
    expect(evaluateBlock(input({ cutPoint: 'ignition', fixes })).decision).toBe('ARMED')
  })

  it('ignition com ignição false às 13:59:40 e motion moving fica ARMED', () => {
    const d = evaluateBlock(
      input({ cutPoint: 'ignition', ignition: { value: false, observedAt: at('13:59:40') }, motion: 'moving' }),
    )
    expect(d.decision).toBe('ARMED')
    expect(d.evidence.ignOff).toBe(false)
  })

  it('fuel_pump sem fix com IGN_OFF válido fica READY por ign_off', () => {
    const d = evaluateBlock(input({ ignition: { value: false, observedAt: at('13:59:40') }, motion: 'stopped' }))
    expect(d).toMatchObject({ decision: 'READY', rule: 'fuel_pump.ign_off' })
  })

  it('IGN_OFF não vale com perfil de ignição unknown', () => {
    const d = evaluateBlock(
      input({
        profile: { ...PROFILE, ignition: 'unknown' },
        ignition: { value: false, observedAt: at('13:59:40') },
        motion: 'stopped',
      }),
    )
    expect(d).toMatchObject({ decision: 'ARMED', reason: 'awaiting_evidence' })
  })

  it('teto 0: fuel_pump exige dois fixes parados', () => {
    const policy = { ...PLATFORM_DEFAULT_POLICY }
    expect(evaluateBlock(input({ policy, fixes: [fix('13:59:50', 0)] }))).toMatchObject({
      decision: 'ARMED',
      reason: 'awaiting_stop',
    })
    expect(evaluateBlock(input({ policy, fixes: [fix('13:59:20', 0), fix('13:59:50', 0)] }))).toMatchObject({
      decision: 'READY',
      rule: 'fuel_pump.stopped_ceiling_zero',
    })
  })
})

describe('T-016 evaluateBlock — CT-CMD-003 evidência inválida nunca autoriza', () => {
  const armed = (fixes: EvidenceFix[]) => evaluateBlock(input({ fixes }))

  it('fix único 61 s antes fica ARMED awaiting_evidence', () => {
    expect(armed([fix('13:58:59', 10)])).toMatchObject({ decision: 'ARMED', reason: 'awaiting_evidence' })
  })
  it('fix com valid = false é ignorado', () => {
    expect(armed([fix('13:59:50', 10, { valid: false })]).decision).toBe('ARMED')
  })
  it('velocidade NULL não vale 0', () => {
    expect(armed([fix('13:59:50', null)])).toMatchObject({ decision: 'ARMED', reason: 'awaiting_evidence' })
  })
  it('processingMode backfill é ignorado (INV-05)', () => {
    const d = armed([fix('13:59:50', 10, { processingMode: 'backfill' })])
    expect(d.decision).toBe('ARMED')
    expect(d.evidence.fixes).toEqual([])
  })
  it('flag JUMP_SUSPECT é ignorada', () => {
    expect(armed([fix('13:59:50', 10, { flags: ['JUMP_SUSPECT'] })]).decision).toBe('ARMED')
  })
  it('fix de outro vínculo é ignorado', () => {
    expect(armed([fix('13:59:50', 10, { assignmentId: '0192a1b2-0000-7000-8000-0000000000b2' })]).decision).toBe('ARMED')
  })
  it('fix mais recente recebido 90 s antes anula a evidência', () => {
    expect(armed([fix('13:59:20', 10), fix('13:59:50', 10, { receivedAt: at('13:58:30') })]).decision).toBe('ARMED')
  })
  it('fix 121 s no futuro é ignorado', () => {
    expect(armed([fix('14:02:01', 10)]).decision).toBe('ARMED')
  })
  it('sem nenhum fix fica ARMED e o prazo é 14:05:00Z (300 s) ou 14:30:00Z com ocorrência', () => {
    expect(armed([])).toMatchObject({ decision: 'ARMED', reason: 'awaiting_evidence' })
    expect(computeExpiresAt(T, POLICY_40, false, 'app').toISOString()).toBe('2026-11-20T14:05:00.000Z')
    expect(computeExpiresAt(T, POLICY_40, true, 'app').toISOString()).toBe('2026-11-20T14:30:00.000Z')
    expect(computeExpiresAt(T, POLICY_40, false, 'contingency').toISOString()).toBe('2026-11-20T14:00:00.000Z')
  })
  it('teto fora de 0–40 lança RangeError', () => {
    expect(() => evaluateBlock(input({ policy: { ...POLICY_40, maxMovingCutKmh: 41 } }))).toThrow(RangeError)
  })
})

describe('T-016 evaluateBlock — CT-CMD-005 posição sob demanda', () => {
  const profile = { ...PROFILE, positionRequestType: 'positionSingle' }

  it('na criação fica ARMED awaiting_on_demand_fix', () => {
    expect(evaluateBlock(input({ profile, fixes: [fix('13:59:50', 10)] }))).toMatchObject({
      decision: 'ARMED',
      reason: 'awaiting_on_demand_fix',
    })
  })
  it('fix 3 s após o started_at do filho, a 25 km/h, leva a READY', () => {
    const d = evaluateBlock(
      input({ profile, now: at('14:00:05'), onDemandSince: T, fixes: [fix('14:00:03', 25, { receivedAt: at('14:00:04') })] }),
    )
    expect(d).toMatchObject({ decision: 'READY', rule: 'fuel_pump.moving_under_ceiling' })
    expect(d.evidence.onDemandFix).toBe(true)
  })
  it('fix 10 s antes do started_at do filho não conta', () => {
    const d = evaluateBlock(input({ profile, now: at('14:00:05'), onDemandSince: T, fixes: [fix('13:59:50', 25)] }))
    expect(d).toMatchObject({ decision: 'ARMED', reason: 'awaiting_on_demand_fix' })
  })
})
```

`tests/acceptance/T-016/availability.test.ts`

```ts
import {
  type AvailabilityInput,
  checkBlockAvailability,
  checkUnblockAvailability,
  isBlockTermsValid,
  parseBlockScope,
} from '@tracksys/domain'
import { describe, expect, it } from 'vitest'

const OP = '0192a1b2-0000-7000-8000-00000000a1fa'
const BENCH = '0192a1b2-0000-7000-8000-00000000bec0'
const V1 = '0192a1b2-0000-7000-8000-0000000000f1'
const V2 = '0192a1b2-0000-7000-8000-0000000000f2'
const homologated = { status: 'homologated' as const, relay: 'yes' as const, commandsComplete: true, hasHomologationRef: true }

function base(over: Partial<AvailabilityInput> = {}): AvailabilityInput {
  return {
    tenantStatus: 'active',
    dispatchEnabled: true,
    blockScope: { kind: 'all' },
    benchOperatorId: BENCH,
    operatorId: OP,
    vehicleId: V1,
    hasOpenPrimaryAssignment: true,
    cutPoint: 'fuel_pump',
    profile: homologated,
    blockTermsTextVersion: 'block-terms-v1/40kmh',
    currentTermsVersion: 1,
    ceilingKmh: 40,
    ...over,
  }
}
const code = (i: AvailabilityInput) => {
  const r = checkBlockAvailability(i)
  return r.available ? 'OK' : r.code
}

describe('T-016 disponibilidade do bloqueio — CT-CMD-001 e CT-CMD-019 (parte pura)', () => {
  it('tudo válido → disponível', () => expect(code(base())).toBe('OK'))
  it('sem vínculo primário aberto → NO_PRIMARY_DEVICE', () =>
    expect(code(base({ hasOpenPrimaryAssignment: false, cutPoint: null }))).toBe('NO_PRIMARY_DEVICE'))
  it('cut_point NULL → CUT_POINT_MISSING', () => expect(code(base({ cutPoint: null }))).toBe('CUT_POINT_MISSING'))
  it('perfil draft fora da bancada → PROFILE_NOT_HOMOLOGATED', () =>
    expect(code(base({ profile: { ...homologated, status: 'draft', hasHomologationRef: false } }))).toBe(
      'PROFILE_NOT_HOMOLOGATED',
    ))
  it('perfil draft com relé e seção completa na operadora de bancada → disponível', () =>
    expect(
      code(base({ operatorId: BENCH, profile: { ...homologated, status: 'draft', hasHomologationRef: false } })),
    ).toBe('OK'))
  it('perfil homologated com relay unknown → RELAY_UNSUPPORTED', () =>
    expect(code(base({ profile: { ...homologated, relay: 'unknown' } }))).toBe('RELAY_UNSUPPORTED'))
  it('escopo none → BLOCK_SCOPE_DISABLED; pilot só libera o veículo listado', () => {
    expect(code(base({ blockScope: { kind: 'none' } }))).toBe('BLOCK_SCOPE_DISABLED')
    expect(code(base({ blockScope: { kind: 'pilot', vehicleIds: [V2] } }))).toBe('BLOCK_SCOPE_DISABLED')
    expect(code(base({ blockScope: { kind: 'pilot', vehicleIds: [V1] } }))).toBe('OK')
  })
  it('despacho desligado → COMMAND_DISPATCH_DISABLED', () =>
    expect(code(base({ dispatchEnabled: false }))).toBe('COMMAND_DISPATCH_DISABLED'))
  it('termo ausente, versão velha ou teto maior que o aceito → BLOCK_TERMS_MISSING', () => {
    expect(code(base({ blockTermsTextVersion: null }))).toBe('BLOCK_TERMS_MISSING')
    expect(code(base({ blockTermsTextVersion: 'block-terms-v1/20kmh' }))).toBe('BLOCK_TERMS_MISSING')
    expect(code(base({ blockTermsTextVersion: 'block-terms-v1/20kmh', ceilingKmh: 10 }))).toBe('OK')
    expect(code(base({ blockTermsTextVersion: 'block-terms-v0/40kmh' }))).toBe('BLOCK_TERMS_MISSING')
  })
  it('suspended_commercial não muda nada (INV-09); closed → TENANT_CLOSED', () => {
    expect(code(base({ tenantStatus: 'suspended_commercial' }))).toBe('OK')
    expect(code(base({ tenantStatus: 'closed' }))).toBe('TENANT_CLOSED')
  })
  it('desbloqueio ignora escopo, termo, cut_point e despacho desligado; aceita perfil suspended', () => {
    const r = checkUnblockAvailability(
      base({
        blockScope: { kind: 'none' },
        blockTermsTextVersion: null,
        cutPoint: null,
        dispatchEnabled: false,
        profile: { ...homologated, status: 'suspended' },
      }),
    )
    expect(r).toEqual({ available: true })
    expect(checkUnblockAvailability(base({ hasOpenPrimaryAssignment: false }))).toEqual({
      available: false,
      code: 'NO_PRIMARY_DEVICE',
    })
  })
  it('parseBlockScope e isBlockTermsValid', () => {
    expect(parseBlockScope('none')).toEqual({ kind: 'none' })
    expect(parseBlockScope(`pilot:${V1},${V2}`)).toEqual({ kind: 'pilot', vehicleIds: [V1, V2] })
    expect(() => parseBlockScope('pilot:abc')).toThrow()
    expect(isBlockTermsValid('block-terms-v1/40kmh', 1, 40)).toBe(true)
    expect(isBlockTermsValid('block-terms-v1/40kmh', 2, 40)).toBe(false)
  })
})
```

`tests/acceptance/T-016/state-machine.test.ts`

```ts
import {
  attributeEvidence,
  type CommandView,
  confirmationDecision,
  isAllowedTransition,
  mapDispatchOutcome,
  reduceCommand,
  TRANSITIONS,
  unblockFinalState,
} from '@tracksys/domain'
import { describe, expect, it } from 'vitest'
import { at, T } from './fixtures.ts'

const PAT = { success: '^engine (stop|resume) ok', failure: 'fail|error' }
const view = (over: Partial<CommandView>): CommandView => ({
  type: 'block',
  state: 'READY',
  createdAt: T,
  expiresAt: at('14:05:00'),
  attempts: [],
  manualSmsTaskEmitted: false,
  ...over,
})

describe('T-016 transições — CT-CMD-009 (parte pura)', () => {
  it('lista tem 23 pares (22 do gatilho de 06 §6 + ARMED>FAILED)', () => expect(TRANSITIONS).toHaveLength(23))
  it('recusa pares fora da lista e regras por tipo', () => {
    expect(isAllowedTransition('block', 'REQUESTED', 'CONFIRMED', { hasAttempts: false })).toBe(false)
    expect(isAllowedTransition('block', 'UNKNOWN', 'DISPATCHING', { hasAttempts: true })).toBe(false)
    expect(isAllowedTransition('unblock', 'READY', 'ARMED', { hasAttempts: false })).toBe(false)
    expect(isAllowedTransition('block', 'DISPATCHING', 'READY', { hasAttempts: true })).toBe(false)
    expect(isAllowedTransition('unblock', 'READY', 'CANCELLED', { hasAttempts: true })).toBe(false)
    expect(isAllowedTransition('block', 'ARMED', 'FAILED', { hasAttempts: false })).toBe(false)
    expect(isAllowedTransition('block', 'ARMED', 'FAILED', { hasAttempts: true })).toBe(true)
    expect(isAllowedTransition('block', 'UNKNOWN', 'CONFIRMED', { hasAttempts: true })).toBe(true)
  })
})

describe('T-016 mapDispatchOutcome — CT-CMD-011 (parte pura)', () => {
  const base = { offlineErrorPattern: 'offline', expiresAt: at('14:05:00'), priorResults: [] as const }
  it('200 → sent e AWAITING_CONFIRMATION', () =>
    expect(
      mapDispatchOutcome({ ...base, type: 'block', outcome: { kind: 'http', status: 200, body: '{}' }, now: T, gprsAttemptsIncludingThis: 1 }),
    ).toEqual({ attemptResult: 'sent', to: 'AWAITING_CONFIRMATION', stateReason: null }))
  it('202 → queued e UNKNOWN queued_by_traccar', () =>
    expect(
      mapDispatchOutcome({ ...base, type: 'block', outcome: { kind: 'http', status: 202, body: '' }, now: T, gprsAttemptsIncludingThis: 1 }),
    ).toEqual({ attemptResult: 'queued', to: 'UNKNOWN', stateReason: 'queued_by_traccar' }))
  it('400 offline às 14:00:10 → ARMED; às 14:05:01 ou na 5ª → FAILED device_offline', () => {
    const offline = { kind: 'http', status: 400, body: 'Device is OFFLINE' } as const
    expect(mapDispatchOutcome({ ...base, type: 'block', outcome: offline, now: at('14:00:10'), gprsAttemptsIncludingThis: 1 })).toEqual({
      attemptResult: 'device_offline', to: 'ARMED', stateReason: 'awaiting_evidence',
    })
    expect(mapDispatchOutcome({ ...base, type: 'block', outcome: offline, now: at('14:05:01'), gprsAttemptsIncludingThis: 1 }).to).toBe('FAILED')
    expect(mapDispatchOutcome({ ...base, type: 'block', outcome: offline, now: at('14:01:00'), gprsAttemptsIncludingThis: 5 }).to).toBe('FAILED')
    expect(mapDispatchOutcome({ ...base, type: 'unblock', outcome: offline, now: at('14:01:00'), gprsAttemptsIncludingThis: 2 }).to).toBe('READY')
  })
  it('timeout: block → UNKNOWN transport_unknown; unblock → AWAITING_CONFIRMATION', () => {
    expect(mapDispatchOutcome({ ...base, type: 'block', outcome: { kind: 'timeout' }, now: T, gprsAttemptsIncludingThis: 1 })).toEqual({
      attemptResult: 'timeout', to: 'UNKNOWN', stateReason: 'transport_unknown',
    })
    expect(mapDispatchOutcome({ ...base, type: 'unblock', outcome: { kind: 'timeout' }, now: T, gprsAttemptsIncludingThis: 1 }).to).toBe(
      'AWAITING_CONFIRMATION',
    )
  })
  it('outro 4xx → rejected e FAILED traccar_rejected', () =>
    expect(
      mapDispatchOutcome({ ...base, type: 'block', outcome: { kind: 'http', status: 400, body: 'bad type' }, now: T, gprsAttemptsIncludingThis: 1 }),
    ).toEqual({ attemptResult: 'rejected', to: 'FAILED', stateReason: 'traccar_rejected' }))
  it('desbloqueio esgotado: UNKNOWN se alguma tentativa pode ter chegado; FAILED se nenhuma', () => {
    expect(unblockFinalState(['device_offline', 'sent', 'device_offline'])).toEqual({ to: 'UNKNOWN', stateReason: 'unblock_unconfirmed' })
    expect(unblockFinalState(['device_offline', 'not_sent', 'sms_rejected'])).toEqual({ to: 'FAILED', stateReason: 'not_delivered' })
  })
})

describe('T-016 confirmação — CT-CMD-012 (parte pura)', () => {
  const c = (over: Partial<Parameters<typeof confirmationDecision>[0]>) =>
    confirmationDecision({
      type: 'block', confirmation: 'ack_and_relay_state', patterns: PAT, attemptStartedAt: T, now: at('14:00:10'),
      confirmTimeoutS: 60, lateMode: false, ack: null, relay: null, fix: null, ...over,
    })
  const ack = (text: string, hms = '14:00:04') => ({ text, eventTime: at(hms), processingMode: 'live' as const })
  it('ack de sucesso + relé blocked às 14:00:09 → confirmed', () =>
    expect(c({ ack: ack(' Engine Stop OK '), relay: { state: 'blocked', observedAt: at('14:00:09') } })).toEqual({ kind: 'confirmed' }))
  it('só o ack até 14:01:00 → deadline_passed', () =>
    expect(c({ ack: ack('engine stop ok'), now: at('14:01:00') })).toEqual({ kind: 'deadline_passed' }))
  it('ack + relé unblocked após o início → contradictory', () =>
    expect(c({ ack: ack('engine stop ok'), relay: { state: 'unblocked', observedAt: at('14:00:09') } })).toEqual({ kind: 'contradictory' }))
  it('padrão de falha → failed ack_failure', () => expect(c({ ack: ack('engine stop fail') })).toEqual({ kind: 'failed', reason: 'ack_failure' }))
  it('texto sem padrão → evidence_only', () => expect(c({ ack: ack('param=1') })).toEqual({ kind: 'evidence_only' }))
  it('ack_only com sucesso → confirmed; HTTP 200 sem ack nunca confirma', () => {
    expect(c({ confirmation: 'ack_only', ack: ack('engine stop ok') })).toEqual({ kind: 'confirmed' })
    expect(c({})).toEqual({ kind: 'pending' })
  })
  it('evidência em backfill só vira evidence_only (INV-05)', () =>
    expect(c({ ack: { ...ack('engine stop ok'), processingMode: 'backfill' }, relay: null })).toEqual({ kind: 'evidence_only' }))
})

describe('T-016 evidência tardia — CT-CMD-013 (parte pura)', () => {
  it('ack de bloqueio às 14:04 com desbloqueio iniciado às 14:03:30 não é atribuído', () => {
    const attempts = [
      { id: 'b1', type: 'block' as const, startedAt: at('14:00:00') },
      { id: 'u1', type: 'unblock' as const, startedAt: at('14:03:30') },
    ]
    expect(attributeEvidence(attempts, { type: 'block', at: at('14:04:00') })).toBeNull()
    expect(attributeEvidence(attempts.slice(0, 1), { type: 'block', at: at('14:04:00') })).toBe('b1')
  })
})

describe('T-016 redutor — trilhas de 06 §5, §8.4 e §9', () => {
  it('block ARMED vencido sem tentativa → EXPIRED; com tentativa offline → FAILED device_offline', () => {
    expect(reduceCommand(view({ state: 'ARMED' }), { kind: 'tick', now: at('14:05:15'), smsEnabled: true, confirmTimeoutS: 60 }).to).toBe('EXPIRED')
    const withAttempt = view({ state: 'ARMED', attempts: [{ seq: 1, channel: 'gprs', startedAt: at('14:00:10'), result: 'device_offline' }] })
    expect(reduceCommand(withAttempt, { kind: 'tick', now: at('14:05:15'), smsEnabled: true, confirmTimeoutS: 60 })).toMatchObject({
      to: 'FAILED', stateReason: 'device_offline',
    })
  })
  it('block DISPATCHING com tentativa pendente e reinício do worker → UNKNOWN worker_restart, sem nova tentativa', () => {
    const r = reduceCommand(
      view({ state: 'DISPATCHING', attempts: [{ seq: 1, channel: 'gprs', startedAt: T, result: 'pending' }] }),
      { kind: 'worker_restart', now: at('14:02:00'), confirmTimeoutS: 60 },
    )
    expect(r.to).toBe('UNKNOWN')
    expect(r.stateReason).toBe('worker_restart')
    expect(r.effects).toContainEqual({ kind: 'finish_attempt', seq: 1, result: 'unknown' })
    expect(r.effects.some((e) => e.kind === 'create_attempt')).toBe(false)
  })
  it('unblock DISPATCHING com reinício → READY e próxima tentativa 60 s após a anterior', () => {
    const r = reduceCommand(
      view({ type: 'unblock', state: 'DISPATCHING', attempts: [{ seq: 1, channel: 'gprs', startedAt: T, result: 'pending' }] }),
      { kind: 'worker_restart', now: at('14:00:20'), confirmTimeoutS: 60 },
    )
    expect(r.to).toBe('READY')
    expect(r.effects).toContainEqual({ kind: 'schedule_dispatch', at: at('14:01:00') })
  })
  it('unblock aos 120 s cria tentativa sms se DEC-01 ativa; senão tarefa manual uma vez', () => {
    const attempts = [
      { seq: 1, channel: 'gprs' as const, startedAt: T, result: 'device_offline' as const },
      { seq: 2, channel: 'gprs' as const, startedAt: at('14:01:00'), result: 'device_offline' as const },
    ]
    const v = view({ type: 'unblock', state: 'READY', attempts })
    expect(reduceCommand(v, { kind: 'tick', now: at('14:02:00'), smsEnabled: true, confirmTimeoutS: 60 }).effects).toContainEqual({
      kind: 'create_attempt', channel: 'sms', seq: 3,
    })
    expect(reduceCommand(v, { kind: 'tick', now: at('14:02:00'), smsEnabled: false, confirmTimeoutS: 60 }).effects).toContainEqual({
      kind: 'manual_sms_task',
    })
    expect(
      reduceCommand({ ...v, manualSmsTaskEmitted: true }, { kind: 'tick', now: at('14:02:30'), smsEnabled: false, confirmTimeoutS: 60 })
        .effects,
    ).not.toContainEqual({ kind: 'manual_sms_task' })
  })
  it('block nunca recebe tentativa sms nem nova tentativa após tentativa incerta', () => {
    const v = view({ state: 'READY', attempts: [{ seq: 1, channel: 'gprs', startedAt: T, result: 'timeout' }] })
    expect(reduceCommand(v, { kind: 'dispatch_requested', now: at('14:01:00') })).toEqual({ to: null, stateReason: null, effects: [] })
    expect(
      reduceCommand(view({ state: 'ARMED' }), { kind: 'tick', now: at('14:02:00'), smsEnabled: true, confirmTimeoutS: 60 }).effects.some(
        (e) => e.kind === 'create_attempt',
      ),
    ).toBe(false)
  })
  it('failover leva AWAITING_CONFIRMATION de unblock a UNKNOWN failover', () =>
    expect(
      reduceCommand(view({ type: 'unblock', state: 'AWAITING_CONFIRMATION', attempts: [{ seq: 1, channel: 'gprs', startedAt: T, result: 'sent' }] }), {
        kind: 'failover',
        now: at('14:00:30'),
      }),
    ).toMatchObject({ to: 'UNKNOWN', stateReason: 'failover' }))
  it('UNKNOWN com evidência tardia confirmada → CONFIRMED e fecha o alerta', () => {
    const r = reduceCommand(view({ state: 'UNKNOWN', attempts: [{ seq: 1, channel: 'gprs', startedAt: T, result: 'timeout' }] }), {
      kind: 'confirmation',
      now: at('14:03:00'),
      result: { kind: 'confirmed' },
    })
    expect(r.to).toBe('CONFIRMED')
    expect(r.effects).toContainEqual({ kind: 'close_unknown_alert' })
  })
  it('cancelar só sem tentativa', () => {
    expect(reduceCommand(view({ state: 'ARMED' }), { kind: 'cancel', now: at('14:01:00'), reason: 'cancelled_by_user' }).to).toBe('CANCELLED')
    expect(
      reduceCommand(view({ type: 'unblock', state: 'READY', attempts: [{ seq: 1, channel: 'gprs', startedAt: T, result: 'device_offline' }] }), {
        kind: 'cancel', now: at('14:01:00'), reason: 'cancelled_by_user',
      }).to,
    ).toBeNull()
  })
})
```

`tests/acceptance/T-016/texts.test.ts`

```ts
import { armedReasonText, effectText, relayBadgeText, stateTitle } from '@tracksys/domain'
import { describe, expect, it } from 'vitest'
import { at, T } from './fixtures.ts'

describe('T-016 textos — CT-CMD-021', () => {
  it('fuel_pump com teto 40 e TTL de 5 min', () => {
    const t = effectText({ cutPoint: 'fuel_pump', ceilingKmh: 40, ttlMin: 5 })
    expect(t).toContain('inclusive em movimento até 40 km/h')
    expect(t).toContain('aguarda até 5 min')
  })
  it('fuel_pump com teto 0', () =>
    expect(effectText({ cutPoint: 'fuel_pump', ceilingKmh: 0, ttlMin: 5 })).toContain('Só é enviado com o veículo parado.'))
  it('starter e ignition', () => {
    expect(effectText({ cutPoint: 'starter', ceilingKmh: 40, ttlMin: 5 })).toContain('não dará nova partida')
    expect(effectText({ cutPoint: 'ignition', ceilingKmh: 40, ttlMin: 30 })).toContain('aguarda até 30 min')
  })
  it('UNKNOWN tem o texto exato e nunca se apresenta como bloqueado', () => {
    const u = stateTitle({ type: 'block', state: 'UNKNOWN', stateReason: 'transport_unknown', ceilingKmh: 40, at: T, expiresAt: at('14:05:00') })
    expect(u.title).toBe('Não foi possível confirmar. O veículo pode ou não estar bloqueado')
    expect(u.title.startsWith('Bloque')).toBe(false)
    const states = ['REQUESTED', 'ARMED', 'READY', 'DISPATCHING', 'AWAITING_CONFIRMATION', 'UNKNOWN', 'FAILED', 'REJECTED', 'EXPIRED', 'CANCELLED'] as const
    for (const state of states) {
      const t = stateTitle({ type: 'block', state, stateReason: 'awaiting_speed', ceilingKmh: 40, at: T, expiresAt: at('14:05:00') })
      expect(t.title, state).not.toMatch(/confirmado/i)
    }
  })
  it('ARMED com teto 40 e prazo 14:05Z', () => {
    const a = stateTitle({ type: 'block', state: 'ARMED', stateReason: 'awaiting_speed', ceilingKmh: 40, at: T, expiresAt: at('14:05:00') })
    expect(a).toEqual({ title: 'Aguardando condição segura — veículo acima de 40 km/h', subtitle: 'Expira às 11:05' })
    expect(armedReasonText('awaiting_contact', 40)).toBe('aguardando sinal do rastreador')
  })
  it('CONFIRMED distingue bloqueio de desbloqueio, em BRT', () => {
    expect(stateTitle({ type: 'block', state: 'CONFIRMED', stateReason: null, ceilingKmh: 40, at: at('14:00:09'), expiresAt: T }).title).toBe(
      'Bloqueio confirmado às 11:00',
    )
    expect(stateTitle({ type: 'unblock', state: 'CONFIRMED', stateReason: null, ceilingKmh: 40, at: at('14:00:09'), expiresAt: T }).title).toBe(
      'Desbloqueio confirmado às 11:00',
    )
  })
  it('selo do relé com idade', () => {
    expect(relayBadgeText('blocked', at('11:00:00'), T)).toBe('Relé: bloqueado · observado há 3 h')
    expect(relayBadgeText('unknown', null, T)).toBe('Relé: estado desconhecido')
  })
})
```

`tests/acceptance/T-016/commands.property.test.ts`

```ts
import { type CommandView, evaluateBlock, type EvidenceFix, isAllowedTransition, reduceCommand } from '@tracksys/domain'
import fc from 'fast-check'
import { describe, expect, it } from 'vitest'
import { ASSIGNMENT, input, POLICY_40, T } from './fixtures.ts'

const E = 60_000
const violation = fc.constantFrom('mode', 'invalid', 'coords', 'jump', 'assignment', 'old', 'future', 'speed')
const fixArb = fc.record({ v: violation, offsetMs: fc.integer({ min: -E, max: 0 }), kmh10: fc.integer({ min: 0, max: 400 }) })

function broken(f: { v: string; offsetMs: number; kmh10: number }, i: number): EvidenceFix {
  const fixTime = new Date(T.getTime() + f.offsetMs)
  const base: EvidenceFix = {
    sourceEventId: String(i + 1), assignmentId: ASSIGNMENT, fixTime, receivedAt: fixTime, valid: true,
    latE7: -50892110, lonE7: -428018920, speedKmhX10: f.kmh10, flags: [], processingMode: 'live',
  }
  switch (f.v) {
    case 'mode': return { ...base, processingMode: 'replay' }
    case 'invalid': return { ...base, valid: false }
    case 'coords': return { ...base, latE7: null, lonE7: null }
    case 'jump': return { ...base, flags: ['JUMP_SUSPECT'] }
    case 'assignment': return { ...base, assignmentId: '0192a1b2-0000-7000-8000-0000000000b9' }
    case 'old': return { ...base, fixTime: new Date(T.getTime() - E - 1 - Math.abs(f.offsetMs)), receivedAt: T }
    case 'future': return { ...base, fixTime: new Date(T.getTime() + 120_001), receivedAt: T }
    default: return { ...base, speedKmhX10: null }
  }
}

describe('T-016 P-CMD-1 — evidência inválida nunca produz READY (1.000 execuções)', () => {
  it('ignition e fuel_pump sem IGN_OFF', () => {
    fc.assert(
      fc.property(fc.constantFrom('ignition', 'fuel_pump'), fc.integer({ min: 0, max: 40 }), fc.array(fixArb, { minLength: 1, maxLength: 8 }),
        (cutPoint, ceiling, raw) => {
          const d = evaluateBlock(input({ cutPoint, policy: { ...POLICY_40, maxMovingCutKmh: ceiling }, fixes: raw.map(broken),
            ignition: { value: null, observedAt: null }, motion: 'unknown' }))
          expect(d.decision).toBe('ARMED')
        }),
      { numRuns: 1000 },
    )
  })
})

const UNCERTAIN = new Set(['pending', 'sent', 'queued', 'timeout', 'error', 'unknown'])
const outcomeArb = fc.constantFrom<object>(
  { kind: 'http', status: 200, body: 'ok' }, { kind: 'http', status: 202, body: '' },
  { kind: 'http', status: 400, body: 'device offline' }, { kind: 'http', status: 400, body: 'bad' },
  { kind: 'http', status: 503, body: '' }, { kind: 'timeout' }, { kind: 'not_sent' }, { kind: 'connection_lost' },
)
const evArb = fc.oneof(
  fc.record({ kind: fc.constant('evaluated'), decision: fc.constantFrom('READY', 'ARMED'), reason: fc.constantFrom('awaiting_speed', null) }),
  fc.record({ kind: fc.constant('revalidation_failed'), reason: fc.constant('authorization_revoked') }),
  fc.record({ kind: fc.constant('dispatch_requested') }),
  fc.record({ kind: fc.constant('dispatch_outcome'), outcome: outcomeArb }),
  fc.record({ kind: fc.constant('confirmation'), result: fc.constantFrom({ kind: 'confirmed' }, { kind: 'failed', reason: 'ack_failure' }, { kind: 'contradictory' }, { kind: 'evidence_only' }) }),
  fc.record({ kind: fc.constant('tick'), smsEnabled: fc.boolean() }),
  fc.record({ kind: fc.constant('sms_outcome'), accepted: fc.boolean() }),
  fc.record({ kind: fc.constant('cancel'), reason: fc.constantFrom('cancelled_by_user', 'superseded_by_unblock') }),
  fc.record({ kind: fc.constant('worker_restart') }),
  fc.record({ kind: fc.constant('failover') }),
)

describe('T-016 P-CMD-2 — sequências de 1 a 40 eventos (1.000 execuções)', () => {
  it('nunca gera par fora da lista nem tentativa de block após tentativa incerta', () => {
    fc.assert(
      fc.property(fc.constantFrom('block', 'unblock'), fc.array(fc.record({ dtMs: fc.integer({ min: 0, max: 90_000 }), ev: evArb }), { minLength: 1, maxLength: 40 }),
        (type, steps) => {
          let cmd: CommandView = { type, state: 'REQUESTED', createdAt: T, expiresAt: new Date(T.getTime() + 300_000), attempts: [], manualSmsTaskEmitted: false }
          let now = T.getTime()
          for (const step of steps) {
            now += step.dtMs
            // biome-ignore lint/suspicious/noExplicitAny: gerador monta a união por campos
            const ev = { ...(step.ev as any), now: new Date(now), offlineErrorPattern: 'offline', confirmTimeoutS: 60 }
            const r = reduceCommand(cmd, ev)
            for (const e of r.effects) {
              if (e.kind === 'create_attempt') {
                if (type === 'block') {
                  expect(e.channel).toBe('gprs')
                  expect(cmd.attempts.some((a) => UNCERTAIN.has(a.result))).toBe(false)
                }
                cmd = { ...cmd, attempts: [...cmd.attempts, { seq: e.seq, channel: e.channel, startedAt: new Date(now), result: 'pending' }] }
              }
              if (e.kind === 'finish_attempt') {
                cmd = { ...cmd, attempts: cmd.attempts.map((a) => (a.seq === e.seq ? { ...a, result: e.result } : a)) }
              }
              if (e.kind === 'manual_sms_task') cmd = { ...cmd, manualSmsTaskEmitted: true }
            }
            if (r.to !== null) {
              expect(isAllowedTransition(type, cmd.state, r.to, { hasAttempts: cmd.attempts.length > 0 })).toBe(true)
              cmd = { ...cmd, state: r.to }
            }
          }
        }),
      { numRuns: 1000 },
    )
  })
})
```

`tests/acceptance/T-016/profiles.test.ts`

```ts
import { parseCapabilityProfile } from '@tracksys/contracts'
import { loadDbEnv } from '@tracksys/db'
import pg from 'pg'
import { afterAll, describe, expect, it } from 'vitest'

const env = loadDbEnv()
const app = new pg.Pool({ connectionString: env.DATABASE_URL_APP, max: 1 })
afterAll(async () => {
  await app.end()
})

describe('T-016 perfis migrados passam no schema — CT-CMD-018 (parte de schema)', () => {
  it('todo capability_profile do banco é válido', async () => {
    const res = await app.query<{ model: string; version: number; status: 'draft' | 'homologated' | 'suspended'; evidence_ref: string | null; capabilities: unknown }>(
      'SELECT model, version, status, evidence_ref, capabilities FROM app.capability_profile ORDER BY model, version',
    )
    expect(res.rows.length).toBeGreaterThan(0)
    for (const r of res.rows) {
      const p = parseCapabilityProfile({ status: r.status, evidenceRef: r.evidence_ref, capabilities: r.capabilities })
      expect(p, `${r.model}/${r.version}`).toMatchObject({ ok: true })
    }
  })

  it('o schema recusa homologated com no_queue unknown e relay yes sem seção commands', () => {
    const commands = {
      version: 1, block_type: 'engineStop', unblock_type: 'engineResume', block_type_gated: null, position_request_type: null,
      set_interval_type: null, no_queue: 'unknown', send_timeout_s: 10, confirm_timeout_s: 60, confirmation: 'ack_only',
      offline_error_pattern: 'offline', stopped_speed_max_kmh_x10: 0,
      ack_patterns: { block: { success: 'ok', failure: 'fail' }, unblock: { success: 'ok', failure: 'fail' } },
      relay_persists_power_cycle: 'yes', sms: { unblock_template_ref: 'j16/unblock-v1', block_template_ref: 'j16/block-v1' },
      homologation_ref: 'packages/testkit/fixtures/j16/homologation/2026-11-18/manifest.json',
    }
    const caps = {
      relay: 'yes', relay_state_reported: 'unknown', ignition: 'yes', power_cut_alarm: 'unknown', sos: 'unknown', accelerometer: 'unknown',
      device_speed_gate: 'unknown', secondary_server: 'unknown', domain_support: 'unknown', sms_position: 'unknown', offline_buffer: 'unknown',
    }
    expect(parseCapabilityProfile({ status: 'homologated', evidenceRef: 'x#sha256=00', capabilities: { ...caps, commands } }).ok).toBe(false)
    expect(parseCapabilityProfile({ status: 'draft', evidenceRef: null, capabilities: caps }).ok).toBe(false)
    expect(
      parseCapabilityProfile({ status: 'homologated', evidenceRef: 'x#sha256=00', capabilities: { ...caps, commands: { ...commands, no_queue: 'yes' } } }).ok,
    ).toBe(true)
  })
})
```

O segundo `it` assume que o schema base do perfil (T-002/T-005) aceita os 11 campos de capacidade com `yes|no|unknown` e chaves extras (`normalization`, `commands`). Se o schema base exigir `normalization`, o autor do PR do cartão acrescenta `normalization` mínimo em `caps` antes do merge do cartão.

## Comandos de verificação

```bash
pnpm install
pnpm db:up
pnpm --filter @tracksys/domain test                 # unidade + P-CMD-1/P-CMD-2 de packages/domain/test
pnpm --filter @tracksys/domain mutation             # score ≥ 80% (falha abaixo)
pnpm test:acceptance tests/acceptance/T-016         # 7 arquivos verdes
pnpm verify                                         # lint, typecheck, migrate, db:check, aceite completo
```

Saída esperada: `mutation score` ≥ 80 no relatório do Stryker; `Test Files 7 passed` para `tests/acceptance/T-016`; `pnpm verify` verde.

## Definição de pronto

- [ ] API pública de `@tracksys/domain` exatamente como nesta especificação (os testes congelados compilam sem alteração).
- [ ] `packages/domain` sem `node:*`, `pg`, `process` ou relógio real (Biome `noNodejsModules` verde).
- [ ] P-CMD-1 e P-CMD-2 com `numRuns: 1000`, seed impressa em falha.
- [ ] Stryker com `break: 80` passando; job `mutation` no CI e no noturno.
- [ ] Nenhuma referência a cobrança, `invoice` ou `suspended_commercial` como critério de bloqueio (busca no diff).
- [ ] PR `feat(domain): domínio de comandos puro (T-016)`, N0, plano no PR (modo de planejamento), revisão cruzada registrada.

## Decisões já tomadas

| Dúvida provável | Resposta |
|---|---|
| A transição ARMED → FAILED não existe no gatilho de 06 §6. Por que entrou? | Bloqueio que recebeu `device_offline` volta a ARMED com tentativa gravada; ao vencer o TTL, EXPIRED é proibido (já houve tentativa) e não havia saída legal. `ARMED>FAILED` só para `block` com ≥ 1 tentativa, motivo `device_offline` (06 §7: "após `expires_at`, FAILED `device_offline`"). A T-017 acrescenta o par ao gatilho. Registrado como lacuna de 06 para o fundador aprovar no PR do cartão. |
| O fix mais recente falha `received_at ≥ t − E`. Uso o anterior? | Não. A evidência inteira é descartada (S = ∅): o fix novo pode mostrar velocidade maior (INV-08). |
| "2 fixes a 0 km/h" vale com um fix em movimento depois deles? | Não. Contam os **2 fixes mais recentes** de S. Um fix novo em movimento desfaz a condição. |
| Teto 0 e fix acima de 0: o motivo é `awaiting_speed`? | Não: `awaiting_stop` ("o veículo precisa parar"). "Acima de 0 km/h" não informa nada ao usuário. |
| Sem linha em `command_policy`, qual política vale? | `PLATFORM_DEFAULT_POLICY` (`version` 0): teto 0, E 60 s, TTL 300/1.800 s, `allow_app_block = false` — os valores que 06 §3.3 dá à v1. A 1ª versão gravada pelo `operator_admin` é a v1 (T-017/T-018). |
| Códigos de indisponibilidade: os de 06 §14 ou os de 09 §3? | O pacote devolve códigos neutros sem prefixo `COMMAND_` (`NO_PRIMARY_DEVICE`, `CUT_POINT_MISSING`, `PROFILE_NOT_HOMOLOGATED`, `BLOCK_TERMS_MISSING`…). A T-018 mapeia para o catálogo de [09 §3](../docs/spec/09-api-e-contratos.md), que é o dono dos `code` HTTP. |
| Veículo sem vínculo primário aberto devolve `CUT_POINT_MISSING`? | Não. Devolve `NO_PRIMARY_DEVICE`, no bloqueio e no desbloqueio, o mesmo nome do `availableActions` de [09 §9.1](../docs/spec/09-api-e-contratos.md) [ADOTADO NA v2.0]. `CUT_POINT_MISSING` fica só para vínculo aberto com `cut_point` NULL. |
| Texto de UNKNOWN contém "bloqueado". Isso viola CT-CMD-021? | O texto obrigatório de 06 §15 e 10 §7 contém "estar bloqueado". O teste exige o texto exato, que nenhum título comece com "Bloque" e que nenhum estado fora de CONFIRMED diga "confirmado". Lacuna de redação registrada para 06/10. |
| Hora BRT com `Intl`? | Não. UTC − 3 h fixo ([10 §2](../docs/spec/10-apps-e-ux.md) [PREMISSA] sem horário de verão). |
| `formatAge` não existe em `packages/domain/src/ux/`. | Ele é entregue no F0 (REQ-UX-005, T-008/T-009). Se faltar, pare e registre no PR: não duplique a função. |
| Onde mora o regex de ack e de offline? | Na seção `commands` do perfil (banco). O domínio recebe as strings por parâmetro e compila com flag `i`; regex inválida já é recusada pelo schema. |
| Posso usar `Date.now()` em algum lugar? | Não. Todo instante entra por parâmetro (`now`). O worker passa o `now()` do banco (06 §3.1). |
| O teste de perfis falha porque o J16 `draft` do F0 tem `relay = 'yes'` sem seção `commands`. | O teste está certo (06 §1: o perfil só ganha `relay = "yes"` com a seção `commands` do S07). Crie migration nova com outra `version` do perfil `draft`: `relay = 'unknown'`, ou `relay = 'yes'` com a seção `commands` completa capturada no S07. Nunca edite migration aplicada. |
| Capacidades do perfil são booleanas (`true`/`null`, como no exemplo de 05 §13) ou `yes`/`no`/`unknown`? | `yes`/`no`/`unknown` ([04 §3.3](../docs/spec/04-dominio-e-dados.md), INV-03). O exemplo booleano de 05 §13 é lacuna de redação. |
| Stryker é lento demais no PR? | O job de PR roda incremental e só quando o diff toca `packages/domain/src/commands/`; o noturno roda completo. Meta de [14 §11](../docs/spec/14-qualidade-e-processo-ia.md): ≤ 6 min. |
