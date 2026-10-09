# T-012 — Push FCM: tokens, `alert_delivery`, recebimento no app

| Campo | Valor |
|---|---|
| Fase | F0 (semana S3: 21–27/10/2026; marco 27/10: alerta provocado chega ao celular) |
| Requisitos | REQ-ALR-011, REQ-ALR-012, REQ-ALR-013; parte de entrega de REQ-ALR-002, REQ-ALR-005, REQ-ALR-006, REQ-ALR-007, REQ-ALR-009 e REQ-ALR-010; REQ-ALR-001 (disponibilidade nas preferências); REQ-ALR-015 (t4 e métricas de latência); REQ-DAD-006 (`app.claim_push_token`); REQ-UX-009 (tela A05 Alertas e toque no push), REQ-UX-010 (tela A06 Modo vigilância; sai junto com o corte 3 de [02 §2.4](../docs/spec/02-escopo-e-fases.md)), REQ-UX-012 (tela A09 Notificações) [ADOTADO NA v2.0]; REQ-ARQ-009 (3ª parte do CT-ARQ-009; outbox e relay são da T-005) |
| Invariantes | INV-01, INV-03, INV-05, INV-07, INV-08 (A06 nunca dispara comando físico) |
| Risco de revisão | **N1** (tabela 2.3 de [02](../docs/spec/02-escopo-e-fases.md)). **Trechos N0:** a migration e `app.claim_push_token` (`SECURITY DEFINER`, CAT-07) exigem revisão adversarial de outro fornecedor e leitura humana linha a linha |
| Depende de | T-011 (alertas, rota `device.state.updated.v1` da outbox, filas, `renderAlertText`, `Metrics`, rotas de vigilância e de alertas), T-009 (app Flutter com login, mapa ao vivo e A03; traz a T-006), T-008 (evento SSE `alert`, `availableActions.watchMode`), T-010 (ações A07 e A08 reutilizadas na A05; até ela entrar, o detalhe mostra só "Ver no mapa" e registra no PR); T-005 (relay da outbox, `OUTBOX_ROUTES`); helper de sessão de teste `signInAs(world, user, { clientKind })` de `packages/testkit` (T-006) |
| Estimativa | 4 sessões de agente (1: migration, função e rotas; 2: consumidor `alerts.deliver`, FCM e métricas; 3: push no app Flutter e ensaio ponta a ponta; 4: telas A05, A06 e A09) |
| Bloqueado por decisão | DEC-03 (conta Apple: sem ela, iOS sai do G0 pelo corte 6 de [02 §2.4](../docs/spec/02-escopo-e-fases.md)); projeto Firebase com chave APNs (ação do fundador no S2) |

## Objetivo

Levar o alerta aberto pela T-011 até a tela bloqueada do cliente final: registro de tokens FCM por usuário (com troca segura de dono do aparelho entre operadoras), preferências por veículo e tipo, uma `alert_delivery` idempotente por usuário e episódio, envio pela API HTTP v1 do FCM com prioridade alta, colapso, retentativa e tratamento de token inválido, e recebimento no app Flutter com canais do Android e Time Sensitive no iOS. Nada sai para fato reprocessado, antigo ou em ambiente de restore (INV-05). Fecha a medição de latência t4 − t0 que alimenta o G0-5 e o "minuto ruim".

## Contexto obrigatório

