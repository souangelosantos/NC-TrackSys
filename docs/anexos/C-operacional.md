# Anexo C — Operacional

> **Resumo:** O que fazer quando algo dá errado e as rotinas que evitam que dê: runbook de 1 página do plantonista da operadora, 11 runbooks técnicos com comandos exatos, checklists do G0 e do onboarding de operadora, procedimento de requisição de autoridade, modelo de postmortem e rotina do fundador. Regras, limiares, scripts e SLO: [13 — Infra e operação](../spec/13-infra-e-operacao.md).
> **Fases:** F0, F1, F2  ·  **Status:** Aprovado para execução
> **Muda em relação à v1.1:**
> - Quatro runbooks de componente viram 11 runbooks com sintoma, diagnóstico, ação, verificação e comunicação.
> - Entra o runbook do plantonista: a central da operadora opera a contingência por SMS sem a plataforma.
> - Entram checklists de gate e de onboarding, procedimento de autoridade, postmortem e rotina do fundador.

## 1. Runbook do plantonista (1 página)

> Imprima esta seção e deixe na central. Use quando o app ou o painel não abrem, quando os alertas param de chegar ou quando a Versix avisar um incidente.

**Passo 1 — A plataforma caiu?** Abra `https://status.tracksys.com.br` (endereço definitivo após DEC-04).
- Tudo verde: o problema é do veículo, do chip ou do celular do cliente. Atenda como sempre.
- Vermelho ou amarelo: siga esta página. A Versix já foi avisada automaticamente.
- A status page também não abre: ligue para a Versix (passo 6) e siga esta página.

**Passo 2 — Confirme quem pede.** Antes de qualquer SMS, confira na lista de contingência: (a) o telefone de quem liga é o do titular; (b) nome completo; (c) placa; (d) 3 últimos dígitos do CPF. Faltou um item → não envie SMS de comando nem informe localização; ofereça retorno no telefone cadastrado.

**Passo 3 — Localizar por SMS.** No portal emnify/Meta Telecom, envie ao número do chip do rastreador (coluna "Linha" da lista) o texto "Posição" do cartão de SMS (`WHERE#` no J16 [VALIDAR — DEC-02]). A resposta chega no portal em até 2 min, com coordenadas ou link de mapa. Sem resposta em 5 min: envie mais 1 vez; se persistir, o rastreador está sem sinal ou desligado — anote.

**Passo 4 — Desbloquear por SMS.** Sempre permitido ao titular confirmado no passo 2. Envie o texto "Desbloquear" do cartão de SMS. "Entregue" no portal não é confirmação: peça ao titular para dar partida e anote o resultado.

**Passo 5 — Bloquear por SMS (contingência).** Só com uma destas condições:
- **(A)** furto ou roubo relatado pelo titular confirmado, com a ocorrência anotada (hora e, se houver, número do BO); ou
- **(B)** pedido do titular confirmado com o veículo **parado**, comprovado por posição SMS de no máximo 5 minutos atrás com velocidade 0 [PREMISSA: 5 min].

E respeite o ponto de corte do veículo (coluna "Corte" da lista), a mesma regra do app ([06 §3.2](../spec/06-comandos-e-bloqueio.md)):

| Corte | Pode bloquear |
|---|---|
| Arranque (`starter`) | Em (A) ou (B): só impede nova partida |
| Bomba de combustível (`fuel_pump`) | Em (B); em (A), se a posição SMS de até 5 min mostrar velocidade ≤ 40 km/h (limite da Lider) |
| Ignição (`ignition`) ou "não sei" | Só com o veículo parado (velocidade 0 na posição SMS de até 5 min), mesmo em furto |
| Sem bloqueio | Nunca |

Nunca bloqueie por falta de pagamento (INV-09). Roubo com a vítima dentro do veículo: não bloqueie; ligue 190.

**Passo 6 — Quem acionar.** Versix: telefone de plantão entregue no onboarding; sem resposta em 5 min, ligue de novo e mande WhatsApp "TRACKSYS FORA — <operadora> — <hora>". Polícia: 190 em roubo em andamento. Equipe de busca e guincho: procedimento interno da operadora.

**Passo 7 — Anote para lançar depois.** No F1, em até 72 h, lance cada SMS de bloqueio ou desbloqueio no painel (Comandos → "Registrar contingência", [06 §10](../spec/06-comandos-e-bloqueio.md)); no F0, envie a anotação à Versix. Anote agora:

