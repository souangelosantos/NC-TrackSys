# T-004 — Contratos iniciais (Zod → OpenAPI 3.1 → clientes TS e Dart) e esqueleto de `api` e `worker`

| Campo | Valor |
|---|---|
| Fase | F0 (semana S1: 07–13/10/2026) |
| Requisitos | REQ-API-001, REQ-API-002, REQ-API-003, REQ-API-004, REQ-API-005, REQ-API-007, REQ-API-019 (corpo e mídia), REQ-ARQ-001, REQ-ARQ-002 (404 no listener público), REQ-ARQ-005, REQ-ARQ-006, REQ-ARQ-007, REQ-ARQ-014, REQ-SEG-021, REQ-SEG-025 |
| Invariantes | INV-03 (enum aberto, `null` explícito), INV-12 (unidades e RFC 3339 verificados no OpenAPI) |
| Risco de revisão | **N1** — revisão cruzada obrigatória. A migration `pgboss` fica fora do schema `app`, mas o fundador a lê linha a linha |
| Depende de | T-001 |
| Estimativa | 3 sessões de agente (1: contratos e CI; 2: `api`; 3: `worker`, pg-boss, Kysely e Compose) |
| Bloqueado por decisão | nenhuma |

## Objetivo

Entregar a fundação de código que as tarefas do S2 usam: o pacote `@tracksys/contracts`, com o pipeline Zod 4 → OpenAPI 3.1 → cliente TypeScript → cliente Dart, o lint de convenções e o `oasdiff` no CI; os esqueletos NestJS 11 (Fastify) de `apps/api` (listeners 3000 e 3001) e `apps/worker` (health na 3002), com configuração validada por Zod no boot, logs JSON com correlação, Problem Details, validação de entrada e de saída pelo registro de rotas, health e readiness; Kysely com tipos gerados e pg-boss com schema próprio; e os serviços `api` e `worker` no `docker-compose.yml` local. Ao fim, T-005 e T-006 só acrescentam módulos.

## Contexto obrigatório

- [09 — API e contratos](../docs/spec/09-api-e-contratos.md) §1 (pipeline e registro), §2 (convenções), §3 (Problem Details e catálogo), §10 (evolução), REQ-API-001 a 005, 007 e 019.
- [03 — Arquitetura](../docs/spec/03-arquitetura.md) §3, §11 (limites), §12 (monorepo e matriz de dependência), §13 (variáveis), REQ-ARQ-001, 002, 005, 006, 007 e 014.
- [08 — Identidade e segurança](../docs/spec/08-identidade-e-seguranca.md) §8 item 8 (redação de log) e §9 (CORS e headers).
- [ADR-001](../docs/adr/ADR-001-monolito-modular-nestjs.md) (duas aplicações Nest no `api`; contexto standalone no `worker`) e [ADR-008](../docs/adr/ADR-008-contrato-primeiro-zod-openapi-sse.md).
- Cartão [T-001](T-001-fundacao-monorepo-e-isolamento.md): `withContext`, `.env.example`, `docker-compose.yml`, CI e `tests/vitest.config.ts` existentes.

## Escopo — fazer

1. `packages/contracts`: primitivos, Problem Details, catálogo de `code`, paginação, nomes de permissões e papéis, `RouteDef`, registro com `health.live` e `health.ready`, scripts `build`, `lint:openapi`, `gen:ts`, `gen:dart`, `check` e `breaking` (seção 1).
2. `apps/api`: duas aplicações Nest no mesmo processo (pública 3000, interna 3001), `@Route('<operationId>')`, checagem do registro no boot, pipeline de validação, filtro de Problem Details, CORS, headers, limite de corpo, logger, health (seção 2).
3. `apps/worker`: contexto standalone, servidor de health na 3002, pg-boss com consumidor `arq.probe` (seção 3).
4. `packages/db`: Kysely (`withDb`), `createPool`, tipos gerados por `kysely-codegen`, migration do schema `pgboss` (seção 4).
5. Esqueletos de `packages/domain` e `packages/testkit` com as regras de dependência de 03 §12 aplicadas por Biome e por teste (seção 5).
6. `infra/app/Dockerfile` (imagem única para os dois processos) e serviços `api`/`worker` no `docker-compose.yml` sob o profile `app` (seção 6).
7. CI: job de contratos (regeneração + `git diff`) e de `oasdiff` contra `main` (seção 6).
8. Testes de aceite em `tests/acceptance/T-004/` e verificação verde.

## Fora do escopo

- Better Auth, sessão, membership, contexto RLS por requisição, `SET LOCAL statement_timeout`, idempotência, ETag e mapeamento de SQLSTATE (T-006).
- Rotas `/internal/v1`, header secreto, outbox, relay e checagem de LISTEN no readiness (T-005). Aqui o listener 3001 só tem health.
- Schemas de recursos (veículo, cliente, rastreador, estado, SSE, eventos `*.v1`): cada tarefa cria os seus junto com a rota.
- `infra/docker-compose.yml` de produção, Caddy, alvo `migrate` e deploy (T-003, T-013). SDK do Sentry no `api` e no `worker` (T-013) e no console (T-007). Swagger UI.
- `build_runner` do cliente Dart (T-009, no app).

## Arquivos a criar/alterar

