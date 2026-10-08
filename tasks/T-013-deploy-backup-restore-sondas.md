# T-013 — Deploy, backup WAL-G, restore testado e sondas

| Campo | Valor |
|---|---|
| Fase | F0 (semana S3: 21–27/10/2026; marco 27/10: restore registrado) |
| Requisitos | REQ-OPS-006, REQ-OPS-007, REQ-OPS-008, REQ-OPS-009, REQ-OPS-016, REQ-OPS-017; REQ-ARQ-014 (redação de logs como segunda linha); REQ-NEG-010 (evidência do G0-7) |
| Invariantes | INV-05 (restore de ensaio sem push, comando ou SMS), INV-07 (verificador de catálogo antes de trocar o código), INV-12 (UTC, segundos) |
| Risco de revisão | **N1** (tabela 2.3 de [02](../docs/spec/02-escopo-e-fases.md)). **Trechos N0:** `.github/workflows/**`, a migration do schema `ops`, a extensão do CAT-06 e `infra/scripts/deploy.sh` (aplica migrations em produção; REQ-OPS-007 é N0) → revisor de outro fornecedor e leitura humana linha a linha desses arquivos |
| Depende de | T-003. Usa artefatos já entregues: T-004 (`infra/app/Dockerfile`, `/health/ready`), T-012 (adaptador FCM, `FCM_API_BASE`) |
| Estimativa | 3 sessões de agente (13a deploy, migration `ops` e CI; 13b backup, restore e `EXTERNAL_EFFECTS`; 13c observabilidade, regras de alerta e sondas) + ~4 h do fundador |
| Bloqueado por decisão | DEC-04 (padrão: smoke e sondas usam o `TRACKSYS_DOMAIN` provisório; trocar = variável + registros A). DEC-12 (padrão: F0 sem standby ativa, ensaio de restore na primária, RTO ≤ 2 h) |
| Tipo | **Mista:** o agente escreve scripts, workflow, configuração e testes locais; o fundador cadastra segredos e executa a verificação na VM (agente sem credencial de produção, REQ-QLD-016) |

## Objetivo

Fechar o ciclo de operação do F0 sobre a VM da T-003: release por tag com migrations expand/contract, verificador de catálogo e rollback automático; base diária WAL-G + WAL contínuo (já arquivando desde a T-003) com retenção 7 + 4 e cópia na Cloudflare R2; **1 restore ensaiado** em ambiente isolado com worker sem efeito externo (G0-7); sonda externa (UptimeRobot) e regras de alerta do F0 no Pushover; logs, métricas e Sentry sem dado pessoal.

## Contexto obrigatório

- [13 §6 a §8, §10 a §12, §13.1, §18](../docs/spec/13-infra-e-operacao.md): segredos, deploy, backups, SLO, observabilidade, alertas, paging.
- [Anexo C R8 e §3](../docs/anexos/C-operacional.md): restore real e checklist do G0.
- [ADR-005](../docs/adr/ADR-005-infra-oracle-always-free.md) §6–§7; [T-003](T-003-vm-primaria-compose-firewall-dns.md) (não repita o que ela entrega).

## Escopo — fazer

**Agente:**
1. Migration `ops` (seção 1) e CAT-06 cobrindo `ops.audit_log`.
2. Workflow `deploy.yml`, `deploy.sh`, `smoke.sh`, job `migration-safety` e artefato `acceptance-report` no CI (seção 2).
3. Compose de produção alinhado à imagem única da T-004 e alvo `migrate` (seção 3).
4. Scripts e timers de backup, retenção, cópia R2, restore real e restore de ensaio; `EXTERNAL_EFFECTS` no worker (seção 4).
5. Alloy (métricas e logs com redação), textfile de métricas, Sentry com `beforeSend`, regras do F0 e Alertmanager (seção 5).
6. Runbooks `docs/runbooks/infra/{deploy,backup-restore,sondas-e-alertas}.md` e testes de aceite locais.

**Fundador (com os runbooks):**
7. Segredos do GitHub (`TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET`, `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS`), ambiente `production` restrito a tags `v*.*.*`, chave pública do CI no usuário `deploy`.
8. Bucket R2 com ciclo de vida de 35 dias e bucket lock de 14 dias [VALIDAR]; Grafana Cloud free; UptimeRobot; Pushover; variáveis novas no `prod.env.sops`.
9. Verificação na VM (bloco "Na VM") com saídas anexadas ao PR; restore de ensaio até 27/10/2026.

## Fora do escopo

- VM standby ativa, réplica, Uptime Kuma, status page, gateway de incidentes, agente SRE, `ops.slo_*` e funções `SECURITY DEFINER` do schema `ops`: F1.
- Spool de auditoria com o banco fora (REQ-OPS-021) e escalonamento automático de 10 min: F1 (gateway).
- Consultas do G0 e relatório de evidências: T-015 (consome o relatório de restore e o artefato `acceptance-report` desta tarefa).
- Sentry no console (`apps/console`): fora; registre no PR se a T-007 não o fez.

## Arquivos a criar/alterar

