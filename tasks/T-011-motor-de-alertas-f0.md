# T-011 — Motor de alertas do F0

| Campo | Valor |
|---|---|
| Fase | F0 (semana S3: 21–27/10/2026; marco 27/10: alerta provocado chega ao celular, com a T-012) |
| Requisitos | REQ-ALR-001 a REQ-ALR-010 (abertura, fechamento, episódio e evidência; a entrega push é da T-012); REQ-ALR-014 (fila e reconhecimento, exceto o evento SSE, que é da T-008); REQ-ALR-015 (marcos t0–t3) |
| Invariantes | INV-01, INV-03, INV-04, INV-05, INV-07, INV-08 (vigilância nunca dispara comando) |
| Risco de revisão | **N1** — revisão cruzada de outro fornecedor; fundador lê o resumo dirigido |
| Depende de | T-005 (outbox, `device_state`, `insertOutboxEvent`, `list_silent_devices`, `list_operator_ids`, `outbox_claim`), T-002 (capacidades do J16). **De fato:** T-006 (sessão, contexto RLS por requisição e `audit_log`, usados pelas rotas) — entregue no S2 |
| Estimativa | 3 sessões de agente (1: migration, pg-boss, relay e domínio puro; 2: consumidor, laços de silêncio e expiração; 3: rotas e aceite) |
| Bloqueado por decisão | DEC-02 (gatilhos de `power_cut` e `sos`, intervalos do J16). Padrão seguro: capacidade `unknown` → tipo indisponível; limiares de 180 s e 1.800 s |

## Objetivo

Abrir e fechar, de forma idempotente e com evidência, os episódios de alerta do F0 — `ignition_on`, `watch_mode_breach`, `power_cut`, `sos`, `offline` e `signal_lost_moving` — a partir do `device.state.updated.v1` gravado pela ingestão e de um laço de silêncio, sem nunca abrir alerta de capacidade não confirmada (INV-03) nem gerar efeito em fato antigo ou reprocessado (INV-05). Entrega também o modo vigilância (cerca âncora de 150 m), a fila de alertas da central com reconhecimento auditado, o relay da outbox sobre pg-boss e os marcos de latência t0–t3 que a T-012 completa com o envio ao FCM.

## Contexto obrigatório

- [07](../docs/spec/07-alertas-e-tempo-real.md) §2–§6, §9, §10, §12: catálogo, avaliação, silêncio, vigilância, episódios, fila, latência.
- [05 §10](../docs/spec/05-ingestao-e-telemetria.md): `device.state.updated.v1` (`transitions`, `location`, `previousLocation`, `processingMode`).
- [04](../docs/spec/04-dominio-e-dados.md) §3.6, §4.2 (tipo A), §4.4 (`outbox_claim`, `list_silent_devices`, `list_operator_ids`).
- [ADR-002](../docs/adr/ADR-002-postgres-unico-fila-barramento.md): pg-boss 10, outbox + LISTEN/NOTIFY, payload só com ids.
- [T-005](T-005-ingestao-traccar-inbox-projecao.md) e [T-002](T-002-spike-j16-bancada.md): aplicador, `seedVerticalSlice`, capacidades `yes|no|unknown`.

## Escopo — fazer

1. Migration `20261021120000_alertas.sql` com o SQL exato da seção (1).
2. pg-boss 10 (2): script `pnpm db:boss` (dono cria e migra o schema `pgboss`, cria as filas de `packages/db/src/queues.ts` e concede ao `tracksys_app`); `verify` e CI passam a rodar `pnpm db:boss` logo após `pnpm db:migrate`.
3. Relay da outbox no worker (3) e rota `device.state.updated.v1 → alerts.evaluate`.
4. Domínio puro em `packages/domain/src/alerts/` (4): catálogo, disponibilidade, regras, episódios, vigilância, presença e textos.
5. Consumidor `alerts.evaluate` (5), laço de silêncio com incidente de plataforma (6) e laço de expiração de 24 h.
6. Rotas de vigilância, fila e reconhecimento (7) e contratos `alert.opened.v1`/`alert.closed.v1`.
7. Pager do fundador (Pushover) e interface `Metrics` em memória (8); fakes de Pushover e de `GET /api/server` do Traccar em `packages/testkit`.
8. Testes de aceite em `tests/acceptance/T-011/` e testes puros em `packages/domain/test/alerts.test.ts`.