| Campo | Exemplo |
|---|---|
| Data e hora do SMS (horário de Brasília) | 12/12/2026 02:14 |
| Placa e tipo | ABC1D23 — desbloqueio |
| Quem pediu, telefone, como confirmou | Titular, telefone cadastrado + nome + placa + CPF |
| Motivo | Pedido do titular / furto / roubo |
| Resposta do rastreador | Texto recebido no portal, sem a senha |
| Posição SMS | Hora e link recebidos |
| BO ou ocorrência | Número, se houver |
| Plantonista | Nome |

Nunca escreva a senha do rastreador na anotação nem no painel.

**Na central, sempre:** lista de contingência impressa, atualizada toda semana e guardada trancada (placa, titular, telefone, 3 últimos dígitos do CPF, linha do chip, modelo do rastreador, corte); cartão de SMS com a senha em poder do responsável da operadora; usuário próprio do plantonista no portal emnify/Meta Telecom. [NOVA DECISÃO PROPOSTA: o console exporta a lista de contingência (PDF e CSV) para o `operator_admin` no F1, com `audit_log` `export.create`.]

## 2. Runbooks técnicos

Convenções: entrar por `ssh ubuntu@tracksys-p` (ou `tracksys-s`) pela Tailscale e `sudo -i`; `dc`, `opsql` e `$TRACKSYS_DOMAIN` vêm de `/etc/profile.d/tracksys.sh` ([13 §2](../spec/13-infra-e-operacao.md)); horários em UTC; toda ação vai para a nota do incidente; SEV e prazos de comunicação em [13 §14](../spec/13-infra-e-operacao.md). Regra de alerta → runbook: AL-01/AL-02 → R1, R3 ou R7; AL-03/AL-05 → R2; AL-07 → R4; AL-08 → R4 ou R5; AL-09 → R6; AL-10 → R3.

### R1 — Banco indisponível

**Sintoma:** `/health/ready` 503 com `checks.db = "fail"`; ingestão respondendo 503 ao Traccar; console e app com erro.
**Diagnóstico:**
```bash
dc ps db
dc logs --tail 200 db
dc exec -T db pg_isready -U postgres -d tracksys
df -h /
dmesg -T | grep -i -E 'out of memory|killed process' | tail -5
opsql "SELECT ops.health_snapshot();"
```
**Ação:**
1. Contêiner parado ou morto por OOM → `dc up -d db`; acompanhe `dc logs -f db` até `database system is ready to accept connections`. A recuperação de crash pode levar até 10 min: não reinicie no meio.
2. `No space left on device` → R2 antes de qualquer outra coisa.
3. `too many connections` → `dc exec -T -u postgres db psql -d tracksys -c "SELECT usename, application_name, state, count(*) FROM pg_stat_activity GROUP BY 1,2,3 ORDER BY 4 DESC;"` e reinicie o dono das conexões (`dc restart worker` ou `dc restart api`).
4. `PANIC`, `invalid page` ou banco sem subir em 15 min → não apague nada em `/var/lib/docker/volumes`; F1: R7; F0: R8.

**Verificação:** `curl -fsS https://api.$TRACKSYS_DOMAIN/health/ready` devolve `{"status":"ok"}`; `opsql "SELECT * FROM ops.inbox_stats();"` mostra `pending` caindo; sondas verdes.
**Comunicação:** SEV1 se passar de 5 min.

### R2 — Disco cheio

