# T-008 — Console: mapa ao vivo (SSE) e histórico por veículo/dia

| Campo | Valor |
|---|---|
| Fase | F0 (semana S2: 14–20/10/2026; marco de 20/10: primeira fatia vertical demonstrada) |
| Requisitos | REQ-ALR-016, REQ-ALR-017, REQ-ALR-018, REQ-ALR-019 (servidor SSE); REQ-ARQ-011 (SSE com filtro de escopo); REQ-API-011, REQ-API-012, REQ-API-006, REQ-API-008, REQ-API-018 (rotas deste cartão); REQ-DAD-012 (índice da consulta de histórico, junto com a T-005; o teste de desempenho CT-DAD-012 é da T-028, F1 [ADOTADO NA v2.0]); REQ-NEG-014 (parte HTTP/SSE do CT-NEG-017); REQ-UX-004 e REQ-UX-005 (lado TS); REQ-UX-008 (tela C07); REQ-UX-026 |
| Invariantes | INV-03, INV-04, INV-06, INV-07, INV-12 |
| Risco de revisão | **N2** na tabela 2.3 de [02](../docs/spec/02-escopo-e-fases.md). Os arquivos de servidor (`apps/api/src/realtime/**`, `apps/api/src/telemetry/**`) e a migration de índice seguem o rito **N0** (revisão adversarial por agente de outro fornecedor + leitura linha a linha), porque REQ-ALR-016, REQ-ALR-019 e REQ-API-008 são N0 |
| Depende de | T-005 (tabelas `device*`/`position`, `pg_notify('device_state')`, `seedVerticalSlice`, `decodePositionFlags`), T-006 (sessão cookie/Bearer, contexto RLS, `auth_changed`, revalidação); usa o esqueleto do console da T-007 (plano B na decisão 1) |
| Estimativa | 3 sessões de agente (1: contratos, domínio e rotas de leitura; 2: hub SSE; 3: telas do console) |
| Bloqueado por decisão | nenhuma (intervalos do J16 com padrão seguro, [VALIDAR — DEC-02]) |

## Objetivo

Entregar o tempo real e a leitura de telemetria que o console e o app usam: `GET /api/v1/stream` (SSE com snapshot, revisão, heartbeat, limites e revogação), `GET /api/v1/vehicles` e `GET /api/v1/vehicles/{vehicleId}` com estado honesto, e `GET /api/v1/vehicles/{vehicleId}/history` com lacunas explícitas. Sobre eles, as telas C02 (`/mapa`, todos os veículos da operadora ao vivo) e C07 (`/veiculos/:id/historico?dia=`). As funções puras de estado de apresentação, idade e resumo de histórico nascem aqui em TS, com vetores JSON que o app (T-009/T-010) reutiliza em Dart. Ao fim, os passos 2–5 da fatia vertical ([02 §3](../docs/spec/02-escopo-e-fases.md)) passam por HTTP e SSE.

## Contexto obrigatório

- [07 §11](../docs/spec/07-alertas-e-tempo-real.md): contrato do SSE e REQ-ALR-016 a REQ-ALR-019; [03 §7](../docs/spec/03-arquitetura.md) e REQ-ARQ-011 (NOTIFY com ids e revisão, releitura sob o contexto da conexão, p95 ≤ 2 s do commit ao frame).
- [04 §7.3 e §10 regra 6](../docs/spec/04-dominio-e-dados.md): REQ-DAD-012 (índice nasce com a consulta) e a exceção única de `position_vehicle_fix_idx`.
- [09 §2, §6, §9.1, §9.4](../docs/spec/09-api-e-contratos.md): convenções, rotas, item de veículo, histórico; REQ-API-006, -008, -011, -012, -018.
- [10 §3, §5, §9](../docs/spec/10-apps-e-ux.md): tokens, estados honestos, telas C02 e C07; REQ-UX-004, -005, -008, -026.
- [08 §2, §4, §9](../docs/spec/08-identidade-e-seguranca.md): transporte da sessão, revogação ≤ 60 s, `withContext` com `readOnly`, CORS e CSP de `app.`.
- Cartões T-005 (DDL e payload do NOTIFY) e T-011 (assinatura de `presenceOf`, consumida depois).

## Escopo — fazer

1. Contratos Zod em `packages/contracts` (seção 1) e registro de `vehicles.list`, `vehicles.get`, `vehicles.history`, `stream.open`; OpenAPI e clientes regenerados.
2. Domínio puro em `packages/domain` (seção 2): presença, estado de apresentação, idade, horário BRT, segmentos e resumo de histórico.
3. Vetores compartilhados em `packages/testkit/fixtures/ux/` (seção 3) e `tokens.json` (se ainda não existir).
4. Rotas de leitura em `apps/api/src/telemetry/` (seção 4) e índice de `position` por veículo (seção 5; REQ-DAD-012: o PR cita a consulta de histórico da seção 4 que o justifica, como manda 04 §7.3). A T-008 é dona de `GET /api/v1/vehicles` e `GET /api/v1/vehicles/{vehicleId}` ([02 §2.3](../docs/spec/02-escopo-e-fases.md)).
5. Hub SSE em `apps/api/src/realtime/` (seção 6), que cumpre REQ-ARQ-011: NOTIFY só com ids e revisão, releitura sob o contexto RLS de cada conexão, `id` igual à revisão.
6. Console: C02 e C07 (seção 7).
7. Entradas em `apps/api/test/scope-fixtures.ts` para as 4 rotas (REQ-API-018).
8. Testes de aceite em `tests/acceptance/T-008/` e demonstração da fatia vertical registrada em `docs/runbooks/gates/G0.md`.

## Fora do escopo

- Adaptador SQL do evento `alert` sobre `app.alert`: o hub expõe a porta `AlertSource` e usa `NullAlertSource` (decisão 8). Evento SSE `command.state` (F1).
- `availableActions.watchMode` real (T-011); disponibilidade de comando (T-018, F1); filtro `presence` em `GET /api/v1/vehicles` (F1).
- Login C01 e cadastro C03–C06 (T-007); fila de alertas C08 (F1); app Flutter (T-009, T-010).
- Conexão de escopo operadora com até 1.000 veículos ([ADIADO PARA O F2]); exportação de histórico (F1).
- Tokens Dart e checagem `tokens-only` (T-009); Sentry, Caddy e deploy (T-003, T-013).