## Fora do escopo

- `alert_delivery`, `push_token`, `alert_preference`, rotas `/me/*`, consumidor `alerts.deliver` e FCM: T-012.
- Evento SSE `alert` e snapshot de alertas abertos: T-008 (aqui só `pg_notify('alert_changed', …)`). Tela da fila no console: sem cartão no F0 (registrado no PR).
- `low_battery`, `overspeed`, `geofence`, destaque de crítico sem reconhecimento (REQ-ALR-020 a 023): F1.
- Exposição Prometheus das métricas e alertas do Grafana: tarefa de observabilidade. Qualquer comando físico (INV-08, INV-11).

## Arquivos a criar/alterar

```
packages/db/migrations/20261021120000_alertas.sql
packages/db/src/queues.ts, packages/db/scripts/boss-setup.ts, package.json (script db:boss; verify), .github/workflows/ci.yml
packages/contracts/src/events/{alert-opened,alert-closed}.v1.ts, packages/contracts/src/http/{alerts,watch-mode}.ts
packages/domain/src/alerts/{catalog,availability,rules,episodes,watch-mode,presence,texts,index}.ts
packages/domain/test/alerts.test.ts
apps/worker/src/outbox/{relay,routes}.ts
apps/worker/src/alerts/{evaluate.consumer,silence.loop,expiry.loop,platform-incident}.ts
apps/worker/src/ops/pager.ts, apps/worker/src/observability/metrics.ts, apps/worker/src/main.ts
apps/api/src/alerts/{alerts.module,alerts.controller,watch-mode.controller}.ts
packages/testkit/src/fakes/{pushover,traccar}.ts
tests/acceptance/T-011/{schema,rules,evaluate,silence,routes,relay}.test.ts
```

## Especificação detalhada

### (1) Migration — SQL exato

```sql
-- migrate:up
-- T-011 — Alertas e modo vigilância (04 §3.6; 07 §3–§6). INV-01, INV-03, INV-05, INV-07.
-- rls: A
CREATE TABLE app.alert (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL, tenant_id uuid NOT NULL, vehicle_id uuid NOT NULL, device_id uuid NULL,
  type text NOT NULL CHECK (type ~ '^[a-z_]{3,40}$'), severity text NOT NULL CHECK (severity IN ('critical', 'warning', 'info')),
  episode_key text NOT NULL CHECK (length(episode_key) <= 200), started_at timestamptz NOT NULL, ended_at timestamptz NULL,
  evidence jsonb NOT NULL DEFAULT '{}', acknowledged_at timestamptz NULL, acknowledged_by uuid NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT alert_episode_key UNIQUE (episode_key),
  CONSTRAINT alert_scope_key UNIQUE (operator_id, tenant_id, id),
  CONSTRAINT alert_vehicle_fk FOREIGN KEY (operator_id, tenant_id, vehicle_id) REFERENCES app.vehicle (operator_id, tenant_id, id),
  CONSTRAINT alert_device_fk FOREIGN KEY (operator_id, device_id) REFERENCES app.device (operator_id, id),
  CONSTRAINT alert_period_chk CHECK (ended_at IS NULL OR ended_at >= started_at)
);
CREATE INDEX alert_timeline_idx ON app.alert (operator_id, tenant_id, started_at DESC);
CREATE UNIQUE INDEX alert_open_key ON app.alert (device_id, type) WHERE ended_at IS NULL;
CREATE TRIGGER alert_immutable BEFORE UPDATE ON app.alert FOR EACH ROW EXECUTE FUNCTION
  app.tg_immutable_columns('operator_id', 'tenant_id', 'vehicle_id', 'device_id', 'type', 'episode_key', 'started_at');
-- rls: A
CREATE TABLE app.watch_mode (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL, tenant_id uuid NOT NULL, vehicle_id uuid NOT NULL,
  anchor_lat_e7 integer NOT NULL CHECK (anchor_lat_e7 BETWEEN -900000000 AND 900000000),
  anchor_lon_e7 integer NOT NULL CHECK (anchor_lon_e7 BETWEEN -1800000000 AND 1800000000),
  radius_m integer NOT NULL DEFAULT 150 CHECK (radius_m BETWEEN 100 AND 500),
  activated_by uuid NOT NULL, activated_at timestamptz NOT NULL DEFAULT now(), deactivated_at timestamptz NULL,
  CONSTRAINT watch_mode_vehicle_fk FOREIGN KEY (operator_id, tenant_id, vehicle_id) REFERENCES app.vehicle (operator_id, tenant_id, id)
);
CREATE UNIQUE INDEX watch_mode_active_key ON app.watch_mode (vehicle_id) WHERE deactivated_at IS NULL;
CREATE TRIGGER watch_mode_immutable BEFORE UPDATE ON app.watch_mode FOR EACH ROW EXECUTE FUNCTION
  app.tg_immutable_columns('operator_id', 'tenant_id', 'vehicle_id', 'anchor_lat_e7', 'anchor_lon_e7', 'radius_m', 'activated_by', 'activated_at');
ALTER TABLE app.alert ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
ALTER TABLE app.watch_mode ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
CREATE POLICY alert_isolation ON app.alert FOR ALL
  USING (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())))
  WITH CHECK (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())));
CREATE POLICY watch_mode_isolation ON app.watch_mode FOR ALL
  USING (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())))
  WITH CHECK (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())));
GRANT SELECT, INSERT, UPDATE ON app.alert, app.watch_mode TO tracksys_app;

-- migrate:down
DROP TABLE app.watch_mode;
DROP TABLE app.alert;
```

