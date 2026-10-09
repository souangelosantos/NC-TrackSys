# T-003 — VM primária, Docker Compose, firewall e DNS

| Campo | Valor |
|---|---|
| Fase | F0 (semana S1: 07–13/10/2026) |
| Requisitos | REQ-OPS-001, REQ-OPS-002, REQ-OPS-003, REQ-OPS-004, REQ-OPS-005, REQ-OPS-023, REQ-ARQ-003, REQ-ARQ-004, REQ-ING-001, REQ-DAD-017, REQ-SEG-019, REQ-SEG-024 |
| Invariantes | INV-07 (banco sem porta pública, papéis sem posse), INV-12 (UTC no host e no banco) |
| Risco de revisão | N1 — os arquivos em caminhos N0 de [14 §6](../docs/spec/14-qualidade-e-processo-ia.md#6-níveis-de-risco) (`.github/**`, `.sops.yaml`, `infra/secrets/**`) seguem o rito N0: revisor de outro fornecedor e leitura linha a linha desses arquivos |
| Depende de | DEC-12 |
| Estimativa | 3 sessões de agente (3a banco, Compose, Caddy e Traccar; 3b provisionamento e firewall; 3c segredos, CI e runbook) + ~5 h do fundador na conta Oracle |
| Bloqueado por decisão | DEC-12 (padrão: região brasileira com capacidade A1 no dia; conta Pay As You Go quando possível; F0 sem standby, RTO ≤ 2 h). DEC-04 (padrão: `TRACKSYS_DOMAIN` provisório só para a bancada; o `gps.` definitivo existe antes do 1º SMS a veículo real) |
| Tipo | **Mista:** o agente escreve scripts e configuração e prova o que dá para provar fora da nuvem; o fundador executa na conta Oracle, na Cloudflare e na Tailscale (agente não tem credencial de produção, REQ-QLD-016) |

## Objetivo

Deixar a VM primária da Oracle reproduzível por script e no ar com `db` (arquivando WAL), `traccar` e `caddy`, firewall em duas camadas, SSH só pela Tailscale, segredos cifrados com SOPS + age e os subdomínios `gps.`, `api.` e `app.` resolvendo para ela. Ao final, o J16 de bancada consegue transmitir para a porta 5023 (marco de 13/10/2026) e os serviços `api`, `worker` e `migrate` já estão declarados no Compose com os limites de [03 §11](../docs/spec/03-arquitetura.md#11-orçamento-de-recursos-vm-de-12-gb-2-ocpu-ampere), prontos para receber a imagem única `tracksys-app` da T-004 (`infra/app/Dockerfile`) e o alvo `migrate` da T-013.

## Contexto obrigatório

- [13 §1 a §6](../docs/spec/13-infra-e-operacao.md#1-topologia): topologia, provisionamento, firewall, Compose, banco, Traccar, segredos.
- [03 §10, §11, §13](../docs/spec/03-arquitetura.md#10-fronteiras-de-confiança-e-portas): portas, orçamento de memória, variáveis.
- [05 §2](../docs/spec/05-ingestao-e-telemetria.md#2-contrato-com-o-traccar): chaves do forward do Traccar.
- [08 §8, §9](../docs/spec/08-identidade-e-seguranca.md#8-segredos): SOPS, limites da 5023, headers do `app.`.
- [ADR-005](../docs/adr/ADR-005-infra-oracle-always-free.md), [ADR-003](../docs/adr/ADR-003-traccar-borda-de-protocolos.md).

## Escopo — fazer

**Agente:**
1. Imagem do banco multi-arquitetura com WAL-G, `postgresql.conf`, modelo de `pg_hba.conf` e papéis operacionais (seção 1).
2. `infra/docker-compose.yml` de produção com os 6 serviços, rede fixa, limites, healthchecks e perfis (seção 2).
3. Caddy com `api.` e `app.` (placeholder do console) e Traccar com configuração renderizada no start (seções 3 e 4).
4. Scripts de provisionamento, firewall, guarda de papel, autoheal e subida inicial, mais as units systemd (seção 5).
5. SOPS + age, verificação de segredos no CI e lista de variáveis de produção (seção 6).
6. Runbook do fundador `docs/runbooks/infra/provisionar-vm.md` (seção 7) e testes de aceite locais.

**Fundador (com o runbook):**
7. Resolver DEC-12; criar a conta/compartimento e rodar `oci-bootstrap.sh`; gerar o user-data e criar as 2 VMs (a standby só com Tailscale no F0).
8. Registrar o domínio provisório e os registros A na Cloudflare (TTL 60 s, sem proxy); criar a chave age e o `prod.env.sops`; rodar `provision.sh --role primary`; subir `db traccar caddy` com `bootstrap-stack.sh`.
9. Executar a verificação na VM (seção "Testes de aceite", bloco VM) e anexar as saídas ao PR.

## Fora do escopo

- Imagens e código de `api`, `worker` e `console`: T-004, T-005, T-007. Aqui só a declaração dos serviços.
- `deploy.sh`, workflow de deploy, backup base diário, retenção, cópia R2, restore e sondas: T-013. Aqui o WAL já arquiva (RPO), sem base diária.
- VM standby ativa, réplica, Uptime Kuma, status page: F1.
- Escrever no banco `traccar` por SQL (proibido, ADR-003).

## Arquivos a criar/alterar

```
infra/db/Dockerfile                         (alterar: digest no FROM, ca-certificates curl, WAL-G)
infra/db/postgresql.conf
infra/db/pg_hba.conf.tpl
infra/db/initdb/10-ops-roles.sh             (executável)
infra/db/roles.sql
infra/docker-compose.yml
infra/env/ci.env                            (valores fictícios para validar o Compose no CI)
infra/env/prod.env.example                  (lista de variáveis, todas vazias)
infra/caddy/Dockerfile
infra/caddy/Caddyfile
infra/caddy/sites/primary.caddy
infra/caddy/sites/standby.caddy
infra/caddy/placeholder/index.html
infra/caddy/placeholder/version.json
infra/traccar/traccar.xml.tpl
infra/traccar/render-config.sh              (executável)
infra/scripts/oci-bootstrap.sh              (executável)
infra/scripts/cloud-init.yaml
infra/scripts/render-cloud-init.sh          (executável)
infra/scripts/provision.sh                  (executável)
infra/scripts/firewall.sh                   (executável)
infra/scripts/role-guard.sh                 (executável)
infra/scripts/autoheal.sh                   (executável)
infra/scripts/bootstrap-stack.sh            (executável)
infra/scripts/check-secret-files.sh         (executável)
infra/systemd/tracksys-secrets.service
infra/systemd/tracksys-firewall.service
infra/systemd/tracksys-autoheal.service
infra/systemd/tracksys-autoheal.timer
infra/systemd/docker.service.d/10-tracksys.conf
.sops.yaml
infra/secrets/prod.env.sops                 (criado e cifrado pelo fundador; o agente só cria .sops.yaml)
.github/workflows/ci.yml                    (alterar: jobs secrets e infra-lint)
docs/runbooks/infra/provisionar-vm.md
tests/acceptance/T-003/compose.test.ts
tests/acceptance/T-003/firewall.test.ts
tests/acceptance/T-003/traccar-config.test.ts
tests/acceptance/T-003/postgres-config.test.ts
tests/acceptance/T-003/caddy.test.ts
tests/acceptance/T-003/secrets.test.ts
```

## Especificação detalhada

### (1) Banco

`infra/db/Dockerfile` (substitui o da T-001 mantendo PostGIS e o `initdb/`):

```dockerfile
FROM postgres:17-bookworm@sha256:<digest do índice multi-arquitetura, fixado no PR>
ARG TARGETARCH
ARG WALG_VERSION=v3.0.<x>
ARG WALG_SHA256_AMD64=<sha256 do artefato amd64>
ARG WALG_SHA256_ARM64=<sha256 do artefato aarch64>
RUN apt-get update \
  && apt-get install -y --no-install-recommends postgresql-17-postgis-3 postgresql-17-postgis-3-scripts ca-certificates curl \
  && rm -rf /var/lib/apt/lists/*
RUN set -eu; \
  case "$TARGETARCH" in amd64) A=amd64; S="$WALG_SHA256_AMD64";; arm64) A=aarch64; S="$WALG_SHA256_ARM64";; *) exit 1;; esac; \
  F="wal-g-pg-ubuntu-22.04-$A.tar.gz"; \
  curl -fsSL -o "/tmp/$F" "https://github.com/wal-g/wal-g/releases/download/$WALG_VERSION/$F"; \
  echo "$S  /tmp/$F" | sha256sum -c -; \
  tar -xzf "/tmp/$F" -C /tmp; install -m 0755 "/tmp/wal-g-pg-ubuntu-22.04-$A" /usr/local/bin/wal-g; rm -f /tmp/wal-g*
COPY initdb/ /docker-entrypoint-initdb.d/
```

`WALG_VERSION` = release estável mais recente da série v3 com ≥ 14 dias na data do PR; nome do artefato [VALIDAR na versão fixada]: se mudar, ajuste `F` e registre no PR. Hash errado falha o build (CT-OPS-005).

`infra/db/postgresql.conf`: um parâmetro por linha, exatamente os valores da tabela de [13 §4.2](../docs/spec/13-infra-e-operacao.md#42-infradbpostgresqlconf-primária-e-réplica) (inclusive `archive_command = 'wal-g wal-push %p'`, `archive_timeout = 60`, `log_parameter_max_length = 0`, `log_parameter_max_length_on_error = 0`, `timezone = 'UTC'`, `shared_preload_libraries = 'pg_stat_statements'`).

`infra/db/pg_hba.conf.tpl`: o texto de [13 §4.3](../docs/spec/13-infra-e-operacao.md#43-pg_hbaconf-renderizado-pelo-deploy-com-envsubst) literal, com `${PEER_TAILSCALE_IP}`; renderizado por `envsubst '${PEER_TAILSCALE_IP}'` para `/run/tracksys/pg_hba.conf` (no F0, `PEER_TAILSCALE_IP` = IP Tailscale da standby já criada).

`infra/db/initdb/10-ops-roles.sh` (volume novo) e `infra/db/roles.sql` (idempotente, padrão `SELECT format(...) WHERE NOT EXISTS (...) \gexec`, executado como `postgres` pelo socket): criam `traccar` (LOGIN, dono do banco `traccar`, sem CONNECT em `tracksys`), `tracksys_replica` (LOGIN REPLICATION), `tracksys_ops_ro` (LOGIN, membro de `pg_monitor`, `ALTER ROLE … SET default_transaction_read_only = on`, `SET statement_timeout = '5s'`, sem USAGE em `app`) e `tracksys_ops_audit` (LOGIN, sem privilégio por enquanto; o schema `ops` vem na T-013). Senhas: `TRACCAR_DB_PASSWORD`, `REPLICA_PASSWORD`, `OPS_RO_PASSWORD`, `OPS_AUDIT_PASSWORD` (≥ 32 caracteres). `roles.sql` também reaplica `REVOKE CONNECT ON DATABASE tracksys FROM traccar`.

### (2) `infra/docker-compose.yml`

Projeto `tracksys`; rede `tracksys` bridge `172.30.0.0/24`; `restart: unless-stopped` em todos; `env_file: /run/tracksys/prod.env` em todos; imagens externas por digest. Healthcheck de todos: `interval: 10s`, `timeout: 3s`, `retries: 3`.

| Serviço | IP | Imagem / build | `mem_limit` / `cpus` | Portas no host | Healthcheck | Perfil |
|---|---|---|---|---|---|---|
| `db` | `.5` | build `./db`, `image: tracksys-db:17` | `5g` / — ; `shm_size: 1g`; `oom_score_adj: -500`; `stop_grace_period: 120s` | `${TAILSCALE_IPV4}:5432:5432` | `pg_isready -U postgres -d tracksys` | — |
| `traccar` | `.6` | `traccar/traccar:<tag>@sha256:<digest>` | `1536m` / — | `5023:5023` | `wget -qO- http://127.0.0.1:8082/api/server` [VALIDAR — T-002 ferramenta disponível na imagem; senão `curl -fs`] | — |
| `caddy` | `.2` | build `./caddy`, `image: tracksys-caddy:${TRACKSYS_VERSION}` | `128m` / `0.5` | `80:80`, `443:443` | `wget -qO- http://127.0.0.1:2019/config/` | — |
| `api` | `.10` | build `context: ..`, `dockerfile: infra/app/Dockerfile`, `target: app`; `image: tracksys-app:${TRACKSYS_VERSION}` | `1g` / `1.5`; `NODE_OPTIONS=--max-old-space-size=768` | nenhuma | `node -e "fetch('http://127.0.0.1:3001/health/ready').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"` (porta interna, com `checks`; a 3000 pública responde só `{"status"}`) | `app` |
| `worker` | `.11` | `image: tracksys-app:${TRACKSYS_VERSION}` (mesma imagem do `api`, sem `build` próprio), `command` do processo worker | `1g` / `1.0`; `--max-old-space-size=512` | nenhuma | idem na porta 3002 | `app` |
| `migrate` | — | build `context: ..`, `dockerfile: infra/app/Dockerfile`, `target: migrate` (alvo criado pela T-013); `image: tracksys-migrate:${TRACKSYS_VERSION}`; `environment: DATABASE_URL: ${MIGRATE_DATABASE_URL}`; argumento `up` ou `check` no `docker compose run` | `512m` | nenhuma | — | `ops` |

Detalhes:
- `db`: `command: ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf", "-c", "hba_file=/etc/postgresql/pg_hba.conf"]`; volumes `db-data:/var/lib/postgresql/data`, `./db/postgresql.conf:/etc/postgresql/postgresql.conf:ro`, `/run/tracksys/pg_hba.conf:/etc/postgresql/pg_hba.conf:ro`.
- `traccar`: `entrypoint: ["/bin/sh", "/opt/tracksys/render-config.sh"]`; volumes `./traccar/traccar.xml.tpl:/opt/tracksys/traccar.xml.tpl:ro`, `./traccar/render-config.sh:/opt/tracksys/render-config.sh:ro`, `traccar-logs:/opt/traccar/logs`; `JAVA_OPTS=-Xms256m -Xmx1g`.
- `caddy`: volumes `caddy-data:/data`, `caddy-config:/config`; `environment: CADDY_ROLE: ${CADDY_ROLE:-primary}, TRACKSYS_DOMAIN: ${TRACKSYS_DOMAIN}, ACME_EMAIL: ${ACME_EMAIL}`.
- `api` e `worker` ficam no perfil `app` até a T-013 tirar o perfil (antes disso o fundador os sobe nomeando o serviço, seção 7). `migrate` é o único serviço com a URL do `tracksys_owner` (`MIGRATE_DATABASE_URL`).
- Nenhum contêiner monta `/var/run/docker.sock`.

`infra/env/ci.env`: todas as variáveis usadas no arquivo com valores fictícios (`TAILSCALE_IPV4=100.64.0.10`, `TRACKSYS_VERSION=v0.0.0-ci`, `TRACKSYS_DOMAIN=tracksys.example`…), só para `docker compose config` no CI e nos testes. `env_file` aponta para `/run/tracksys/prod.env`; nos testes, use `--env-file infra/env/ci.env` e a variável `TRACKSYS_ENV_FILE` (padrão `/run/tracksys/prod.env`) no `env_file`.

### (3) Caddy

`infra/caddy/Dockerfile`: `FROM caddy:2.10@sha256:<digest>`; `COPY Caddyfile /etc/caddy/Caddyfile`; `COPY sites/ /etc/caddy/sites/`; `COPY placeholder/ /srv/console/`. A T-007 troca o placeholder pelo build do console.

`infra/caddy/Caddyfile`:

```caddyfile
{
	admin 127.0.0.1:2019
	email {$ACME_EMAIL}
	servers {
		protocols h1 h2
	}
}
import /etc/caddy/sites/{$CADDY_ROLE}.caddy
```

`infra/caddy/sites/primary.caddy`:

```caddyfile
api.{$TRACKSYS_DOMAIN} {
	@blocked path /internal/* /metrics /metrics/*
	respond @blocked 404
	header Strict-Transport-Security "max-age=31536000; includeSubDomains"
	reverse_proxy api:3000 {
		header_up X-Client-Port {http.request.remote.port}
		flush_interval -1
	}
}
app.{$TRACKSYS_DOMAIN} {
	root * /srv/console
	header {
		Strict-Transport-Security "max-age=31536000; includeSubDomains"
		X-Content-Type-Options "nosniff"
		Referrer-Policy "no-referrer"
		Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://tiles.openfreemap.org; connect-src 'self' https://api.{$TRACKSYS_DOMAIN} https://tiles.openfreemap.org; worker-src blob:; frame-ancestors 'none'"
	}
	try_files {path} /index.html
	file_server
}
```

Sem diretiva `log` (o `api` grava `access_log`). `sites/standby.caddy` traz `status.{$TRACKSYS_DOMAIN}` com `reverse_proxy uptime-kuma:3001` (usado no F1). `placeholder/index.html` mostra "TrackSys — em implantação"; `placeholder/version.json` = `{"version":"placeholder"}`.

### (4) Traccar

`infra/traccar/traccar.xml.tpl`: XML `<!DOCTYPE properties SYSTEM 'http://java.sun.com/dtd/properties.dtd'>` com as chaves de [05 §2](../docs/spec/05-ingestao-e-telemetria.md#2-contrato-com-o-traccar) e [13 §5](../docs/spec/13-infra-e-operacao.md#5-traccar-operacional), com estes valores (nomes [VALIDAR — DEC-02], confirmados ou corrigidos na T-002):

| Chave | Valor no modelo |
|---|---|
| `database.driver` / `database.url` / `database.user` / `database.password` | `org.postgresql.Driver` / `jdbc:postgresql://db:5432/traccar` / `traccar` / `@TRACCAR_DB_PASSWORD@` |
| `database.historyDays` | `7` (REQ-DAD-017) |
| `database.registerUnknown` | `false` |
| `forward.enable`, `forward.type`, `forward.url` | `true`, `json`, `http://api:3001/internal/v1/traccar/positions` |
| `forward.header` | `X-Ingest-Token: @INGEST_SHARED_SECRET@` |
| `forward.retry.enable`, `.delay`, `.count`, `.limit` | `true`, `1000`, `10`, `20000` |
| `event.forward.enable`, `.url`, `.header` | `true`, `http://api:3001/internal/v1/traccar/events`, `X-Ingest-Token: @INGEST_SHARED_SECRET@` |
| `processing.copyAttributes` | ausente (nenhuma linha) |
| `filter.enable` | `false` |
| `gt06.port` | `5023` |
| `geocoder.enable` | `false` |
| `logger.level`, `logger.full`, `logger.console` | `info`, `false`, `true` |

`infra/traccar/render-config.sh` (POSIX sh, sem dependências): falha (`exit 78`) se `INGEST_SHARED_SECRET` tiver menos de 32 caracteres ou `TRACCAR_DB_PASSWORD` estiver vazio; troca `@VAR@` com `sed` (escapando `&`, `/` e `\` do valor) de `/opt/tracksys/traccar.xml.tpl` para `/opt/traccar/conf/traccar.xml` (modo 0600); nunca imprime valores; termina com `exec java $JAVA_OPTS -jar tracker-server.jar conf/traccar.xml` a partir de `/opt/traccar` [VALIDAR — T-002 comando da imagem fixada].

### (5) Provisionamento, firewall e serviços do host

| Arquivo | Conteúdo obrigatório |
|---|---|
| `oci-bootstrap.sh` | OCI CLI, idempotente por nome (consulta antes de criar): compartimento `tracksys`; VCN `10.0.0.0/16`; subnet pública regional `10.0.0.0/24`; internet gateway e rota; security list de [13 §2.1](../docs/spec/13-infra-e-operacao.md#21-firewall-em-duas-camadas) (TCP 80, 443, 5023 de `0.0.0.0/0`; UDP 41641 de `10.0.0.0/24`; ICMP 3/4; sem TCP 22); 2 instâncias `VM.Standard.A1.Flex` 2 OCPU/12 GB/boot 100 GB Ubuntu 24.04 ARM (`tracksys-p` FD-1, `tracksys-s` FD-2) com o user-data renderizado; IPs privados secundários `10.0.0.11` e `10.0.0.21`; IP público reservado `ip-svc` → `10.0.0.11` e `ip-sby` → `10.0.0.20`; bucket `tracksys-backup` (privado, versionamento desligado); grupo dinâmico `tracksys-vms` com política de leitura do prefixo `ops/` do bucket; orçamento com alerta em US$ 1; quota que zera shapes pagos. Flags [VALIDAR] na versão da OCI CLI do fundador; o script imprime os OCIDs criados em `infra/scripts/.oci-state.json` (no `.gitignore`) |
| `cloud-init.yaml` + `render-cloud-init.sh` | Usuário `ubuntu` com a chave Ed25519 do fundador; instala Tailscale e entra com chave de uso único (validade 1 h, tag `tag:prod` ou `tag:standby`); renderizado localmente para `infra/scripts/.cloud-init.rendered.yaml` (no `.gitignore`), nunca commitado |
| `provision.sh --role primary\|standby [--check]` | Os 8 passos de [13 §2](../docs/spec/13-infra-e-operacao.md#2-provisionamento-reproduzível), idempotentes; `--check` só verifica e sai 0 se nada mudaria, 1 se algo mudaria (lista o quê). Detecta `aarch64`/`x86_64` e funciona nos dois (REQ-OPS-001). No F0 os timers de backup, métricas e restore não são instalados (T-013) |
| `firewall.sh [--print]` | Gera e aplica as regras de [13 §2.1](../docs/spec/13-infra-e-operacao.md#21-firewall-em-duas-camadas): `INPUT` política `DROP`, aceitando `lo`, `ESTABLISHED,RELATED`, ICMP, `tailscale0`, UDP 41641 de `10.0.0.0/24` e TCP 80/443/5023; cadeia `DOCKER-USER` na interface pública (`PUBLIC_IFACE`, padrão a da rota padrão): 5023 com `connlimit --connlimit-above 50 --connlimit-mask 32` → `DROP` e `hashlimit --hashlimit-above 60/minute --hashlimit-mode srcip --hashlimit-name trk5023` em SYN novos → `DROP`; 5432 vinda da interface pública → `DROP`; `RETURN` no fim. `--print` só imprime em formato `iptables-restore` (usado nos testes). Nunca chama `netfilter-persistent reload` |
| `role-guard.sh` | [13 §9.3](../docs/spec/13-infra-e-operacao.md#93-guarda-de-papel-no-boot): lê `/etc/tracksys/role`; `standby` libera; `primary` lê `ops/role.json` do bucket por instance principal (10 tentativas a cada 30 s) e compara o OCID com o do IMDS; diferente → grava `fenced`, sai 1 e manda page (Pushover, variáveis `PUSHOVER_*`); inacessível → sai 1 (falha fechada). `provision.sh --role primary` grava o marcador inicial `{"primary":"<OCID>","epoch":1,"at":"<RFC 3339>"}` se não existir |
| `autoheal.sh` | Timer de 30 s: reinicia contêiner do projeto com health `unhealthy`; no máximo 3 reinícios por contêiner em 15 min (estado em `/var/lib/tracksys/autoheal.json`); no 4º, não reinicia e manda page "AL-12 <serviço>" |
| `bootstrap-stack.sh` | Subida inicial antes da T-013: `sops -d infra/secrets/prod.env.sops > /run/tracksys/prod.env` (0600 root), renderiza `pg_hba.conf`, `docker compose up -d --wait db traccar caddy`, aplica `infra/db/roles.sql` como `postgres` pelo socket |
| `check-secret-files.sh` | Falha (`exit 1`, listando) se existir no git arquivo `*.env`, `.env.*` (exceto `.env.example` da raiz e `infra/env/*.example`/`ci.env`), `*.key` ou `*.pem` fora de `infra/secrets/*.sops` |
| Units systemd | `tracksys-secrets.service` (oneshot no boot: decifra para `/run/tracksys/`), `tracksys-firewall.service` (`After=docker.service`, `PartOf=docker.service`, roda `firewall.sh`), `tracksys-autoheal.timer` (30 s), drop-in `docker.service.d/10-tracksys.conf` com `After=`/`Wants=tailscaled.service network-online.target` e `ExecStartPre=/opt/tracksys/infra/scripts/role-guard.sh` |

Host em UTC com chrony apontando para `169.254.169.254`; swap de 2 GB com `vm.swappiness=1`; `daemon.json` de [13 §2](../docs/spec/13-infra-e-operacao.md#2-provisionamento-reproduzível) passo 3.

### (6) Segredos

`.sops.yaml`:

```yaml
creation_rules:
  - path_regex: ^infra/secrets/.*\.sops$
    input_type: dotenv
    output_type: dotenv
    age: >-
      <age pública do fundador>,<age pública da VM primária>,<age pública da VM standby>
```

`infra/env/prod.env.example` lista, vazias, as variáveis do F0 até aqui: `TRACKSYS_DOMAIN`, `TRACKSYS_VERSION`, `ACME_EMAIL`, `CADDY_ROLE`, `TAILSCALE_IPV4`, `PEER_TAILSCALE_IP`, `POSTGRES_PASSWORD`, `TRACKSYS_OWNER_PASSWORD`, `TRACKSYS_APP_PASSWORD`, `TRACKSYS_INGEST_PASSWORD`, `TRACCAR_DB_PASSWORD`, `REPLICA_PASSWORD`, `OPS_RO_PASSWORD`, `OPS_AUDIT_PASSWORD`, `INGEST_SHARED_SECRET`, `MIGRATE_DATABASE_URL`, `WALG_S3_PREFIX`, `AWS_ENDPOINT`, `AWS_REGION`, `AWS_S3_FORCE_PATH_STYLE`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `WALG_LIBSODIUM_KEY`, `WALG_LIBSODIUM_KEY_TRANSFORM`, `WALG_COMPRESSION_METHOD`, `PUSHOVER_APP_TOKEN`, `PUSHOVER_USER_KEY`. As tarefas seguintes acrescentam as suas no mesmo arquivo.

CI (`.github/workflows/ci.yml`, acrescentar):
- job `secrets`: `docker run --rm -v "$PWD":/repo zricethezav/gitleaks:v8.<x>@sha256:<digest> detect --source /repo --no-banner --redact` e `infra/scripts/check-secret-files.sh`; verifica também que toda linha de valor em `infra/secrets/*.sops` começa com `ENC[AES256_GCM,` (CT-SEG-019).
- job `infra-lint`: `shellcheck` (imagem `koalaman/shellcheck:v0.10.0`) em `infra/**/*.sh`; `docker compose -f infra/docker-compose.yml --env-file infra/env/ci.env config --quiet`; `caddy validate` com a imagem fixada.

### (7) Runbook do fundador — `docs/runbooks/infra/provisionar-vm.md`

Passos numerados, cada um com comando exato e o que conferir: (1) DEC-12 e conta; (2) chave age do fundador (`age-keygen`, 2 cópias offline); (3) `render-cloud-init.sh` com a chave Tailscale de uso único; (4) `oci-bootstrap.sh`; (5) registros A de `gps.`, `api.`, `app.` → `ip-svc` e `status.` → `ip-sby`, TTL 60 s, proxy desligado; (6) bucket, chave S3 compatível do usuário IAM restrito ao bucket e `WALG_LIBSODIUM_KEY` (`openssl rand -hex 32`); (7) `prod.env.sops` (`sops --encrypt --in-place`); (8) `provision.sh --role primary` (e `--role standby` na `tracksys-s`); (9) `bootstrap-stack.sh`; (10) bloco de verificação na VM; (11) antes do `deploy.sh` da T-013, subida manual da aplicação: `docker compose build api migrate && docker compose run --rm migrate up && docker compose run --rm migrate check && docker compose up -d --wait api worker` (nomear o serviço ativa o perfil; exige o alvo `migrate` que a T-013 acrescenta ao `infra/app/Dockerfile`).

## Testes de aceite (congelados)

Locais (rodam no CI, sem nuvem):

`tests/acceptance/T-003/compose.test.ts` (CT-OPS-003, CT-ARQ-003 e CT-ARQ-004 na parte estática)
- Dado `docker compose -f infra/docker-compose.yml --env-file infra/env/ci.env config --format json`, Então existem os serviços `db`, `traccar`, `caddy`, `api`, `worker`, `migrate`; `mem_limit` (bytes) = 5368709120, 1610612736, 134217728, 1073741824, 1073741824, 536870912; `cpus` de `api`, `worker`, `caddy` = 1.5, 1.0, 0.5.
- Então as únicas portas publicadas são `80`, `443`, `5023` e `5432` com `host_ip = 100.64.0.10`; `api` e `worker` não publicam porta.
- Então todo healthcheck tem `interval = 10s`, `timeout = 3s`, `retries = 3`; todo serviço tem `restart = unless-stopped`; nenhum volume monta `docker.sock`; só `migrate` referencia `MIGRATE_DATABASE_URL`.
- Então `api` e `worker` usam `image = tracksys-app:v0.0.0-ci`, `migrate` usa `tracksys-migrate:v0.0.0-ci` com `build.target = migrate`, o healthcheck do `api` cita `127.0.0.1:3001/health/ready` e nenhum serviço referencia `apps/api/Dockerfile` ou `apps/worker/Dockerfile`.

`tests/acceptance/T-003/firewall.test.ts` (CT-OPS-002 e CT-SEG-024 na parte estática)
- Dado `PUBLIC_IFACE=enp0s6 infra/scripts/firewall.sh --print`, Então a saída contém `:INPUT DROP`, aceita `-i tailscale0`, `--dport 80`, `--dport 443`, `--dport 5023` e `udp --dport 41641 -s 10.0.0.0/24`, e não contém regra que aceite `--dport 22` fora de `tailscale0`.
- Então a cadeia `DOCKER-USER` tem, para `-i enp0s6 -p tcp --dport 5023`, `--connlimit-above 50` com `-j DROP` e `--hashlimit-above 60/minute` com `-j DROP`, `--dport 5432 -j DROP` na interface pública e termina com `-j RETURN`.

`tests/acceptance/T-003/traccar-config.test.ts` (CT-ING-001)
- Dado `INGEST_SHARED_SECRET` com 40 caracteres contendo `&` e `/` e `TRACCAR_DB_PASSWORD=x…`, Quando `render-config.sh` roda em modo de teste (`RENDER_ONLY=1`, saída num diretório temporário), Então o XML tem `forward.url = http://api:3001/internal/v1/traccar/positions`, `forward.header` = `X-Ingest-Token: <segredo exato>`, `database.registerUnknown = false`, `database.historyDays = 7`, nenhuma chave `processing.copyAttributes`, e o arquivo tem modo 0600.
- Dado o segredo com 16 caracteres, Então sai com 78 e o stderr não contém o segredo.
- Então `git grep` do segredo de teste no repositório retorna 0 ocorrências.

`tests/acceptance/T-003/postgres-config.test.ts` (CT-OPS-004 na parte estática)
- Dado `infra/db/postgresql.conf`, Então `shared_buffers = 1280MB`, `archive_mode = on`, `archive_timeout = 60`, `wal_level = replica`, `max_slot_wal_keep_size = 10GB`, `log_parameter_max_length = 0`, `log_parameter_max_length_on_error = 0`, `timezone = 'UTC'`.
- Dado `PEER_TAILSCALE_IP=100.64.0.20 envsubst` sobre `pg_hba.conf.tpl`, Então existe `host replication tracksys_replica 100.64.0.20/32 scram-sha-256` e a última linha é `host all all 0.0.0.0/0 reject`.

`tests/acceptance/T-003/caddy.test.ts`
- Dado a imagem `caddy` fixada, Quando `caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` roda com `CADDY_ROLE=primary` e `TRACKSYS_DOMAIN=tracksys.example`, Então sai com 0.
- Dado `sites/primary.caddy`, Então contém `respond @blocked 404` para `/internal/*` e `/metrics`, `header_up X-Client-Port {http.request.remote.port}`, `protocols h1 h2` no global e nenhuma diretiva `log`.

`tests/acceptance/T-003/secrets.test.ts` (CT-SEG-019 e CT-QLD-016 na parte de arquivos)
- Dado um arquivo temporário `infra/prod.env` com `ASAAS_API_KEY=chave-de-teste-0123456789abcdef`, Quando `check-secret-files.sh` roda, Então sai com 1 citando `infra/prod.env` (o teste apaga o arquivo no `finally`).
- Dado o repositório sem esse arquivo, Então sai com 0.
- Dado `.sops.yaml`, Então tem `path_regex: ^infra/secrets/.*\.sops$` e 3 destinatários age.

Na VM (executados pelo fundador; saídas anexadas ao PR):
- CT-OPS-001: `provision.sh --role primary` sai 0 em ≤ 30 min; 2ª execução ≤ 5 min; `--check` sai 0; `tailscale status` com `tag:prod`; `chronyc tracking` com offset < 100 ms; `iptables -S INPUT` começa com `-P INPUT DROP`.
- CT-OPS-002 / CT-ARQ-003 / CT-SEG-024: `nmap -Pn -sT -p 1-65535 <ip-svc>` de fora mostra só 80, 443, 5023; `ssh ubuntu@<ip-svc>` expira em 10 s; 51 conexões simultâneas na 5023 de um IP externo → a 51ª não completa e o contador de `DROP` da `DOCKER-USER` > 0; `systemctl restart docker` → regras de volta em ≤ 60 s.
- CT-OPS-003: `docker inspect` com os limites acima; `docker compose exec caddy kill -STOP 1` → reiniciado em ≤ 90 s.
- CT-OPS-004 / CT-ARQ-004: `SHOW shared_buffers` = `1280MB`, `SHOW archive_timeout` = `1min`; `psql "host=<ip-svc> port=5432"` de fora expira; `tracksys_ops_ro` em `SELECT 1 FROM app.vehicle` → 42501.
- WAL: com escrita de teste por 10 min, `now() − last_archived_time` ≤ 120 s em todas as leituras de `pg_stat_archiver` e `failed_count` estável.
- CT-OPS-023: `curl -s -H "Authorization: Bearer Oracle" http://169.254.169.254/opc/v2/instance/` → `canonicalRegionName` ∈ `sa-saopaulo-1`, `sa-vinhedo-1`; `WALG_S3_PREFIX`/`AWS_ENDPOINT` com a mesma região.
- CT-ING-001: `docker compose exec traccar cat /opt/traccar/conf/traccar.xml` com a URL e o segredo certos.
- DNS: `dig +noall +answer gps.<domínio provisório>` com TTL ≤ 60 e o IP de `ip-svc`.
- Marco S1: posição do J16 de bancada visível no Traccar (túnel SSH `-L 8082:172.30.0.6:8082`).

## Comandos de verificação

```bash
pnpm install
pnpm lint
pnpm test:acceptance -- tests/acceptance/T-003
docker compose -f infra/docker-compose.yml --env-file infra/env/ci.env config --quiet
docker run --rm -v "$PWD/infra":/infra koalaman/shellcheck:v0.10.0 $(cd infra && git ls-files '*.sh' | sed 's|^|/infra/|')
docker buildx build --platform linux/amd64,linux/arm64 infra/db          # CT-OPS-005 (2 builds; leva minutos)
docker buildx build --build-arg WALG_SHA256_AMD64=0000000000000000000000000000000000000000000000000000000000000000 --platform linux/amd64 infra/db   # deve falhar no sha256sum -c
pnpm verify
```

## Definição de pronto

- [ ] Testes locais de `T-003` verdes; jobs `secrets` e `infra-lint` verdes no PR.
- [ ] Fundador executou o runbook; saídas da verificação na VM anexadas ao PR; marco S1 (posição do J16 no Traccar da VM) registrado.
- [ ] `prod.env.sops` só com valores `ENC[AES256_GCM,…]`; chave age e `WALG_LIBSODIUM_KEY` em 2 cópias offline.
- [ ] `pg_stat_archiver` arquivando sem falha há ≥ 1 h.
- [ ] PR `feat(infra): VM primária, compose, firewall e DNS (T-003)` com revisão cruzada (N0 nos arquivos de segredos e CI).

## Decisões já tomadas (não pergunte, siga)

| Dúvida provável | Resposta |
|---|---|
| O Dockerfile da aplicação não existe ainda. O Compose quebra? | Não. `api` e `worker` ficam no perfil `app` e `migrate` no perfil `ops`; `docker compose config` não exige o build. A T-004 cria `infra/app/Dockerfile` (imagem única `tracksys-app`, estágio final `app`); a T-013 acrescenta o alvo `migrate` e tira o perfil `app` ([13 §3](../docs/spec/13-infra-e-operacao.md#3-docker-compose)). |
| Healthcheck do `api` na 3000 ou na 3001? | Na 3001 (interna, com `checks`), como o `worker` na 3002. A 3000 pública responde só `{"status"}` ([03](../docs/spec/03-arquitetura.md) REQ-ARQ-005) e é a das sondas e do smoke da T-013. |
| Arquivar WAL já, sem base diária? | Sim ([13 §18](../docs/spec/13-infra-e-operacao.md#18-requisitos): a T-003 já sobe arquivando). A base diária, a retenção e o restore são da T-013. |
| Domínio definitivo ainda não existe (DEC-04). | Use um domínio provisório só para a bancada em `TRACKSYS_DOMAIN`. Nenhum veículo real recebe SMS com o domínio provisório. Trocar o domínio depois é só mudar a variável e os registros A. |
| Standby no F0? | Só a VM criada (garante capacidade A1) com Tailscale. Nenhum contêiner nela no F0. |
| IP reservado não pode ser movido entre VMs no Always Free [VALIDAR — DEC-12]. | Crie mesmo assim; o failover do F1 troca os registros A se o `oci network public-ip update` falhar. Não bloqueia o F0. |
| Posso usar `ufw`? | Não. `iptables` com `firewall.sh` e cadeia `DOCKER-USER` ([13 §2.1](../docs/spec/13-infra-e-operacao.md#21-firewall-em-duas-camadas)). `ufw` não enxerga as portas publicadas pelo Docker. |
| Por que `render-config.sh` dentro do contêiner do Traccar? | O segredo nunca fica no repositório nem em arquivo do host; é renderizado no start a partir do `env_file` ([05 §2](../docs/spec/05-ingestao-e-telemetria.md#2-contrato-com-o-traccar)). |
| A imagem do Traccar não tem `wget`. | Troque o healthcheck por `curl -fs` ou por `java`/`nc` disponível na imagem fixada e registre no PR. Não instale pacotes na imagem. |
| `tracksys_ops_audit` sem privilégios? | Sim, até a T-013 criar o schema `ops` e conceder `INSERT` em `ops.audit_log`. |
| Agente pode rodar `oci-bootstrap.sh`? | Não. Agente não tem credencial de produção. Ele escreve, testa com `--help`, `shellcheck` e `--print`, e o fundador executa. |