- [07](../docs/spec/07-alertas-e-tempo-real.md) §2 (textos e canais), §3 item 6 (janela), §6 (encerramento), §7 (FCM), §8 (preferências), §10 (latência), §12.
- [04](../docs/spec/04-dominio-e-dados.md) §3.4 (`push_token`), §3.6 (`alert_delivery`, `alert_preference`), §4.2 (tipos A, B, E, G), §4.4 (`claim_push_token`).
- [02 §2.5](../docs/spec/02-escopo-e-fases.md) G0-5 (p95 ≤ 60 s, amostra ≥ 20 entregas).
- [T-011](T-011-motor-de-alertas-f0.md): `alert.opened.v1`/`alert.closed.v1`, `notifyClose`, `stale`, `evidence.timings`, `QUEUES`, rota da outbox, rotas de vigilância e `GET /api/v1/alerts`; [T-005](T-005-ingestao-traccar-inbox-projecao.md): relay e `OUTBOX_ROUTES`.
- [10 §6](../docs/spec/10-apps-e-ux.md): telas A05, A06 e A09, rotas internas do app (`/alertas`, `/alertas/:id`) e REQ-UX-009, REQ-UX-010 e REQ-UX-012; [02 §2.4](../docs/spec/02-escopo-e-fases.md) (corte 3).

## Escopo — fazer

1. Migration `20261022120000_push.sql` com o SQL exato da seção (1) e, em `packages/db/catalog-allowlist.json`, as entradas da seção (1.1): `push_token` em `withoutOperatorId` (CAT-03) e `app.claim_push_token(uuid, text, text)` em `securityDefiner` (CAT-07; `EXECUTE` só para `tracksys_app`).
2. Rotas `/api/v1/me/push-tokens` e `/api/v1/me/alert-preferences` (2), as leituras do app `GET /api/v1/alerts/{alertId}` e `GET /api/v1/vehicles/{vehicleId}/watch-mode` (2), com schemas em `packages/contracts` e clientes TS/Dart regenerados.
3. Fila `alerts.deliver` criada na migration com `pgboss.create_queue` e listada em `QUEUES`, rotas do relay `alert.opened.v1` e `alert.closed.v1 → alerts.deliver` e consumidor (3).
4. Adaptador FCM HTTP v1 com OAuth de conta de serviço (4) e fake de FCM em `packages/testkit/src/fakes/fcm.ts`.
5. Métricas `alert_latency_seconds`, `alert_stage_seconds{stage}`, `alert_deliveries_total{status}` na interface `Metrics` da T-011.
6. Job diário 03:47 UTC que apaga tokens sem uso há 60 dias.
7. App Flutter (5): permissão com explicação antes do pedido, canais, sincronização de token, banner em primeiro plano, toque abre o detalhe do alerta (A05); telas A05 Alertas, A06 Modo vigilância (interruptor no A03) e A09 Notificações (preferências), de [10 §6](../docs/spec/10-apps-e-ux.md). Se o fundador aplicar o corte 3 de [02 §2.4](../docs/spec/02-escopo-e-fases.md), a A06 não é entregue e REQ-UX-010 passa para o F1 (registro na seção "Cortes" do `G0.md`); A05 e A09 ficam.
8. `--dart-define=FIREBASE_*` acrescentados ao build de release em `.github/workflows/mobile-release.yml` (criado pela T-010), com os valores em variáveis do ambiente `mobile-release`.
9. Testes de aceite em `tests/acceptance/T-012/`, testes Flutter em `apps/mobile/test/{push,alerts,watch_mode,notifications}/` e ensaio ponta a ponta registrado em `docs/runbooks/gates/G0.md`.

## Fora do escopo

- Push para a equipe da operadora (F0–F1 usa a fila do console) e restrição de `tenant_member` por veículo (modelo de acesso da [08](../docs/spec/08-identidade-e-seguranca.md), F1).
- Histórico de alertas no app além de 30 dias, filtros na A05 e central de notificações: F1. (O detalhe do alerta A05, a vigilância A06 e as preferências A09 entram aqui [ADOTADO NA v2.0].)
- Reconhecer alerta pelo app (cliente não tem `alert.ack`, [08 §3](../docs/spec/08-identidade-e-seguranca.md)) e mudar o raio da vigilância na A06 (o app sempre envia `{}`, raio 150 m).
- `overspeed.params` e demais tipos do F1. SMS, WhatsApp ou e-mail como canal de alerta.
- Consultas do G0-5 (T-015) e expurgo de tokens de usuários sem membership ativa (`app.retention_purge`, T-027 no F1).

