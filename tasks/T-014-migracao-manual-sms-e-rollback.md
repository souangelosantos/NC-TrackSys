# T-014 — Migração manual por SMS, rollback e `pilot provision`

| Campo | Valor |
|---|---|
| Fase | F0 (S3–S4: 1º veículo e rollback em 22/10/2026; demais até 29/10/2026 12:00 BRT) |
| Requisitos | REQ-ONB-008, REQ-ONB-009, REQ-ONB-015 (modelos e renderização; a pré-checagem de onda é F1), REQ-ONB-016 (domínio e plano B no piloto); itens G0-8 e G0-9 de REQ-NEG-010; provisionamento no Traccar pelo subcomando `pilot provision` (sem REQ próprio: dono fixado em [02 §2.3](../docs/spec/02-escopo-e-fases.md), "Donos de fronteira") [ADOTADO NA v2.0] |
| Invariantes | INV-03 (`domain_support` desconhecido não vira "sim"; contato ausente não vira "migrado"), INV-06 (a 1ª posição pertence ao vínculo vigente), INV-11 (agente não envia SMS nem comando), INV-12 (horários em UTC) |
| Risco de revisão | N1 |
| Depende de | T-005, DEC-02, DEC-04. Usa artefatos já entregues: T-002 (`fixtures/j16/sms/templates.json`, perfil J16, alvo de rollback em `lider.md`), T-007 (API de rastreadores e tela C05; `provisioning` derivado de `traccar_device_id`), T-004 (imagem `tracksys-app` e variáveis `TRACCAR_API_*` do `worker`), T-013 (sonda TCP de `gps.`) |
| Estimativa | 3 sessões de agente (14a modelos de SMS e lógica pura; 14b CLI do piloto, registro no `G0.md` e runbook; 14c `pilot provision`) + execução do fundador com a Lider (22/10: ~3 h; 28–29/10: ~1 h por veículo) |
| Bloqueado por decisão | DEC-02 (padrão seguro: modelo `draft` ou `domain_support ≠ "yes"` → nenhum SMS a veículo real; o software fica pronto e é ensaiado no J16 de bancada). DEC-04 (o `gps.` definitivo existe antes do 1º SMS a veículo real; com domínio provisório o preflight recusa) |
| Tipo | **Mista:** o agente entrega modelos, CLI, testes e runbook; o fundador e a Lider executam os SMS (agente sem acesso ao portal emnify nem credencial de produção, REQ-QLD-016, INV-11) |

## Objetivo

Levar 5 a 10 rastreadores J16 reais do servidor da SmartGPS para `gps.<TRACKSYS_DOMAIN>` sem visita ao veículo, um por vez e com rede de segurança: pré-checagem que **barra** o SMS sem termo, vínculo, provisionamento, modelo validado ou domínio no ar; acompanhamento do 1º contato em até 10 min; rollback por SMS quando não houver contato; e registro de cada passo em `docs/runbooks/gates/G0.md`. O rollback é provado em 1 veículo da frota da Lider em 22/10/2026 (G0-8) antes dos demais; a janela de 48 h do G0 exige os veículos transmitindo até 29/10/2026 12:00 BRT.

## Contexto obrigatório

- [11 §4.6, §5, §6, §7 passos 1–8](../docs/spec/11-onboarding-e-migracao.md): procedimento do piloto, modelos de SMS, domínio e plano B, cronograma da Lider.
- [02 §2.1, §2.2, §2.4, §2.5 (G0-8, G0-9)](../docs/spec/02-escopo-e-fases.md): piloto e bloqueio, prazo duro, plano de corte.
- [Anexo C §1 e §3](../docs/anexos/C-operacional.md): runbook do plantonista (versão F0) e checklist de go-live.
- [02 §2.3](../docs/spec/02-escopo-e-fases.md) ("Donos de fronteira": provisionamento no Traccar), [05 §6](../docs/spec/05-ingestao-e-telemetria.md) (`device.traccar_device_id` nulo → quarentena `device_identity_mismatch`) e [04 §3](../docs/spec/04-dominio-e-dados.md) (`app.device`).

## Escopo — fazer