**Sintoma:** AL-03 (> 80%); AL-05; log do Postgres com `No space left on device`.
**Diagnóstico:**
```bash
df -h /
du -xh --max-depth=3 /var/lib/docker 2>/dev/null | sort -h | tail -15
docker system df
dc exec -T -u postgres db du -sh /var/lib/postgresql/data/pg_wal
dc exec -T -u postgres db psql -d tracksys -Atc "SELECT archived_count, failed_count, last_archived_time, last_failed_time FROM pg_stat_archiver;"
dc exec -T -u postgres db psql -d tracksys -Atc "SELECT slot_name, active, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) FROM pg_replication_slots;"
opsql "SELECT * FROM ops.storage_stats();"
```
**Ação, nesta ordem:**
1. `/opt/tracksys/infra/scripts/disk-cleanup.sh` (logs do Docker, journal acima de 500 MB, imagens além das 3 últimas tags). Nunca `docker volume prune`.
2. `pg_wal` grande e `failed_count` subindo → arquivamento quebrado; `dc logs --since 1h db | grep -i wal-g` mostra a causa (credencial, bucket, rede). Corrija no SOPS e aplique (R10 passo 3). Nunca apague arquivos de `pg_wal` à mão.
3. Slot inativo retendo mais de 8 GB (standby fora há horas) → `dc exec -T -u postgres db psql -c "SELECT pg_drop_replication_slot('standby_1');"`; reconstrua a standby depois (`standby-rebuild.sh`).
4. Inbox ou outbox crescendo → confira se `ingest.retention` e a limpeza da outbox rodaram: `opsql "SELECT * FROM ops.queue_stats();"`.
5. Ainda acima de 90% → aumente o boot volume no console da OCI (Block Storage → Boot Volumes → Edit) e, após o rescan do disco indicado pela OCI, rode `growpart /dev/sda 1 && resize2fs /dev/sda1` [VALIDAR nome do dispositivo]; custo em [13 §16](../spec/13-infra-e-operacao.md).

**Verificação:** `df -h /` < 75%; `last_archived_time` há menos de 2 min.
**Comunicação:** SEV2; SEV1 se o banco parou.

### R3 — Traccar sem conexões

**Sintoma:** AL-10 (queda > 30% das sessões em 5 min); `ingest_last_received_age_seconds` > 300 s; "sem comunicação" suprimido ([07 §4](../spec/07-alertas-e-tempo-real.md)).
**Diagnóstico:**
```bash
nsenter -t "$(docker inspect -f '{{.State.Pid}}' "$(dc ps -q traccar)")" -n ss -Htn state established '( sport = :5023 )' | wc -l   # sessões no namespace do contêiner
dc ps traccar && dc logs --tail 200 traccar
dig +short gps.$TRACKSYS_DOMAIN                   # deve ser o ip-svc
iptables -L DOCKER-USER -v -n | head -20          # contador de DROP subindo = limite de taxa barrando
dc exec -T api node -e "fetch('http://traccar:8082/api/server').then(r=>console.log(r.status)).catch(e=>console.log(e.message))"
```
De fora (notebook): `nc -vz -w 5 gps.$TRACKSYS_DOMAIN 5023`. No portal emnify/Meta Telecom: chips sem sessão de dados, por operadora móvel.
**Ação:**
1. Traccar parado ou sem responder → `dc restart traccar` (todas as sessões reconectam).
2. DNS errado → corrija o A na Cloudflare (TTL 60 s). Security list ou iptables alterados → `/opt/tracksys/infra/scripts/firewall.sh`.
3. `DROP` da 5023 subindo com muitos rastreadores atrás do mesmo NAT da emnify → acrescente a faixa à allowlist ([13 §2.1](../spec/13-infra-e-operacao.md)) e rode `firewall.sh`.
4. Queda concentrada numa operadora móvel no portal → falha da rede celular, não da plataforma: avise as operadoras; nada a reiniciar.

**Verificação:** sessões ≥ 90% do nível anterior em 15 min [VALIDAR — DEC-02: tempo de reconexão do J16]; 30 min depois, `ingest.reconcile` recuperou a lacuna ([05 §12](../spec/05-ingestao-e-telemetria.md)).
**Comunicação:** SEV1; informe que "sem comunicação" ficou suprimido no intervalo.

### R4 — Inbox acumulando

**Sintoma:** AL-07; alertas atrasados (AL-08).
**Diagnóstico:**
```bash
opsql "SELECT * FROM ops.inbox_stats();"     # pending, quarantined, idade, código de erro
opsql "SELECT * FROM ops.queue_stats();"
dc ps worker && dc logs --since 15m worker | grep -E '"level":"(error|fatal)"' | tail -20
```
**Ação:**
1. `worker` parado ou `unhealthy` → `dc restart worker`.
2. Mesmo código de erro em muitas linhas logo após um deploy → `/opt/tracksys/infra/scripts/deploy.sh rollback`.
3. Depois da correção: `dc exec -T worker node dist/cli.js ingest:wake-pending`.
4. Quarentena, só com a causa entendida: `dc exec -T worker node dist/cli.js ingest:reprocess --reason <código> --since <RFC 3339> --dry-run`, depois sem `--dry-run` (equivale ao script pnpm de [05](../spec/05-ingestao-e-telemetria.md); sem efeito externo, INV-05).

