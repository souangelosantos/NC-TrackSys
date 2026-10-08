# T-001 — Fundação: monorepo, Postgres local e isolamento em 3 níveis

| Campo | Valor |
|---|---|
| Fase | F0 (semana S1: 07–13/10/2026) |
| Requisitos | REQ-DAD-002, REQ-DAD-003 (padrões para as 4 tabelas desta tarefa), REQ-DAD-004, REQ-DAD-005 (CAT-01 a CAT-06; a CAT-07 entra na T-005 ou na T-006), REQ-QLD-005 (job acceptance-freeze) |
| Invariantes | INV-07 (isolamento), INV-12 (convenções) |
| Regras de catálogo | CAT-01 a CAT-06; testes ISO-01 a ISO-09 (2 operadoras × 2 clientes) e testes do `withContext` |
| Risco de revisão | **N0** (migrations e contexto RLS) — revisão cruzada por agente de outro fornecedor + leitura humana linha a linha |
| Depende de | nenhuma (primeira tarefa do repositório) |
| Estimativa | 1 sessão de agente |
| Bloqueado por decisão | nenhuma |

> **Este cartão é autossuficiente.** Tudo o que você precisa para implementar está aqui: arquivos com conteúdo exato, SQL validado e testes de aceite prontos. Os links da seção "Contexto" explicam o porquê, mas não são necessários para executar. **Validação prévia:** este conteúdo foi executado em 08/10/2026 contra PostgreSQL 17: migration (up, rollback e up de novo), verificador de catálogo, lint, typecheck e os 23 testes passaram. Cada proteção do `withContext` e do verificador tem um teste que falha quando a proteção é removida (testado por mutação).

## Objetivo

Criar o esqueleto do monorepo e a primeira migration com o modelo de isolamento em 3 níveis (plataforma → operadora → cliente). A partir desta tarefa, **nenhuma tabela entra no schema `app` sem RLS forçada, política e FK composta**: o CI verifica isso automaticamente em todo PR (verificador de catálogo) e prova o isolamento com testes reais no banco.

## Contexto (por quê)

- [ADR-004 — Isolamento em 3 níveis](../docs/adr/ADR-004-isolamento-tres-niveis.md) e [04 — Domínio e dados](../docs/spec/04-dominio-e-dados.md): modelo RLS, papéis de banco, funções de contexto.
- [14 — Qualidade e processo com IA](../docs/spec/14-qualidade-e-processo-ia.md): testes congelados, níveis de risco, CI.
- [AGENTS.md](../AGENTS.md): regras gerais para agentes.

## Pré-requisitos do ambiente

- Node.js ≥ 22.12 (recomendado 24 LTS, arquivo `.nvmrc`).
- pnpm 10.28.0 (`corepack enable` ou `npm i -g pnpm@10.28.0`).
- Docker com Compose v2.17+ (usa `docker compose up --wait`).
- Acesso de rede ao Docker Hub e aos repositórios apt do Debian e do PostgreSQL (PGDG), usados no build da imagem do banco.
- Porta local `54329` livre.

## Escopo — fazer

1. Criar os arquivos da raiz com o conteúdo exato da seção "Especificação detalhada" (1).
2. Criar a imagem do banco e o `docker-compose.yml` (2).
3. Criar a migration `20261007120000_fundacao_isolamento.sql` com o SQL exato (3).
4. Implementar o pacote `@tracksys/db` (4): `loadDbEnv`, `withContext`, `runCatalogChecks`, `loadCatalogAllowlist` e o script `check-catalog`.
5. Copiar os testes de aceite congelados para `tests/acceptance/T-001/` **sem alterar nada** (5).
6. Criar o workflow de CI (6).
7. Rodar `pnpm install` para gerar o `pnpm-lock.yaml` e commitá-lo.
8. Rodar a sequência de verificação e deixar tudo verde.

## Fora do escopo

- Apps NestJS, Kysely, Better Auth, Traccar, console, app Flutter (tarefas T-002 em diante).
- Outras tabelas (membership, device, position etc.), particionamento e gatilhos de `updated_at`.
- Deploy, backups e qualquer infraestrutura na Oracle.
- Alterar versões major das dependências listadas.

## Arquivos a criar

```
.editorconfig
.env.example
.github/workflows/ci.yml
.gitignore
.nvmrc
biome.json
docker-compose.yml
infra/db/Dockerfile
infra/db/initdb/00-init.sh            (executável: chmod +x)
package.json
pnpm-lock.yaml                        (gerado por pnpm install)
pnpm-workspace.yaml
tsconfig.base.json
packages/db/catalog-allowlist.json
packages/db/migrations/20261007120000_fundacao_isolamento.sql
packages/db/package.json
packages/db/scripts/check-catalog.ts
packages/db/src/allowlist.ts
packages/db/src/catalog.ts
packages/db/src/context.ts
packages/db/src/env.ts
packages/db/src/index.ts
packages/db/tsconfig.json
tests/tsconfig.json
tests/vitest.config.ts
tests/acceptance/T-001/world.ts
tests/acceptance/T-001/isolation.test.ts
tests/acceptance/T-001/context.test.ts
tests/acceptance/T-001/catalog.test.ts
```

Não crie `.env` no git (está no `.gitignore`); localmente rode `cp .env.example .env`.

## Especificação detalhada

### (1) Raiz do monorepo — conteúdo exato

`package.json`
```json
{
  "name": "tracksys",
  "private": true,
  "type": "module",
  "packageManager": "pnpm@10.28.0",
  "engines": {
    "node": ">=22.12"
  },
  "scripts": {
    "db:up": "docker compose up -d --wait db",
    "db:down": "docker compose down",
    "db:reset": "docker compose down -v && docker compose up -d --wait db",
    "db:migrate": "dbmate --migrations-dir ./packages/db/migrations --no-dump-schema --wait up",
    "db:rollback": "dbmate --migrations-dir ./packages/db/migrations --no-dump-schema rollback",
    "db:check": "tsx packages/db/scripts/check-catalog.ts",
    "lint": "biome check .",
    "format": "biome format --write .",
    "typecheck": "pnpm -r run typecheck && tsc -p tests/tsconfig.json",
    "test:acceptance": "vitest run --config tests/vitest.config.ts",
    "verify": "pnpm lint && pnpm typecheck && pnpm db:migrate && pnpm db:rollback && pnpm db:migrate && pnpm db:check && pnpm test:acceptance"
  },
  "devDependencies": {
    "@biomejs/biome": "^2.5.15",
    "@tracksys/db": "workspace:*",
    "@types/node": "^24.19.1",
    "@types/pg": "^8.23.1",
    "dbmate": "^2.36.0",
    "pg": "^8.23.1",
    "tsx": "^4.23.15",
    "typescript": "^7.0.2",
    "vitest": "^5.0.3"
  }
}
```

