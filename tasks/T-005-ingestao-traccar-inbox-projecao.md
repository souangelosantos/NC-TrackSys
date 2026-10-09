# T-005 — Ingestão Traccar → `ingest_inbox` → `position`/`device_state`/`outbox`

| Campo | Valor |
|---|---|
| Fase | F0 (semana S2: 14–20/10/2026; fatia vertical demonstrada até 20/10/2026) |
| Requisitos | REQ-ING-002 a REQ-ING-015, REQ-ING-017, REQ-ING-020; REQ-DAD-001, REQ-DAD-004 e REQ-DAD-006 a REQ-DAD-011 (parte do F0 que cabe a estas tabelas); REQ-DAD-005 (estende o verificador com CAT-07); REQ-DAD-012 (índices das consultas desta tarefa; o teste de desempenho CT-DAD-012 é da T-028, F1); REQ-NEG-014 (parte de ingestão e banco; a metade HTTP/SSE fecha na T-008); REQ-ARQ-009 (outbox na transação e relay; a 3ª parte do CT-ARQ-009, `alert_delivery`, fecha na T-012); REQ-ARQ-013 (quarentena `source_id_regression`; a page vem com as métricas da ingestão, REQ-ING-021: T-013/T-028); REQ-API-015; REQ-ONB-019 (`app.device_ingest_probe`; o aviso em C05 é da T-007); REQ-QLD-009 (P1–P4 para INV-01 a INV-04 e INV-05 no caminho de reprocessamento; P5 do motor de alertas fica com a T-011) |
| Invariantes | INV-01, INV-02, INV-03, INV-04, INV-05, INV-06, INV-07, INV-12 |
| Risco de revisão | **N1** (tabela 2.3 de [02](../docs/spec/02-escopo-e-fases.md)). **Trechos N0:** a migration, `catalog-allowlist.json`, CAT-07 e as funções `SECURITY DEFINER` exigem revisão adversarial de outro fornecedor e leitura humana linha a linha (AGENTS.md; REQ-NEG-014 é N0) |
| Depende de | T-001 (isolamento), T-002 (capturas e perfil J16 `draft`), T-004 (pacotes `contracts` e esqueleto `api`/`worker`) |
| Estimativa | 3 sessões de agente (1: migration, CAT-07 e domínio puro; 2: aplicador, rotas, worker e relay; 3: propriedades e fatia vertical) |
| Bloqueado por decisão | DEC-02 (formato do envelope e do perfil). Padrão seguro enquanto aberta: toda capacidade `unknown`, correção WNRO desligada, sem `position.id` → quarentena |

## Objetivo

Transformar cada mensagem que o Traccar decodifica em fato durável, exatamente uma vez: custódia na `ingest_inbox`, normalização para unidades canônicas, dono resolvido no servidor pelo vínculo vigente no `fix_time`, projeção síncrona em `position`/`device_state`/`outbox` com savepoint e reprocessamento pelo worker. Ao final, o roteiro da primeira fatia vertical ([02 §3](../docs/spec/02-escopo-e-fases.md)) passa automatizado com capturas reais do J16, os testes de propriedade de INV-01 a INV-04 rodam no CI e o verificador de catálogo ganha a regra CAT-07 para a lista fechada de funções `SECURITY DEFINER`.

## Contexto obrigatório

- [05](../docs/spec/05-ingestao-e-telemetria.md) §3–§11, §13, §16: rotas, normalização, identidade, janela, projeção, ordenação, compactação, eventos, reprocessamento, perfil, propriedades.
- [04](../docs/spec/04-dominio-e-dados.md) §3.2, §3.3, §3.5, §4.1–§4.4, §5.1, §7: DDL, RLS, papéis, funções definidoras, partições.
- [02 §3](../docs/spec/02-escopo-e-fases.md) e REQ-NEG-014: roteiro e dados da fatia vertical.
- [03 §6](../docs/spec/03-arquitetura.md), REQ-ARQ-009 e REQ-ARQ-013 (outbox, relay, instância de origem); [09](../docs/spec/09-api-e-contratos.md) REQ-API-015; [11 §10](../docs/spec/11-onboarding-e-migracao.md) e REQ-ONB-019 (sonda de quarentena); [14](../docs/spec/14-qualidade-e-processo-ia.md) REQ-QLD-009.
- [ADR-002](../docs/adr/ADR-002-postgres-unico-fila-barramento.md) (outbox + NOTIFY, sem broker) e [ADR-003](../docs/adr/ADR-003-traccar-borda-de-protocolos.md) (Traccar só como borda).
- [T-002](T-002-spike-j16-bancada.md): `fixtures/j16/` e `capability-profile.draft.json` (capacidades `yes|no|unknown`).

## Escopo — fazer

1. Migration `20261014120000_ingestao.sql` com o SQL exato da seção (1): gatilho de imutabilidade, frota mínima, ingestão, RLS, privilégios, 6 funções `SECURITY DEFINER` (as 5 de [04 §4.4](../docs/spec/04-dominio-e-dados.md) e a sonda `app.device_ingest_probe` de [11 §10](../docs/spec/11-onboarding-e-migracao.md)), partições e perfil J16 `draft`.
2. CAT-07 em `@tracksys/db` e allowlist da seção (2); mensagem do script passa a `Catálogo OK: nenhuma violação de CAT-01..CAT-07.`
3. Contratos Zod em `packages/contracts` (3): envelopes do Traccar, perfil base, `telemetry.position.accepted.v1`, `device.state.updated.v1`.
4. Domínio puro em `packages/domain/src/ingestion/` (4): `normalizeTraccar`, `checkTimeWindow`, movimento, compactação, `decideProjection`, flags, haversine.
5. Aplicador em `packages/db/src/ingestion/` (5): sequência do [05 §7](../docs/spec/05-ingestao-e-telemetria.md) com savepoint, dedupe, regressão de id, `insertOutboxEvent`, `reprocessPending`.
6. Listener interno do `api` (6): `POST /internal/v1/traccar/positions` e `/events`, `GET /internal/healthz`, ordem de verificação 401 → 413 → 400 → 503 → 202.
7. Worker (7): laço de reprocessamento de `pending` a cada 5 s, `app.ensure_partitions()` no boot e às 00:17 UTC e relay da outbox (REQ-ARQ-009) sem rota de produção.
8. Helpers de teste em `packages/testkit` (8), aceite em `tests/acceptance/T-005/` e propriedades puras em `packages/domain/test/`. `.env.example` mantém (T-004) ou ganha `DATABASE_URL_INGEST`, `INGEST_SHARED_SECRET`, `INGEST_SOURCE_INSTANCE=traccar-01` e `INTERNAL_PORT=3001` (valores só de desenvolvimento).

## Fora do escopo