## Arquivos a criar/alterar

```
criar    packages/contracts/design/tokens.json            (só se não existir; conteúdo exato de 10 §3)
criar    packages/contracts/src/design/tokens.ts           (reexporta tokens.json tipado)
criar    packages/contracts/src/realtime/{vehicle-state,alert-event,stream}.ts
criar    packages/contracts/src/http/{vehicles,history}.ts (se vehicles.ts já existir pela T-007: alterar)
alterar  packages/contracts/src/routes/registry.ts  packages/contracts/src/errors/catalog.ts
gerar    packages/contracts/openapi/openapi.json  packages/contracts/generated/{ts,dart}/**
criar    packages/domain/src/alerts/presence.ts
criar    packages/domain/src/ux/{brt,age-format,presentation-state,history-summary,index}.ts
criar    packages/testkit/fixtures/ux/{presentation-vectors,age-vectors,history-vectors}.json
criar    packages/db/migrations/20261016120000_position_vehicle_idx.sql
criar    apps/api/src/telemetry/{telemetry.module,vehicles-read.controller,vehicles-read.repo,history.controller,history.repo,gaps,available-actions}.ts
criar    apps/api/src/realtime/{realtime.module,stream.controller,hub,pg-listener,sse-writer,alert-source,session-revalidator}.ts
alterar  apps/api/src/env.ts  apps/api/src/app.module.ts  apps/api/test/scope-fixtures.ts
criar    apps/console/src/routes/mapa.tsx  apps/console/src/routes/veiculos.$vehicleId.historico.tsx
criar    apps/console/src/live/{sse-parser,stream-client,stream-plan,live-store,fleet-loader,use-live-fleet}.ts
criar    apps/console/src/map/{fleet-layer,marker-icons,interpolate,history-layer}.ts
criar    apps/console/src/components/{fleet-list,fleet-filters,vehicle-panel,state-chip,age-text,reconnect-banner,day-picker,history-summary,history-table}.tsx
criar    apps/console/src/**/*.test.ts(x)                  (unitários, não congelados)
criar    tests/acceptance/T-008/harness.ts  tests/acceptance/T-008/{stream,revocation,vehicles,history,slice-http,presentation,console-live}.test.ts
alterar  docs/runbooks/gates/G0.md                          (evidência da demonstração)
```

## Especificação detalhada

### (1) Contratos (`packages/contracts`)

- `realtime/vehicle-state.ts` — `VehicleStateEvent = z.strictObject({ vehicleId: z.uuid(), deviceId: z.uuid(), isPrimary: z.boolean(), revision: z.number().int().nonnegative(), lastContactAt: iso.nullable(), lastFixAt: iso.nullable(), position: z.strictObject({ latitude: z.number().min(-90).max(90), longitude: z.number().min(-180).max(180), speedKmh: z.number().min(0).nullable(), courseDeg: z.number().int().min(0).max(359).nullable() }).nullable(), ignition: z.boolean().nullable(), motion: z.enum(['moving','stopped','unknown']), relayState: z.enum(['blocked','unblocked','unknown']), powerState: z.enum(['main','battery','unknown']), presence: z.enum(['online','delayed','offline','lost_moving']) })`, com `iso = z.iso.datetime()` (UTC com `Z`). Exemplo exato de [07 §11](../docs/spec/07-alertas-e-tempo-real.md).
- `realtime/alert-event.ts` — `AlertEvent` com os campos do exemplo de 07 §11 (`alertId`, `vehicleId`, `type`, `severity`, `status` ∈ `open|acknowledged|closed`, `startedAt`, `endedAt`, `acknowledgedAt`, `title`, `body`); `type` e `severity` como `z.string().min(1)` (o catálogo é da T-011; o cliente só trata `critical` de forma especial).
- `realtime/stream.ts` — `StreamQuery = z.strictObject({ vehicleIds: z.string().optional() })` transformado em lista de 1 a 200 UUIDs distintos (vazio, repetido, > 200 ou inválido → 422 `VALIDATION_FAILED`); `StreamReady = { vehicles: int, openAlerts: int, serverTime }`; `StreamClose = { reason: 'session_revoked'|'session_expired'|'replaced'|'lifetime'|'overflow'|'shutdown' }`. Entram no OpenAPI como componentes; a rota registra `200: null` com `summary` listando os eventos.
- `http/vehicles.ts` — `VehicleItem` = item de [09 §9.1](../docs/spec/09-api-e-contratos.md) + `presenceThresholds: { delayedAfterS, offlineAfterS, lostMovingAfterS }` (aditivo). `primaryDevice: { id, model: string|null, imeiLast4: string|null, profileStatus: 'draft'|'homologated'|'suspended'|null } | null`; `state: VehicleStateEvent | null` (sem vínculo primário); `stateAge: { contactAgeS: int|null, fixAgeS: int|null }`; `availableActions: { block: {available: false, reason}, unblock: {available: false, reason}, watchMode: {available: boolean, active: boolean} }`.
- `http/history.ts` — resposta de [09 §9.4](../docs/spec/09-api-e-contratos.md) + `availableFrom: iso.nullable()` (aditivo: início do 1º vínculo primário visível no escopo). Itens: `{ fixTime, latitude: number|null, longitude: number|null, speedKmh: number|null, courseDeg: int|null, ignition: boolean|null, valid: boolean, flags: string[] }`. `gaps[]: { from, to, durationS, kind: 'signal_lost_moving'|'no_data' }`.
- Catálogo de erros (se ausentes): `STREAM_SCOPE_TOO_LARGE` (422, extensão `maxVehicles: 200`), `HISTORY_RANGE_TOO_LARGE` (422), `HISTORY_REQUIRES_EXPORT` (422).

### (2) Domínio puro (`packages/domain`)

