# 09 — API e contratos

> **Resumo:** Fixa o contrato da API pública `/api/v1`: fonte única em Zod 4 (`packages/contracts`), OpenAPI 3.1 gerado, clientes TypeScript e Dart gerados, CI que barra mudança incompatível; convenções de formato e unidades; Problem Details (RFC 9457) com catálogo de códigos estáveis; idempotência; concorrência por ETag; a tabela completa das rotas do F0 e o resumo do F1/F2; rotas internas e webhook; e exemplos JSON completos de lista de veículos, comando e histórico.
> **Fases:** F0, F1, F2  ·  **Status:** Aprovado para execução
> **Muda em relação à v1.1:**
> - OpenAPI escrito à mão vira OpenAPI gerado de Zod, com clientes gerados e `oasdiff` no CI ([ADR-008](../adr/ADR-008-contrato-primeiro-zod-openapi-sse.md)).
> - Registro de rotas único alimenta OpenAPI, guard de permissão, idempotência, limites e o teste de isolamento por rota.
> - Catálogo fechado de `code` com status HTTP; 404 para fora do escopo em toda rota.
> - Idempotência por usuário + operação + chave com hash da intenção; comando guarda a chave para sempre.
> - Histórico síncrono limitado a 7 dias e aos 90 dias quentes; além disso, exportação assíncrona.

## 1. Contrato primeiro

```text
packages/contracts/src/{common,auth,http,sse,events,internal,routes}/   # problem.ts, problem-codes.ts, permissions.ts (nomes de 08 §3),
                                                                        # vehicles.ts…, vehicle-state.ts (07 §11), *.v1.ts (03 §6), traccar.ts (05 §3), registry.ts
packages/contracts/scripts/build-openapi.ts
packages/contracts/openapi/openapi.json                                 # gerado e versionado
packages/contracts/generated/ts/schema.d.ts · generated/dart/          # gerados e versionados
```

Registro de rotas (fonte do OpenAPI, do guard e dos testes):

```ts
// packages/contracts/src/routes/registry.ts — trecho
export const routes = {
  'vehicles.list': { method: 'GET', path: '/api/v1/vehicles', phase: 'F0', auth: 'session', permission: 'vehicle.read',
    query: VehicleListQuery, responses: { 200: VehicleListResponse }, idempotency: 'none', rateLimit: 'default', aiTool: true },
  'commands.create': { method: 'POST', path: '/api/v1/vehicles/{vehicleId}/commands', phase: 'F1', auth: 'session',
    permission: 'command.execute', params: VehicleParams, body: CommandCreateRequest, responses: { 202: Command },
    idempotency: 'required', idempotencyRetention: 'forever', rateLimit: 'command' },
} as const satisfies Record<string, RouteDef>
// auth: 'session' | 'public' | 'share_session' | 'webhook_asaas'; a chave é o operationId do OpenAPI
```

No `apps/api`, o decorator `@Route('<operationId>')` liga o handler ao registro; um guard único aplica autenticação, permissão ([08 §3](08-identidade-e-seguranca.md)), idempotência (§4), limite ([08 §9](08-identidade-e-seguranca.md)) e valida entrada e saída com os mesmos schemas.

Pipeline (scripts de `packages/contracts/package.json`; versões fixadas na T-004):

```bash
pnpm --filter @tracksys/contracts build      # tsx scripts/build-openapi.ts: z.toJSONSchema() por schema + paths do registro → openapi/openapi.json (OpenAPI 3.1)
pnpm --filter @tracksys/contracts gen:ts     # openapi-typescript openapi/openapi.json -o generated/ts/schema.d.ts
pnpm --filter @tracksys/contracts gen:dart   # docker run openapitools/openapi-generator-cli:<tag fixada> generate -g dart-dio \
                                             #   -o generated/dart --additional-properties=pubName=tracksys_api,enumUnknownDefaultCase=true
pnpm contracts:check                         # build + gen:* + git diff --exit-code + lint de convenções (REQ-API-005)
docker run --rm -v "$PWD":/w tufin/oasdiff breaking /w/.ci/openapi.main.json /w/packages/contracts/openapi/openapi.json --fail-on ERR
```

O console usa `openapi-fetch` com o tipo `paths` gerado; o app usa o pacote Dart `tracksys_api` por dependência de caminho. Conversão Zod → JSON Schema nativa do Zod 4; se faltar recurso, a T-004 adota `zod-openapi` e registra no PR [VALIDAR — T-004]. Opções exatas do gerador Dart: [VALIDAR — T-004].

## 2. Convenções

| Tema | Regra |
|---|---|
| Base | `https://api.<TRACKSYS_DOMAIN>/api/v1`; versão no caminho; `/internal/v1` só na porta 3001 ([03 REQ-ARQ-002](03-arquitetura.md)) |
| Chaves e enums | Chaves em camelCase. Enums em snake_case minúsculo (`fuel_pump`, `moving`, `tenant_owner`), exceto estados de comando, em maiúsculas iguais ao banco e a [06](06-comandos-e-bloqueio.md) (`AWAITING_CONFIRMATION`). Enum de resposta é aberto: cliente trata valor desconhecido como `unknown` |
| Desconhecido | `null` explícito ou `"unknown"`, nunca omitido nem `false`/`0` em campo de estado (INV-03) |
| Tempo | RFC 3339 em UTC com `Z`; intervalo `from` inclusivo, `to` exclusivo; BRT só na UI |
| Unidades (INV-12) | Sufixo no nome: `speedKmh`, `courseDeg`, `radiusM`, `ttlS`, `ageS`, `valueCents` (inteiro, BRL), `batteryPct`, `maxBytes`. Coordenadas `latitude`/`longitude` em graus decimais WGS84 com até 7 casas (`lat_e7 / 10⁷`) |
| Ids | uuid em minúsculas gerado pelo servidor (UUIDv7 recomendado); o cliente não escolhe id de recurso |
| Coleção | `{ "items": [...], "nextCursor": "<opaco>" \| null, "serverTime": "…" }`; `limit` padrão 50, máximo 200 (exceção: histórico, §9.4); `limit` > 200 → 422; keyset por (campo de ordenação, `id`), sem OFFSET; cursor = base64url de JSON validado por Zod, inválido → 422 |
| Recurso | `GET` de item devolve `ETag`; criação 201 com `Location`; ação assíncrona 202 com `Location` do acompanhamento |
| Headers de entrada | `Authorization`, `Idempotency-Key`, `If-Match`, `X-Operator-Id` ([08 §4](08-identidade-e-seguranca.md)), `X-Request-Id` (UUID, ecoado; senão gerado), `X-App-Version` (app), `Last-Event-ID` (SSE) |
| Corpo | `application/json` UTF-8, máximo 1 MiB (importação F1: `multipart/form-data` até 10 MiB); objeto estrito (`z.strictObject`): campo desconhecido → 422 |
| Tempo limite | 10 s por requisição (SSE fora); `SET LOCAL statement_timeout = '5s'` nas transações de rota; estouro → 503 |
| Texto | `title` e `detail` em PT-BR para humanos; o cliente decide pelo `code` |

## 3. Erros: Problem Details

Toda resposta 4xx/5xx usa `Content-Type: application/problem+json`, com `type` = `https://api.<domínio>/problems/<code em kebab-case>`, `title`, `status`, `code`, `detail` opcional, `instance` (caminho), `correlationId` (igual a `X-Request-Id`) e extensões do código. Nunca contém stack, SQL, segredo nem eco do corpo.

```json
{
  "type": "https://api.tracksys.com.br/problems/validation-failed", "title": "Dados inválidos", "status": 422,
  "code": "VALIDATION_FAILED", "detail": "1 campo inválido.", "instance": "/api/v1/vehicles",
  "correlationId": "0192a1b2-7f00-7000-8000-00000000aa01",
  "errors": [{ "path": "plate", "rule": "pattern", "message": "Placa deve seguir o padrão AAA1A11." }]
}
```

