# T-012 — Push FCM no servidor: tokens, preferências, `alert_delivery` e entrega

| Campo | Valor |
|---|---|
| Fase | F0 (semana S3: 21–27/10/2026; marco 27/10: alerta provocado vira entrega `sent` no fake de FCM e chega ao celular pela T-032) |
| Requisitos | REQ-ALR-011, REQ-ALR-012, REQ-ALR-013; parte de entrega de REQ-ALR-002, REQ-ALR-005, REQ-ALR-006, REQ-ALR-007, REQ-ALR-009 e REQ-ALR-010; REQ-ALR-001 (disponibilidade nas preferências); REQ-ALR-015 (t4 e métricas de latência); REQ-DAD-006 (`app.claim_push_token`); REQ-ARQ-009 (3ª parte do CT-ARQ-009; outbox e publicador da outbox são da T-005); REQ-QLD-009 (extensão da P5 da T-011 com o fake de FCM e `alert_delivery`; fecha o CT-QLD-009); REQ-QLD-011 (ISO-01..ISO-05 em `alert_preference` e `alert_delivery`, Postgres real) |
| Invariantes | INV-01, INV-03, INV-05, INV-07 |
| Risco de revisão | N0 pelo caminho: `packages/db/migrations/20261022120000_push.sql` e `packages/db/catalog-allowlist.json` (`app.claim_push_token`, `SECURITY DEFINER`, CAT-07); demais arquivos N1. Revisor de outro fornecedor e leitura humana linha a linha só nos arquivos N0 |
| Depende de | T-004 (CAT-07, `app.tg_immutable_columns()` e `membership_definer_read`), T-005 (publicador da outbox e `OUTBOX_ROUTES`), T-006 (`withContext`, sessão e `signInAs(world, user, { clientKind })` de `packages/testkit`), T-011 (alertas, rota `device.state.updated.v1` da outbox, filas, `renderAlertText`, `Metrics`, rotas de vigilância e de alertas) |
| Estimativa | 2 sessões de agente (1: migration, função, rotas e leituras; 2: consumidor `alerts.deliver`, adaptador FCM, métricas e propriedade P5) |
| Bloqueado por decisão | Projeto Firebase com conta de serviço (ação do fundador no S2). O app que recebe o push, o iOS (DEC-03) e a chave APNs são da [T-032](T-032-app-push-alertas-vigilancia-notificacoes.md) |

## Objetivo

Levar o alerta aberto pela T-011 até o FCM:
- registro de tokens por usuário, com troca segura de dono do aparelho entre operadoras;
- preferências por veículo e tipo e uma `alert_delivery` idempotente por usuário e episódio;
- envio pela API HTTP v1 com prioridade alta, colapso, retentativa e tratamento de token inválido.

Nada sai para fato reprocessado, antigo ou em ambiente de restore (INV-05). Fecha a medição de latência t4 − t0 que alimenta o G0-5 e o "minuto ruim". O recebimento no app e as telas A05, A06 e A09 são da T-032.

## Contexto obrigatório