```
alterar  .env.example  .gitignore  biome.json  docker-compose.yml  package.json  tsconfig.base.json
alterar  .github/workflows/ci.yml  packages/db/package.json  packages/db/src/index.ts
criar    infra/app/Dockerfile
criar    packages/contracts/{package.json,tsconfig.json}
criar    packages/contracts/scripts/{build-openapi.ts,lint-openapi.ts,check.ts}
criar    packages/contracts/src/index.ts
criar    packages/contracts/src/common/{primitives.ts,pagination.ts,problem.ts,problem-codes.ts}
criar    packages/contracts/src/auth/{permissions.ts,roles.ts}
criar    packages/contracts/src/http/health.ts
criar    packages/contracts/src/routes/{types.ts,registry.ts}
gerar    packages/contracts/openapi/openapi.json  packages/contracts/generated/ts/schema.d.ts  packages/contracts/generated/dart/**
criar    packages/domain/{package.json,tsconfig.json,src/index.ts}  packages/testkit/{package.json,tsconfig.json,src/index.ts}
criar    packages/db/src/{kysely.ts,pool.ts}  packages/db/scripts/{gen-types.ts,pgboss-sql.ts}
gerar    packages/db/src/generated/db.ts
criar    packages/db/migrations/20261010120000_pgboss.sql
criar    apps/api/{package.json,tsconfig.json,scripts/build.ts}
criar    apps/api/src/{main.ts,bootstrap.ts,index.ts,testing.ts,public.module.ts,internal.module.ts}
criar    apps/api/src/config/env.ts
criar    apps/api/src/platform/{logger.ts,db.module.ts,queue.ts,security-headers.ts}
criar    apps/api/src/platform/http/{route.decorator.ts,registry-check.ts,route-pipeline.ts,problem.filter.ts,zod-issues.ts}
criar    apps/api/src/platform/health/{health.controller.ts,readiness.ts}
criar    apps/worker/{package.json,tsconfig.json,scripts/build.ts}
criar    apps/worker/src/{main.ts,worker.module.ts}  apps/worker/src/config/env.ts
criar    apps/worker/src/platform/{logger.ts,health-server.ts,readiness.ts,queue.ts}
criar    apps/worker/src/jobs/arq-probe.consumer.ts
criar    tests/acceptance/T-004/{support/proc.ts,support/tcp-proxy.ts,fixtures/*.json}
criar    tests/acceptance/T-004/{config,health,probe-job,http-contract,problem-catalog,openapi,logs-headers,deps}.test.ts
```

## Especificação detalhada

### (1) `@tracksys/contracts`

Depende só de `zod` (^4, o mesmo major da T-001). `exports: { ".": "./src/index.ts" }`.

- `common/primitives.ts`: `Uuid = z.uuid()` (formato `uuid`), `DateTime = z.iso.datetime({ offset: false })` (RFC 3339 com `Z`), `Limit = z.coerce.number().int().min(1).max(200).default(50)`, `Cursor = z.string().regex(/^[A-Za-z0-9_-]{1,512}$/)` (base64url de JSON; o conteúdo é validado por Zod na rota), `collection(item)` → `z.strictObject({ items: z.array(item), nextCursor: Cursor.nullable(), serverTime: DateTime })`.
- `common/problem.ts`: `Problem` com `type`, `title`, `status`, `code` (`ProblemCode`), `detail?`, `instance`, `correlationId` (uuid), `errors?: [{ path, rule, message }]` e extensões abertas (`z.looseObject`). Registrado com `.meta({ id: 'Problem' })`.
- `common/problem-codes.ts`: `PROBLEM_CODES` = mapa `code → { status, title }` com **todos** os códigos da tabela de 09 §3, exceto `INGEST_*` (a T-005 acrescenta no mesmo arquivo). Pares exatos: MALFORMED_REQUEST 400, IDEMPOTENCY_KEY_REQUIRED 400, OPERATOR_SELECTION_REQUIRED 400, AUTH_REQUIRED 401, INVALID_CREDENTIALS 401, WEBHOOK_UNAUTHORIZED 401, FORBIDDEN 403, CSRF_REJECTED 403, TWO_FACTOR_ENROLLMENT_REQUIRED 403, STEP_UP_REQUIRED 403, STEP_UP_INVALID 403, NOT_FOUND 404, INVITATION_INVALID 404, CONFLICT 409, IDEMPOTENCY_CONFLICT 409, DEVICE_ALREADY_REGISTERED 409, SIM_ALREADY_REGISTERED 409, ASSIGNMENT_OVERLAP 409, WATCH_MODE_VEHICLE_ON 409, WATCH_MODE_NO_FIX 409, TELEMETRY_STALE 409, SPEED_ABOVE_LIMIT 409, COMMAND_ALREADY_ACTIVE 409, COMMAND_IN_FLIGHT 409, COMMAND_NOT_CANCELLABLE 409, PRECONDITION_FAILED 412, PAYLOAD_TOO_LARGE 413, UNSUPPORTED_MEDIA_TYPE 415, CUT_POINT_MISSING 422, PROFILE_NOT_HOMOLOGATED 422, COMMAND_NOT_ALLOWED 422, VALIDATION_FAILED 422, HISTORY_RANGE_TOO_LARGE 422, HISTORY_REQUIRES_EXPORT 422, STREAM_SCOPE_TOO_LARGE 422, ALERT_PREFERENCE_LOCKED 422, CLIENT_UPGRADE_REQUIRED 426, PRECONDITION_REQUIRED 428, RATE_LIMITED 429, INTERNAL_ERROR 500, DEPENDENCY_UNAVAILABLE 503, COMMAND_DISPATCH_DISABLED 503 (42 códigos). `title` em PT-BR (ex.: `VALIDATION_FAILED` → "Dados inválidos"). `problemType(code, domain)` = `https://api.<domain>/problems/<code em kebab-case>`.
- `auth/permissions.ts`: `PERMISSIONS` = nomes da coluna "Permissão" de 08 §3 (F0 e F1), `type Permission`. `auth/roles.ts`: `ROLES` (6 papéis de `membership`) e `F0_ROLES = ['operator_admin', 'operator_agent', 'tenant_owner']`.
- `http/health.ts`: `HealthLive = { status: 'ok' }`; `HealthReadyPublic = { status: 'ok' | 'unavailable' }`; `HealthReadyDetailed = { status, checks: Record<string, 'ok' | 'fail'> }`.
- `routes/types.ts`:

```ts
export interface RouteDef {
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  path: string                                   // '/api/v1/vehicles/{vehicleId}'
  phase: 'F0' | 'F1' | 'F2'
  listener?: 'public' | 'internal'               // padrão 'public'; 'internal' não entra no OpenAPI
  auth: 'session' | 'public' | 'share_session' | 'webhook_asaas'
  permission?: Permission | Permission[] | null  // obrigatório (pode ser null = só sessão) quando auth = 'session'
  params?: z.ZodObject; query?: z.ZodObject; body?: z.ZodType
  responses: Partial<Record<200 | 201 | 202 | 204 | 503, z.ZodType | null>>
  idempotency: 'none' | 'optional' | 'required'; idempotencyRetention?: '24h' | 'forever'
  rateLimit: string; aiTool?: boolean; summary: string                // summary em PT-BR
}
```

- `routes/registry.ts`: `export const routes = { 'health.live': {...}, 'health.ready': {...} } as const satisfies Record<string, RouteDef>`. Os dois são `GET`, `auth: 'public'`, `idempotency: 'none'`, `rateLimit: 'none'`; `health.ready` responde 200 e 503 com `HealthReadyPublic`. **Regra:** o registro contém só rotas com handler; cada tarefa acrescenta rota, schema e handler no mesmo PR.

Scripts (`packages/contracts/package.json`):

| Script | Comando |
|---|---|
| `build` | `tsx scripts/build-openapi.ts` → `openapi/openapi.json`: `openapi: "3.1.0"`, `info.version` = versão do pacote, `servers: [{ url: "https://api.tracksys.com.br" }]`, `paths` do registro (`listener !== 'internal'`, `operationId` = chave, `{param}` mantido), `components.schemas` de `z.toJSONSchema(z.globalRegistry, { target: 'draft-2020-12', uri: id => '#/components/schemas/' + id })`; toda resposta 4xx/5xx referencia `Problem` com `application/problem+json`. JSON com chaves ordenadas e 2 espaços (saída determinística) |
| `lint:openapi` | `tsx scripts/lint-openapi.ts openapi/openapi.json` (regras abaixo) |
| `gen:ts` | `openapi-typescript openapi/openapi.json -o generated/ts/schema.d.ts` |
| `gen:dart` | `docker run --rm -u "$(id -u):$(id -g)" -v "$PWD/../..":/local openapitools/openapi-generator-cli:v7.10.0 generate -i /local/packages/contracts/openapi/openapi.json -g dart-dio -o /local/packages/contracts/generated/dart --additional-properties=pubName=tracksys_api,enumUnknownDefaultCase=true` (tag + digest fixados no PR) |
| `check` | `tsx scripts/check.ts`: `build` → `lint:openapi` → `gen:ts` → `gen:dart` → falha se `git status --porcelain -- openapi generated` não estiver vazio, listando os arquivos |
| `breaking` | `docker run --rm -v "$PWD/../..":/w tufin/oasdiff:<tag> breaking /w/.ci/openapi.main.json /w/packages/contracts/openapi/openapi.json --fail-on ERR` |

Lint de convenções (`lintOpenApi(doc): string[]`, exportado para teste; o script imprime uma linha por violação e sai com 1). Percorre toda propriedade de todo schema e parâmetro:

| Regra | Mensagem exata |
|---|---|
| Chave fora de `^[a-z][a-zA-Z0-9]*$` | `chave fora de camelCase: <chave>` |
| Chave terminada em `At` ou `Time`, tipo `string`, sem `format: date-time` | `data sem format date-time: <chave>` |
| Chave `id` ou terminada em `Id`, tipo `string`, sem `format: uuid` | `id sem format uuid: <chave>` |
| Tipo `number`/`integer` e alguma palavra camelCase da chave ∈ {speed, distance, duration, age, ttl, radius, course, altitude, value, amount, price, battery, timeout} sem terminar em `Kmh`, `M`, `S`, `Deg`, `Cents`, `Pct` ou `Bytes` | `grandeza sem unidade: <chave>` |
| Chave terminada em `Cents` com tipo diferente de `integer` | `dinheiro deve ser inteiro: <chave>` |

### (2) `apps/api` — esqueleto