- Reconciliação e backfill (REQ-ING-016): T-015 (reconciliação) e T-028 (backfill automático, F1). Retenção da inbox e `app.retention_purge` (REQ-ING-018, REQ-DAD-013): T-027 (F1). Métricas e pages da ingestão (REQ-ING-021): T-013 (sonda de atraso) e T-028 (Prometheus, F1). Teste de desempenho CT-DAD-012: T-028 (F1).
- Rotas do relay para filas de consumidor (`device.state.updated.v1 → alerts.evaluate`): T-011, que só acrescenta a entrada em `apps/worker/src/outbox/routes.ts`. Aqui o relay nasce com o mapa de rotas vazio (linha sem rota é só marcada publicada).
- Cadastro de rastreador/vínculo e `rebind` de `device_state` (CT-DAD-011, 2ª parte): T-007. `app.memberships_for_user`: T-006. `app.claim_push_token`: T-012. 404 e SSE da fatia vertical (passos 2–5 de [02 §3](../docs/spec/02-escopo-e-fases.md)): T-008. Correlação de `commandResult`: F1.
- `infra/traccar/traccar.xml.tpl` (T-003/T-002). Escrever no banco do Traccar (proibido, ADR-003).

## Arquivos a criar/alterar

```
packages/db/migrations/20261014120000_ingestao.sql
packages/db/catalog-allowlist.json
packages/db/src/{allowlist,catalog,index}.ts, packages/db/scripts/check-catalog.ts   (CAT-07; mensagem)
packages/db/src/ingestion/{inbox,apply-projection,outbox,reprocess,faults,index}.ts
packages/contracts/src/{internal/traccar,fleet/capability-profile}.ts
packages/contracts/src/events/{telemetry-position-accepted.v1,device-state-updated.v1}.ts
packages/domain/{package.json,tsconfig.json}                 (criar se a T-004 não criou; dev: vitest, fast-check)
packages/domain/src/ingestion/{normalize,window,motion,compaction,decide,flags,geo,profile,index}.ts
packages/domain/test/ingestion.property.test.ts
apps/api/src/ingestion/{traccar.controller,ingestion.module,ingest-token.hook,ingest-env}.ts
apps/api/src/internal-main.ts                                (script "start:internal" no package.json do api)
apps/worker/src/ingestion/{reprocess-pending,partitions}.ts  e registro em apps/worker/src/main.ts
apps/worker/src/outbox/{relay,routes}.ts                     (relay; routes.ts nasce vazio)
packages/testkit/src/{j16-fixtures,vertical-slice}.ts
.env.example
tests/acceptance/T-005/harness.ts e tests/acceptance/T-005/{schema,http,normalization,reprocess,relay,vertical-slice,ingestion.property}.test.ts
```

## Especificação detalhada

### (1) Migration — SQL exato (DDL de [04 §3](../docs/spec/04-dominio-e-dados.md), recorte da T-005)