| `code` | HTTP | Quando | Extensões | Dono |
|---|---|---|---|---|
| `MALFORMED_REQUEST` | 400 | JSON ilegível | — | 09 |
| `IDEMPOTENCY_KEY_REQUIRED` | 400 | Rota exige `Idempotency-Key` e não veio, ou formato inválido | — | 09 |
| `OPERATOR_SELECTION_REQUIRED` | 400 | Usuário com memberships em mais de uma operadora sem `X-Operator-Id` | `operators[{id, displayName}]` | 08 |
| `AUTH_REQUIRED` | 401 | Sem sessão, sessão expirada, revogada ou no transporte errado | `reason` | 08 |
| `INVALID_CREDENTIALS` | 401 | Login ou TOTP inválido (mesma resposta exista ou não o e-mail) | — | 08 |
| `WEBHOOK_UNAUTHORIZED` | 401 | Token do webhook ausente ou errado | — | 08 |
| `FORBIDDEN` | 403 | Recurso visível; papel sem a permissão (ex.: `tenant_member` sem `can_command`, `allow_app_block = false`, cliente reconhecendo alerta, equipe nas preferências de alerta); escrita em transação somente leitura; login no app de usuário com 2FA ativo (F0) | `reason` opcional; F0: `two_factor_app_unsupported` ([08 §2](08-identidade-e-seguranca.md)) | 08 |
| `CSRF_REJECTED` | 403 | Mutação por cookie sem `Origin` permitido | — | 08 |
| `TWO_FACTOR_ENROLLMENT_REQUIRED` | 403 | Papel exige 2FA ativo | — | 08 |
| `STEP_UP_REQUIRED` | 403 | Comando sem prova; TOTP com mais de 5 min; cadastro de chave sem login recente | `requiredMethod`: `device_key`, `device_key_registration`, `totp`, `password` | 08 |
| `STEP_UP_INVALID` | 403 | Prova recusada | `reason`: `challenge_expired`, `challenge_used`, `intent_mismatch`, `key_revoked`, `signature_invalid`, `totp_reused` | 08 |
| `NOT_FOUND` | 404 | Inexistente **ou fora do escopo** (sem revelar existência) | — | 09 |
| `INVITATION_INVALID` | 404 | Convite inválido, usado ou vencido | — | 08 |
| `CONFLICT` | 409 | Estado conflitante sem código específico | — | 09 |
| `IDEMPOTENCY_CONFLICT` | 409 | Mesma chave com intenção diferente | — | 09 |
| `DEVICE_ALREADY_REGISTERED` · `SIM_ALREADY_REGISTERED` | 409 | IMEI ou ICCID ativo na plataforma, sem revelar a operadora (REQ-DAD-022) | — | 04 |
| `ASSIGNMENT_OVERLAP` | 409 | Vínculo sobreposto (SQLSTATE 23P01) | — | 04 |
| `WATCH_MODE_VEHICLE_ON` · `WATCH_MODE_NO_FIX` | 409 | Vigilância com ignição ligada ou sem fix válido em 24 h | — | 07 |
| `TELEMETRY_STALE` | 409 | Evidência ausente, inválida ou com mais de 60 s quando a política recusa em vez de armar (§9.3) | `evidence` | 06 |
| `SPEED_ABOVE_LIMIT` | 409 | Reservado: hoje a política de 06 arma (`awaiting_speed`) em vez de recusar | `speedKmh`, `maxMovingCutKmh` | 06 |
| `COMMAND_ALREADY_ACTIVE` · `COMMAND_IN_FLIGHT` | 409 | Já existe `block`/`unblock` ativo; o ativo já saiu para o rastreador (com `Retry-After`) | `activeCommandId` | 06 |
| `COMMAND_NOT_CANCELLABLE` | 409 | Cancelamento depois de DISPATCHING | — | 06 |
| `CUT_POINT_MISSING` · `PROFILE_NOT_HOMOLOGATED` | 422 | Vínculo sem `cut_point`; perfil sem homologação com relé (INV-10). Nomes canônicos: os `COMMAND_CUT_POINT_MISSING`, `COMMAND_PROFILE_NOT_HOMOLOGATED` etc. de [06 §14](06-comandos-e-bloqueio.md) mapeiam para os códigos desta tabela (T-018) | — | 06 |
| `COMMAND_NOT_ALLOWED` | 422 | Política recusa | `reason`: `block_terms_missing`, `block_scope_disabled`, `relay_unsupported`, `tenant_closed` (lista em 06) | 06 |
| `PRECONDITION_FAILED` | 412 | `If-Match` diferente do `ETag` atual | — | 09 |
| `PAYLOAD_TOO_LARGE` | 413 | Corpo acima do limite | `maxBytes` | 09 |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | `Content-Type` não aceito na rota | — | 09 |
| `VALIDATION_FAILED` | 422 | Schema ou regra semântica; inclui token de redefinição de senha inválido, usado ou vencido (`errors[0] = {path: "token", rule: "token_invalid"}`, [08 §2](08-identidade-e-seguranca.md)) | `errors[{path, rule, message}]` | 09 |
| `HISTORY_RANGE_TOO_LARGE` | 422 | Histórico com `to − from` > 7 dias | `maxRangeS: 604800` | 09 |
| `HISTORY_REQUIRES_EXPORT` | 422 | `from` anterior aos 90 dias quentes | `hotSince` | 09 |
| `STREAM_SCOPE_TOO_LARGE` · `ALERT_PREFERENCE_LOCKED` | 422 | Ver [07](07-alertas-e-tempo-real.md) | ver 07 | 07 |
| `CLIENT_UPGRADE_REQUIRED` | 426 | `X-App-Version` abaixo de `MIN_APP_VERSION` | `minVersion` | 09 |
| `PRECONDITION_REQUIRED` | 428 | PATCH/PUT sem `If-Match` | — | 09 |
| `RATE_LIMITED` | 429 | Limite de taxa (com `Retry-After`) | `retryAfterS` | 08 |
| `INTERNAL_ERROR` | 500 | Erro não previsto, inclusive violação do contrato de resposta | — | 09 |
| `DEPENDENCY_UNAVAILABLE` | 503 | Banco fora, pool esgotado, `statement_timeout` (com `Retry-After: 5`) | — | 09 |
| `COMMAND_DISPATCH_DISABLED` | 503 | `block` com despacho desligado (failover, REQ-ARQ-016) | — | 06 |
| `INGEST_*` | 400/401/413/503 | Rotas internas | ver 05 | [05 §3](05-ingestao-e-telemetria.md) |

Recusa síncrona de comando (permissão, step-up, política) não cria linha em `command`: grava `audit_log` `command.request` com `result = 'denied'` ([06 §4.2](06-comandos-e-bloqueio.md)). Mapeamento de erro do banco: 42501 (WITH CHECK) e 23503 (FK composta) → 404; 23P01 → 409 específico; 23505 → 409 específico da constraint; 25006 → 403; 57014, 08xxx e 53300 → 503; 40001/40P01 → 1 nova tentativa da transação, depois 503.

## 4. Idempotência

Obrigatória em:

| Operação | Rota | Retenção da chave |
|---|---|---|
| `command.create` · `command.contingency` | `POST /api/v1/vehicles/{vehicleId}/commands` · `.../commands/contingency` | Com o comando (5 anos): a própria linha de `command` é o registro ([06 §4.3](06-comandos-e-bloqueio.md)) |
| `invitation.create` | `POST /api/v1/invitations` | 24 h |
| `import.create` | `POST /api/v1/imports` | 24 h |
| `share_link.create` | `POST /api/v1/share-links` | 24 h |
| `export.create` | `POST /api/v1/exports`, `POST /api/v1/evidence-packages`, `POST /api/v1/me/data-exports` | 24 h |