`pnpm-workspace.yaml`
```yaml
packages:
  - "apps/*"
  - "packages/*"
onlyBuiltDependencies:
  - esbuild
```

`.nvmrc` contém apenas `24`.

`.gitignore`
```
node_modules/
dist/
coverage/
.env
*.log
.DS_Store
```

`.editorconfig`
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
indent_style = space
indent_size = 2
insert_final_newline = true
trim_trailing_whitespace = true
```

`.env.example`
```ini
# Copie para .env (cp .env.example .env). Valores apenas para desenvolvimento local.
POSTGRES_PASSWORD=postgres_dev_pw
TRACKSYS_OWNER_PASSWORD=owner_dev_pw
TRACKSYS_APP_PASSWORD=app_dev_pw
TRACKSYS_INGEST_PASSWORD=ingest_dev_pw
DATABASE_URL=postgres://tracksys_owner:owner_dev_pw@127.0.0.1:54329/tracksys?sslmode=disable
DATABASE_URL_APP=postgres://tracksys_app:app_dev_pw@127.0.0.1:54329/tracksys?sslmode=disable
DATABASE_URL_ADMIN=postgres://postgres:postgres_dev_pw@127.0.0.1:54329/tracksys?sslmode=disable
```

`tsconfig.base.json`
```json
{
  "compilerOptions": {
    "target": "ES2023",
    "lib": ["ES2023"],
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "types": ["node"],
    "noEmit": true
  }
}
```

`biome.json`
```json
{
  "$schema": "./node_modules/@biomejs/biome/configuration_schema.json",
  "files": {
    "includes": ["**", "!**/node_modules", "!**/dist", "!**/coverage"]
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 120
  },
  "linter": {
    "enabled": true,
    "rules": {
      "preset": "recommended",
      "suspicious": {
        "noFocusedTests": "error",
        "noSkippedTests": "error"
      }
    }
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "semicolons": "asNeeded"
    }
  }
}
```

### (2) Banco local — conteúdo exato

`docker-compose.yml`
```yaml
name: tracksys
services:
  db:
    build: ./infra/db
    image: tracksys-db:17
    command: ['postgres', '-c', 'timezone=UTC', '-c', 'log_timezone=UTC']
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres_dev_pw}
      TRACKSYS_OWNER_PASSWORD: ${TRACKSYS_OWNER_PASSWORD:-owner_dev_pw}
      TRACKSYS_APP_PASSWORD: ${TRACKSYS_APP_PASSWORD:-app_dev_pw}
      TRACKSYS_INGEST_PASSWORD: ${TRACKSYS_INGEST_PASSWORD:-ingest_dev_pw}
    ports:
      - "127.0.0.1:54329:5432"
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U postgres -d tracksys"]
      interval: 2s
      timeout: 3s
      retries: 30
volumes:
  db-data:
```

`infra/db/Dockerfile` (multi-arquitetura: o mesmo arquivo serve amd64 no notebook/CI e arm64 na VM Oracle)
```dockerfile
FROM postgres:17-bookworm
RUN apt-get update \
  && apt-get install -y --no-install-recommends postgresql-17-postgis-3 postgresql-17-postgis-3-scripts \
  && rm -rf /var/lib/apt/lists/*
COPY initdb/ /docker-entrypoint-initdb.d/
```

`infra/db/initdb/00-init.sh` (roda uma única vez, na criação do volume; cria os papéis de banco e o banco `tracksys`)
```bash
#!/usr/bin/env bash
# Executado uma única vez, na criação do volume, pelo entrypoint oficial do Postgres.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL
  CREATE ROLE tracksys_owner LOGIN PASSWORD '${TRACKSYS_OWNER_PASSWORD}';
  CREATE ROLE tracksys_app LOGIN PASSWORD '${TRACKSYS_APP_PASSWORD}' NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  CREATE ROLE tracksys_ingest LOGIN PASSWORD '${TRACKSYS_INGEST_PASSWORD}' NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  CREATE DATABASE tracksys OWNER tracksys_owner;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname tracksys <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS postgis;
  CREATE EXTENSION IF NOT EXISTS btree_gist;
  REVOKE ALL ON DATABASE tracksys FROM PUBLIC;
  GRANT CONNECT ON DATABASE tracksys TO tracksys_app, tracksys_ingest;
EOSQL
```

Papéis criados: `tracksys_owner` (dono do banco e do schema; usado pelas migrations), `tracksys_app` (API e worker; `NOBYPASSRLS`, nunca dono de tabela), `tracksys_ingest` (reservado para a ingestão, T-005). O superusuário `postgres` só é usado no meta-teste do catálogo e em manutenção.

### (3) Migration — SQL exato

`packages/db/migrations/20261007120000_fundacao_isolamento.sql`
```sql
-- migrate:up
-- T-001 — Fundação do isolamento em 3 níveis (plataforma → operadora → cliente).
-- Requisitos: ADR-004, INV-07, regras de catálogo CAT-01..CAT-06.
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

CREATE SCHEMA app;

-- Contexto de segurança por transação (definido com set_config(..., true)).
-- As três funções falham fechado: sem contexto, devolvem NULL / array vazio.
CREATE FUNCTION app.current_operator_id() RETURNS uuid
  LANGUAGE sql STABLE
  AS $$ SELECT nullif(current_setting('app.operator_id', true), '')::uuid $$;

CREATE FUNCTION app.current_scope() RETURNS text
  LANGUAGE sql STABLE
  AS $$
    SELECT CASE current_setting('app.scope', true)
      WHEN 'operator' THEN 'operator'
      WHEN 'tenant' THEN 'tenant'
      ELSE NULL
    END
  $$;

CREATE FUNCTION app.current_tenant_ids() RETURNS uuid[]
  LANGUAGE sql STABLE
  AS $$ SELECT coalesce(nullif(current_setting('app.tenant_ids', true), '')::uuid[], '{}'::uuid[]) $$;

-- Operadora (raiz do isolamento).
-- rls: D
CREATE TABLE app.operator (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  legal_name text NOT NULL CHECK (length(legal_name) BETWEEN 1 AND 200),
  display_name text NOT NULL CHECK (length(display_name) BETWEEN 1 AND 120),
  document text NULL CHECK (document IS NULL OR document ~ '^[0-9]{11}$|^[0-9]{14}$'),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'closed')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Marca dinâmica exibida no app do cliente final.
-- rls: C
CREATE TABLE app.operator_brand (
  operator_id uuid PRIMARY KEY REFERENCES app.operator (id),
  display_name text NOT NULL CHECK (length(display_name) BETWEEN 1 AND 120),
  logo_url text NULL CHECK (logo_url IS NULL OR logo_url ~ '^https://'),
  primary_color text NOT NULL DEFAULT '#3B82F6' CHECK (primary_color ~ '^#[0-9A-Fa-f]{6}$'),
  secondary_color text NULL CHECK (secondary_color IS NULL OR secondary_color ~ '^#[0-9A-Fa-f]{6}$'),
  support_whatsapp text NULL CHECK (support_whatsapp IS NULL OR support_whatsapp ~ '^\+[1-9][0-9]{7,14}$'),
  support_phone text NULL CHECK (support_phone IS NULL OR support_phone ~ '^\+[1-9][0-9]{7,14}$'),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Cliente final da operadora (pessoa física ou jurídica).
-- rls: C
CREATE TABLE app.tenant (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL REFERENCES app.operator (id),
  kind text NOT NULL CHECK (kind IN ('person', 'company')),
  display_name text NOT NULL CHECK (length(display_name) BETWEEN 1 AND 200),
  document text NULL CHECK (document IS NULL OR document ~ '^[0-9]{11}$|^[0-9]{14}$'),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended_commercial', 'closed')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT tenant_operator_id_id_key UNIQUE (operator_id, id)
);
CREATE INDEX tenant_operator_id_idx ON app.tenant (operator_id);

-- Veículo do cliente. FK composta impede apontar para cliente de outra operadora.
-- rls: A
CREATE TABLE app.vehicle (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  plate text NULL CHECK (plate IS NULL OR plate ~ '^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$'),
  kind text NOT NULL CHECK (kind IN ('car', 'motorcycle', 'truck', 'other')),
  make text NULL,
  model text NULL,
  color text NULL,
  year smallint NULL CHECK (year IS NULL OR year BETWEEN 1950 AND 2100),
  nickname text NULL,
  archived_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT vehicle_tenant_fk FOREIGN KEY (operator_id, tenant_id) REFERENCES app.tenant (operator_id, id),
  CONSTRAINT vehicle_operator_tenant_id_key UNIQUE (operator_id, tenant_id, id)
);
CREATE INDEX vehicle_operator_tenant_idx ON app.vehicle (operator_id, tenant_id);
CREATE UNIQUE INDEX vehicle_active_plate_per_operator_key
  ON app.vehicle (operator_id, plate)
  WHERE archived_at IS NULL AND plate IS NOT NULL;

-- RLS habilitada e forçada em todas as tabelas (CAT-01).
ALTER TABLE app.operator ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.operator FORCE ROW LEVEL SECURITY;
ALTER TABLE app.operator_brand ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.operator_brand FORCE ROW LEVEL SECURITY;
ALTER TABLE app.tenant ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.tenant FORCE ROW LEVEL SECURITY;
ALTER TABLE app.vehicle ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.vehicle FORCE ROW LEVEL SECURITY;

-- operator: equipe da operadora lê e escreve a própria linha; cliente só lê.
CREATE POLICY operator_staff_all ON app.operator FOR ALL
  USING (id = app.current_operator_id() AND app.current_scope() = 'operator')
  WITH CHECK (id = app.current_operator_id() AND app.current_scope() = 'operator');
CREATE POLICY operator_tenant_read ON app.operator FOR SELECT
  USING (id = app.current_operator_id() AND app.current_scope() = 'tenant');

-- operator_brand: mesmo padrão (o app do cliente precisa ler a marca).
CREATE POLICY operator_brand_staff_all ON app.operator_brand FOR ALL
  USING (operator_id = app.current_operator_id() AND app.current_scope() = 'operator')
  WITH CHECK (operator_id = app.current_operator_id() AND app.current_scope() = 'operator');
CREATE POLICY operator_brand_tenant_read ON app.operator_brand FOR SELECT
  USING (operator_id = app.current_operator_id() AND app.current_scope() = 'tenant');

-- tenant: equipe da operadora gerencia; cliente só lê o próprio registro.
CREATE POLICY tenant_staff_all ON app.tenant FOR ALL
  USING (operator_id = app.current_operator_id() AND app.current_scope() = 'operator')
  WITH CHECK (operator_id = app.current_operator_id() AND app.current_scope() = 'operator');
CREATE POLICY tenant_self_read ON app.tenant FOR SELECT
  USING (
    operator_id = app.current_operator_id()
    AND app.current_scope() = 'tenant'
    AND id = ANY (app.current_tenant_ids())
  );

-- vehicle: política padrão de tabela de cliente.
CREATE POLICY vehicle_isolation ON app.vehicle FOR ALL
  USING (
    operator_id = app.current_operator_id()
    AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids()))
  )
  WITH CHECK (
    operator_id = app.current_operator_id()
    AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids()))
  );

-- Privilégios do papel da aplicação (sem DELETE: desativação é por status/archived_at).
GRANT USAGE ON SCHEMA app TO tracksys_app;
GRANT SELECT, INSERT, UPDATE ON app.operator, app.operator_brand, app.tenant, app.vehicle TO tracksys_app;
GRANT EXECUTE ON FUNCTION app.current_operator_id(), app.current_scope(), app.current_tenant_ids() TO tracksys_app;

-- migrate:down
DROP SCHEMA app CASCADE;
```

Regras que este SQL materializa e que **toda migration futura** deve seguir:
- Contexto por transação com `set_config(..., true)`; as três funções `app.current_*` falham fechado (sem contexto, nada é visível).
- Tabela de cliente: `operator_id` e `tenant_id` NOT NULL, FK composta `(operator_id, tenant_id) → app.tenant (operator_id, id)`, política padrão `operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids()))` em `USING` e `WITH CHECK`.
- Tabela da operadora: política `FOR ALL` restrita ao escopo `operator` + política `FOR SELECT` para o escopo `tenant` quando o cliente precisar ler (ex.: marca).
- Sem `GRANT DELETE` para `tracksys_app`: desativação é por `status`/`archived_at`.
- Toda migration começa com `SET LOCAL lock_timeout = '5s'; SET LOCAL statement_timeout = '60s';` (o dbmate roda cada arquivo numa transação) e cada `CREATE TABLE` do schema `app` leva o comentário `-- rls: <tipo>` ([04](../docs/spec/04-dominio-e-dados.md) §4.2).
- FK composta liga as colunas **na mesma posição**: `(operator_id, tenant_id) → (operator_id, id)` de `app.tenant`; `(operator_id, tenant_id, vehicle_id) → (operator_id, tenant_id, id)` de `app.vehicle`.

### (4) Pacote `@tracksys/db`

`packages/db/package.json`
```json
{
  "name": "@tracksys/db",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "exports": {
    ".": "./src/index.ts"
  },
  "scripts": {
    "typecheck": "tsc -p tsconfig.json"
  },
  "dependencies": {
    "pg": "^8.23.1",
    "zod": "^4.6.5"
  },
  "devDependencies": {
    "@types/node": "^24.19.1",
    "@types/pg": "^8.23.1",
    "typescript": "^7.0.2"
  }
}
```

`packages/db/tsconfig.json`
```json
{
  "extends": "../../tsconfig.base.json",
  "include": ["src/**/*.ts", "scripts/**/*.ts"]
}
```

`packages/db/catalog-allowlist.json` (exceções exigem justificativa ≥ 10 caracteres e revisão N0)
```json
{
  "rlsExempt": {},
  "nullableTenantId": {},
  "withoutOperatorId": {},
  "appendOnly": ["audit_log", "command_event", "access_log"]
}
```

**API pública** (`packages/db/src/index.ts` exporta exatamente estes nomes; os testes congelados dependem deles):

| Export | Contrato |
|---|---|
| `loadDbEnv(): DbEnv` | Se `DATABASE_URL` não estiver no ambiente e existir `.env` no diretório atual, carrega com `process.loadEnvFile('.env')`. Valida com Zod que `DATABASE_URL` (dono), `DATABASE_URL_APP` (aplicação) e `DATABASE_URL_ADMIN` (superusuário local, só testes) são URLs `postgres://` ou `postgresql://`; lança erro se faltar algum. `type DbEnv` é exportado. |
| `type DbContext` | União discriminada por `scope` de objetos **estritos** (`z.strictObject`): `{ scope: 'operator'; operatorId: string }` ou `{ scope: 'tenant'; operatorId: string; tenantIds: string[] }`. Chave desconhecida (ex.: `tenantIds` no escopo `operator`) é erro, nunca descartada em silêncio. |
| `withContext<T>(pool: pg.Pool, context: DbContext, fn: (client: pg.PoolClient) => Promise<T>): Promise<T>` | 1) Valida `context` com Zod **antes** de abrir conexão: `operatorId` e cada `tenantIds[i]` são UUID (`z.uuid()`); `tenantIds` tem de 1 a 1000 itens no escopo `tenant`. Entrada inválida → rejeita sem tocar no banco. 2) Pega uma conexão do pool, `BEGIN`, executa `SELECT set_config('app.operator_id', $1, true), set_config('app.scope', $2, true), set_config('app.tenant_ids', $3, true)` com `$3 = '{id1,id2}'` no escopo `tenant` e `''` no escopo `operator`. 3) Chama `fn(client)`; sucesso → `COMMIT` e devolve o resultado; se o `COMMIT` responder `ROLLBACK` (`result.command === 'ROLLBACK'`: erro engolido dentro do callback abortou a transação), lança `Error` com a palavra `abortada`. Erro → `ROLLBACK` e relança o mesmo erro. 4) No `finally`, roda `RESET ALL` (desfaz `set_config(..., false)` feito no callback) e libera a conexão; se o `ROLLBACK` ou o `RESET ALL` falhar, libera com `client.release(erro)`, o que descarta a conexão em vez de devolvê-la ao pool. |
| `CatalogAllowlistSchema` | Zod `z.strictObject` (chave desconhecida = erro): `{ rlsExempt, nullableTenantId, withoutOperatorId: Record<string, string(min 10)>; appendOnly: string[] }`. A chave `securityDefiner` entra com a CAT-07 (T-005 ou T-006), que estende este schema no mesmo PR. |
| `type CatalogAllowlist`, `type CatalogRule` (`'CAT-01'` … `'CAT-06'`), `interface CatalogViolation { rule: CatalogRule; object: string; message: string }` | Tipos. |
| `loadCatalogAllowlist(): CatalogAllowlist` | Lê `packages/db/catalog-allowlist.json` relativo ao módulo (`new URL('../catalog-allowlist.json', import.meta.url)`) e valida com o schema. |
| `runCatalogChecks(db: Pick<pg.ClientBase, 'query'> \| Pick<pg.Pool, 'query'>, allowlist: CatalogAllowlist): Promise<CatalogViolation[]>` | Executa as consultas abaixo no catálogo e devolve **todas** as violações (lista vazia = OK). Deve funcionar com um `Pool` ou com um `Client` dentro de uma transação aberta (o meta-teste cria tabelas e verifica antes do `ROLLBACK`). |