```sql
-- migrate:up
-- T-005 — Frota mínima, ingestão e funções definidoras. INV-01..04, INV-06, INV-07. Tipos RLS no comentário de cada tabela.
SET LOCAL lock_timeout = '5s'; SET LOCAL statement_timeout = '60s';
-- CREATE OR REPLACE com o mesmo corpo da T-006: a ordem de merge não importa (04 §3.2).
CREATE OR REPLACE FUNCTION app.tg_immutable_columns() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE col text;
BEGIN
  FOREACH col IN ARRAY TG_ARGV LOOP
    IF to_jsonb(NEW) -> col IS DISTINCT FROM to_jsonb(OLD) -> col THEN
      RAISE EXCEPTION 'coluna %.% é imutável', TG_TABLE_NAME, col USING ERRCODE = 'integrity_constraint_violation';
    END IF;
  END LOOP;
  RETURN NEW;
END $$;
CREATE TRIGGER tenant_immutable BEFORE UPDATE ON app.tenant FOR EACH ROW EXECUTE FUNCTION app.tg_immutable_columns('operator_id');
CREATE TRIGGER vehicle_immutable BEFORE UPDATE ON app.vehicle FOR EACH ROW EXECUTE FUNCTION app.tg_immutable_columns('operator_id', 'tenant_id');
-- rls: F + G (leitura por app/ingest; escrita só por migration do dono)
CREATE TABLE app.capability_profile (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  model text NOT NULL, firmware_range text NOT NULL DEFAULT '*', protocol text NOT NULL,
  version integer NOT NULL CHECK (version >= 1),
  capabilities jsonb NOT NULL CHECK (jsonb_typeof(capabilities) = 'object' AND capabilities ?& ARRAY[
    'relay', 'relay_state_reported', 'ignition', 'power_cut_alarm', 'sos', 'accelerometer',
    'device_speed_gate', 'secondary_server', 'domain_support', 'sms_position', 'offline_buffer']),
  sms_templates_ref text NULL,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'homologated', 'suspended')),
  homologated_at timestamptz NULL, evidence_ref text NULL, created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT capability_profile_version_key UNIQUE (model, firmware_range, version),
  CONSTRAINT capability_profile_homologation_chk CHECK (status <> 'homologated' OR (homologated_at IS NOT NULL AND evidence_ref IS NOT NULL))
);
-- rls: C
CREATE TABLE app.sim_card (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL REFERENCES app.operator (id),
  iccid text NOT NULL CHECK (iccid ~ '^[0-9]{18,20}$'),
  provider text NOT NULL DEFAULT 'emnify' CHECK (provider IN ('emnify')),
  msisdn text NULL CHECK (msisdn ~ '^\+[1-9][0-9]{7,14}$'), apn text NULL CHECK (length(apn) <= 100),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deactivated')),
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT sim_card_iccid_key UNIQUE (iccid), CONSTRAINT sim_card_operator_iccid_key UNIQUE (operator_id, iccid)
);
-- rls: C + G
CREATE TABLE app.device (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL REFERENCES app.operator (id),
  imei text NOT NULL CHECK (imei ~ '^[0-9]{15}$'),
  model text NOT NULL, firmware text NULL, protocol text NOT NULL,
  capability_profile_id uuid NULL REFERENCES app.capability_profile (id), sim_iccid text NULL,
  status text NOT NULL DEFAULT 'stock' CHECK (status IN ('stock', 'installed', 'maintenance', 'retired')),
  traccar_device_id bigint NULL,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT device_operator_id_key UNIQUE (operator_id, id),
  CONSTRAINT device_sim_fk FOREIGN KEY (operator_id, sim_iccid) REFERENCES app.sim_card (operator_id, iccid)
);
CREATE UNIQUE INDEX device_imei_active_key ON app.device (imei) WHERE status <> 'retired';
CREATE UNIQUE INDEX device_sim_active_key ON app.device (sim_iccid) WHERE status <> 'retired';
-- rls: B
CREATE TABLE app.device_assignment (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL, tenant_id uuid NOT NULL, vehicle_id uuid NOT NULL, device_id uuid NOT NULL,
  cut_point text NULL CHECK (cut_point IN ('fuel_pump', 'ignition', 'starter')),
  is_primary boolean NOT NULL DEFAULT true,
  valid_from timestamptz NOT NULL DEFAULT now(), valid_to timestamptz NULL,
  installed_by uuid NULL, notes text NULL CHECK (length(notes) <= 2000), created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT device_assignment_period_chk CHECK (valid_to IS NULL OR valid_to > valid_from),
  CONSTRAINT device_assignment_vehicle_fk FOREIGN KEY (operator_id, tenant_id, vehicle_id) REFERENCES app.vehicle (operator_id, tenant_id, id),
  CONSTRAINT device_assignment_device_fk FOREIGN KEY (operator_id, device_id) REFERENCES app.device (operator_id, id),
  CONSTRAINT device_assignment_scope_key UNIQUE (operator_id, tenant_id, id),
  CONSTRAINT device_assignment_fact_key UNIQUE (operator_id, tenant_id, id, vehicle_id, device_id),
  CONSTRAINT device_assignment_device_excl EXCLUDE USING gist (device_id WITH =, tstzrange(valid_from, valid_to, '[)') WITH &&),
  CONSTRAINT device_assignment_primary_excl
    EXCLUDE USING gist (vehicle_id WITH =, tstzrange(valid_from, valid_to, '[)') WITH &&) WHERE (is_primary)
);
CREATE INDEX device_assignment_vehicle_idx ON app.device_assignment (operator_id, tenant_id, vehicle_id, valid_from DESC);
CREATE FUNCTION app.tg_device_assignment_close() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE last_fix timestamptz;
BEGIN
  IF OLD.valid_to IS NOT NULL AND (NEW.valid_to, NEW.cut_point) IS DISTINCT FROM (OLD.valid_to, OLD.cut_point) THEN
    RAISE EXCEPTION 'vínculo % já encerrado', OLD.id USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF OLD.valid_to IS NULL AND NEW.valid_to IS NOT NULL THEN
    SELECT max(p.fix_time) INTO last_fix FROM app.position p WHERE p.assignment_id = NEW.id AND p.fix_time >= NEW.valid_to;
    IF last_fix IS NOT NULL THEN
      RAISE EXCEPTION 'valid_to anterior a posição já gravada (%)', last_fix USING ERRCODE = 'integrity_constraint_violation';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER device_assignment_immutable BEFORE UPDATE ON app.device_assignment FOR EACH ROW
  EXECUTE FUNCTION app.tg_immutable_columns('operator_id', 'tenant_id', 'vehicle_id', 'device_id', 'is_primary', 'valid_from');
CREATE TRIGGER device_assignment_close BEFORE UPDATE ON app.device_assignment FOR EACH ROW EXECUTE FUNCTION app.tg_device_assignment_close();
-- rls: F + G (escrita só por tracksys_ingest; leitura definidora em app.device_ingest_probe)
CREATE TABLE app.ingest_inbox (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_instance text NOT NULL CHECK (source_instance ~ '^traccar-[a-z0-9-]+$'),
  kind text NOT NULL CHECK (kind IN ('position', 'event')),
  source_event_id text NOT NULL CHECK (length(source_event_id) BETWEEN 1 AND 128),
  payload jsonb NULL, payload_sha256 bytea NULL CHECK (length(payload_sha256) = 32),
  received_at timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processed', 'quarantined', 'failed')),
  attempts smallint NOT NULL DEFAULT 0, next_attempt_at timestamptz NULL, processed_at timestamptz NULL,
  error text NULL CHECK (length(error) <= 2000),
  CONSTRAINT ingest_inbox_identity_key UNIQUE (source_instance, kind, source_event_id)
);
CREATE INDEX ingest_inbox_pending_idx ON app.ingest_inbox (next_attempt_at) WHERE status = 'pending';
CREATE INDEX ingest_inbox_quarantined_idx ON app.ingest_inbox (received_at) WHERE status = 'quarantined';
CREATE INDEX ingest_inbox_received_at_idx ON app.ingest_inbox (received_at);
-- rls: B (append-only)
CREATE TABLE app.position (
  fix_time timestamptz NOT NULL, received_at timestamptz NOT NULL, source_event_id text NOT NULL,
  operator_id uuid NOT NULL, tenant_id uuid NOT NULL, vehicle_id uuid NOT NULL, device_id uuid NOT NULL, assignment_id uuid NOT NULL,
  lat_e7 integer NULL CHECK (lat_e7 BETWEEN -900000000 AND 900000000),
  lon_e7 integer NULL CHECK (lon_e7 BETWEEN -1800000000 AND 1800000000), flags integer NOT NULL DEFAULT 0,
  speed_kmh_x10 smallint NULL CHECK (speed_kmh_x10 >= 0), course_deg smallint NULL CHECK (course_deg BETWEEN 0 AND 359),
  altitude_m smallint NULL, satellites smallint NULL CHECK (satellites BETWEEN 0 AND 99),
  ignition boolean NULL, valid boolean NOT NULL, extra jsonb NULL CHECK (pg_column_size(extra) <= 1024),
  CONSTRAINT position_pkey PRIMARY KEY (assignment_id, fix_time),
  CONSTRAINT position_assignment_fk FOREIGN KEY (operator_id, tenant_id, assignment_id, vehicle_id, device_id)
    REFERENCES app.device_assignment (operator_id, tenant_id, id, vehicle_id, device_id),
  CONSTRAINT position_coords_chk CHECK ((lat_e7 IS NULL) = (lon_e7 IS NULL) AND (NOT valid OR lat_e7 IS NOT NULL))
) PARTITION BY RANGE (fix_time);
CREATE SEQUENCE app.device_state_revision_seq;
-- rls: B + G
CREATE TABLE app.device_state (
  device_id uuid PRIMARY KEY, operator_id uuid NOT NULL, tenant_id uuid NULL, vehicle_id uuid NULL, assignment_id uuid NULL,
  revision bigint NOT NULL DEFAULT nextval('app.device_state_revision_seq'),
  last_contact_at timestamptz NULL, last_fix_at timestamptz NULL,
  lat_e7 integer NULL, lon_e7 integer NULL, speed_kmh_x10 smallint NULL, course_deg smallint NULL, ignition boolean NULL,
  motion text NOT NULL DEFAULT 'unknown' CHECK (motion IN ('moving', 'stopped', 'unknown')),
  relay_state text NOT NULL DEFAULT 'unknown' CHECK (relay_state IN ('blocked', 'unblocked', 'unknown')), relay_observed_at timestamptz NULL,
  power_state text NOT NULL DEFAULT 'unknown' CHECK (power_state IN ('main', 'battery', 'unknown')),
  aux jsonb NOT NULL DEFAULT '{}', updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT device_state_device_fk FOREIGN KEY (operator_id, device_id) REFERENCES app.device (operator_id, id),
  CONSTRAINT device_state_assignment_fk FOREIGN KEY (operator_id, tenant_id, assignment_id, vehicle_id, device_id)
    REFERENCES app.device_assignment (operator_id, tenant_id, id, vehicle_id, device_id),
  CONSTRAINT device_state_binding_chk CHECK (num_nulls(tenant_id, vehicle_id, assignment_id) IN (0, 3))
) WITH (fillfactor = 70);
CREATE INDEX device_state_scope_idx ON app.device_state (operator_id, tenant_id);
CREATE FUNCTION app.tg_device_state_revision() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.revision := greatest(nextval('app.device_state_revision_seq'), OLD.revision + 1);  -- INV-04 por construção
  NEW.updated_at := now();
  RETURN NEW;
END $$;
CREATE TRIGGER device_state_revision BEFORE UPDATE ON app.device_state FOR EACH ROW EXECUTE FUNCTION app.tg_device_state_revision();
CREATE TRIGGER device_state_immutable BEFORE UPDATE ON app.device_state FOR EACH ROW EXECUTE FUNCTION app.tg_immutable_columns('device_id', 'operator_id');
-- rls: A + G
CREATE TABLE app.outbox (
  id bigserial PRIMARY KEY, operator_id uuid NOT NULL REFERENCES app.operator (id), tenant_id uuid NULL,
  type text NOT NULL CHECK (type ~ '^[a-z]+(\.[a-z_]+)+\.v[0-9]+$'), entity_id uuid NOT NULL, payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz NULL,
  CONSTRAINT outbox_tenant_fk FOREIGN KEY (operator_id, tenant_id) REFERENCES app.tenant (operator_id, id)
);
CREATE INDEX outbox_unpublished_idx ON app.outbox (id) WHERE published_at IS NULL; CREATE INDEX outbox_created_at_idx ON app.outbox (created_at);
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['capability_profile', 'sim_card', 'device', 'device_assignment', 'ingest_inbox', 'position', 'device_state', 'outbox'] LOOP
    EXECUTE format('ALTER TABLE app.%I ENABLE ROW LEVEL SECURITY, FORCE ROW LEVEL SECURITY', t);
  END LOOP;
  FOREACH t IN ARRAY ARRAY['device_assignment', 'position', 'device_state'] LOOP                       -- tipo B
    EXECUTE format($p$CREATE POLICY %1$s_staff_all ON app.%1$I FOR ALL
      USING (operator_id = app.current_operator_id() AND app.current_scope() = 'operator')
      WITH CHECK (operator_id = app.current_operator_id() AND app.current_scope() = 'operator')$p$, t);
    EXECUTE format($p$CREATE POLICY %1$s_tenant_read ON app.%1$I FOR SELECT
      USING (operator_id = app.current_operator_id() AND app.current_scope() = 'tenant' AND tenant_id = ANY (app.current_tenant_ids()))$p$, t);
  END LOOP;
  FOREACH t IN ARRAY ARRAY['sim_card', 'device'] LOOP                                                  -- tipo C
    EXECUTE format($p$CREATE POLICY %1$s_staff_all ON app.%1$I FOR ALL
      USING (operator_id = app.current_operator_id() AND app.current_scope() = 'operator')
      WITH CHECK (operator_id = app.current_operator_id() AND app.current_scope() = 'operator')$p$, t);
  END LOOP;
  FOREACH t IN ARRAY ARRAY['device', 'device_state', 'ingest_inbox'] LOOP                              -- tipo G
    EXECUTE format('CREATE POLICY %1$s_definer_read ON app.%1$I FOR SELECT TO tracksys_owner USING (true)', t);
  END LOOP;
  -- operator_definer_read é compartilhada com a T-006 (04 §3.2): cria só se ainda não existir.
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'app' AND tablename = 'operator' AND policyname = 'operator_definer_read') THEN
    CREATE POLICY operator_definer_read ON app.operator FOR SELECT TO tracksys_owner USING (true);
  END IF;
  FOREACH t IN ARRAY ARRAY['outbox', 'capability_profile'] LOOP
    EXECUTE format('CREATE POLICY %1$s_owner_all ON app.%1$I FOR ALL TO tracksys_owner USING (true) WITH CHECK (true)', t);
  END LOOP;
END $$;
CREATE POLICY outbox_isolation ON app.outbox FOR ALL                                                  -- tipo A
  USING (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())))
  WITH CHECK (operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids())));
CREATE POLICY capability_profile_read ON app.capability_profile FOR SELECT TO tracksys_app, tracksys_ingest USING (true);
CREATE POLICY ingest_inbox_ingest_all ON app.ingest_inbox FOR ALL TO tracksys_ingest USING (true) WITH CHECK (true);
GRANT USAGE ON SCHEMA app TO tracksys_ingest;
GRANT EXECUTE ON FUNCTION app.current_operator_id(), app.current_scope(), app.current_tenant_ids() TO tracksys_ingest;
GRANT SELECT ON app.capability_profile TO tracksys_app, tracksys_ingest;
GRANT SELECT, INSERT, UPDATE ON app.sim_card, app.device, app.device_assignment, app.device_state TO tracksys_app;
GRANT SELECT ON app.position TO tracksys_app; GRANT SELECT, INSERT ON app.outbox TO tracksys_app;
GRANT SELECT ON app.device, app.device_assignment TO tracksys_ingest; GRANT SELECT, INSERT ON app.position, app.outbox TO tracksys_ingest;
GRANT SELECT, INSERT, UPDATE ON app.device_state TO tracksys_ingest;
GRANT SELECT, INSERT, UPDATE, DELETE ON app.ingest_inbox TO tracksys_ingest;
GRANT USAGE ON SEQUENCE app.outbox_id_seq, app.device_state_revision_seq TO tracksys_app, tracksys_ingest;
```