### (2) pg-boss 10

- `packages/db/src/queues.ts`: `export const QUEUES = ['alerts.evaluate'] as const` (a T-012 acrescenta `alerts.deliver`). Política `standard`, `retryLimit: 5`, `retryDelay: 2`, `retryBackoff: true`, `expireInSeconds: 120`.
- `boss-setup.ts` (`pnpm db:boss`), com `DATABASE_URL` do dono: `start()` com migração ligada, `createQueue` de cada fila (cria partição: exige dono [VALIDAR — pg-boss 10]), `stop()`, e então `GRANT USAGE ON SCHEMA pgboss`, `SELECT, INSERT, UPDATE, DELETE ON ALL TABLES`, `USAGE, SELECT ON ALL SEQUENCES` e `EXECUTE ON ALL FUNCTIONS IN SCHEMA pgboss TO tracksys_app`. Idempotente.
- Runtime (`worker` e `api`): `APP_DATABASE_URL`, schema `pgboss`, migração desligada (opção da versão 10 [VALIDAR — ADR-002]). O `api` não consome filas.

### (3) Relay da outbox

`LISTEN outbox_new` numa conexão dedicada + varredura a cada 5 s. Cada rodada, numa transação do `tracksys_app`: `SELECT * FROM app.outbox_claim(500)` e, para cada linha com rota em `routes.ts`, `send(fila, { outboxId, type, operatorId, tenantId, entityId }, { singletonKey: '<fila>:<outboxId>' })` usando o mesmo client (opção `db` do `send` [VALIDAR — pg-boss 10]); linha sem rota só é marcada publicada. Plano B se `db` não existir: `send` antes do claim, com o mesmo `singletonKey`; o consumidor já é idempotente por `episode_key`.

### (4) Domínio puro (`@tracksys/domain`)