- [07 §2](../docs/spec/07-alertas-e-tempo-real.md#2-catálogo) (textos e canais), §3 item 6 (janela), §6 (encerramento), §7 (FCM), §8 (preferências), §10 (latência), §12.
- [04 §3.4](../docs/spec/04-dominio-e-dados.md#34-identidade) (`push_token`), §3.6 (`alert_delivery`, `alert_preference`), §4.2 (tipos A, B, E, G), §4.4 (`claim_push_token`).
- [02 §2.5](../docs/spec/02-escopo-e-fases.md#25-gate-g0-31102026) G0-5 (p95 ≤ 60 s, amostra ≥ 20 entregas).
- [T-011](T-011-motor-de-alertas-f0.md): `alert.opened.v1`/`alert.closed.v1`, `notifyClose`, `stale`, `evidence.timings`, `QUEUES`, rota da outbox, rotas de vigilância e `GET /api/v1/alerts`; [T-005](T-005-ingestao-traccar-inbox-projecao.md): publicador da outbox e `OUTBOX_ROUTES`.

## Escopo — fazer

1. Migration `20261022120000_push.sql` com o SQL exato da seção (1) e, em `packages/db/catalog-allowlist.json`, as entradas da seção (1.1): `push_token` em `withoutOperatorId` (CAT-03) e `app.claim_push_token(uuid, text, text)` em `securityDefiner` (CAT-07; `EXECUTE` só para `tracksys_app`).
2. Rotas `/api/v1/me/push-tokens` e `/api/v1/me/alert-preferences` (2), as leituras do app `GET /api/v1/alerts/{alertId}` e `GET /api/v1/vehicles/{vehicleId}/watch-mode` (2), com schemas em `packages/contracts` e clientes TS/Dart regenerados.
3. Fila `alerts.deliver` criada na migration com `pgboss.create_queue` e listada em `QUEUES`, rotas do publicador da outbox `alert.opened.v1` e `alert.closed.v1 → alerts.deliver` e consumidor (3).
4. Adaptador FCM HTTP v1 com OAuth de conta de serviço (4) e fake de FCM em `packages/testkit/src/fakes/fcm.ts` (a T-013 o reutiliza).
5. Métricas `alert_latency_seconds`, `alert_stage_seconds{stage}`, `alert_deliveries_total{status}` na interface `Metrics` da T-011.
6. Job diário 03:47 UTC que apaga tokens sem uso há 60 dias.
7. Testes de aceite em `tests/acceptance/T-012/`.

## Fora do escopo

- Tudo que roda no celular: permissão, canais, sincronização de token, banner, toque que abre o alerta, telas A05, A06 e A09 e `--dart-define=FIREBASE_*` no build de release: [T-032](T-032-app-push-alertas-vigilancia-notificacoes.md).
- Push para a equipe da operadora (F0–F1 usa a fila do console) e restrição de `tenant_member` por veículo (modelo de acesso da [08](../docs/spec/08-identidade-e-seguranca.md), F1).
- Reconhecer alerta pelo app (cliente não tem `alert.ack`, [08 §3](../docs/spec/08-identidade-e-seguranca.md#3-papéis-e-permissões)) e mudar o raio da vigilância (o app sempre envia `{}`, raio 150 m).
- `overspeed.params` e demais tipos do F1. SMS, WhatsApp ou e-mail como canal de alerta.
- Consultas do G0-5 (T-015) e expurgo de tokens de usuários sem membership ativa (`app.retention_purge`, T-027 no F1).

## Arquivos a criar/alterar

```
packages/db/migrations/20261022120000_push.sql
packages/db/catalog-allowlist.json, packages/db/src/queues.ts
packages/contracts/src/http/{push-tokens,alert-preferences}.ts (+ OpenAPI e clientes gerados)
packages/contracts/src/http/{alerts,watch-mode}.ts (alterar: AlertDetail e WatchModeStatus; arquivos da T-011)
apps/api/src/alerts/{push-tokens.controller,alert-preferences.controller,alert-detail.controller,watch-mode-read.controller}.ts
apps/worker/src/alerts/{deliver.consumer,fcm.adapter,fcm.auth,token-cleanup}.ts, apps/worker/src/outbox/routes.ts
packages/testkit/src/fakes/fcm.ts
tests/acceptance/T-012/{schema,routes,delivery,delivery.property}.test.ts   (a P5 da T-011 fica intacta; a extensão é arquivo novo)
```

## Especificação detalhada

### (1) Migration — SQL exato

```sql
-- migrate:up
-- T-012 — Tokens de push, preferências e entregas (04 §3.4, §3.6, §4.2–§4.4; 07 §7–§8). INV-01, INV-05, INV-07.
SET LOCAL lock_timeout = '5s'; SET LOCAL statement_timeout = '60s';
-- rls: E + G
CREATE TABLE app.push_token (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth."user" (id),
  platform text NOT NULL CHECK (platform IN ('android', 'ios')), token text NOT NULL CHECK (length(token) BETWEEN 32 AND 4096),
  last_seen_at timestamptz NOT NULL DEFAULT now(), created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT push_token_token_key UNIQUE (token)
);
CREATE INDEX push_token_user_idx ON app.push_token (user_id);
-- rls: A
CREATE TABLE app.alert_preference (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL, tenant_id uuid NOT NULL, user_id uuid NOT NULL REFERENCES auth."user" (id), vehicle_id uuid NOT NULL,
  type text NOT NULL CHECK (type ~ '^[a-z_]{3,40}$'), enabled boolean NOT NULL, params jsonb NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT alert_preference_user_vehicle_type_key UNIQUE (user_id, vehicle_id, type),
  CONSTRAINT alert_preference_vehicle_fk FOREIGN KEY (operator_id, tenant_id, vehicle_id) REFERENCES app.vehicle (operator_id, tenant_id, id)
);
CREATE TRIGGER alert_preference_immutable BEFORE UPDATE ON app.alert_preference FOR EACH ROW EXECUTE FUNCTION
  app.tg_immutable_columns('operator_id', 'tenant_id', 'user_id', 'vehicle_id', 'type');
-- rls: B
CREATE TABLE app.alert_delivery (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL, tenant_id uuid NOT NULL, alert_id uuid NOT NULL,
  channel text NOT NULL DEFAULT 'push' CHECK (channel IN ('push')), user_id uuid NOT NULL REFERENCES auth."user" (id),
  delivery_key text NOT NULL CHECK (length(delivery_key) <= 200),
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'expired', 'suppressed', 'no_token')),
  attempts smallint NOT NULL DEFAULT 0, sent_at timestamptz NULL, error text NULL CHECK (length(error) <= 2000),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT alert_delivery_key UNIQUE (delivery_key),
  CONSTRAINT alert_delivery_alert_fk FOREIGN KEY (operator_id, tenant_id, alert_id) REFERENCES app.alert (operator_id, tenant_id, id)
);
CREATE INDEX alert_delivery_alert_idx ON app.alert_delivery (alert_id);
ALTER TABLE app.push_token ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
ALTER TABLE app.alert_preference ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
ALTER TABLE app.alert_delivery ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
CREATE POLICY push_token_member ON app.push_token FOR ALL
  USING (EXISTS (SELECT 1 FROM app.membership m WHERE m.user_id = push_token.user_id AND m.status = 'active'
    AND m.operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR m.tenant_id = ANY (app.current_tenant_ids()))))
  WITH CHECK (EXISTS (SELECT 1 FROM app.membership m WHERE m.user_id = push_token.user_id AND m.status = 'active'
    AND m.operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR m.tenant_id = ANY (app.current_tenant_ids()))));
CREATE POLICY push_token_owner_all ON app.push_token FOR ALL TO tracksys_owner USING (true) WITH CHECK (true);
CREATE POLICY alert_preference_isolation ON app.alert_preference FOR ALL
  USING (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())))
  WITH CHECK (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())));
CREATE POLICY alert_delivery_staff_all ON app.alert_delivery FOR ALL
  USING (operator_id = app.current_operator_id() AND app.current_scope() = 'operator')
  WITH CHECK (operator_id = app.current_operator_id() AND app.current_scope() = 'operator');
CREATE POLICY alert_delivery_tenant_read ON app.alert_delivery FOR SELECT
  USING (operator_id = app.current_operator_id() AND app.current_scope() = 'tenant' AND tenant_id = ANY (app.current_tenant_ids()));
GRANT SELECT, INSERT, UPDATE, DELETE ON app.push_token TO tracksys_app;
GRANT SELECT, INSERT, UPDATE ON app.alert_preference, app.alert_delivery TO tracksys_app;

CREATE FUNCTION app.claim_push_token(p_user_id uuid, p_platform text, p_token text) RETURNS uuid
  LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
AS $$
DECLARE v_id uuid;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM app.membership m WHERE m.user_id = p_user_id AND m.status = 'active'
      AND m.operator_id = app.current_operator_id()
      AND (app.current_scope() = 'operator' OR m.tenant_id = ANY (app.current_tenant_ids()))) THEN
    RAISE EXCEPTION 'usuário fora do escopo do contexto' USING ERRCODE = '42501';
  END IF;
  DELETE FROM app.push_token t WHERE t.token = p_token AND t.user_id <> p_user_id;
  INSERT INTO app.push_token (user_id, platform, token) VALUES (p_user_id, p_platform, p_token)
    ON CONFLICT (token) DO UPDATE SET last_seen_at = now(), platform = EXCLUDED.platform
    RETURNING id INTO v_id;
  RETURN v_id;
END $$;
REVOKE ALL ON FUNCTION app.claim_push_token(uuid, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.claim_push_token(uuid, text, text) TO tracksys_app;
SELECT pgboss.create_queue('alerts.deliver', '{"policy":"standard","retryLimit":3,"retryDelay":30,"retryBackoff":true,"expireInSeconds":180}'::json);

-- migrate:down
SELECT pgboss.delete_queue('alerts.deliver');
DROP FUNCTION app.claim_push_token(uuid, text, text);
DROP TABLE app.alert_delivery, app.alert_preference, app.push_token;
```

### (1.1) Catálogo e allowlist

- **CAT-03:** `app.push_token` não tem `operator_id` (o token é do usuário e do aparelho, que podem ter memberships em várias operadoras; tipo E de [04 §4.2](../docs/spec/04-dominio-e-dados.md#42-tipos-de-tabela-e-políticas)). Entrada no mesmo PR, em `packages/db/catalog-allowlist.json`, no formato da T-005 (nome da tabela sem schema): `"withoutOperatorId": { …, "push_token": "token FCM do usuário; escopo pela membership ativa na política push_token_member (tipo E)" }`. `alert_preference` e `alert_delivery` têm `operator_id` e `tenant_id` NOT NULL e não entram na allowlist.
- **CAT-04:** `alert_preference_vehicle_fk` e `alert_delivery_alert_fk` ligam `operator_id → operator_id` e `tenant_id → tenant_id` na mesma posição; as FKs para `auth."user"` ficam fora do schema `app` e da regra.
- **CAT-07:** entrada `"securityDefiner": { …, "app.claim_push_token(uuid, text, text)": "mesmo aparelho usado por usuários de operadoras diferentes: tira o token do usuário anterior" }`, no formato da chave criada pela T-004 (assinatura de `oidvectortypes` → justificativa; o schema `z.strictObject` recusa chave desconhecida). Justificativas com ≥ 10 caracteres. `EXECUTE` só para `tracksys_app`, nunca PUBLIC.
- A fila `alerts.deliver` nasce aqui, aplicada pelo dono (`DATABASE_URL`), como a `alerts.evaluate` da T-011; o plano B `db:boss` da T-011 só vale se `pgboss.create_queue` não existir na versão fixada.

A função lê `app.membership` como dono e usa a política `membership_definer_read` (tipo G), criada pela T-004. Esta migration não cria política compartilhada.

### (2) Rotas (sessão e contexto por requisição da T-006; erros Problem Details com `code`)

| Rota | Comportamento |
|---|---|
| `PUT /api/v1/me/push-tokens` body `{"token": 32–4096 caracteres, "platform": "android" \| "ios"}` | `SELECT app.claim_push_token($me, $platform, $token)` no contexto da sessão; o token passa a pertencer ao usuário atual e renova `last_seen_at`. 204 |
| `DELETE /api/v1/me/push-tokens` body `{"token": "…"}` | `DELETE … WHERE token = $1 AND user_id = $me`; 204 mesmo sem linha (idempotente) |
| `GET /api/v1/me/alert-preferences?vehicleId=<uuid>` | Só `tenant_owner`/`tenant_member` (equipe da operadora → 403 `FORBIDDEN`); veículo fora do escopo → 404. 200 `{"items":[{"type","enabled","locked","available","params"}]}` com os 6 tipos do F0 na ordem do catálogo; sem linha = padrão do catálogo; `available` = `availableAlertTypes` do perfil do dispositivo primário (T-011) |
| `PUT /api/v1/me/alert-preferences` body `{"vehicleId","type","enabled","params"?}` | Upsert por `(user_id, vehicle_id, type)`. `sos` ou `watch_mode_breach` com `enabled = false` → 422 `ALERT_PREFERENCE_LOCKED`; tipo fora do catálogo do F0 → 422 `ALERT_TYPE_UNKNOWN`; tipo indisponível com `enabled = true` → 422 `ALERT_TYPE_UNAVAILABLE`; fora do escopo → 404. 200 com o item |
| `GET /api/v1/alerts/{alertId}` (`alerts.get`, permissão `alert.read`) | Detalhe para a A05, sob `withContext(…, { readOnly: true })`: o item de `GET /api/v1/alerts` (T-011) + `title` e `body` (`renderAlertText` da abertura, os mesmos do push), `vehicleId` e `lastLocation` (`evidence.lastLocation` em graus, `{latitude, longitude}`, ou `null`; INV-03). Fora do escopo ou inexistente → 404 `NOT_FOUND` idêntico (REQ-API-008). Rota aditiva a [09 §6](../docs/spec/09-api-e-contratos.md#6-rotas-do-f0), registrada no PR e no `scope-fixtures.ts` |
| `GET /api/v1/vehicles/{vehicleId}/watch-mode` (`watch-mode.get`, permissão `vehicle.read`) | Estado da vigilância para a A06: 200 `{"active": true, "watchModeId", "anchor": {latitude, longitude}, "radiusM", "activatedAt"}` ou `{"active": false}`. Fora do escopo → 404. Rota aditiva a [09 §6](../docs/spec/09-api-e-contratos.md#6-rotas-do-f0), registrada no PR e no `scope-fixtures.ts` |

### (3) Consumidor `alerts.deliver`

Job `{ outboxId, type, operatorId, tenantId, entityId = alertId }`, contexto `operator`, payload validado com `AlertOpenedV1`/`AlertClosedV1`. Fila com `expireInSeconds: 180`.

1. **Sem efeito (INV-05):** `processingMode ≠ 'live'` ou `stale = true` → nenhuma `alert_delivery`, só log `info`.
2. **Destinatários (abertura):** memberships `active` com `role = 'tenant_owner'` no `tenant_id` do alerta e preferência efetiva ligada para `(vehicle_id, type)`. Preferência desligada → sem linha (o alerta segue na fila da central). **Encerramento:** só se `notifyClose = true`, e só para quem tem a entrega `…:push:open` em `sent`.
3. **Chave:** `INSERT … (delivery_key = '<alertId>:<userId>:push:<open|close>', status = 'pending') ON CONFLICT (delivery_key) DO NOTHING RETURNING id`. Só quem inseriu envia; linha `pending` criada há mais de 2 min (job anterior morreu) é retomada; as demais são ignoradas. Duplicata residual no aparelho é absorvida pelo `collapseId`.
4. `ALERT_DELIVERY_ENABLED=false` → `suppressed`, sem chamada ao FCM. Sem token com `last_seen_at` nos últimos 60 dias → `no_token`. Até 5 tokens do usuário, os de `last_seen_at` mais recente.
5. **Rodadas:** até 5; cada rodada envia a todos os tokens ainda pendentes; esperas de 2, 4, 8 e 16 s × U[0,8; 1,2] (ou `Retry-After`, se maior), com `sleep` e `random` injetáveis. Respostas: tabela de [07 §7](../docs/spec/07-alertas-e-tempo-real.md#7-entrega-push-fcm) (404 `UNREGISTERED`/403 `SENDER_ID_MISMATCH` apagam o token; 400 → `failed` sem retentativa; 401 → `failed` e page ao fundador; 429/500/503/timeout de 10 s/rede → nova rodada). `sent` e `sent_at` no primeiro 200; `attempts` = rodadas feitas; esgotadas sem 200 → `failed` com `error`.
6. **Janela:** abertura vence em 3.600 s (`critical`) ou 600 s (demais) contados de `evidence.timings.originAt`; encerramento, 600 s de `endedAt`. Vencida antes do envio ou entre rodadas → `expired`, sem novas chamadas.
7. **Métricas** no primeiro `sent` de cada entrega de abertura: `alert_latency_seconds{type,severity}` = `sent_at − originAt`; `alert_stage_seconds{stage}` para `ingest`, `project`, `evaluate`, `deliver` a partir de `evidence.timings`; `alert_deliveries_total{status}` em todo status final.

### (4) Adaptador FCM

- `fcm.auth.ts`: `FCM_SERVICE_ACCOUNT_JSON` (base64) validado por Zod no boot do worker (`client_email`, `private_key`, `token_uri`, `project_id`); JWT RS256 com `node:crypto` (`iss`, `scope = https://www.googleapis.com/auth/firebase.messaging`, `aud = token_uri`, `iat`, `exp = iat + 3600`), troca por `access_token` no `token_uri` e cache até 5 min antes de expirar.
- `fcm.adapter.ts`: `POST {FCM_API_BASE}/v1/projects/{FCM_PROJECT_ID}/messages:send` com o corpo exato de [07 §7](../docs/spec/07-alertas-e-tempo-real.md#7-entrega-push-fcm): `notification` com `renderAlertText` (T-011; `{veículo}` = apelido, senão placa); `data` só com strings (`alertId`, `vehicleId`, `type`, `severity`, `startedAt`, `link = tracksys://alerts/<alertId>`); `collapseId` = 32 primeiros hex de SHA-256 da `episode_key` em `android.notification.tag` e `apns-collapse-id`; TTL 3.600/1.800/600 s por severidade (`android.ttl` e `apns-expiration`); `critical`/`warning` → `priority HIGH`, `channel_id alerts_high`, `apns-priority 10`, `interruption-level time-sensitive`; `info` → `NORMAL`, `alerts_info`, `5`, `active`; `thread-id = vehicleId`.
- Env: `FCM_PROJECT_ID`, `FCM_SERVICE_ACCOUNT_JSON`, `FCM_API_BASE` (padrão `https://fcm.googleapis.com`), `ALERT_DELIVERY_ENABLED` (padrão `true`). Log nunca contém token FCM, chave ou JWT: só `push_token.id`.
- `packages/testkit/src/fakes/fcm.ts`: servidor HTTP com endpoint OAuth e `messages:send`; grava cada mensagem (corpo e cabeçalhos) e responde por roteiro por token (ex.: `[503, 503, 200]`, `404 UNREGISTERED`), com relógio controlável para `sent_at`.

## Testes de aceite (congelados)

Base: `seedVerticalSlice` (T-005), usuários e sessões de teste da T-006 (`dono.a1`, `dono.a2`, `agente.alfa`, `admin.beta`), V1 com apelido "Gol prata", alertas produzidos pela T-011 em processo, `handleDeliverJob` chamado com fake de FCM, `sleep`/`random`/relógio injetados e `Metrics` em memória. Datas dos CTs deslocadas para o dia UTC corrente, mantendo a hora.

`schema.test.ts`
- Catálogo sem violação (CAT-01..CAT-07, com a CAT-03 e a CAT-04 da T-001 endurecida); `withoutOperatorId` contém `push_token` e nenhuma outra tabela desta migration; `securityDefiner` contém `app.claim_push_token(uuid, text, text)`; `has_function_privilege` → `tracksys_app` com EXECUTE e PUBLIC sem EXECUTE. Numa transação desfeita, sem a entrada `push_token` na allowlist do teste, `runCatalogChecks` acusa `CAT-03 app.push_token`. `SELECT name FROM pgboss.queue` contém `alerts.deliver` e casa com `QUEUES`.
- ISO-01 a ISO-05 para `alert_preference` e `alert_delivery`; contexto `tenant` não escreve em `alert_delivery` (42501); `tracksys_app` com `DELETE` em `alert_delivery` → 42501.
- `push_token` (tipo E): token de usuário da Beta invisível no contexto da Alfa; `claim_push_token` para usuário sem membership no contexto → 42501; o mesmo token reivindicado por `admin.beta` no contexto da Beta some de `dono.a1` (1 linha no total).

`routes.test.ts`
- Tokens: `PUT` com o mesmo token 2 vezes → 1 linha e `last_seen_at` renovado; `DELETE` → 204 e 0 linhas; 2º `DELETE` → 204; token de 31 caracteres → erro de validação.
- CT-ALR-013: `dono.a1` sem linhas → `ignition_on` com `enabled = false` e `sos` com `enabled = true, locked = true`; `PUT` `ignition_on` ligado → 200; `dono.a2` com `vehicleId = V1` → 404.
- CT-ALR-006 (parte): `PUT` `sos` com `enabled = false` → 422 `ALERT_PREFERENCE_LOCKED`.
- CT-ALR-001 (parte): perfil com `sos = 'unknown'` → `sos` com `available = false`; `agente.alfa` → 403 `FORBIDDEN`.
- Leituras do app: alerta `sos` aberto de V1 → `dono.a1` em `GET /api/v1/alerts/{id}` → 200 com `title = "Pânico acionado"`, `vehicleId = V1` e `lastLocation` em graus; `dono.a2`, `admin.beta` e UUID aleatório → 404 com `type`, `title` e `detail` iguais. `GET /api/v1/vehicles/{V1}/watch-mode` de `dono.a1` → `{"active": false}`; depois do `POST` da T-011 → `active = true`, `radiusM = 150` e o mesmo `activatedAt` do `POST`; `dono.a2` → 404.

`delivery.test.ts`
- CT-ALR-011: alerta `sos` para `dono.a1` com 1 token Android e 1 iOS → fake recebe 2 mensagens com `android.priority = "HIGH"`, `channel_id = "alerts_high"`, `apns-priority = "10"`, `interruption-level = "time-sensitive"` e `apns-collapse-id` = 32 primeiros hex de SHA-256 da `episode_key`; 1 `alert_delivery` `sent` com `delivery_key = "<alertId>:<userId>:push:open"`; nada para `dono.a2`.
- CT-ALR-012: roteiro 503, 503, 200 → `sent`, `attempts = 3`, esperas em [1,6; 2,4] s e [3,2; 4,8] s; 404 `UNREGISTERED` em T1 e 200 em T2 → T1 sai de `push_token` e a entrega fica `sent`; 503 contínuo em `warning` → 5 rodadas, `failed` e nenhuma chamada depois.
- CT-ALR-002 (entrega): preferência ligada e `serverTime = <hoje>T00:14:03Z` → fake recebe "Ignição ligada" — "Gol prata: ignição ligada às 21:14."; sem linha de preferência → 0 `alert_delivery` e 0 chamadas.
- CT-ALR-005 (entrega): abertura → 1 push; sinal repetido → 0 push; fechamento às 03:20:00Z → 1 push `info` "Gol prata: energia do veículo restabelecida às 00:20." com o mesmo `collapseId`.
- CT-ALR-006 (entrega): posição e evento `alarm` do mesmo acionamento → 1 push por token de `dono.a1`.
- CT-ALR-007 (entrega): fechamento de `offline` com contato às 10:41:00Z → "Gol prata voltou a comunicar às 07:41." só para quem recebeu a abertura.
- CT-ALR-009 (entrega): o mesmo job de `alerts.deliver` 3 vezes, 2 em paralelo → 1 `alert_delivery` por usuário e 1 mensagem por token.
- CT-ARQ-009 3ª parte: o mesmo `alert.opened.v1` entregue 2 vezes ao consumidor de push → 1 `alert_delivery`.
- CT-ALR-010 (entrega): `processingMode = "reprocess"` → 0 `alert_delivery` e 0 chamadas; `stale = true` → idem; `ALERT_DELIVERY_ENABLED=false` → entregas `suppressed` e 0 chamadas.
- Janela: alerta `critical` com `originAt` 61 min antes do job → `expired` e 0 chamadas.
- CT-ALR-015 (t4): `serverTime = 15:20:00.000Z` e fake aceitando às 15:20:07.400Z → `alert_latency_seconds` registra 7,4 e as 4 etapas somam 7,4 s (± 0,001).
- Limpeza: token com `last_seen_at` há 61 dias some; há 59 dias fica.

`delivery.property.test.ts` (P5 de [14 §9.1](../docs/spec/14-qualidade-e-processo-ia.md#91-propriedades), extensão da `replay.property.test.ts` da T-011; fast-check `numRuns: 25` com Postgres, seed impressa na falha): o mesmo gerador de 1 a 50 mensagens com `processingMode` em `replay`, `backfill` ou `reprocess`, intercaladas com mensagens `live` já processadas, agora com preferências ligadas e tokens de `dono.a1`, passando por `runRelayOnce`, `handleEvaluateJob` e `handleDeliverJob` → o fake de FCM recebe 0 chamadas novas e `alert_delivery` não ganha linha (**CT-QLD-009**: remover a condição `processingMode === 'live'` antes de criar `alert_delivery` faz a propriedade falhar com contraexemplo de 1 mensagem `replay` e 1 chamada ao fake de FCM).

## Comandos de verificação

```bash
pnpm install
pnpm db:reset && pnpm db:migrate                 # a fila alerts.deliver nasce na migration (plano B da T-011: + pnpm db:boss)
pnpm db:check                                   # Catálogo OK: nenhuma violação de CAT-01..CAT-07.
pnpm test:acceptance -- tests/acceptance/T-012
pnpm verify                                     # T-001, T-002, T-005, T-011 e T-012 verdes
pnpm db:rollback && pnpm db:migrate                  # prova o down desta migration (o pnpm verify também prova)
```

## Definição de pronto

- [ ] Comandos verdes local e no CI; testes congelados anteriores intactos; `T-012/**` congelado no 1º commit do PR (escrito por agente de outro fornecedor).
- [ ] Com `ALERT_DELIVERY_ENABLED=true` e o fake de FCM, um `sos` provocado em V1 produz 1 `alert_delivery` `sent` por token de `dono.a1` e `alert_latency_seconds` registrado (o ensaio com aparelho real é da T-032).
- [ ] Entradas `push_token` (CAT-03) e `app.claim_push_token` (CAT-07) na allowlist; `has_function_privilege` confere.
- [ ] PR `feat(alerts): push FCM no servidor, tokens e entregas (T-012)` com `Risco declarado: N0`, REQ, INV, revisão cruzada de outro fornecedor nos arquivos N0 e as decisões 1, 2, 4 e 8 citadas.

## Decisões já tomadas

| Dúvida provável | Resposta |
|---|---|
| 1. `firebase-admin` ou `google-auth-library`? | Nenhum: OAuth da conta de serviço com JWT RS256 em `node:crypto` e `fetch` para a API HTTP v1. Controle total de erros, cabeçalhos e retentativa; zero dependência nova no worker. |
| 2. Quem recebe push no F0? | Só `tenant_owner` do cliente do veículo. `tenant_member` espera o modelo de acesso por veículo ([08](../docs/spec/08-identidade-e-seguranca.md), F1): mais seguro não vazar alerta de veículo sem acesso. Escolha reversível, registrada no PR. |
| 3. Preferência desligada gera `alert_delivery`? | Não. A linha só existe para quem deve receber; o episódio continua registrado e na fila da central. |
| 4. Fato reprocessado, `stale` ou modo `backfill`/`replay` | Nenhuma `alert_delivery` ([07 §3](../docs/spec/07-alertas-e-tempo-real.md#3-avaliação) item 6; INV-05). `expired` é só para entrega `pending` cuja janela venceu. |
| 5. Retentativa no pg-boss ou dentro do job? | Dentro do job, com `sleep` injetável (esperas de [07 §7](../docs/spec/07-alertas-e-tempo-real.md#7-entrega-push-fcm) são curtas e com jitter próprio). O retry do pg-boss só cobre a queda do worker, retomando `pending` com mais de 2 min. |
| 6. `apns-priority` e prioridade Android do aviso `info` | `5` e `NORMAL` (o capítulo só fixa `critical`/`warning`); canal `alerts_info`, `interruption-level: active`. |
| 7. Onde ficam as chaves do Firebase? | Só no servidor: `FCM_SERVICE_ACCOUNT_JSON` e `FCM_PROJECT_ID` no `prod.env.sops` e nos segredos do CI. O app recebe os valores públicos por `--dart-define` (T-032). |
| 8. Equipe da operadora pode ler/editar preferências? | Não: 403. No F0 ela não recebe push; preferência é do usuário do cliente. |
| 9. Tokens de quem perdeu toda membership | Ficam até existir `app.retention_purge` (T-027, F1); a entrega já os ignora, porque só lê destinatários com membership ativa. |
| 10. Rota de detalhe do alerta e de estado da vigilância não estão em 09? | São leituras aditivas (`alerts.get` e `watch-mode.get`), com o mesmo isolamento das demais (404 idêntico, `scope-fixtures.ts`); registrar no PR para a 09 §6 incorporar. Nenhuma escrita nova. |
| 11. Quem cria o fake de FCM? | Esta tarefa, em `packages/testkit/src/fakes/fcm.ts`. A T-013 o usa no teste de `EXTERNAL_EFFECTS` e, se esta tarefa ainda não estiver em `main`, cria uma versão local mínima com o mesmo caminho. |
| 12. As telas e o ensaio com aparelho entram aqui? | Não. A [T-032](T-032-app-push-alertas-vigilancia-notificacoes.md) entrega o app (A05, A06, A09, canais, token) e registra o ensaio ponta a ponta de 27/10 em `docs/runbooks/gates/G0.md`. |