**Agente:**
1. Modelos de SMS versionados e renderização segura (seção 1).
2. Lógica pura do piloto: decisão de 1º contato, rollback e formatação (seção 2).
3. Módulo de leitura e escrita das seções do piloto no `G0.md` (seção 3).
4. CLI `pnpm pilot` com `preflight`, `migrate`, `rollback`, `status` e `provision` (seções 4 e 4.1).
5. `provisionDevice` no `worker` (seção 4.1): cria o rastreador pela API do Traccar e grava `device.traccar_device_id` como `tracksys_app` com contexto da operadora; o job automático do F1 (T-024) reutiliza a mesma função.
6. Runbook `docs/runbooks/onboarding/migracao-piloto.md` (com a seção "Provisionar à mão (demonstração de 20/10)") e front matter de `docs/runbooks/onboarding/lider.md` (seção 5).
7. Testes de aceite em `tests/acceptance/T-014/`.

**Fundador e Lider (com o runbook, seção 6):** termos, cadastro, ensaio na bancada, veículo de 22/10 com rollback, demais veículos até 29/10 12:00 BRT, acompanhamento de 48 h.

## Fora do escopo

- Tabelas de onda, importador, SMS pela API emnify, rollback automático, avisos M1–M4: F1 (REQ-ONB-002 a REQ-ONB-014).
- Cadastro de cliente, veículo, rastreador e vínculo (T-007). Job automático de provisionamento no `worker` (`provisioning` `pending → done` sem intervenção) e estado `failed`: F1, com o importador (T-024).
- Qualquer escrita no banco do Traccar (proibida, `AGENTS.md`): só a API REST dele.
- Convite dos titulares para o app (T-007/T-009) e texto do termo de participação ([Anexo B](../docs/anexos/B-juridico.md)).
- Qualquer comando físico pela plataforma (bloqueio só após o G-CMD, REQ-NEG-011).

## Arquivos a criar/alterar

```
packages/domain/src/onboarding/sms-templates.ts
packages/domain/src/onboarding/pilot.ts
packages/domain/src/gates/g0-markdown.ts          (seções do piloto; a T-015 acrescenta as suas)
packages/domain/src/index.ts                      (alterar: exportar os módulos)
infra/scripts/pilot/pilot.ts                      (CLI; roda com tsx)
infra/scripts/pilot/api-client.ts                 (fetch + Zod; token só em memória)
infra/scripts/pilot/probes.ts                     (DNS e TCP com node:dns e node:net)
apps/worker/src/fleet/provision-device.ts         (provisionDevice: API do Traccar + UPDATE como tracksys_app)
apps/worker/src/cli/pilot-provision.ts            (entrada do subcomando; empacotada na imagem tracksys-app)
packages/testkit/src/fakes/traccar.ts             (alterar, ou criar se a T-011 ainda não entrou: GET/POST /api/devices)
package.json                                      (alterar: script "pilot": "tsx infra/scripts/pilot/pilot.ts")
docs/runbooks/onboarding/migracao-piloto.md
docs/runbooks/onboarding/lider.md                 (alterar: front matter no topo; conteúdo da T-002 preservado)
docs/runbooks/gates/G0.md                         (criar as 2 seções se não existirem; nada é apagado)
tests/acceptance/T-014/{sms-templates,pilot-logic,preflight,g0-log,first-contact,provision}.test.ts
tests/acceptance/T-014/fixtures/{G0.md,lider.md,templates-teste.json}
```

## Especificação detalhada

### (1) Modelos de SMS — `sms-templates.ts`

- `SMS_TEMPLATES: Readonly<Record<string, Readonly<Record<SmsKey, SmsTemplate>>>>`, com a chave `'j16/v1'` igual, campo a campo, a `packages/testkit/fixtures/j16/sms/templates.json` da T-002 (`SmsKey` = `query_server`, `query_params`, `set_server_domain`, `set_server_ip`, `rollback`, `position`, `reset`; `SmsTemplate = {text, status: 'draft' | 'validated', expectedReply, evidenceRef}`). `packages/domain` não lê arquivo: o teste garante a igualdade.
- `renderSms(ref, key, vars: {host?, port?, rollbackHost?, rollbackPort?}): {text, septets}`. **Não existe parâmetro de senha**: `{password}` é sempre renderizado como `{senha}` literal (modo manual de [11 §5](../docs/spec/11-onboarding-e-migracao.md) item 5); quem envia digita a senha no portal.
- Erros (`SmsTemplateError` com `code`): `SMS_TEMPLATE_NOT_FOUND`; `SMS_TEMPLATE_NOT_VALIDATED` (status `draft`: proibido no piloto, REQ-ONB-015); `SMS_VAR_MISSING`; `SMS_HOST_TOO_LONG` (host com mais de 60 caracteres); `SMS_NOT_GSM7` (caractere fora do alfabeto básico GSM 03.38 e da extensão); `SMS_TOO_LONG` (mais de 160 septetos; caractere da extensão `^{}\[~]|€` conta 2).
- `rollback` usa `{rollbackHost}`/`{rollbackPort}` tal como o S11 validou com o alvo real da SmartGPS [VALIDAR — DEC-02].