| Export | Contrato |
|---|---|
| `ALERT_CATALOG` | Os 6 tipos do F0 com severidade, padrão de preferência, `locked` (`sos`, `watch_mode_breach`) e textos de [07 §2](../docs/spec/07-alertas-e-tempo-real.md) |
| `availableAlertTypes(profile)` | `ignition_on` ⇔ `ignition = 'yes'`; `sos` ⇔ `sos = 'yes'`; `power_cut` ⇔ `power_cut_alarm = 'yes'` ou `normalization.power_source ≠ null`; `watch_mode_breach`, `offline`, `signal_lost_moving` sempre. Qualquer outro valor (`'no'`, `'unknown'`, ausente) → indisponível (INV-03) |
| `evaluateStateEvent(event, ctx)` | `ctx = { profile, openAlerts, watchMode, currentState, now }` → `{ open[], bump[], close[], unexpectedAlarms[] }` com as regras e chaves de [07 §2, §3, §5, §6](../docs/spec/07-alertas-e-tempo-real.md); só `isPrimary = true` |
| `evaluateSilence(candidate, ctx)` | `signal_lost_moving` se `motion = 'moving'`, `ignition IS DISTINCT FROM false` e silêncio > `max(180, 3 × moving_interval_s)` s; `offline` se silêncio > 1.800 s e sem `signal_lost_moving` aberto; `started_at` = `last_contact_at` + limiar, ou `fim do incidente + 10 min` se maior |
| `isStale(severity, originAt, openedAt)` | `critical` > 60 min; demais > 10 min |
| `presenceOf(state, profile, now)` | `lost_moving`, `offline`, `delayed` (> `stopped_interval_s` + 60 s), `online` ([07 §11](../docs/spec/07-alertas-e-tempo-real.md) item 4) |
| `renderAlertText(type, { vehicleLabel, at, closing? })` | Título e corpo PT-BR; `{hora}` em `HH:mm` America/Sao_Paulo; sem coordenadas |

Evidência gravada: `{openRevision, closeRevision, trigger, processingMode, stale, signalCount, lastSignalAt, closeReason, lastLocation, timings: {originAt, receivedAt, projectedAt, openedAt}}`, com `originAt = source.serverTime` (silêncio: limiar cruzado), `receivedAt = source.receivedAt`, `projectedAt = occurredAt` do evento e `openedAt` = relógio do worker.

### (5) Consumidor `alerts.evaluate`

Por job: `withContext(app, { scope: 'operator', operatorId })` → lê o payload da outbox por `outboxId` e valida com `DeviceStateUpdatedV1` → `pg_advisory_xact_lock(hashtextextended('alerts:' || deviceId, 0))` → carrega perfil (`device` → `capability_profile`), alertas abertos do dispositivo (`FOR UPDATE`), vigilância ativa do veículo e `device_state` atual → `evaluateStateEvent` → aplica: `INSERT … ON CONFLICT (episode_key) DO NOTHING RETURNING id`; se inseriu, `insertOutboxEvent('alert.opened.v1')` e `pg_notify('alert_changed', '{"a","o","t","v"}')`; sinal repetido soma `signalCount` e `lastSignalAt` sem evento; fechamento grava `ended_at`, `closeRevision`, `closeReason`, `alert.closed.v1` com `notifyClose = true` só para `contact_resumed` e `power_restored`. Reordenação: se `device_state.revision` > revisão do evento e o estado atual contradiz a abertura, abre e fecha na mesma transação com `superseded`. Alarme de tipo indisponível → `metrics.inc('alerts_unexpected_alarm_total', { alarm })`, sem alerta.

### (6) Laço de silêncio, incidente e expiração

- A cada 15 s, só no worker que obtém `pg_try_advisory_lock(7011)` numa conexão dedicada: verifica incidente; `SELECT * FROM app.list_silent_devices($now)`; para cada candidato, transação com contexto `operator` do candidato e o lock do item (5), relê `device_state` e aplica `evaluateSilence`. Fechamento por contato: no consumidor, evento com `lastContact` em `changes`.
- Incidente ([07 §4](../docs/spec/07-alertas-e-tempo-real.md) item 4) — abertura de `offline`/`signal_lost_moving` suspensa enquanto valer e por mais 10 min: (a) `GET {TRACCAR_API_URL}/api/server` falha (timeout 5 s) em 2 checagens seguidas [VALIDAR — DEC-02 rota]; (b) somando operadoras (`list_operator_ids` + contexto de cada uma), `N` = vínculos com contato nas últimas 24 h ≥ 10 e mais de 50% de `N` com `last_contact_at` em `[now − 480 s, now − 180 s)`; (c) `max(last_contact_at)` < `now − 120 s` e ≥ `now − 720 s`. Início do incidente → 1 page (prioridade 2) ao fundador.
- Expiração a cada 5 min: `power_cut` e `sos` abertos com `lastSignalAt` (ou `started_at`) + 24 h < `now` → `ended_at` = esse instante, `closeReason = 'expired'`, `notifyClose = false`.