**Formato de `object` nas violações** (os testes comparam texto): `app.<tabela>` para CAT-01, CAT-02, CAT-03, CAT-05 (tabela) e CAT-06; `app.<tabela>.<nome_da_constraint>` para CAT-04 (uma violação por par de colunas faltante); para CAT-05, `app.<função>()` (função), `schema app` (schema) e `tracksys_app` (atributo do papel ou herança; a mensagem de herança cita o nome do papel herdado).

**Consultas de referência por regra** (schema `app`; `relkind IN ('r','p')`):

| Regra | O que é violação | Consulta (resumo exato do critério) |
|---|---|---|
| CAT-01 | Tabela sem RLS habilitada **e** forçada, fora de `rlsExempt` | `NOT (c.relrowsecurity AND c.relforcerowsecurity)` em `pg_class` (inclui partições) |
| CAT-02 | Tabela com RLS e sem nenhuma política | `c.relrowsecurity AND NOT c.relispartition AND NOT EXISTS (SELECT 1 FROM pg_policy p WHERE p.polrelid = c.oid)` |
| CAT-03 | Tabela sem `operator_id` NOT NULL, exceto `app.operator` e as chaves de `withoutOperatorId`; ou com `tenant_id` anulável fora de `nullableTenantId` | `pg_attribute` de `operator_id` e `tenant_id` (LEFT JOIN) olhando `attnotnull`; ignora partições. Uma violação por problema. |
| CAT-04 | FK (`contype = 'f'`, `conparentid = 0`), exceto para `app.operator`, que não liga **na mesma posição** `operator_id → operator_id` e `tenant_id → tenant_id` quando a tabela referenciada tem essas colunas; FK para `app.tenant` também precisa de `tenant_id → id` | pares `unnest(con.conkey, con.confkey)` com `pg_attribute` dos dois lados, comparados com o conjunto exigido. Uma violação por par faltante (coluna trocada conta como faltante). |
| CAT-05 | `tracksys_app` inexistente, superusuário ou `BYPASSRLS`; membro, direto ou herdado, de papel superusuário, com `BYPASSRLS` ou dono de objeto do schema `app`; ou dono de tabela, função ou do próprio schema `app` | `pg_roles`, `pg_has_role('tracksys_app'::name, r.oid, 'MEMBER')`, `pg_class.relowner`, `pg_proc.proowner`, `pg_namespace.nspowner` |
| CAT-06 | Tabela listada em `appendOnly` que existe e em que `tracksys_app` tem `UPDATE` (inclusive só em uma coluna), `DELETE` ou `TRUNCATE` | `to_regclass('app.<t>')`, `has_any_column_privilege(..., 'UPDATE')` e `has_table_privilege(..., 'DELETE' / 'TRUNCATE')` |

`packages/db/scripts/check-catalog.ts`: conecta com `DATABASE_URL` (via `loadDbEnv()`), roda `runCatalogChecks(client, loadCatalogAllowlist())`, imprime `Catálogo OK: nenhuma violação de CAT-01..CAT-06.` quando vazio; senão imprime uma linha por violação no formato `CAT-0X <object>: <message>` em stderr e termina com código de saída 1. Sempre fecha a conexão.