### (2) Lógica do piloto — `pilot.ts`

| Função | Regra |
|---|---|
| `maskImei(imei)` | `'***' + últimos 4` (ex.: `***0017`); IMEI fora de `^[0-9]{15}$` → erro |
| `decideFirstContact({smsSentAt, lastContactAt, now})` | `lastContactAt ≥ smsSentAt` e `lastContactAt − smsSentAt ≤ 600 s` → `{status: 'migrated', firstContactAt, elapsedS}`; senão, `now − smsSentAt < 600 s` → `{status: 'waiting', remainingS}`; senão `{status: 'no_contact', lateContactAt?}` (contato depois de 10 min não muda o resultado). `lastContactAt` nulo ou anterior ao SMS nunca conta (INV-03) |
| `evaluateRollback({rollbackSmsAt, confirmedAt, result})` | `result = 'back_on_source'` e `confirmedAt − rollbackSmsAt ≤ 600 s` → `{ok: true, elapsedS}`; senão `{ok: false, elapsedS, reason: 'late' \| 'not_back'}` |
| `formatElapsed(s)` | `200` → `3 min 20 s`; `45` → `45 s`; `600` → `10 min`; inteiro ≥ 0 |
| `toRfc3339Utc(date)` | `YYYY-MM-DDTHH:MM:SSZ` (sem milissegundos) |

### (3) Seções do `G0.md` — `g0-markdown.ts`

Funções puras sobre o texto do arquivo: `ensureSection(md, heading, header)`, `parseTable(md, heading)`, `appendRow(md, heading, cells)`, `replaceRow(md, heading, match, cells)`, `parsePilotRows(md)`, `parseTerms(md)`. Conteúdo fora da seção alterada fica idêntico, byte a byte. Seções exatas (a T-015 as lê):

```markdown
## Migração do piloto

| Veículo | Tipo | SMS (UTC) | 1º contato ou confirmação (UTC) | Resultado | Duração |
|---|---|---|---|---|---|
| ***0017 | migrar | 2026-10-22T13:00:00Z | 2026-10-22T13:03:20Z | migrado | 3 min 20 s |
| ***0017 | rollback | 2026-10-22T17:00:00Z | 2026-10-22T17:06:00Z | de volta no tracker-net | 6 min |

## Termos de participação (G0-9)

| Titular | Veículos | Assinado em (UTC) | Sem bloqueio remoto no piloto | Guarda do arquivo |
|---|---|---|---|---|
| T01 | ***0017 | 2026-10-20T14:00:00Z | sim | cofre do fundador: termo-T01.pdf |
```

`Tipo` ∈ `migrar`, `rollback`; `Resultado` ∈ `migrado`, `sem contato`, `aguardando`, `de volta no tracker-net`, `não voltou`; `Duração` = `formatElapsed` ou `—`. Titular por código (`T01`…`T10`) e veículo por IMEI mascarado: placa, nome e CPF ficam fora do repositório (lista de correspondência no cofre do fundador).

### (4) CLI — `pnpm pilot <comando>`

Ambiente (Zod): `TRACKSYS_API_URL` (`https://api.<domínio>`), `TRACKSYS_API_TOKEN` opcional. Sem token, pede e-mail, senha (sem eco) e, se o login exigir, o código TOTP, usando `POST /api/v1/auth/sign-in/email` e `POST /api/v1/auth/two-factor/verify-totp` (T-006); o token do cabeçalho `set-auth-token` fica só em memória. Nunca imprime token, senha, IMEI completo nem coordenada. Usuário: `operator_admin` ou `operator_agent` da Lider (`device.read`).

Dados lidos: `GET /api/v1/devices/{deviceId}` (`imeiLast4`, `capabilityProfileId`, `provisioning`, `lastContactAt`, `currentAssignment`) e `GET /api/v1/capability-profiles` (`capabilities.domain_support`) da T-007 [alinhar com T-007: formato da coleção]. Configuração: front matter de `docs/runbooks/onboarding/lider.md` (seção 5).

**`pilot preflight --device <uuid>`** — imprime `OK <checagem>` ou `FALHOU <checagem>: <motivo>` para cada item, nesta ordem, e sai 0 só se todos passarem:

| # | Checagem | Falha quando |
|---|---|---|
| 1 | `termo` | O IMEI mascarado não está em `## Termos de participação (G0-9)` com `Assinado em` ≤ agora |
| 2 | `vinculo` | `currentAssignment` nulo |
| 3 | `provisionamento` | `provisioning ≠ 'done'` |
| 4 | `contato-atual` | `lastContactAt` ≥ agora − 10 min ("já comunica com a TrackSys: nada a migrar") |
| 5 | `modelos` | `set_server_domain` (ou `set_server_ip` no plano B) ou `rollback` de `smsTemplatesRef` sem `validated` |
| 6 | `dominio` | `targetHost` é domínio e `domain_support` ≠ `"yes"` (`"no"`, `"unknown"` ou ausente; INV-03) → "use o plano B (IP) após revisar o ADR-005"; `targetHost` é IPv4 e `adr005RevisedForIp ≠ true` |
| 7 | `dec-04` | `targetHost` é domínio e (`dec04Resolved ≠ true` ou `targetHost ≠ 'gps.' + <domínio de TRACKSYS_API_URL>`) |
| 8 | `dns` | Algum registro A de `targetHost` ≠ `serviceIp` ou TTL > 60 (pula se IP) |
| 9 | `tcp` | Conexão a `targetHost:targetPort` não abre em 5 s |
| 10 | `alvo-rollback` | `rollbackHost` ou `rollbackPort` vazio ou com `<` |

Com tudo `OK`, imprime os 2 textos para copiar no portal (migração e rollback), já renderizados, com `{senha}` literal. Com qualquer `FALHOU`, **não imprime texto de SMS** (CT-ONB-008). Exemplo de saída (texto dos modelos ilustrativo; o real vem da T-002):

```text
Rastreador ***0017 (perfil J16 em `draft`: bloqueio indisponível, rastreamento ok) — alvo gps.tracksys.example:5023
OK termo · OK vinculo · OK provisionamento · OK contato-atual · OK modelos
OK dominio · OK dec-04 · OK dns (203.0.113.10, TTL 60) · OK tcp (0,21 s) · OK alvo-rollback
SMS de migração (portal emnify/Meta Telecom, linha do chip deste rastreador):
  SERVER,{senha},1,gps.tracksys.example,5023,0#
SMS de rollback (use só se não houver contato em 10 min):
  SERVER,{senha},0,198.51.100.7,7700,0#
```

Esquema do front matter (Zod, em `pilot.ts` da CLI): `targetHost` hostname ou IPv4; `targetPort` e `rollbackPort` inteiros 1–65535; `serviceIp` IPv4; `rollbackHost` hostname ou IPv4; `smsTemplatesRef` `^[a-z0-9]+/v[0-9]+$`; `dec04Resolved` e `adr005RevisedForIp` `true|false`. Campo inválido → `FALHOU config: <campo>` e saída 1, antes de qualquer chamada à API.

**`pilot migrate --device <uuid> [--sms-at <RFC 3339>]`** — roda o preflight (falha → sai 1); pergunta a hora do envio (Enter = agora, em UTC); grava a linha `migrar … | aguardando | —`; consulta `devices.get` a cada 10 s até `decideFirstContact` sair de `waiting`; troca a linha por `migrado` + duração, ou por `sem contato` e imprime "SEM CONTATO EM 10 MIN: envie agora o SMS de rollback" com o texto. Interrupção (Ctrl+C) deixa a linha `aguardando`; rodar de novo com o mesmo `--sms-at` retoma sem duplicar.

**`pilot rollback --device <uuid> --sms-at <RFC 3339> [--result back_on_source|not_back --confirmed-at <RFC 3339>]`** — sem `--result`, grava `rollback … | aguardando`; com `--result`, completa a mesma linha e imprime "rollback em 6 min: dentro do limite de 10 min (G0-8)" ou "fora do limite" / "não voltou: abrir chamado para o instalador".

**`pilot status`** — para cada veículo com linha `migrado` mais recente que qualquer `rollback`, mostra `***0017  migrado  último contato há 40 s` (transmitindo = contato há ≤ 10 min) e o total: "N veículos transmitindo (G0-1 exige ≥ 5)".

### (4.1) `pilot provision` — provisionamento no Traccar

