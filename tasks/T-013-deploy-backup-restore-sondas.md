# T-013 — Deploy por tag, backup WAL-G, restore testado e sondas do F0

| Campo | Valor |
|---|---|
| Fase | F0 (semana S3: 21–27/10/2026; marco 27/10: restore registrado) |
| Requisitos | REQ-OPS-006, REQ-OPS-007, REQ-OPS-008 (WAL-G e retenção; a cópia na R2 é da T-033), REQ-OPS-009, REQ-OPS-016 (Sentry com `beforeSend`; Alloy e Loki são da T-033), REQ-OPS-017 (subconjunto do F0 por sonda local e UptimeRobot; as regras no Grafana são da T-033); REQ-ARQ-012 (limites de recurso no compose; o teste de carga é da T-033); REQ-DAD-020 (expand/contract no deploy e `migration-safety`; o `migration-compat` é da T-033); REQ-ING-021 (parte F0: sonda de atraso da ingestão com page no Pushover; as métricas Prometheus completas de [05 §17](../docs/spec/05-ingestao-e-telemetria.md#17-métricas-de-ingestão) são da T-028, F1); REQ-ARQ-014 (redação de logs como segunda linha); REQ-NEG-010 (evidência do G0-7); REQ-QLD-011 (a única tabela nova é `ops.audit_log`, fora de `app`: ISO-01..ISO-05 não se aplicam; os privilégios e a CAT-06 são provados no `ops-schema.test.ts`, com Postgres real) |
| Invariantes | INV-05 (restore de ensaio sem push, comando ou SMS), INV-07 (verificador de catálogo antes de trocar o código), INV-12 (UTC, segundos) |
| Risco de revisão | N0 pelo caminho: `.github/workflows/ci.yml` (job `migration-safety` e `acceptance-report`), `packages/db/migrations/20261021130000_ops_auditoria.sql`, `packages/db/catalog-allowlist.json` e `packages/db/src/catalog.ts` (CAT-06), `infra/scripts/deploy.sh` (aplica migrations em produção; REQ-OPS-007 é N0); demais arquivos N1. Revisor de outro fornecedor e leitura humana linha a linha só nos arquivos N0 |
| Depende de | T-003, T-004 (`infra/app/Dockerfile`, `/health/ready`). O fake de FCM de `external-effects.test.ts` (`packages/testkit/src/fakes/fcm.ts`) tem plano B local: se a T-012 ainda não o entregou, este cartão o cria |
| Estimativa | 3 sessões de agente (1: migration `ops`, `deploy.sh`, `smoke.sh`, `migration-safety` e CI; 2: backup, retenção, restore, ensaio e `EXTERNAL_EFFECTS`; 3: sondas locais, Sentry, UptimeRobot, limites de recurso) + ~4 h do fundador |
| Bloqueado por decisão | DEC-04 (padrão: smoke e sondas usam o `TRACKSYS_DOMAIN` provisório; trocar = variável + registros A). DEC-12 (padrão: F0 sem standby ativa, ensaio de restore na primária, RTO ≤ 2 h) |
| Tipo | **Mista:** o agente escreve scripts, configuração e testes locais; o fundador cadastra segredos e executa a verificação na VM (agente sem credencial de produção, REQ-QLD-016) |

## Objetivo

Fechar o ciclo de operação essencial do F0 sobre a VM da T-003, com o fundador no comando:
- release por tag (`ssh deploy@tracksys-p <tag>`, forced-command) com migrations expand/contract, verificador de catálogo e rollback automático;
- base diária WAL-G no Object Storage da Oracle (WAL contínuo já arquivando desde a T-003), retenção 7 + 4 e **1 restore ensaiado** em ambiente isolado, com worker sem efeito externo (G0-7);
- sondas de ingestão, disco, backup e arquivamento com page no Pushover, UptimeRobot e Sentry sem dado pessoal.

Deploy por Action, Grafana, carga e cópia R2 são da [T-033](T-033-operacao-avancada-deploy-observabilidade-carga.md).

## Contexto obrigatório

- [13 §6 a §8, §10 a §12, §13.1, §18](../docs/spec/13-infra-e-operacao.md#6-configuração-e-segredos): segredos, deploy, backups, SLO, observabilidade, alertas, paging.
- [Anexo C R8 e §3](../docs/anexos/C-operacional.md#3-checklist-de-go-live-do-piloto-zero-g0-31102026): restore real e checklist do G0.
- [ADR-005](../docs/adr/ADR-005-infra-oracle-always-free.md) §6–§7; [T-003](T-003-vm-primaria-compose-firewall-dns.md) (não repita o que ela entrega).
- [03 §11](../docs/spec/03-arquitetura.md#11-orçamento-de-recursos-vm-de-12-gb-2-ocpu-ampere) e REQ-ARQ-012 (limites de recurso); [04 §10](../docs/spec/04-dominio-e-dados.md#10-migrations-expandcontract) e REQ-DAD-020 (expand/contract, N/N+1); [05 §17](../docs/spec/05-ingestao-e-telemetria.md#17-métricas-de-ingestão) e REQ-ING-021 (limiares de page da ingestão).

## Escopo — fazer

**Agente:**
1. Migration `ops` (seção 1) e CAT-06 cobrindo `ops.audit_log`.
2. `deploy.sh`, `smoke.sh`, job `migration-safety` e artefato `acceptance-report` no CI (seção 2).
3. Compose de produção alinhado à imagem única da T-004, alvo `migrate` e teste dos limites de [03 §11](../docs/spec/03-arquitetura.md#11-orçamento-de-recursos-vm-de-12-gb-2-ocpu-ampere) (seção 3).
4. Scripts e timers de backup, retenção, restore real e restore de ensaio; `EXTERNAL_EFFECTS` no worker (seção 4).
5. Sentry com `beforeSend`, `metrics-textfile.sh`, `disk-cleanup.sh`, sonda de atraso da ingestão e `host-watch.sh` com page no Pushover (seções 5 e 5.1).
6. Runbooks `docs/runbooks/infra/{deploy,backup-restore,sondas-e-alertas}.md` e testes de aceite locais.

**Fundador (com os runbooks):**
7. Chave pública do deploy no usuário `deploy` da VM e `DEPLOY_KNOWN_HOSTS` na máquina dele; deploy só em dia útil sem feriado, 08:00–19:59 BRT.
8. UptimeRobot; Pushover; Sentry; variáveis novas no `prod.env.sops`.
9. Verificação na VM (bloco "Na VM") com saídas anexadas ao PR; restore de ensaio até 27/10/2026.

## Fora do escopo

- Deploy por GitHub Action (`deploy.yml`), rollback disparado pelo CI, Alloy, Grafana Cloud, Alertmanager, regras AL-08, AL-11 e AL-12, `migration-compat`, teste de carga e cópia R2: [T-033](T-033-operacao-avancada-deploy-observabilidade-carga.md) (F1).
- VM standby ativa, réplica, Uptime Kuma (a sonda de atraso da ingestão do F0 roda por timer na primária, seção 5.1; vai para o Kuma da standby no F1, T-028), status page, gateway de incidentes, agente SRE, `ops.slo_*` e funções `SECURITY DEFINER` do schema `ops`: F1.
- Spool de auditoria com o banco fora (REQ-OPS-021) e escalonamento automático de 10 min: F1 (gateway).
- Consultas do G0 e relatório de evidências: T-015 (consome o relatório de restore e o artefato `acceptance-report` desta tarefa).
- SDK do Sentry no console (`apps/console`): T-007 (`VITE_SENTRY_DSN` opcional). Aqui só o DSN de produção como variável de build do console e o host de ingestão do Sentry no `connect-src` da CSP de `app.`.
- Métricas Prometheus da ingestão no `api` (`ingest_*` de 05 §17 expostas em `/metrics`): T-028 (F1). CT-DAD-012 de desempenho: T-034 (F1).

## Arquivos a criar/alterar

```
.github/workflows/ci.yml                              (alterar: migration-safety; verify gera acceptance-report.json)
packages/db/migrations/20261021130000_ops_auditoria.sql   (timestamp distinto do 20261021120000_alertas.sql da T-011)
packages/db/catalog-allowlist.json, packages/db/src/catalog.ts   (CAT-06 cobre ops.audit_log)
infra/app/Dockerfile                                  (alterar: alvo migrate)  · infra/app/migrate-entrypoint.sh
infra/docker-compose.yml                              (alterar: sem perfil app; imagens tracksys-app / tracksys-migrate)
infra/docker-compose.drill.yml · infra/db/pg_hba.drill.conf
infra/scripts/deploy.sh · smoke.sh · check-migration-safety.sh · disk-cleanup.sh · metrics-textfile.sh
infra/scripts/lib/{audit,page,metrics}.sh
infra/scripts/backup/{base-backup,retain,restore,restore-drill}.sh · infra/scripts/backup/drill-sink.mjs
infra/scripts/probes/{uptimerobot-check,ingest-lag,host-watch}.sh
infra/caddy/sites/primary.caddy                       (alterar: host de ingestão do Sentry no connect-src de app.)
infra/systemd/tracksys-{backup,backup-retain,metrics,disk-cleanup,ingest-lag,host-watch}.{service,timer}
infra/scripts/provision.sh                            (alterar: timers e sudoers do deploy)
infra/env/prod.env.example, infra/env/ci.env, .env.example   (alterar: variáveis novas)
apps/worker/src/config/env.ts                         (alterar: EXTERNAL_EFFECTS)
apps/worker/src/integrations/null-adapters.ts
apps/api/src/observability/sentry.ts · apps/worker/src/observability/sentry.ts
packages/domain/src/observability/scrub-sentry-event.ts
docs/runbooks/infra/deploy.md · backup-restore.md · sondas-e-alertas.md
tests/acceptance/T-013/{ops-schema,deploy-script,migration-safety,backup-scripts,drill-compose,external-effects,sentry-scrub,resource-limits,host-watch,ingest-lag}.test.ts
tests/acceptance/T-013/fixtures/**                    (fakes de docker/git/wal-g/curl, backup-list.json)
```

## Especificação detalhada

### (1) Schema `ops` — SQL exato

```sql
-- migrate:up
-- T-013 — Auditoria de operação de plataforma (13 §4.4). Fora de app: não guarda dado de operadora ou cliente.
SET LOCAL lock_timeout = '5s'; SET LOCAL statement_timeout = '60s';
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'tracksys_ops_audit') THEN
    RAISE EXCEPTION 'papel tracksys_ops_audit ausente: aplique infra/db/roles.sql (T-003) antes';
  END IF;
END $$;
CREATE SCHEMA IF NOT EXISTS ops;
REVOKE ALL ON SCHEMA ops FROM PUBLIC;
CREATE TABLE ops.audit_log (
  id uuid PRIMARY KEY,                                   -- gerado pelo script; reenvio com ON CONFLICT DO NOTHING
  actor_type text NOT NULL CHECK (actor_type IN ('user', 'system', 'ai_agent')),
  actor_id text NOT NULL CHECK (length(actor_id) BETWEEN 1 AND 200),
  action text NOT NULL CHECK (action ~ '^ops\.[a-z_]+$'),
  target text NULL CHECK (length(target) <= 200),
  reason text NULL CHECK (length(reason) <= 500),
  result text NOT NULL CHECK (result IN ('success', 'denied', 'error')),
  incident_id text NULL CHECK (length(incident_id) <= 100),
  host text NOT NULL CHECK (length(host) BETWEEN 1 AND 100),
  at timestamptz NOT NULL,
  detail jsonb NOT NULL DEFAULT '{}' CHECK (pg_column_size(detail) <= 8192)
);
CREATE INDEX audit_log_at_idx ON ops.audit_log (at);
GRANT USAGE ON SCHEMA ops TO tracksys_ops_audit;
GRANT INSERT ON ops.audit_log TO tracksys_ops_audit;
GRANT SELECT (id) ON ops.audit_log TO tracksys_ops_audit;   -- exigido pelo ON CONFLICT (id)

-- migrate:down
DROP TABLE ops.audit_log;
DROP SCHEMA ops;                                         -- sem CASCADE: falha se outra tarefa já usa o schema
```

CAT-06 (redação endurecida da T-001: `UPDATE` inclusive só em uma coluna por `has_any_column_privilege`, `DELETE` ou `TRUNCATE`):
- `appendOnly` aceita nome qualificado (`"ops.audit_log"`); sem ponto continua `app.<t>` (o teste congelado da T-001 não muda).
- Para cada entrada existente, há violação se `tracksys_app`, `tracksys_ops_audit` ou `tracksys_ops_ro` (os que existirem) tiver qualquer desses privilégios; `object` = nome qualificado.
- O schema `ops` fica fora de CAT-01..CAT-04 (não é `app`) e não leva entrada em `withoutOperatorId`.
- Se `pnpm db:reset` não criar `tracksys_ops_audit`/`tracksys_ops_ro` em dev e CI (initdb da T-003), passe `OPS_RO_PASSWORD`/`OPS_AUDIT_PASSWORD` de desenvolvimento no `.env.example` e no `docker-compose.yml` da raiz.


### (2) Deploy manual assistido, smoke e guarda de migrations

O fundador publica a tag em `main` depois do CI verde e roda `ssh deploy@tracksys-p vX.Y.Z` (forced-command). Janela: dia útil sem feriado, 08:00–19:59 BRT, disciplina registrada no runbook. A janela automática e a Action são da T-033.

**CI (`ci.yml`):**
- O passo de testes do `verify` vira `pnpm test:acceptance -- --reporter=default --reporter=json --outputFile=acceptance-report.json` e publica o artefato `acceptance-report` (retenção 90 dias; usado no G0-6 pela T-015).
- Job novo `migration-safety` em PR: `infra/scripts/check-migration-safety.sh --base origin/${{ github.base_ref }}`.

**`check-migration-safety.sh --base <ref> | --changed-files <arquivo>`:**
- Lista os arquivos alterados e examina, em cada `packages/db/migrations/*.sql` alterado ou novo, **só** o trecho entre `-- migrate:up` e `-- migrate:down`, sem comentários.
- Padrões destrutivos (sem diferenciar maiúsculas): `DROP COLUMN`, `DROP TABLE`, `RENAME`, `ALTER COLUMN … TYPE`, `SET NOT NULL`.
- Falha (`exit 1`, citando arquivo e padrão) se houver padrão em arquivo sem sufixo `_contract.sql`.
- Falha se um arquivo `_contract.sql` vier no mesmo PR que algum arquivo em `apps/**`.
- Falha se uma migration já existente em `origin/main` foi modificada.

**`infra/scripts/deploy.sh`** (forced-command; caminhos sobrescrevíveis por `TRACKSYS_ROOT=/opt/tracksys`, `TRACKSYS_ETC=/etc/tracksys`, `TRACKSYS_RUN=/run/tracksys` para os testes):
1. Argumento = `$1` ou, sem argumento, `$SSH_ORIGINAL_COMMAND`. Aceita só `^(build-only )?v[0-9]+\.[0-9]+\.[0-9]+$` ou `^rollback$`; outro → `exit 2` com "comando recusado", auditoria `ops.deploy` `denied`, sem nenhuma outra ação. `flock -n $TRACKSYS_RUN/deploy.lock` (ocupado → `exit 2`).
2. Passos 1–8 de [13 §7](../docs/spec/13-infra-e-operacao.md#7-deploy), com estas regras adicionais: recusa árvore suja (`git status --porcelain` não vazio); build = `dc build` (imagens `tracksys-app:<tag>`, `tracksys-migrate:<tag>`, `tracksys-caddy:<tag>`); migrations = `dc run --rm migrate up`; catálogo = `dc run --rm migrate check`. Ordem expand/contract (REQ-DAD-020): migrations e catálogo **antes** de trocar o código; o rollback de código nunca roda `rollback` de migration ([04 §10](../docs/spec/04-dominio-e-dados.md#10-migrations-expandcontract) item 3), porque toda migration funciona com o código da versão anterior.
3. Códigos de saída: `0` sucesso; `1` falha no `up`/smoke com rollback concluído (page prioridade 1 "deploy <tag> revertido para <PREV>"); `3` falha antes de trocar o código (fetch, ancestralidade, árvore suja, build, migration ou catálogo; page prioridade 1 "deploy <tag> abortado: <etapa>"; `current-version` intacto); `4` smoke do rollback falhou (page prioridade 2, SEV1).
4. Auditoria (`lib/audit.sh`): `dc exec -T -u postgres db psql -X -v ON_ERROR_STOP=1 -d tracksys` com `SET ROLE tracksys_ops_audit; INSERT INTO ops.audit_log … ON CONFLICT (id) DO NOTHING` (`id` de `/proc/sys/kernel/random/uuid`, `action` ∈ `ops.deploy`, `ops.deploy_rollback`, `actor_type = 'system'`, `actor_id = 'founder:ssh'` (chamada pelo forced-command) ou `'root:<SUDO_USER|root>'`, `host = $(hostname)`, `detail` com tag, `PREV`, etapa e código). Falha na auditoria só gera aviso no stderr (sem spool no F0).
5. `DEPLOY_FAULT=smoke|catalog` simula a falha da etapa **só** quando o processo é root sem `SUDO_USER` (execução manual pelo fundador na VM; o `sudo` do usuário `deploy` limpa o ambiente) e grava `detail.fault`. Usado no CT-OPS-006/007 na VM sem publicar release quebrada em `main`.

**`smoke.sh <tag>`**, os itens do passo 6 de [13 §7](../docs/spec/13-infra-e-operacao.md#7-deploy), cada um imprimindo `OK <item>` ou `FALHOU <item>`:
1. `curl -fsS --max-time 10 https://api.$TRACKSYS_DOMAIN/health/ready` contém `"status":"ok"`.
2. `docker inspect` das imagens de `api` e `worker` termina em `:<tag>`.
3. `/health/ready` do worker (`172.30.0.11:3002`) responde 200.
4. `https://app.$TRACKSYS_DOMAIN/version.json` contém a tag.
5. `nc -z -w 5 gps.$TRACKSYS_DOMAIN 5023`.
6. Se havia sessões TCP antes do deploy (`nsenter -t <pid do traccar> -n ss -Htn state established '( sport = :5023 )'` ≥ 1), `extract(epoch FROM now() − max(received_at))` de `app.ingest_inbox` (como `postgres`, transação `READ ONLY`) fica < 120 em até 120 s.
7. A soma de `http_requests_total{status=~"5.."}` em `172.30.0.10:3001/metrics` é igual antes e depois.

**`provision.sh` (alterar):** `/etc/sudoers.d/tracksys-deploy` exatamente `Defaults:deploy env_keep += "SSH_ORIGINAL_COMMAND"` e `deploy ALL=(root) NOPASSWD: /opt/tracksys/infra/scripts/deploy.sh`, validado com `visudo -cf`; instala os timers das seções 4 e 5 na primária.

### (3) Compose, imagem de migração e limites de recurso

- `infra/docker-compose.yml`: `api` e `worker` sem `profiles`, `image: tracksys-app:${TRACKSYS_VERSION}`, `build: { context: .., dockerfile: infra/app/Dockerfile, target: app }` (imagem única da T-004; `worker` com `command` do processo worker). `migrate` (perfil `ops`): `image: tracksys-migrate:${TRACKSYS_VERSION}`, `target: migrate`, `environment: DATABASE_URL: ${MIGRATE_DATABASE_URL}`. Limites e healthchecks da T-003 inalterados.
- `infra/app/Dockerfile`, alvo `migrate`: `node:24-bookworm-slim` com o binário `dbmate` do pacote npm (arquitetura do build), `packages/db/migrations/` e `check-catalog.js` (esbuild de `packages/db/scripts/check-catalog.ts`, com `catalog-allowlist.json` ao lado). `migrate-entrypoint.sh up` → `dbmate --migrations-dir /app/migrations --no-dump-schema --wait up`; `check` → `node /app/check-catalog.js`; outro argumento → `exit 64`. Usuário `node`.
- Limites de [03 §11](../docs/spec/03-arquitetura.md#11-orçamento-de-recursos-vm-de-12-gb-2-ocpu-ampere) (`mem_limit`, `cpus`) de `db`, `api` e `worker` declarados no `infra/docker-compose.yml`; o teste `resource-limits.test.ts` compara o `docker compose config` com a tabela do capítulo.

### (4) Backup, restore e efeitos externos

| Peça | Regra |
|---|---|
| `backup/base-backup.sh` (timer 06:00 UTC) | `dc exec -T -u postgres db wal-g backup-push /var/lib/postgresql/data`; sucesso → `tracksys_backup_last_success_timestamp_seconds` e `tracksys_backup_base_size_bytes` em `/var/lib/tracksys/metrics/backup.prom` (`lib/metrics.sh`: escreve em `.tmp` e `mv`, atômico); falha → `exit 1` (o alerta AL-04 cobre) |
| `backup/retain.sh` (07:00 UTC) | Lê `wal-g backup-list --json --detail`; domingo (UTC): `wal-g backup-mark <base do dia>`; bases permanentes com mais de 28 dias: `wal-g backup-mark -i <base>`; depois `wal-g delete retain FULL 7 --confirm` [VALIDAR flags na versão fixada] |
| `backup/restore.sh --target-time <RFC 3339> \| --target-name <nome>` | Restore real do [Anexo C R8](../docs/anexos/C-operacional.md) passo 3 em host novo: volume `db-data` vazio, `wal-g backup-fetch … LATEST`, `recovery.signal`, `recovery_target_*`, `recovery_target_action = 'promote'`; recusa rodar se `db-data` não estiver vazio |
| `backup/restore-drill.sh` (manual no F0) | Ensaio de [13 §8](../docs/spec/13-infra-e-operacao.md#8-backups-e-restore) itens 1–7, com o projeto `tracksys-drill` desta tabela |
| `infra/docker-compose.drill.yml` | Projeto `tracksys-drill`. Redes: `drill-internal` (`internal: true`, `172.31.0.0/24`) e `drill-egress` (bridge). `db`: imagem `tracksys-db:17`, nas 2 redes (só ele alcança o object storage), volume próprio `drill-db-data`, `mem_limit: 1536m`, `command` com `-c archive_mode=off -c shared_buffers=256MB -c hba_file=/etc/postgresql/pg_hba.conf` montando `infra/db/pg_hba.drill.conf`. `worker`: `tracksys-app:${TRACKSYS_VERSION}`, só `drill-internal`, `mem_limit: 512m`, `env_file: /run/tracksys/drill.env`. `sink`: mesma imagem, `node /drill/drill-sink.mjs`, só `drill-internal`. `migrate`: `tracksys-migrate`, perfil `ops`. Nenhuma porta publicada |
| `pg_hba.drill.conf` | `local all postgres peer` · `local all all scram-sha-256` · `host tracksys tracksys_app,tracksys_ingest,tracksys_owner 172.31.0.0/24 scram-sha-256` · `host all all 0.0.0.0/0 reject` |
| `drill-sink.mjs` | `node:http` na 8080; conta toda requisição exceto `GET /__count` (que devolve `{"requests":N}`); nunca loga corpo nem cabeçalho |

**`restore-drill.sh`**, em ordem:
1. `START` = agora, `T` = `START − 10 min`.
2. Contagens da produção como `postgres` pelo socket, em `BEGIN READ ONLY`: `count(*)` de `app.position` por `received_at` e de `app.audit_log` por `at` em `[T − 24 h, T − 5 min)`.
3. `wal-g backup-fetch` no volume vazio e `recovery_target_time = T`.
4. Espera `pg_isready` e `pg_is_in_recovery() = false` (máx. 2 h) e marca `READY`.
5. No restaurado: `max(received_at)` de `app.ingest_inbox` (perda = `max(0, T − max)`), mesmas contagens e `dc run --rm migrate check`.
6. Gera `/run/tracksys/drill.env` a partir do `prod.env`, com `DATABASE_URL_*` para o `db` do projeto, `EXTERNAL_EFFECTS=off`, `COMMAND_DISPATCH_ENABLED=false`, `EMNIFY_SMS_ENABLED=false`, `FCM_API_BASE=http://sink:8080`, `TRACCAR_API_URL=http://sink:8080` e `SENTRY_DSN=` vazio.
7. Sobe `sink` e `worker` por 10 min e lê `/__count`.
8. Derruba o projeto com `down -v`, grava `/var/lib/tracksys/restore/AAAA-MM-DD.md` e `tracksys_restore_drill_last_success_timestamp_seconds` (só se `result: ok`). O fundador copia o relatório para `docs/runbooks/restore/`.

**Relatório do ensaio** (front matter lido pela T-015, chaves exatas):
- `drill: restore`, `date`, `host`, `base`, `targetTime`, `startedAt`, `readyAt`;
- `durationSeconds` (`READY − START`), `lossSeconds`, `countsMatch` (boolean), `catalogOk`, `externalCalls` (do `sink`);
- `result`: `ok` se `durationSeconds ≤ 7200`, `lossSeconds ≤ 300`, `countsMatch`, `catalogOk` e `externalCalls = 0`; senão `falhou`;
- corpo com a tabela de contagens produção × restaurado. Sem IMEI, coordenada, e-mail ou segredo.

**`EXTERNAL_EFFECTS` no worker:** variável obrigatória (`on` \| `off`, Zod). Ausente ou outro valor: `exit 78` citando o nome.
- Com `off`, o adaptador FCM vira `NullPushSender`: nenhuma requisição, entrega gravada como `suppressed` com `error = 'external_effects_off'`.
- Com `off`, o cliente Traccar vira `NullTraccarClient`: saúde `unknown` e qualquer outra chamada lança `EXTERNAL_EFFECTS_DISABLED`.
- Cada supressão loga `msg=external_effect_suppressed adapter=<fcm|traccar>` em `warn` e incrementa `external_effects_suppressed_total{adapter}`; o boot loga `msg=external_effects_off`.
- Adaptadores futuros (emnify, Asaas, e-mail) seguem a mesma regra. `.env.example` e `prod.env.example` = `on`.

### (5) Sondas locais, Sentry e UptimeRobot

- `metrics-textfile.sh` (timer 15 s): `tracksys_tcp_established{port="5023"}` pelo `ss` no namespace do contêiner `traccar` (`nsenter`).
- `disk-cleanup.sh` (timer 05:00 UTC): `journalctl --vacuum-size=300M`, logs rotacionados, imagens `tracksys-*` além das 3 últimas tags; nunca toca em volumes.
- **Sentry** (`@sentry/node`, major estável atual, só em `api` e `worker`; dependência nova justificada no PR, porque a T-004 adiou o SDK para esta tarefa):
  - inicializa só com `SENTRY_DSN` não vazio, com `sendDefaultPii: false`, `release: TRACKSYS_VERSION`, `tracesSampleRate: 0.05` e `beforeSend: scrubSentryEvent`;
  - `scrubSentryEvent` (puro, em `packages/domain`) remove `request.data`, `request.query_string`, `request.cookies` e os headers `authorization`, `cookie`, `x-ingest-token`, `asaas-access-token` (sem diferenciar maiúsculas);
  - troca sequências de 15 dígitos por `***` + 4 últimos em `message` e `exception.values[].value`.
- **CSP do console:** `infra/caddy/sites/primary.caddy` acrescenta `{$SENTRY_CSP_HOST}` (origem de ingestão do DSN do console, ex.: `https://o<id>.ingest.us.sentry.io` [VALIDAR]) ao `connect-src` de `app.`; vazio → nada muda. O build do console recebe `VITE_SENTRY_DSN` (SDK da T-007). Host de estilo/tiles extra registrado pela T-008 entra aqui também.
- **UptimeRobot** (free, 5 min; cadastrado pelo fundador): `slo-gps-tcp` (porta, `gps.<domínio>:5023`) e `slo-api-https` (palavra-chave `"status":"ok"` em `https://api.<domínio>/health/ready`), alerta Pushover prioridade 2 no F0 (única sonda externa = AL-01/AL-02) [VALIDAR integração Pushover no plano free; senão e-mail + app UptimeRobot]. `probes/uptimerobot-check.sh` (`UPTIMEROBOT_READ_API_KEY`, `POST https://api.uptimerobot.com/v2/getMonitors` [VALIDAR API]) sai 0 só se os 2 monitores existem, `interval = 300` e estão `up`.
- `host-watch.sh` (timer `tracksys-host-watch`, 60 s, na primária; REQ-OPS-017, subconjunto do F0 sem Grafana):
  - quatro regras, cada uma com uma page por episódio, pelo `lib/page.sh`;
  - estado em `$TRACKSYS_RUN/host-watch.<regra>.state` com o instante da 1ª leitura ruim; nova page só depois de 15 min sem a condição;
  - corpo da page só com números e o runbook.

| Regra | Condição | Page |
|---|---|---|
| `AL-03` | uso de `/` (`df --output=pcent /`) > 80% por ≥ 5 min | Pushover prioridade 0, título `AL-03 SEV2` |
| `AL-03-SEV1` | uso de `/` > 90% por ≥ 5 min | prioridade 1, título `AL-03 SEV1` |
| `AL-04` | `time() − tracksys_backup_last_success_timestamp_seconds` > 93.600 s em `backup.prom`, ou arquivo ausente | prioridade 2 (emergência), título `AL-04 SEV2` |
| `AL-05` | `pg_stat_archiver` (como `postgres`, `READ ONLY`): `now() − last_archived_time` > 300 s com `xact_commit` crescendo desde a leitura anterior, ou `failed_count` maior que o da leitura de 5 min antes | prioridade 0, título `AL-05 SEV2` |

Variáveis novas (`prod.env.example`, vazias salvo indicação; `ci.env`, fictícias):
- `SENTRY_DSN`, `VITE_SENTRY_DSN`, `SENTRY_CSP_HOST`, `EXTERNAL_EFFECTS`, `UPTIMEROBOT_READ_API_KEY`.
- `TRUSTED_PROXY_CIDRS=172.30.0.2/32` (preenchida: IP do `caddy` na rede da T-003; valor de produção de [13 §6](../docs/spec/13-infra-e-operacao.md#6-configuração-e-segredos), registrado em [15 §5](../docs/spec/15-decisoes-riscos-premissas.md#5-propostas-de-decisão-registradas-nos-capítulos); o `api` da T-006 só confia em `X-Forwarded-For` vindo dele).
- Nomes de banco canônicos da T-001: `DATABASE_URL_APP` e `DATABASE_URL_INGEST` nos apps; `MIGRATE_DATABASE_URL` só no `migrate` (injetado como `DATABASE_URL`); `DATABASE_URL_ADMIN` nunca no `prod.env`.

### (5.1) Sonda de atraso da ingestão (REQ-ING-021, parte F0)

`infra/scripts/probes/ingest-lag.sh` (timer `tracksys-ingest-lag`, a cada 60 s, na primária):
1. Consulta como `postgres` pelo socket em `BEGIN READ ONLY` (comando sobrescrevível por `TRACKSYS_PSQL` nos testes), só agregados: `count(*)` e `extract(epoch FROM now() − min(received_at))` de `app.ingest_inbox` com `status = 'pending'`, e `extract(epoch FROM now() − max(received_at))` de toda a inbox.
2. Grava `ingest_pending_count`, `ingest_pending_oldest_age_seconds` (0 sem `pending`) e `ingest_last_received_age_seconds` (ausente com inbox vazia, INV-03) em `/var/lib/tracksys/metrics/ingest.prom` por `lib/metrics.sh`.
3. Page pelo `lib/page.sh` (Pushover prioridade 1, título `AL-07 ingestão atrasada`, corpo só com números e o runbook) quando `ingest_pending_oldest_age_seconds > 300`.
4. Também pagina quando `ingest_last_received_age_seconds > 300` com `tracksys_tcp_established{port="5023"} ≥ 1` no textfile da seção 5 ([05 §17](../docs/spec/05-ingestao-e-telemetria.md#17-métricas-de-ingestão)).
5. Uma page por episódio: estado em `$TRACKSYS_RUN/ingest-lag.state`; nova page só depois de 15 min sem condição.
6. Funciona com o `worker` parado e sem Grafana Cloud. No F1, a T-028 passa a calcular as métricas no `api` (05 §17) e tira estas três do textfile.

## Testes de aceite (congelados)

Locais (`tests/acceptance/T-013/`, rodam no CI sem nuvem; scripts com `TRACKSYS_ROOT/ETC/RUN` em diretório temporário e `PATH` com os fakes de `fixtures/bin/` que gravam cada chamada):

- `ops-schema.test.ts` — Dado o schema migrado, Então `ops.audit_log` existe e `pnpm db:check` sai 0. Dado `tracksys_ops_audit`, Quando insere 2 vezes o mesmo `id` `0e7c9a7e-5b1a-4c55-9d1e-3f2a6b1c0d01` com `ON CONFLICT (id) DO NOTHING`, Então há 1 linha; Quando `UPDATE ops.audit_log SET result = 'success'`, Então SQLSTATE 42501; `tracksys_app` em `SELECT 1 FROM ops.audit_log` → 42501. Dado, numa transação desfeita, `GRANT UPDATE ON ops.audit_log TO tracksys_ops_audit`, Então `runCatalogChecks` contém `CAT-06 ops.audit_log`; o mesmo com `GRANT UPDATE (result) ON ops.audit_log TO tracksys_ops_audit` (só uma coluna) e com `GRANT TRUNCATE ON ops.audit_log TO tracksys_ops_ro`. Inserção com `action = 'deploy'` → 23514.
- `deploy-script.test.ts` (CT-OPS-006, CT-OPS-007 na parte local) — Dado `current-version = v0.3.0` e `SSH_ORIGINAL_COMMAND='bash'`, Então `exit 2`, stderr "comando recusado" e 0 chamadas a `docker`. Dado `v0.3.1` com o fake de `docker compose up --wait` saindo 1, Então há um 2º `up` com `TRACKSYS_VERSION=v0.3.0`, `current-version = v0.3.0`, o fake de `curl` registra 1 POST ao Pushover com `priority=1` e `exit 1`. Dado `v0.4.0` com o fake de `migrate check` saindo 1, Então nenhum `up` é chamado, `current-version = v0.3.0`, 1 page e `exit 3`. Dado `v0.3.2` saudável, Então `current-version = v0.3.2`, `previous-version = v0.3.0` e o fake de `psql` recebe 1 `INSERT INTO ops.audit_log` com `ops.deploy` e `success`. Dado tag fora de `origin/main`, Então `exit 3` sem build. Dado árvore suja, Então `exit 3`. Dado `DEPLOY_FAULT=smoke` com `SUDO_USER=deploy`, Então a variável é ignorada.
- `migration-safety.test.ts` (CT-OPS-007) — Dado `20261101000000_remove_nickname.sql` com `ALTER TABLE app.vehicle DROP COLUMN nickname` no `up`, Então `exit 1` citando `DROP COLUMN`; renomeado para `20261101000000_remove_nickname_contract.sql` e sem `apps/**` na lista, Então `exit 0`; com `apps/api/src/main.ts` na lista, Então `exit 1`. Dado `DROP TABLE app.x` só depois de `-- migrate:down`, Então `exit 0`. Dado `20261007120000_fundacao_isolamento.sql` modificado, Então `exit 1`.
- `backup-scripts.test.ts` (CT-OPS-008 na parte local) — Dado `fixtures/backup-list.json` com 15 bases diárias de 07/10/2026 (quarta) a 21/10/2026 e as de 11/10 e 18/10 permanentes, Quando `retain.sh` roda com `date` fixado em 25/10/2026 07:00Z (domingo), Então o fake de `wal-g` recebe `backup-mark` da base de 25/10, nenhum `backup-mark -i` (nenhuma permanente com mais de 28 dias) e `delete retain FULL 7 --confirm`; com `date` em 16/11/2026 (segunda), Então `backup-mark -i` da base de 11/10. `base-backup.sh` com sucesso grava `backup.prom` com `tracksys_backup_last_success_timestamp_seconds` inteiro e sem arquivo `.tmp` restante.
- `drill-compose.test.ts` (CT-OPS-009 na parte estática) — Dado `docker compose -f infra/docker-compose.drill.yml --env-file infra/env/ci.env config --format json`, Então `drill-internal` tem `internal: true`; `worker` e `sink` estão só nela; `db` está nas 2 redes e seu `command` contém `archive_mode=off`; nenhum serviço publica porta. Dado o `drill.env` gerado por `restore-drill.sh --render-env-only` a partir de `infra/env/ci.env`, Então contém `EXTERNAL_EFFECTS=off`, `COMMAND_DISPATCH_ENABLED=false`, `EMNIFY_SMS_ENABLED=false`, `FCM_API_BASE=http://sink:8080`, `TRACCAR_API_URL=http://sink:8080` e `SENTRY_DSN=` vazio.
- `external-effects.test.ts` (INV-05) — Dado o worker com `EXTERNAL_EFFECTS=off`, `FCM_API_BASE` apontando para o fake de FCM da T-012 e 1 entrega `pending` de `ignition_on`, Quando o job de entrega roda, Então o fake recebe 0 requisições, a entrega fica `suppressed` com `error = 'external_effects_off'`, o log tem `external_effect_suppressed` e `external_effects_suppressed_total{adapter="fcm"} = 1`. Dado `EXTERNAL_EFFECTS=talvez`, Então o worker sai com 78 citando `EXTERNAL_EFFECTS`.
- `sentry-scrub.test.ts` (CT-OPS-016, parte F0) — Dado um evento com header `Authorization: Bearer abc`, `request.data = {"senha":"x"}` e `query_string = "token=y"`, Quando `scrubSentryEvent`, Então não restam `authorization`, `data` nem `query_string`; uma mensagem com `359339000000001` sai com `***0001`. Dado `api` e `worker` no harness da T-005, Quando `/metrics` (3001 e 3002) é lido, Então nenhum rótulo se chama `vehicle_id`, `device_id`, `user_id`, `imei` ou `ip`. A redação de logs no Alloy é da T-033.
- `resource-limits.test.ts` (REQ-ARQ-012, parte F0) — Dado `docker compose -f infra/docker-compose.yml --env-file infra/env/ci.env config --format json`, Então `mem_limit` e `cpus` de `db`, `api` e `worker` são iguais aos de 03 §11 e nenhum serviço de aplicação usa `profiles: [app]`.
- `host-watch.test.ts` (CT-OPS-017, parte F0) — Com fakes de `df`, `psql` e `curl` e relógio injetável:
  - Dado `/` a 81% desde 5 min e 10 s, Quando `host-watch.sh` roda, Então 1 POST ao Pushover com `priority=0` e título `AL-03 SEV2`; a rodada seguinte → 0 POST novo.
  - Dado `/` a 81% só há 3 min, ou a 79%, Então 0 POST.
  - Dado `/` a 91% por 6 min, Então 1 POST com `priority=1` e título `AL-03 SEV1`.
  - Dado `backup.prom` com sucesso há 27 h, Então 1 POST com `priority=2` e título `AL-04 SEV2`; com sucesso há 25 h → 0 POST; arquivo ausente → 1 POST.
  - Dado `last_archived_time` há 400 s com `xact_commit` crescendo, Então 1 POST `AL-05 SEV2`; com `xact_commit` parado → 0 POST; com `failed_count` 3 → 4 em 5 min → 1 POST.
  - Dado a condição sumida por 16 min e depois de volta, Então nova page. Corpo sem IMEI nem coordenada.
- `ingest-lag.test.ts` (CT-ING-021, parte F0) — Dado o banco local migrado com o `worker` parado, `TRACKSYS_PSQL` apontando para o `psql` do `DATABASE_URL_ADMIN` e 1 linha `pending` em `app.ingest_inbox` com `received_at = now() − 301 s` (falha injetada), Quando `ingest-lag.sh` roda, Então `ingest.prom` tem `ingest_pending_oldest_age_seconds` ≥ 301 e `ingest_pending_count 1`, e o fake de `curl` registra exatamente 1 POST ao Pushover com `priority=1` e título `AL-07 ingestão atrasada`, sem IMEI nem coordenada no corpo; 2ª rodada 60 s depois → 0 POST novo; sem `pending` e `received_at` recente → `ingest_pending_oldest_age_seconds 0` e 0 POST; inbox vazia → `ingest_last_received_age_seconds` ausente do arquivo e 0 POST; último recebimento há 301 s com `tracksys_tcp_established{port="5023"} 3` no textfile → 1 page; com `0` sessões → 0 page.

Na VM (fundador; saídas anexadas ao PR):
- CT-OPS-006: `v0.x.0` publicado e saudável (`current-version` igual); `ssh deploy@tracksys-p bash` → "comando recusado"; como root `DEPLOY_FAULT=smoke deploy.sh v0.x.1` → `api` e `worker` voltam a `v0.x.0` em ≤ 5 min, 1 page; `ssh deploy@tracksys-p v0.x.1` sem falha → `current-version = v0.x.1`.
- CT-OPS-007: como root `DEPLOY_FAULT=catalog deploy.sh v0.x.2` → `exit 3`, versão anterior servindo, 1 page.
- CT-OPS-008: `pg_stat_archiver` a cada minuto por 10 min com `now() − last_archived_time` ≤ 120 s; 2 bases noturnas seguidas em `wal-g backup-list`; um objeto do bucket baixado sem a chave não abre como segmento de WAL. A conferência na R2 é da T-033; até lá o risco é aceito (decisão 15).
- CT-OPS-009 / G0-7: `restore-drill.sh` às 13:00 UTC até 27/10/2026 → relatório com `result: ok`, `durationSeconds ≤ 7200`, `lossSeconds ≤ 300`, `externalCalls: 0`; copiado para `docs/runbooks/restore/`.
- CT-ING-021 na VM: `systemctl list-timers tracksys-ingest-lag.timer tracksys-host-watch.timer` ativos e `ingest.prom` atualizado há < 120 s; nenhuma falha é provocada em produção (o caminho de page é provado pelo teste local), exceto `AL-03`.
- CT-OPS-017 / sondas: `uptimerobot-check.sh` sai 0; Pushover de emergência às 03:00 BRT reconhecido; `AL-03` provocado com `fallocate` até 81% por 5 min → 1 page prioridade 0 "AL-03 SEV2"; Sentry recebe erro de teste sem `authorization`.

## Comandos de verificação

```bash
pnpm install
pnpm db:reset && pnpm db:migrate && pnpm db:check   # Catálogo OK: nenhuma violação de CAT-01..CAT-07.
pnpm test:acceptance -- tests/acceptance/T-013
docker compose -f infra/docker-compose.yml --env-file infra/env/ci.env config --quiet
docker compose -f infra/docker-compose.drill.yml --env-file infra/env/ci.env config --quiet
docker run --rm -v "$PWD/infra":/infra koalaman/shellcheck:v0.10.0 $(cd infra && git ls-files '*.sh' | sed 's|^|/infra/|')
infra/scripts/check-migration-safety.sh --base origin/main
docker buildx build --platform linux/amd64,linux/arm64 --target migrate -f infra/app/Dockerfile .
pnpm verify
```

## Definição de pronto

- [ ] Testes locais da T-013 verdes; `migration-safety`, `secrets` e `infra-lint` verdes no PR.
- [ ] 1º deploy por tag (`ssh deploy@tracksys-p <tag>`) concluído; rollback e abort provados na VM (CT-OPS-006/007).
- [ ] WAL arquivando sem falha há ≥ 48 h; 2 bases noturnas.
- [ ] `docs/runbooks/restore/2026-10-2X.md` com `result: ok` no repositório até 27/10/2026 (G0-7).
- [ ] UptimeRobot e Pushover testados; timers `tracksys-ingest-lag` e `tracksys-host-watch` ativos na primária.
- [ ] PR `feat(infra): deploy por tag, backup WAL-G, restore e sondas (T-013)` com REQ/INV, `Risco declarado: N0` e revisão cruzada de outro fornecedor nos arquivos N0 indicados.

## Decisões já tomadas

| Dúvida provável | Resposta |
|---|---|
| 1. Qual Dockerfile vale para `api`, `worker` e `migrate`? | O `infra/app/Dockerfile` da T-004 (imagem única `tracksys-app`), que a T-003 já referencia; nenhum serviço usa `apps/api/Dockerfile` nem `apps/worker/Dockerfile`. Esta tarefa acrescenta o alvo `migrate` e tira o perfil `app` de `api` e `worker`, como a T-003 previu. |
| 2. `/health/ready` público ou só na 3001? | O smoke e as sondas usam `https://api.<domínio>/health/ready` ([13 §7, §10](../docs/spec/13-infra-e-operacao.md#7-deploy)): a 3000 pública da T-004 responde só `{"status":"ok"}` (ou 503 `{"status":"unavailable"}`), sem `checks`. O healthcheck do Docker fica em `127.0.0.1:3001/health/ready` (`api`) e `:3002` (`worker`). |
| 3. Onde roda o restore de ensaio no F0? | Na primária, em projeto isolado: a standby não roda contêiner no F0 (T-003). Limites somados do ensaio: ~2 GB. No F1 o ensaio mensal vai para a standby. |
| 4. O banco restaurado pode arquivar WAL? | Não. `archive_mode=off` no ensaio; senão ele empurraria uma nova timeline para o bucket de produção. |
| 5. Por que contagens da produção como `postgres`? | `tracksys_ops_ro` não tem USAGE em `app` e as funções `ops.*` são do F1. O acesso é pelo socket, em `READ ONLY`, só `count`/`max`, o mesmo caminho do `pg_create_restore_point` do deploy. |
| 6. Como provar rollback na VM sem release quebrada em `main`? | `DEPLOY_FAULT`, aceito só para root direto (o `sudo` do `deploy` limpa o ambiente) e auditado. Nunca crie migration de teste em `main`. |
| 7. `EXTERNAL_EFFECTS` tem padrão? | Não: obrigatória. Ausente derruba o boot (78). Desligar efeito por omissão esconderia push perdido; ligar por omissão quebraria o INV-05 no ensaio. |
| 8. Auditoria se o banco estiver fora? | No F0 só aviso no stderr. Spool idempotente é REQ-OPS-021 (F1). |
| 9. Escalonamento de SEV1 após 10 min sem recuperação? | F1 (gateway). No F0, AL-02 (UptimeRobot) e AL-04 já saem em prioridade 2. |
| 10. A T-008 registrou host extra na CSP do console? | Ajuste `infra/caddy/sites/primary.caddy` nesta tarefa e cite o PR da T-008. |
| 11. Agente pode cadastrar segredos ou rodar `deploy.sh` na VM? | Não (REQ-QLD-016). Escreve, testa com fakes, `shellcheck` e `--render-env-only`; o fundador executa. |
| 12. A sonda de atraso da ingestão do F0 é o Uptime Kuma? | Não: o Kuma roda na standby, que não tem contêiner no F0 (T-003). No F0 a sonda é o timer `tracksys-ingest-lag` na primária (seção 5.1), com page direto no Pushover; no F1 a T-028 a leva para o Kuma e para as métricas do `api`. |
| 13. O deploy do F0 é por Action? | Não: é manual assistido. O fundador roda `ssh deploy@tracksys-p <tag>` depois do CI verde, em dia útil sem feriado, 08:00–19:59 BRT. O `deploy.sh` (rollback automático, auditoria, smoke) é o mesmo que a T-033 passa a chamar pela Action. |
| 14. Sem Grafana no F0, quem avisa disco, backup e arquivamento? | O timer `host-watch.sh` (seção 5), com os mesmos limiares de AL-03, AL-04 e AL-05 e page pelo Pushover. A T-033 leva essas regras ao Grafana e acrescenta AL-08, AL-11 e AL-12. |
| 15. Onde fica a cópia do backup fora da Oracle? | Na T-033 (`copy-r2.sh`, até 15/11/2026). Até lá o backup vive só no Object Storage da Oracle, risco aceito e registrado em [15](../docs/spec/15-decisoes-riscos-premissas.md). |
| 16. Onde roda o teste de carga de 100 msg/s? | Na T-033, em workflow manual sobre banco descartável. Nunca na VM de produção: semearia 3.000 rastreadores falsos no banco real e disputaria memória com o piloto. |