Estilo dos arquivos TypeScript: ESM, imports com extensão `.ts` entre arquivos locais (ex.: `from './context.ts'`), `import pg from 'pg'` para valores e `import type { Pool, PoolClient } from 'pg'` para tipos, Zod 4 (`z.uuid()`, `z.discriminatedUnion`). Rode `pnpm format` antes de commitar.

### (5) Testes de aceite congelados — copiar sem alterar

`tests/tsconfig.json`
```json
{
  "extends": "../tsconfig.base.json",
  "include": ["**/*.ts"]
}
```

`tests/vitest.config.ts`
```ts
import { existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

const root = fileURLToPath(new URL('..', import.meta.url))
if (!process.env.DATABASE_URL && existsSync(`${root}.env`)) {
  process.loadEnvFile(`${root}.env`)
}

export default defineConfig({
  test: {
    root,
    include: ['tests/acceptance/**/*.test.ts'],
    testTimeout: 20_000,
    hookTimeout: 30_000,
    fileParallelism: false,
  },
})
```

`tests/acceptance/T-001/world.ts`
```ts
import { randomUUID } from 'node:crypto'
import { withContext } from '@tracksys/db'
import type { Pool } from 'pg'

export interface SeededOperator {
  operatorId: string
  tenantIds: string[]
  vehicleIds: string[]
}

/** Cria uma operadora com N clientes e 1 veículo por cliente, usando o papel da aplicação. */
export async function seedOperator(app: Pool, name: string, tenants: number): Promise<SeededOperator> {
  const operatorId = randomUUID()
  return withContext(app, { scope: 'operator', operatorId }, async (c) => {
    await c.query('INSERT INTO app.operator (id, legal_name, display_name) VALUES ($1, $2, $2)', [operatorId, name])
    const tenantIds: string[] = []
    const vehicleIds: string[] = []
    for (let i = 1; i <= tenants; i++) {
      const tenantId = randomUUID()
      const vehicleId = randomUUID()
      await c.query("INSERT INTO app.tenant (id, operator_id, kind, display_name) VALUES ($1, $2, 'person', $3)", [
        tenantId,
        operatorId,
        `Cliente ${i} de ${name}`,
      ])
      await c.query("INSERT INTO app.vehicle (id, operator_id, tenant_id, kind) VALUES ($1, $2, $3, 'car')", [
        vehicleId,
        operatorId,
        tenantId,
      ])
      tenantIds.push(tenantId)
      vehicleIds.push(vehicleId)
    }
    return { operatorId, tenantIds, vehicleIds }
  })
}
```

`tests/acceptance/T-001/isolation.test.ts`
```ts
import { randomUUID } from 'node:crypto'
import { loadDbEnv, withContext } from '@tracksys/db'
import pg from 'pg'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { type SeededOperator, seedOperator } from './world.ts'

const env = loadDbEnv()
const app = new pg.Pool({ connectionString: env.DATABASE_URL_APP, max: 4 })

let a: SeededOperator
let b: SeededOperator

beforeAll(async () => {
  a = await seedOperator(app, 'Operadora A', 2)
  b = await seedOperator(app, 'Operadora B', 2)
})

afterAll(async () => {
  await app.end()
})

const ids = (rows: { id: string }[]) => rows.map((r) => r.id).sort()

describe('T-001 isolamento em 3 níveis (INV-07)', () => {
  it('ISO-01: cliente A1 vê somente o próprio veículo', async () => {
    const res = await withContext(
      app,
      { scope: 'tenant', operatorId: a.operatorId, tenantIds: [a.tenantIds[0] as string] },
      (c) => c.query<{ id: string }>('SELECT id FROM app.vehicle'),
    )
    expect(ids(res.rows)).toEqual([a.vehicleIds[0]])
  })

  it('ISO-01b: lista de tenants de outra operadora não abre nada', async () => {
    const res = await withContext(
      app,
      { scope: 'tenant', operatorId: a.operatorId, tenantIds: [b.tenantIds[0] as string] },
      (c) => c.query<{ id: string }>('SELECT id FROM app.vehicle'),
    )
    expect(res.rows).toEqual([])
  })

  it('ISO-02: escopo operadora A vê todos os clientes de A e nada de B', async () => {
    const res = await withContext(app, { scope: 'operator', operatorId: a.operatorId }, (c) =>
      c.query<{ id: string }>('SELECT id FROM app.vehicle'),
    )
    expect(ids(res.rows)).toEqual([...a.vehicleIds].sort())
    for (const v of b.vehicleIds) expect(ids(res.rows)).not.toContain(v)
  })

  it('ISO-02b: escopo operadora B vê os 2 clientes de B e nada de A (2 operadoras × 2 clientes)', async () => {
    const res = await withContext(app, { scope: 'operator', operatorId: b.operatorId }, (c) =>
      c.query<{ id: string }>('SELECT id FROM app.tenant'),
    )
    expect(ids(res.rows)).toEqual([...b.tenantIds].sort())
  })

  it('ISO-02c: membro de 2 clientes da mesma operadora vê os veículos dos dois', async () => {
    const res = await withContext(app, { scope: 'tenant', operatorId: a.operatorId, tenantIds: a.tenantIds }, (c) =>
      c.query<{ id: string }>('SELECT id FROM app.vehicle'),
    )
    expect(ids(res.rows)).toEqual([...a.vehicleIds].sort())
  })

  it('ISO-03: sem contexto, nenhuma linha é visível', async () => {
    for (const table of ['app.operator', 'app.operator_brand', 'app.tenant', 'app.vehicle']) {
      const res = await app.query<{ n: number }>(`SELECT count(*)::int AS n FROM ${table}`)
      expect(res.rows[0]?.n, table).toBe(0)
    }
  })

  it('ISO-04: INSERT com operator_id de outra operadora é barrado pela RLS', async () => {
    await expect(
      withContext(app, { scope: 'operator', operatorId: a.operatorId }, (c) =>
        c.query("INSERT INTO app.vehicle (operator_id, tenant_id, kind) VALUES ($1, $2, 'car')", [
          b.operatorId,
          b.tenantIds[0],
        ]),
      ),
    ).rejects.toMatchObject({ code: '42501' })
  })

  it('ISO-04b: cliente A1 não cria veículo para o cliente A2', async () => {
    await expect(
      withContext(app, { scope: 'tenant', operatorId: a.operatorId, tenantIds: [a.tenantIds[0] as string] }, (c) =>
        c.query("INSERT INTO app.vehicle (operator_id, tenant_id, kind) VALUES ($1, $2, 'car')", [
          a.operatorId,
          a.tenantIds[1],
        ]),
      ),
    ).rejects.toMatchObject({ code: '42501' })
  })

  it('ISO-04c: cliente A1 não move o próprio veículo para o cliente A2', async () => {
    await expect(
      withContext(app, { scope: 'tenant', operatorId: a.operatorId, tenantIds: [a.tenantIds[0] as string] }, (c) =>
        c.query('UPDATE app.vehicle SET tenant_id = $1 WHERE id = $2', [a.tenantIds[1], a.vehicleIds[0]]),
      ),
    ).rejects.toMatchObject({ code: '42501' })
  })

  it('ISO-05: FK composta impede veículo da operadora A apontar para cliente da B', async () => {
    await expect(
      withContext(app, { scope: 'operator', operatorId: a.operatorId }, (c) =>
        c.query("INSERT INTO app.vehicle (operator_id, tenant_id, kind) VALUES ($1, $2, 'car')", [
          a.operatorId,
          b.tenantIds[0],
        ]),
      ),
    ).rejects.toMatchObject({ code: '23503' })
  })

  it('ISO-07: cliente lê o próprio tenant e não consegue alterá-lo', async () => {
    const ctx = { scope: 'tenant' as const, operatorId: a.operatorId, tenantIds: [a.tenantIds[0] as string] }
    const seen = await withContext(app, ctx, (c) => c.query<{ id: string }>('SELECT id FROM app.tenant'))
    expect(ids(seen.rows)).toEqual([a.tenantIds[0]])
    const upd = await withContext(app, ctx, (c) =>
      c.query("UPDATE app.tenant SET display_name = 'invadido' WHERE id = $1", [a.tenantIds[0]]),
    )
    expect(upd.rowCount).toBe(0)
  })

  it('ISO-07b: operadora A não altera cliente da operadora B', async () => {
    const upd = await withContext(app, { scope: 'operator', operatorId: a.operatorId }, (c) =>
      c.query("UPDATE app.tenant SET display_name = 'invadido' WHERE id = ANY($1::uuid[])", [b.tenantIds]),
    )
    expect(upd.rowCount).toBe(0)
  })

  it('ISO-08: o papel da aplicação não tem DELETE', async () => {
    await expect(
      withContext(app, { scope: 'operator', operatorId: a.operatorId }, (c) =>
        c.query('DELETE FROM app.vehicle WHERE id = $1', [a.vehicleIds[0]]),
      ),
    ).rejects.toMatchObject({ code: '42501' })
  })

  it('ISO-09: operadora inexistente no contexto não enxerga nada', async () => {
    const res = await withContext(app, { scope: 'operator', operatorId: randomUUID() }, (c) =>
      c.query<{ n: number }>('SELECT count(*)::int AS n FROM app.vehicle'),
    )
    expect(res.rows[0]?.n).toBe(0)
  })
})
```