## Arquivos a criar/alterar

```
packages/db/migrations/20261022120000_push.sql
packages/db/catalog-allowlist.json, packages/db/src/queues.ts
packages/contracts/src/http/{push-tokens,alert-preferences}.ts (+ OpenAPI e clientes gerados)
packages/contracts/src/http/{alerts,watch-mode}.ts (alterar: AlertDetail e WatchModeStatus; arquivos da T-011)
apps/api/src/alerts/{push-tokens.controller,alert-preferences.controller,alert-detail.controller,watch-mode-read.controller}.ts
.github/workflows/mobile-release.yml (alterar: --dart-define=FIREBASE_*)
apps/worker/src/alerts/{deliver.consumer,fcm.adapter,fcm.auth,token-cleanup}.ts, apps/worker/src/outbox/routes.ts
packages/testkit/src/fakes/fcm.ts
apps/mobile/pubspec.yaml (firebase_core, firebase_messaging)
apps/mobile/lib/push/{push_service,push_token_sync,alert_link,firebase_options}.dart, apps/mobile/lib/main.dart
apps/mobile/android/app/src/main/AndroidManifest.xml, apps/mobile/android/app/src/main/kotlin/**/MainActivity.kt
apps/mobile/ios/Runner/{Runner.entitlements,Info.plist}
apps/mobile/lib/features/{alerts/alerts_screen,alerts/alert_detail_screen,alerts/alerts_repository}.dart
apps/mobile/lib/features/{vehicle/watch_mode_switch,vehicle/watch_mode_repository}.dart
apps/mobile/lib/features/{notifications/notifications_screen,notifications/permission_explainer,notifications/notifications_banner}.dart
apps/mobile/lib/router.dart, apps/mobile/lib/features/home/home_screen.dart, apps/mobile/lib/features/vehicle/vehicle_detail_screen.dart, apps/mobile/lib/features/account/account_screen.dart (alterar: rotas /alertas e /alertas/:id, acesso pelo Início, interruptor no A03, link para A09 na Conta)
apps/mobile/test/push/{alert_link_test,push_token_sync_test}.dart
apps/mobile/test/alerts/alert_detail_test.dart, apps/mobile/test/watch_mode/watch_mode_switch_test.dart, apps/mobile/test/notifications/notifications_test.dart
tests/acceptance/T-012/{schema,routes,delivery}.test.ts
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

- **CAT-03:** `app.push_token` não tem `operator_id` (o token é do usuário e do aparelho, que podem ter memberships em várias operadoras; tipo E de [04 §4.2](../docs/spec/04-dominio-e-dados.md)). Entrada no mesmo PR, em `packages/db/catalog-allowlist.json`, no formato da T-005 (nome da tabela sem schema): `"withoutOperatorId": { …, "push_token": "token FCM do usuário; escopo pela membership ativa na política push_token_member (tipo E)" }`. `alert_preference` e `alert_delivery` têm `operator_id` e `tenant_id` NOT NULL e não entram na allowlist.
- **CAT-04:** `alert_preference_vehicle_fk` e `alert_delivery_alert_fk` ligam `operator_id → operator_id` e `tenant_id → tenant_id` na mesma posição; as FKs para `auth."user"` ficam fora do schema `app` e da regra.
- **CAT-07:** entrada `"securityDefiner": { …, "app.claim_push_token(uuid, text, text)": "mesmo aparelho usado por usuários de operadoras diferentes: tira o token do usuário anterior" }`, no formato da chave criada com a CAT-07 (T-005 ou T-006, a que chegou primeiro: assinatura de `oidvectortypes` → justificativa; o schema `z.strictObject` recusa chave desconhecida). Justificativas com ≥ 10 caracteres. `EXECUTE` só para `tracksys_app`, nunca PUBLIC.
- A fila `alerts.deliver` nasce aqui, aplicada pelo dono (`DATABASE_URL`), como a `alerts.evaluate` da T-011; plano B `db:boss` da T-011 só se `pgboss.create_queue` não existir na versão fixada.

A função lê `app.membership` como dono: exige a política `membership_definer_read` (tipo G) criada pela T-006. Se ela não existir em `main`, crie-a nesta migration (`FOR SELECT TO tracksys_owner USING (true)`) e registre no PR.

### (2) Rotas (sessão e contexto por requisição da T-006; erros Problem Details com `code`)

| Rota | Comportamento |
|---|---|
| `PUT /api/v1/me/push-tokens` body `{"token": 32–4096 caracteres, "platform": "android" \| "ios"}` | `SELECT app.claim_push_token($me, $platform, $token)` no contexto da sessão; o token passa a pertencer ao usuário atual e renova `last_seen_at`. 204 |
| `DELETE /api/v1/me/push-tokens` body `{"token": "…"}` | `DELETE … WHERE token = $1 AND user_id = $me`; 204 mesmo sem linha (idempotente) |
| `GET /api/v1/me/alert-preferences?vehicleId=<uuid>` | Só `tenant_owner`/`tenant_member` (equipe da operadora → 403 `FORBIDDEN`); veículo fora do escopo → 404. 200 `{"items":[{"type","enabled","locked","available","params"}]}` com os 6 tipos do F0 na ordem do catálogo; sem linha = padrão do catálogo; `available` = `availableAlertTypes` do perfil do dispositivo primário (T-011) |
| `PUT /api/v1/me/alert-preferences` body `{"vehicleId","type","enabled","params"?}` | Upsert por `(user_id, vehicle_id, type)`. `sos` ou `watch_mode_breach` com `enabled = false` → 422 `ALERT_PREFERENCE_LOCKED`; tipo fora do catálogo do F0 → 422 `ALERT_TYPE_UNKNOWN`; tipo indisponível com `enabled = true` → 422 `ALERT_TYPE_UNAVAILABLE`; fora do escopo → 404. 200 com o item |
| `GET /api/v1/alerts/{alertId}` (`alerts.get`, permissão `alert.read`) | Detalhe para a A05, sob `withContext(…, { readOnly: true })`: o item de `GET /api/v1/alerts` (T-011) + `title` e `body` (`renderAlertText` da abertura, os mesmos do push), `vehicleId` e `lastLocation` (`evidence.lastLocation` em graus, `{latitude, longitude}`, ou `null`; INV-03). Fora do escopo ou inexistente → 404 `NOT_FOUND` idêntico (REQ-API-008). Rota aditiva a [09 §6](../docs/spec/09-api-e-contratos.md), registrada no PR e no `scope-fixtures.ts` |
| `GET /api/v1/vehicles/{vehicleId}/watch-mode` (`watch-mode.get`, permissão `vehicle.read`) | Estado da vigilância para a A06: 200 `{"active": true, "watchModeId", "anchor": {latitude, longitude}, "radiusM", "activatedAt"}` ou `{"active": false}`. Fora do escopo → 404. Rota aditiva a [09 §6](../docs/spec/09-api-e-contratos.md), registrada no PR e no `scope-fixtures.ts` |

### (3) Consumidor `alerts.deliver`

Job `{ outboxId, type, operatorId, tenantId, entityId = alertId }`, contexto `operator`, payload validado com `AlertOpenedV1`/`AlertClosedV1`. Fila com `expireInSeconds: 180`.

1. **Sem efeito (INV-05):** `processingMode ≠ 'live'` ou `stale = true` → nenhuma `alert_delivery`, só log `info`.
2. **Destinatários (abertura):** memberships `active` com `role = 'tenant_owner'` no `tenant_id` do alerta e preferência efetiva ligada para `(vehicle_id, type)`. Preferência desligada → sem linha (o alerta segue na fila da central). **Encerramento:** só se `notifyClose = true`, e só para quem tem a entrega `…:push:open` em `sent`.
3. **Chave:** `INSERT … (delivery_key = '<alertId>:<userId>:push:<open|close>', status = 'pending') ON CONFLICT (delivery_key) DO NOTHING RETURNING id`. Só quem inseriu envia; linha `pending` criada há mais de 2 min (job anterior morreu) é retomada; as demais são ignoradas. Duplicata residual no aparelho é absorvida pelo `collapseId`.
4. `ALERT_DELIVERY_ENABLED=false` → `suppressed`, sem chamada ao FCM. Sem token com `last_seen_at` nos últimos 60 dias → `no_token`. Até 5 tokens do usuário, os de `last_seen_at` mais recente.
5. **Rodadas:** até 5; cada rodada envia a todos os tokens ainda pendentes; esperas de 2, 4, 8 e 16 s × U[0,8; 1,2] (ou `Retry-After`, se maior), com `sleep` e `random` injetáveis. Respostas: tabela de [07 §7](../docs/spec/07-alertas-e-tempo-real.md) (404 `UNREGISTERED`/403 `SENDER_ID_MISMATCH` apagam o token; 400 → `failed` sem retentativa; 401 → `failed` e page ao fundador; 429/500/503/timeout de 10 s/rede → nova rodada). `sent` e `sent_at` no primeiro 200; `attempts` = rodadas feitas; esgotadas sem 200 → `failed` com `error`.
6. **Janela:** abertura vence em 3.600 s (`critical`) ou 600 s (demais) contados de `evidence.timings.originAt`; encerramento, 600 s de `endedAt`. Vencida antes do envio ou entre rodadas → `expired`, sem novas chamadas.
7. **Métricas** no primeiro `sent` de cada entrega de abertura: `alert_latency_seconds{type,severity}` = `sent_at − originAt`; `alert_stage_seconds{stage}` para `ingest`, `project`, `evaluate`, `deliver` a partir de `evidence.timings`; `alert_deliveries_total{status}` em todo status final.

### (4) Adaptador FCM

- `fcm.auth.ts`: `FCM_SERVICE_ACCOUNT_JSON` (base64) validado por Zod no boot do worker (`client_email`, `private_key`, `token_uri`, `project_id`); JWT RS256 com `node:crypto` (`iss`, `scope = https://www.googleapis.com/auth/firebase.messaging`, `aud = token_uri`, `iat`, `exp = iat + 3600`), troca por `access_token` no `token_uri` e cache até 5 min antes de expirar.
- `fcm.adapter.ts`: `POST {FCM_API_BASE}/v1/projects/{FCM_PROJECT_ID}/messages:send` com o corpo exato de [07 §7](../docs/spec/07-alertas-e-tempo-real.md): `notification` com `renderAlertText` (T-011; `{veículo}` = apelido, senão placa); `data` só com strings (`alertId`, `vehicleId`, `type`, `severity`, `startedAt`, `link = tracksys://alerts/<alertId>`); `collapseId` = 32 primeiros hex de SHA-256 da `episode_key` em `android.notification.tag` e `apns-collapse-id`; TTL 3.600/1.800/600 s por severidade (`android.ttl` e `apns-expiration`); `critical`/`warning` → `priority HIGH`, `channel_id alerts_high`, `apns-priority 10`, `interruption-level time-sensitive`; `info` → `NORMAL`, `alerts_info`, `5`, `active`; `thread-id = vehicleId`.
- Env: `FCM_PROJECT_ID`, `FCM_SERVICE_ACCOUNT_JSON`, `FCM_API_BASE` (padrão `https://fcm.googleapis.com`), `ALERT_DELIVERY_ENABLED` (padrão `true`). Log nunca contém token FCM, chave ou JWT: só `push_token.id`.
- `packages/testkit/src/fakes/fcm.ts`: servidor HTTP com endpoint OAuth e `messages:send`; grava cada mensagem (corpo e cabeçalhos) e responde por roteiro por token (ex.: `[503, 503, 200]`, `404 UNREGISTERED`), com relógio controlável para `sent_at`.