- `main.ts`: `loadApiEnv()` → `createApiApps(env)` → `listen`. `ConfigError` ou `RouteRegistryError` → mensagem em stderr e `process.exit(78)`. SIGTERM fecha as duas aplicações, os pools e o pg-boss em ≤ 10 s.
- `config/env.ts` (Zod, antes de abrir conexão): `NODE_ENV` (`development`|`test`|`production`, padrão `development`), `TRACKSYS_DOMAIN` (hostname), `TRACKSYS_VERSION` (não vazio), `LOG_LEVEL` (`fatal`|`error`|`warn`|`info`|`debug`, padrão `info`), `DATABASE_URL_APP` e `DATABASE_URL_INGEST` (`postgres://`; com `production`, usuário `postgres` ou `tracksys_owner` → erro), `API_PORT`/`INTERNAL_PORT` (inteiros, padrão 3000/3001, diferentes), `INGEST_SHARED_SECRET` (≥ 32), `INGEST_SOURCE_INSTANCE` (`^traccar-[a-z0-9-]+$`), `BETTER_AUTH_SECRET` (≥ 32), `BETTER_AUTH_URL` (URL; em `production` igual a `https://api.<TRACKSYS_DOMAIN>`), `SENTRY_DSN` (URL opcional; vazio = ausente). Mensagem: `Configuração inválida: <NOME> (<regra>)` por variável; nunca o valor. Os apps nunca leem `DATABASE_URL` (papel dono, só dbmate, `db:check` e `db:types`) nem `DATABASE_URL_ADMIN` (superusuário local, só testes e semeadura).
- `bootstrap.ts`: `createApiApps(env, overrides?)` cria os pools fora do Nest (`createPool(env.DATABASE_URL_APP, { max: 20, applicationName: 'api' })`; ingest `max: 10`, sem uso aqui), o pg-boss só de envio (seção 4) e duas aplicações `NestFactory.create(…, new FastifyAdapter({ loggerInstance, bodyLimit: 1_048_576, requestTimeout: 10_000, genReqId, trustProxy: false }))`: `PublicModule` (health + módulos de requisição futuros) na `API_PORT` e `InternalModule` (só health por enquanto) na `INTERNAL_PORT`. `overrides` (usado só por `testing.ts`) aceita `routes` e `controllers` extras.
- `@Route('<operationId>')`: aplica `@Get/@Post/...` com o caminho do registro (`{x}` → `:x`) e grava o `operationId` como metadado. `registry-check.ts` usa `DiscoveryService` no boot: entrada do registro (do listener) sem handler → `contrato sem handler: <id>`; handler sem entrada → `rota sem contrato: <id>`; `aiTool: true` fora de `GET` → `aiTool só em GET: <id>`; `auth: 'session'` sem a chave `permission` → `rota sem permissão: <id>`.
- `route-pipeline.ts` (interceptor único): valida `params`, `query` e `body` com os schemas do registro (objetos estritos) → 422 `VALIDATION_FAILED` com `errors` por `zod-issues.ts`; chama o handler, que devolve `{ status, body?, headers? }`; valida `body` com `responses[status]`; violação → 500 `INTERNAL_ERROR` e 1 log `level=error`, `msg=response_contract_violation`, `route=<operationId>`. Mapa de `rule`: `unrecognized_keys` → `unrecognized_key` (1 erro por chave); `invalid_format` com regex → `pattern`; outro `invalid_format` → `format`; `too_small`/`too_big` em string → `min_length`/`max_length`, em número → `min`/`max`; `invalid_type` com valor ausente → `required`, senão `type`; `invalid_value` → `enum`; `custom` → `params.rule`. `path` = caminho unido por `.`.
- `problem.filter.ts`: `ProblemError(code, { detail?, extensions?, headers? })` vira Problem Details (`Content-Type: application/problem+json`, `instance` = caminho sem query, `correlationId` = id da requisição). Erros do Fastify: corpo > 1 MiB → 413 `PAYLOAD_TOO_LARGE` com `maxBytes: 1048576`; JSON ilegível → 400 `MALFORMED_REQUEST`; `Content-Type` fora de `application/json` e `application/merge-patch+json` em rota com corpo → 415; rota inexistente → 404 `NOT_FOUND`. Qualquer outro erro → 500 `INTERNAL_ERROR` sem mensagem original, stack ou SQL no corpo (vão só para o log).
- Correlação: `genReqId` usa `X-Request-Id` se for UUID, senão `randomUUID()`; a resposta sempre ecoa `X-Request-Id`.
- `security-headers.ts` (hook `onSend`, toda resposta dos dois listeners): `Strict-Transport-Security: max-age=31536000; includeSubDomains`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`, `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`, `Cross-Origin-Resource-Policy: same-site`. CORS (só no público): origem permitida `https://app.<TRACKSYS_DOMAIN>` (mais `http://localhost:5173` com `NODE_ENV=development`), `credentials: true`, métodos e headers permitidos/expostos e `max-age` 600 exatamente como 08 §9; origem fora da lista não recebe header CORS.
- `logger.ts`: pino em stdout, uma linha JSON com `ts` (ISO 8601 UTC), `level` (rótulo), `service` (`api`), `version` (`TRACKSYS_VERSION`), `correlationId`, `msg`. `redact` com `censor: '[REDACTED]'` nos caminhos de 08 §8 item 8: `req.headers.authorization`, `req.headers.cookie`, `req.headers["asaas-access-token"]`, `req.headers["x-ingest-token"]`, `*.password`, `*.token`, `*.apiKey`, `*.signature`, `*.nonce`, `*.secret`, `*.code`. Corpo de requisição nunca é logado. O `worker` usa o mesmo arquivo copiado com `service: 'worker'`; `deps.test.ts` compara as duas listas de `redact`.
- Health (`health.controller.ts`, `@Route('health.live')`/`@Route('health.ready')`): `live` → 200 `{"status":"ok"}` sem tocar em dependência. `readiness.ts` mantém checagens registráveis (`register(name, fn)`); aqui só `db` = `SELECT 1` no pool do app com prazo de 1 s. Listener 3000: 200 `{"status":"ok"}` ou 503 `{"status":"unavailable"}`, sem detalhes. Listener 3001: mesmo status com `checks` (ex.: `{"status":"unavailable","checks":{"db":"fail"}}`). O healthcheck do Docker usa a 3001.