**Verificação:** `pending` = 0 em 10 min; p95 de alerta < 30 s.
**Comunicação:** SEV2; SEV1 se a latência passar de 120 s por 5 min.

### R5 — Push falhando

**Sintoma:** `alert_deliveries_total{status="failed"}` subindo; AL-08; clientes sem alerta.
**Diagnóstico:**
```bash
opsql "SELECT * FROM ops.alert_latency(now() - interval '30 minutes', now());"
dc logs --since 30m worker | grep -i fcm | grep -E '"level":"(warn|error)"' | tail -20
```
Classifique o erro do FCM [VALIDAR códigos na versão da API]: `UNREGISTERED` em poucos tokens → normal (token antigo, removido); `UNAUTHENTICATED` ou `PERMISSION_DENIED` em todos → credencial; `THIRD_PARTY_AUTH_ERROR` só no iOS → chave APNs no Firebase; `UNAVAILABLE` ou `INTERNAL` → instabilidade do FCM (página de status do Firebase).
**Ação:** credencial → nova chave da conta de serviço no Google Cloud, `FCM_*` no SOPS, aplique (R10 passo 3) e revogue a antiga; APNs → nova chave `.p8` no Apple Developer, carregada no Firebase; FCM fora → só comunicar: as entregas pendentes são retentadas ([07](../spec/07-alertas-e-tempo-real.md)).
**Verificação:** ignição ligada no J16 de bancada gera push no celular de teste em ≤ 60 s.
**Comunicação:** SEV1 se nenhum push sai há mais de 5 min; peça às operadoras que acompanhem a fila de alertas do console.

### R6 — Certificado expirando

**Sintoma:** AL-09 (< 14 dias); erro de TLS no navegador ou no app.
**Diagnóstico:**
```bash
for h in api app status; do echo | openssl s_client -connect $h.$TRACKSYS_DOMAIN:443 -servername $h.$TRACKSYS_DOMAIN 2>/dev/null | openssl x509 -noout -enddate; done
dc logs --since 24h caddy | grep -i -E 'acme|challenge|certificate' | tail -30
dig +short api.$TRACKSYS_DOMAIN
```
**Ação:** porta 80 fechada → reabra na security list (o desafio HTTP-01 usa a 80); DNS na VM errada → corrija; limite da Let's Encrypt → aguarde, o Caddy também tenta outro emissor [VALIDAR emissores padrão da versão]; em seguida `dc restart caddy`.
**Verificação:** `notAfter` mais de 30 dias à frente nos 3 hosts.
**Comunicação:** SEV3; SEV1 se expirou.

### R7 — Failover para a standby (F1)

**Quando:** primária inacessível nas duas sondas por ≥ 10 min, ou no ar mas irrecuperável (banco corrompido, disco perdido) por decisão do fundador. Corrupção lógica (DELETE ou migration errada) **não** se resolve com failover, porque a standby já replicou o erro: use R8 com ponto anterior.
**Diagnóstico (na standby):**
```bash
tailscale ping -c 3 tracksys-p
oci compute instance get --instance-id "$PRIMARY_OCID" --auth instance_principal --query 'data."lifecycle-state"'
opsql "SELECT * FROM ops.replication_status();"     # replay recente?
```
**Ação:** `/opt/tracksys/infra/scripts/failover --reason "<texto>"`; o script segue [13 §9.2](../spec/13-infra-e-operacao.md) e imprime cada etapa. Parou no fencing: confira no console da OCI; com a instância `STOPPED` ou `TERMINATED`, ou com o `ip-svc` desanexado à mão, rode `failover --fenced-manually --reason "<texto>"`. Nunca promova com a primária possivelmente viva e dona do `ip-svc`.
**Verificação:** `slo-gps-tcp` e `slo-api-https` verdes; sessões TCP subindo; `opsql "SELECT ops.health_snapshot();"` com `inRecovery = false`; comandos que estavam em DISPATCHING ou AWAITING_CONFIRMATION agora UNKNOWN com motivo `failover`.
**Depois (≤ 24 h):** ligue a ex-primária pelo console (o guarda a mantém `fenced`) e rode nela `/opt/tracksys/infra/scripts/standby-rebuild.sh --primary tracksys-s`.
**Comunicação:** SEV1; status page; WhatsApp às operadoras; postmortem.