### (5) App Flutter (`apps/mobile`)

- `firebase_core` e `firebase_messaging`; `FirebaseOptions` montado de `--dart-define` (`FIREBASE_API_KEY`, `FIREBASE_PROJECT_ID`, `FIREBASE_MESSAGING_SENDER_ID`, `FIREBASE_APP_ID_ANDROID`, `FIREBASE_APP_ID_IOS`); nenhum `google-services.json` ou `GoogleService-Info.plist` no repositório.
- Android: `POST_NOTIFICATIONS` no manifesto e pedido em tempo de execução (Android 13+); canais criados em `MainActivity.kt`: `alerts_high` ("Alertas", `IMPORTANCE_HIGH`) e `alerts_info` ("Avisos", `IMPORTANCE_DEFAULT`).
- iOS: capacidades Push Notifications e Time Sensitive (`com.apple.developer.usernotifications.time-sensitive`), `UIBackgroundModes = remote-notification`; permissão pedida após o login, com texto PT-BR explicando os alertas de segurança.
- `push_token_sync.dart`: `PUT /api/v1/me/push-tokens` no login, a cada retorno ao primeiro plano e em `onTokenRefresh`; `DELETE` no logout antes de apagar a sessão; falha de rede → nova tentativa em 30 s, sem bloquear a UI.
- Primeiro plano: `onMessage` mostra `MaterialBanner` com título, corpo e ação "Ver" (abre o detalhe). Toque (`onMessageOpenedApp` e `getInitialMessage`): `alert_link.dart` valida `tracksys://alerts/<uuid>` e abre `/alertas/<alertId>` (A05, 1 toque; REQ-UX-009) com o app encerrado, em segundo plano ou aberto; sem sessão, passa pelo login e volta ao alerta (destino guardado pelo `go_router` da T-009); link inválido abre `/inicio`.
- **A05 Alertas** (`/alertas` e `/alertas/:id`; acesso por ícone de alertas no topo do Início): lista de 30 dias com abertos primeiro, montada com `GET /api/v1/alerts?status=open`, `?status=acknowledged` e `?status=closed&from=<agora − 30 d>` (T-011), nessa ordem, seguindo `nextCursor`; atualiza com o evento SSE `alert` recebido pelo cliente SSE da T-009 (deduplicado por `alertId`, precedência `closed` > `acknowledged` > `open`, como no console da T-008). Detalhe por `GET /api/v1/alerts/{alertId}`: título, corpo, hora BRT, veículo, mini-mapa com `lastLocation` (sem marcador se `null`, com "Local do alerta indisponível"), estado atual do veículo (chip e idade da T-009); ações "Ver no mapa" (`/inicio?veiculo=<vehicleId>`: centraliza e abre o card; 2º toque), "Falar com a central" (A07, T-010) e "Navegar até o veículo" (A08, T-010). 404 → "Alerta não encontrado", sem nenhum dado do alerta. Sem botão de reconhecer.
- **A06 Modo vigilância** (interruptor no A03 da T-009): visível com `availableActions.watchMode.available` ou `active`; estado lido de `GET /api/v1/vehicles/{vehicleId}/watch-mode`. Ligar → confirmação "Avisaremos se o veículo sair 150 m deste local ou se a ignição ligar" → `POST /api/v1/vehicles/{vehicleId}/watch-mode` com `{}`; 201/200 → círculo de `radiusM` metros em volta de `anchor` e "Vigilância ativa desde {HH:mm BRT de activatedAt}". 409 `WATCH_MODE_VEHICLE_ON` → "Desligue o veículo para ativar a vigilância"; 409 `WATCH_MODE_NO_FIX` → "Sem posição válida nas últimas 24 h. Não é possível ativar."; outro erro → "Não foi possível ativar. Tente de novo." e o interruptor volta. Desligar → `DELETE` (204). Sem conexão → interruptor desabilitado (nenhuma ação que escreve offline, T-009). Nenhum comando físico (INV-08).
- **A09 Notificações** (pela Conta, A10): explicação PT-BR antes do pedido de permissão (Android 13+ `POST_NOTIFICATIONS`; iOS com Time Sensitive); permissão negada → faixa "Alertas desligados neste celular" + "Ativar" no Início (abre as configurações do sistema); preferências por veículo × tipo de `GET /api/v1/me/alert-preferences`: `locked` → interruptor travado "Sempre ativo"; `available = false` → "Indisponível neste rastreador"; mudança → `PUT`, com 422 revertendo o interruptor. Cartão no 1º acesso: "Quer ser avisado quando a ignição ligar?" (só se `ignition_on` estiver `available`).

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