### (3) `apps/worker` — esqueleto

`main.ts`: `loadWorkerEnv()` (mesmas regras: `NODE_ENV`, `TRACKSYS_DOMAIN`, `TRACKSYS_VERSION`, `LOG_LEVEL`, `DATABASE_URL_APP`, `DATABASE_URL_INGEST`, `WORKER_HEALTH_PORT` padrão 3002, `INGEST_SOURCE_INSTANCE`, `TRACCAR_API_URL` padrão `http://traccar:8082`, `TRACCAR_API_USER` e `TRACCAR_API_PASSWORD` não vazios, `SENTRY_DSN`; erro → 78) → `NestFactory.createApplicationContext(WorkerModule)` → pg-boss `start()` → `health-server.ts` (`node:http`, só `GET /health/live` e `GET /health/ready`; qualquer outra rota → 404 JSON `{"status":"not_found"}`). Readiness: `{"status":"ok","checks":{"db":"ok","pgboss":"ok"}}` ou 503 com o item `fail` (`pgboss` = `start()` concluído e sem erro). `arq-probe.consumer.ts`: `boss.work('arq.probe', …)` conclui o job e loga `msg=arq_probe_done` com `jobId`. Pool `max: 10`.

### (4) Banco: Kysely e pg-boss

- `pool.ts`: `createPool(url, { max, applicationName })` → `pg.Pool` com `application_name`. `kysely.ts`: `withDb<T>(pool, ctx, fn: (db: Kysely<DB>) => Promise<T>)` chama `withContext` da T-001 e cria um `Kysely<DB>` sobre um "pool de uma conexão" que devolve sempre o `PoolClient` da transação (`release` vazio). Nunca abre conexão fora de `withContext`. Exporte `withDb`, `createPool`, `type DB`.
- `scripts/gen-types.ts` (scripts raiz `db:types` e `db:types:check`): `loadDbEnv()` e `kysely-codegen --dialect postgres --url <DATABASE_URL> --include-pattern "(app|auth).*" --exclude-pattern "(app.position_p*|app.access_log_p*)" --out-file packages/db/src/generated/db.ts`; o `check` falha se `git status --porcelain` do arquivo não estiver vazio.
- pg-boss (major 10): `migrate: false` sempre; o schema nasce por migration de `tracksys_owner`, o app nunca recebe `CREATE`. `api`: `new PgBoss({ connectionString: DATABASE_URL_APP, schema: 'pgboss', migrate: false, supervise: false, schedule: false, max: 2 })`, só `send`. `worker`: mesmo com `supervise: true`, `max: 10`.
- `scripts/pgboss-sql.ts` imprime `PgBoss.getConstructionPlans('pgboss')` da versão fixada; a saída é colada na migration abaixo (troca de versão do pg-boss = migration nova).

```sql
-- packages/db/migrations/20261010120000_pgboss.sql
-- migrate:up
-- T-004 — Fila pg-boss (ADR-002). Schema fora de `app`: sem RLS, sem dados de cliente (job leva só ids, REQ-ARQ-010).
SET LOCAL lock_timeout = '5s'; SET LOCAL statement_timeout = '60s';
-- <cole aqui a saída de: tsx packages/db/scripts/pgboss-sql.ts, sem BEGIN/COMMIT próprios (o dbmate já abre a transação)>
GRANT USAGE ON SCHEMA pgboss TO tracksys_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA pgboss TO tracksys_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA pgboss TO tracksys_app;
ALTER DEFAULT PRIVILEGES FOR ROLE tracksys_owner IN SCHEMA pgboss
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO tracksys_app;
SELECT pgboss.create_queue('arq.probe', '{"policy":"standard","retryLimit":0}'::json);
-- migrate:down
DROP SCHEMA pgboss CASCADE;
```

Filas novas entram por migration (`SELECT pgboss.create_queue(...)`) na tarefa que as usa. [VALIDAR — T-004: nome e assinatura de `getConstructionPlans`/`create_queue` na versão fixada; se a versão exigir DDL em runtime pelo papel do app, pare e registre no PR — não conceda `CREATE` a `tracksys_app`.]

### (5) `packages/domain`, `packages/testkit` e regras de dependência