`pnpm pilot provision --operator <uuid> --device <uuid> [--dry-run]` chama `provisionDevice` de `apps/worker/src/fleet/provision-device.ts`. Na VM, o fundador roda o mesmo código pela imagem já publicada: `dc run --rm --no-deps worker node dist/cli/pilot-provision.js --operator <uuid> --device <uuid>` (ambiente do `worker`: `DATABASE_URL_APP`, `TRACCAR_API_URL`, `TRACCAR_API_USER`, `TRACCAR_API_PASSWORD`, `EXTERNAL_EFFECTS=on`). O agente nunca roda em produção (REQ-QLD-016).

1. **Ambiente (Zod):** `DATABASE_URL_APP` obrigatório e com usuário `tracksys_app` (outro usuário, inclusive `tracksys_owner` ou superusuário → sai 78 com "papel recusado", antes de qualquer chamada); `DATABASE_URL`, `DATABASE_URL_ADMIN` e `MIGRATE_DATABASE_URL` são ignorados mesmo se presentes. `EXTERNAL_EFFECTS=off` → sai 1 com `EXTERNAL_EFFECTS_DISABLED` (ensaio de restore, T-013).
2. **Leitura:** `withContext(pool, { scope: 'operator', operatorId })` e `SELECT id, imei, model, status, traccar_device_id FROM app.device WHERE id = $1 FOR UPDATE`. Sem linha (inexistente ou de outra operadora, pela RLS) → sai 1 "rastreador não encontrado nesta operadora", 0 chamadas ao Traccar. `status = 'retired'` → sai 1.
3. **Já provisionado:** `traccar_device_id` preenchido → `GET {TRACCAR_API_URL}/api/devices?id=<id>`; `uniqueId` igual ao IMEI → `OK já provisionado ***0017 → traccar <id>` e sai 0; diferente ou ausente → sai 1 `traccar_id_mismatch`, sem alterar nada.
4. **Criação idempotente:** `GET /api/devices?uniqueId=<imei>` (Basic com `TRACCAR_API_USER`/`TRACCAR_API_PASSWORD`, tempo limite 10 s); existe → reutiliza o `id`; senão `POST /api/devices` com `{"name": "<model> ***<4 últimos>", "uniqueId": "<imei>", "category": "car"}` e lê o `id` da resposta [VALIDAR — versão do Traccar fixada na T-003: filtro `uniqueId` e campos obrigatórios].
5. **Gravação:** na mesma transação, `UPDATE app.device SET traccar_device_id = $id, updated_at = now() WHERE id = $device AND traccar_device_id IS NULL`; 1 linha → COMMIT e `OK provisionado ***0017 → traccar <id>`; `provisioning` passa a `done` (derivado pela T-007). Erro do Traccar (4xx/5xx/tempo) → ROLLBACK, `traccar_device_id` continua NULL, sai 1 com o status HTTP.
6. `--dry-run`: faz só os `GET` e imprime o que faria; nenhum `POST` nem `UPDATE`.
7. Saída e log nunca têm IMEI completo, senha do Traccar nem cabeçalho `Authorization`.

**Demonstração de 20/10 (antes desta tarefa entrar):** o fundador faz o mesmo passo à mão com o J16 de bancada — cria o dispositivo pela interface do Traccar e grava o id com SQL como `tracksys_app` com contexto da operadora (igual ao corte 5 de [02 §2.4](../docs/spec/02-escopo-e-fases.md); nunca como `tracksys_owner`), seguindo a seção "Provisionar à mão" do runbook.

### (5) Runbook e configuração

`docs/runbooks/onboarding/lider.md` ganha, no topo, front matter plano (`chave: valor`, sem aninhamento; parser próprio, sem dependência nova): `operator: lider`, `targetHost`, `targetPort` (`5023` [VALIDAR — DEC-02]), `serviceIp` (`ip-svc` da T-003), `rollbackHost`, `rollbackPort` (resultado do `query_server` da T-002), `smsTemplatesRef: j16/v1`, `dec04Resolved: false`, `adr005RevisedForIp: false`. Sem senha.

`docs/runbooks/onboarding/migracao-piloto.md`: os passos da seção 6 com comandos exatos, a regra "um veículo por vez", o que fazer em cada resultado e o modelo de mensagem para a Lider confirmar o rollback no tracker-net.

### (6) Execução (fundador e Lider)