Outros POST aceitam a chave opcionalmente, com a mesma semântica. Formato: 16 a 64 caracteres `[A-Za-z0-9_-]`; comandos exigem UUID.

```sql
-- rls: A (tenant_id NULL em operação de nível operadora → entrada em nullableTenantId); criada pela T-006, DDL canônico em 04
CREATE TABLE app.idempotency_record (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL REFERENCES app.operator (id), tenant_id uuid NULL,
  user_id uuid NOT NULL REFERENCES auth."user" (id),
  operation text NOT NULL CHECK (operation ~ '^[a-z_-]+(\.[a-z_-]+)+$'),   -- operationId do registro de rotas, ex.: device-assignments.create
  key text NOT NULL CHECK (key ~ '^[A-Za-z0-9_-]{16,64}$'),
  intent_sha256 bytea NOT NULL CHECK (length(intent_sha256) = 32),
  response_status smallint NULL, resource_type text NULL, resource_id uuid NULL, problem jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz NOT NULL,   -- created_at + 24 h
  CONSTRAINT idempotency_record_tenant_fk FOREIGN KEY (operator_id, tenant_id) REFERENCES app.tenant (operator_id, id),
  CONSTRAINT idempotency_record_scope_key UNIQUE (user_id, operation, key)
);
```

1. Escopo: usuário + operação + chave. Intenção: SHA-256 de `operation + "\n" + JCS(params) + "\n" + JCS(body)` (JSON canônico RFC 8785); em comandos, o corpo sem `stepUp` (repetição com nova assinatura devolve o mesmo comando).
2. Primeiro comando da transação da rota: `INSERT ... ON CONFLICT (user_id, operation, key) DO NOTHING RETURNING id`. Requisição concorrente com a mesma chave espera no índice único até a primeira terminar (arbitragem pelo banco, sem lock em memória).
3. Sem linha devolvida: lê a existente. Mesmo hash → repete o status original com a representação atual de `resource_id` (ou o `problem` gravado) e `Idempotent-Replayed: true`. Hash diferente → 409 `IDEMPOTENCY_CONFLICT`.
4. Com linha: executa, grava `response_status`, `resource_type`, `resource_id` e faz COMMIT. Erro de validação ou exceção → ROLLBACK e a chave fica livre. Recusa de negócio persistida (ex.: comando `REJECTED` com 409) grava `problem` sem `correlationId`.
5. `expires_at = created_at + 24 h`; chave vencida é reaproveitada pelo `ON CONFLICT … WHERE expires_at <= now()` (T-006); o expurgo de volume é de hora em hora por `app.retention_purge('idempotency_record', 50000)` ([04 §4.4](04-dominio-e-dados.md); a função ainda não tem cartão no F0). Comandos não usam esta tabela: `command` guarda `idempotency_key` UNIQUE por `(operator_id, tenant_id)` e `request_sha256`; a mesma chave vinda de outro usuário recebe 409 `IDEMPOTENCY_CONFLICT`, o que mantém o escopo por usuário.
6. Comando: a checagem de idempotência vem antes da verificação do step-up, então a repetição devolve o comando existente sem consumir outro desafio ([08 §6.3](08-identidade-e-seguranca.md)).

## 5. Concorrência otimista

1. `ETag` forte `"u<updated_at em microssegundos desde a época>"`, ex.: `"u1760972400123456"`, em `tenant`, `vehicle`, `device` e `operator_brand` (`command_policy` é versionada por INSERT, [06 §3.3](06-comandos-e-bloqueio.md)).
2. PATCH e PUT desses recursos exigem `If-Match`: ausente → 428 `PRECONDITION_REQUIRED`; diferente → 412 `PRECONDITION_FAILED` com o `ETag` atual no header. PATCH segue JSON Merge Patch (RFC 7396): `null` limpa campo opcional; aceita `application/merge-patch+json` e `application/json`.
3. SQL: `UPDATE app.vehicle SET nickname = $3, updated_at = greatest(clock_timestamp(), updated_at + interval '1 microsecond') WHERE id = $1 AND updated_at = $2 RETURNING updated_at`; 0 linhas → relê: ausente → 404, presente → 412.
4. Comando usa `stateVersion` ([06 §4.3](06-comandos-e-bloqueio.md)): `ETag: "<stateVersion>"` e `POST /api/v1/commands/{id}/cancel` com `If-Match: "<stateVersion>"`.

## 6. Rotas do F0