```
.github/workflows/deploy.yml                          (novo)
.github/workflows/ci.yml                              (alterar: migration-safety; verify gera acceptance-report.json)
packages/db/migrations/20261021120000_ops_auditoria.sql
packages/db/catalog-allowlist.json, packages/db/src/catalog.ts   (CAT-06 cobre ops.audit_log)
infra/app/Dockerfile                                  (alterar: alvo migrate)  · infra/app/migrate-entrypoint.sh
infra/docker-compose.yml                              (alterar: sem perfil app; imagens tracksys-app / tracksys-migrate)
infra/docker-compose.drill.yml · infra/db/pg_hba.drill.conf
infra/scripts/deploy.sh · smoke.sh · check-migration-safety.sh · disk-cleanup.sh · metrics-textfile.sh
infra/scripts/lib/{audit,page,metrics}.sh
infra/scripts/backup/{base-backup,retain,copy-r2,restore,restore-drill}.sh · infra/scripts/backup/drill-sink.mjs
infra/scripts/probes/uptimerobot-check.sh · infra/scripts/grafana-sync.sh
infra/systemd/tracksys-{backup,backup-retain,backup-copy,metrics,disk-cleanup}.{service,timer}
infra/systemd/alloy.service.d/10-tracksys.conf
infra/alloy/config.alloy · infra/alloy/redaction.alloy
infra/grafana/rules/f0.rules.yaml · f0.rules.test.yaml · infra/grafana/alertmanager.yaml.tpl
infra/scripts/provision.sh                            (alterar: timers, sudoers do deploy, Alloy)
infra/env/prod.env.example, infra/env/ci.env, .env.example   (alterar: variáveis novas)
apps/worker/src/config/env.ts                         (alterar: EXTERNAL_EFFECTS)
apps/worker/src/integrations/null-adapters.ts
apps/api/src/observability/sentry.ts · apps/worker/src/observability/sentry.ts
packages/domain/src/observability/scrub-sentry-event.ts
docs/runbooks/infra/deploy.md · backup-restore.md · sondas-e-alertas.md
tests/acceptance/T-013/{ops-schema,deploy-script,migration-safety,backup-scripts,drill-compose,external-effects,observability,alert-rules}.test.ts
tests/acceptance/T-013/fixtures/**                    (fakes de docker/git/wal-g/curl, backup-list.json, alloy-redaction.alloy)
```

## Especificação detalhada

### (1) Schema `ops` — SQL exato