`tests/acceptance/T-001/context.test.ts`
```ts
import { randomUUID } from 'node:crypto'
import { loadDbEnv, withContext } from '@tracksys/db'
import pg from 'pg'
import { afterAll, describe, expect, it } from 'vitest'
import { seedOperator } from './world.ts'

const env = loadDbEnv()
const single = new pg.Pool({ connectionString: env.DATABASE_URL_APP, max: 1 })

afterAll(async () => {
  await single.end()
})

describe('T-001 withContext', () => {
  it('rejeita escopo tenant sem tenantIds antes de tocar no banco', async () => {
    await expect(
      withContext(single, { scope: 'tenant', operatorId: randomUUID(), tenantIds: [] }, async () => 1),
    ).rejects.toThrow()
  })

  it('rejeita operatorId que não é uuid', async () => {
    await expect(withContext(single, { scope: 'operator', operatorId: 'nao-e-uuid' }, async () => 1)).rejects.toThrow()
  })

  it('rejeita chave desconhecida no contexto (objeto estrito)', async () => {
    const ctx = { scope: 'operator', operatorId: randomUUID(), tenantIds: [randomUUID()] }
    await expect(withContext(single, ctx as never, async () => 1)).rejects.toThrow()
  })

  it('o contexto não vaza para a próxima transação da mesma conexão', async () => {
    const seeded = await seedOperator(single, 'Operadora Vazamento', 1)
    const inside = await withContext(single, { scope: 'operator', operatorId: seeded.operatorId }, (c) =>
      c.query<{ n: number }>('SELECT count(*)::int AS n FROM app.vehicle'),
    )
    expect(inside.rows[0]?.n).toBe(1)
    const outside = await single.query<{ n: number }>('SELECT count(*)::int AS n FROM app.vehicle')
    expect(outside.rows[0]?.n).toBe(0)
  })

  it('erro dentro do callback desfaz a transação inteira', async () => {
    const seeded = await seedOperator(single, 'Operadora Rollback', 1)
    const ctx = { scope: 'operator' as const, operatorId: seeded.operatorId }
    await expect(
      withContext(single, ctx, async (c) => {
        await c.query("INSERT INTO app.vehicle (operator_id, tenant_id, kind) VALUES ($1, $2, 'motorcycle')", [
          seeded.operatorId,
          seeded.tenantIds[0],
        ])
        throw new Error('falha proposital')
      }),
    ).rejects.toThrow('falha proposital')
    const res = await withContext(single, ctx, (c) =>
      c.query<{ n: number }>("SELECT count(*)::int AS n FROM app.vehicle WHERE kind = 'motorcycle'"),
    )
    expect(res.rows[0]?.n).toBe(0)
  })

  it('set_config de sessão feito dentro do callback não vaza para o próximo uso da conexão', async () => {
    const seeded = await seedOperator(single, 'Operadora Sessão', 1)
    await withContext(single, { scope: 'operator', operatorId: randomUUID() }, (c) =>
      c.query("SELECT set_config('app.operator_id', $1, false), set_config('app.scope', 'operator', false)", [
        seeded.operatorId,
      ]),
    )
    const after = await single.query<{ n: number; op: string | null }>(
      "SELECT (SELECT count(*)::int FROM app.vehicle) AS n, nullif(current_setting('app.operator_id', true), '') AS op",
    )
    expect(after.rows[0]).toEqual({ n: 0, op: null })
  })

  it('erro engolido dentro do callback não vira sucesso silencioso', async () => {
    const seeded = await seedOperator(single, 'Operadora Abortada', 1)
    const ctx = { scope: 'operator' as const, operatorId: seeded.operatorId }
    await expect(
      withContext(single, ctx, async (c) => {
        await c
          .query("INSERT INTO app.vehicle (operator_id, tenant_id, kind) VALUES ($1, $2, 'invalido')", [
            seeded.operatorId,
            seeded.tenantIds[0],
          ])
          .catch(() => undefined)
        return 'ok'
      }),
    ).rejects.toThrow('abortada')
    const res = await withContext(single, ctx, (c) =>
      c.query<{ n: number }>('SELECT count(*)::int AS n FROM app.vehicle'),
    )
    expect(res.rows[0]?.n).toBe(1)
  })
})
```