| Método e caminho | Permissão | Request → Response | Idem. |
|---|---|---|---|
| `POST /api/v1/auth/sign-in/email` | público | `{email, password}` → 200 `{user, twoFactorRedirect}`; app recebe o token em `set-auth-token`, console recebe cookie ([08 §2](08-identidade-e-seguranca.md)) | — |
| `POST /api/v1/auth/two-factor/verify-totp` | login pendente | `{code}` → 200 sessão completa | — |
| `POST /api/v1/auth/sign-out` | sessão | → 200; no app revoga a chave do aparelho | — |
| `POST /api/v1/auth/request-password-reset` · `/reset-password` | público | `{email}` → 200 sempre · `{token, newPassword}` → 200 | — |
| `POST /api/v1/auth/change-password` | sessão | `{currentPassword, newPassword}` → 200; revoga outras sessões e chaves | — |
| `POST /api/v1/auth/two-factor/enable` · `/disable` | sessão + senha | `{password}` → 200 `{totpURI, backupCodes[10]}` · 200 | — |
| `GET /api/v1/me` | sessão | → 200 `{user{id, name, email, twoFactorEnabled}, clientKind, operator{id, displayName}, brand, memberships[{id, role, tenantId}], permissions[]}` | — |
| `POST /api/v1/invitations` | `user.manage_staff` / `user.manage_customer` | `{email, name, role, tenantId?}` → 201 `{membershipId, status: "invited", expiresAt}` | obrigatória |
| `POST /api/v1/invitations/accept` | público (token) | `{token, password}` → 200 `{userId}` | — |
| `GET /api/v1/memberships` · `DELETE /api/v1/memberships/{membershipId}` | `user.manage_*` | `?tenantId&role&status&cursor&limit` → coleção · → 204 e revogação ≤ 60 s | — |
| `GET /api/v1/tenants` · `POST` | `tenant.read` · `tenant.write` | `?q&status&cursor&limit` → coleção · `{kind, displayName, document?}` → 201 + `ETag` | opcional |
| `GET /api/v1/tenants/{tenantId}` · `PATCH` | `tenant.read` · `tenant.write` | → 200 + `ETag` · merge patch + `If-Match` → 200 | — |
| `GET /api/v1/vehicles` | `vehicle.read` | `?tenantId&q&presence&cursor&limit` → coleção com estado (§9.1) | — |
| `POST /api/v1/vehicles` | `vehicle.write` | `{tenantId, kind, plate?, make?, model?, color?, year?, nickname?}` → 201 + `ETag` | opcional |
| `GET /api/v1/vehicles/{vehicleId}` · `PATCH` | `vehicle.read` · `vehicle.write` | item de §9.1 + `ETag` · merge patch + `If-Match` (titular: só `nickname`, `color`) | — |
| `GET /api/v1/vehicles/{vehicleId}/history` | `telemetry.history` | `?from&to&cursor&limit` → §9.4 | — |
| `GET /api/v1/vehicles/{vehicleId}/assignments` | `vehicle.read` + `device.read` | → coleção `{id, deviceId, cutPoint, isPrimary, validFrom, validTo}` | — |
| `GET /api/v1/devices` · `POST` | `device.read` · `device.write` | `?status&q&cursor&limit` · `{imei, model, protocol, capabilityProfileId, firmware?, simIccid?}` → 201 `{…, provisioning: "pending"}` (o worker cadastra no Traccar); cria na mesma transação a linha de `device_state` do rastreador, sem vínculo (T-007); 409 `DEVICE_ALREADY_REGISTERED` | opcional |
| `GET /api/v1/devices/{deviceId}` · `PATCH` | `device.read` · `device.write` | → 200 + `ETag`, `provisioning` ∈ `pending`, `done`, `failed`, IMEI completo só aqui · `{status, firmware, simIccid}` + `If-Match` | — |
| `GET /api/v1/sim-cards` · `POST` | `device.read` · `device.write` | `?q&cursor&limit` · `{iccid, msisdn?, apn?}` → 201; 409 `SIM_ALREADY_REGISTERED` | opcional |
| `POST /api/v1/device-assignments` | `assignment.write` | `{vehicleId, deviceId, cutPoint, isPrimary, notes?}` com `cutPoint` obrigatório (`fuel_pump`, `ignition`, `starter` ou `null` explícito = sem bloqueio, INV-10) → 201; 409 `ASSIGNMENT_OVERLAP` | opcional |
| `POST /api/v1/device-assignments/{assignmentId}/close` | `assignment.write` | `{reason, deviceStatus?}` → 200 `{validTo}` (corte não retroativo, [04 §9.1](04-dominio-e-dados.md)); `deviceStatus` opcional `stock` (padrão) ou `maintenance` define o status do rastreador devolvido (C06, [10 §9](10-apps-e-ux.md); acréscimo aditivo da T-007) | — |
| `GET /api/v1/capability-profiles` | equipe da operadora | → coleção `{id, model, firmwareRange, protocol, version, status, capabilities}` | — |
| `GET /api/v1/operator/brand` · `PUT` | sessão · `brand.manage` | → 200 + `ETag`, `If-None-Match` igual → 304 sem corpo (T-009; `GET /api/v1/me` traz o mesmo `brand`) · `{displayName, logoUrl, primaryColor, secondaryColor, supportWhatsapp, supportPhone}` + `If-Match`. O `PUT` serve à tela Marca (C13, F1); no F0 a marca é gravada pelo script `seed:brand` ([10 §4](10-apps-e-ux.md)) | — |
| `GET /api/v1/stream` | `telemetry.live` | SSE ([07 §11](07-alertas-e-tempo-real.md)) | — |
| `GET /api/v1/alerts` · `POST /api/v1/alerts/{alertId}/acknowledge` | `alert.read` · `alert.ack` | [07 §9](07-alertas-e-tempo-real.md) | — |
| `POST` · `DELETE /api/v1/vehicles/{vehicleId}/watch-mode` | `watch_mode.manage` | [07 §5](07-alertas-e-tempo-real.md) | — |
| `GET` · `PUT /api/v1/me/alert-preferences`; `PUT` · `DELETE /api/v1/me/push-tokens` | sessão | [07 §7–8](07-alertas-e-tempo-real.md) | — |
| `GET /health/live` · `/health/ready` | público | [03 REQ-ARQ-005](03-arquitetura.md) | — |

## 7. Rotas do F1 e do F2 (resumo)

| Grupo | Rotas | Fase | Regras |
|---|---|---|---|
| Comandos | `GET /api/v1/vehicles/{id}/command-availability` · `POST /api/v1/vehicles/{id}/commands/challenges` (201) · `POST /api/v1/vehicles/{id}/commands` (202, idem.) · `POST /api/v1/vehicles/{id}/commands/contingency` (201, idem.) · `GET /api/v1/vehicles/{id}/commands` · `GET /api/v1/commands/{commandId}` · `POST /api/v1/commands/{commandId}/cancel` | F1 | [06 §14](06-comandos-e-bloqueio.md), [08 §6](08-identidade-e-seguranca.md), §9.2 |
| Step-up e sessões | `POST /api/v1/me/step-up` (204) · `POST /api/v1/device-keys` (201) · `GET /api/v1/me/device-keys` · `DELETE /api/v1/device-keys/{id}` · `POST /api/v1/users/{userId}/revoke-sessions` (204) | F1 | [08 §6](08-identidade-e-seguranca.md) |
| Política e termo | `GET` · `POST /api/v1/command-policies` (201 nova `version`, step-up de console) · `POST /api/v1/tenants/{tenantId}/block-terms` (201) | F1 | [06 §3.3, §12](06-comandos-e-bloqueio.md) |
| Links | `POST /api/v1/share-links` (201, idem.) · `GET /api/v1/share-links?vehicleId=` · `DELETE /api/v1/share-links/{id}` · `POST /api/v1/public/share-sessions` · `GET /api/v1/public/share-sessions/current` · `GET /api/v1/public/stream` | F1 | [08 §7](08-identidade-e-seguranca.md) |
| Ocorrência | `POST /api/v1/vehicles/{id}/occurrences` · `GET` · `PATCH /api/v1/occurrences/{id}` · `POST /api/v1/occurrences/{id}/close` | F1 | [06](06-comandos-e-bloqueio.md) |
| Exportação | `POST /api/v1/exports` (202, idem.) · `GET /api/v1/exports/{id}` · `GET /api/v1/exports/{id}/download` | F1 | §9.4 |
| Conformidade | `GET /api/v1/audit-log` · `POST` · `GET` · `DELETE /api/v1/support-grants` · `POST /api/v1/legal-holds` · `POST /api/v1/legal-holds/{id}/release` · `POST /api/v1/evidence-packages` (202, idem.) · `GET /api/v1/evidence-packages/{id}/download` · `POST /api/v1/me/data-exports` (202, idem.) · `POST` · `DELETE /api/v1/me/consents` | F1 | [08 §11](08-identidade-e-seguranca.md) |
| Cobrança | `GET` · `PUT /api/v1/billing/account` · `GET /api/v1/invoices` · `GET /api/v1/invoices/{id}` (com `pixPayload`) · `GET /api/v1/platform-fees` | F1 | [12](12-cobranca-e-svas.md) |
| Atendimento e SVA | `GET` · `POST /api/v1/tickets` · `PATCH /api/v1/tickets/{id}` · `GET /api/v1/partners` · `POST /api/v1/referrals` | F1 | [10](10-apps-e-ux.md), [12](12-cobranca-e-svas.md) |
| Onboarding | `POST /api/v1/imports` (multipart, idem.) · `GET /api/v1/imports/{id}` · `POST /api/v1/imports/{id}/commit` · `POST /api/v1/migration-waves` · `GET /api/v1/migration-waves/{id}` · `POST /api/v1/migration-waves/{id}/rollback` | F1 | [11](11-onboarding-e-migracao.md) |
| Cercas | `GET` · `POST /api/v1/vehicles/{id}/geofences` · `PATCH` · `DELETE /api/v1/geofences/{id}` | F1 | [07](07-alertas-e-tempo-real.md) |
| F2 | Portal do parceiro `/api/v1/partner/*` · onboarding `/api/v1/platform/operators` · diagnóstico `GET /api/v1/sim-cards/{id}/diagnostics` · agente de suporte `POST /api/v1/support-agent/messages` | F2 | [11](11-onboarding-e-migracao.md), [12](12-cobranca-e-svas.md), [08 §12](08-identidade-e-seguranca.md) |

## 8. Rotas internas e webhook

