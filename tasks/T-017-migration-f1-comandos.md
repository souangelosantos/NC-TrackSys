# T-017 — Migration do F1 de comandos, chave do aparelho, consentimento e segredos da operadora

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/11/2026) |
| Requisitos | REQ-CMD-004, REQ-CMD-009, REQ-CMD-010, REQ-CMD-020, REQ-CMD-022, REQ-DAD-001, REQ-DAD-003, REQ-SEG-020, REQ-DAD-026, REQ-QLD-011 |
| Invariantes | INV-06, INV-07, INV-08, INV-10, INV-12 |
| Regras de catálogo | CAT-01 a CAT-07 (a CAT-07 e as políticas `*_definer_read` vêm da T-004; esta migration cria uma função `SECURITY DEFINER`, `app.revoke_device_keys(uuid)`, e a acrescenta a `securityDefiner`); ISO-01 a ISO-05 para cada tabela nova |
| Risco de revisão | N0 — migration, RLS, gatilhos e cifra; revisão adversarial de outro fornecedor + leitura humana linha a linha |
| Depende de | T-004 (`app.tg_immutable_columns`, CAT-07, `membership_definer_read`), T-005 (`device`, `device_assignment`, `outbox` e helper de outbox), T-006 (`auth."user"`, `membership`, `audit_log`, `withContext` com `userId` e `app.current_user_id()`), T-016 (pares de transição) |
| Estimativa | 2 sessões de agente |
| Bloqueado por decisão | Nenhuma (DEC-07 só define o valor gravado pela Lider; o CHECK 0–40 é da plataforma) |

## Objetivo

Criar, numa única migration, as tabelas que o F1 de comandos precisa — `command_policy`, `occurrence`, `command`, `command_attempt`, `command_event`, `command_challenge`, `device_key`, `consent`, `operator_secret` — com RLS forçada, políticas por tipo, FK composta, gatilhos de máquina de estados e de imutabilidade, e grants mínimos. Entregar em `packages/db` os helpers transacionais de comando (transição condicional + `command_event` + outbox + NOTIFY) e a cifra AES-256-GCM dos segredos da operadora. Ao final, o banco recusa sozinho transição inválida, segundo comando de relé ativo, segunda ocorrência aberta, teto acima de 40 km/h, chave de aparelho reativada ou escrita por outro usuário, `can_command` ligado por quem não é `tenant_owner` e qualquer escrita fora do escopo.

## Contexto obrigatório