### R8 — Restore de backup

**Quando:** F0 sem standby; perda das duas VMs ou da região; corrupção lógica replicada.
1. Alvo: `--target-time "<RFC 3339>"` antes do incidente ou `--target-name deploy-<tag>` (ponto criado em todo deploy). Bases: `wal-g backup-list` em qualquer host com as variáveis do SOPS.
2. Host: VM limpa ou nova (`oci-bootstrap.sh` + `provision.sh --role primary`; fora da Oracle, só `provision.sh` em Ubuntu 24.04), ~30 min.
3. `/opt/tracksys/infra/scripts/backup/restore.sh --target-time "2026-11-20T14:05:00Z"`: `backup-fetch`, `recovery.signal`, recuperação até o alvo, promoção.
4. Suba `traccar api worker caddy` com `COMMAND_DISPATCH_ENABLED=false` e `EMNIFY_SMS_ENABLED=false`; rode a reconciliação de REQ-ARQ-016 (`dc exec -T worker node dist/cli.js commands:reconcile-failover`); religue as flags.
5. Banco `traccar` restaurado junto → mantenha `INGEST_SOURCE_INSTANCE`; recriado vazio → troque para `traccar-02` (REQ-ARQ-013).
6. Lacuna de ingestão, se o Traccar antigo ainda existir: `ingest:backfill --from <alvo> --to <agora>` (até 7 dias, sem efeito externo, [05 §12](../spec/05-ingestao-e-telemetria.md)).
7. Revogações perdidas entre o alvo e o incidente (sessões, links, grants, chaves de aparelho, memberships): no Loki, `{service="api"} | json | action=~".*\\.revoke|auth\\.sessions_revoke"` no intervalo; refaça cada uma pelo console ou CLI [exige 1 linha de log por ação de auditoria com `action` e ids, proposta para [08](../spec/08-identidade-e-seguranca.md)].
8. Rede: `ip-svc` para o host novo (`oci network public-ip update ...`) ou registros A na Cloudflare.
9. `dc exec -T -u postgres db wal-g backup-push /var/lib/postgresql/data` imediato (nova timeline).

**Verificação:** checagens de [13 §8](../spec/13-infra-e-operacao.md) item 5; sondas verdes; ≤ 2 h e perda ≤ 5 min (G0-7).
**Comunicação:** SEV1; informe às operadoras o intervalo perdido, se houver.

### R9 — VM recuperada pela Oracle

**Sintoma:** instância `STOPPED` sem ação nossa; e-mail da Oracle sobre instância ociosa ou recuperada; instância `TERMINATED`; "Out of host capacity" ao criar.
**Diagnóstico:** console da OCI → Compute → Instances (estado e Work Requests); e-mails da conta; `oci compute instance get --instance-id <OCID> --query 'data."lifecycle-state"'`.
**Ação:**
1. Primária parada: F1 → R7 se o incidente já passa de 10 min; senão `oci compute instance action --action START --instance-id <OCID>` e acompanhe o boot (o guarda libera se ela ainda for a primária do marcador). F0 → START; sem volta em 30 min, R8.
2. Standby parada → START; a réplica alcança pelo slot ou pelo `restore_command`; sem alcançar em 1 h, `standby-rebuild.sh`.
3. Terminada → `oci-bootstrap.sh` recria. "Out of host capacity" → repita a cada 5 min por até 2 h, depois outro fault domain; em último caso, shape pago temporário ([13 §16](../spec/13-infra-e-operacao.md)).
4. Prevenção: conta em Pay As You Go e instâncias acima dos limiares de ociosidade [VALIDAR — DEC-12].

**Verificação:** `cat /etc/tracksys/role` correto nas duas VMs; lag da réplica < 60 s.
**Comunicação:** conforme o impacto.

### R10 — Segredo vazado

**Sintoma:** alerta do gitleaks ou do secret scanning do GitHub; segredo em log, Sentry ou print; notebook ou celular perdido; acesso estranho.
**Ação (conter → trocar → verificar):**
1. Revogue primeiro no provedor (tabela abaixo).
2. Gere o valor novo (`openssl rand -base64 48` para segredos internos), edite com `sops infra/secrets/prod.env.sops` (e `standby.env.sops`) e faça commit.
3. Aplique: `/opt/tracksys/infra/scripts/deploy.sh "$(cat /etc/tracksys/current-version)"` (o redeploy da mesma tag relê os segredos).
4. Confirme que o valor antigo é recusado.
5. Procure uso indevido no intervalo de exposição (Loki, logs do provedor, `audit_log`); acesso a dado pessoal → R11.