| Rota | Autenticação | Contrato | Dono |
|---|---|---|---|
| `POST /internal/v1/traccar/positions` · `/events` | `X-Ingest-Token`, só porta 3001 | 202 `{result, inboxId}`; erros `INGEST_*`; corpo ≤ 256 KiB; prazo 5 s | [05 §3](05-ingestao-e-telemetria.md) |
| `POST /api/v1/webhooks/asaas/{operatorId}` | Header `asaas-access-token` [VALIDAR — tarefa de cobrança] contra o SHA-256 da operadora do caminho | Corpo ≤ 256 KiB; 200 `{"result": "processed" \| "duplicate" \| "ignored"}` após o commit; 401 `WEBHOOK_UNAUTHORIZED`; sem sessão, sem CORS; dedupe pelo id do evento; nunca aciona comando (INV-09) | [12](12-cobranca-e-svas.md), [08 §8](08-identidade-e-seguranca.md) |

Schemas das rotas internas ficam em `packages/contracts/src/internal/traccar.ts` e não entram no OpenAPI público.

## 9. Exemplos

### 9.1 `GET /api/v1/vehicles?limit=2` (`agente.alfa`)

`state` é exatamente o schema do evento SSE `vehicle.state` ([07 §11](07-alertas-e-tempo-real.md)); `stateAge` é calculado contra `serverTime` e o cliente recalcula a cada 10 s; `availableActions` explica por que uma ação está indisponível.

Acréscimos aditivos adotados na v2.0 (T-008):
- `presenceThresholds: {delayedAfterS, offlineAfterS, lostMovingAfterS}` em cada item, do perfil efetivo do dispositivo primário (`stopped_interval_s + 60`, `1800`, `max(180, 3 × moving_interval_s)`; perfil ausente ou não legível → `{360, 1800, 180}`), usado pelo cliente para recalcular `presence` ([10 §5](10-apps-e-ux.md)).
- `availableActions.block.reason`/`unblock.reason` no F0 (nunca disponível), na ordem: `NO_PRIMARY_DEVICE` (veículo sem vínculo primário aberto) → `CUT_POINT_MISSING` → `PROFILE_NOT_HOMOLOGATED` → `COMMAND_DISPATCH_DISABLED`. `watchMode` vale `{available: false, active: false}` até a T-011 ligar o leitor real.
- No escopo `tenant`, `app.device` (tipo C) não é legível: o titular recebe `primaryDevice.model`, `imeiLast4` e `profileStatus` nulos e os limiares padrão do J16 [VALIDAR — DEC-02]. Perfil diferente do J16 no escopo do cliente (F1) exige função `SECURITY DEFINER` ou visão de limiares, com revisão N0 e CAT-07 ([04](04-dominio-e-dados.md)).

```json
{
  "items": [
    {
      "id": "0192a1b2-0000-7000-8000-0000000000f1", "tenantId": "0192a1b2-0000-7000-8000-0000000000a1",
      "plate": "TST1A23", "nickname": "Gol prata", "kind": "car", "make": "Volkswagen", "model": "Gol",
      "color": "Prata", "year": 2019, "archivedAt": null,
      "primaryDevice": { "id": "0192a1b2-0000-7000-8000-0000000000d1", "model": "J16", "imeiLast4": "0001", "profileStatus": "draft" },
      "state": {
        "vehicleId": "0192a1b2-0000-7000-8000-0000000000f1", "deviceId": "0192a1b2-0000-7000-8000-0000000000d1",
        "isPrimary": true, "revision": 1048577, "lastContactAt": "2026-10-20T15:20:00.000Z", "lastFixAt": "2026-10-20T15:19:58.000Z",
        "position": { "latitude": -5.089211, "longitude": -42.801892, "speedKmh": 18.5, "courseDeg": 179 },
        "ignition": true, "motion": "moving", "relayState": "unknown", "powerState": "main", "presence": "online"
      },
      "stateAge": { "contactAgeS": 4, "fixAgeS": 6 },
      "presenceThresholds": { "delayedAfterS": 360, "offlineAfterS": 1800, "lostMovingAfterS": 180 },
      "availableActions": { "block": { "available": false, "reason": "PROFILE_NOT_HOMOLOGATED" },
        "unblock": { "available": false, "reason": "PROFILE_NOT_HOMOLOGATED" }, "watchMode": { "available": true, "active": false } }
    },
    {
      "id": "0192a1b2-0000-7000-8000-0000000000f3", "tenantId": "0192a1b2-0000-7000-8000-0000000000a2",
      "plate": "TST3C45", "nickname": null, "kind": "motorcycle", "make": "Honda", "model": "CG 160",
      "color": "Vermelha", "year": 2022, "archivedAt": null,
      "primaryDevice": { "id": "0192a1b2-0000-7000-8000-0000000000d4", "model": "J16", "imeiLast4": "0004", "profileStatus": "draft" },
      "state": {
        "vehicleId": "0192a1b2-0000-7000-8000-0000000000f3", "deviceId": "0192a1b2-0000-7000-8000-0000000000d4",
        "isPrimary": true, "revision": 1040002, "lastContactAt": "2026-10-20T14:41:10.000Z", "lastFixAt": null,
        "position": null, "ignition": null, "motion": "unknown", "relayState": "unknown", "powerState": "unknown", "presence": "offline"
      },
      "stateAge": { "contactAgeS": 2334, "fixAgeS": null },
      "presenceThresholds": { "delayedAfterS": 360, "offlineAfterS": 1800, "lostMovingAfterS": 180 },
      "availableActions": { "block": { "available": false, "reason": "CUT_POINT_MISSING" },
        "unblock": { "available": false, "reason": "CUT_POINT_MISSING" }, "watchMode": { "available": false, "active": false } }
    }
  ],
  "nextCursor": "eyJrIjpbIlRTVDNDNDUiLCIwMTkyYTFiMi0wMDAwLTcwMDAtODAwMC0wMDAwMDAwMDAwZjMiXX0",
  "serverTime": "2026-10-20T15:20:04.000Z"
}
```

### 9.2 `POST /api/v1/vehicles/{vehicleId}/commands` (F1)

Headers: `Authorization: Bearer <token>`, `Idempotency-Key: 0192a1b2-9a00-7000-8000-000000000101`, `Content-Type: application/json`, `X-App-Version: 1.3.0`. Corpo do app (step-up por chave do aparelho, [08 §6.3](08-identidade-e-seguranca.md)):

```json
{
  "type": "block", "reasonCode": "theft_suspected", "reason": null,
  "stepUp": { "kind": "device_key", "challengeId": "0192a1b2-0c00-7000-8000-00000000c001",
              "deviceKeyId": "0192a1b2-0b00-7000-8000-00000000b001", "signature": "MEUCIQDx3k0Zr2…assinatura-DER-em-base64url…" }
}
```

Corpo do console (TOTP na sessão há ≤ 5 min): `{"type": "block", "reasonCode": "theft_suspected", "reason": "Cliente ligou às 21:00 relatando furto na garagem", "stepUp": {"kind": "console_totp"}}`. `reasonCode` vem do catálogo de [06 §6](06-comandos-e-bloqueio.md).

Resposta `202 Accepted`, `Location: /api/v1/commands/0192a1b2-0d00-7000-8000-00000000d001`, `ETag: "2"`. 202 significa pedido persistido, **não** veículo bloqueado. Repetição com a mesma chave: 202 com `Idempotent-Replayed: true`. O resultado chega por `GET /api/v1/commands/{id}`, push ([07](07-alertas-e-tempo-real.md)) e pelo evento SSE `command.state` (sem `id`; `data` = `{commandId, vehicleId, type, state, stateVersion, stateReason, at}`), enviado às conexões que têm o veículo no escopo; o cliente descarta `stateVersion` menor ou igual à exibida.