| Export | Contrato |
|---|---|
| `presenceThresholdsOf(profile)` (`alerts/presence.ts`) | `stopped = normalization.stopped_interval_s ?? 300`, `moving = normalization.moving_interval_s ?? 30` do perfil efetivo (`resolveProfile`, T-005) [VALIDAR — DEC-02] → `{ delayedAfterS: stopped + 60, offlineAfterS: 1800, lostMovingAfterS: max(180, 3 × moving) }`; perfil `null` → `{360, 1800, 180}` |
| `presenceFrom(s, t, now)` | `idadeS = floor((now − lastContactAt)/1000)`, negativo vira 0. Ordem: `lastContactAt = null` → `offline`; `motion = 'moving'` e `ignition !== false` e `idadeS ≥ lostMovingAfterS` → `lost_moving`; `idadeS ≥ offlineAfterS` → `offline`; `idadeS ≥ delayedAfterS` → `delayed`; senão `online` (limiar inclusivo, decisão 3) |
| `presenceOf(state, profile, now)` | `presenceFrom(state, presenceThresholdsOf(profile), now)` — assinatura que a T-011 consome |
| `presentationOf({ state, thresholds, now, openCriticalAlertTitle? })` (`ux/presentation-state.ts`) | Tabela e precedência de [10 §5](../docs/spec/10-apps-e-ux.md) → `{ state, colorToken, iconMaterial, iconLucide, title, subtitle, badges[] }`. `moving`: "Em movimento · {v} km/h" com `v = round(speedKmh)` (meio para cima); sem velocidade "Em movimento". `offline`: "Sem comunicação desde {relógio}" · "Estava {anterior}"; com `lastContactAt = null`: "Sem comunicação" · "Nenhum contato registrado". `lost_moving`: "Comunicação perdida em movimento" · "Pode ser bloqueador de sinal" |
| Selos | `delayed` (presença `delayed`): "Última informação {formatAge(lastContactAt)}". `gps_stale`: presença `online`/`delayed`, `lastFixAt ≠ null` e `lastContactAt − lastFixAt > delayedAfterS` (decisão 4): "GPS sem sinal desde {relógio(lastFixAt)}". `alert`: com `openCriticalAlertTitle` → `{ kind: 'alert', text: título }` |
| `formatAge(at, now)` / `formatAgeSpoken(at, now)` (`ux/age-format.ts`) | Texto de 10 §5: "agora", "há 45 s", "há 13 min", "há 3 h", "há 3 h 15 min", "em 18/10 às 19:10". Falado: "agora", "há 45 segundos", "há 1 minuto", "há 13 minutos", "há 3 horas", "há 3 horas e 15 minutos", "em 18 de outubro às 19:10" |
| `brt.ts` | Deslocamento fixo UTC−03:00: `formatBrtClock(at, now)` ("HH:mm" se mesmo dia BRT de `now`, senão "dd/MM HH:mm"), `formatBrtTime`, `formatBrtDate` ("dd/MM/aaaa"), `brtDayRange('2026-10-20')` → `{ from: '2026-10-20T03:00:00Z', to: '2026-10-21T03:00:00Z' }`, `brtToday(now)` |
| `buildHistorySegments(items, gaps)` / `summarizeHistory(items, gaps)` (`ux/history-summary.ts`) | Só pontos `valid`. Trecho sólido entre pontos consecutivos; lacuna vira trecho `gap` de `gap.from` a `gap.to` com rótulo "Sem dados {HH:mm}–{HH:mm}" (BRT). Resumo: `firstAt`, `lastAt`, `distanceM` = soma de `haversineM` (T-005) só nos trechos sólidos; texto "{x} km" (1 casa, vírgula) ou "≥ {x} km (há lacunas)" quando `gaps` não está vazio |

`anterior` = "em movimento", "parado com ignição ligada", "estacionado", "parado" (stopped + ignição nula) ou "em situação desconhecida". Ícones e `colorToken` exatamente da tabela de 10 §5.

### (3) Vetores compartilhados (`packages/testkit/fixtures/ux/`)

`presentation-vectors.json` (o teste monta `position` com latitude −5.089211 e longitude −42.801892 quando `hasPosition = true`):

```json
{ "now": "2026-10-20T15:20:00Z", "thresholds": { "delayedAfterS": 360, "offlineAfterS": 1800, "lostMovingAfterS": 180 },
  "vectors": [
  { "id": 1, "motion": "moving", "ignition": true, "hasPosition": true, "speedKmh": 48, "lastContactAt": "2026-10-20T15:19:50Z", "lastFixAt": "2026-10-20T15:19:50Z", "expect": { "state": "moving", "color": "moving", "title": "Em movimento · 48 km/h", "subtitle": null, "badges": [] } },
  { "id": 2, "motion": "stopped", "ignition": true, "hasPosition": true, "speedKmh": 0, "lastContactAt": "2026-10-20T15:19:00Z", "lastFixAt": "2026-10-20T15:19:00Z", "expect": { "state": "idle", "color": "idle", "title": "Parado com ignição ligada", "subtitle": null, "badges": [] } },
  { "id": 3, "motion": "stopped", "ignition": false, "hasPosition": true, "speedKmh": 0, "lastContactAt": "2026-10-20T15:16:00Z", "lastFixAt": "2026-10-20T15:16:00Z", "expect": { "state": "parked", "color": "parked", "title": "Estacionado", "subtitle": null, "badges": [] } },
  { "id": 4, "motion": "stopped", "ignition": null, "hasPosition": true, "speedKmh": 0, "lastContactAt": "2026-10-20T15:19:00Z", "lastFixAt": "2026-10-20T15:19:00Z", "expect": { "state": "stopped", "color": "parked", "title": "Parado · ignição desconhecida", "subtitle": null, "badges": [] } },
  { "id": 5, "motion": "stopped", "ignition": false, "hasPosition": true, "speedKmh": 0, "lastContactAt": "2026-10-20T15:12:00Z", "lastFixAt": "2026-10-20T15:12:00Z", "expect": { "state": "parked", "color": "parked", "title": "Estacionado", "subtitle": null, "badges": [{ "kind": "delayed", "text": "Última informação há 8 min" }] } },
  { "id": 6, "motion": "moving", "ignition": true, "hasPosition": true, "speedKmh": 35, "lastContactAt": "2026-10-20T15:16:30Z", "lastFixAt": "2026-10-20T15:16:30Z", "expect": { "state": "lost_moving", "color": "danger", "title": "Comunicação perdida em movimento", "subtitle": "Pode ser bloqueador de sinal", "badges": [] } },
  { "id": 7, "motion": "moving", "ignition": null, "hasPosition": true, "speedKmh": 35, "lastContactAt": "2026-10-20T14:40:00Z", "lastFixAt": "2026-10-20T14:40:00Z", "expect": { "state": "lost_moving", "color": "danger", "title": "Comunicação perdida em movimento", "subtitle": "Pode ser bloqueador de sinal", "badges": [] } },
  { "id": 8, "motion": "moving", "ignition": false, "hasPosition": true, "speedKmh": 12, "lastContactAt": "2026-10-20T15:16:30Z", "lastFixAt": "2026-10-20T15:16:30Z", "expect": { "state": "moving", "color": "moving", "title": "Em movimento · 12 km/h", "subtitle": null, "badges": [] } },
  { "id": 9, "motion": "stopped", "ignition": false, "hasPosition": true, "speedKmh": 0, "lastContactAt": "2026-10-20T14:40:00Z", "lastFixAt": "2026-10-20T14:40:00Z", "expect": { "state": "offline", "color": "offline", "title": "Sem comunicação desde 11:40", "subtitle": "Estava estacionado", "badges": [] } },
  { "id": 10, "motion": "unknown", "ignition": null, "hasPosition": false, "speedKmh": null, "lastContactAt": "2026-10-20T15:19:30Z", "lastFixAt": null, "expect": { "state": "no_position", "color": "offline", "title": "Comunicando, ainda sem posição GPS", "subtitle": null, "badges": [] } },
  { "id": 11, "motion": "unknown", "ignition": null, "hasPosition": true, "speedKmh": null, "lastContactAt": "2026-10-20T15:19:30Z", "lastFixAt": "2026-10-20T15:19:30Z", "expect": { "state": "unknown", "color": "offline", "title": "Situação desconhecida", "subtitle": null, "badges": [] } },
  { "id": 12, "motion": "stopped", "ignition": false, "hasPosition": true, "speedKmh": 0, "lastContactAt": "2026-10-20T15:19:40Z", "lastFixAt": "2026-10-20T14:00:00Z", "expect": { "state": "parked", "color": "parked", "title": "Estacionado", "subtitle": null, "badges": [{ "kind": "gps_stale", "text": "GPS sem sinal desde 11:00" }] } }
] }
```