- `@tracksys/domain`: dependências só `@tracksys/contracts` e `zod`; `src/index.ts` vazio exportando `{}`. `@tracksys/testkit`: `private`, só usado como `devDependency`.
- `biome.json`: `javascript.parser.unsafeParameterDecoratorsEnabled: true`; `overrides` para `packages/domain/**` com `correctness.noNodejsModules: "error"` e `style.noRestrictedImports` barrando `pg`, `kysely`, `pg-boss` e `@nestjs/*` [VALIDAR — T-004: nomes das opções no Biome 2 fixado].
- `tsconfig.base.json`: acrescente `"experimentalDecorators": true`. Nest usa `@Inject(TOKEN)` explícito em todo parâmetro de construtor; `emitDecoratorMetadata` não é usado.
- `deps.test.ts` lê todos os `package.json` e aplica a matriz de 03 §12 (contracts → só `zod`; domain → só contracts e `zod`; db → sem `apps/*` e `@nestjs/*`; api e worker → não importam um ao outro nem `@tracksys/console`; testkit só como devDependency).

### (6) Build, Compose e CI

- `apps/*/scripts/build.ts`: esbuild (bundle ESM, `platform: 'node'`, `target: 'node22'`, sourcemap) de `src/main.ts` para `dist/main.js`; `@tracksys/*` entram no bundle; todo outro import bare fica externo e **precisa** estar nas `dependencies` do app (o plugin falha o build citando o pacote).
- `infra/app/Dockerfile`: `node:24-bookworm-slim`, multi-estágio, `pnpm install --frozen-lockfile`, `pnpm --filter @tracksys/api --filter @tracksys/worker build`, `pnpm deploy --prod` de cada app; estágio final nomeado `app` (a T-013 acrescenta o alvo `migrate` no mesmo arquivo); imagem final roda como usuário `node`; `amd64` e `arm64`.
- `docker-compose.yml`: serviços `api` e `worker` com `profiles: ["app"]` (o `pnpm db:up` da T-001 continua subindo só o `db`), mesma imagem `tracksys-app:${TRACKSYS_VERSION:-dev}`, `env_file: .env` com `DATABASE_URL_*` apontando para `db:5432`, `depends_on: db (service_healthy)`, `mem_limit: 1g` nos dois, `cpus: 1.5` (`api`) e `1.0` (`worker`), `NODE_OPTIONS=--max-old-space-size=768` / `512`, healthcheck `node -e` em `http://127.0.0.1:3001/health/ready` (`api`) e `:3002` (`worker`) a cada 10 s com 3 falhas; só `127.0.0.1:3000:3000` publicado.
- `.env.example`: mantém as variáveis da T-001 e acrescenta, com valores só de desenvolvimento, todas as variáveis das seções 2 e 3 (ex.: `INGEST_SHARED_SECRET=dev-ingest-secret-com-pelo-menos-32-chars`, `BETTER_AUTH_URL=http://localhost:3000`, `TRACKSYS_DOMAIN=tracksys.com.br`, `TRACKSYS_VERSION=dev`). `.gitignore`: `.ci/` e `.tmp/`.
- `package.json` raiz: scripts `build` (`pnpm -r run build`), `contracts:check` (`pnpm --filter @tracksys/contracts check`), `contracts:breaking`, `db:types`, `db:types:check`; `verify` = `pnpm lint && pnpm typecheck && pnpm contracts:check && pnpm build && pnpm db:migrate && pnpm db:rollback && pnpm db:migrate && pnpm db:check && pnpm db:types:check && pnpm test:acceptance` (mantém a prova do `down` da T-001). devDependencies novas: `@tracksys/api`, `@tracksys/contracts`, `@tracksys/testkit` (`workspace:*`), `pg-boss`, `kysely-codegen`, `esbuild`.
- CI: o job `verify` passa a rodar o `pnpm verify` acima (Docker já disponível). Job novo `contracts-breaking` em PR sem o rótulo `api-breaking`: `git show origin/${{ github.base_ref }}:packages/contracts/openapi/openapi.json > .ci/openapi.main.json` (se não existir em `main`, o job termina verde com aviso) e `pnpm contracts:breaking`.

Versões: majors canônicos (NestJS 11, Fastify 5, Zod 4, pg-boss 10, Biome 2); demais pacotes (`kysely`, `kysely-codegen`, `pino`, `openapi-typescript`, `esbuild`) na última versão estável com ≥ 2 semanas, fixadas no lockfile e listadas no PR.

## Testes de aceite (congelados)

Em `tests/acceptance/T-004/`. Processos sobem por `support/proc.ts` a partir de `apps/*/dist/main.js` com portas livres; `support/tcp-proxy.ts` fica entre os processos e o Postgres para simular queda do banco. Testes longos declaram `{ timeout: 60_000 }`.