| Segredo | Como trocar | Efeito colateral |
|---|---|---|
| `INGEST_SHARED_SECRET` | Valor novo; o deploy re-renderiza `traccar.xml` e reinicia `traccar` e `api` | Rastreadores reconectam |
| `BETTER_AUTH_SECRET` | Valor novo | Todas as sessões caem |
| Senhas de papéis do banco | `ALTER ROLE <papel> PASSWORD '<novo>'` como `postgres`, SOPS, deploy | — |
| `SECRETS_MASTER_KEYS` | Nova versão ativa e `secrets.rewrap` ([08 §8](../spec/08-identidade-e-seguranca.md)) | — |
| Chave Asaas de uma operadora | A operadora gera outra no Asaas e atualiza no console | — |
| Conta de serviço do FCM, chave APNs | Revogar no Google Cloud ou na Apple; nova no SOPS ou no Firebase | — |
| Credenciais S3 (Oracle, R2) | Revogar a Customer Secret Key ou o token da R2; nova no SOPS | — |
| `WALG_LIBSODIUM_KEY` | Nova chave e base completa imediata; a antiga fica offline enquanto existir backup cifrado com ela | — |
| Token da Cloudflare, chave da Tailscale, token do Pushover, `ANTHROPIC_API_KEY`, chave SSH do CI | Revogar no painel do provedor; novo no SOPS ou no GitHub | — |
| Chave age de VM ou do fundador | Tirar o destinatário do `.sops.yaml`, `sops updatekeys` e **trocar todos os segredos do arquivo** (o histórico do git segue decifrável com a chave vazada) | Rotação completa |

**Verificação:** gitleaks verde; valor antigo recusado; nenhum uso suspeito.
**Comunicação:** SEV1 se o segredo dá acesso a dado pessoal ou a comando; postmortem.

### R11 — Incidente de segurança com dado pessoal

No serviço principal a operadora é controladora e a Versix, operadora (processadora) ([Anexo B](B-juridico.md)).

| Prazo desde a ciência | Ação | Quem |
|---|---|---|
| ≤ 1 h | Conter: revogar acessos (R10); isolar o host (tirar da Tailscale; snapshot com `oci bv boot-volume-backup create --boot-volume-id <OCID>`); preservar evidência (exportar Loki e `audit_log` do intervalo) | Fundador |
| ≤ 24 h | Escopo: operadoras, número de titulares, categorias (localização, cadastro, credencial), período. Aviso por escrito a cada operadora afetada com relatório preliminar ([08](../spec/08-identidade-e-seguranca.md) [PREMISSA]; prazo final no DPA) | Fundador |
| ≤ 3 dias úteis | A controladora comunica a ANPD e os titulares quando o incidente puder causar risco ou dano relevante (Res. CD/ANPD 15/2024 [VALIDAR com advogado — DEC-08]); a Versix entrega o relatório técnico. Na finalidade em que a Versix é controladora (SVA), ela mesma comunica | Operadora; Versix |
| ≤ 5 dias úteis | Postmortem (§6) com ações corretivas e prazos | Fundador |
| Sempre | Registro do incidente guardado por 5 anos, mesmo sem comunicação à ANPD [VALIDAR — DEC-08] | Fundador |

Relatório técnico para a controladora: natureza dos dados; titulares afetados (número e categorias); medidas de segurança existentes; riscos e possíveis impactos; motivo de eventual demora; medidas de contenção e mitigação; contato do encarregado (`privacidade@<domínio>`) [VALIDAR conteúdo exigido pela Res. 15/2024 — DEC-08].

## 3. Checklist de go-live do Piloto Zero (G0, 31/10/2026)

Critérios G0-1 a G0-9: [02 §2.5](../spec/02-escopo-e-fases.md). Evidências em `docs/runbooks/gates/G0.md`.

