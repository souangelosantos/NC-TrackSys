# T-006 — Autenticação (Better Auth) e contexto RLS por requisição

| Campo | Valor |
|---|---|
| Fase | F0 (semana S2: 14–20/10/2026) |
| Requisitos | REQ-SEG-001, REQ-SEG-002, REQ-SEG-003, REQ-SEG-004, REQ-SEG-005, REQ-SEG-006, REQ-SEG-007 (HTTP), REQ-SEG-008, REQ-SEG-009, REQ-SEG-010, REQ-SEG-023, REQ-SEG-026, REQ-API-008, REQ-API-009, REQ-API-018, REQ-ARQ-008, REQ-ARQ-010 (job de e-mail), REQ-DAD-001 e REQ-DAD-003 (`membership`), REQ-DAD-006 (`memberships_for_user`), REQ-DAD-009 (partições de `access_log`; as de `position` são da T-005), REQ-QLD-011 |
| Invariantes | INV-07 (isolamento), INV-11 (nenhum papel tem comando implícito), INV-12 |
| Regras de catálogo | CAT-01 a CAT-07 (a regra CAT-07 é da T-004; esta tarefa só acrescenta entrada em `securityDefiner`); ISO-01 a ISO-05 para `membership`, `audit_log` e `idempotency_record` |
| Risco de revisão | **N0** — modo de planejamento antes de editar; revisão adversarial por agente de outro fornecedor; leitura humana linha a linha |
| Depende de | T-001, T-004 (registro, pipeline, `withDb`, pg-boss, CAT-07, `app.tg_immutable_columns()` e as políticas `operator_definer_read`/`tenant_definer_read`) |
| Estimativa | 3 sessões de agente, uma por fatia (ver "Fatias") |
| Bloqueado por decisão | nenhuma (provedor de e-mail: Resend [PREMISSA], troca sem efeito no contrato) |

## Objetivo

Fazer cada requisição autenticada virar, no banco, exatamente o contexto RLS a que o usuário tem direito. Entregar o Better Auth embutido (e-mail + senha, TOTP para `operator_admin`, sessões de console por cookie de 12 h e de app por bearer de 30 dias), as tabelas `membership`, `audit_log`, `access_log` e `idempotency_record`, a função definidora `app.memberships_for_user`, o pipeline que resolve sessão → membership → contexto → permissão → `withDb`, a matriz de permissões do F0, convite e redefinição de senha com e-mail pelo `worker`, limites de taxa e o CLI que cria a primeira operadora. Sem esta tarefa, nenhuma rota de dados existe.

## Contexto obrigatório