Em seguida, no mesmo arquivo, **copie literalmente** de [04 §4.4](../docs/spec/04-dominio-e-dados.md) (bloco `F0 · 9/9`) as funções `app.resolve_device_for_ingest(text, text)`, `app.list_operator_ids(boolean)`, `app.outbox_claim(integer)`, `app.list_silent_devices(timestamptz)` e `app.ensure_partitions(integer)`, o `REVOKE ALL ... FROM PUBLIC` e os `GRANT EXECUTE` delas, **omitindo** `app.memberships_for_user` (T-006). Única alteração: o segundo laço de `ensure_partitions` (partições de `access_log`) fica dentro de `IF to_regclass('app.access_log') IS NOT NULL THEN … END IF;`, porque `access_log` nasce na T-006. Copie também, literalmente, a sonda de [11 §10](../docs/spec/11-onboarding-e-migracao.md) (REQ-ONB-019): `app.device_ingest_probe(uuid)`, o índice `ingest_inbox_quarantine_uid_idx`, o `REVOKE ALL ... FROM PUBLIC` e o `GRANT EXECUTE ... TO tracksys_app` (ela lê `ingest_inbox` pela política `ingest_inbox_definer_read` e `device` pela `device_definer_read`). Depois `SELECT app.ensure_partitions();` e o perfil:

```sql
INSERT INTO app.capability_profile (model, firmware_range, protocol, version, capabilities, status)
VALUES ('J16', '*', 'gt06', 1, $json$<conteúdo literal de packages/testkit/fixtures/j16/capability-profile.draft.json>$json$::jsonb, 'draft');

-- migrate:down
DROP FUNCTION app.device_ingest_probe(uuid), app.ensure_partitions(integer), app.list_silent_devices(timestamptz), app.outbox_claim(integer),
  app.list_operator_ids(boolean), app.resolve_device_for_ingest(text, text);
DROP TABLE app.outbox, app.device_state, app.position, app.ingest_inbox, app.device_assignment, app.device, app.sim_card, app.capability_profile;
DROP SEQUENCE app.device_state_revision_seq; DROP FUNCTION app.tg_device_state_revision(), app.tg_device_assignment_close();
DROP TRIGGER vehicle_immutable ON app.vehicle; DROP TRIGGER tenant_immutable ON app.tenant;
-- Ficam: app.tg_immutable_columns e operator_definer_read (compartilhadas com a T-006, 04 §3.2)
```

### (2) CAT-07 e allowlist

`catalog-allowlist.json` (chaves da T-001 validadas por `z.strictObject`) recebe, sem apagar entradas já existentes (ex.: as da T-006):
- `withoutOperatorId` (CAT-03): `"capability_profile": "catálogo de modelos de rastreador compartilhado entre operadoras; escrita só por migration do dono"` e `"ingest_inbox": "custódia bruta antes de resolver o dono; acesso só de tracksys_ingest e da sonda definidora"`;
- `nullableTenantId`: `device_state` e `outbox` (textos de [04 §5.1](../docs/spec/04-dominio-e-dados.md));
- `appendOnly`: `"position"`;
- `securityDefiner` (chave nova, formato de [04 §5.1](../docs/spec/04-dominio-e-dados.md): assinatura → justificativa ≥ 10 caracteres), com estas 6 chaves (mais `app.memberships_for_user(uuid)`, se a T-006 já estiver em `main`): `app.resolve_device_for_ingest(text, text)`, `app.list_operator_ids(boolean)`, `app.outbox_claim(integer)`, `app.list_silent_devices(timestamp with time zone)`, `app.ensure_partitions(integer)` (justificativa = coluna "Por que existe" de [04 §4.4](../docs/spec/04-dominio-e-dados.md)) e `app.device_ingest_probe(uuid)` (`"sonda de quarentena por rastreador para o aviso de C05; só agregados no escopo operator (11 §10)"`).

Se a T-006 ainda não entregou a CAT-07, esta tarefa estende o `CatalogAllowlistSchema` (`z.strictObject`) com `securityDefiner: z.record(z.string(), z.string().min(10)).default({})` (o teste congelado da T-001 continua compilando) e `CatalogRule` com `'CAT-07'`; se já entregou, só acrescenta as entradas. A regra é a mesma nos dois cartões:

| Violação CAT-07 (schema `app`, `prosecdef`; `object` = `'app.' \|\| p.proname \|\| '(' \|\| oidvectortypes(p.proargtypes) \|\| ')'`, ex.: `app.tmp_definer()`) | Mensagem |
|---|---|
| Função fora de `securityDefiner` | `função SECURITY DEFINER fora da allowlist` |
| Chave de `securityDefiner` sem função | `allowlist cita função inexistente` |
| `proconfig` sem o item `search_path=pg_catalog, pg_temp` | `search_path não fixado` |
| `has_function_privilege('public', p.oid, 'EXECUTE')` | `executável por PUBLIC` |
| `pg_get_userbyid(p.proowner) <> 'tracksys_owner'` | `dono diferente de tracksys_owner` |

Qual papel executa cada função não fica na allowlist: os testes de aceite provam o 42501 do papel errado (seção "Testes de aceite", `schema.test.ts`).

### (3) Contratos (`packages/contracts`)

- `TraccarPositionEnvelope`: `z.looseObject({ position, device })`; `position.deviceId` inteiro obrigatório; `id` inteiro ≥ 0 opcional [VALIDAR — DEC-02: o forward traz `position.id`; padrão seguro: sem id e perfil `traccar_id` → quarentena `missing_source_id`]; `latitude`/`longitude` números (faixa vira quarentena, não 400); `fixTime`, `deviceTime`, `serverTime` em `z.iso.datetime({ offset: true })`; `fixTime` obrigatório se `outdated !== true`; `attributes` registro livre (padrão `{}`); `device = { id: int, uniqueId: string 1..64, name? }`. `TraccarEventEnvelope`: `{ event: { id, type, eventTime, deviceId, positionId?, attributes? }, position?, device }` [VALIDAR — DEC-02].
- `CapabilityProfileBase`: 11 chaves `yes|no|unknown` obrigatórias, `normalization` **opcional** (campos de [05 §13](../docs/spec/05-ingestao-e-telemetria.md); ausente = `generic-traccar/1`), chaves extras permitidas (`commands`, `evidence`; a T-016 estende).
- `TelemetryPositionAcceptedV1` e `DeviceStateUpdatedV1`: campos exatos dos exemplos de [05 §10](../docs/spec/05-ingestao-e-telemetria.md); `changes` ⊆ `location|ignition|motion|relayState|powerState|batteryLevel|lastContact|alarm`; `cause` ∈ `position|heartbeat|event`; `processingMode` ∈ `live|reprocess|backfill|replay`.

### (4) Domínio puro (`@tracksys/domain`)

| Export | Contrato |
|---|---|
| `resolveProfile(caps: unknown \| null)` | Perfil efetivo; sem perfil → `generic-traccar/1` (tudo `unknown`, `traccar_id`); `normalizationProfile = '<model>/<version>'` |
| `normalizeTraccar(env, profile)` | Tabela de [05 §4](../docs/spec/05-ingestao-e-telemetria.md); único ponto de conversão (INV-12); ausente → `null`/`'unknown'` (INV-03) |
| `checkTimeWindow(fixTime, receivedAt, profile)` | `[receivedAt − 30 d, receivedAt + 120 s]`; códigos `fix_time_in_future`, `fix_time_too_old`, `wnro_suspect`; WNRO soma 619.315.200 s só com `wnro_correction = true` (flag 64; padrão `false` até o spike provar o defeito [VALIDAR — DEC-02]) |
| `decideProjection(state, msg, profile)` | Plano: linha de `position` ou `null`, campos de `device_state` + `aux`, `changes`, `transitions`, flags; regras de [05 §4.2, §8, §9](../docs/spec/05-ingestao-e-telemetria.md); sem mudança → plano sem update |
| `POSITION_FLAGS`, `decodePositionFlags(n)` | Bits de [05 §4.1](../docs/spec/05-ingestao-e-telemetria.md) → nomes (usado pela T-018) |
| `haversineM(a, b)` | Raio 6.371.008,8 m |