`age-vectors.json`: `{ "now": "2026-10-20T15:20:00Z", "vectors": [ [at, texto, falado], … ] }` com: `15:20:30Z` (futuro) → "agora"/"agora"; `15:19:55Z` → "agora"; `15:19:50Z` → "há 10 s"/"há 10 segundos"; `15:19:15Z` → "há 45 s"/"há 45 segundos"; `15:19:00Z` → "há 1 min"/"há 1 minuto"; `15:07:00Z` → "há 13 min"/"há 13 minutos"; `14:20:00Z` → "há 1 h"/"há 1 hora"; `12:20:00Z` → "há 3 h"/"há 3 horas"; `12:05:00Z` → "há 3 h 15 min"/"há 3 horas e 15 minutos"; `2026-10-19T15:20:01Z` → "há 23 h 59 min"/"há 23 horas e 59 minutos"; `2026-10-19T15:20:00Z` → "em 19/10 às 12:20"/"em 19 de outubro às 12:20"; `2026-10-18T22:10:00Z` → "em 18/10 às 19:10"/"em 18 de outubro às 19:10" (horas sem data com dia de 20/10).

`history-vectors.json`: vetor `gap` = os 4 itens e o `gaps` do exemplo de 09 §9.4 → segmentos `[sólido p1–p3, gap p3–p4 "Sem dados 08:03–08:09", sólido p4]`, `firstAt 07:58`, `lastAt 08:09`, `distanceM` 315 ± 1, texto "≥ 0,3 km (há lacunas)"; vetor `continuous` = itens p1 e p2, `gaps: []` → 1 segmento sólido, `distanceM` 160 ± 1, texto "0,2 km".

### (4) Rotas de leitura (`apps/api/src/telemetry/`)

Todas com `withContext(pool, ctx, fn, { readOnly: true })`; recurso fora do escopo → 404 `NOT_FOUND` idêntico a inexistente (REQ-API-008).

| Rota (id) | Permissão | Entrada → Saída |
|---|---|---|
| `GET /api/v1/vehicles` (`vehicles.list`) | `vehicle.read` | `?tenantId&q&cursor&limit` (padrão 50, máx. 200) → coleção de `VehicleItem`; keyset por `(coalesce(plate,''), id)`; `q` casa prefixo da placa normalizada ou trecho do apelido sem diferenciar maiúsculas |
| `GET /api/v1/vehicles/{vehicleId}` (`vehicles.get`) | `vehicle.read` | → `VehicleItem` + `ETag` |
| `GET /api/v1/vehicles/{vehicleId}/history` (`vehicles.history`) | `telemetry.history` | `?from&to&cursor&limit` (padrão 1.000, máx. 5.000) → seção 1; limite de taxa 30/min por usuário |

Se a T-007 já tiver criado `vehicles.list`/`vehicles.get` com os campos de cadastro, **acrescente** os campos de estado ao mesmo schema e handler; não crie rota paralela.

Consulta do item (estado do vínculo primário vigente; sob escopo `tenant` a RLS de `app.device` devolve NULL, então `model`, `imeiLast4` e `profileStatus` saem `null` e os limiares usam o perfil `null`):

```sql
SELECT v.id, v.tenant_id, v.plate, v.nickname, v.kind, v.make, v.model, v.color, v.year, v.archived_at,
       a.id AS assignment_id, a.device_id, a.cut_point, d.model AS device_model, right(d.imei, 4) AS imei_last4,
       cp.status AS profile_status, cp.capabilities, s.revision, s.last_contact_at, s.last_fix_at, s.lat_e7, s.lon_e7,
       s.speed_kmh_x10, s.course_deg, s.ignition, s.motion, s.relay_state, s.power_state
FROM app.vehicle v
LEFT JOIN app.device_assignment a ON a.operator_id = v.operator_id AND a.tenant_id = v.tenant_id AND a.vehicle_id = v.id
      AND a.is_primary AND a.valid_from <= now() AND (a.valid_to IS NULL OR a.valid_to > now())
LEFT JOIN app.device d ON d.operator_id = a.operator_id AND d.id = a.device_id
LEFT JOIN app.capability_profile cp ON cp.id = d.capability_profile_id
LEFT JOIN app.device_state s ON s.device_id = a.device_id AND s.assignment_id = a.id
WHERE v.archived_at IS NULL AND ($1::uuid IS NULL OR v.tenant_id = $1)
  AND (coalesce(v.plate, ''), v.id) > ($2::text, $3::uuid)
ORDER BY coalesce(v.plate, ''), v.id
LIMIT $4 + 1;
```