| Arquivo | Dado / Quando / Então |
|---|---|
| `config.test.ts` (CT-ARQ-006) | Dado o ambiente válido sem `DATABASE_URL_APP`, Quando `node apps/api/dist/main.js`, Então sai com 78 em ≤ 2.000 ms e o stderr contém `DATABASE_URL_APP`. Dado `INGEST_SHARED_SECRET=CANARIO-12345678` (16 caracteres), Então 78 e o stderr não contém `CANARIO-12345678`. Dado `NODE_ENV=production` e `DATABASE_URL_APP=postgres://tracksys_owner:x@127.0.0.1:54329/tracksys`, Então 78. Dado `API_PORT=3000` e `INTERNAL_PORT=3000`, Então 78 citando `INTERNAL_PORT`. Dado o `worker` sem `TRACCAR_API_USER`, Então 78 citando `TRACCAR_API_USER` |
| `health.test.ts` (CT-ARQ-005, CT-ARQ-002 parte) | Dado `api` e `worker` no ar via proxy, Quando 5 chamadas a `GET /health/live`, Então todas 200 `{"status":"ok"}` em ≤ 50 ms; `GET :API_PORT/health/ready` → 200 com corpo exatamente `{"status":"ok"}`; `:INTERNAL_PORT` → `{"status":"ok","checks":{"db":"ok"}}`; `worker` → `{"status":"ok","checks":{"db":"ok","pgboss":"ok"}}`. Quando o proxy fecha, Então em ≤ 5 s: 3001 → 503 com `checks.db = "fail"`, 3000 → 503 `{"status":"unavailable"}`, `worker` → 503 com `checks.db = "fail"`, e `/health/live` continua 200. Quando o proxy reabre, Então os três voltam a 200 em ≤ 15 s. Quando `POST :API_PORT/internal/v1/traccar/positions`, Então 404 `application/problem+json` com `code = "NOT_FOUND"`. Quando `GET :WORKER/qualquer`, Então 404 |
| `probe-job.test.ts` (CT-ARQ-001) | Dado o `api` no ar e o `worker` parado, Quando um job `arq.probe` é enviado com pg-boss (`DATABASE_URL_APP`), Então após 30 s o job está `created`; Quando o `worker` sobe, Então o job fica `completed` em ≤ 10 s e o stdout do `worker` tem 1 linha `arq_probe_done` com o `jobId` |
| `http-contract.test.ts` (CT-API-001, CT-API-004, CT-API-007, CT-API-019 parte) | Com `createApiApps(env, { routes, controllers })` de `@tracksys/api/testing` e o registro de fixture `vehicles.create` (`POST /api/v1/vehicles`, corpo estrito `{tenantId: uuid, kind: 'car'\|'motorcycle'\|'truck'\|'other', plate?: /^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$/}`) e `vehicles.get` (resposta `{ignition: boolean\|null}`): Dado handler `@Route('vehicles.archive')` sem entrada, Então lança `RouteRegistryError` com `rota sem contrato: vehicles.archive`; Dado `vehicles.archive` no registro sem handler, Então `contrato sem handler: vehicles.archive`. Quando `POST` com `{"tenantId":"0192a1b2-0000-7000-8000-0000000000a1","kind":"car","plate":"abc-1234"}`, Então 422 `VALIDATION_FAILED` com `errors[0]` contendo `path: "plate"` e `rule: "pattern"`; com `"cor2":"x"` a mais, Então 422 com `rule = "unrecognized_key"`. Dado o handler de `vehicles.get` devolvendo `"ignition":"false"`, Então 500 `INTERNAL_ERROR` e 1 log `response_contract_violation` com `route = "vehicles.get"`. Dado um handler que lança `Error('SELECT * FROM app.vehicle falhou')` e `X-Request-Id: 0192a1b2-7f00-7000-8000-00000000aa01`, Então 500 `application/problem+json`, `correlationId` igual ao header e corpo sem `SELECT` nem `\n    at `. Com `X-Request-Id: abc`, Então a resposta traz `X-Request-Id` UUID diferente de `abc`. Corpo de 1.048.577 bytes → 413 `PAYLOAD_TOO_LARGE` com `maxBytes = 1048576`; corpo `{` → 400 `MALFORMED_REQUEST`; `Content-Type: text/plain` → 415 |
| `problem-catalog.test.ts` (CT-API-007 catálogo) | Dado `PROBLEM_CODES`, Então é igual à tabela de 42 pares `code → status` copiada no teste; os 42 `problemType(code, 'tracksys.com.br')` são distintos e `VALIDATION_FAILED` → `https://api.tracksys.com.br/problems/validation-failed` |
| `openapi.test.ts` (CT-API-002, CT-API-003, CT-API-005) | Quando `pnpm --filter @tracksys/contracts build` roda, Então `openapi.json` tem `openapi = "3.1.0"`, `paths["/health/live"]`, `paths["/health/ready"]` e `components.schemas.Problem`, e `git status --porcelain -- packages/contracts/openapi packages/contracts/generated/ts` fica vazio após `gen:ts`. Dado `fixtures/lint-bad.json` com `speed_kmh`, `speed: number` e `valueCents: number`, Então `lintOpenApi` devolve `chave fora de camelCase: speed_kmh`, `grandeza sem unidade: speed` e `dinheiro deve ser inteiro: valueCents`; com `contactAgeS` inteiro e `pageSize`, Então nenhuma violação. Dado `fixtures/oas-base.json` e `fixtures/oas-sem-plate.json`, Quando `oasdiff breaking --fail-on ERR` roda, Então sai ≠ 0 citando `plate`; com `fixtures/oas-vinlast4.json` (campo opcional novo), Então sai 0 |
| `logs-headers.test.ts` (CT-ARQ-014 parte, CT-SEG-021 parte, CT-SEG-025) | Dado `TRACKSYS_VERSION=t004`, `INGEST_SHARED_SECRET=CANARIO-<32 aleatórios>` e requisições com `Authorization: Bearer CANARIO-b1` e `Cookie: s=CANARIO-c1`, Então toda linha do stdout do `api` é JSON com `ts`, `level`, `service = "api"`, `version = "t004"`, `msg`, as linhas de requisição têm `correlationId`, e nenhuma contém `CANARIO-`. `OPTIONS /health/live` com `Origin: https://evil.example` → sem `Access-Control-Allow-Origin`; com `Origin: https://app.tracksys.com.br` → exatamente esse valor e `Access-Control-Allow-Credentials: true`. `GET /health/live` → `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`, `Strict-Transport-Security: max-age=31536000; includeSubDomains`, `Referrer-Policy: no-referrer` |
| `deps.test.ts` (CT-ARQ-007) | Dado `packages/domain/src/__probe__.ts` com `import { readFile } from 'node:fs/promises'`, Quando `pnpm exec biome lint` no arquivo, Então falha citando `noNodejsModules`; Dado `apps/worker/src/__probe__.ts` com `import '@tracksys/api'`, Quando `pnpm --filter @tracksys/worker typecheck`, Então falha com `TS2307`; os arquivos são removidos no `finally`. A matriz de 03 §12 sobre os `package.json` passa, e as listas `redact` do `api` e do `worker` são iguais |