| Quando | Passo | Pronto quando |
|---|---|---|
| até 20/10 | Escolher 5–10 veículos (frota, funcionários, voluntários); termo do [Anexo B](../docs/anexos/B-juridico.md) assinado por titular, informando se o veículo fica sem bloqueio remoto (sim, salvo servidor secundário provado na T-002 [VALIDAR — DEC-02]); linha em `## Termos` | Termos = titulares |
| até 20/10 | Cadastro no console (C03–C06): cliente, veículo, rastreador, chip e vínculo com a resposta do relé/ponto de corte; `pilot provision` na VM para cada rastreador (até a T-014 entrar, o passo à mão do runbook) → `provisioning = done` | `pilot preflight` passa nos itens 2–3 |
| antes do 1º SMS real | DEC-02 e DEC-04 resolvidas; `gps.` definitivo com TTL 60 s, sem proxy, no `ip-svc`; sonda TCP verde (T-013); `lider.md` com `dec04Resolved: true`; runbook do plantonista F0 ([Anexo C §1](../docs/anexos/C-operacional.md): sem bloqueio pela plataforma, contingência por SMS como hoje) entregue à Lider | `pilot preflight` 100% `OK` |
| 21/10 (ensaio) | J16 de bancada: `pilot migrate` para o domínio definitivo; rollback com alvo = `ip-sby` e `sudo timeout 900 nc -lk 5023 >/dev/null` na `tracksys-s` (vê-se a sessão em `ss -Htn state established '( sport = :5023 )'`); depois migrar de novo | Ensaio anotado no PR (fora da tabela do G0) |
| 22/10, 13:00–17:00 BRT | 1 veículo da frota da Lider: `pilot migrate` → `migrado` → SMS de rollback pelo portal → `pilot rollback` → a Lider confirma no tracker-net → `--result` → `pilot migrate` de novo no mesmo dia | 3 linhas no `G0.md`; rollback ≤ 10 min (G0-8) |
| 28/10 a 29/10 12:00 BRT | Demais veículos, um por vez, 09:00–16:00 BRT; `sem contato` → rollback imediato e nova tentativa noutro horário | `pilot status` ≥ 5 transmitindo às 12:00 BRT de 29/10 |
| 29/10 12:00 → 31/10 12:00 BRT | Acompanhar com `pilot status` 3 vezes ao dia; queda de contato > 10 min → causa com a Lider/titular, anotada para `## Lacunas explicadas` (T-015) | Janela de 48 h do G0 |

Menos de 5 transmitindo em 29/10 12:00 BRT → o G0 passa para o fim da janela de 48 h, no máximo 07/11/2026 (REQ-NEG-017); registrar em `## Cortes`. Pedido do titular para voltar ao tracker-net a qualquer momento → `pilot rollback`, sem discussão.

Resposta por resultado:

| Resultado | Ação imediata | Depois |
|---|---|---|
| `migrado` | Avisar a Lider; o veículo deixa de atualizar no app antigo | Conferir em C05 o 1º ponto no dia seguinte |
| `sem contato` | SMS de rollback no mesmo minuto; `pilot rollback --sms-at` | Lider confere no tracker-net; nova tentativa só noutro horário |
| `de volta no tracker-net` | Registrar `--result back_on_source` | Investigar a causa (cobertura, senha, IMEI) antes de repetir |
| `não voltou` (ou 30 min sem resposta da Lider) | Registrar `--result not_back`; avisar o titular pela Lider | Visita do instalador; veículo fica fora do piloto |
| Resposta de senha errada no portal | Não repetir; nada a registrar como migração | Lider obtém a senha com o instalador ou a SmartGPS |

## Testes de aceite (congelados)

`tests/acceptance/T-014/` (rodam no CI; datas fixas em UTC; nenhum dado real):