- `position` = `{ latitude: lat_e7/10⁷, longitude: lon_e7/10⁷, speedKmh: speed_kmh_x10/10, courseDeg }` só com `last_fix_at` e `lat_e7` não nulos; senão `null` (INV-03). `stateAge` contra `serverTime` (relógio injetável `CLOCK` do `api`; se não existir, criar `apps/api/src/platform/clock.ts`). IMEI completo nunca sai nesta rota.
- `available-actions.ts` (F0, nunca disponível): `block`/`unblock` com `reason` na ordem `NO_PRIMARY_DEVICE` → `CUT_POINT_MISSING` (`cut_point` NULL) → `PROFILE_NOT_HOMOLOGATED` (status ≠ `homologated` ou desconhecido no escopo) → `COMMAND_DISPATCH_DISABLED`. `watchMode` vem da porta `WatchModeStatusReader` com padrão `{ available: false, active: false }`.
- Histórico, na ordem: schema (422) → veículo no escopo (404) → `to ≤ from` 422 `VALIDATION_FAILED` → `to − from > 604800 s` 422 `HISTORY_RANGE_TOO_LARGE` → `from < agora − 90 d` 422 `HISTORY_REQUIRES_EXPORT` → `to` futuro é cortado em agora. Consulta: `FROM app.position p JOIN app.device_assignment a ON a.operator_id = p.operator_id AND a.tenant_id = p.tenant_id AND a.id = p.assignment_id WHERE p.vehicle_id = $1 AND a.is_primary AND p.fix_time >= $from AND p.fix_time < $to AND (p.fix_time, p.assignment_id) > ($ct, $ca) ORDER BY p.fix_time, p.assignment_id LIMIT $limit + 1`. Cursor = base64url de `{"t": fixTime, "a": assignmentId, "s": speedKmh|null}` validado por Zod (inválido → 422).
- `gaps.ts` (puro): para cada par consecutivo, incluindo o ponto do cursor e o 1º da página: `dt > 180 s` com `speedKmh` anterior ≥ 5 → `signal_lost_moving`; senão `dt > 2400 s` → `no_data` [PREMISSA; intervalos do J16 — DEC-02]. Nada interpolado. `qualitySummary` por página; `flags` por `decodePositionFlags` (T-005); `availableFrom` = `min(valid_from)` dos vínculos primários do veículo visíveis no escopo; `dataWatermark` = maior `received_at` da página (null sem itens).

### (5) Migration de índice

`20261016120000_position_vehicle_idx.sql` (timestamp posterior ao da T-005; ajuste se preciso). Não crie se a T-005 já tiver índice iniciado por `(vehicle_id, fix_time)`. Índice direto no pai, sem `CONCURRENTLY`: é a exceção única de [04 §10](../docs/spec/04-dominio-e-dados.md) regra 6 (entra antes do 1º veículo real, com `position` só com dados de bancada) e o `db:lint` da T-019 a aceita por nome. Nenhum índice em colunas de `device_state` que mudam a cada mensagem (REQ-DAD-012).

```sql
-- migrate:up
SET LOCAL lock_timeout = '5s'; SET LOCAL statement_timeout = '60s';
CREATE INDEX IF NOT EXISTS position_vehicle_fix_idx ON app.position (vehicle_id, fix_time);
-- migrate:down
DROP INDEX IF EXISTS app.position_vehicle_fix_idx;
```

### (6) Hub SSE (`apps/api/src/realtime/`)

1. **Abertura** (`stream.controller.ts`, rota `stream.open`, permissão `telemetry.live`, sem tempo limite de 10 s): autenticação da T-006 **antes** da query (sem credencial → 401 `AUTH_REQUIRED`, mesmo com `?access_token=`); o log de acesso nunca grava a query crua, só a contagem de `vehicleIds` (REQ-SEG-021). Escopo: `SELECT id FROM app.vehicle WHERE archived_at IS NULL [AND id = ANY($1)]` sob o contexto; algum id ausente → 404 para o pedido inteiro; sem `vehicleIds` e > 200 → 422 `STREAM_SCOPE_TOO_LARGE`. Erros saem como Problem Details antes de qualquer byte de stream.
2. **Cabeçalhos**: `reply.hijack()` e `raw.writeHead(200, { ...reply.getHeaders(), 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-cache, no-transform', 'X-Accel-Buffering': 'no' })` — copiar `reply.getHeaders()` preserva CORS, `X-Request-Id` e headers de segurança.
3. **Snapshot**: `retry: 5000`, um `vehicle.state` por linha de `device_state` vinculada aos veículos do escopo (`id: <revision>`), os alertas abertos de `AlertSource.openAlerts(ctx, vehicleIds)`, depois `event: ready`. `Last-Event-ID` é aceito e ignorado (snapshot sempre completo).
4. **Ao vivo**: `pg-listener.ts` mantém um `pg.Client` dedicado (`tracksys_app`) com `LISTEN device_state`, `LISTEN alert_changed`, `LISTEN auth_changed`; queda → reconexão com espera de 1 s dobrando até 30 s e, ao voltar, ressincronização: cada conexão relê seu escopo e recebe só revisões maiores que as enviadas. NOTIFY `device_state` (`{"d","o","t","v","r"}`) é coalescido por 250 ms por dispositivo (fica a maior `r`); para cada conexão inscrita em `v` com `operatorId = o`, relê `device_state` sob o contexto da conexão (uma leitura por dispositivo e contexto distinto); linha invisível → descarta; revisão ≤ última enviada naquela conexão → descarta.
5. **Presença na emissão**: `presenceFrom` com `presenceThresholdsOf(perfil)` no escopo operadora e perfil `null` no escopo `tenant`.
6. **Limites**: 2 conexões por sessão (a 3ª entra e a mais antiga recebe `event: close` + `data: {"reason":"replaced"}` e é encerrada); vida de 60 min (`lifetime`); fila de saída: `raw.write` falso enfileira, `drain` esvazia, fila > 500 → `overflow`; `SIGTERM`/`beforeApplicationShutdown` → `shutdown`. Heartbeat `: keep-alive <RFC 3339 em segundos>` a cada 15 s.
7. **Revogação**: NOTIFY `auth_changed` `{"u"}` → revalida as conexões do usuário pela função da T-006 (sessão + `app.memberships_for_user` + `resolveRequestContext`) em ≤ 5 s; sessão inválida ou contexto diferente → `close` `session_revoked`. A cada 60 s, revalida todas: sessão vencida → `session_expired`; contexto mudou → `session_revoked`.
8. **Env** (Zod em `env.ts`): `SSE_HEARTBEAT_MS=15000`, `SSE_REVALIDATE_MS=60000`, `SSE_LIFETIME_MS=3600000`, `SSE_COALESCE_MS=250`, `SSE_MAX_QUEUE=500`; valores diferentes do padrão só com `NODE_ENV=test`. 200 veículos e 2 conexões são constantes.