- [06 §3.3, §4.3, §5, §6, §11](../docs/spec/06-comandos-e-bloqueio.md#33-política-da-operadora-command_policy) — DDL de referência, gatilho e regras.
- [04 §1, §3.2, §3.4, §4.2, §4.3, §10](../docs/spec/04-dominio-e-dados.md#1-hierarquia-e-convenções) — convenções, imutabilidade, tipos A–G, migrations.
- [08 §6.1, §6.2, §8 itens 4–5](../docs/spec/08-identidade-e-seguranca.md#61-chave-do-aparelho-cadastro-f1) — `device_key`, `command_challenge`, `operator_secret`.
- [12 §3](../docs/spec/12-cobranca-e-svas.md#3-dados-acréscimos-a-04-6) — `consent` e `tg_consent_guard`.
- [T-001](T-001-fundacao-monorepo-e-isolamento.md) — `withContext`, verificador de catálogo, formato dos testes.

## Escopo — fazer

1. Migration `packages/db/migrations/20261102090000_f1_comandos.sql` com o SQL da seção 1 (bloco A ou B de `device_key`, conforme a regra da seção 1.3).
2. `packages/db/catalog-allowlist.json`: acrescentar `"command_policy"` em `appendOnly`; no bloco A de `device_key` (seção 1.3), acrescentar também `"device_key"` em `withoutOperatorId` com justificativa (CAT-03: chave do aparelho pertence ao usuário e não tem `operator_id`; o isolamento é por `user_id`, política `device_key_self`, tipo E); e `"app.revoke_device_keys(uuid)"` em `securityDefiner` (CAT-07: a central revoga chaves de outro usuário, que a política `device_key_self` não permite).
3. `packages/db/src/commands.ts`: helpers da seção 2, exportados por `packages/db/src/index.ts`.
4. `packages/db/src/secrets.ts`: cifra e acesso a `operator_secret` (seção 3), exportados por `index.ts`.
5. Regenerar os tipos Kysely com o script da T-004.
6. `.env.example`: `SECRETS_MASTER_KEYS` e `SECRETS_ACTIVE_KEY_VERSION` com valores de desenvolvimento (seção 3).
7. Na mesma migration, `auth.email_token` aceita o `purpose` `device_key_not_me` (link "Não fui eu" da T-018): `ALTER TABLE auth.email_token DROP CONSTRAINT email_token_purpose_check, ADD CONSTRAINT email_token_purpose_check CHECK (purpose IN ('invitation', 'password_reset', 'device_key_not_me'))` [VALIDAR o nome da constraint com `\d auth.email_token`]; o `down` restaura os dois valores.
8. Testes congelados em `tests/acceptance/T-017/` (seção "Testes de aceite").

## Fora do escopo

- Rotas HTTP, step-up, desafio (T-018); jobs do worker (T-020); job `secrets.rewrap` e rota da chave Asaas (T-023).
- Tabelas `partner`, `referral` (T-026), `share_link` (T-025), `legal_hold`, `platform_support_grant` (T-027), cobrança (T-023).
- Linha inicial de `command_policy` para operadoras existentes: sem linha vale `PLATFORM_DEFAULT_POLICY` (T-016).
- FK de `consent.partner_id` (entra com `partner` na T-026).

## Arquivos a criar/alterar

```
packages/db/migrations/20261102090000_f1_comandos.sql
packages/db/catalog-allowlist.json
packages/db/src/commands.ts
packages/db/src/secrets.ts
packages/db/src/index.ts
packages/db/src/generated/*            (tipos Kysely regenerados pela T-004)
.env.example
tests/acceptance/T-017/world.ts
tests/acceptance/T-017/isolation.test.ts
tests/acceptance/T-017/command-triggers.test.ts
tests/acceptance/T-017/transition-helper.test.ts
tests/acceptance/T-017/identity-consent.test.ts
tests/acceptance/T-017/secrets.test.ts
```

## Especificação detalhada

### 1. Migration

#### 1.1 Cabeçalho e tabelas de comando

```sql
-- migrate:up
-- T-017 — F1 de comandos. Fonte: 06 §6, 08 §6 e §8, 12 §3. Revisão N0.
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

-- rls: C (+ leitura do cliente) · append-only (CAT-06)
CREATE TABLE app.command_policy (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL REFERENCES app.operator (id),
  version integer NOT NULL CHECK (version >= 1),
  max_moving_cut_kmh smallint NOT NULL DEFAULT 0 CHECK (max_moving_cut_kmh BETWEEN 0 AND 40),
  evidence_max_age_s smallint NOT NULL DEFAULT 60 CHECK (evidence_max_age_s BETWEEN 15 AND 60),
  armed_ttl_s smallint NOT NULL DEFAULT 300 CHECK (armed_ttl_s BETWEEN 60 AND 300),
  occurrence_armed_ttl_s smallint NOT NULL DEFAULT 1800 CHECK (occurrence_armed_ttl_s BETWEEN 300 AND 1800),
  allow_app_block boolean NOT NULL DEFAULT false,
  created_by uuid NOT NULL REFERENCES auth."user" (id),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT command_policy_version_key UNIQUE (operator_id, version)
);

-- rls: A
CREATE TABLE app.occurrence (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL, tenant_id uuid NOT NULL, vehicle_id uuid NOT NULL,
  opened_by uuid NOT NULL REFERENCES auth."user" (id),
  opened_at timestamptz NOT NULL DEFAULT now(),
  police_report_number text NULL CHECK (length(police_report_number) <= 40),
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'recovered', 'closed')),
  closed_at timestamptz NULL, closed_by uuid NULL REFERENCES auth."user" (id),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT occurrence_scope_key UNIQUE (operator_id, tenant_id, id),
  CONSTRAINT occurrence_vehicle_fk FOREIGN KEY (operator_id, tenant_id, vehicle_id) REFERENCES app.vehicle (operator_id, tenant_id, id),
  CONSTRAINT occurrence_closed_chk CHECK ((status = 'open') = (closed_at IS NULL))
);
CREATE UNIQUE INDEX occurrence_open_key ON app.occurrence (vehicle_id) WHERE status = 'open';
CREATE INDEX occurrence_scope_idx ON app.occurrence (operator_id, tenant_id, opened_at DESC);
```

Depois, **copie sem alterar** de [06 §6](../docs/spec/06-comandos-e-bloqueio.md#6-modelo-de-dados) os blocos `CREATE TABLE app.command` (com os 3 índices), `CREATE TABLE app.command_attempt` (com o índice `command_attempt_inflight_key`) e `CREATE TABLE app.command_event` (com o índice), marcando `-- rls: A` em `command`, `-- rls: B` em `command_attempt` e `-- rls: A · append-only (CAT-06)` em `command_event`. A função `app.tg_command_state()` entra **com uma única mudança** em relação a 06 §6: o par `'ARMED>FAILED'` no array e a cláusula extra abaixo (motivo em "Decisões já tomadas" da T-016):

```sql
     OR (pair = 'ARMED>FAILED' AND (NEW.type <> 'block'
         OR NOT EXISTS (SELECT 1 FROM app.command_attempt a WHERE a.command_id = NEW.id)))
```

inserida logo após a linha `OR (pair IN ('DISPATCHING>READY', 'AWAITING_CONFIRMATION>READY') AND NEW.type <> 'unblock')`. O gatilho de imutabilidade de `command` recebe também `'policy_snapshot'` na lista de colunas.

```sql
-- tentativa encerrada não muda mais (06 §6)
CREATE FUNCTION app.tg_command_attempt_finished() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.finished_at IS NOT NULL THEN
    RAISE EXCEPTION 'tentativa % já encerrada', OLD.id USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER command_attempt_finished BEFORE UPDATE ON app.command_attempt FOR EACH ROW
  EXECUTE FUNCTION app.tg_command_attempt_finished();
CREATE TRIGGER command_attempt_immutable BEFORE UPDATE ON app.command_attempt FOR EACH ROW
  EXECUTE FUNCTION app.tg_immutable_columns('operator_id', 'tenant_id', 'command_id', 'seq', 'channel', 'started_at');
CREATE TRIGGER occurrence_immutable BEFORE UPDATE ON app.occurrence FOR EACH ROW
  EXECUTE FUNCTION app.tg_immutable_columns('operator_id', 'tenant_id', 'vehicle_id', 'opened_by', 'opened_at');
```

#### 1.2 Desafio, consentimento, segredo e membership

```sql
-- rls: A · desafio de step-up (08 §6.2)
CREATE TABLE app.command_challenge (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL, tenant_id uuid NOT NULL, vehicle_id uuid NOT NULL,
  user_id uuid NOT NULL REFERENCES auth."user" (id),
  device_key_id uuid NOT NULL REFERENCES app.device_key (id),
  type text NOT NULL CHECK (type IN ('block', 'unblock')),
  reason_code text NOT NULL CHECK (reason_code IN ('theft_suspected', 'preventive', 'customer_request', 'installation_test',
    'recovered', 'pre_dispatch_fix', 'occurrence_interval', 'other')),
  nonce bytea NOT NULL CHECK (length(nonce) = 32),
  expires_at timestamptz NOT NULL, consumed_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT command_challenge_vehicle_fk FOREIGN KEY (operator_id, tenant_id, vehicle_id) REFERENCES app.vehicle (operator_id, tenant_id, id),
  CONSTRAINT command_challenge_ttl_chk CHECK (expires_at <= created_at + interval '60 seconds')
);
CREATE INDEX command_challenge_user_idx ON app.command_challenge (user_id, created_at DESC);
CREATE FUNCTION app.tg_command_challenge_consume() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.consumed_at IS NOT NULL OR NEW.consumed_at IS NULL
     OR (to_jsonb(NEW) - 'consumed_at') IS DISTINCT FROM (to_jsonb(OLD) - 'consumed_at') THEN
    RAISE EXCEPTION 'desafio só aceita consumo único' USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER command_challenge_consume BEFORE UPDATE ON app.command_challenge FOR EACH ROW
  EXECUTE FUNCTION app.tg_command_challenge_consume();

-- rls: A · consentimento por finalidade (12 §3, §16)
CREATE TABLE app.consent (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL, tenant_id uuid NOT NULL,
  user_id uuid NOT NULL REFERENCES auth."user" (id),
  purpose text NOT NULL CHECK (purpose IN ('block_terms', 'sva_referral', 'sva_partner_share', 'sva_maintenance', 'impact_alert')),
  partner_id uuid NULL,
  text_version text NOT NULL CHECK (text_version ~ '^[a-z-]+-v[0-9]+(/[0-9]+kmh)?$'),
  text_sha256 bytea NOT NULL CHECK (length(text_sha256) = 32),
  granted_at timestamptz NOT NULL DEFAULT now(), revoked_at timestamptz NULL,
  CONSTRAINT consent_tenant_fk FOREIGN KEY (operator_id, tenant_id) REFERENCES app.tenant (operator_id, id),
  CONSTRAINT consent_partner_chk CHECK ((purpose IN ('sva_referral', 'sva_partner_share')) = (partner_id IS NOT NULL))
);
CREATE UNIQUE INDEX consent_active_key ON app.consent
  (tenant_id, user_id, purpose, coalesce(partner_id, '00000000-0000-0000-0000-000000000000'::uuid)) WHERE revoked_at IS NULL;
CREATE FUNCTION app.tg_consent_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.revoked_at IS NOT NULL OR NEW.revoked_at IS NULL
     OR (to_jsonb(NEW) - 'revoked_at') IS DISTINCT FROM (to_jsonb(OLD) - 'revoked_at') THEN
    RAISE EXCEPTION 'consentimento só aceita revogação' USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER consent_guard BEFORE UPDATE ON app.consent FOR EACH ROW EXECUTE FUNCTION app.tg_consent_guard();

-- rls: C · segredo cifrado da operadora (08 §8 item 4; 11 §5 item 4)
CREATE TABLE app.operator_secret (
  id uuid PRIMARY KEY,                                  -- gerado pela aplicação antes de cifrar (entra no AAD)
  operator_id uuid NOT NULL REFERENCES app.operator (id),
  kind text NOT NULL CHECK (kind IN ('asaas_api_key', 'sms_password')),
  ciphertext bytea NOT NULL CHECK (length(ciphertext) BETWEEN 17 AND 4096),
  nonce bytea NOT NULL CHECK (length(nonce) = 12),
  key_version smallint NOT NULL CHECK (key_version >= 1),
  last4 text NOT NULL CHECK (length(last4) BETWEEN 1 AND 4),
  created_at timestamptz NOT NULL DEFAULT now(), rotated_at timestamptz NULL,
  CONSTRAINT operator_secret_kind_key UNIQUE (operator_id, kind)
);
CREATE TRIGGER operator_secret_immutable BEFORE UPDATE ON app.operator_secret FOR EACH ROW
  EXECUTE FUNCTION app.tg_immutable_columns('id', 'operator_id', 'kind', 'created_at');

-- membership: permissão de comando do familiar (06 §4.1, CT-CMD-007)
ALTER TABLE app.membership ADD COLUMN can_command boolean NOT NULL DEFAULT false;
ALTER TABLE app.membership ADD CONSTRAINT membership_can_command_chk CHECK (NOT can_command OR role = 'tenant_member');
```

#### 1.3 `device_key` — bloco A ou B

Antes de escrever a migration, rode `grep -l "CREATE TABLE app.device_key" packages/db/migrations/*.sql`. **Vazio** → bloco A (a tabela nasce aqui, como diz [04 §3.7](../docs/spec/04-dominio-e-dados.md#37-conformidade)). **Encontrado** (a T-006 já a criou) → bloco B. O bloco vem **antes** de `command_challenge` na migration (FK).

```sql
-- Bloco A · rls: E
CREATE TABLE app.device_key (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth."user" (id),
  public_key bytea NOT NULL CHECK (length(public_key) = 91),
  platform text NOT NULL CHECK (platform IN ('android', 'ios')),
  label text NOT NULL CHECK (length(label) BETWEEN 1 AND 60),
  user_verification text NOT NULL CHECK (user_verification IN ('biometric', 'device_credential')),
  created_at timestamptz NOT NULL DEFAULT now(), last_used_at timestamptz NULL, revoked_at timestamptz NULL
);
CREATE UNIQUE INDEX device_key_user_active_key ON app.device_key (user_id) WHERE revoked_at IS NULL;

-- Bloco B · a tabela já existe (T-006)
ALTER TABLE app.device_key
  ADD COLUMN label text NOT NULL DEFAULT 'Aparelho' CHECK (length(label) BETWEEN 1 AND 60),
  ADD COLUMN user_verification text NOT NULL DEFAULT 'biometric' CHECK (user_verification IN ('biometric', 'device_credential')),
  ADD COLUMN last_used_at timestamptz NULL;
DROP INDEX IF EXISTS app.device_key_user_active_idx;
CREATE UNIQUE INDEX device_key_user_active_key ON app.device_key (user_id) WHERE revoked_at IS NULL;

-- Nos dois blocos
CREATE TRIGGER device_key_immutable BEFORE UPDATE ON app.device_key FOR EACH ROW
  EXECUTE FUNCTION app.tg_immutable_columns('id', 'user_id', 'public_key', 'platform', 'created_at');
CREATE FUNCTION app.tg_device_key_revoke_once() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.revoked_at IS NOT NULL THEN
    RAISE EXCEPTION 'chave revogada não muda' USING ERRCODE = '23514';   -- revogação não se desfaz (08 §6.5)
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER device_key_revoke_once BEFORE UPDATE ON app.device_key FOR EACH ROW
  EXECUTE FUNCTION app.tg_device_key_revoke_once();
```

Nos dois blocos a política é `device_key_self` (seção 1.4, tipo E). No bloco A, `device_key` ganha `ENABLE` + `FORCE ROW LEVEL SECURITY` na seção 1.4. No bloco B, a migration executa `DROP POLICY IF EXISTS device_key_member ON app.device_key` antes de criar `device_key_self`.

#### 1.4 RLS e grants

```sql
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['command_policy', 'occurrence', 'command', 'command_attempt', 'command_event',
    'command_challenge', 'consent', 'operator_secret'] LOOP
    EXECUTE format('ALTER TABLE app.%I ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY', t);
  END LOOP;
  FOREACH t IN ARRAY ARRAY['occurrence', 'command', 'command_event', 'command_challenge', 'consent'] LOOP   -- tipo A
    EXECUTE format($p$CREATE POLICY %1$s_isolation ON app.%1$I FOR ALL
      USING (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())))
      WITH CHECK (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())))$p$, t);
  END LOOP;
  FOREACH t IN ARRAY ARRAY['command_attempt'] LOOP                                                          -- tipo B
    EXECUTE format($p$CREATE POLICY %1$s_staff_all ON app.%1$I FOR ALL
      USING (operator_id = app.current_operator_id() AND app.current_scope() = 'operator')
      WITH CHECK (operator_id = app.current_operator_id() AND app.current_scope() = 'operator')$p$, t);
    EXECUTE format($p$CREATE POLICY %1$s_tenant_read ON app.%1$I FOR SELECT
      USING (operator_id = app.current_operator_id() AND app.current_scope() = 'tenant' AND tenant_id = ANY (app.current_tenant_ids()))$p$, t);
  END LOOP;
  FOREACH t IN ARRAY ARRAY['command_policy', 'operator_secret'] LOOP                                        -- tipo C
    EXECUTE format($p$CREATE POLICY %1$s_staff_all ON app.%1$I FOR ALL
      USING (operator_id = app.current_operator_id() AND app.current_scope() = 'operator')
      WITH CHECK (operator_id = app.current_operator_id() AND app.current_scope() = 'operator')$p$, t);
  END LOOP;
END $$;
CREATE POLICY command_policy_tenant_read ON app.command_policy FOR SELECT
  USING (operator_id = app.current_operator_id() AND app.current_scope() = 'tenant');
-- device_key (tipo E): só o usuário do contexto (app.user_id) lê e escreve as próprias chaves (04 §4.2)
-- Só no bloco A: ALTER TABLE app.device_key ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY;
CREATE POLICY device_key_self ON app.device_key FOR ALL
  USING (user_id = app.current_user_id()) WITH CHECK (user_id = app.current_user_id());
CREATE POLICY device_key_definer ON app.device_key FOR ALL TO tracksys_owner USING (true) WITH CHECK (true);   -- só app.revoke_device_keys

-- Revogação pela central: age sobre outro usuário, por isso SECURITY DEFINER (CAT-07, 04 §4.4, 08 §6.5)
CREATE FUNCTION app.revoke_device_keys(p_user_id uuid) RETURNS integer
  LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
AS $$
DECLARE v_count integer;
BEGIN
  IF app.current_scope() IS DISTINCT FROM 'operator' OR NOT EXISTS (
       SELECT 1 FROM app.membership m WHERE m.user_id = p_user_id AND m.operator_id = app.current_operator_id()) THEN
    RAISE EXCEPTION 'usuário fora da operadora do contexto' USING ERRCODE = '42501';
  END IF;
  UPDATE app.device_key SET revoked_at = now() WHERE user_id = p_user_id AND revoked_at IS NULL;
  GET DIAGNOSTICS v_count = ROW_COUNT;
  RETURN v_count;
END $$;
REVOKE ALL ON FUNCTION app.revoke_device_keys(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.revoke_device_keys(uuid) TO tracksys_app;

GRANT SELECT, INSERT ON app.command_policy, app.command_event TO tracksys_app;
GRANT SELECT, INSERT, UPDATE ON app.command, app.command_attempt, app.occurrence, app.command_challenge,
  app.consent, app.operator_secret, app.device_key TO tracksys_app;
```

`-- migrate:down`: `DROP TABLE` na ordem inversa (`operator_secret`, `consent`, `command_challenge`, `command_event`, `command_attempt`, `command`, `occurrence`, `command_policy`), `DROP FUNCTION` de `app.revoke_device_keys`, `app.tg_device_key_revoke_once` e das demais funções criadas, `ALTER TABLE app.membership DROP CONSTRAINT membership_can_command_chk, DROP COLUMN can_command`; bloco A: `DROP TABLE app.device_key`; bloco B: remover as 3 colunas, os gatilhos, `device_key_self` e `device_key_definer`, o índice novo, e recriar `device_key_user_active_idx` e `device_key_member`. Comentário no down: "down de expand: só desenvolvimento; produção nunca roda migrate down ([13 §7](../docs/spec/13-infra-e-operacao.md#7-deploy))".

### 2. Helpers de comando (`packages/db/src/commands.ts`)

Todos recebem `q: Pick<pg.ClientBase, 'query'>` de dentro de `withContext` (nunca abrem transação própria) e usam SQL parametrizado.

| Função | Contrato |
|---|---|
| `insertCommand(q, row): Promise<{ id: string; stateVersion: 1 }>` | INSERT com `state = 'REQUESTED'` (ou `'UNKNOWN'` para `requested_via = 'contingency'`), `state_version = 1`; grava na mesma chamada o `command_event` de criação (`from_state` NULL, `to_state` = estado inicial, `actor` = `user:<uuid>`). Criação **não** gera evento de outbox: só transições geram (CT-CMD-020 conta 4 eventos para 5 `command_event`). 23505 em `command_active_relay_key` vira `ActiveRelayCommandError` com o id do ativo (lido em seguida) |
| `transitionCommand(q, t): Promise<{ applied: false } \| { applied: true; stateVersion: number }>` | `t = { commandId, fromState, fromVersion, toState, stateReason, actor, detail, processingMode }`. `UPDATE app.command SET state = $to, state_version = $v + 1, state_reason = $r WHERE id = $id AND state = $from AND state_version = $v RETURNING operator_id, tenant_id, vehicle_id, device_id, type, requested_via`. 0 linhas → `{ applied: false }` sem efeito. 1 linha → INSERT `command_event` (`from_state`, `to_state`, `actor`, `detail`), outbox `command.state.changed.v1` (payload validado por `CommandStateChangedV1` da T-016, `entity_id = commandId`) e `SELECT pg_notify('command_changed', json_build_object('c', id, 'o', operator_id, 't', tenant_id, 'v', vehicle_id)::text)` |
| `recordCommandEvidence(q, { commandId, state, actor, detail })` | `command_event` com `from_state = to_state = state` e `detail.kind = 'evidence'` (06 §8.1 item 2); não muda `state_version` |
| `insertAttempt(q, { commandId, seq, channel, startedAt? })` | INSERT `result = 'pending'`; devolve `id` |
| `finishAttempt(q, { commandId, seq, result, rawResponse?, providerRef? })` | `UPDATE … SET result, finished_at = now(), raw_response = left($raw, 4000) … WHERE command_id = $1 AND seq = $2 AND finished_at IS NULL`; 0 linhas → erro |
| `currentPolicy(q, operatorId): Promise<CommandPolicyValues>` | Maior `version` de `command_policy` da operadora; sem linha → `PLATFORM_DEFAULT_POLICY` de `@tracksys/domain` |

`actor` aceita só `user:<uuid>` ou `system:(api|worker|reconcile|failover)` (CHECK de 06 §6). `raw_response` passa por `redactRaw()` local: remove `Authorization`, senhas (`password`, `senha`) e trunca em 4.000 caracteres.

### 3. Segredos da operadora (`packages/db/src/secrets.ts`)

```ts
export interface MasterKeys { activeVersion: number; keys: ReadonlyMap<number, Buffer> }
export function loadMasterKeys(env: { SECRETS_MASTER_KEYS?: string; SECRETS_ACTIVE_KEY_VERSION?: string }): MasterKeys
export function encryptSecret(k: MasterKeys, aad: { operatorId: string; kind: SecretKind; id: string }, plaintext: string):
  { ciphertext: Buffer; nonce: Buffer; keyVersion: number }
export function decryptSecret(k: MasterKeys, aad: { operatorId: string; kind: SecretKind; id: string },
  row: { ciphertext: Buffer; nonce: Buffer; keyVersion: number }): string
export async function putOperatorSecret(q, k, i: { operatorId: string; kind: SecretKind; plaintext: string }): Promise<{ id: string; last4: string; keyVersion: number }>
export async function readOperatorSecret(q, k, i: { operatorId: string; kind: SecretKind }): Promise<string | null>
export async function rewrapOperatorSecrets(q, k): Promise<number>   // linhas visíveis no contexto com key_version < ativa
export type SecretKind = 'asaas_api_key' | 'sms_password'
```

1. `SECRETS_MASTER_KEYS` = `"<versão>:<base64 de 32 bytes>[,<versão>:<base64>]"`; `SECRETS_ACTIVE_KEY_VERSION` presente na lista. Validação por Zod; chave com outro tamanho ou versão ativa ausente → erro citando só o nome da variável.
2. AES-256-GCM (`node:crypto`), nonce aleatório de 12 bytes, tag de 16 bytes concatenada ao fim do `ciphertext`, AAD = `"<operatorId>:<kind>:<id>"` em UTF-8 ([08 §8](../docs/spec/08-identidade-e-seguranca.md#8-segredos)).
3. `putOperatorSecret`: gera `id` (`randomUUID()`) só no 1º INSERT; troca de valor faz UPDATE da mesma linha (mesmo `id`, novo nonce, `rotated_at = now()`). `last4` = 4 últimos caracteres do valor.
4. `readOperatorSecret` decifra com a `key_version` da linha. Falha de autenticação (AAD ou tag) lança `SecretDecryptError` sem o valor nem o AAD na mensagem.
5. Nada desta seção loga, devolve ou serializa texto claro, chave ou nonce.

`.env.example` acrescenta (valor fixo e público, só para desenvolvimento; decodifica para 32 bytes):

```ini
SECRETS_MASTER_KEYS=1:ZGV2LW9ubHktbWFzdGVyLWtleS0zMi1ieXRlcy0wMDE=
SECRETS_ACTIVE_KEY_VERSION=1
```

## Testes de aceite (congelados)

Postgres real, papel `tracksys_app` com `withContext` (T-001) e `DATABASE_URL_ADMIN` só para semear `auth."user"` e perfis. Os blocos completos são escritos no PR do cartão a partir deste plano (DoR item 6); nomes de `describe`/`it` e asserções abaixo são normativos.

`tests/acceptance/T-017/world.ts` exporta `seedCommandWorld(app, admin)` (o contexto dos testes de `device_key` e `membership` passa `userId`, T-006) que cria, com UUID aleatório: operadoras Alfa e Beta; clientes A1 e A2 (Alfa) e B1 (Beta); usuários `admin.alfa`, `agente.alfa`, `dono.a1`, `familia.a1`, `dono.a2`, `admin.beta` em `auth."user"` com memberships; veículos V1 (A1), V3 (A2), V2 (B1); rastreadores R1 (V1), R3 (V3), R2 (V2) com perfil `j16-gt06` de teste e vínculos primários abertos (`cut_point = 'fuel_pump'` em R1, NULL em R3). Devolve todos os ids.

`tests/acceptance/T-017/isolation.test.ts` — `describe('T-017 isolamento das tabelas novas (INV-07)')`, um bloco `it.each` por tabela (`occurrence`, `command`, `command_attempt`, `command_event`, `command_challenge`, `consent`, `command_policy`, `operator_secret`):
- `ISO-01 <tabela>: contexto tenant de A1 vê só linhas de A1` → linhas de A2 e da Beta ausentes (em `command_policy`, A1 lê a política da Alfa e não a da Beta; em `operator_secret`, A1 vê 0 linhas).
- `ISO-02 <tabela>: escopo operator da Alfa vê A1 e A2 e nada da Beta`.
- `ISO-03 <tabela>: sem contexto, 0 linhas`.
- `ISO-04 <tabela>: INSERT com operator_id da Beta no contexto da Alfa → 42501`; e `ISO-04b`: tenant A1 inserindo `tenant_id` de A2 → 42501; em `command_attempt`, `command_policy` e `operator_secret`, qualquer INSERT no escopo tenant → 42501.
- `ISO-05 <tabela>: FK composta recusa veículo/comando/cliente de outra operadora → 23503`.
- `device_key (tipo E, device_key_self)`:
  - `dono.a1` com `userId = dono.a1` vê a própria chave; sem `userId` no contexto, 0 linhas (INV-07);
  - contexto tenant de A2 com `userId = dono.a2` e contexto operator da Beta com `userId = admin.beta` não veem a chave de `dono.a1`;
  - segunda chave ativa do mesmo usuário → 23505;
  - **CT-DAD-026:** contexto operator da Beta (`userId = admin.beta`) faz `UPDATE ... SET revoked_at = NULL` na chave K de `dono.a1` → 0 linhas atualizadas e K intacta; `INSERT` com `user_id` de outro usuário → 42501;
  - `revoked_at` preenchido: o próprio dono tenta `UPDATE revoked_at = NULL` ou qualquer outro campo → 23514 (`device_key_revoke_once`).

`tests/acceptance/T-017/command-triggers.test.ts` — `describe('T-017 máquina de estados no banco — CT-CMD-009, CT-CMD-010, CT-CMD-004, CT-CMD-022')`:
- `block REQUESTED v1 → CONFIRMED é recusado` → SQLSTATE 23514.
- `REQUESTED → READY com state_version = 3 é recusado` → 23514.
- `UNKNOWN → DISPATCHING é recusado` → 23514.
- `unblock READY com 1 tentativa → CANCELLED é recusado` → 23514.
- `block ARMED com tentativa device_offline → FAILED é aceito; sem tentativa → 23514; unblock ARMED → FAILED → 23514`.
- `comando nasce só REQUESTED (UNKNOWN só em contingência)` → INSERT `state = 'READY'` → 23514; `UNKNOWN` com `requested_via = 'app'` → 23514; `UNKNOWN` com `contingency` → grava.
- `2 UPDATE condicionais concorrentes com state_version = 2: exatamente 1 altera 1 linha` (duas conexões, `Promise.all`).
- `segundo block ativo no mesmo rastreador → 23505 em command_active_relay_key`; `block CONFIRMED + novo block → grava`.
- `colunas imutáveis: UPDATE de type, device_id, expires_at ou policy_snapshot → 23000`.
- `tentativa encerrada não muda: UPDATE de result após finished_at → 23000`; `2ª tentativa gprs em voo do mesmo comando → 23505`.
- `command_policy: v2 com max_moving_cut_kmh = 41 → 23514; = 40 grava; UPDATE ou DELETE por tracksys_app → 42501`.
- `command_event: UPDATE e DELETE por tracksys_app → 42501` (CT-CMD-020).
- `segunda ocorrência open em V1 → 23505; após closed, nova open grava` (CT-CMD-022).
- `occurrence status closed sem closed_at → 23514`.

`tests/acceptance/T-017/transition-helper.test.ts` — `describe('T-017 transitionCommand — CT-CMD-020 (parte de banco)')`:
- `REQUESTED → READY → DISPATCHING → AWAITING_CONFIRMATION → CONFIRMED gera 5 command_event, igual a state_version, e 4 command.state.changed.v1` → `count(command_event) = 5 = state_version`; o 1º com `from_state` NULL; outbox com exatamente 4 eventos do tipo, o 1º com `fromState: 'REQUESTED'` e `toState: 'READY'`.
- `transição com versão velha devolve applied=false e não grava evento nem outbox`.
- `NOTIFY command_changed chega a um LISTEN com c, o, t, v e sem coordenadas` (payload < 200 bytes).
- `insertCommand com block ativo no mesmo rastreador lança ActiveRelayCommandError com o id do ativo`.
- `currentPolicy sem linha devolve version 0 e teto 0; com v1 e v2 devolve v2`.

`tests/acceptance/T-017/identity-consent.test.ts` — `describe('T-017 desafio, consentimento e can_command')`:
- `desafio consumido uma vez: 2º UPDATE de consumed_at → 23000; UPDATE de nonce → 23000`.
- `desafio com expires_at = created_at + 61 s → 23514`.
- `consent só revoga: UPDATE de text_version → 23000; revogar 2 vezes → 23000`.
- `2 consentimentos ativos block_terms do mesmo usuário e cliente → 23505; revogado + novo → grava`.
- `sva_referral sem partner_id → 23514; block_terms com partner_id → 23514`.
- `can_command = true em tenant_owner → 23514; em tenant_member → grava; dono.a1 (escopo tenant, userId = dono.a1) altera can_command de familia.a1 → 1 linha`.
- **CT-DAD-026 (membership_tenant_manage):** contexto tenant de A1 com `userId = familia.a1` (`tenant_member`) insere membership `tenant_member` com `can_command = true` → 42501; o mesmo com `userId = dono.a1` → grava; sem `userId` → 42501.
- **`app.revoke_device_keys`:** `agente.alfa` (contexto operator da Alfa) revoga as chaves de `dono.a1` → retorna 1 e `revoked_at` preenchido; para `admin.beta` (sem membership na Alfa) → 42501; no contexto tenant de A1 → 42501; 2ª chamada → 0; `has_function_privilege`: `tracksys_app` com EXECUTE e PUBLIC sem EXECUTE; o catálogo (CAT-07) lista a função na allowlist.

`tests/acceptance/T-017/secrets.test.ts` — `describe('T-017 operator_secret — CT-SEG-020 (parte de banco e cifra)')`:
- `ciphertext não contém o texto claro`: `putOperatorSecret('asaas-teste-chave-0001')` → `position(convert_to('asaas-teste-chave-0001','UTF8') in ciphertext) = 0`, `last4 = '0001'`, `readOperatorSecret` devolve o original.
- `linha copiada para a Beta não decifra`: copiar `ciphertext`, `nonce`, `key_version` para uma linha da Beta (mesmo `kind`, outro `id`) → `readOperatorSecret` no contexto da Beta lança `SecretDecryptError`.
- `rotação: com chaves 1 e 2 e ativa 2, rewrapOperatorSecrets regrava e deixa 0 linhas com key_version = 1`.
- `tenant A1 não lê operator_secret (0 linhas)`.

`identity-consent.test.ts` (complemento): `email_token` com `purpose = 'device_key_not_me'` grava; `purpose = 'outro'` → 23514.
- `loadMasterKeys recusa chave de 31 bytes citando só SECRETS_MASTER_KEYS`.

## Comandos de verificação

```bash
pnpm db:up
pnpm db:migrate                                   # Applied: 20261102090000_f1_comandos.sql
pnpm db:check                                     # Catálogo OK: nenhuma violação de CAT-01..CAT-07.
pnpm exec dbmate --migrations-dir ./packages/db/migrations --no-dump-schema rollback && pnpm db:migrate
pnpm test:acceptance tests/acceptance/T-017
pnpm verify
```

## Definição de pronto

- [ ] Migration única, com `-- rls: X` em cada tabela, `lock_timeout` e `statement_timeout`, sem `DELETE` concedido a `tracksys_app`.
- [ ] `command_policy` em `appendOnly`; `pnpm db:check` verde; rollback e novo `up` verdes.
- [ ] `device_key_self`, `device_key_revoke_once` e `app.revoke_device_keys` (CAT-07, `EXECUTE` só para `tracksys_app`) na migration; `pnpm db:check` verde com a função na allowlist.
- [ ] Gatilho de 06 §6 copiado byte a byte, exceto o par `ARMED>FAILED` e `policy_snapshot` na imutabilidade, diferenças listadas na descrição do PR.
- [ ] Helpers sem transação própria, sem log de payload; segredos nunca em log ou erro.
- [ ] Testes congelados de T-001 e T-005 continuam verdes.
- [ ] PR `feat(db): migration do F1 de comandos (T-017)`, N0, plano no PR, revisão cruzada registrada.

## Decisões já tomadas

| Dúvida provável | Resposta |
|---|---|
| 1. `command_event` é tipo A ou B? | Tipo A, append-only (sem UPDATE/DELETE, CAT-06): o `api` grava o evento de criação na transação do pedido, no contexto do titular (escopo `tenant`), e o tipo A mantém o cliente preso ao próprio cliente. |
| 2. `command_attempt` continua B? | Sim. Só o worker (escopo `operator`) e o registro de contingência da central gravam tentativas. |
| 3. Crio a política v1 para as operadoras existentes? | Não. `created_by` exige usuário e a migration não tem um. Sem linha, vale `PLATFORM_DEFAULT_POLICY` (mesmos valores da v1 de 06 §3.3). A Lider grava a sua versão pelo console com step-up (GC-1). |
| 4. `device_key` já existe? | Use a regra da seção 1.3 (grep antes de escrever). Nunca edite a migration da T-006. |
| 5. Por que `text_sha256` em `consent`? | Prova o texto aceito ([Anexo B §1](../docs/anexos/B-juridico.md#1-prontidão-jurídica-por-marco): SHA-256 no `consent/manifest.json`); a versão sozinha não prova o conteúdo. |
| 6. Por que `last4` em `operator_secret`? | `GET /api/v1/billing/account` devolve `apiKeyLast4` sem decifrar ([08 §8](../docs/spec/08-identidade-e-seguranca.md#8-segredos) item 6); a API nunca chama `decryptSecret`. |
| 7. `consent.partner_id` sem FK? | Nesta migration, sim: `partner` nasce na T-026, que acrescenta a FK composta. O CHECK já exige `partner_id` nas finalidades de parceiro. |
| 8. E o `membership.vehicle_ids`? | Não existe. No F1, `can_command` vale para todos os veículos do cliente; o limite de segurança no banco continua sendo o cliente. |
| 9. Helper usa Kysely ou `pg`? | `pg` (`Pick<pg.ClientBase, 'query'>`), igual a `withContext` da T-001; funciona com o cliente que o `api` e o `worker` já recebem. |
| 10. `pg_notify` com coordenadas? | Nunca. Só ids (`c`, `o`, `t`, `v`); o hub SSE relê sob RLS ([03 §7](../docs/spec/03-arquitetura.md#7-tempo-real-sse--listennotify)). |
| 11. Onde fica a chave mestra em produção? | `infra/secrets/prod.env.sops` (SOPS + age, [08 §8](../docs/spec/08-identidade-e-seguranca.md#8-segredos)); o valor do `.env.example` é só para desenvolvimento. |
| 12. Quem escreve `device_key` e o que o contexto precisa ter? | Só o próprio usuário: `withContext` com `userId` (T-006) grava `app.user_id`, e `device_key_self` compara `user_id = app.current_user_id()`. Sem `userId`, nenhuma linha passa. |
| 13. Como a central revoga a chave de outro usuário? | Por `app.revoke_device_keys(p_user_id)` (`SECURITY DEFINER`, CAT-07, `EXECUTE` só para `tracksys_app`): exige escopo `operator` e membership do usuário na operadora do contexto, senão 42501. A rota grava `audit_log` `device_key.revoke` na mesma transação (T-018). |
| 14. Chave revogada pode ser reativada? | Nunca. `device_key_revoke_once` recusa (23514) qualquer UPDATE de linha com `revoked_at` preenchido; a rota revoga só linhas `revoked_at IS NULL`. |
| 15. Quem liga `can_command`? | Só `tenant_owner` ativo do cliente: o WITH CHECK de `membership_tenant_manage` (criado na T-006) exige membership `tenant_owner` ativa do `app.user_id` do contexto. `tenant_member` não cria membro nem liga `can_command` (42501). |