`apps/mobile/test/push/`: `alert_link_test.dart` (link válido → `/alertas/<alertId>`; esquema, host ou UUID inválidos → `/inicio`); `push_token_sync_test.dart` (com cliente falso: login, retorno ao primeiro plano e renovação chamam `PUT`; logout chama `DELETE` antes de limpar a sessão).

Testes Flutter de tela (cliente falso, relógio fixo, `LiveMapController` falso da T-009):
- `alerts/alert_detail_test.dart` — **CT-UX-009**: `getInitialMessage` com `tracksys://alerts/<id>` de `sos` de V1 → 1º quadro após o login guardado é o detalhe com "Pânico acionado" (1 toque); "Ver no mapa" → `/inicio?veiculo=<V1>` com V1 centralizado (2 toques); API com 404 → "Alerta não encontrado" e nenhum título, corpo ou mapa; sessão expirada → `/entrar` e, depois do login, o detalhe do mesmo alerta. Lista com 1 `closed`, 1 `acknowledged` e 1 `open` → ordem `open`, `acknowledged`, `closed`; evento SSE `alert` com `status = "closed"` move o item para o fim.
- `watch_mode/watch_mode_switch_test.dart` — **CT-UX-010**: V1 estacionado com `available = true`; ativar com `POST` respondendo 201 e `activatedAt = <hoje>T00:14:00Z` → confirmação com o texto exato, círculo de 150 m e "Vigilância ativa desde 21:14"; 409 `WATCH_MODE_VEHICLE_ON` → "Desligue o veículo para ativar a vigilância" e interruptor desligado; 409 `WATCH_MODE_NO_FIX` → texto da A06; sem conexão → interruptor desabilitado e 0 requisições.
- `notifications/notifications_test.dart` — **CT-UX-012**: 1º login no Android 14 (plataforma falsa) → explicação antes da chamada de permissão e os canais `alerts_high` (alta) e `alerts_info` pedidos ao `MainActivity` pelo canal de plataforma; permissão negada → faixa "Alertas desligados neste celular" no Início; `sos` → interruptor travado "Sempre ativo"; perfil sem `power_cut_alarm` (`available = false`) → `power_cut` "Indisponível neste rastreador"; `PUT` com 422 → interruptor volta ao estado anterior.