`aux` guarda `fixSourceEventId`, `statusAt`, `statusSourceEventId`, `slowSince`, `lastStored {latE7, lonE7, fixTime}`, `lastAlarm`, `batteryLevel`, `batteryV`, `totalDistanceM`, `odometerM`, `hoursS`. Ordem de localização: `(fix_time, source_event_id)` com id comparado como inteiro (texto, se `fp1:`).

### (5) Aplicador (`@tracksys/db`)

`ingestTraccar(pool, { kind, envelope, receivedAt, sourceInstance, processingMode }, { faults? })` executa [05 §7](../docs/spec/05-ingestao-e-telemetria.md) como `tracksys_ingest`, **com estas correções vinculantes** (decisões 1–4): resolve por `app.resolve_device_for_ingest(sourceInstance, device.uniqueId)`; contexto `scope = 'operator'` com o `operator_id` devolvido; **sem** o `INSERT` defensivo em `device_state` (a linha nasce com o `device`, [04 §3.5](../docs/spec/04-dominio-e-dados.md); ausente → erro `device_state_missing`, fica `pending`); `SELECT … FOR UPDATE` em `device_state`; confere `device.traccar_device_id = position.deviceId` (NULL ou diferente → `device_identity_mismatch`); lê o vínculo com `p_at ∈ [valid_from, valid_to)` sob RLS (vínculo já encerrado e `receivedAt > valid_to + 24 h` → quarentena `closed_assignment_late`, [04 §9.1](../docs/spec/04-dominio-e-dados.md) [PREMISSA: 24 h]; o aceite CT-DAD-018 é da T-007); `UPDATE device_state` só se o plano mudar algo, `RETURNING revision` (o gatilho atribui); `position` com `ON CONFLICT (assignment_id, fix_time) DO NOTHING`. Devolve `{ result, inboxId }`. `insertOutboxEvent(client, { operatorId, tenantId, type, entityId, payload })` valida o payload no schema do tipo, insere e chama `pg_notify('outbox_new', id)`; a projeção também emite `pg_notify('device_state', '{"d","o","t","v","r"}')` só com ids e revisão. `reprocessPending(pool, { now, limit = 100 })`: chama o aplicador com `processingMode = 'reprocess'` (os eventos da outbox levam esse valor e nenhum consumidor gera efeito externo com eles, INV-05); `FOR UPDATE SKIP LOCKED` por `next_attempt_at <= now`, mesma transação, esperas 2/8/32/120 s × U[0,75; 1,25], 5ª falha → `quarantined` com `projection_failed: <erro>` e log `error`. Regressão de id: máximo em memória por `(source_instance, kind)` das últimas 24 h; id > 10.000 abaixo → `source_id_regression`.

### (6) Listener interno do `api`

`IngestionModule` entra no `InternalModule` da T-004 (Fastify via NestJS 11, `bodyLimit: 262144`, porta `INTERNAL_PORT`, só rede Docker; mesmo processo do `api` em produção). `internal-main.ts` (script `start:internal`) sobe só o `InternalModule`, para o harness dos testes. Ordem: hook `onRequest` compara SHA-256 de `X-Ingest-Token` e do segredo com `timingSafeEqual` (401 `INGEST_UNAUTHORIZED`, sem ler corpo nem logar o valor) → 413 `INGEST_PAYLOAD_TOO_LARGE` → Zod (400 `INGEST_INVALID_ENVELOPE` com `errors[].path` em notação de pontos) → `ingestTraccar` com prazo de 5 s (`statement_timeout 4000ms`, `lock_timeout 1000ms`; falha antes do savepoint → 503 `INGEST_UNAVAILABLE` + `Retry-After: 5`) → 202 `{"result","inboxId"}`. Erros em `application/problem+json` com `code`. Rota `events`: `alarm` → fluxo de status (`cause = 'event'`, `observedAt = eventTime` [VALIDAR — DEC-02: campo e retentativa do forward de eventos; padrão seguro: tratar como sem retentativa, o alarme também chega no atributo `alarm` da posição]); demais tipos (inclusive `commandResult`) → inbox `processed` sem projeção. `GET /internal/healthz` → 200 `{"status":"ok"}`. Env validado por Zod (mesmas regras do `config/env.ts` da T-004): `INGEST_SHARED_SECRET` (≥ 32), `INGEST_SOURCE_INSTANCE` (`^traccar-[a-z0-9-]+$`), `DATABASE_URL_INGEST`, `INGEST_FAULTS` (JSON `{killBeforeCommit, killAfterCommit, failProjectionOnce}: string[]` de `sourceEventId`; **boot falha** se presente com `NODE_ENV ≠ test`).

### (7) Worker

`reprocess-pending.ts`: laço de 5 s com pool `DATABASE_URL_INGEST`; aceita `REPROCESS_FAULTS={"killBeforeCommit":[...]}` só em teste. `partitions.ts`: `SELECT app.ensure_partitions()` como `tracksys_app` no boot e às 00:17 UTC (`setTimeout` até o próximo horário; sem pg-boss); log `error` se a última partição de `position` cobre menos que hoje + 3 dias.

Relay (`outbox/relay.ts`, REQ-ARQ-009, [03 §6](../docs/spec/03-arquitetura.md) regras 2 a 4): `LISTEN outbox_new` numa conexão dedicada + varredura a cada 5 s, com o pg-boss do `worker` da T-004. Cada rodada, numa transação do `tracksys_app`: `SELECT * FROM app.outbox_claim(500)` e, para cada linha com rota em `routes.ts`, `send(fila, { eventId: outboxId, type, operatorId, tenantId, entityId }, { singletonKey: '<fila>:<outboxId>' })` com o mesmo client (opção `db` do `send` [VALIDAR — pg-boss 10]; plano B: `send` antes do claim, com o mesmo `singletonKey`); linha sem rota só é marcada publicada. `routes.ts` exporta `OUTBOX_ROUTES = {}` (a T-011 acrescenta `device.state.updated.v1 → alerts.evaluate`); `createRelay({ routes, listen })` e `runRelayOnce(client, routes)` aceitam mapa injetado nos testes. Payload do job só com ids (REQ-ARQ-010). `OUTBOX_RELAY=off` desliga o relay do `worker` e só é aceito com `NODE_ENV=test` (boot falha fora disso).

### (8) Testkit

`j16-fixtures.ts`: `loadJ16Fixture(dir, file)` e `deriveMovingPosition(base, { id, fixTime, serverTime, imei, traccarDeviceId })` (ignição `true`, `speed = 16.2` nós ≈ 30 km/h, demais campos da captura S03). `vertical-slice.ts`: `seedVerticalSlice(appPool)` cria, com `withContext` do `tracksys_app`, Alfa (A1, A2), Beta (B1), V1 (`TST1A23`, `car`, A1), V2 (`TST2B34`, `motorcycle`, B1), dois `device` com IMEI `86` + 13 dígitos aleatórios e `traccar_device_id` aleatório, vínculos primários (V1 com `cut_point = 'fuel_pump'`) e as linhas de `device_state` já vinculadas; devolve todos os ids.