```json
{
  "id": "0192a1b2-0d00-7000-8000-00000000d001", "vehicleId": "0192a1b2-0000-7000-8000-0000000000f1",
  "deviceId": "0192a1b2-0000-7000-8000-0000000000d1", "type": "block", "state": "READY", "stateVersion": 2,
  "stateReason": null, "cutPoint": "fuel_pump", "ceilingKmh": 40, "policyVersion": 3,
  "requestedVia": "app", "requestedBy": "0192a1b2-0000-7000-8000-0000000000e1", "reasonCode": "theft_suspected",
  "createdAt": "2026-11-20T00:10:30.120Z", "expiresAt": "2026-11-20T00:15:30.120Z",
  "evidence": { "evaluatedAt": "2026-11-20T00:10:30.120Z", "lastFixAt": "2026-11-20T00:10:21.000Z", "speedKmh": 23.5 }
}
```

Campos e prazos seguem [06 §14](06-comandos-e-bloqueio.md) (`expiresAt` = criação + `armed_ttl_s`); `evidence` resume `evidence_snapshot`.

### 9.3 Erro `TELEMETRY_STALE`

```json
{
  "type": "https://api.tracksys.com.br/problems/telemetry-stale", "title": "Telemetria antiga para decidir o comando",
  "status": 409, "code": "TELEMETRY_STALE",
  "detail": "O rastreador está sem comunicação há 38 min e a última posição válida tem 41 min. O bloqueio exige posição de até 60 s.",
  "instance": "/api/v1/vehicles/0192a1b2-0000-7000-8000-0000000000f1/commands",
  "correlationId": "0192a1b2-7f00-7000-8000-00000000aa02",
  "evidence": { "lastContactAt": "2026-11-20T23:32:00.000Z", "lastFixAt": "2026-11-20T23:29:00.000Z", "ageS": 2460, "maxAgeS": 60, "presence": "offline" }
}
```

Nenhuma linha em `command`; `audit_log` `command.request` `denied`. Com presença `online` ou `delayed`, a política de [06 §3](06-comandos-e-bloqueio.md) arma (`awaiting_evidence` ou `awaiting_on_demand_fix`) em vez de recusar. [ADOTADO NA v2.0: com presença `offline` (contato há mais de 1.800 s), o pedido de `block` é recusado na hora com 409 `TELEMETRY_STALE` em vez de ficar ARMED 5 min sem chance de evidência; `unblock` segue [06](06-comandos-e-bloqueio.md).]

### 9.4 `GET /api/v1/vehicles/{vehicleId}/history`

Regras: `from` e `to` obrigatórios (RFC 3339, `to > from`); `to − from` ≤ 604.800 s (7 dias), senão 422 `HISTORY_RANGE_TOO_LARGE`; `from` ≥ agora − 90 dias, senão 422 `HISTORY_REQUIRES_EXPORT`; `to` no futuro é cortado em agora. Inclui as posições de todos os vínculos primários do veículo no período ([04 §7.3](04-dominio-e-dados.md)), em ordem de `fixTime`. Página: `limit` padrão 1.000, máximo 5.000 pontos (exceção à regra de coleção); cursor com o último `(fixTime, assignmentId)`. `flags` traz os nomes dos bits de [05 §4.1](05-ingestao-e-telemetria.md). `gaps`: `signal_lost_moving` quando o ponto anterior tem `speedKmh` ≥ 5 e o intervalo passa de 180 s; `no_data` quando o intervalo passa de 2.400 s [PREMISSA; intervalos do J16 — DEC-02]. Lacuna não é preenchida nem interpolada. `availableFrom` (acréscimo aditivo da T-008) = início do 1º vínculo primário do veículo visível no escopo, ou `null` sem vínculo; o app e o console usam o campo para "Histórico disponível a partir de {data}" (A04, C07).

`GET /api/v1/vehicles/0192a1b2-0000-7000-8000-0000000000f1/history?from=2026-10-20T03:00:00Z&to=2026-10-21T03:00:00Z` (dia 20/10 em BRT):

```json
{
  "vehicleId": "0192a1b2-0000-7000-8000-0000000000f1",
  "from": "2026-10-20T03:00:00.000Z",
  "to": "2026-10-21T03:00:00.000Z",
  "units": { "speed": "km/h", "course": "deg", "coordinates": "WGS84, graus decimais", "time": "UTC, RFC 3339" },
  "items": [
    { "fixTime": "2026-10-20T10:58:12.000Z", "latitude": -5.089211, "longitude": -42.801892, "speedKmh": 0.0, "courseDeg": null, "ignition": false, "valid": true, "flags": ["KEEPALIVE_30MIN"] },
    { "fixTime": "2026-10-20T11:02:30.000Z", "latitude": -5.088011, "longitude": -42.801102, "speedKmh": 18.5, "courseDeg": 34, "ignition": true, "valid": true, "flags": [] },
    { "fixTime": "2026-10-20T11:03:00.000Z", "latitude": -5.086842, "longitude": -42.800331, "speedKmh": 31.4, "courseDeg": 36, "ignition": true, "valid": true, "flags": [] },
    { "fixTime": "2026-10-20T11:09:40.000Z", "latitude": -5.079100, "longitude": -42.795020, "speedKmh": 27.8, "courseDeg": 41, "ignition": true, "valid": true, "flags": ["LATE"] }
  ],
  "gaps": [{ "from": "2026-10-20T11:03:00.000Z", "to": "2026-10-20T11:09:40.000Z", "durationS": 400, "kind": "signal_lost_moving" }],
  "qualitySummary": { "points": 4, "validPoints": 4, "invalidPoints": 0, "latePoints": 1, "maxGapS": 400 },
  "nextCursor": null,
  "availableFrom": "2026-09-02T14:10:00.000Z",
  "dataWatermark": "2026-10-21T03:00:04.512Z",
  "serverTime": "2026-10-21T10:00:00.000Z"
}
```

Período maior que 7 dias ou anterior aos 90 dias quentes: `POST /api/v1/exports` com `{"kind": "vehicle_history", "vehicleId": "…", "from": "2026-06-01T03:00:00Z", "to": "2026-07-01T03:00:00Z", "format": "csv"}` e `Idempotency-Key` → 202 `{id, status: "queued"}`; até 92 dias por exportação, dentro dos 12 meses retidos; o worker lê o quente (Postgres) e o frio (Parquet, [04 §8.3](04-dominio-e-dados.md)); o resultado traz SHA-256 e fica disponível por 7 dias em `GET /api/v1/exports/{id}/download`, que revalida a permissão.

## 10. Evolução de schema

1. Em `/api/v1` só entra mudança aditiva: rota nova, campo opcional novo na requisição, campo novo na resposta, valor novo em enum de requisição, valor novo em enum de resposta (enum aberto; Dart gerado com `enumUnknownDefaultCase=true`, TS com ramo `default`).
2. Incompatível e proibido em `/api/v1`: remover ou renomear campo ou rota, mudar tipo, unidade ou formato, tornar obrigatório um campo de requisição, tornar anulável um campo de resposta que não era, remover valor de enum, mudar status de sucesso ou o significado de um `code`.
3. Caminho para mudança incompatível: rota nova ou `/api/v2/...` do recurso; a antiga recebe `deprecated: true` e os headers `Deprecation` (RFC 9745) e `Sunset` (RFC 8594) com ≥ 90 dias de antecedência, e só sai quando `MIN_APP_VERSION` já exige uma versão do app que não a usa.
4. Eventos de outbox e SSE: tipo `.v2` publicado em paralelo ao `.v1` até todos os consumidores migrarem ([ADR-008](../adr/ADR-008-contrato-primeiro-zod-openapi-sse.md)).
5. `X-App-Version` abaixo de `MIN_APP_VERSION` (variável do `api`) → 426 `CLIENT_UPGRADE_REQUIRED`; o app mostra a tela de atualização. Requisição sem o header (console) não é afetada.
6. O CI compara o OpenAPI do PR com o de `main` via `oasdiff breaking --fail-on ERR`; exceção só com o rótulo `api-breaking` e rota nova em `/api/v2`.