## Comandos de verificação

```bash
pnpm install
pnpm db:reset && pnpm db:migrate                 # a fila alerts.deliver nasce na migration (plano B da T-011: + pnpm db:boss)
pnpm db:check                                   # Catálogo OK: nenhuma violação de CAT-01..CAT-07.
pnpm test:acceptance -- tests/acceptance/T-012
pnpm verify                                     # T-001, T-002, T-005, T-011 e T-012 verdes
pnpm db:rollback && pnpm db:migrate                  # prova o down desta migration (o pnpm verify também prova)
cd apps/mobile && flutter analyze && flutter test test/push test/alerts test/watch_mode test/notifications
```

## Definição de pronto

- [ ] Comandos verdes local e no CI; testes congelados anteriores intactos; `T-012/**` congelado no PR.
- [ ] Ensaio ponta a ponta (marco 27/10): com o J16 de bancada, 3 `ignition_on` (exige `ignition = 'yes'` no perfil [VALIDAR — DEC-02]; padrão seguro sem ignição confirmada: 3 `watch_mode_breach` por deslocamento) e 1 `offline` provocados chegam a 1 Android (teste fechado) com o app fechado e a tela bloqueada, e a 1 iPhone (TestFlight) se DEC-03 permitir; `sent_at − originAt` de cada entrega ≤ 60 s; o toque na notificação abre o detalhe do alerta e "Ver no mapa" centraliza o veículo; registrado em `docs/runbooks/gates/G0.md`.
- [ ] PR `feat(alerts): push FCM, tokens e entregas (T-012)` com REQ, INV, risco N1 com trechos N0, revisão cruzada de outro fornecedor, as decisões 1, 2, 4, 8, 11 e 12 citadas e, se aplicado, o corte 3.