`tests/acceptance/T-001/catalog.test.ts`
```ts
import { loadCatalogAllowlist, loadDbEnv, runCatalogChecks } from '@tracksys/db'
import pg from 'pg'
import { afterAll, describe, expect, it } from 'vitest'

const env = loadDbEnv()
const admin = new pg.Pool({ connectionString: env.DATABASE_URL_ADMIN, max: 2 })
const allowlist = loadCatalogAllowlist()

afterAll(async () => {
  await admin.end()
})

describe('T-001 verificador de catálogo (CAT-01..CAT-06)', () => {
  it('o schema migrado não tem nenhuma violação', async () => {
    expect(await runCatalogChecks(admin, allowlist)).toEqual([])
  })

  it('ISO-06: o verificador aponta cada tipo de violação (meta-teste, tudo desfeito no fim)', async () => {
    const client = await admin.connect()
    try {
      await client.query('BEGIN')
      // CAT-01: tabela sem RLS.
      await client.query('CREATE TABLE app.tmp_sem_rls (id int PRIMARY KEY, operator_id uuid NOT NULL)')
      // CAT-02: RLS sem política.
      await client.query('CREATE TABLE app.tmp_sem_politica (id int PRIMARY KEY, operator_id uuid NOT NULL)')
      await client.query('ALTER TABLE app.tmp_sem_politica ENABLE ROW LEVEL SECURITY')
      await client.query('ALTER TABLE app.tmp_sem_politica FORCE ROW LEVEL SECURITY')
      // CAT-03: tenant_id sem operator_id.
      await client.query('CREATE TABLE app.tmp_sem_operator (id int PRIMARY KEY, tenant_id uuid NOT NULL)')
      await client.query('ALTER TABLE app.tmp_sem_operator ENABLE ROW LEVEL SECURITY')
      await client.query('ALTER TABLE app.tmp_sem_operator FORCE ROW LEVEL SECURITY')
      await client.query('CREATE POLICY p ON app.tmp_sem_operator USING (false)')
      // CAT-04: FK simples para tabela de cliente.
      await client.query(
        'CREATE TABLE app.tmp_fk_ruim (id int PRIMARY KEY, operator_id uuid NOT NULL, tenant_id uuid NOT NULL, vehicle_id uuid REFERENCES app.vehicle (id))',
      )
      await client.query('ALTER TABLE app.tmp_fk_ruim ENABLE ROW LEVEL SECURITY')
      await client.query('ALTER TABLE app.tmp_fk_ruim FORCE ROW LEVEL SECURITY')
      await client.query('CREATE POLICY p ON app.tmp_fk_ruim USING (false)')
      // CAT-03: tabela sem operator_id fora de withoutOperatorId (e a mesma forma, listada, não acusa).
      for (const name of ['tmp_sem_escopo', 'tmp_plataforma']) {
        await client.query(`CREATE TABLE app.${name} (id int PRIMARY KEY)`)
        await client.query(`ALTER TABLE app.${name} ENABLE ROW LEVEL SECURITY`)
        await client.query(`ALTER TABLE app.${name} FORCE ROW LEVEL SECURITY`)
        await client.query(`CREATE POLICY p ON app.${name} USING (false)`)
      }
      // CAT-04: FK composta com as colunas trocadas (tenant_id → operator_id, operator_id → id).
      await client.query(
        'CREATE TABLE app.tmp_fk_trocada (id int PRIMARY KEY, operator_id uuid NOT NULL, tenant_id uuid NOT NULL, CONSTRAINT tmp_fk_trocada_fk FOREIGN KEY (tenant_id, operator_id) REFERENCES app.tenant (operator_id, id))',
      )
      // Controle positivo: FK composta correta para app.vehicle não acusa.
      await client.query(
        'CREATE TABLE app.tmp_fk_ok (id int PRIMARY KEY, operator_id uuid NOT NULL, tenant_id uuid NOT NULL, vehicle_id uuid NOT NULL, CONSTRAINT tmp_fk_ok_fk FOREIGN KEY (operator_id, tenant_id, vehicle_id) REFERENCES app.vehicle (operator_id, tenant_id, id))',
      )
      for (const name of ['tmp_fk_trocada', 'tmp_fk_ok']) {
        await client.query(`ALTER TABLE app.${name} ENABLE ROW LEVEL SECURITY`)
        await client.query(`ALTER TABLE app.${name} FORCE ROW LEVEL SECURITY`)
        await client.query(`CREATE POLICY p ON app.${name} USING (false)`)
      }
      // CAT-05: papel da aplicação dono de tabela e membro do papel dono do schema.
      await client.query('ALTER TABLE app.tmp_fk_ruim OWNER TO tracksys_app')
      await client.query('GRANT tracksys_owner TO tracksys_app')
      // CAT-06: tabelas append-only com UPDATE na tabela e UPDATE só em uma coluna
      // (nomes temporários, para não colidir com tabelas futuras).
      for (const name of ['tmp_append_only', 'tmp_append_col']) {
        await client.query(`CREATE TABLE app.${name} (id int PRIMARY KEY, operator_id uuid NOT NULL)`)
        await client.query(`ALTER TABLE app.${name} ENABLE ROW LEVEL SECURITY`)
        await client.query(`ALTER TABLE app.${name} FORCE ROW LEVEL SECURITY`)
        await client.query(`CREATE POLICY p ON app.${name} USING (false)`)
      }
      await client.query('GRANT SELECT, INSERT, UPDATE ON app.tmp_append_only TO tracksys_app')
      await client.query('GRANT SELECT, INSERT, UPDATE (operator_id) ON app.tmp_append_col TO tracksys_app')

      const metaAllowlist = {
        ...allowlist,
        withoutOperatorId: { ...allowlist.withoutOperatorId, tmp_plataforma: 'tabela de plataforma do meta-teste' },
        appendOnly: [...allowlist.appendOnly, 'tmp_append_only', 'tmp_append_col'],
      }
      const violations = await runCatalogChecks(client, metaAllowlist)
      const found = violations.map((v) => `${v.rule} ${v.object}`)
      expect(found).toContain('CAT-01 app.tmp_sem_rls')
      expect(found).toContain('CAT-02 app.tmp_sem_politica')
      expect(found).toContain('CAT-03 app.tmp_sem_operator')
      expect(found).toContain('CAT-03 app.tmp_sem_escopo')
      expect(found).not.toContain('CAT-03 app.tmp_plataforma')
      expect(found).toContain('CAT-04 app.tmp_fk_ruim.tmp_fk_ruim_vehicle_id_fkey')
      expect(found.filter((f) => f.startsWith('CAT-04 app.tmp_fk_ruim'))).toHaveLength(2)
      expect(found.filter((f) => f === 'CAT-04 app.tmp_fk_trocada.tmp_fk_trocada_fk')).toHaveLength(2)
      expect(found.filter((f) => f.startsWith('CAT-04 app.tmp_fk_ok'))).toEqual([])
      expect(found).toContain('CAT-05 app.tmp_fk_ruim')
      expect(
        violations.some(
          (v) => v.rule === 'CAT-05' && v.object === 'tracksys_app' && v.message.includes('tracksys_owner'),
        ),
      ).toBe(true)
      expect(found).toContain('CAT-06 app.tmp_append_only')
      expect(found).toContain('CAT-06 app.tmp_append_col')
    } finally {
      await client.query('ROLLBACK')
      client.release()
    }
  })
})
```