### (7) Rotas (`apps/api`, sessão e contexto da T-006; erros Problem Details com `code`)

| Rota | Comportamento |
|---|---|
| `POST /api/v1/vehicles/{vehicleId}/watch-mode` body `{"radiusM"?: 100–500}` | Papéis `tenant_owner`, `tenant_member` com acesso, `operator_admin`, `operator_agent` (outros → 403 `FORBIDDEN_ROLE`). Fora do escopo → 404. Dispositivo primário sem fix válido nas últimas 24 h → 409 `WATCH_MODE_NO_FIX`; `ignition = true` ou `motion = 'moving'` → 409 `WATCH_MODE_VEHICLE_ON`; raio inválido → 422. Já ativo → 200; senão 201. Corpo `{watchModeId, anchor:{latitude, longitude}, radiusM, activatedAt}`; âncora = `device_state.lat_e7/lon_e7`. `audit_log` `watch_mode.activate` |
| `DELETE /api/v1/vehicles/{vehicleId}/watch-mode` | 204 (também sem modo ativo); fecha violação aberta com `deactivated`; `audit_log` `watch_mode.deactivate` |
| `GET /api/v1/alerts?status=open\|acknowledged\|closed&severity=&vehicleId=&from=&to=&cursor=` | `open` = sem `ended_at` e sem reconhecimento; `acknowledged` = sem `ended_at` e reconhecido; `closed` = com `ended_at`. Ordem: não reconhecidos, severidade (`critical` > `warning` > `info`), `started_at` crescente. Página de 50 com `nextCursor` opaco. Item: `alertId, type, typeLabel, severity, status, vehicleId, vehicleLabel, plate, tenantId, tenantName, startedAt, endedAt, acknowledgedAt, acknowledgedBy, lastContactAt` |
| `POST /api/v1/alerts/{id}/acknowledge` body `{"note"?: ≤ 500}` | Só `operator_admin`, `operator_agent`, `search_team` (cliente → 403 `ALERT_ACK_FORBIDDEN`). Fora do escopo → 404. Idempotente (2º pedido devolve o mesmo estado). Fecha com `acknowledged` só `sos`, `watch_mode_breach` e `power_cut` de perfil sem `power_source`. `audit_log` `alert.acknowledge` com `reason = note`. 200 com o item |

### (8) Pager, métricas e env

`pager.ts`: `POST {PUSHOVER_API_URL}/1/messages.json` (`token`, `user`, `title`, `message`, `priority=2`, `retry=60`, `expire=3600`); sem `PUSHOVER_TOKEN` fora de produção, só log `error`. `metrics.ts`: `inc(name, labels)` e `observe(name, value, labels)` com registro em memória consultável nos testes. Env (Zod): `TRACCAR_API_URL`, `PUSHOVER_API_URL` (padrão `https://api.pushover.net`), `PUSHOVER_TOKEN`, `PUSHOVER_USER`.

## Testes de aceite (congelados)

Base comum: `seedVerticalSlice` (T-005), V1 com apelido "Gol prata", perfil de teste inserido pelo dono no `beforeAll` quando o cenário exige capacidade `yes`, mensagens injetadas com `ingestTraccar` (T-005) e handlers chamados em processo (`runRelayOnce`, `handleEvaluateJob`, `runSilenceTick(now)`, `runExpiryTick(now)`) com relógio, `Metrics`, fake de Pushover e fake de Traccar. **Datas dos CTs deslocadas para o dia UTC corrente, mantendo a hora** (partições de `position`); textos em BRT inalterados.

`rules.test.ts` (puro): disponibilidade com `sos = 'unknown'` → indisponível e `'yes'` → disponível; distâncias de CT-ALR-004 (133 m dentro, 200 m fora) com `haversineM`; `renderAlertText('ignition_on', { vehicleLabel: 'Gol prata', at: <hoje>T00:14:03Z })` → "Ignição ligada" — "Gol prata: ignição ligada às 21:14."; `isStale('warning', t, t + 25 min) = true`.