## Decisões já tomadas (não pergunte, siga)

| Dúvida provável | Resposta |
|---|---|
| 1. `firebase-admin` ou `google-auth-library`? | Nenhum: OAuth da conta de serviço com JWT RS256 em `node:crypto` e `fetch` para a API HTTP v1. Controle total de erros, cabeçalhos e retentativa; zero dependência nova no worker. |
| 2. Quem recebe push no F0? | Só `tenant_owner` do cliente do veículo. `tenant_member` espera o modelo de acesso por veículo ([08](../docs/spec/08-identidade-e-seguranca.md), F1): mais seguro não vazar alerta de veículo sem acesso. Escolha reversível, registrada no PR. |
| 3. Preferência desligada gera `alert_delivery`? | Não. A linha só existe para quem deve receber; o episódio continua registrado e na fila da central. |
| 4. Fato reprocessado, `stale` ou modo `backfill`/`replay` | Nenhuma `alert_delivery` ([07 §3](../docs/spec/07-alertas-e-tempo-real.md) item 6; INV-05). `expired` é só para entrega `pending` cuja janela venceu. |
| 5. Retentativa no pg-boss ou dentro do job? | Dentro do job, com `sleep` injetável (esperas de [07 §7](../docs/spec/07-alertas-e-tempo-real.md) são curtas e com jitter próprio). O retry do pg-boss só cobre a queda do worker, retomando `pending` com mais de 2 min. |
| 6. `apns-priority` e prioridade Android do aviso `info` | `5` e `NORMAL` (o capítulo só fixa `critical`/`warning`); canal `alerts_info`, `interruption-level: active`. |
| 7. Configuração do Firebase no repositório? | Não. `--dart-define` em build local e CI; os valores ficam nos segredos do CI e no gerenciador do fundador. |
| 8. Toque na notificação abre o quê? | O detalhe do alerta `/alertas/:id` (A05), como manda REQ-UX-009; o mapa com o veículo centralizado fica a 1 toque ("Ver no mapa" → `/inicio?veiculo=<vehicleId>`). [ADOTADO NA v2.0: A05 e A06 entram nesta tarefa.] |
| 9. Equipe da operadora pode ler/editar preferências? | Não: 403. No F0 ela não recebe push; preferência é do usuário do cliente. |
| 10. Tokens de quem perdeu toda membership | Ficam até existir `app.retention_purge` (T-027, F1); a entrega já os ignora, porque só lê destinatários com membership ativa. |
| 11. A06 entra se o prazo apertar? | A06 sai junto com o corte 3 de [02 §2.4](../docs/spec/02-escopo-e-fases.md) (modo vigilância): o fundador registra o corte na seção "Cortes" do `G0.md`, REQ-UX-010 passa para o F1 e o restante desta tarefa segue. A05 e A09 não têm corte (REQ-UX-009 e REQ-UX-012 são P0). |
| 12. Rota de detalhe do alerta e de estado da vigilância não estão em 09? | São leituras aditivas (`alerts.get` e `watch-mode.get`), com o mesmo isolamento das demais (404 idêntico, `scope-fixtures.ts`); registrar no PR para a 09 §6 incorporar. Nenhuma escrita nova. |