## Comandos de verificação

```bash
pnpm install
cp .env.example .env
pnpm db:up
pnpm db:migrate                                   # Applied: 20261010120000_pgboss.sql
pnpm contracts:check                              # build + lint + gen:ts + gen:dart + diff vazio
pnpm db:types:check
pnpm build
pnpm verify                                       # inclui os testes da T-001 e da T-004
pnpm exec dbmate --migrations-dir ./packages/db/migrations --no-dump-schema rollback && pnpm db:migrate
docker compose --profile app up -d --build --wait api worker
curl -fsS http://127.0.0.1:3000/health/ready      # {"status":"ok"}
docker compose --profile app down
```

## Definição de pronto

- Todos os comandos acima verdes, local e no CI; `acceptance-freeze` verde (T-001 intacta).
- `openapi.json`, `generated/ts` e `generated/dart` versionados e iguais à regeneração.
- Versões fixadas, tag e digest das imagens `openapi-generator-cli` e `oasdiff` listados no PR.
- Revisão cruzada registrada; o PR lista REQ/CT acima, risco N1 e a migration `pgboss` destacada para leitura linha a linha.

## Decisões já tomadas

| Dúvida provável | Resposta |
|---|---|
| Zod → OpenAPI com qual biblioteca? | `z.toJSONSchema` nativo do Zod 4 (`draft-2020-12`, compatível com OpenAPI 3.1). `zod-openapi` só se faltar recurso concreto; registre o caso no PR (resolve o [VALIDAR — T-004] de 09 §1). |
| Registrar já todas as rotas do F0? | Não. O boot falha com contrato sem handler (REQ-API-001). Cada tarefa adiciona rota + schema + handler + cliente regenerado no mesmo PR. |
| Kysely e pg-boss não são da T-005/T-006? | Entram aqui: T-005 e T-006 dependem só da T-004 e rodam em paralelo no S2; os dois precisam da mesma base (T-001 já previa Kysely na T-004; 04 §10 item 8). |
| Por que o readiness público não mostra `checks`? | 03 REQ-ARQ-005 exige corpo só com `status` em `https://api.<domínio>`. O detalhe fica na 3001 e na 3002 (rede Docker), que o healthcheck usa e que o CT-ARQ-005 mede. |
| Por que esbuild e não `tsc`/SWC para build? | TypeScript 7 só faz typecheck (`noEmit` da T-001). esbuild aceita decorators legados; sem `emitDecoratorMetadata`, toda injeção usa `@Inject(TOKEN)`. |
| Nomes das variáveis de banco? | Os canônicos da T-001: `DATABASE_URL` (`tracksys_owner`: dbmate, `db:check`, `db:types`), `DATABASE_URL_APP` (`tracksys_app`: `api`, `worker` e testes), `DATABASE_URL_INGEST` (`tracksys_ingest`) e `DATABASE_URL_ADMIN` (superusuário local, só testes e semeadura, nunca em `apps/`). `APP_DATABASE_URL`, `ADMIN_DATABASE_URL` e `INGEST_DATABASE_URL` não existem. |
| Gerador Dart com quais opções? | Exatamente `pubName=tracksys_api,enumUnknownDefaultCase=true` (09 §1). `build_runner` roda no app (T-009); `generated/dart` guarda só a saída do gerador. |
| `nestjs-pino`? | Não. pino direto como `loggerInstance` do Fastify e um `LoggerService` fino para o Nest. |
| Compose de produção? | Fora daqui (`infra/docker-compose.yml`, T-003/T-013). O serviço local espelha imagem, limites e healthcheck para a VM copiar. |
| CORS e headers já aqui, sem sessão? | Sim: não dependem de sessão (REQ-SEG-025). `Cache-Control: no-store` vai em toda resposta, um superconjunto da regra "toda resposta autenticada". |
| O rótulo `api-breaking` vale de quem aplicou? | Só do fundador: o status obrigatório `label-guard` (T-019) fica vermelho se o `labeled` mais recente for de outra conta. O job chama-se `contracts-breaking` também na 14 §11. |
| Commit | Conventional Commits, ex.: `feat(contracts): pipeline openapi (T-004)`, `feat(api): esqueleto nest (T-004)`. |