### (7) Console (`apps/console`)

- **Cliente SSE** (`live/stream-client.ts`): `fetch` com `credentials: 'include'`, `Accept: text/event-stream`, `Last-Event-ID` e `X-Operator-Id` (quando a sessão escolheu operadora); parser próprio em `sse-parser.ts` (`retry`, `event`, `id`, `data` multilinha, comentários, CRLF). `close` `session_revoked`/`session_expired` e HTTP 401 → `/login`; demais `close` e erro de rede → espera de 1 s dobrando até 30 s, ± 20%. A partir do 3º `replaced` em 5 min, para e mostra "Mapa aberto em outra aba ou janela" + botão "Retomar aqui". SSE caído há > 10 s → faixa "Reconectando…".
- **Plano** (`stream-plan.ts`): `fleet-loader.ts` lê todas as páginas de `GET /api/v1/vehicles?limit=200` e de `GET /api/v1/tenants` (nome do cliente para a busca); `planStreams(ids)` divide em blocos de até 200, no máximo 2. Acima de 400 veículos, transmite ao vivo os 400 primeiros do filtro/busca atual e mostra "Atualização ao vivo de até 400 veículos por vez. Refine a busca."
- **Estado** (`live-store.ts`): por `vehicleId`, guarda só eventos `isPrimary = true`; descarta mesmo `(vehicleId, deviceId)` com revisão ≤ exibida; `deviceId` diferente substitui. `alert` deduplicado por `alertId` com precedência `closed` > `acknowledged` > `open`; selo `alert` só para `critical` não fechado. Apresentação recalculada a cada 10 s; textos de idade a cada 1 s só com `document.visibilityState = 'visible'`.
- **C02 `/mapa`**: MapLibre GL JS com `https://tiles.openfreemap.org/styles/liberty`; enquadra os veículos com posição (margem 64 px; nenhum → Brasil inteiro); ícones desenhados em canvas por estado (36 px, contorno branco de 2 px, tracejado em `offline`/`lost_moving`, seta girada por `courseDeg` só em `moving`, anel `danger` com selo `alert`); interpolação linear de até 1.000 ms entre posições válidas de revisão maior, salto direto com `prefers-reduced-motion`. Lista virtualizada (`@tanstack/react-virtual`) com placa, apelido, cliente, chip (cor + ícone + texto), "Última posição válida {idade}" e selos. Filtros: "Todos", "Em movimento" (`moving`), "Parado" (`idle`, `parked`, `stopped`), "Sem comunicação" (`offline`, `lost_moving`), "Outros" (`no_position`, `unknown`). Busca por placa, apelido ou cliente, sem acento. Clique → painel com estado, selos, "Última posição válida {idade} ({HH:mm})", "Ignição: ligada/desligada/desconhecida", "Alimentação: veículo/bateria interna/desconhecida", velocidade e "Ver histórico do dia". Cores só de `tokens.ts`, aplicadas como variáveis CSS em runtime (nenhum hex em `apps/console/src/`). Mudança de estado anunciada com `aria-live="polite"`.
- **C07 `/veiculos/:id/historico?dia=AAAA-MM-DD`** (padrão: hoje BRT): seletor "Hoje", "Ontem" e calendário de hoje e dos 89 dias anteriores; `brtDayRange` → requisições com `limit=5000` seguindo `nextCursor` até o fim **antes** de desenhar o resumo; trajeto na cor `moving`, lacuna tracejada com o rótulo, marcadores de início e fim, resumo "Primeiro ponto {HH:mm} · Último ponto {HH:mm}" e distância de `summarizeHistory`; tabela virtualizada (hora BRT `HH:mm:ss`, velocidade, ignição, válido "Sim/Não"). Dia antes de `availableFrom` → "Histórico disponível a partir de {dd/MM/aaaa}"; dia sem pontos → "Sem posições neste dia".

## Testes de aceite (congelados)

Base: `seedVerticalSlice` (T-005); usuários `admin.alfa`, `agente.alfa`, `dono.a1`, `dono.a2`, `admin.beta` e sessões (console por cookie com `Origin` de `app.`, app por Bearer; admins com 2FA concluído) pelos helpers de teste da T-006; posições por `ingestTraccar` (T-005); `api` em processo com `CLOCK` controlável; datas dos CTs deslocadas para ontem (UTC) mantendo a hora. `harness.ts` lê eventos SSE com parser de teste próprio.