```sql
-- migrate:up
-- T-013 — Auditoria de operação de plataforma (13 §4.4). Fora de app: não guarda dado de operadora ou cliente.
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

CAT-06: `appendOnly` aceita nome qualificado (`"ops.audit_log"`); sem ponto continua `app.<t>` (o teste congelado da T-001 não muda). Para cada entrada existente, violação se `tracksys_app`, `tracksys_ops_audit` ou `tracksys_ops_ro` (os que existirem) tiver `UPDATE` ou `DELETE`; `object` = nome qualificado. Se `pnpm db:reset` não criar `tracksys_ops_audit`/`tracksys_ops_ro` em dev e CI (initdb da T-003), passe `OPS_RO_PASSWORD`/`OPS_AUDIT_PASSWORD` de desenvolvimento no `.env.example` e no `docker-compose.yml` da raiz.

### (2) Deploy

`.github/workflows/deploy.yml`: `on: push: tags: ['v*.*.*']` e `workflow_dispatch` com `tag` (string, obrigatório) e `force` (boolean, padrão `false`); `concurrency: { group: deploy-production, cancel-in-progress: false }`; `permissions: contents: read`; toda action fixada por SHA de commit com a versão em comentário.
- Job `verify` (`ubuntu-24.04`): `actions/checkout` em `ref: ${{ inputs.tag || github.ref }}`; recusa tag fora de `^v[0-9]+\.[0-9]+\.[0-9]+$` ou que não seja ancestral de `origin/main`; repete os passos do job `verify` do `ci.yml`; publica o artefato `acceptance-report` (retenção 90 dias).
- Job `deploy` (`needs: verify`, `environment: production`, `timeout-minutes: 30`): janela `TZ=America/Sao_Paulo`: segunda a sexta, 08:00–19:59; fora dela só com `force: true` (senão falha com "fora da janela de deploy"); `tailscale/github-action` com OAuth client e `tags: tag:ci`; grava `DEPLOY_SSH_KEY` (0600) e `DEPLOY_KNOWN_HOSTS`; `ssh -o BatchMode=yes -o StrictHostKeyChecking=yes deploy@tracksys-p "$TAG"`; o código de saída do SSH é o do job.

`ci.yml`: o passo de testes do `verify` vira `pnpm test:acceptance -- --reporter=default --reporter=json --outputFile=acceptance-report.json` e publica `acceptance-report` (usado no G0-6 pela T-015). Job novo `migration-safety` em PR: `infra/scripts/check-migration-safety.sh --base origin/${{ github.base_ref }}`.

`check-migration-safety.sh --base <ref> | --changed-files <arquivo>`: lista os arquivos alterados; para cada `packages/db/migrations/*.sql` alterado ou novo, examina **só** o trecho entre `-- migrate:up` e `-- migrate:down`, sem comentários; padrões destrutivos (sem diferenciar maiúsculas): `DROP COLUMN`, `DROP TABLE`, `RENAME`, `ALTER COLUMN … TYPE`, `SET NOT NULL`. Falha (`exit 1`, citando arquivo e padrão) se houver padrão em arquivo sem sufixo `_contract.sql`, ou arquivo `_contract.sql` no mesmo PR que algum arquivo em `apps/**`; também falha se uma migration já existente em `origin/main` foi modificada.

`infra/scripts/deploy.sh` (forced-command; caminhos sobrescrevíveis por `TRACKSYS_ROOT=/opt/tracksys`, `TRACKSYS_ETC=/etc/tracksys`, `TRACKSYS_RUN=/run/tracksys` para os testes):
1. Argumento = `$1` ou, sem argumento, `$SSH_ORIGINAL_COMMAND`. Aceita só `^(build-only )?v[0-9]+\.[0-9]+\.[0-9]+$` ou `^rollback$`; outro → `exit 2` com "comando recusado", auditoria `ops.deploy` `denied`, sem nenhuma outra ação. `flock -n $TRACKSYS_RUN/deploy.lock` (ocupado → `exit 2`).
2. Passos 1–8 de [13 §7](../docs/spec/13-infra-e-operacao.md), com estas regras adicionais: recusa árvore suja (`git status --porcelain` não vazio); build = `dc build` (imagens `tracksys-app:<tag>`, `tracksys-migrate:<tag>`, `tracksys-caddy:<tag>`); migrations = `dc run --rm migrate up`; catálogo = `dc run --rm migrate check`.
3. Códigos de saída: `0` sucesso; `1` falha no `up`/smoke com rollback concluído (page prioridade 1 "deploy <tag> revertido para <PREV>"); `3` falha antes de trocar o código (fetch, ancestralidade, árvore suja, build, migration ou catálogo; page prioridade 1 "deploy <tag> abortado: <etapa>"; `current-version` intacto); `4` smoke do rollback falhou (page prioridade 2, SEV1).
4. Auditoria (`lib/audit.sh`): `dc exec -T -u postgres db psql -X -v ON_ERROR_STOP=1 -d tracksys` com `SET ROLE tracksys_ops_audit; INSERT INTO ops.audit_log … ON CONFLICT (id) DO NOTHING` (`id` de `/proc/sys/kernel/random/uuid`, `action` ∈ `ops.deploy`, `ops.deploy_rollback`, `actor_type = 'system'`, `actor_id = 'ci:<GITHUB_RUN_ID>'` ou `'root:<SUDO_USER|root>'`, `host = $(hostname)`, `detail` com tag, `PREV`, etapa e código). Falha na auditoria só gera aviso no stderr (sem spool no F0).
5. `DEPLOY_FAULT=smoke|catalog` simula a falha da etapa **só** quando o processo é root sem `SUDO_USER` (execução manual pelo fundador na VM; o `sudo` do usuário `deploy` limpa o ambiente) e grava `detail.fault`. Usado no CT-OPS-006/007 na VM sem publicar release quebrada em `main`.

`smoke.sh <tag>`: os 6 itens de [13 §7](../docs/spec/13-infra-e-operacao.md) passo 6, nesta forma: `curl -fsS --max-time 10 https://api.$TRACKSYS_DOMAIN/health/ready` contém `"status":"ok"`; `docker inspect` das imagens de `api` e `worker` termina em `:<tag>`; `/health/ready` do worker (`172.30.0.11:3002`) 200; `https://app.$TRACKSYS_DOMAIN/version.json` contém a tag; `nc -z -w 5 gps.$TRACKSYS_DOMAIN 5023`; sessões TCP antes do deploy por `nsenter -t <pid do traccar> -n ss -Htn state established '( sport = :5023 )'` — se ≥ 1, `extract(epoch FROM now() − max(received_at))` de `app.ingest_inbox` (como `postgres`, transação `READ ONLY`) < 120 em até 120 s; soma de `http_requests_total{status=~"5.."}` em `172.30.0.10:3001/metrics` igual antes e depois. Cada item imprime `OK <item>` ou `FALHOU <item>`.

`provision.sh` (alterar): `/etc/sudoers.d/tracksys-deploy` exatamente `Defaults:deploy env_keep += "SSH_ORIGINAL_COMMAND"` e `deploy ALL=(root) NOPASSWD: /opt/tracksys/infra/scripts/deploy.sh`, validado com `visudo -cf`; instala os timers da seção 4 e 5 na primária.

### (3) Compose e imagem de migração

- `infra/docker-compose.yml`: `api` e `worker` sem `profiles`, `image: tracksys-app:${TRACKSYS_VERSION}`, `build: { context: .., dockerfile: infra/app/Dockerfile, target: app }` (imagem única da T-004; `worker` com `command` do processo worker). `migrate` (perfil `ops`): `image: tracksys-migrate:${TRACKSYS_VERSION}`, `target: migrate`, `environment: DATABASE_URL: ${MIGRATE_DATABASE_URL}`. Limites e healthchecks da T-003 inalterados.
- `infra/app/Dockerfile`, alvo `migrate`: `node:24-bookworm-slim` com o binário `dbmate` do pacote npm (arquitetura do build), `packages/db/migrations/` e `check-catalog.js` (esbuild de `packages/db/scripts/check-catalog.ts`, com `catalog-allowlist.json` ao lado). `migrate-entrypoint.sh up` → `dbmate --migrations-dir /app/migrations --no-dump-schema --wait up`; `check` → `node /app/check-catalog.js`; outro argumento → `exit 64`. Usuário `node`.

### (4) Backup, restore e efeitos externos

| Peça | Regra |
|---|---|
| `backup/base-backup.sh` (timer 06:00 UTC) | `dc exec -T -u postgres db wal-g backup-push /var/lib/postgresql/data`; sucesso → `tracksys_backup_last_success_timestamp_seconds` e `tracksys_backup_base_size_bytes` em `/var/lib/tracksys/metrics/backup.prom` (`lib/metrics.sh`: escreve em `.tmp` e `mv`, atômico); falha → `exit 1` (o alerta AL-04 cobre) |
| `backup/retain.sh` (07:00 UTC) | Lê `wal-g backup-list --json --detail`; domingo (UTC): `wal-g backup-mark <base do dia>`; bases permanentes com mais de 28 dias: `wal-g backup-mark -i <base>`; depois `wal-g delete retain FULL 7 --confirm` [VALIDAR flags na versão fixada] |
| `backup/copy-r2.sh` (de hora em hora, :15) | `rclone copy` (nunca `sync`) do bucket Oracle para `r2:$R2_BUCKET` com remotos definidos só por variáveis `RCLONE_CONFIG_OCI_*` e `RCLONE_CONFIG_R2_*`; sucesso → `tracksys_backup_copy_last_success_timestamp_seconds` |
| `backup/restore.sh --target-time <RFC 3339> \| --target-name <nome>` | Restore real do [Anexo C R8](../docs/anexos/C-operacional.md) passo 3 em host novo: volume `db-data` vazio, `wal-g backup-fetch … LATEST`, `recovery.signal`, `recovery_target_*`, `recovery_target_action = 'promote'`; recusa rodar se `db-data` não estiver vazio |
| `backup/restore-drill.sh` (manual no F0) | Ensaio de [13 §8](../docs/spec/13-infra-e-operacao.md) itens 1–7, com o projeto `tracksys-drill` desta tabela |
| `infra/docker-compose.drill.yml` | Projeto `tracksys-drill`. Redes: `drill-internal` (`internal: true`, `172.31.0.0/24`) e `drill-egress` (bridge). `db`: imagem `tracksys-db:17`, nas 2 redes (só ele alcança o object storage), volume próprio `drill-db-data`, `mem_limit: 1536m`, `command` com `-c archive_mode=off -c shared_buffers=256MB -c hba_file=/etc/postgresql/pg_hba.conf` montando `infra/db/pg_hba.drill.conf`. `worker`: `tracksys-app:${TRACKSYS_VERSION}`, só `drill-internal`, `mem_limit: 512m`, `env_file: /run/tracksys/drill.env`. `sink`: mesma imagem, `node /drill/drill-sink.mjs`, só `drill-internal`. `migrate`: `tracksys-migrate`, perfil `ops`. Nenhuma porta publicada |
| `pg_hba.drill.conf` | `local all postgres peer` · `local all all scram-sha-256` · `host tracksys tracksys_app,tracksys_ingest,tracksys_owner 172.31.0.0/24 scram-sha-256` · `host all all 0.0.0.0/0 reject` |
| `drill-sink.mjs` | `node:http` na 8080; conta toda requisição exceto `GET /__count` (que devolve `{"requests":N}`); nunca loga corpo nem cabeçalho |

`restore-drill.sh`, em ordem: (1) `START` = agora, `T` = `START − 10 min`; (2) contagens da produção como `postgres` pelo socket em `BEGIN READ ONLY`: `count(*)` de `app.position` por `received_at` e de `app.audit_log` por `at` em `[T − 24 h, T − 5 min)`; (3) `wal-g backup-fetch` no volume vazio e `recovery_target_time = T`; (4) espera `pg_isready` e `pg_is_in_recovery() = false` (máx. 2 h) → `READY`; (5) no restaurado: `max(received_at)` de `app.ingest_inbox` → perda = `max(0, T − max)`; mesmas contagens; `dc run --rm migrate check`; (6) gera `/run/tracksys/drill.env` a partir do `prod.env` com `DATABASE_URL_*` para `db` do projeto, `EXTERNAL_EFFECTS=off`, `COMMAND_DISPATCH_ENABLED=false`, `EMNIFY_SMS_ENABLED=false`, `FCM_API_BASE=http://sink:8080`, `TRACCAR_API_URL=http://sink:8080`, `SENTRY_DSN=` (vazio); sobe `sink` e `worker` por 10 min; lê `/__count`; (7) derruba o projeto com `down -v` e grava `/var/lib/tracksys/restore/AAAA-MM-DD.md` e `tracksys_restore_drill_last_success_timestamp_seconds` (só se `result: ok`). O fundador copia o relatório para `docs/runbooks/restore/` no repositório.

Relatório (front matter lido pela T-015, chaves exatas): `drill: restore`, `date`, `host`, `base`, `targetTime`, `startedAt`, `readyAt`, `durationSeconds` (`READY − START`), `lossSeconds`, `countsMatch` (boolean), `catalogOk`, `externalCalls` (do `sink`), `result` (`ok` se `durationSeconds ≤ 7200`, `lossSeconds ≤ 300`, `countsMatch`, `catalogOk` e `externalCalls = 0`; senão `falhou`); corpo com a tabela de contagens produção × restaurado. Sem IMEI, coordenada, e-mail ou segredo.

**`EXTERNAL_EFFECTS` no worker:** variável obrigatória (`on` \| `off`, Zod; ausente ou outro valor → `exit 78` citando o nome). `off`: o adaptador FCM vira `NullPushSender` (nenhuma requisição; entrega gravada como `suppressed` com `error = 'external_effects_off'`) e o cliente Traccar vira `NullTraccarClient` (saúde `unknown`, qualquer outra chamada lança `EXTERNAL_EFFECTS_DISABLED`); cada supressão loga `msg=external_effect_suppressed adapter=<fcm|traccar>` em `warn` e incrementa `external_effects_suppressed_total{adapter}`; o boot loga `msg=external_effects_off`. Adaptadores futuros (emnify, Asaas, e-mail) seguem a mesma regra. `.env.example` e `prod.env.example` = `on`.

### (5) Observabilidade, alertas e sondas

- **Alloy** (`infra/alloy/config.alloy`, systemd na primária, `EnvironmentFile=/run/tracksys/prod.env`): `prometheus.exporter.unix` com textfile em `/var/lib/tracksys/metrics`; `prometheus.exporter.cadvisor`; `prometheus.exporter.postgres` como `tracksys_ops_ro` em `172.30.0.5`; scrape de `172.30.0.10:3001/metrics` (`job="api"`), `172.30.0.11:3002/metrics` (`job="worker"`), Caddy `:2019/metrics`; `prometheus.remote_write` e `loki.write` para o Grafana Cloud (`GRAFANA_PROM_URL`, `GRAFANA_PROM_USER`, `GRAFANA_LOKI_URL`, `GRAFANA_LOKI_USER`, `GRAFANA_PUSH_TOKEN`); `loki.source.docker` → `redaction.pii` → `loki.write`; `relabel` que descarta rótulos `vehicle_id`, `device_id`, `user_id`, `imei`, `ip`.
- `infra/alloy/redaction.alloy`: `declare "pii"` com `loki.process` e 3 `stage.replace`: `\b(\d{11})\d{4}\b` (grupo 1 → `***`, sobra `***` + 4 últimos); `(-?\d{1,3}\.\d{4,})` → `[coord]`; `(Bearer\s+[A-Za-z0-9._~+/=-]+)` → `Bearer [redigido]` [VALIDAR sintaxe na versão fixada do Alloy].
- `metrics-textfile.sh` (timer 15 s): `tracksys_tcp_established{port="5023"}` pelo `ss` no namespace do contêiner `traccar` (`nsenter`).
- `disk-cleanup.sh` (timer 05:00 UTC e chamado pela regra L1 a 85%): `journalctl --vacuum-size=300M`, logs rotacionados, imagens `tracksys-*` além das 3 últimas tags; nunca toca em volumes.
- **Sentry** (`@sentry/node`, major estável atual, só em `api` e `worker`; dependência nova justificada no PR — a T-004 adiou o SDK para esta tarefa): inicializa só com `SENTRY_DSN` não vazio; `sendDefaultPii: false`, `release: TRACKSYS_VERSION`, `tracesSampleRate: 0.05`, `beforeSend: scrubSentryEvent`. `scrubSentryEvent` (puro, em `packages/domain`): remove `request.data`, `request.query_string`, `request.cookies` e os headers `authorization`, `cookie`, `x-ingest-token`, `asaas-access-token` (sem diferenciar maiúsculas); troca sequências de 15 dígitos por `***` + 4 últimos em `message` e `exception.values[].value`.
- **Regras do F0** (`infra/grafana/rules/f0.rules.yaml`, formato Prometheus, carregadas no Grafana Cloud por `grafana-sync.sh` com `mimirtool rules load`; rótulos `severity` e `runbook`, `emergency="true"` onde indicado):

| Alerta | Expressão | `for` | Rótulos |
|---|---|---|---|
| `AL-03` | `1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} > 0.80` | 5m | `SEV2`, R2 |
| `AL-03-SEV1` | mesma expressão `> 0.90` | 5m | `SEV1`, R2 |
| `AL-04` | `time() - tracksys_backup_last_success_timestamp_seconds > 93600` | 0m | `SEV2`, `emergency="true"`, R8 |
| `AL-05` | `(pg_stat_archiver_last_archive_age > 300 and on() sum(rate(pg_stat_database_xact_commit{datname="tracksys"}[5m])) > 0) or increase(pg_stat_archiver_failed_count[5m]) > 0` [VALIDAR nomes do exporter] | 0m | `SEV2`, R2 |
| `AL-07` | `ingest_pending_count > 500` (for 2m) **ou** `ingest_pending_oldest_age_seconds > 300` (for 0m) — 2 regras | — | `SEV2`, R4 |
| `AL-08` / `AL-08-SEV1` | `histogram_quantile(0.95, sum by (le) (rate(alert_latency_seconds_bucket[5m]))) > 60` / `> 120` | 5m | `SEV2` / `SEV1`, R4 |
| `AL-11` | `sum(rate(http_requests_total{job="api",status=~"5.."}[5m])) / sum(rate(http_requests_total{job="api"}[5m])) > 0.02 and sum(increase(http_requests_total{job="api"}[5m])) >= 100` | 0m | `SEV2` |
| `AL-12` | `increase(container_oom_events_total[15m]) > 0` (o laço de reinício já pagina pelo autoheal da T-003) | 0m | `SEV2` |

- `alertmanager.yaml.tpl` (renderizado com `envsubst` por `grafana-sync.sh`; `mimirtool alertmanager load`) [VALIDAR — Alertmanager gerenciado do Grafana Cloud free com `pushover_configs`; senão contact point Pushover do Grafana com o mesmo mapeamento]: rota por rótulos → `emergency="true"` → Pushover prioridade 2 (`retry: 60s`, `expire: 3h`); `SEV1` → prioridade 1; `SEV2` → prioridade 0; `SEV3` → e-mail (`group_interval: 24h`). Título `"<alertname> <severity>"`; corpo com o runbook; nunca IMEI ou coordenada.
- **UptimeRobot** (free, 5 min; cadastrado pelo fundador): `slo-gps-tcp` (porta, `gps.<domínio>:5023`) e `slo-api-https` (palavra-chave `"status":"ok"` em `https://api.<domínio>/health/ready`), alerta Pushover prioridade 2 no F0 (única sonda externa = AL-01/AL-02) [VALIDAR integração Pushover no plano free; senão e-mail + app UptimeRobot]. `probes/uptimerobot-check.sh` (`UPTIMEROBOT_READ_API_KEY`, `POST https://api.uptimerobot.com/v2/getMonitors` [VALIDAR API]) sai 0 só se os 2 monitores existem, `interval = 300` e estão `up`.

Variáveis novas (`prod.env.example`, vazias; `ci.env`, fictícias): `SENTRY_DSN`, `EXTERNAL_EFFECTS`, `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `GRAFANA_PROM_URL`, `GRAFANA_PROM_USER`, `GRAFANA_LOKI_URL`, `GRAFANA_LOKI_USER`, `GRAFANA_PUSH_TOKEN`, `UPTIMEROBOT_READ_API_KEY`, `ALERT_EMAIL_TO`.

## Testes de aceite (congelados)

Locais (`tests/acceptance/T-013/`, rodam no CI sem nuvem; scripts com `TRACKSYS_ROOT/ETC/RUN` em diretório temporário e `PATH` com os fakes de `fixtures/bin/` que gravam cada chamada):

- `ops-schema.test.ts` — Dado o schema migrado, Então `ops.audit_log` existe e `pnpm db:check` sai 0. Dado `tracksys_ops_audit`, Quando insere 2 vezes o mesmo `id` `0e7c9a7e-5b1a-4c55-9d1e-3f2a6b1c0d01` com `ON CONFLICT (id) DO NOTHING`, Então há 1 linha; Quando `UPDATE ops.audit_log SET result = 'success'`, Então SQLSTATE 42501; `tracksys_app` em `SELECT 1 FROM ops.audit_log` → 42501. Dado, numa transação desfeita, `GRANT UPDATE ON ops.audit_log TO tracksys_ops_audit`, Então `runCatalogChecks` contém `CAT-06 ops.audit_log`. Inserção com `action = 'deploy'` → 23514.
- `deploy-script.test.ts` (CT-OPS-006, CT-OPS-007 na parte local) — Dado `current-version = v0.3.0` e `SSH_ORIGINAL_COMMAND='bash'`, Então `exit 2`, stderr "comando recusado" e 0 chamadas a `docker`. Dado `v0.3.1` com o fake de `docker compose up --wait` saindo 1, Então há um 2º `up` com `TRACKSYS_VERSION=v0.3.0`, `current-version = v0.3.0`, o fake de `curl` registra 1 POST ao Pushover com `priority=1` e `exit 1`. Dado `v0.4.0` com o fake de `migrate check` saindo 1, Então nenhum `up` é chamado, `current-version = v0.3.0`, 1 page e `exit 3`. Dado `v0.3.2` saudável, Então `current-version = v0.3.2`, `previous-version = v0.3.0` e o fake de `psql` recebe 1 `INSERT INTO ops.audit_log` com `ops.deploy` e `success`. Dado tag fora de `origin/main`, Então `exit 3` sem build. Dado árvore suja, Então `exit 3`. Dado `DEPLOY_FAULT=smoke` com `SUDO_USER=deploy`, Então a variável é ignorada.
- `migration-safety.test.ts` (CT-OPS-007) — Dado `20261101000000_remove_nickname.sql` com `ALTER TABLE app.vehicle DROP COLUMN nickname` no `up`, Então `exit 1` citando `DROP COLUMN`; renomeado para `20261101000000_remove_nickname_contract.sql` e sem `apps/**` na lista, Então `exit 0`; com `apps/api/src/main.ts` na lista, Então `exit 1`. Dado `DROP TABLE app.x` só depois de `-- migrate:down`, Então `exit 0`. Dado `20261007120000_fundacao_isolamento.sql` modificado, Então `exit 1`.
- `backup-scripts.test.ts` (CT-OPS-008 na parte local) — Dado `fixtures/backup-list.json` com 15 bases diárias de 07/10/2026 (quarta) a 21/10/2026 e as de 11/10 e 18/10 permanentes, Quando `retain.sh` roda com `date` fixado em 25/10/2026 07:00Z (domingo), Então o fake de `wal-g` recebe `backup-mark` da base de 25/10, nenhum `backup-mark -i` (nenhuma permanente com mais de 28 dias) e `delete retain FULL 7 --confirm`; com `date` em 16/11/2026 (segunda), Então `backup-mark -i` da base de 11/10. `copy-r2.sh` contém `rclone copy` e não contém `rclone sync`. `base-backup.sh` com sucesso grava `backup.prom` com `tracksys_backup_last_success_timestamp_seconds` inteiro e sem arquivo `.tmp` restante.
- `drill-compose.test.ts` (CT-OPS-009 na parte estática) — Dado `docker compose -f infra/docker-compose.drill.yml --env-file infra/env/ci.env config --format json`, Então `drill-internal` tem `internal: true`; `worker` e `sink` estão só nela; `db` está nas 2 redes e seu `command` contém `archive_mode=off`; nenhum serviço publica porta. Dado o `drill.env` gerado por `restore-drill.sh --render-env-only` a partir de `infra/env/ci.env`, Então contém `EXTERNAL_EFFECTS=off`, `COMMAND_DISPATCH_ENABLED=false`, `EMNIFY_SMS_ENABLED=false`, `FCM_API_BASE=http://sink:8080`, `TRACCAR_API_URL=http://sink:8080` e `SENTRY_DSN=` vazio.
- `external-effects.test.ts` (INV-05) — Dado o worker com `EXTERNAL_EFFECTS=off`, `FCM_API_BASE` apontando para o fake de FCM da T-012 e 1 entrega `pending` de `ignition_on`, Quando o job de entrega roda, Então o fake recebe 0 requisições, a entrega fica `suppressed` com `error = 'external_effects_off'`, o log tem `external_effect_suppressed` e `external_effects_suppressed_total{adapter="fcm"} = 1`. Dado `EXTERNAL_EFFECTS=talvez`, Então o worker sai com 78 citando `EXTERNAL_EFFECTS`.
- `observability.test.ts` (CT-OPS-016) — Dado o contêiner `grafana/alloy` fixado com `fixtures/alloy-redaction.alloy` (importa `infra/alloy/redaction.alloy`, lê um arquivo e envia a `loki.echo`) e a linha `imei=359339000000001 lat=-5.0891021 lon=-42.8018503 auth=Bearer abc.def`, Então a saída contém `***0001` e não contém `359339000000001`, `-5.0891021`, `-42.8018503` nem `abc.def`. Dado um evento com header `Authorization: Bearer abc`, `request.data = {"senha":"x"}` e `query_string = "token=y"`, Quando `scrubSentryEvent`, Então não restam `authorization`, `data` nem `query_string`. Dado `api` e `worker` no harness da T-005, Quando `/metrics` (3001 e 3002) é lido, Então nenhum rótulo se chama `vehicle_id`, `device_id`, `user_id`, `imei` ou `ip`.
- `alert-rules.test.ts` (CT-OPS-017) — `promtool test rules f0.rules.test.yaml` (imagem `prom/prometheus` fixada) sai 0, e o arquivo de teste contém: disco em 81% por 6 min → `AL-03` com `severity=SEV2`; 79% → nenhum alerta; 4% de 5xx com 300 requisições em 5 min → `AL-11`; 4% com 60 requisições → nenhum; backup há 27 h → `AL-04` com `emergency="true"`; p95 de 130 s por 6 min → `AL-08-SEV1`. `amtool config routes test` sobre o template renderizado com `ci.env`: `severity=SEV2` → `pushover-p0`; `severity=SEV1` → `pushover-p1`; `emergency=true,severity=SEV2` → `pushover-p2`; `severity=SEV3` → `email`.

Na VM (fundador; saídas anexadas ao PR):
- CT-OPS-006: `v0.x.0` publicado e saudável (`current-version` igual); `ssh deploy@tracksys-p bash` → "comando recusado"; como root `DEPLOY_FAULT=smoke deploy.sh v0.x.1` → `api` e `worker` voltam a `v0.x.0` em ≤ 5 min, 1 page; `deploy.sh v0.x.1` sem falha → `current-version = v0.x.1`.
- CT-OPS-007: como root `DEPLOY_FAULT=catalog deploy.sh v0.x.2` → `exit 3`, versão anterior servindo, 1 page.
- CT-OPS-008: `pg_stat_archiver` a cada minuto por 10 min com `now() − last_archived_time` ≤ 120 s; 2 bases noturnas seguidas em `wal-g backup-list`; o mesmo objeto de WAL na R2 em ≤ 2 h; `rclone cat` de um objeto não começa com o cabeçalho de WAL legível.
- CT-OPS-009 / G0-7: `restore-drill.sh` às 13:00 UTC até 27/10/2026 → relatório com `result: ok`, `durationSeconds ≤ 7200`, `lossSeconds ≤ 300`, `externalCalls: 0`; copiado para `docs/runbooks/restore/`.
- CT-OPS-017 / sondas: `uptimerobot-check.sh` sai 0; Pushover de emergência às 03:00 BRT reconhecido; `AL-03` provocado com `fallocate` até 81% por 5 min → 1 page prioridade 0 "AL-03 SEV2"; Sentry recebe erro de teste sem `authorization`.

## Comandos de verificação

```bash
pnpm install
pnpm db:reset && pnpm db:migrate && pnpm db:check   # Catálogo OK: nenhuma violação de CAT-01..CAT-07.
pnpm test:acceptance -- tests/acceptance/T-013
docker compose -f infra/docker-compose.yml --env-file infra/env/ci.env config --quiet
docker compose -f infra/docker-compose.drill.yml --env-file infra/env/ci.env config --quiet
docker run --rm -v "$PWD/infra":/infra koalaman/shellcheck:v0.10.0 $(cd infra && git ls-files '*.sh' | sed 's|^|/infra/|')
docker run --rm -v "$PWD/infra/grafana":/g --entrypoint promtool prom/prometheus:v3.<x>@sha256:<digest> test rules /g/rules/f0.rules.test.yaml
infra/scripts/check-migration-safety.sh --base origin/main
docker buildx build --platform linux/amd64,linux/arm64 --target migrate -f infra/app/Dockerfile .
pnpm verify
```

## Definição de pronto

- [ ] Testes locais da T-013 verdes; `migration-safety`, `secrets` e `infra-lint` verdes no PR.
- [ ] 1º deploy por tag pela Action concluído; rollback e abort provados na VM (CT-OPS-006/007).
- [ ] WAL arquivando sem falha há ≥ 48 h; 2 bases noturnas; cópia R2 < 26 h.
- [ ] `docs/runbooks/restore/2026-10-2X.md` com `result: ok` no repositório até 27/10/2026 (G0-7).
- [ ] UptimeRobot e Pushover testados; regras do F0 carregadas no Grafana Cloud.
- [ ] PR `feat(infra): deploy, backup WAL-G, restore e sondas (T-013)` com REQ/INV/risco e revisão cruzada (N0 nos trechos indicados).

## Decisões já tomadas (não pergunte, siga)

| Dúvida provável | Resposta |
|---|---|
| A T-003 usa `apps/api/Dockerfile` e a T-004 entregou `infra/app/Dockerfile` (imagem única). Qual vale? | A da T-004, já em `main`. Esta tarefa alinha o Compose de produção (`tracksys-app`) e tira o perfil `app`, como a T-003 previu. |
| `/health/ready` público ou só na 3001? | O smoke e as sondas usam `https://api.<domínio>/health/ready` ([13 §7, §10](../docs/spec/13-infra-e-operacao.md)). Se a T-004 só expõe na 3001, acrescente a rota na 3000 com `{"status":"ok"}` sem detalhes e registre no PR. |
| Onde roda o restore de ensaio no F0? | Na primária, em projeto isolado: a standby não roda contêiner no F0 (T-003). Limites somados do ensaio: ~2 GB. No F1 o ensaio mensal vai para a standby. |
| O banco restaurado pode arquivar WAL? | Não. `archive_mode=off` no ensaio; senão ele empurraria uma nova timeline para o bucket de produção. |
| Por que contagens da produção como `postgres`? | `tracksys_ops_ro` não tem USAGE em `app` e as funções `ops.*` são do F1. O acesso é pelo socket, em `READ ONLY`, só `count`/`max` — o mesmo caminho do `pg_create_restore_point` do deploy. |
| Como provar rollback na VM sem release quebrada em `main`? | `DEPLOY_FAULT`, aceito só para root direto (o `sudo` do `deploy` limpa o ambiente) e auditado. Nunca crie migration de teste em `main`. |
| `EXTERNAL_EFFECTS` tem padrão? | Não: obrigatória. Ausente derruba o boot (78). Desligar efeito por omissão esconderia push perdido; ligar por omissão quebraria o INV-05 no ensaio. |
| Auditoria se o banco estiver fora? | No F0 só aviso no stderr e no log do Action. Spool idempotente é REQ-OPS-021 (F1). |
| Escalonamento de SEV1 após 10 min sem recuperação? | F1 (gateway). No F0, AL-02 (UptimeRobot) e AL-04 já saem em prioridade 2. |
| A T-008 registrou host extra na CSP do console? | Ajuste `infra/caddy/sites/primary.caddy` nesta tarefa e cite o PR da T-008. |
| Agente pode cadastrar segredos ou rodar `deploy.sh` na VM? | Não (REQ-QLD-016). Escreve, testa com fakes, `shellcheck` e `--render-env-only`; o fundador executa. |