- `sms-templates.test.ts` (CT-ONB-015 na parte F0) — Dado `SMS_TEMPLATES['j16/v1']` e `templates.json` da T-002, Então chaves, `text` e `status` são iguais. Dado `fixtures/templates-teste.json` carregado como `teste/v1` com `set_server_domain = "SERVER,{password},1,{host},{port},0#"` `validated`, Quando `renderSms('teste/v1', 'set_server_domain', {host: 'gps.tracksys.com.br', port: 5023})`, Então `text = "SERVER,{senha},1,gps.tracksys.com.br,5023,0#"` e `septets ≤ 160`; com host de 40 caracteres, Então renderiza; com host de 61 caracteres, Então `SMS_HOST_TOO_LONG`; com host `gps.ação.com.br`, Então `SMS_NOT_GSM7`; com o modelo `draft`, Então `SMS_TEMPLATE_NOT_VALIDATED`; sem `port`, Então `SMS_VAR_MISSING`. Nenhum teste passa senha.
- `pilot-logic.test.ts` (CT-ONB-008 e CT-ONB-009 na parte de decisão) — Dado SMS às `13:00:00Z` e `lastContactAt = 13:03:20Z`, Quando `now = 13:03:25Z`, Então `migrated` com `elapsedS = 200` e `formatElapsed = "3 min 20 s"`. Dado `lastContactAt = 12:59:59Z` (contato anterior ao SMS) e `now = 13:05:00Z`, Então `waiting` com `remainingS = 300`. Dado `lastContactAt` nulo e `now = 13:10:00Z`, Então `no_contact`. Dado contato às `13:11:00Z`, Então `no_contact` com `lateContactAt = 13:11:00Z`. Dado rollback às `17:00:00Z` (14:00 BRT) e confirmação `back_on_source` às `17:06:00Z`, Então `ok` com 360 s; às `17:10:01Z`, Então `ok: false`, `reason = 'late'`; `not_back`, Então `reason = 'not_back'`. `maskImei('860000000000017') = '***0017'`.
- `preflight.test.ts` (CT-ONB-008 2ª parte, CT-ONB-016 na parte do piloto) — Fake HTTP da API e sondas injetadas; `fixtures/G0.md` com `T01 | ***0017 | 2026-10-20T14:00:00Z`; `fixtures/lider.md` com `targetHost: gps.tracksys.example`, `serviceIp: 203.0.113.10`, `dec04Resolved: true`; rastreador `***0017` com vínculo, `provisioning: 'done'`, `lastContactAt: null`, perfil `domain_support: "yes"`; DNS `203.0.113.10` TTL 60; TCP abre. Quando `pilot preflight`, Então sai 0, 10 linhas `OK` e os 2 textos de SMS. Dado o rastreador `***0025` sem termo, Então sai 1, `FALHOU termo` e a saída não contém `SERVER`. Dado `provisioning: 'pending'`, Então `FALHOU provisionamento`. Dado `lastContactAt` há 2 min, Então `FALHOU contato-atual`. Dado `domain_support: "unknown"`, Então `FALHOU dominio` com "plano B". Dado TTL 300, Então `FALHOU dns`. Dado `dec04Resolved: false`, Então `FALHOU dec-04`. Em todos os casos a saída não contém o token do fake nem 15 dígitos seguidos.
- `g0-log.test.ts` — Dado `fixtures/G0.md` com a seção `## Cortes` e sem `## Migração do piloto`, Quando `appendRow` grava `***0017 | migrar | 2026-10-22T13:00:00Z | 2026-10-22T13:03:20Z | migrado | 3 min 20 s`, Então a seção é criada com o cabeçalho exato e o texto anterior fica idêntico; Quando `replaceRow` troca `aguardando` por `migrado` com o mesmo SMS, Então a seção continua com 1 linha desse SMS; `parsePilotRows` devolve `{vehicle: '***0017', kind: 'migrar', smsAt: '2026-10-22T13:00:00Z', outcomeAt: '2026-10-22T13:03:20Z', outcome: 'migrado'}`.
- `provision.test.ts` (provisionamento, 02 §2.3) — Banco local migrado, `seedVerticalSlice` (T-005) e fake de Traccar de `packages/testkit` com usuário e senha de teste. Dado R3 (Alfa, `stock`, `traccar_device_id` NULL), Quando `provisionDevice` roda com `DATABASE_URL_APP`, Então o fake recebe 1 `GET ?uniqueId=` e 1 `POST /api/devices` com `uniqueId` = IMEI de R3 e Basic correto, `app.device.traccar_device_id` = id devolvido e a saída é `OK provisionado ***0003 → traccar <id>`; 2ª execução → 0 `POST` e "já provisionado"; fake já com o `uniqueId` → 0 `POST` e o id existente gravado; `--dry-run` → 0 `POST` e coluna NULL; `POST` respondendo 500 → sai 1 e coluna NULL; R3 com `--operator` da Beta → sai 1 e 0 chamadas ao fake; `DATABASE_URL_APP` com usuário `tracksys_owner` → sai 78 e 0 chamadas; `EXTERNAL_EFFECTS=off` → sai 1 e 0 chamadas; `traccar_device_id` gravado que o fake devolve com outro `uniqueId` → sai 1 `traccar_id_mismatch`. Depois de provisionar, uma posição de R3 com `position.deviceId` = id enviada a `POST /internal/v1/traccar/positions` fica `processed` (antes: quarentena `device_identity_mismatch`). Nenhuma saída contém 15 dígitos seguidos nem a senha.
- `first-contact.test.ts` (CT-ONB-008 1ª parte, INV-06) — Dado `seedVerticalSlice` (T-005) com V1 vinculado a A1 e sem contato, Quando uma posição de V1 com `serverTime = <hoje>T13:03:20Z` é enviada a `POST /internal/v1/traccar/positions`, Então `GET /api/v1/devices/{V1}` como `agente.alfa` traz `lastContactAt = <hoje>T13:03:20Z`, a 1ª linha de `app.position` de V1 tem o `tenant_id` de A1 e `decideFirstContact` com SMS às `13:00:00Z` dá `migrated` em 200 s.