- `stream.test.ts` — **CT-ALR-016**: `dono.a1` com `?vehicleIds=<V2>` → 404 `application/problem+json` sem bytes de stream; com `?vehicleIds=<V1>` e Bearer → 200 `text/event-stream; charset=utf-8`, `Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no`, 1ª linha `retry: 5000`, 1 `vehicle.state` com `vehicleId = V1` e `id` = `revision`, `ready` com `vehicles = 1`, `openAlerts = 0`; sem credencial e `?access_token=<token válido>` → 401 e o token não aparece no log capturado. **CT-ALR-017**: `agente.alfa` com 250 veículos sem `vehicleIds` → 422 `STREAM_SCOPE_TOO_LARGE`, `maxVehicles = 200`; 201 ids → 422; 3 conexões de 100 veículos na mesma sessão → a 1ª recebe `event: close` com `{"reason":"replaced"}` e termina, as outras 2 seguem recebendo heartbeat. **CT-ALR-018** (servidor): reconexão com `Last-Event-ID: <revisão atual>` recebe o snapshot completo antes de `ready`; `pg_notify('device_state', …)` com `r` menor que a enviada → 0 eventos; posição nova de V1 → `vehicle.state` com revisão maior em ≤ 1 s; 5 posições de V1 em 100 ms → no máximo 2 eventos, o último com a maior revisão; 60 s sem mudança → 4 ± 1 comentários `: keep-alive`. Com `SSE_LIFETIME_MS=2000`, `close` `lifetime` em 2–3 s. **CT-ARQ-011**: SSE aberto de `agente.alfa` (operadora A, escopo todo) e de `admin.beta` (operadora B); posição nova de V1 projetada pela `ingestTraccar` com revisão `r` → `agente.alfa` recebe `vehicle.state` com `id: r` em ≤ 2 s depois do retorno da `ingestTraccar` (commit da projeção); `admin.beta` não recebe nenhum evento (só `: keep-alive`) em 5 s. Com 20 posições de V1 espaçadas de 300 ms, p95 do intervalo commit → frame ≤ 2 s; o payload do NOTIFY capturado por um `LISTEN device_state` de teste só tem as chaves `d`, `o`, `t`, `v` e `r` (nenhuma coordenada).
- `revocation.test.ts` — **CT-ALR-019** e parte SSE do **CT-SEG-007**: `dono.a1` com SSE aberto; `admin.alfa` faz `DELETE /api/v1/memberships/{membership de dono.a1}` → `close` `session_revoked` em ≤ 5 s; nova conexão com o mesmo token → 401. Com o LISTEN de `auth_changed` desligado por injeção, o fechamento ocorre em ≤ 61 s pela revalidação. `POST /api/v1/auth/sign-out` → `session_revoked` em ≤ 5 s.
- `vehicles.test.ts` — **CT-API-011**: V1 com `device_state.ignition = NULL`, `last_fix_at` 15:19:58Z e `CLOCK` 15:20:04Z → `"ignition": null`, `"fixAgeS": 6`, `presenceThresholds = {360, 1800, 180}`; rastreador sem fix → `"position": null`, `"motion": "unknown"`, `"fixAgeS": null`; vínculo com `cut_point` NULL → `availableActions.block.reason = "CUT_POINT_MISSING"`; V1 (`fuel_pump`, perfil `draft`) → `PROFILE_NOT_HOMOLOGATED`; 300 veículos na Alfa → p95 de 20 chamadas de `limit=200` ≤ 300 ms. **CT-API-008**: `dono.a2` em `GET /api/v1/vehicles/{V1}` e em UUID aleatório → 404 com `type`, `title` e `detail` iguais. Escopo: `agente.alfa` recebe `imeiLast4` com 4 dígitos e nenhum corpo casa `/\d{15}/`; `dono.a1` recebe `primaryDevice.model = null`. **CT-API-006** (parte): 120 veículos → páginas de 50, 50 e 20, última com `nextCursor = null`; `limit=201` → 422.
- `history.test.ts` — **CT-API-012**: V1 com 2.880 posições no dia (a cada 30 s desde 03:00Z) → `dono.a1` recebe 1.000 itens em ordem e `nextCursor`; seguindo o cursor, 1.000 e 880, depois `null`; p95 da 1ª página ≤ 500 ms em 20 chamadas; `to − from = 604801 s` → 422 `HISTORY_RANGE_TOO_LARGE`; `from` 91 dias atrás → 422 `HISTORY_REQUIRES_EXPORT`; `limit=5001` → 422; rastreador R1 transferido de V1 para V3 (cliente A1) às 12:00Z → dia de V1 só com `fixTime` < 12:00Z e de V3 só ≥ 12:00Z. Exemplo de 9.4 (4 pontos) → `gaps = [{from: 11:03:00Z, to: 11:09:40Z, durationS: 400, kind: "signal_lost_moving"}]`, `latePoints = 1`, `maxGapS = 400`; com `limit=3`, a lacuna aparece na 2ª página (via cursor). Dois pontos parados a 2.401 s → `no_data`. Vínculo primário iniciado em D+1 13:00Z e dia D pedido → `items = []` e `availableFrom` = D+1 13:00Z. `admin.beta` e `dono.a2` → 404. **REQ-DAD-012** (parte da T-008; o CT-DAD-012 de desempenho com 2,5 M posições é da T-028): depois do `db:migrate`, `pg_indexes` mostra `position_vehicle_fix_idx` em `app.position` com colunas `(vehicle_id, fix_time)`, e cada partição existente de `position` tem índice filho anexado a ele (`pg_inherits`); nenhum índice de `app.device_state` contém `revision`, `last_contact_at`, `last_fix_at`, `lat_e7` ou `lon_e7`. O `down` é provado pelo `pnpm verify` (`db:rollback` e `db:migrate` de novo).
- `slice-http.test.ts` — **CT-NEG-017** (passos 2–5 de [02 §3](../docs/spec/02-escopo-e-fases.md)): SSE abertos de `dono.a1` (V1), `agente.alfa` (escopo todo), `dono.a2` (escopo vazio → `ready` com `vehicles = 0`) e `admin.beta` (V2); posição nova de V1 → `dono.a1` e `agente.alfa` recebem o evento; `dono.a2` e `admin.beta` recebem 0 evento de V1 em 3 s; `dono.a2` → lista vazia e 404 em V1; `admin.beta` → só V2 e 404 em V1; `admin.alfa` → 404 em V2; `agente.alfa` → lista com V1 e o veículo de A2, nenhum da Beta.
- `presentation.test.ts` — **CT-UX-004**: os 12 vetores; o vetor 9 nunca tem título "Estacionado"; o vetor 7 sai `lost_moving` com `tokens.color.danger = #EF4444`; V1 `parked` com contato 15:14:01Z e relógio em 15:20:01Z → selo "Última informação há 6 min". **CT-UX-005**: todos de `age-vectors.json` (texto e falado); a partir de "há 45 s", 15 s depois → "há 1 min". **CT-ALR-018** (redutor do console): exibindo 1048577, chega 1048512 → mantém 1048577; chega 1048601 → exibe 1048601; `deviceId` diferente com `isPrimary = true` substitui. `history-vectors.json` passa em `buildHistorySegments`/`summarizeHistory`.
- `console-live.test.ts` — **CT-UX-026**: `planStreams` de 250 ids → blocos de 200 e 50; com a API real, `agente.alfa` com 250 veículos → `fleet-loader` traz 250, nenhum da Beta; os 2 streams do plano → `ready.vehicles` 200 e 50; `toFeatureCollection(store)` → 250 features; com 2 `offline`, 1 `lost_moving` e o resto `parked`, o filtro "Sem comunicação" devolve 3. **CT-UX-008** (C07): `brtDayRange('2026-10-20')` → `from=2026-10-20T03:00:00Z&to=2026-10-21T03:00:00Z`; resposta de 9.4 → trecho `gap` com "Sem dados 08:03–08:09" e resumo começando com "≥"; `fetch` falso com 2 páginas → 2 requisições antes do resumo; `availableFrom` 2026-10-22T13:00:00Z e dia 21/10 → "Histórico disponível a partir de 22/10/2026".