- [ ] VM primária pelo `provision.sh`; CT-OPS-001, CT-OPS-002 e CT-OPS-023 (região brasileira) verdes.
- [ ] `gps.`, `api.` e `app.` com TTL 60 s, sem proxy, no `ip-svc`; TLS válido em `api.` e `app.`.
- [ ] Deploy por tag com 1 rollback automático provado (CT-OPS-006) e migration barrada pelo verificador (CT-OPS-007).
- [ ] WAL arquivando há ≥ 48 h sem falha; 2 bases noturnas seguidas; cópia R2 em dia (CT-OPS-008).
- [ ] Restore ensaiado (G0-7, CT-OPS-009): ≤ 2 h, perda ≤ 5 min, relatório em `docs/runbooks/restore/`.
- [ ] Chave do WAL-G e chave age do fundador em 2 cópias offline, testadas (decifrar `prod.env.sops` num notebook limpo).
- [ ] UptimeRobot sondando `gps.` (TCP) e `api.` (HTTPS) a cada 5 min; Pushover de emergência testado às 03:00 BRT e reconhecido.
- [ ] Regras do F0 ([13 §12](../spec/13-infra-e-operacao.md)) disparadas uma vez cada em teste; Sentry com erro de teste sem PII (CT-OPS-016).
- [ ] G0-1, G0-2 e G0-5 pelas consultas da T-015; G0-6 verde no pipeline implantado.
- [ ] Rollback de SMS em 1 veículo (G0-8); termos assinados (G0-9).
- [ ] §1 entregue à Lider na versão F0: sem bloqueio pela plataforma, contingência por SMS como hoje.
- [ ] Contatos de incidente (fundador, `operator_admin` e plantonista da Lider) testados por WhatsApp.

## 4. Checklist operacional de onboarding de operadora

Plano de 14 dias: [11](../spec/11-onboarding-e-migracao.md). Aqui, só o que a operação exige antes do 1º veículo real.

- [ ] Contatos de incidente da operadora (admin, plantonista, telefone, WhatsApp) na lista de transmissão de incidentes da Versix.
- [ ] Plantonista treinado (1 h) com o §1 e ensaio de localização por SMS feito.
- [ ] Lista de contingência impressa e guardada; cartão de SMS com a senha em poder do `operator_admin`.
- [ ] Usuário próprio do plantonista no portal emnify/Meta Telecom.
- [ ] F1: faixas de saída da emnify/Meta Telecom na allowlist da 5023 ([13 §2.1](../spec/13-infra-e-operacao.md)) [VALIDAR — DEC-01].
- [ ] Capacidade: veículos atuais + previstos dentro da coluna de [13 §17](../spec/13-infra-e-operacao.md); disco projetado < 70%.
- [ ] Endereço da status page e telefone de plantão da Versix entregues.
- [ ] DPA assinado com a lista de suboperadores de [13 §15](../spec/13-infra-e-operacao.md).
- [ ] Primeira onda acompanhada no painel `/migracao` ([10](../spec/10-apps-e-ux.md) C15), sem AL-10 durante a onda.

## 5. Requisição de autoridade

Base legal: [Anexo B](B-juridico.md). Passos técnicos: [08 §11](../spec/08-identidade-e-seguranca.md). Prazo: o do documento; sem prazo, ≤ 10 dias úteis [PREMISSA].

1. **Registrar.** Abra um atendimento (`ticket`) com assunto "Requisição de autoridade" e anexe o documento: órgão, número, data, prazo e pedido.
2. **Conferir autenticidade.** Ligue para o órgão pelo telefone do site oficial (não o do documento) e confirme número e signatário.
3. **Classificar** [VALIDAR — DEC-08]:
   - dados cadastrais (nome, CPF, endereço) → autoridade com competência legal pode requisitar sem ordem judicial;
   - registros de acesso (IP, porta, data e hora; `access_log`) → só com ordem judicial;
   - histórico de localização, alertas e comandos → ordem judicial ou autorização escrita do titular vítima.
4. **Quem responde.** A operadora (controladora), pelo `operator_admin`. Pedido endereçado à Versix: repasse à operadora em ≤ 24 h, salvo ordem de sigilo que proíba [VALIDAR — DEC-08]; a Versix responde direto só o que a ordem exigir dela.
5. **Congelar.** O `operator_admin` cria o `legal_hold` com `authorityRef` (ex.: `Ofício 123/2026 — 1º DP`) no veículo e no período pedidos.
6. **Gerar.** Pacote de evidências só com o escopo pedido (veículo, período, tipos); anote o SHA-256 do ZIP.
7. **Entregar** por canal oficial (e-mail institucional do órgão, sistema do tribunal ou mídia entregue em mãos), citando o SHA-256 no ofício de resposta. O download no console expira em 7 dias.
8. **Registrar** no atendimento: cópia da resposta, data e quem entregou. O `audit_log` registra a exportação sozinho.
9. **Urgência** (roubo em andamento, risco à vida): o caminho mais rápido é o titular vítima compartilhar a localização ao vivo com a polícia por link temporário; a central orienta o titular.
10. **Encerrar.** Libere o `legal_hold` só quando o procedimento terminar ou o prazo informado acabar.