Execução (fundador; anexar ao PR e ao `G0.md`): saída do `pilot preflight` do veículo de 22/10; as 3 linhas de 22/10 (CT-ONB-009, G0-8); `dig +noall +answer gps.<domínio>` com TTL ≤ 60 e o `ip-svc` (CT-ONB-016); `pilot status` às 12:00 BRT de 29/10.

## Comandos de verificação

```bash
pnpm install
pnpm lint && pnpm typecheck
pnpm db:up && pnpm db:migrate
pnpm test:acceptance -- tests/acceptance/T-014
TRACKSYS_API_URL=https://api.tracksys.example pnpm pilot --help     # lista preflight, migrate, rollback, status, provision
pnpm verify
```

## Definição de pronto

- [ ] Testes da T-014 verdes; `pnpm verify` verde no PR.
- [ ] `lider.md` com front matter; `migracao-piloto.md` revisado pelo fundador.
- [ ] Rastreadores do piloto com `provisioning = done` pelo `pilot provision` (saída anexada ao PR, só IMEI mascarado).
- [ ] Ensaio na bancada (21/10) e veículo de 22/10 com rollback ≤ 10 min registrados (G0-8).
- [ ] ≥ 5 veículos transmitindo em 29/10/2026 12:00 BRT, ou adiamento do G0 registrado em `## Cortes`.
- [ ] PR `feat(onboarding): migração manual por SMS e rollback do piloto (T-014)` com REQ/INV/risco e revisão cruzada.

## Decisões já tomadas (não pergunte, siga)

| Dúvida provável | Resposta |
|---|---|
| O `G0.md` registra a placa ([11 §4.6](../docs/spec/11-onboarding-e-migracao.md))? | Não. O repositório é lido por agentes (REQ-QLD-016): veículo por IMEI mascarado e titular por código; a correspondência com placa e nome fica no cofre do fundador. Registrar a divergência no PR. |
| A CLI pode enviar o SMS pela API emnify? | Não. DEC-01 e o envio automático são F1. No F0 o fundador envia pelo portal; a CLI só renderiza e acompanha. |
| A senha SMS do J16 entra na CLI ou no repositório? | Nunca. O texto sai com `{senha}` literal e quem envia digita no portal ([11 §5](../docs/spec/11-onboarding-e-migracao.md) itens 4–5). |
| `domain_support` ficou `"unknown"` no spike. | Preflight falha (INV-03). Plano B por IP só com `adr005RevisedForIp: true`, depois de o fundador revisar o ADR-005 ([11 §6](../docs/spec/11-onboarding-e-migracao.md) item 4). |
| E se o J16 aceitar servidor secundário? | Só com evidência da T-002 [VALIDAR — DEC-02]: o modelo novo entra em `templates.json` como `validated` e o termo registra "não" em "sem bloqueio remoto". Sem prova, só `set_server_domain`. |
| Contato depois de 10 min conta como migrado? | Não. Fica `sem contato` (o rollback já foi pedido); o veículo é migrado de novo noutra tentativa. |
| Posso migrar vários veículos em paralelo? | Não no F0: um por vez, para o rollback caber no expediente da central. |
| Datas e horários? | UTC (RFC 3339) em arquivo e saída da CLI; BRT só como referência humana no runbook (INV-12). |
| Dependência nova para YAML, prompts ou DNS? | Nenhuma: front matter plano com parser próprio, `node:readline`, `node:dns`, `node:net`. |
| Onde roda o `pilot provision` e com que papel? | Na VM, pela imagem do `worker` (já tem o cliente do Traccar e `DATABASE_URL_APP`), como `tracksys_app` com contexto da operadora. Nunca `tracksys_owner` nem `DATABASE_URL_ADMIN`; o banco do Traccar nunca é escrito, só a API REST. [ADOTADO NA v2.0, 02 §2.3] |
| Por que não um job automático já no F0? | São 5–10 rastreadores, um por vez; o subcomando idempotente basta e não cria fila nova. O job do F1 (T-024) reutiliza `provisionDevice`. |