## Testes de aceite (congelados)

`harness.ts` sobe `api` (`start:internal`) e `worker` como processos filhos com `INGEST_SOURCE_INSTANCE = traccar-t005-<aleatório>`, espera `healthz` e permite SIGKILL/reinício. Nenhum teste depende de banco limpo.

`schema.test.ts`
- Dado o schema migrado, Quando `runCatalogChecks(admin, loadCatalogAllowlist())`, Então `[]`. Dado, numa transação revertida, `CREATE FUNCTION app.tmp_definer() … SECURITY DEFINER` sem `search_path` e com EXECUTE a PUBLIC, Então aparecem `CAT-07 app.tmp_definer()` (fora da allowlist, sem `search_path`, PUBLIC).
- CT-DAD-006 com IMEIs aleatórios: `tracksys_ingest` resolve o IMEI `installed` → 1 linha `(device, operadora)`; `retired`, inexistente ou instância `'xx'` → 0 linhas; `tracksys_app` chamando → SQLSTATE 42501. `tracksys_ingest` chamando `list_operator_ids`, `outbox_claim`, `list_silent_devices`, `ensure_partitions` ou `device_ingest_probe` → 42501.
- CT-ONB-019 (parte de banco): Dado um rastreador da Alfa sem vínculo, com IMEI aleatório, e 4 linhas da inbox `quarantined` com `error = 'no_assignment'`, `payload #>> '{device,uniqueId}'` = esse IMEI e `received_at` na última hora, Quando o contexto `operator` da Alfa chama `app.device_ingest_probe(<id>)`, Então `quarantined_24h = 4` e `last_error = 'no_assignment'`; com o contexto `operator` da Beta ou o escopo `tenant` de A1, Então 1 linha com `quarantined_24h = 0` e `last_error` NULL.
- ISO-01 a ISO-05 para `device`, `device_assignment`, `position`, `device_state` e `outbox`; CT-DAD-002 (sem contexto, 0 linhas nas 5); CT-DAD-004: `tracksys_ingest` lendo `app.vehicle` → 42501; `tracksys_app` lendo `app.ingest_inbox` → 42501.
- CT-DAD-001, CT-DAD-007, CT-DAD-008 (inclusive `ON CONFLICT` com 1 linha e `lat_e7 = 910000000` → 23514); CT-DAD-009 (39 partições de `position`, todas com RLS forçada; 2ª chamada retorna 0; `fix_time` D + 23 dias → 23514); CT-DAD-011 1ª parte (`revision` gravada > 42 mesmo pedindo 42 ou 0).
- Dado o perfil J16, Então `capabilities` é igual ao `capability-profile.draft.json` e `status = 'draft'`.

`http.test.ts`: CT-ING-002 (401 em ≤ 100 ms, 0 linhas, nenhum log com `errado`), CT-ING-003 (262.145 bytes → 413; lock externo de 10 s em `device_state` → 202 `pending` em ≤ 2 s; `db` inacessível por URL inválida → 503 com `Retry-After: 5` em ≤ 5 s), CT-ING-004, CT-ING-005, CT-ING-010 e CT-ARQ-009 1ª parte (falha injetada → `pending`, `attempts = 1`, 0 `position`, 0 outbox, nenhum NOTIFY recebido por um `LISTEN` de teste e 0 job no pg-boss). CT-API-015: todas as capturas de `packages/testkit/fixtures/j16/` passam em `TraccarPositionEnvelope` ou `TraccarEventEnvelope`; a captura sem `position.deviceId` → 400 `INGEST_INVALID_ENVELOPE`. CT-ARQ-013 (sem a page): com a inbox já tendo (`<instância do harness>`, `position`, `938441`), uma posição de id `1` na mesma instância → quarentena `source_id_regression` e log `error` com esse código; com outra instância (`traccar-t005b-<aleatório>`), a mesma posição → `processed`.

`normalization.test.ts` (funções puras, valores exatos): CT-ING-006, CT-ING-007, CT-ING-009, CT-ING-011, CT-ING-012, CT-ING-013, CT-ING-017 (capacidade `'yes'` onde o capítulo diz `true`).

`reprocess.test.ts`: CT-ING-008 (vínculo A1 até T, A2 desde T; fix de T − 60 s → `tenant_id` A1 com flag 512; `device_state` de A2 sem nova revisão); CT-ING-014 (`transitions.ignition = {from:false,to:true}`, `revision`/`previousRevision` corretas, payload passa no Zod); CT-ING-015 1ª parte com `now` injetado (5 tentativas com esperas em [1,5; 2,5], [6; 10], [24; 40], [90; 150] s e `quarantined` com `projection_failed`). INV-05 (REQ-QLD-009, parte da T-005): a mensagem projetada por `reprocessPending` grava `telemetry.position.accepted.v1` e `device.state.updated.v1` com `processingMode = 'reprocess'`.

`relay.test.ts` (CT-ARQ-009 2ª parte), com `runRelayOnce`/`createRelay` em processo e rota de teste `{ 'telemetry.position.accepted.v1': 'arq.probe' }` (fila da T-004); o `worker` do harness sobe com `OUTBOX_RELAY=off` (aceito só com `NODE_ENV=test`, como `INGEST_FAULTS`) para não disputar a outbox, e as asserções olham só os ids gravados pelo teste: Dado o relay com `listen: false`, Quando 10 eventos são gravados com `insertOutboxEvent`, Então os 10 viram jobs `arq.probe` com `singletonKey = 'arq.probe:<outboxId>'` e `published_at` preenchido em ≤ 10 s; uma 2ª rodada cria 0 job; uma linha de tipo sem rota (`device.state.updated.v1` com `OUTBOX_ROUTES` vazio) fica com `published_at` preenchido e 0 job. A 3ª parte do CT-ARQ-009 (`alert_delivery` único) é da T-012.

`vertical-slice.test.ts` — CT-NEG-017 (parte de ingestão e banco) e CT-ING-022. Dado `seedVerticalSlice` e P0…P4 derivados de S03 com ids `990100 + i` e `fix_time` P1 = agora − 60 s, P2 − 45 s, P3 − 30 s, P4 − 15 s, P0 − 10 min:
- Quando P1 chega 10 vezes, Então 10 × 202 (1 `processed`, 9 `duplicate`) e a revisão de V1 não muda após a 1ª.
- Quando P2 chega com `killBeforeCommit`, Então a conexão cai e nada é gravado; reiniciado o `api` sem essa falha, o reenvio dá `processed`. Quando P3 chega com `killAfterCommit`, Então o reenvio após reinício dá `duplicate`.
- Quando P4 chega com `failProjectionOnce` (202 `pending`) e o worker morre com `killBeforeCommit` no reprocessamento, Então o worker reiniciado deixa a linha `processed`.
- Quando P0 chega por último, Então vai para `position` com flag `LATE` (1) e `device_state.last_fix_at` = `fix_time` de P4.
- Então: 5 linhas `processed` na inbox e 5 em `position`; revisões observadas após cada passo nunca diminuem; na outbox, 5 `telemetry.position.accepted.v1` e nenhum par repetido de `(type, source.sourceEventId)`; contexto `tenant` de A2 e `operator` da Beta contam 0 em `position` e `device_state` de V1; `INSERT` em `app.position` por `tracksys_ingest` com contexto da Beta e `tenant_id` de A1 → 42501.