## 11. Requisitos

Fixture dos CTs: a mesma de [08 §13](08-identidade-e-seguranca.md).

### REQ-API-001 — Contrato único e registro de rotas
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-12
**Regra.** Todo schema de requisição, resposta, erro, evento SSE e evento de outbox DEVE nascer em `packages/contracts` (Zod 4). Toda rota pública DEVE estar no registro do §1; o `api` DEVE falhar no boot com rota sem handler ou handler sem rota.
**Aceite.** CT-API-001 — Dado um handler `@Route('vehicles.archive')` sem entrada no registro, Quando o `api` inicia, Então sai com código 78 e o stderr contém `rota sem contrato: vehicles.archive`; Dado a entrada no registro sem handler, Então sai com 78 e `contrato sem handler: vehicles.archive`.

### REQ-API-002 — OpenAPI e clientes gerados e versionados
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** —
**Regra.** `pnpm contracts:check` DEVE regenerar `openapi/openapi.json` (OpenAPI 3.1), o cliente TS e o cliente Dart e falhar com `git diff --exit-code` se algo mudar. O CI DEVE rodá-lo em todo PR.
**Aceite.** CT-API-002 — Dado `main`, Quando `pnpm contracts:check` roda, Então sai com 0; Dado um PR que adiciona o campo opcional `vinLast4` em `VehicleSummary` sem regenerar, Então sai com 1 listando `packages/contracts/openapi/openapi.json` e `packages/contracts/generated/ts/schema.d.ts`.

### REQ-API-003 — Mudança incompatível barrada
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** —
**Regra.** O CI DEVE rodar `oasdiff breaking` entre o OpenAPI de `main` e o do PR com `--fail-on ERR`, salvo rótulo `api-breaking` com rota em `/api/v2`.
**Aceite.** CT-API-003 — Dado um PR que remove `plate` da resposta de `GET /api/v1/vehicles`, Quando o job de contratos roda, Então falha apontando a remoção da propriedade; Dado um PR que só adiciona `vinLast4` opcional, Então passa.

### REQ-API-004 — Validação de entrada e de saída
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-03, INV-12
**Regra.** O `api` DEVE validar parâmetros, query e corpo com os schemas do registro (objeto estrito) e validar a resposta antes de enviar; violação de resposta DEVE virar 500 `INTERNAL_ERROR` com log `response_contract_violation`.
**Aceite.** CT-API-004 — Dado `agente.alfa`, Quando `POST /api/v1/vehicles` com `{"tenantId":"<A1>","kind":"car","plate":"abc-1234"}`, Então 422 com `errors[0] = {path: "plate", rule: "pattern"}`; com o campo extra `"cor2": "x"`, Então 422 com `rule = "unrecognized_key"`; Dado um handler de teste que devolve `"ignition": "false"` (string), Então 500 `INTERNAL_ERROR` e 1 log `response_contract_violation` com `route = "vehicles.get"`.

### REQ-API-005 — Convenções de formato verificadas
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-12
**Regra.** O lint de convenções DEVE reprovar no OpenAPI: chave fora de camelCase; data sem `format: date-time`; id sem `format: uuid`; campo numérico cujo nome contém `speed`, `distance`, `duration`, `age`, `ttl`, `radius`, `course`, `altitude`, `value`, `amount`, `price`, `battery` ou `timeout` sem terminar em `Kmh`, `M`, `S`, `Deg`, `Cents`, `Pct` ou `Bytes`; dinheiro (`*Cents`) que não seja inteiro.
**Aceite.** CT-API-005 — Dado um schema com `speed_kmh`, Quando `pnpm contracts:check` roda, Então falha com `chave fora de camelCase: speed_kmh`; com `speed: number`, Então `grandeza sem unidade: speed`; com `valueCents` do tipo `number` não inteiro, Então `dinheiro deve ser inteiro: valueCents`.

### REQ-API-006 — Paginação por cursor
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-07
**Regra.** Coleções DEVEM usar keyset com cursor opaco, `limit` padrão 50 e máximo 200, aplicando o escopo antes da paginação.
**Aceite.** CT-API-006 — Dado 120 veículos na Alfa, Quando `agente.alfa` lista sem `limit` e segue os cursores, Então recebe 50, 50 e 20 itens, o último com `nextCursor = null`, sem repetição nem falta mesmo com 1 veículo criado entre a 1ª e a 2ª página; Quando usa `limit=201`, Então 422; com cursor adulterado, Então 422.

### REQ-API-007 — Problem Details com `code` estável
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** —
**Regra.** Todo erro DEVE seguir o §3 com `code` do catálogo; NÃO DEVE conter stack, SQL, segredo ou eco do corpo. Um `code` publicado NÃO DEVE mudar de status nem de significado em `/api/v1`.
**Aceite.** CT-API-007 — Dado falha de banco injetada em `GET /api/v1/tenants`, Então 500 com `Content-Type: application/problem+json`, `code = "INTERNAL_ERROR"`, `correlationId` igual ao header `X-Request-Id` e corpo sem `SELECT` nem linhas `at `; e o teste do catálogo falha se dois códigos tiverem o mesmo `type` ou se um código do enum Zod faltar na tabela do §3.

### REQ-API-008 — 404 para recurso fora do escopo
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N0 · **Invariantes:** INV-07
**Regra.** Recurso de outra operadora ou de outro cliente DEVE responder exatamente como recurso inexistente (404 `NOT_FOUND`), inclusive quando a violação vem de RLS (42501) ou de FK composta (23503).
**Aceite.** CT-API-008 — Dado `dono.a2`, Quando `GET /api/v1/vehicles/{V1}` e `GET /api/v1/vehicles/{uuid aleatório}`, Então ambos 404 com `type`, `title` e `detail` iguais; Quando `admin.beta` faz `PATCH /api/v1/vehicles/{V1}`, Então 404; Quando `agente.alfa` faz `POST /api/v1/device-assignments` com `vehicleId = V2`, Então 404, não 409 nem 500.

### REQ-API-009 — Idempotency-Key
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N0 · **Invariantes:** INV-08
**Regra.** As rotas do §4 DEVEM exigir `Idempotency-Key` e aplicar escopo, hash da intenção, arbitragem pelo índice único, repetição com `Idempotent-Replayed: true` e retenção do §4.
**Aceite.** CT-API-009 — Dado `admin.alfa`, Quando envia 2 vezes o mesmo convite com a chave K1, Então recebe 201 e 201 com `Idempotent-Replayed: true`, e existem 1 membership e 1 job de e-mail; Quando K1 vem com outro e-mail, Então 409 `IDEMPOTENCY_CONFLICT`; Quando 2 requisições idênticas com K2 chegam em paralelo, Então 1 membership; sem a chave, Então 400 `IDEMPOTENCY_KEY_REQUIRED`; Quando o expurgo roda 25 h depois, Então K1 cria convite novo; Dado um comando criado com a chave K3 há 30 dias, Quando K3 é reenviada com o mesmo corpo, Então 202 com `Idempotent-Replayed: true` e o mesmo `id`.

### REQ-API-010 — ETag e If-Match
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** —
**Regra.** Os recursos do §5 DEVEM devolver `ETag` e exigir `If-Match` em PATCH e PUT (428 sem, 412 diferente).
**Aceite.** CT-API-010 — Dado A1 com `ETag: "u1760972400123456"`, Quando `agente.alfa` faz `PATCH /api/v1/tenants/{A1}` sem `If-Match`, Então 428 `PRECONDITION_REQUIRED`; com `If-Match: "u1760972400000000"`, Então 412 com o `ETag` atual; com o `ETag` atual, Então 200 e um `ETag` novo diferente do anterior.