- [08 §2](../docs/spec/08-identidade-e-seguranca.md#2-autenticação-better-auth) (Better Auth, sessões, CSRF, TOTP, revogação), §3 (matriz), §4 (do request ao banco), §8 item 8, §9 (limites), §11 (`access_log`, `audit_log`), REQ-SEG-001 a 010, 023 e 026.
- [04 §1](../docs/spec/04-dominio-e-dados.md#1-hierarquia-e-convenções) (contexto derivado), §3.2, §3.4 e §3.7 (DDL), §4.1 a §4.4 (RLS, papéis, funções definidoras), §5.1 (CAT e allowlist).
- [09 §3](../docs/spec/09-api-e-contratos.md#3-erros-problem-details) (catálogo e mapeamento de erros do banco), §4 (idempotência), §6 (rotas de auth, `me`, convites, memberships), REQ-API-008, 009 e 018.
- [ADR-006](../docs/adr/ADR-006-identidade-better-auth-chave-aparelho.md). [03](../docs/spec/03-arquitetura.md) REQ-ARQ-008 e 010.
- Cartões [T-001](T-001-fundacao-monorepo-e-isolamento.md) (`withContext`, verificador de catálogo) e [T-004](T-004-contratos-e-esqueleto-api-worker.md) (registro, pipeline, `withDb`, pg-boss, logger).

## Escopo — fazer

1. Migration `20261014130000_identidade.sql` com o SQL exato da seção 1 e as entradas de allowlist da seção 2 (a regra CAT-07 é da T-004).
2. `withContext(pool, ctx, fn, opts?)` com `opts = { readOnly?: boolean; statementTimeoutMs?: number }` e `ctx` ganhando `userId?: string` (UUID):
   - sem `opts` e sem `userId`, o comportamento é idêntico ao da T-001 (os testes congelados da T-001 continuam verdes);
   - `userId` presente grava `app.user_id` com `set_config(..., true)`; ausente, a variável fica sem valor e `app.current_user_id()` devolve NULL;
   - `ctx` continua validado por `z.strictObject` (agora com `userId` opcional) e `opts` é argumento separado, validado por outro `z.strictObject` (chave extra = erro);
   - `withDb` repassa `opts`; `SET TRANSACTION READ ONLY` e `SET LOCAL statement_timeout` vêm logo após o `BEGIN`;
   - o `RESET ALL` depois do COMMIT/ROLLBACK e o descarte da conexão quando ele falha (`release(err)`, T-001) continuam valendo.
3. Better Auth em `apps/api/src/identity/auth.ts` e um handler `@Route` por caminho da allowlist (seção 3). O handler HTTP genérico do Better Auth **não** é montado.
4. Pipeline de rota (seção 4), matriz de permissões e `resolveRequestContext` puros em `packages/domain/src/auth/` (seção 5).
5. Rotas `me.get`, `invitations.create`, `invitations.accept`, `memberships.list`, `memberships.revoke` e as de auth (seção 3), com schemas em `packages/contracts/src/auth/` e clientes regenerados.
6. Convite e redefinição de senha com token próprio e e-mail pelo `worker` (seção 6).
7. Idempotência (seção 7), mapeamento de erros do banco (seção 8), limites de taxa, `access_log` e `audit_log` (seção 9).
8. `pg_notify('auth_changed', '{"u":"<userId>"}')` em logout, troca/redefinição de senha e revogação de membership, na mesma transação.
9. Suíte de isolamento por rota gerada do registro (`apps/api/test/scope.e2e.test.ts` + `scope-fixtures.ts`) e teste de matriz papel × rota.
10. CLI `operator:create` (seção 10) e `seedIdentityWorld` em `packages/testkit`.
11. Testes de aceite de `tests/acceptance/T-006/` escritos **antes** da implementação (DoR item 6 para N0): como o cartão descreve os testes em tabela, eles são o 1º commit de cada PR de fatia (`test(auth): aceite congelado (T-006)`), escrito por agente de fornecedor diferente do implementador e lido pelo fundador antes dos commits de implementação (14 §7 item 3; um PR só de testes quebraria o `verify` de `main`).

## Fatias

Três PRs sequenciais, um por fatia, com branch `t-006-<k>-slug`. Cada fatia tem no máximo 400 linhas de produção em N0 e torna verdes só o subconjunto de testes indicado. O teste congelado de cada fatia é o 1º commit do PR dela.

| Fatia | Branch | Entrega | Testes que ficam verdes |
|---|---|---|---|
| 1 | `t-006-1-migration` | Migration `20261014130000_identidade.sql`, `withContext` com `opts` e `userId`, `app.current_user_id()`, `memberships_for_user`, entradas da allowlist (seção 2), `ROLE_PERMISSIONS` | `catalog-identity.test.ts`, `permissions.test.ts` |
| 2 | `t-006-2-sessao-e-contexto` | Better Auth e login, pipeline de sessão e contexto, `/me`, `memberships.list`/`revoke`, matriz, erros do banco, idempotência, suíte de isolamento | `auth-session.test.ts`, `two-factor.test.ts`, `context.test.ts`, `memberships.test.ts`, `scope-suite.test.ts` |
| 3 | `t-006-3-convite-e-limites` | Convite, redefinição de senha, e-mail pelo `worker`, limites de taxa, `access_log`/`audit_log`, CLI `operator:create`, `seedIdentityWorld` | `invitations.test.ts`, `password-reset.test.ts`, `rate-limit.test.ts`, `access-audit.test.ts` |

A fatia 1 é marco do checkpoint de 16/10 (02 §2.4): ela destrava a T-007 e o `withContext` com `userId` para a T-012 e a T-017.

## Fora do escopo

- Chave do aparelho, step-up, grants de suporte, `platform_admin`, papéis `installer`, `search_team` e `tenant_member` (F1; aqui ficam sem permissão).
- Fechamento de conexões SSE por `auth_changed` (T-008 consome o NOTIFY; aqui só se emite).
- Rotas de frota e telas do console (T-007); `GET`/`PUT /api/v1/operator/brand`; app (T-009).
- `app.ensure_partitions` e os gatilhos `tenant_immutable`/`vehicle_immutable` (T-005). `app.retention_purge`, inclusive o tipo `idempotency_record` (T-027, F1).

## Arquivos a criar/alterar

```
criar    packages/db/migrations/20261014130000_identidade.sql
alterar  packages/db/{catalog-allowlist.json,src/context.ts,src/kysely.ts,src/index.ts}
criar    packages/db/src/{audit.ts,access-log.ts}    gerar packages/db/src/generated/db.ts
criar    packages/domain/src/auth/{permissions.ts,context.ts,invite-rules.ts,password.ts,common-passwords.txt}  packages/domain/src/common/jcs.ts
criar    packages/contracts/src/auth/{session.ts,me.ts,invitations.ts,memberships.ts}  packages/contracts/src/jobs/email-send.ts
         (alterar registry.ts; regenerar openapi e clientes)
criar    apps/api/src/identity/{identity.module.ts,auth.ts,auth.controller.ts,me.controller.ts,invitations.controller.ts,
         memberships.controller.ts,request-auth.ts,request-context.ts,rate-limit.ts,access-log.hook.ts,totp-replay.ts,password-policy.ts}
criar    apps/api/src/platform/{db-errors.ts,idempotency.ts,route-transaction.ts}  apps/api/src/cli.ts
criar    apps/api/test/{scope.e2e.test.ts,scope-fixtures.ts,permissions.matrix.test.ts}
criar    apps/worker/src/identity/{email.consumer.ts,email-sender.ts}  packages/testkit/src/identity-world.ts  (exporta seedIdentityWorld e signInAs)
alterar  apps/api/src/config/env.ts  apps/worker/src/config/env.ts  .env.example  apps/api/scripts/build.ts (entrada cli)
criar    tests/acceptance/T-006/{world.ts,auth-session,two-factor,context,invitations,password-reset,memberships,rate-limit,access-audit,catalog-identity,scope-suite,permissions}.test.ts
```

## Especificação detalhada

### (1) Migration — SQL exato

```sql
-- migrate:up
-- T-006 — Identidade: schema auth (Better Auth), membership, auditoria, registro de acesso e idempotência.
-- Requisitos: REQ-SEG-001, REQ-SEG-008, REQ-SEG-010, REQ-SEG-026, REQ-API-009, REQ-DAD-001, REQ-DAD-006. CAT-01..CAT-07.
SET LOCAL lock_timeout = '5s'; SET LOCAL statement_timeout = '60s';
-- (a) Schema auth: fora do RLS; acesso só pelo módulo identity (ADR-006). Tabelas do Better Auth no formato do CLI.
CREATE SCHEMA auth;
CREATE TABLE auth."user" (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name text NOT NULL CHECK (length(name) BETWEEN 1 AND 200),
  email text NOT NULL CHECK (email = lower(email) AND length(email) <= 254), "emailVerified" boolean NOT NULL DEFAULT false,
  image text NULL, "twoFactorEnabled" boolean NOT NULL DEFAULT false,
  "createdAt" timestamptz NOT NULL DEFAULT now(), "updatedAt" timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT user_email_key UNIQUE (email)
);
CREATE TABLE auth.session (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), "expiresAt" timestamptz NOT NULL, token text NOT NULL,
  "createdAt" timestamptz NOT NULL DEFAULT now(), "updatedAt" timestamptz NOT NULL DEFAULT now(), "ipAddress" text NULL, "userAgent" text NULL,
  "userId" uuid NOT NULL REFERENCES auth."user" (id) ON DELETE CASCADE,
  "clientKind" text NULL CHECK ("clientKind" IN ('console', 'app')),   -- NULL: sessão recusada com 401
  "stepUpAt" timestamptz NULL,                                         -- F1 (08 §6.4)
  CONSTRAINT session_token_key UNIQUE (token)
);
CREATE INDEX session_user_idx ON auth.session ("userId");
CREATE TABLE auth.account (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), "accountId" text NOT NULL, "providerId" text NOT NULL,
  "userId" uuid NOT NULL REFERENCES auth."user" (id) ON DELETE CASCADE, "accessToken" text NULL, "refreshToken" text NULL, "idToken" text NULL,
  "accessTokenExpiresAt" timestamptz NULL, "refreshTokenExpiresAt" timestamptz NULL, scope text NULL, password text NULL,
  "createdAt" timestamptz NOT NULL DEFAULT now(), "updatedAt" timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX account_user_idx ON auth.account ("userId");
CREATE TABLE auth.verification (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), identifier text NOT NULL, value text NOT NULL,
  "expiresAt" timestamptz NOT NULL, "createdAt" timestamptz NOT NULL DEFAULT now(), "updatedAt" timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE auth."twoFactor" (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), secret text NOT NULL, "backupCodes" text NOT NULL,
  "userId" uuid NOT NULL REFERENCES auth."user" (id) ON DELETE CASCADE
);
-- Tabelas próprias do módulo identity (snake_case).
CREATE TABLE auth.totp_last_step (user_id uuid PRIMARY KEY REFERENCES auth."user" (id),
  last_step bigint NOT NULL CHECK (last_step > 0), updated_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE auth.email_token (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), purpose text NOT NULL CHECK (purpose IN ('invitation', 'password_reset')),
  user_id uuid NOT NULL REFERENCES auth."user" (id), operator_id uuid NULL, membership_id uuid NULL,
  token_sha256 bytea NULL CHECK (length(token_sha256) = 32),          -- só o hash; o token nasce no worker
  expires_at timestamptz NOT NULL, used_at timestamptz NULL, created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT email_token_sha256_key UNIQUE (token_sha256),
  CONSTRAINT email_token_invitation_chk CHECK ((purpose = 'invitation') = (operator_id IS NOT NULL AND membership_id IS NOT NULL))
);
CREATE INDEX email_token_open_idx ON auth.email_token (user_id, purpose) WHERE used_at IS NULL;
GRANT USAGE ON SCHEMA auth TO tracksys_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA auth TO tracksys_app;
GRANT DELETE ON auth.session, auth.verification, auth."twoFactor" TO tracksys_app;   -- exigência do Better Auth
-- (b) Usuário do contexto (04 §4.2 item 5). app.tg_immutable_columns() vem da T-004.
CREATE FUNCTION app.current_user_id() RETURNS uuid LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('app.user_id', true), '')::uuid $$;
GRANT EXECUTE ON FUNCTION app.current_user_id() TO tracksys_app;
-- (c) membership
-- rls: C + G
CREATE TABLE app.membership (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth."user" (id), operator_id uuid NOT NULL REFERENCES app.operator (id), tenant_id uuid NULL,
  role text NOT NULL CHECK (role IN ('operator_admin', 'operator_agent', 'installer', 'search_team', 'tenant_owner', 'tenant_member')),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('invited', 'active', 'revoked')),
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT membership_tenant_fk FOREIGN KEY (operator_id, tenant_id) REFERENCES app.tenant (operator_id, id),
  CONSTRAINT membership_role_scope_chk CHECK ((tenant_id IS NULL) = (role IN ('operator_admin', 'operator_agent', 'installer', 'search_team'))),
  CONSTRAINT membership_user_scope_role_key UNIQUE NULLS NOT DISTINCT (user_id, operator_id, tenant_id, role)
);
CREATE INDEX membership_user_idx ON app.membership (user_id) WHERE status = 'active';
CREATE INDEX membership_operator_tenant_idx ON app.membership (operator_id, tenant_id);
CREATE TRIGGER membership_immutable BEFORE UPDATE ON app.membership FOR EACH ROW
  EXECUTE FUNCTION app.tg_immutable_columns('user_id', 'operator_id', 'tenant_id', 'role');
ALTER TABLE app.membership ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
CREATE POLICY membership_staff_all ON app.membership FOR ALL
  USING (operator_id = app.current_operator_id() AND app.current_scope() = 'operator')
  WITH CHECK (operator_id = app.current_operator_id() AND app.current_scope() = 'operator');
CREATE POLICY membership_tenant_read ON app.membership FOR SELECT
  USING (operator_id = app.current_operator_id() AND app.current_scope() = 'tenant' AND tenant_id = ANY (app.current_tenant_ids()));
-- membership_tenant_manage é criada na parte (g), depois da função que o WITH CHECK usa.
CREATE POLICY membership_definer_read ON app.membership FOR SELECT TO tracksys_owner USING (true);
-- (d) audit_log — tenant_id NULL em ação de nível operadora. Append-only (CAT-06).
-- rls: A
CREATE TABLE app.audit_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), operator_id uuid NOT NULL REFERENCES app.operator (id), tenant_id uuid NULL,
  actor_type text NOT NULL CHECK (actor_type IN ('user', 'support', 'system', 'ai_agent')), actor_id text NULL,
  action text NOT NULL CHECK (action ~ '^[a-z_]+(\.[a-z_]+)+$'), target_type text NOT NULL, target_id text NULL,
  reason text NULL CHECK (length(reason) <= 500), result text NOT NULL CHECK (result IN ('success', 'denied', 'error')),
  ip inet NULL, at timestamptz NOT NULL DEFAULT now(), correlation_id uuid NULL,
  CONSTRAINT audit_log_tenant_fk FOREIGN KEY (operator_id, tenant_id) REFERENCES app.tenant (operator_id, id)
);
CREATE INDEX audit_log_operator_at_idx ON app.audit_log (operator_id, at DESC);
CREATE INDEX audit_log_target_idx ON app.audit_log (target_type, target_id);
ALTER TABLE app.audit_log ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
CREATE POLICY audit_log_isolation ON app.audit_log FOR ALL
  USING (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())))
  WITH CHECK (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())));
-- (e) access_log — plataforma (Marco Civil, 6 meses), sem operator_id (withoutOperatorId). Partições mensais; de 2027-01 em diante, app.ensure_partitions (T-005).
-- rls: F
CREATE TABLE app.access_log (
  id uuid NOT NULL DEFAULT gen_random_uuid(), user_id uuid NULL, ip inet NOT NULL,
  source_port integer NOT NULL CHECK (source_port BETWEEN 0 AND 65535), user_agent text NULL CHECK (length(user_agent) <= 512),
  at timestamptz NOT NULL DEFAULT now(), CONSTRAINT access_log_pkey PRIMARY KEY (id, at)
) PARTITION BY RANGE (at);
-- rls: F (partições herdam as políticas do pai; RLS forçada em cada uma, CAT-01)
CREATE TABLE app.access_log_p202610 PARTITION OF app.access_log FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2026-11-01 00:00:00+00');
CREATE TABLE app.access_log_p202611 PARTITION OF app.access_log FOR VALUES FROM ('2026-11-01 00:00:00+00') TO ('2026-12-01 00:00:00+00');
CREATE TABLE app.access_log_p202612 PARTITION OF app.access_log FOR VALUES FROM ('2026-12-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');
ALTER TABLE app.access_log ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
ALTER TABLE app.access_log_p202610 ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
ALTER TABLE app.access_log_p202611 ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
ALTER TABLE app.access_log_p202612 ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
CREATE POLICY access_log_app_insert ON app.access_log FOR INSERT TO tracksys_app WITH CHECK (true);
-- (f) idempotency_record — 09 §4; tenant_id NULL em operação de nível operadora; operation = operationId do registro (com hífen).
-- rls: A
CREATE TABLE app.idempotency_record (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), operator_id uuid NOT NULL REFERENCES app.operator (id), tenant_id uuid NULL,
  user_id uuid NOT NULL REFERENCES auth."user" (id), operation text NOT NULL CHECK (operation ~ '^[a-z_-]+(\.[a-z_-]+)+$'),
  key text NOT NULL CHECK (key ~ '^[A-Za-z0-9_-]{16,64}$'), intent_sha256 bytea NOT NULL CHECK (length(intent_sha256) = 32),
  response_status smallint NULL, resource_type text NULL, resource_id uuid NULL, problem jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz NOT NULL,
  CONSTRAINT idempotency_record_tenant_fk FOREIGN KEY (operator_id, tenant_id) REFERENCES app.tenant (operator_id, id),
  CONSTRAINT idempotency_record_scope_key UNIQUE (user_id, operation, key)
);
ALTER TABLE app.idempotency_record ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
CREATE POLICY idempotency_record_isolation ON app.idempotency_record FOR ALL
  USING (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())))
  WITH CHECK (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())));
-- (g) Função definidora (04 §4.4, texto exato) e políticas tipo G das tabelas que ela lê.
CREATE FUNCTION app.memberships_for_user(p_user_id uuid)
  RETURNS TABLE (membership_id uuid, operator_id uuid, tenant_id uuid, role text)
  LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
AS $$
  SELECT m.id, m.operator_id, m.tenant_id, m.role FROM app.membership m
    JOIN app.operator o ON o.id = m.operator_id AND o.status = 'active'
    LEFT JOIN app.tenant t ON t.operator_id = m.operator_id AND t.id = m.tenant_id
   WHERE m.user_id = p_user_id AND m.status = 'active' AND (m.tenant_id IS NULL OR t.status <> 'closed')
$$;
REVOKE ALL ON FUNCTION app.memberships_for_user(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.memberships_for_user(uuid) TO tracksys_app;
-- Política que consulta a própria tabela dá "infinite recursion detected in policy"; por isso o
-- WITH CHECK de membership_tenant_manage pergunta a uma função definidora (lê via membership_definer_read).
CREATE FUNCTION app.is_active_tenant_owner(p_operator_id uuid, p_tenant_id uuid)
  RETURNS boolean
  LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
AS $$
  SELECT EXISTS (
    SELECT 1 FROM app.membership m
     WHERE m.user_id = app.current_user_id() AND m.operator_id = p_operator_id
       AND m.tenant_id = p_tenant_id AND m.role = 'tenant_owner' AND m.status = 'active')
$$;
REVOKE ALL ON FUNCTION app.is_active_tenant_owner(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.is_active_tenant_owner(uuid, uuid) TO tracksys_app;
-- Cliente cria e revoga só tenant_member dos próprios tenants, e só se for tenant_owner ativo (04 §4.2).
CREATE POLICY membership_tenant_manage ON app.membership FOR ALL
  USING (operator_id = app.current_operator_id() AND app.current_scope() = 'tenant' AND tenant_id = ANY (app.current_tenant_ids()) AND role = 'tenant_member')
  WITH CHECK (operator_id = app.current_operator_id() AND app.current_scope() = 'tenant' AND tenant_id = ANY (app.current_tenant_ids()) AND role = 'tenant_member'
              AND app.is_active_tenant_owner(operator_id, tenant_id));
-- (h) Privilégios (04 §4.3): sem DELETE; audit_log e access_log append-only.
GRANT SELECT, INSERT, UPDATE ON app.membership, app.idempotency_record TO tracksys_app;
GRANT SELECT, INSERT ON app.audit_log TO tracksys_app;
GRANT INSERT ON app.access_log TO tracksys_app;
-- (i) Fila do e-mail (pg-boss, T-004).
SELECT pgboss.create_queue('email.send', '{"policy":"standard","retryLimit":5,"retryDelay":30,"retryBackoff":true}'::json);

-- migrate:down
SELECT pgboss.delete_queue('email.send');
DROP TABLE app.idempotency_record, app.access_log, app.audit_log, app.membership;
DROP FUNCTION app.memberships_for_user(uuid), app.is_active_tenant_owner(uuid, uuid), app.current_user_id();
DROP SCHEMA auth CASCADE;
-- Ficam: app.tg_immutable_columns e as políticas operator_definer_read/tenant_definer_read (base definidora da T-004).
```

### (2) Allowlist

`catalog-allowlist.json` ganha as entradas abaixo na chave `securityDefiner` da T-004 (`Record<assinatura, justificativa ≥ 10>`, formato de [04 §5.1](../docs/spec/04-dominio-e-dados.md#51-regras-cat-pnpm-dbcheck-ci-em-todo-pr)), sem apagar as que a T-005 gravou em `main`:

```json
{
  "rlsExempt": {},
  "nullableTenantId": {
    "membership": "tenant_id NULL identifica a equipe da operadora (operator_admin, operator_agent, installer, search_team)",
    "audit_log": "ação administrativa de nível operadora sem cliente alvo",
    "idempotency_record": "operação de nível operadora (ex.: convite de equipe) não tem cliente"
  },
  "withoutOperatorId": {
    "access_log": "registro de acesso da plataforma (Marco Civil), sem dono operadora; o app só insere"
  },
  "appendOnly": ["audit_log", "command_event", "access_log"],
  "securityDefiner": {
    "app.memberships_for_user(uuid)": "monta o contexto da requisição antes de existir contexto (08 §4)",
    "app.is_active_tenant_owner(uuid, uuid)": "WITH CHECK de membership_tenant_manage sem recursão de RLS (política não pode consultar a própria tabela)"
  }
}
```

A regra CAT-07 está em [T-004, seção 7](T-004-contratos-e-esqueleto-api-worker.md); `app.current_user_id()` não é `SECURITY DEFINER` e não entra na lista.

As tabelas desta tarefa passam nas regras novas da T-001: `access_log` não tem `operator_id` e entra em `withoutOperatorId` (CAT-03); toda FK para `app.tenant` liga `operator_id → operator_id` e `tenant_id → id` na mesma posição, e as FKs para `auth."user"` e `app.operator` ficam fora da CAT-04; `tracksys_app` não tem UPDATE, DELETE nem TRUNCATE em `audit_log` e `access_log` (CAT-06).

### (3) Better Auth e rotas

`createAuth(env, authPool)`: opções de 08 §2 com estes ajustes: `database` = `pg.Pool` (`DATABASE_URL_APP`, `options: '-c search_path=auth'`, `max: 5`); `session.additionalFields` com `input: false`; `advanced.database.generateId: () => randomUUID()`; `twoFactor({ issuer: 'TrackSys', backupCodeOptions: { amount: 10 } })`; sem `databaseHooks` e sem `sendResetPassword` (ver seção 6). Origem do console: `https://app.<TRACKSYS_DOMAIN>` (mais `http://localhost:5173` em `development`). [VALIDAR — T-006: nomes de opções e de `auth.api.*` na versão fixada; registre diferenças no PR.]

| `operationId` | Método e caminho | Auth · permissão | Request → Response |
|---|---|---|---|
| `auth.sign-in-email` | `POST /api/v1/auth/sign-in/email` | público | `{email, password}` → 200 `{user{id,name,email,twoFactorEnabled}, twoFactorRedirect}` |
| `auth.verify-totp` · `auth.verify-backup-code` | `POST /api/v1/auth/two-factor/verify-totp` · `/verify-backup-code` | login pendente | `{code}` → 200 `{user{…}}` |
| `auth.sign-out` · `auth.get-session` | `POST /api/v1/auth/sign-out` · `GET /api/v1/auth/get-session` | sessão · `null` | → 200 `{status:"ok"}` · 200 `{user{…}, session{id, clientKind, expiresAt}}` |
| `auth.request-password-reset` · `auth.reset-password` | `POST /api/v1/auth/request-password-reset` · `/reset-password` | público | `{email}` → 200 `{status:"ok"}` sempre · `{token, newPassword}` → 200 `{status:"ok"}` |
| `auth.change-password` | `POST /api/v1/auth/change-password` | sessão · `null` | `{currentPassword, newPassword}` → 200; revoga as outras sessões |
| `auth.two-factor-enable` · `-disable` | `POST /api/v1/auth/two-factor/enable` · `/disable` | sessão · `null` | `{password}` → 200 `{totpURI, backupCodes[10]}` · 200 `{status:"ok"}` |
| `me.get` | `GET /api/v1/me` | sessão · `null` | → 200 `{user{id,name,email,twoFactorEnabled}, clientKind, operator{id,displayName}\|null, brand{displayName,logoUrl,primaryColor,secondaryColor,supportWhatsapp,supportPhone}\|null, memberships[{id,role,tenantId}], permissions[]}` |
| `invitations.create` | `POST /api/v1/invitations` | sessão · `user.manage_customer` | `{email, name, role, tenantId?}` → 201 `{membershipId, status:"invited", expiresAt}`; `Idempotency-Key` obrigatória |
| `invitations.accept` | `POST /api/v1/invitations/accept` | público | `{token, password}` → 200 `{userId}` |
| `memberships.list` · `memberships.revoke` | `GET /api/v1/memberships` · `DELETE /api/v1/memberships/{membershipId}` | sessão · `user.manage_customer` | `?tenantId&role&status&cursor&limit` → coleção `{id,userId,name,email,role,tenantId,status,createdAt}` · → 204 |

Login (`auth.sign-in-email`): sem `Origin` → `clientKind = 'app'`; `Origin` = origem do console → `'console'`; outra → 403 `CSRF_REJECTED`. Chama `auth.api.signInEmail({ body, headers, asResponse: true })`; erro de credencial → 401 `INVALID_CREDENTIALS` com o mesmo corpo exista ou não o e-mail. Sucesso: `UPDATE auth.session SET "clientKind" = $1, "expiresAt" = CASE WHEN $1 = 'console' THEN "createdAt" + interval '12 hours' ELSE "expiresAt" END WHERE token = $2`; app → remove `Set-Cookie` da resposta; console → remove `set-auth-token` e grava `Max-Age=43200` no cookie `__Secure-tracksys.session_token`. Usuário com 2FA: console recebe `twoFactorRedirect: true`; app recebe 403 `FORBIDDEN` `reason: "two_factor_app_unsupported"`. `verify-totp` aplica o mesmo `UPDATE` e a proteção contra reuso: após sucesso, calcula o passo casado (s−1, s ou s+1, decifrando o segredo com a chave do Better Auth) e executa `INSERT INTO auth.totp_last_step … ON CONFLICT (user_id) DO UPDATE SET last_step = EXCLUDED.last_step, updated_at = now() WHERE auth.totp_last_step.last_step < EXCLUDED.last_step RETURNING user_id`; sem linha → apaga a sessão recém-criada e responde 401 `INVALID_CREDENTIALS`. Se o passo não puder ser calculado, usa `floor(agora/30) + 1` (falha fechada).

### (4) Pipeline de rota `auth: 'session'` (ordem fixa)

1. Limite por IP (600/min) — seção 9.
2. Transporte: `Authorization: Bearer` presente → `bearer`; senão cookie `__Secure-tracksys.session_token` → `cookie`; nenhum → 401 `AUTH_REQUIRED` `reason: "missing"`.
3. `auth.api.getSession({ headers })` nulo → 401 `reason: "invalid"`; `clientKind` NULL → 401 `invalid`; `console` por bearer ou `app` por cookie → 401 `reason: "wrong_transport"`; `console` com `now() > createdAt + 12 h` → apaga a sessão e 401 `reason: "expired"`.
4. Cookie + método fora de GET/HEAD/OPTIONS + `Origin` ausente ou diferente da origem do console → 403 `CSRF_REJECTED`, sem efeito.
5. Limite por sessão (300/min). `access_log` (seção 9).
6. `SELECT * FROM app.memberships_for_user($userId)` (função definidora; única leitura de `app` sem contexto).
7. Operadora: `X-Operator-Id` (uuid) fora das operadoras das memberships → 404 `NOT_FOUND`; sem o header e com mais de uma operadora → 400 `OPERATOR_SELECTION_REQUIRED` com `operators[{id, displayName}]` (nome lido com o contexto de cada operadora).
8. Gate de 2FA: membership `operator_admin` na operadora e `twoFactorEnabled = false` → só `me.get`, `auth.get-session`, `auth.sign-out` e `auth.two-factor-*`; demais → 403 `TWO_FACTOR_ENROLLMENT_REQUIRED`.
9. `resolveRequestContext(memberships, operatorId)` (pura, 08 §4 item 3). `null` → 404 em toda rota exceto `me.get` (200 com listas vazias) e `auth.*`.
10. Permissão: todas as permissões da rota ⊆ união de `ROLE_PERMISSIONS` dos papéis na operadora; senão 403 `FORBIDDEN`. Restrições finas (campo, papel convidado, recurso) ficam no handler, depois de carregar o recurso sob RLS (invisível → 404; visível sem direito → 403).
11. Transação de rota (`route-transaction.ts`), exceto `auth.*` e `invitations.accept`: `withDb(pool, ctx, fn, { readOnly: method === 'GET', statementTimeoutMs: 5000 })` → idempotência (seção 7) → handler. Jobs são enfileirados **na mesma transação** (`send` do pg-boss com a opção `db` sobre o `PoolClient` da rota [VALIDAR — T-006]). SQLSTATE 40001/40P01 → 1 nova tentativa da transação inteira, depois 503.

### (5) Matriz do F0 e regras de convite

`ROLE_PERMISSIONS` (`packages/domain/src/auth/permissions.ts`), união por papel:

| Permissão | `operator_admin` | `operator_agent` | `tenant_owner` |
|---|---|---|---|
| `tenant.read` · `vehicle.read` · `telemetry.live` · `telemetry.history` · `alert.read` · `alert.ack` · `watch_mode.manage` | sim | sim | sim (próprio cliente, por RLS) |
| `tenant.write` · `device.read` · `device.write` · `assignment.write` | sim | sim | — |
| `vehicle.write` | sim | sim | sim (handler aceita só `nickname` e `color`) |
| `user.manage_customer` | sim | sim | sim (convida só `tenant_member`: F1) |
| `user.manage_staff` · `brand.manage` | sim | — | — |

`installer`, `search_team` e `tenant_member` têm conjunto vazio no F0. `canInvite(papéisDoConvidante, papelAlvo)` (`invite-rules.ts`): `operator_admin` → `operator_admin`, `operator_agent`, `tenant_owner`; `operator_agent` → só `tenant_owner`; `tenant_owner` → só `tenant_member` (fora do enum do F0 → nunca). Revogar membership de equipe exige `user.manage_staff`; ninguém revoga a própria (409 `CONFLICT`).

### (6) Convite, redefinição de senha e e-mail

- `invitations.create` (transação de rota): corpo `{email (minúsculo), name (1–200), role ∈ F0_ROLES, tenantId?}`; `tenant_owner` exige `tenantId` (senão 422 `rule: "tenant_required"`), equipe o proíbe (`tenant_forbidden`); `canInvite` falso → 403; cliente invisível → 404, `closed` → 409. Cria `auth."user"` se o e-mail não existir; `INSERT` da membership `invited` (`ON CONFLICT ON CONSTRAINT membership_user_scope_role_key`: `active` → 409 `CONFLICT`; `revoked` → volta a `invited`; `invited` → mantém); marca `used_at` dos tokens abertos dessa membership; `INSERT auth.email_token` (`invitation`, `expires_at = now() + 72 h`); enfileira `email.send`; `audit_log` `membership.invite`.
- `invitations.accept`: hash SHA-256 do token → `email_token` aberto e não vencido; senão 404 `INVITATION_INVALID`. Abre `withDb` no escopo `operator` da linha e, na mesma transação: relê o token `FOR UPDATE`; usuário sem conta `credential` → aplica a política de senha (422 sem consumir o token) e cria a conta com o hash do Better Auth; com conta → a senha precisa conferir (senão 401 `INVALID_CREDENTIALS`); `UPDATE app.membership SET status = 'active' WHERE id = $1 AND status = 'invited'` (0 linhas → 404 `INVITATION_INVALID`); `used_at = now()`; `"emailVerified" = true`; `audit_log` `membership.accept`.
- `auth.request-password-reset`: e-mail com conta `credential` → invalida tokens abertos, `INSERT email_token` (`password_reset`, `now() + 1 h`), enfileira; sempre 200 `{status:"ok"}`, mesmo corpo. `auth.reset-password`: token válido → política de senha → novo hash em `auth.account` → `DELETE` das sessões do usuário → `used_at` → `pg_notify`; token inválido → 422 com `errors[0] = {path: "token", rule: "token_invalid"}`.
- Política de senha (`password.ts`, pura; a lista é carregada pelo `api` no boot): 10 a 128 caracteres (`password_min_length`/`password_max_length`); recusa (`password_common`) se `lower(senha)` ou `lower(senha)` sem dígitos finais estiver em `common-passwords.txt` (10.000 senhas mais comuns da SecLists, licença MIT, citada no PR).
- Job `email.send` (contrato em `packages/contracts/src/jobs/email-send.ts`): `{eventId, type: 'invitation'|'password_reset'|'login_lockout', operatorId|null, tenantId|null, entityId}` (`entityId` = id do `email_token`, ou do usuário no bloqueio). O consumidor do `worker`: transação → `UPDATE auth.email_token SET token_sha256 = $hash WHERE id = $1 AND used_at IS NULL AND expires_at > now() RETURNING …` com token de 32 bytes aleatórios em base64url (0 linhas → conclui sem enviar) → COMMIT → envia. Links: `https://app.<TRACKSYS_DOMAIN>/convite#<token>` e `/redefinir-senha#<token>`. Nome da operadora no convite lido com o contexto `operator` do payload. Retentativa gera token novo (o anterior deixa de valer). Log só com `emailTokenId`, `type` e destino mascarado (`n***@exemplo.com`).
- `EmailSender`: `resend` (`POST https://api.resend.com/emails`, prazo 10 s) ou `file` (grava `{to, subject, text}` em `EMAIL_FILE_DIR`; proibido com `NODE_ENV=production`, erro 78). Variáveis do `worker`: `EMAIL_DRIVER`, `EMAIL_FROM`, `RESEND_API_KEY` (obrigatória com `resend`), `EMAIL_FILE_DIR` (padrão `.tmp/emails`). Do `api`: `TRUSTED_PROXY_CIDRS` (CIDRs separados por vírgula, padrão vazio).

### (7) Idempotência (09 §4)

Primeiro comando da transação de rota com chave: `INSERT INTO app.idempotency_record (operator_id, tenant_id, user_id, operation, key, intent_sha256, expires_at) VALUES (…, now() + interval '24 hours') ON CONFLICT (user_id, operation, key) DO UPDATE SET intent_sha256 = EXCLUDED.intent_sha256, response_status = NULL, resource_type = NULL, resource_id = NULL, problem = NULL, created_at = now(), expires_at = EXCLUDED.expires_at WHERE app.idempotency_record.expires_at <= now() RETURNING id`. Com linha → executa e grava `response_status`, `resource_type`, `resource_id`. Sem linha → lê a existente: mesmo hash → repete o status com a representação atual do recurso e `Idempotent-Replayed: true`; hash diferente → 409 `IDEMPOTENCY_CONFLICT`. Intenção = SHA-256 de `operation + "\n" + JCS(params) + "\n" + JCS(body)` (`jcs.ts`, RFC 8785). `tenant_id` = NULL no escopo `operator`, `ctx.tenantIds[0]` no escopo `tenant`. Chave: `[A-Za-z0-9_-]{16,64}`; ausente em rota `required` ou fora do formato → 400 `IDEMPOTENCY_KEY_REQUIRED`.

### (8) Erros do banco → HTTP (`db-errors.ts`)

42501 e 23503 → 404 `NOT_FOUND`; 23P01 → 409 do mapa de constraints (padrão `CONFLICT`); 23505 → 409 do mapa (padrão `CONFLICT`); 23000 (gatilhos de imutabilidade) → 409 `CONFLICT`; 25006 → 403 `FORBIDDEN`; 57014, `08***` e 53300 → 503 `DEPENDENCY_UNAVAILABLE` com `Retry-After: 5`; demais → 500. `registerConstraintProblem(constraint, code)` é usado pelas tarefas seguintes (T-007: IMEI, ICCID, sobreposição).

### (9) Limites, `access_log` e `audit_log`

- Contadores em memória do processo (`rate-limit.ts`), resposta 429 `RATE_LIMITED` com `Retry-After` e `retryAfterS`: login 5 falhas/15 min por par e-mail+IP (bloqueio de 15 min contado da 5ª falha, inclusive para senha certa), 50 falhas/h por e-mail (bloqueio de 1 h + 1 job `login_lockout`), 20 tentativas/15 min por IP; `verify-totp` 5/15 min por login pendente; `request-password-reset` 3/h por e-mail e 10/h por IP (excedido: 200 sem enviar); `invitations/accept` 10/min por IP e 60 falhas/h bloqueiam o IP por 1 h; demais rotas 300/min por sessão e 600/min por IP.
- IP e porta: do socket; `X-Forwarded-For` (primeiro salto) e `X-Client-Port` só quando o socket vem de `TRUSTED_PROXY_CIDRS`.
- `access_log` (`appendAccessLog(pool, …)`, transação própria, tabela tipo F sem contexto): 1 linha por login com sucesso e por par (usuário, IP, porta) novo em 15 min (cache em memória); falha de gravação só loga erro.
- `audit_log` (`appendAudit(db, …)` dentro da transação da mudança, com `correlation_id`): `membership.invite|accept|revoke`, `auth.two_factor_enable|disable`, `operator.create` (CLI, `actor_type = 'system'`).

### (10) CLI e mundo de teste

`node apps/api/dist/cli.js operator:create --legal-name "<razão>" --display-name "<nome>" [--document <dígitos>] --admin-email <e-mail> --admin-name "<nome>"` (também `pnpm --filter @tracksys/api cli …`): numa transação `withDb({ scope: 'operator', operatorId: <uuid novo> })` cria `operator`, `operator_brand` (nome, cor padrão), usuário, membership `operator_admin` `invited`, `email_token` e job; `audit_log` `operator.create`. Imprime `{"operatorId","membershipId","expiresAt"}`; nunca o token. `seedIdentityWorld()` (testkit) cria Alfa (A1, A2), Beta (B1) e `admin.alfa`, `agente.alfa`, `dono.a1`, `dono.a2`, `admin.beta` (`<nome>@exemplo.com`, senhas `CANARIO-<uuid>`), com opção de 2FA ativo e segredo TOTP conhecido. `signInAs(world, user, { clientKind = 'app' })` (exportado de `packages/testkit`, usado pela T-012 e seguintes) faz o login real pelas rotas desta tarefa e devolve os headers da sessão: `app` → `Authorization: Bearer <token>`; `console` → cookie `__Secure-tracksys.session_token` e `Origin` do console (com TOTP do segredo conhecido quando o usuário tem 2FA).

## Testes de aceite (congelados)

`tests/acceptance/T-006/`, com `api` e `worker` em processo (`EMAIL_DRIVER=file`, `TRUSTED_PROXY_CIDRS=127.0.0.1/32,::1/128`, `TRACKSYS_DOMAIN=tracksys.com.br`) e o mundo de `world.ts`.

| Arquivo | Dado / Quando / Então |
|---|---|
| `auth-session.test.ts` (CT-SEG-001, 003, 004, 005) | `POST /api/v1/auth/sign-up/email` com `{"email":"x@exemplo.com","password":"Senha-forte-123"}` → 404 `NOT_FOUND` e `auth."user"` sem linha nova. `dono.a1` com senha errada e `naoexiste@exemplo.com` → 401 `INVALID_CREDENTIALS`, corpos iguais exceto `correlationId`. Login sem `Origin` → `set-auth-token` e nenhum `Set-Cookie`; o token como cookie → 401; `expiresAt` da sessão forçado para `now() - 1 s` → 401; `expiresAt` = `now() + 30 dias − 25 h` (última renovação há 25 h) → a requisição renova para ≈ `now() + 30 dias`; com `now() + 30 dias − 1 h` → não renova. Login de `agente.alfa` com `Origin: https://app.tracksys.com.br` → `Set-Cookie` com `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`, `Max-Age=43200` e sem `Domain=`; cookie como Bearer → 401; `createdAt` forçado para 12 h e 1 s atrás → 401 `reason: "expired"`. `POST /api/v1/invitations` por cookie com `Origin: https://evil.example`, sem `Origin` e com `Origin: https://status.tracksys.com.br` → 403 `CSRF_REJECTED` e 0 membership nova; com `Origin: https://app.tracksys.com.br` → 201 |
| `two-factor.test.ts` (CT-SEG-006) | `admin.alfa` sem 2FA: `GET /api/v1/memberships` → 403 `TWO_FACTOR_ENROLLMENT_REQUIRED`; `GET /api/v1/me` → 200. Após `enable` + `verify-totp`: login com senha → `twoFactorRedirect: true` e `GET /api/v1/memberships` → 401 até `verify-totp` válido (200). O mesmo código em outro login no mesmo passo de 30 s (o teste começa com ≥ 10 s restantes no passo) → 401 `INVALID_CREDENTIALS`. Login de `admin.alfa` sem `Origin` → 403 `reason: "two_factor_app_unsupported"` |
| `context.test.ts` (CT-SEG-008, CT-DAD-002 e 003 parte) | Rota de fixture `GET /api/v1/__test/context` (via `@tracksys/api/testing`) devolve `current_setting` da transação: `agente.alfa` → `app.scope = 'operator'`; `dono.a1` → `app.tenant_ids = '{<A1>}'`; `agente.alfa` com `X-Operator-Id: <Beta>` → 404; usuário com memberships na Alfa e na Beta sem o header → 400 `OPERATOR_SELECTION_REQUIRED` com as 2 operadoras. Handler GET de fixture que faz `INSERT` → SQLSTATE 25006 → 403 `FORBIDDEN`. `tracksys_app` sem contexto conta `membership` → 0. Contexto `tenant` de A1 insere `tenant_member` em A1 → grava; `tenant_owner` → 42501 |
| `invitations.test.ts` (CT-SEG-010, CT-API-009, CT-SEG-002 parte) | `admin.alfa` convida `novo@exemplo.com` como `tenant_owner` de A1 com `Idempotency-Key: K1-0000000000000001` → 201 `status: "invited"` e 1 job `email.send` `created`; o `worker` grava o e-mail com o link; `auth.email_token` só tem `token_sha256` (nenhuma coluna contém o token). Repetição com K1 → 201 com `Idempotent-Replayed: true`, 1 membership e 1 job; K1 com outro e-mail → 409 `IDEMPOTENCY_CONFLICT`; 2 requisições paralelas com K2 → 1 membership; sem chave → 400 `IDEMPOTENCY_KEY_REQUIRED`; `expires_at` de K1 forçado ao passado → K1 cria convite novo. Aceite com `"123456789"` → 422 `password_min_length`; com `"password1234"` → 422 `password_common`; com `expires_at` = `now() + 1 h` (71 h após a emissão) e senha válida → 200 e membership `active`; mesmo token de novo → 404 `INVITATION_INVALID`. `agente.alfa` convida `operator_admin` → 403 |
| `password-reset.test.ts` (CT-ARQ-008, CT-SEG-002 parte) | Com o `worker` parado, `request-password-reset` de `dono.a1` responde 200 em ≤ 500 ms e existe 1 job `email.send` `created`; `naoexiste@exemplo.com` → 200 com o mesmo corpo e 0 job. `dono.a1` com 2 sessões redefine a senha → as 2 recebem 401 na requisição seguinte; token reutilizado → 422 `token_invalid` |
| `memberships.test.ts` (CT-SEG-007 HTTP) | `admin.alfa` lista memberships → só da Alfa. Revoga `dono.a1` às `T` → 204, 1 NOTIFY `auth_changed` com `{"u":"<id de dono.a1>"}`, `audit_log` `membership.revoke`; a requisição seguinte de `dono.a1` a `GET /api/v1/__test/context` → 404 e `GET /api/v1/me` → 200 com `memberships: []`. `admin.beta` revoga membership da Alfa → 404; `admin.alfa` revoga a própria → 409 |
| `rate-limit.test.ts` (CT-SEG-023) | `X-Forwarded-For: 203.0.113.10`: 5 senhas erradas de `dono.a1` → 6ª com a senha certa → 429 com `Retry-After` entre 890 e 900; de `198.51.100.7` com a senha certa → 200; a sessão aberta antes continua 200; o mesmo com `naoexiste@exemplo.com` → mesma resposta na 6ª. De `192.0.2.50`, 21 tentativas com e-mails diferentes → a 21ª recebe 429 |
| `access-audit.test.ts` (CT-SEG-026) | `dono.a1` entra com `X-Forwarded-For: 203.0.113.10` e `X-Client-Port: 51515` → 1 `access_log` com esse IP, `source_port = 51515` e `at` UTC; 10 requisições com a mesma porta → continua 1; porta 51600 → 2. Convite cria `audit_log` `membership.invite`, `actor_type = 'user'`, `result = 'success'`. `tracksys_app` executa `UPDATE app.audit_log SET reason = 'x'` → 42501 |
| `catalog-identity.test.ts` (CT-DAD-005, CT-DAD-006 parte, ISO-01..05) | `pnpm db:check` → `Catálogo OK: nenhuma violação de CAT-01..CAT-07.` `memberships_for_user` executada por `tracksys_ingest` → 42501; contexto `tenant` de A1 com `userId` de `dono.a1` insere membership `tenant_member` → 1 linha; o mesmo INSERT com `userId` de um `tenant_member` de A1 → 42501, sem erro de recursão; `is_active_tenant_owner` executada por `tracksys_ingest` → 42501; para `dono.a1` com A1 `closed` → 0 linhas; com a Alfa `suspended` → 0 linhas. ISO-01 a 05 em `membership`, `audit_log` e `idempotency_record` (leitura cruzada 0 linhas; `operator_id` da Beta → 42501; `tenant_id` da Beta → 23503). CT-DAD-009 (parte de `access_log`): depois de `SELECT app.ensure_partitions()` (a função é da T-005; se ainda não estiver em `main`, o teste a pula com `to_regprocedure`), existem as partições de `access_log` do mês UTC corrente e do seguinte, todas com `relrowsecurity` e `relforcerowsecurity`; `withContext` com `userId` grava `app.user_id` e `app.current_user_id()` devolve esse UUID, sem `userId` devolve NULL, e `withContext` sem `userId` passa nos testes da T-001 |
| `scope-suite.test.ts` (CT-API-018) | `buildScopeCases(routes, fixtures)` gera `memberships.revoke:401` e `memberships.revoke:cross-operator-404`, e a suíte `apps/api/test/scope.e2e.test.ts` passa; com a rota de fixture `sim-cards.get` sem entrada em `scope-fixtures.ts` → lança `rota sem fixture de isolamento: sim-cards.get` |
| `permissions.test.ts` (CT-SEG-009 parte) | `ROLE_PERMISSIONS` é igual à tabela da seção 5 copiada no teste; `canInvite` cobre os 9 pares papel × papel do F0; o teste de matriz falha se uma rota `session` não tiver linha |

## Comandos de verificação

```bash
pnpm install && cp .env.example .env && pnpm db:up
pnpm db:migrate                  # Applied: 20261014130000_identidade.sql
pnpm db:check                    # Catálogo OK: nenhuma violação de CAT-01..CAT-07.
pnpm db:types:check && pnpm contracts:check
pnpm --filter @tracksys/api test # scope.e2e + matriz
pnpm verify                      # inclui T-001, T-004 e T-006 (e db:rollback + db:migrate)
pnpm db:rollback && pnpm db:migrate
```

## Definição de pronto

- Testes de `tests/acceptance/T-006/` no 1º commit do PR, lidos pelo fundador antes da implementação e intactos depois; todos os comandos acima verdes, local e no CI.
- Revisão adversarial de outro fornecedor e leitura humana linha a linha registradas; o PR lista REQ/CT, risco N0 e as respostas dos [VALIDAR — T-006].
- Nenhum token, senha, cookie ou e-mail completo em log (CANARIO ausente do stdout/stderr dos testes).

## Decisões já tomadas

| Dúvida provável | Resposta |
|---|---|
| Montar o handler do Better Auth em `/api/v1/auth/*`? | Não. Um handler registrado por caminho da allowlist chama `auth.api.*`; o resto não existe (CT-SEG-001 por construção) e todo caminho passa pelo registro (REQ-API-001). |
| Snake_case no schema `auth`? | As tabelas do Better Auth seguem o CLI (ADR-006, colunas camelCase entre aspas); ids `uuid`. As tabelas próprias (`totp_last_step`, `email_token`) usam snake_case. |
| Convite e redefinição pelo fluxo do Better Auth? | Não: o token nasceria no `api` e iria no payload do job. Tabela própria com só o SHA-256; o `worker` gera o token e envia (08 §2 item 3, REQ-ARQ-008, REQ-ARQ-010). Resolve o [VALIDAR — T-006] de 08 §2. |
| Onde guardar o último passo TOTP? | `auth.totp_last_step`, com verificação pós-sucesso e revogação da sessão criada (resolve o [VALIDAR — T-006] de 08 §2). |
| `clientKind` por hook do Better Auth? | Não: o handler de login grava `clientKind` e o prazo de 12 h logo após o sucesso; sessão com `clientKind` NULL recebe 401 (falha fechada). |
| Usuário com 2FA no app? | No F0, 403 `two_factor_app_unsupported`: só a equipe usa TOTP, pelo console. O F1 revê para `installer`/`search_team`. |
| Quem cria `memberships_for_user`? | Esta tarefa: ela lê `membership`, que nasce aqui. A T-005 cria as demais funções de 04 §4.4. As políticas G de `operator`/`tenant` e o gatilho de imutabilidade vêm da T-004. |
| `idempotency_record` sem expurgo? | Chave vencida é reaproveitada pelo `ON CONFLICT … WHERE expires_at <= now()` (CT-API-009 passa sem DELETE). O expurgo de volume entra no tipo `idempotency_record` de `app.retention_purge` (T-027, F1). |
| O ISO-06 congelado da T-001 colide com a `app.audit_log` real? | Não. O meta-teste do catálogo usa tabelas `app.tmp_*` (ex.: `tmp_append_only`) criadas e desfeitas na mesma transação, com a allowlist estendida só no teste. Esta tarefa **não** leva o rótulo `acceptance-change` e não altera `tests/acceptance/T-001/**`. |
| Versão da migration | `20261014130000` (a T-005 usa `20261014120000_ingestao.sql`); o dbmate identifica a migration pela versão numérica, então as duas não podem coincidir. |
| `access_log` sem `operator_id` na CAT-03 | Entra em `withoutOperatorId` na seção 2, no mesmo PR. |
| `tenant_member`, `installer`, `search_team` no F0? | Constam no CHECK da tabela, sem permissão e fora do enum de convite. |
| Contadores de limite no banco? | Não no F0–F1: um processo `api`, memória (08 §9). |
| Partições de `access_log` depois de dezembro? | `app.ensure_partitions` (T-005) cria `access_log_pAAAAMM` com o mesmo nome e limites UTC. |
| `userId` no contexto | `withContext` aceita `userId` opcional e grava `app.user_id`; quem grava `device_key` (T-017) DEVE passá-lo. Sem `userId`, `app.current_user_id()` devolve NULL e nenhuma política que o use passa. |
| `device_key` nasce na T-006? | Não. Nasce na T-017 (bloco A); a T-006 entrega só `withContext` com `userId`, `app.current_user_id()` e `membership_definer_read`. `auth.email_token.purpose` é ampliado pela T-017 com `device_key_not_me` (constraint `email_token_purpose_check`). |
| Commit | `feat(db): identidade (T-006)`, `feat(api): sessao e contexto rls (T-006)`, `test(auth): aceite congelado (T-006)`. |
