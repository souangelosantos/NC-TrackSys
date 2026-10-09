# T-033 — Operação avançada: deploy automatizado com rollback, Alloy/Grafana/Alertmanager, migration-compat, teste de carga e cópia R2

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (01–15/11/2026 ou 16–30/11/2026; a cópia R2 até 15/11/2026) |
| Requisitos | REQ-OPS-006 (disparo pela Action), REQ-OPS-008 (cópia R2), REQ-OPS-016 (Alloy e redação no Loki), REQ-OPS-017 (regras no Grafana), REQ-ARQ-012 (teste de carga), REQ-DAD-020 (`migration-compat`), REQ-ARQ-014 (redação no Alloy), REQ-ING-021 (métricas Prometheus completas expostas no Grafana) |
| Invariantes | INV-05, INV-07, INV-12 |
| Risco de revisão | N0 pelo caminho: `.github/workflows/**` (`deploy.yml`, `load-test.yml`, `ci.yml`); demais arquivos N1 (scripts, Alloy, regras) |
| Depende de | T-013 (`deploy.sh`, `smoke.sh`, backup WAL-G, `host-watch.sh`, `ingest-lag.sh`) e T-019 (guardas de CI) |
| Estimativa | 3 sessões de agente (1: `deploy.yml` e `migration-compat`; 2: Alloy, Grafana Cloud, regras e Alertmanager; 3: teste de carga e cópia R2) |
| Bloqueado por decisão | DEC-04 (domínio usado no smoke), DEC-12 (standby e R2) |
| Status | Resumido — DoR pendente |

## Objetivo

Passar a operação do F0 (deploy manual assistido, sondas locais, backup só na Oracle) para o regime do F1:
- deploy por tag disparado pela GitHub Action, com rollback automático;
- métricas e logs no Grafana Cloud com redação de dado pessoal e regras de alerta com Pushover por prioridade;
- compatibilidade N/N+1 de migrations no CI, teste de carga de pior caso e cópia do backup na Cloudflare R2.

## Contexto obrigatório

- [13 §6](../docs/spec/13-infra-e-operacao.md#6-configuração-e-segredos) a §8, §10 a §13: segredos, deploy, backups, observabilidade, alertas e paging.
- [03 §11](../docs/spec/03-arquitetura.md#11-orçamento-de-recursos-vm-de-12-gb-2-ocpu-ampere) e REQ-ARQ-012: limites de recurso e carga de 100 msg/s.
- [04 §10](../docs/spec/04-dominio-e-dados.md#10-migrations-expandcontract) e REQ-DAD-020: expand/contract e compatibilidade N/N+1.
- [T-013](T-013-deploy-backup-restore-sondas.md): o que já existe e não se repete. [Anexo C](../docs/anexos/C-operacional.md) R8.

## Escopo — fazer

1. `.github/workflows/deploy.yml`: tag `v*.*.*` e `workflow_dispatch`, job `verify` e job `deploy` (Tailscale + SSH forced-command), janela em dia útil sem feriado (`packages/domain/src/calendar/holidays-br.ts`), `force` só com justificativa, ambiente `production` restrito a tags.
2. Job `migration-compat` no `ci.yml` e `check-migration-compat.sh` (REQ-DAD-020): migrations do PR aplicadas num banco limpo e a suíte `tests/acceptance` do commit base rodando contra o schema novo.
3. Alloy (métricas e logs com `redaction.alloy`), Grafana Cloud, `f0.rules.yaml` com `promtool test rules`, Alertmanager e `grafana-sync.sh`. Regras AL-03, AL-04, AL-05 e AL-07 passam do `host-watch.sh` e da `ingest-lag.sh` para o Grafana; entram AL-08, AL-11 e AL-12.
4. Teste de carga (CT-ARQ-012): simulador de carga em `packages/testkit` (`seed-load-fleet.ts`, `simulate-ingest.ts`), `docker-compose.load.yml`, `run-load.sh` e `load-test.yml` manual (3.000 rastreadores a 30 s por 15 min).
5. `copy-r2.sh` e timer: `rclone copy` horário do bucket Oracle para a R2 (nunca `sync`), com bucket lock; cobre a parte "fora da Oracle" do CT-OPS-008.

## Fora do escopo

- Standby, failover, Uptime Kuma e status page: T-028. Gateway de incidentes e agente SRE: T-034.
- Reescrever `deploy.sh`, `smoke.sh` ou o backup WAL-G (T-013).
- Teste de carga contra a VM de produção ou contra banco real.

## Para completar o DoR

1. Especificação detalhada de `deploy.yml` (SHAs das actions, permissões, janela com feriados e `force`), de `check-migration-compat.sh`, de `config.alloy` e `redaction.alloy`, de `f0.rules.yaml`, do template do Alertmanager e dos scripts de carga.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-033/`, congelados antes da implementação (CT-OPS-006 por Action, CT-OPS-016 com Alloy, CT-OPS-017 com `promtool`, CT-DAD-020, CT-ARQ-012).
3. Lacunas concretas a fechar:
   - [VALIDAR] Alertmanager gerenciado do Grafana Cloud free com `pushover_configs`; senão contact point Pushover do Grafana com o mesmo mapeamento de prioridades.
   - [VALIDAR] sintaxe de `stage.replace` e de `declare` na versão fixada do Alloy.
   - [VALIDAR] `mimirtool rules load` e `mimirtool alertmanager load` no plano free.
   - Nomes das métricas do exporter de Postgres para AL-05 (`pg_stat_archiver_*`).
   - Bucket R2: ciclo de vida de 35 dias e bucket lock de 14 dias [VALIDAR]; credenciais fora do repositório.
   - Segredos do GitHub (`TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET`, `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS`) cadastrados pelo fundador.
   - Verificação de dia útil sem feriado no `deploy.yml` reutilizando o calendário do TypeScript (como chamar do job).
4. Seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md#5-dor-e-dod)): `actor_id = 'ci:<GITHUB_RUN_ID>'` na auditoria, migração das regras locais para o Grafana sem page dupla, carga só em banco descartável, retirada do `host-watch.sh` depois que o Grafana pagar, risco aceito da R2 até 15/11.
5. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