### REQ-API-011 — Lista de veículos com estados honestos
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-03, INV-04, INV-07
**Regra.** `GET /api/v1/vehicles` e `GET /api/v1/vehicles/{id}` DEVEM devolver o item do §9.1: `state` com o schema do SSE `vehicle.state`, desconhecido como `null`/`"unknown"`, `stateAge` contra `serverTime`, `presenceThresholds` e `availableActions` com motivo.
**Aceite.** CT-API-011 — Dado V1 com `device_state.ignition` NULL, último fix às 15:19:58Z e `serverTime` 15:20:04Z, Então o item tem `"ignition": null` e `"fixAgeS": 6`; Dado um rastreador que nunca teve fix, Então `"position": null`, `"motion": "unknown"` e `"fixAgeS": null`; Dado vínculo com `cut_point` NULL, Então `availableActions.block.reason = "CUT_POINT_MISSING"`; Dado 300 veículos na Alfa, Então o p95 da primeira página com `limit=200` fica ≤ 300 ms.

### REQ-API-012 — Histórico síncrono limitado
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-02, INV-03, INV-06, INV-07
**Regra.** O histórico DEVE seguir o §9.4: máximo de 7 dias por chamada, só dentro dos 90 dias quentes, vínculos primários históricos, ordem por `fixTime`, lacunas explícitas e nada interpolado.
**Aceite.** CT-API-012 — Dado V1 com 2.880 posições em 20/10/2026, Quando `dono.a1` pede `from=2026-10-20T03:00:00Z&to=2026-10-21T03:00:00Z`, Então recebe 1.000 itens em ordem e `nextCursor`, com p95 ≤ 500 ms; com `to − from` = 604.801 s, Então 422 `HISTORY_RANGE_TOO_LARGE`; com `from` 91 dias atrás, Então 422 `HISTORY_REQUIRES_EXPORT`; Dado R1 transferido de V1 para V2 em 2026-10-20T12:00Z, Quando pede o dia de V1, Então só aparecem posições com `fixTime` < 12:00Z.

### REQ-API-013 — Exportação assíncrona de histórico
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-07
**Regra.** `POST /api/v1/exports` DEVE aceitar até 92 dias dentro dos 12 meses retidos, responder 202, gerar CSV com SHA-256 e servir o download por 7 dias revalidando a permissão.
**Aceite.** CT-API-013 — Dado `dono.a1` em 15/10/2026, Quando exporta V1 de 2026-06-01T03:00Z a 2026-07-01T03:00Z, Então 202 com `id`, e `GET /api/v1/exports/{id}` mostra `ready` com `sha256` em ≤ 5 min; Quando `dono.a2` chama o download, Então 404; Quando o download é pedido 8 dias depois, Então 404; com 93 dias, Então 422.

### REQ-API-014 — Criação de comando com resposta 202
**Fase:** F1 · **Prioridade:** P0 · **Risco:** N0 · **Invariantes:** INV-08, INV-09, INV-10
**Regra.** `POST /api/v1/vehicles/{id}/commands` DEVE responder 202 só após o commit, com `Location`, `ETag` e estado `READY` ou `ARMED`; recusa síncrona DEVE responder com o `code` do §3 sem criar linha em `command`. O app NÃO DEVE enfileirar comando offline.
**Aceite.** CT-API-014 — Dado V1 com perfil homologado, `cut_point = "fuel_pump"`, fix válido de 9 s a 23,5 km/h e step-up válido, Quando o comando é enviado, Então 202 com `Location: /api/v1/commands/{id}`, `ETag: "2"`, `state = "READY"` e `command_event` de `REQUESTED` para `READY`; Dado V3 com `cut_point` NULL, Então 422 `CUT_POINT_MISSING`, 0 linhas novas em `command` e 1 `audit_log` `denied`; Dado perfil `draft` fora da operadora de bancada, Então 422 `PROFILE_NOT_HOMOLOGATED`; Dado `block` ARMED em V1, Quando chega outro `block`, Então 409 `COMMAND_ALREADY_ACTIVE` com `activeCommandId`.

### REQ-API-015 — Contratos internos validados pelas capturas reais
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-01
**Regra.** Os schemas de `packages/contracts/src/internal/traccar.ts` DEVEM aceitar todas as capturas reais do J16 em `packages/testkit` e recusar envelopes fora do contrato de [05 §3](05-ingestao-e-telemetria.md).
**Aceite.** CT-API-015 — Dado as capturas `packages/testkit/fixtures/j16/*.json` da T-002, Quando o teste de contrato roda, Então 100% são aceitas por `TraccarPositionEnvelope` ou `TraccarEventEnvelope`; Dado uma captura sem `position.deviceId`, Quando enviada a `/internal/v1/traccar/positions`, Então 400 `INGEST_INVALID_ENVELOPE`.

### REQ-API-016 — Versão mínima do app
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** —
**Regra.** Requisição com `X-App-Version` abaixo de `MIN_APP_VERSION` DEVE receber 426 `CLIENT_UPGRADE_REQUIRED`; sem o header, segue normal.
**Aceite.** CT-API-016 — Dado `MIN_APP_VERSION=1.2.0`, Quando o app envia `X-App-Version: 1.1.9`, Então 426 com `minVersion = "1.2.0"`; com `1.2.0`, Então 200; Quando o console chama sem o header, Então 200.

### REQ-API-017 — Depreciação com prazo
**Fase:** F1 · **Prioridade:** P2 · **Risco:** N1 · **Invariantes:** —
**Regra.** Rota depreciada DEVE enviar `Deprecation` e `Sunset` com ≥ 90 dias e NÃO DEVE ser removida antes do `Sunset`.
**Aceite.** CT-API-017 — Dado a rota `vehicles.legacy-list` depreciada com sunset em 30/06/2027, Quando chamada, Então a resposta tem `Sunset: Wed, 30 Jun 2027 00:00:00 GMT` e `Deprecation`; Dado um PR em 01/05/2027 que a remove, Então o CI falha citando o sunset.

### REQ-API-018 — Teste de autenticação e isolamento por rota
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N0 · **Invariantes:** INV-07
**Regra.** A suíte `apps/api/test/scope.e2e.test.ts` DEVE ser gerada do registro: toda rota `auth: 'session'` sem credencial → 401; toda rota com id no caminho, chamada pela Alfa com recurso da Beta → 404; toda coleção da Alfa sem itens da Beta. Rota nova sem fixture de isolamento DEVE falhar a suíte ([ADR-004](../adr/ADR-004-isolamento-tres-niveis.md) item 10).
**Aceite.** CT-API-018 — Dado o registro com `vehicles.get`, Quando a suíte roda, Então executa os casos `vehicles.get:401` e `vehicles.get:cross-operator-404`, ambos verdes; Dado a rota nova `sim-cards.get` sem entrada em `scope-fixtures.ts`, Então a suíte falha com `rota sem fixture de isolamento: sim-cards.get`.

### REQ-API-019 — Limites de corpo e de tempo
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** —
**Regra.** O `api` DEVE recusar corpo acima de 1 MiB (10 MiB só na importação), aplicar `statement_timeout` de 5 s e responder 503 `DEPENDENCY_UNAVAILABLE` com `Retry-After: 5` em indisponibilidade ou estouro de prazo.
**Aceite.** CT-API-019 — Dado `agente.alfa`, Quando `POST /api/v1/tenants` com 1.048.577 bytes, Então 413 `PAYLOAD_TOO_LARGE` com `maxBytes = 1048576`; Dado uma consulta de teste com `pg_sleep(6)`, Então 503 com `Retry-After: 5`; Dado o contêiner `db` parado, Então `GET /api/v1/vehicles` responde 503 em ≤ 2 s.