`schema.test.ts`: catálogo sem violação (CAT-01..CAT-07); ISO-01 a ISO-05 para `alert` e `watch_mode`; segundo alerta aberto do mesmo `(device_id, type)` com outra chave → 23505; `UPDATE alert SET type = 'sos'` → 23000; `tracksys_app` com `DELETE` → 42501.

`evaluate.test.ts`
- CT-ALR-001: perfil `sos = 'unknown'` e posição com `alarm = "sos"` → 0 alertas e `alerts_unexpected_alarm_total{alarm="sos"} = 1`; `sos = 'yes'` → 1 alerta `sos` `critical`.
- CT-ALR-002 (parte do alerta): `ignition` `false → true` com `serverTime = <hoje>T00:14:03Z` → 1 `ignition_on` aberto, 1 `alert.opened.v1`; ignição anterior NULL → 0 alertas; depois `true → false` → fechado com `ignition_off`.
- CT-ALR-005 (parte do alerta): `powerCut` às 03:10:00Z abre; às 03:12:00Z `signalCount = 2` e 0 evento novo; `charge = true` às 03:20:00Z fecha com `power_restored` e `notifyClose = true`.
- CT-ALR-006 (parte do alerta): posição e evento `alarm` do mesmo acionamento com 2 s → 1 alerta; reconhecimento por `agente.alfa` fecha com `acknowledged`; `sos` 1 min depois → novo alerta.
- CT-ALR-009: o mesmo job da revisão R com `ignition` `false → true` entregue 3 vezes, 2 em paralelo → 1 alerta com `episode_key = "ignition_on:<deviceId>:<R>"` e 1 `alert.opened.v1`.
- CT-ALR-010 (parte do alerta): `sos` reprocessado (`processingMode = "reprocess"`) → alerta com `evidence.processingMode = "reprocess"`; `ignition_on` com `observedAt` 25 min antes da abertura → `evidence.stale = true` e `stale = true` no evento.
- CT-ALR-015 (t0–t3): `originAt ≤ receivedAt ≤ projectedAt ≤ openedAt`, com `originAt = serverTime`.
- CT-ALR-004: vigilância ativa (âncora −5,0892110, −42,8018920; raio 150; `ignition = 'unknown'`); fix a 133 m e depois a 200 m → 0 alertas; 2º fix seguido a 200 m → 1 `watch_mode_breach` com `evidence.trigger = "distance"`; 3º fix fora → nenhum novo. Nenhuma linha em tabela de comando (INV-08).

`silence.test.ts`
- CT-ALR-007: V1 parado, `last_contact_at = 10:00:00Z`; `runSilenceTick(10:30:14Z)` → `offline` com `started_at = 10:30:00Z`; heartbeat às 10:41:00Z → fechado com `contact_resumed`, `notifyClose = true`. Dado 20 dispositivos com contato às 09:59:50Z e o fake de Traccar falhando desde 10:00:00Z, ticks a cada 15 s até 10:45:00Z → 0 `offline` e o fake de Pushover recebe exatamente 1 page.
- CT-ALR-008: `motion = 'moving'`, `ignition = true`, `last_contact_at = 14:00:00Z`; tick às 14:03:14Z → `signal_lost_moving` com `started_at = 14:03:00Z`; com `ignition = false` às 13:59:50Z → nenhum, e às 14:30:14Z abre `offline`; `signal_lost_moving` aberto há 40 min → nenhum `offline`.
- Expiração: `sos` com `lastSignalAt` = T; `runExpiryTick(T + 24 h + 1 s)` → `expired`, `notifyClose = false`.