## Comandos de verificação

```bash
pnpm install
pnpm db:up && pnpm db:migrate && pnpm db:check
pnpm contracts:check                                   # OpenAPI e clientes TS/Dart iguais à regeneração
pnpm lint && pnpm typecheck
pnpm test:acceptance -- tests/acceptance/T-008
pnpm --filter @tracksys/console test && pnpm --filter @tracksys/console build
pnpm verify
pnpm db:rollback && pnpm db:migrate                  # prova o down desta migration (o pnpm verify também prova)
```

Demonstração (registrar em `docs/runbooks/gates/G0.md`, vídeo ≤ 2 min): J16 de bancada (ou capturas reenviadas a `POST /internal/v1/traccar/positions`) → posição nova aparece em `/mapa` de `agente.alfa` sem recarregar; desligar o J16 → após 30 min, "Sem comunicação desde {hora}"; `/veiculos/V1/historico` do dia mostra o trajeto e o horário do 1º e do último ponto igual ao da API. Conferir no DevTools que estilo, sprites e fontes vêm só de `tiles.openfreemap.org` (CSP de 08 §9); outro host → registrar no PR para a T-013 ajustar o Caddyfile.

## Definição de pronto

- [ ] 4 rotas no registro com validação de entrada e saída e caso em `scope-fixtures.ts` (`vehicles.get:cross-operator-404` etc.).
- [ ] `tests/acceptance/T-008/**` verde; `pnpm verify` verde local e no CI; rollback da migration funciona.
- [ ] Revisão adversarial N0 registrada para `apps/api/src/realtime/**`, `apps/api/src/telemetry/**` e a migration.
- [ ] Demonstração registrada no G0; PR `feat(console): mapa ao vivo via SSE e histórico (T-008)` citando REQ, INV, CT e as divergências das decisões 3, 4, 8, 9 e 11.

## Decisões já tomadas (não pergunte, siga)

| # | Dúvida provável | Resposta |
|---|---|---|
| 1 | `apps/console` ainda não existe (T-007 não entrou)? | Crie só o mínimo que a T-007 também usa (Vite, TanStack Router, cliente TS, rota `/login` provisória que chama `sign-in/email`) e registre no PR; ao rebasear sobre a T-007, fique com os arquivos dela. |
| 2 | `EventSource` no console? | Não: ele não envia `X-Operator-Id` nem `Last-Event-ID` sob controle. `fetch` + `ReadableStream` com parser próprio, sem biblioteca nova. |
| 3 | Limiar de presença com `>` (07 §11) ou `≥`? | `≥` (inclusivo). O CT-UX-004 exige "há 6 min" com exatamente 360 s; mostrar a degradação 1 s antes é o lado honesto. Divergência de texto com 07 §11 registrada no PR. |
| 4 | `gps_stale` no vetor 5 (contato e fix às 15:12)? | O selo compara o fix com o **último contato** (`lastContactAt − lastFixAt > delayedAfterS`), não com agora; senão o vetor 5 ganharia "GPS sem sinal" quando o problema é comunicação. Registrado no PR. |
| 5 | Evento com `isPrimary = false`? | Ignorado na exibição do F0 (mapa e lista mostram só o primário). |
| 6 | Operadora com mais de 400 veículos? | Máximo de 2 conexões por sessão; 400 ao vivo pelo filtro atual e faixa explicativa. Conexão de 1.000 é F2. |
| 7 | Duas abas do console disputando conexões? | Reconexão com espera, como manda 07 §11; após o 3º `replaced` em 5 min, para e oferece "Retomar aqui". |
| 8 | Evento `alert` sem a tabela `app.alert` (T-011 é S3)? | Porta `AlertSource` + `NullAlertSource` (snapshot sem alertas, `openAlerts = 0`); LISTEN de `alert_changed` já ligado chamando a porta. O adaptador SQL entra com a T-011 (pendência registrada no PR). |
| 9 | `presence.ts` está na lista de arquivos da T-011? | Nasce aqui (S2) com a assinatura `presenceOf(state, profile, now)` da T-011, que passa a só reutilizá-lo. |
| 10 | Titular (`tenant`) não lê `app.device` (RLS tipo C da T-005)? | Correto e intencional: `model`, `imeiLast4` e `profileStatus` saem `null` e os limiares usam o padrão J16. Nunca trocar de contexto para buscar o perfil. |
| 11 | Nova conexão após membership revogada: 401 (CT-ALR-019) ou 404 (08 §4 item 3)? | 401 `AUTH_REQUIRED` na rota de stream, como manda o CT-ALR-019; as demais rotas seguem a T-006. Divergência registrada no PR. |
| 12 | Hub com pg-boss ou Redis? | Não (ADR-002): NOTIFY + releitura sob RLS no próprio `api`, um processo no F0. |
| 13 | Horário BRT com fuso `America/Sao_Paulo`? | Deslocamento fixo UTC−03:00 ([10 §2](../docs/spec/10-apps-e-ux.md) item 6, sem horário de verão [PREMISSA]); vetores dependem disso. |
| 14 | Distância do histórico atravessando lacuna? | Não soma trecho de lacuna; por isso "≥". Uma casa decimal, vírgula. |
| 15 | Dependência nova? | Só `maplibre-gl` e `@tanstack/react-virtual` no console (stack de 03/ADR-007); nenhuma no `api`. |