### (6) CI — conteúdo exato

`.github/workflows/ci.yml`
```yaml
name: ci

on:
  pull_request:
  push:
    branches: [main]

jobs:
  verify:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: cp .env.example .env
      - run: pnpm db:up
      - run: pnpm verify

  acceptance-freeze:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Testes de aceite existentes não podem ser alterados sem o rótulo acceptance-change
        if: ${{ !contains(github.event.pull_request.labels.*.name, 'acceptance-change') }}
        run: |
          git diff --diff-filter=MDR --name-only "origin/${{ github.base_ref }}...HEAD" -- tests/acceptance > changed.txt
          if [ -s changed.txt ]; then
            echo "::error::Arquivos congelados alterados (exige rótulo acceptance-change e aprovação humana):"
            cat changed.txt
            exit 1
          fi
```

O job `acceptance-freeze` bloqueia PR que **modifica, apaga ou renomeia** arquivos já existentes em `tests/acceptance/**` sem o rótulo `acceptance-change`. Adicionar testes de uma tarefa nova é permitido.

## Comandos de verificação (nesta ordem, todos devem passar)

```bash
corepack enable                 # ou: npm i -g pnpm@10.28.0
pnpm install
cp .env.example .env
pnpm db:up                      # build da imagem + Postgres saudável na porta 54329
pnpm verify                     # lint → typecheck → db:migrate → db:rollback → db:migrate → db:check → test:acceptance
```

Resultado esperado de `pnpm verify`: Biome sem erros; `tsc` sem erros; `Applied:`, `Rolled back:` e `Applied:` de novo para `20261007120000_fundacao_isolamento.sql`; `Catálogo OK: nenhuma violação de CAT-01..CAT-06.`; **Test Files 3 passed, Tests 23 passed** (isolamento 14, `withContext` 7, catálogo 2).

## Definição de pronto

- [ ] Todos os arquivos da lista existem, com o conteúdo exato onde este cartão o fornece.
- [ ] `pnpm verify` verde localmente e no CI do PR.
- [ ] Rollback e novo `up` da migration funcionam (já dentro do `pnpm verify`).
- [ ] `tests/acceptance/T-001/**` idêntico ao deste cartão.
- [ ] `pnpm-lock.yaml` commitado.
- [ ] Branch `t-001-fundacao-monorepo-e-isolamento`; PR com título `feat(db): fundação do monorepo e isolamento em 3 níveis (T-001)`, descrição citando INV-07, CAT-01..CAT-06 e risco N0, e revisão cruzada registrada (ver [14](../docs/spec/14-qualidade-e-processo-ia.md)).

## Decisões já tomadas (não pergunte, siga)

| Dúvida provável | Resposta |
|---|---|
| Usar Kysely já? | Não. Kysely entra na T-004. Aqui só `pg`. |
| Criar tabelas além de operator, operator_brand, tenant e vehicle? | Não. Cada tabela nova vem com a tarefa que a usa. |
| Gatilho de `updated_at`? | Não nesta tarefa. |
| Por que `tracksys_app` não tem DELETE? | Desativação é lógica (`status`, `archived_at`); histórico e auditoria não somem. |
| Por que porta 54329? | Evitar conflito com um Postgres local na 5432. |
| Por que PostGIS no init se T-001 não usa? | Paridade com produção; as tarefas de cerca e geometria usam. A imagem é a mesma em dev, CI e VM ARM. |
| Senhas no `.env.example`? | Só desenvolvimento local. Produção usa segredos cifrados ([13](../docs/spec/13-infra-e-operacao.md)). |
| Testes dependem de banco limpo? | Não. Cada teste cria operadoras com UUID aleatório; o meta-teste desfaz tudo com `ROLLBACK`. |
| `pnpm install` pede para aprovar build do esbuild | Já resolvido por `onlyBuiltDependencies` no `pnpm-workspace.yaml`. |
| Biome avisa sobre schema ou preset | Use exatamente o `biome.json` deste cartão (`"preset": "recommended"`, schema do `node_modules`). |
| A versão instalada de uma dependência é mais nova | Mantenha o major do `package.json`; o lockfile fixa o resto. |
| O build da imagem falhou por rede | A imagem precisa do apt do Debian e do PGDG. Em rede restrita, registre no PR e peça liberação. Não troque a imagem nem remova o PostGIS. |
| Identificadores em inglês ou português? | Código e identificadores em inglês; comentários, mensagens de teste e documentação em PT-BR. |
| Commit | Conventional Commits, ex.: `feat(db): ...`, `test(db): ...`, `ci: ...`. |
| Nomes das variáveis de banco? | `DATABASE_URL` (dono: dbmate, `db:check`), `DATABASE_URL_APP` (aplicação e testes), `DATABASE_URL_ADMIN` (superusuário local, só testes e semeadura; nunca em `apps/`). São os nomes canônicos de [03](../docs/spec/03-arquitetura.md) §13; a T-005 acrescenta `DATABASE_URL_INGEST`. |
| Zod em `packages/db`? | Sim: valida ambiente, contexto e allowlist (regra "Zod em toda fronteira" do `AGENTS.md`). |
| Por que `RESET ALL` e não `DISCARD ALL`? | `DISCARD ALL` apaga os prepared statements que o driver guarda por conexão e quebraria o próximo uso. `RESET ALL` limpa os parâmetros de sessão (inclusive `app.*`), que é o que importa para o isolamento. |
| Por que `withoutOperatorId` em vez de deixar passar tabela sem `operator_id`? | Tabela sem coluna de escopo é exceção que precisa de justificativa revisada (N0). As tarefas que criam tabelas de plataforma ou de usuário (ex.: `capability_profile`, `ingest_inbox`, `push_token`) acrescentam a entrada no mesmo PR. |
| Teste com `.only` ou `.skip`? | Proibido: o Biome (`noFocusedTests`, `noSkippedTests`) falha o lint. |
| Quem aplica o rótulo `acceptance-change`? | Só o fundador. Nesta tarefa o CI só exige o rótulo; a checagem de quem o aplicou é da T-019. |
| Conta que abre o PR? | A conta do agente (`versix-agent`, [14](../docs/spec/14-qualidade-e-processo-ia.md)) ou, enquanto ela não existir, a do fundador, registrada na descrição do PR. O merge é sempre do fundador. |
| Fuso horário? | O Postgres local roda com `timezone=UTC` (INV-12); a aplicação grava `timestamptz`. |