## 6. Modelo de postmortem

Arquivo `docs/runbooks/postmortems/AAAA-MM-DD-<slug>.md`. Sem culpados: o foco é sistema e processo.

```markdown
# Postmortem — <título curto>

| Campo | Valor |
|---|---|
| SEV | SEV1 / SEV2 |
| Início / detecção / mitigação / fim (UTC) | 2026-12-12T05:10Z / … / … / … |
| Duração do impacto | … min |
| Minutos ruins consumidos | … de 216 no mês |
| Operadoras e veículos afetados | … |
| Alertas atrasados (> 120 s) / não entregues | … / … |
| Comandos afetados (UNKNOWN, FAILED) | … |
| Dado pessoal envolvido? | Não / Sim → Anexo C R11 |

## Resumo (3 linhas)
## Linha do tempo (UTC)
## Detecção: como soubemos e quanto tempo levou
## Causa raiz (5 porquês)
## O que funcionou e o que falhou
## Ações do agente SRE (de `ops.audit_log`)
## Comunicação feita (status page, operadoras, horários)
## Ações corretivas
| Ação | Tarefa (T-NNN) | Dono | Prazo |
|---|---|---|---|
## Lições
```

## 7. Rotina do fundador

**Semanal** (segunda, 09:00 BRT, 30 min):

| Item | Onde | OK quando |
|---|---|---|
| SLO | Painel "SLO" | Minutos ruins da semana ≤ 50 (ritmo dos 216/mês) |
| Incidentes | Gateway e `docs/runbooks/postmortems/` | Postmortems e ações corretivas dentro do prazo |
| Backups | `wal-g backup-list`; painel | 7 bases diárias; cópia R2 < 26 h; arquivamento sem falha |
| Recursos | Painéis "Host e contêineres" e "Banco" | Disco < 70%, RAM < 80%, CPU < 70% ([03 §14](../spec/03-arquitetura.md)) |
| Atualizações de segurança | `apt list --upgradable`; `/var/run/reboot-required`; Dependabot; gitleaks | Reboot pendente agendado em janela anunciada (48 h); CVE crítica em imagem base vira tarefa |
| Quarentena | `opsql "SELECT * FROM ops.inbox_stats();"` | Causa conhecida para toda linha `quarantined` |

**Mensal** (1º dia útil, ~2 h):

| Item | Onde | OK quando |
|---|---|---|
| SLO e créditos | Relatório de `ops.slo.monthly` | Publicado na status page e enviado às operadoras até o dia 5 |
| Restore | `docs/runbooks/restore/` | Ensaio do mês verde (AL-14 sem disparo) |
| Custos | Billing da OCI (~R$ 0), R2, API Claude; REQ-NEG-003 | Infra ≤ 10% da receita |
| Decisões | [15](../spec/15-decisoes-riscos-premissas.md) | Toda DEC aberta com dono e prazo; vencidas resolvidas ou reprogramadas |
| Acessos | Tailscale, GitHub, OCI, Cloudflare, grants de suporte ativos, destinatários do `.sops.yaml` | Só quem precisa |
| Versões | Postgres 17.x, Traccar (troca de versão refaz a homologação), Caddy, Node 24 | Patch aplicado ou tarefa aberta |
| Paging | Teste de emergência do Pushover | Reconhecido em ≤ 5 min |
| Capacidade | [13 §17](../spec/13-infra-e-operacao.md) | Próximo gatilho a ≥ 2 meses |

**Trimestral:** ensaio de failover (CT-OPS-011). **Semestral:** ensaio de contingência com o plantonista de cada operadora (CT-OPS-024). **Anual:** rotação de `SECRETS_MASTER_KEYS` ([08 §8](../spec/08-identidade-e-seguranca.md)) e revisão deste anexo.