`routes.test.ts` (HTTP, sessões de teste da T-006)
- CT-ALR-003: V1 parado, ignição `false`, fix válido há 2 h em (−5,0892110, −42,8018920); `dono.a1` faz POST `{}` → 201 com essa âncora, `radiusM = 150` e `audit_log` `watch_mode.activate`; repetir → 200 com o mesmo `watchModeId`; ignição `true` → 409 `WATCH_MODE_VEHICLE_ON`; `dono.a2` → 404.
- CT-ALR-014 (exceto SSE): na Alfa, `offline` (warning) 10:00, `signal_lost_moving` (critical) 10:05, `ignition_on` (warning) 10:01, e 1 alerta da Beta; `agente.alfa` lista `status=open` → 3 itens na ordem `signal_lost_moving`, `offline`, `ignition_on`; reconhece o primeiro → `acknowledged_by = agente.alfa`, `audit_log` `alert.acknowledge`, `ended_at` NULL e o item sai de `open` e aparece em `acknowledged`; `dono.a1` reconhecendo → 403.

`relay.test.ts`: 1 linha `device.state.updated.v1` na outbox → `runRelayOnce` cria 1 job em `alerts.evaluate` e marca `published_at`; 2ª rodada cria 0 jobs; `telemetry.position.accepted.v1` é marcado publicado sem job.

## Comandos de verificação

```bash
pnpm install
pnpm db:reset && pnpm db:migrate && pnpm db:boss
pnpm db:check                                   # Catálogo OK: nenhuma violação de CAT-01..CAT-07.
pnpm --filter @tracksys/domain test
pnpm test:acceptance -- tests/acceptance/T-011
pnpm verify                                     # T-001, T-002, T-005 e T-011 verdes
pnpm exec dbmate --migrations-dir ./packages/db/migrations --no-dump-schema rollback && pnpm db:migrate
```

## Definição de pronto

- [ ] Comandos verdes local e no CI; `tests/acceptance/T-001`, `T-002` e `T-005` intactos; `T-011/**` congelado no PR.
- [ ] Ensaio em bancada: ignição do J16 ligada gera `ignition_on` em ≤ 10 s após o `serverTime` (consulta em `app.alert`), registrado no PR.
- [ ] PR `feat(alerts): motor de alertas do F0 (T-011)` com REQ, INV, risco N1, revisão cruzada e as decisões 1, 3 e 6 citadas.

## Decisões já tomadas (não pergunte, siga)

| Dúvida provável | Resposta |
|---|---|
| 1. Contexto RLS dos jobs e do laço: `tenant` ou `operator`? | `operator` da operadora do evento/candidato: o consumidor precisa ler `device` e `capability_profile` (tipo C/F). A escrita em `alert` (tipo A) continua barrada para outra operadora. |
| 2. [07](../docs/spec/07-alertas-e-tempo-real.md) diz capacidade `true`/`null` | Leia `'yes'`/`'unknown'` (T-002). Só `'yes'` habilita o tipo. |
| 3. Quem reconhece alerta? | Só a equipe da operadora no F0 (a central trata SOS); cliente recebe 403. Mudança é reversível e fica registrada no PR. |
| 4. pg-boss já existe? | Não; entra aqui (primeiro consumidor). Filas e partições criadas pelo dono em `db:boss`; runtime sem migrar. Sem Redis nem RabbitMQ (ADR-002). |
| 5. Gatilho `watch_mode_immutable` não está em [04](../docs/spec/04-dominio-e-dados.md) | Entra por REQ-DAD-001 (colunas de escopo e de âncora imutáveis); a desativação só muda `deactivated_at`. |
| 6. `alert.opened.v1` de modo não ao vivo ou `stale` é gravado? | Sim, com `processingMode` e `stale` no payload; a T-012 não cria `alert_delivery` para eles (INV-05). |
| 7. Silêncio de um dispositivo sem perfil | `moving_interval_s` ausente → 30 s (limiar 180 s); `offline` sempre 1.800 s [VALIDAR — DEC-02]. |
| 8. Laço de silêncio em dois workers | Só quem tem `pg_try_advisory_lock(7011)` roda; o outro tenta de novo a cada 15 s. |
| 9. Rotas sem a T-006 mergeada | Pare: rotas exigem sessão e contexto por requisição. Domínio, consumidor e laços seguem; registre no PR. |
| 10. `alerts.deliver` sem consumidor ainda | A rota `alert.* → alerts.deliver` é da T-012; até lá esses eventos ficam só publicados. |