`ingestion.property.test.ts` (fast-check, `numRuns: 25`, 1 operadora, 2 dispositivos novos por execução): P1–P4 de [05 §16](../docs/spec/05-ingestao-e-telemetria.md) chamando `ingestTraccar`. Em P2, o conjunto de `position` usa `fix_time` distintos; o empate de `fix_time` é coberto pela versão pura (`numRuns: 1000`), que precisa falhar com contraexemplo de 2 fixes se o desempate por id for removido (CT-ING-020). A versão pura de P1–P4 (`packages/domain/test/ingestion.property.test.ts`) roda em todo PR com `numRuns: 1000` e imprime a seed na falha (REQ-QLD-009).

## Comandos de verificação

```bash
pnpm install
pnpm db:reset && pnpm db:migrate
pnpm db:check                                    # Catálogo OK: nenhuma violação de CAT-01..CAT-07.
pnpm --filter @tracksys/domain test              # propriedades puras (numRuns 1000)
pnpm test:acceptance -- tests/acceptance/T-005
pnpm verify                                      # T-001, T-002 e T-005 verdes (inclui db:rollback + db:migrate)
pnpm db:rollback && pnpm db:migrate
```

## Definição de pronto

- [ ] Comandos acima verdes local e no CI; rollback e novo `up` funcionam; `tests/acceptance/T-001/**` e `T-002/**` intactos; `T-005/**` congelado no PR.
- [ ] Demonstração ao vivo com o J16 de bancada (passo 1 de [02 §3](../docs/spec/02-escopo-e-fases.md)) registrada em `docs/runbooks/gates/G0.md`.
- [ ] PR `feat(ingestion): Traccar → inbox → projeção (T-005)` citando REQ, INV-01..07 e INV-12, CT-NEG-017 (parcial), risco N1 com trechos N0, revisão cruzada de outro fornecedor e as decisões 1–4 desta tabela.

## Decisões já tomadas (não pergunte, siga)

| Dúvida provável | Resposta |
|---|---|
| 1. [05 §6](../docs/spec/05-ingestao-e-telemetria.md) e [04 §4.4](../docs/spec/04-dominio-e-dados.md) dão assinaturas diferentes para `resolve_device_for_ingest` | Vale [04](../docs/spec/04-dominio-e-dados.md) (`source_instance, unique_id` → `device_id, operator_id`); o vínculo é lido depois, sob RLS e com o lock de `device_state`. |
| 2. Contexto da projeção: `tenant` ([05 §7](../docs/spec/05-ingestao-e-telemetria.md)) ou `operator`? | `operator` ([04 §4.1](../docs/spec/04-dominio-e-dados.md) item 4): tabelas tipo B recusam escrita no escopo `tenant`. |
| 3. Revisão: `nextval` no UPDATE ou gatilho? Apagar `device_state` ao encerrar vínculo? | Gatilho `device_state_revision`; não passe `revision`. A linha nunca é apagada ([04 §3.5](../docs/spec/04-dominio-e-dados.md)). Vínculo vigente ≠ `device_state.assignment_id` → erro `device_state_binding_mismatch` (fica `pending`; quem religa é a T-007). |
| 4. Unicidade de `position`: PK de [04](../docs/spec/04-dominio-e-dados.md) ou índice proposto em [05 §5](../docs/spec/05-ingestao-e-telemetria.md)? | PK `(assignment_id, fix_time)`. Mesmo `fix_time` com outro id grava 1 linha (a primeira); a localização usa o desempate por id; sem linha nova, sem `telemetry.position.accepted.v1`. |
| 5. `true`/`null` de [05](../docs/spec/05-ingestao-e-telemetria.md) nas capacidades? | Leia `"yes"`/`"unknown"` (T-002). Campos de `normalization` mantêm os tipos de [05 §13](../docs/spec/05-ingestao-e-telemetria.md). |
| 6. Chave de inbox sem `position.id` | Sempre `fp1:` + SHA-256 (o perfil só é conhecido depois de resolver); com perfil `traccar_id`, quarentena `missing_source_id` na mesma linha. |
| 7. Usar pg-boss ou Kysely aqui? | Kysely não: reprocessamento é laço simples e o aplicador usa SQL explícito com `pg` (savepoint e ordem de [05 §7](../docs/spec/05-ingestao-e-telemetria.md)). pg-boss só no relay, com a instância e o schema da T-004 (sem migration de fila: o relay nasce sem rota). As rotas para filas de consumidor entram na T-011. |
| 8. Quais funções `SECURITY DEFINER` e políticas G esta tarefa cria? | As 6 da seção (1) e `device_`, `device_state_`, `ingest_inbox_definer_read`, `outbox_` e `capability_profile_owner_all`; `operator_definer_read` com guarda de existência e `tg_immutable_columns` com `CREATE OR REPLACE`, porque a T-006 faz o mesmo (a ordem de merge não importa e o `down` não os apaga). Se já houver outra função em `main` (ex.: `memberships_for_user` da T-006), mantenha a entrada dela em `securityDefiner`: o CAT-07 roda sobre o catálogo real. |
| 12. Tabelas sem `operator_id` passam na CAT-03? | Só com entrada em `withoutOperatorId`: `capability_profile` e `ingest_inbox`, no mesmo PR (seção 2). Toda FK das tabelas novas liga `operator_id → operator_id` e `tenant_id → tenant_id` (ou `tenant_id → id` em `app.tenant`) na mesma posição (CAT-04). |
| 13. REQ-ARQ-009 aqui, se o primeiro consumidor é da T-011? | Sim (dono da outbox e do relay, decisão da v2.0). O relay já roda no F0 marcando publicadas as linhas sem rota; a T-011 só acrescenta a rota. |
| 9. IMEI do J16 nas fixtures × unicidade de IMEI | Testes trocam `uniqueId` e `deviceId` por valores aleatórios do `seedVerticalSlice`; o IMEI real só aparece na demonstração manual, nunca no repositório. |
| 10. T-002 atrasou | Sessão 1 (migration, CAT-07, domínio) não depende dela; perfil fica com as 11 chaves `unknown` até o PR da T-002, e o aceite da fatia vertical espera as capturas. Não fabrique captura. |
| 11. Onde fica a parte HTTP/SSE de CT-NEG-017? | Na T-008 (depende de T-005 e T-006). Aqui só ingestão e banco. |
