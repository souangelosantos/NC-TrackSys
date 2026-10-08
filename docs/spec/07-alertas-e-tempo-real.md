# 07 — Alertas e tempo real

> **Resumo:** Fixa o catálogo de alertas do F0 e do F1 com gatilho exato, severidade e texto da notificação; o modo vigilância; o ciclo de vida dos episódios; a entrega push pelo FCM; as preferências por usuário; a fila de alertas da central; a medição de latência que alimenta o "minuto ruim"; e o contrato do tempo real por SSE. À noite o caminho crítico é rastreador → TrackSys → push no celular do cliente, porque o plantonista da operadora é reativo.
> **Fases:** F0, F1  ·  **Status:** Aprovado para execução
> **Muda em relação à v1.1:**
> - Alertas do primeiro marco definidos (a v1.1 deixava o E1 sem alertas): SOS, corte de alimentação, sem comunicação e comunicação perdida em movimento entram no F0.
> - Heurística de bloqueador de sinal (jammer) e modo vigilância com cerca âncora de 150 m.
> - WebSocket vira SSE com snapshot na reconexão e descarte por revisão (INV-04).
> - Latência medida por etapa, com p95 ≤ 30 s e "minuto ruim" acima de 120 s.

## 1. Onde fica o código

| Peça | Caminho |
|---|---|
| Catálogo, regras, episódios, vigilância, presença, textos (puro) | `packages/domain/src/alerts/{catalog,rules,episodes,watch-mode,presence,texts}.ts` |
| Avaliação (fila `alerts.evaluate`, consome `device.state.updated.v1`) e laço de silêncio | `apps/worker/src/alerts/{evaluate.consumer,silence.loop}.ts` |
| Entrega (fila `alerts.deliver`, consome `alert.opened.v1` e `alert.closed.v1`) | `apps/worker/src/alerts/{deliver.consumer,fcm.adapter}.ts` |
| Rotas de alertas, vigilância, preferências e tokens | `apps/api/src/alerts/*.controller.ts` |
| SSE | `apps/api/src/stream/{stream.controller,stream.hub}.ts` |
| Contratos | `packages/contracts/src/events/{alert-opened,alert-closed}.v1.ts`, `packages/contracts/src/sse/*.ts` |
| Fake de FCM | `packages/testkit/src/fakes/fcm.ts` |

## 2. Catálogo

| Tipo | Fase | Gatilho exato | Sev. | Fonte | Depende de hardware | Padrão | Notificação (título — corpo) |
|---|---|---|---|---|---|---|---|
| `ignition_on` | F0 | `transitions.ignition` de `false` para `true` | warning | Posição ou heartbeat | `ignition = true` | Desligado | "Ignição ligada" — "{veículo}: ignição ligada às {hora}." |
| `watch_mode_breach` | F0 | Modo vigilância ativo e (ignição `true` observada após a ativação **ou** 2 fixes válidos consecutivos a mais de `radius_m` da âncora) — §5 | critical | Posição + `watch_mode` | Não (ignição opcional) | Ligado, não desativável | "Modo vigilância: movimento" — "{veículo} saiu do local ou teve a ignição ligada às {hora}. Toque para ver no mapa." |
| `power_cut` | F0 | `alarms` contém `powerCut`; ou, com `power_cut_alarm = false` e `power_source` definido, transição `power_state` `main → battery` | critical | Posição ou evento `alarm` | `power_cut_alarm` ou `power_source` [VALIDAR — DEC-02] | Ligado | "Alimentação cortada" — "{veículo}: o rastreador perdeu a energia do veículo às {hora} e está na bateria interna." |
| `sos` | F0 | `alarms` contém `sos` | critical | Posição ou evento `alarm` | `sos = true` [VALIDAR — DEC-02] e botão instalado | Ligado, não desativável | "Pânico acionado" — "{veículo}: botão de pânico às {hora}. Toque para falar com a central." |
| `offline` | F0 | Sem contato há > 1.800 s (30 min) e sem `signal_lost_moving` aberto | warning | Laço de silêncio | Não | Ligado | "Sem comunicação" — "{veículo} não comunica desde {hora}. Última posição no app." |
| `signal_lost_moving` | F0 | `motion = 'moving'`, `ignition` diferente de `false` e sem contato há > 180 s | critical | Laço de silêncio | Não | Ligado | "Comunicação perdida em movimento" — "{veículo} parou de comunicar em movimento às {hora}. Pode ser bloqueador de sinal. Veja a última posição." |
| `low_battery` | F1 | `alarms` contém `lowBattery`, ou `batteryLevel ≤ 20` com `power_state ≠ 'main'` | warning | Posição ou heartbeat | `batteryLevel` reportado [VALIDAR — DEC-02] | Ligado | "Bateria do rastreador baixa" — "{veículo}: bateria interna em {n}% sem energia do veículo." |
| `overspeed` | F1 | 2 fixes válidos consecutivos acima do limite do usuário (padrão 110 km/h; faixa 40–200) | warning | Posição | Não | Desligado | "Excesso de velocidade" — "{veículo}: {v} km/h às {hora}, acima do limite de {limite} km/h." |
| `geofence` | F1 | 2 fixes válidos consecutivos do outro lado da borda da cerca (borda conta como dentro) | warning | Posição + `geofence` | Não | Ligado para a cerca criada | "Cerca virtual" — "{veículo} {entrou em \| saiu de} {cerca} às {hora}." |

Regras do catálogo:
1. `{veículo}` = apelido do veículo, senão a placa; `{hora}` = `HH:mm` em America/Sao_Paulo [PREMISSA: fuso único por operadora até existir campo de fuso]. Texto sem coordenadas nem endereço (aparece na tela bloqueada).
2. **Disponibilidade:** o tipo só existe para o veículo se o perfil do dispositivo primário tem a capacidade exigida igual a `true`. Capacidade `null` ou `false` → tipo indisponível ("Indisponível neste rastreador" nas preferências); alarme recebido mesmo assim fica em `position.extra` e soma `alerts_unexpected_alarm_total{alarm}`, sem abrir alerta (INV-03).
3. **Ignição desligada por padrão:** ligada, notificaria cada uso legítimo do dono; o modo vigilância cobre o carro estacionado. O app oferece ligar no primeiro acesso ([10](10-apps-e-ux.md)).
4. Avisos de encerramento (severidade `info`): "{veículo} voltou a comunicar às {hora}." (`offline`, `signal_lost_moving`) e "{veículo}: energia do veículo restabelecida às {hora}." (`power_cut`), só para quem recebeu o push de abertura.

| Severidade | Android | iOS | Console |
|---|---|---|---|
| `critical`, `warning` | Canal `alerts_high` (importância alta) | `interruption-level: time-sensitive` | Fila; `critical` no topo com som |
| `info` | Canal `alerts_info` (importância padrão) | `interruption-level: active` | — |

## 3. Avaliação

1. **Entradas:** job `alerts.evaluate` por `device.state.updated.v1` (payload lido da outbox sob o contexto RLS do job, [05 §10](05-ingestao-e-telemetria.md)); laço de silêncio a cada 15 s (§4); ações no `api` (reconhecer, desativar vigilância), que fecham episódios na própria transação.
2. **Serialização por dispositivo:** toda transação de avaliação começa com `SELECT pg_advisory_xact_lock(hashtextextended('alerts:' || $device_id, 0))`.
3. **Transições exatas:** o consumidor usa `transitions`, `location` e `previousLocation` do evento, calculados sob o lock da projeção; não guarda estado próprio. No F0–F1 só o dispositivo primário do veículo (`isPrimary = true`) gera alertas.
4. **Reordenação:** se o evento abre um episódio mas `device_state.revision` já é maior e o estado atual contradiz a condição (ex.: ignição agora `false`), o alerta é aberto e fechado na mesma transação (`closeReason = 'superseded'`) e segue a regra de entrega normal.
5. **Abertura:** `INSERT INTO app.alert (…, episode_key) … ON CONFLICT (episode_key) DO NOTHING`; se inseriu, grava `alert.opened.v1` na outbox e `pg_notify('alert_changed', '{"a":"<alertId>","o":"<operatorId>","t":"<tenantId>","v":"<vehicleId>"}')` na mesma transação. Fechamento: `UPDATE … SET ended_at`, `alert.closed.v1` e o mesmo NOTIFY.
6. **Fato antigo e modo não ao vivo (INV-05):** o episódio é registrado, mas só gera entrega se `processingMode = 'live'` e o fato tem até 60 min (`critical`) ou 10 min (demais), medido de `observedAt` (ou do limiar cruzado) até a abertura. Fora disso: `evidence.stale = true` ou `evidence.processingMode` registrado, nenhuma `alert_delivery`.

Exemplo de evento (ids fictícios); `alert.closed.v1` acrescenta `endedAt`, `closeReason` e `notifyClose`:

```json
{ "type": "alert.opened.v1", "eventId": "0192a1b2-0010-7c3d-8e4f-5a6b7c8d9e10", "occurredAt": "2026-10-21T00:14:05.210Z", "processingMode": "live",
  "operatorId": "0192a1b2-0000-7000-8000-00000000a1fa", "tenantId": "0192a1b2-0000-7000-8000-0000000000a1",
  "vehicleId": "0192a1b2-0000-7000-8000-0000000000f1", "deviceId": "0192a1b2-0000-7000-8000-0000000000d1",
  "alertId": "0192a1b2-0011-7c3d-8e4f-5a6b7c8d9e11", "alertType": "sos", "severity": "critical",
  "episodeKey": "sos:0192a1b2-0000-7000-8000-0000000000d1:1048577", "startedAt": "2026-10-21T00:14:03.000Z", "stale": false }
```

## 4. Sem comunicação e comunicação perdida em movimento

1. O laço roda a cada 15 s em um único worker (`pg_try_advisory_lock` de chave fixa) e chama `app.list_silent_devices(p_now timestamptz)`: função SECURITY DEFINER (dono `tracksys_owner`, executável por `tracksys_app`) que devolve só `device_id`, `operator_id`, `tenant_id`, `vehicle_id`, `revision`, `last_contact_at`, `motion` e `ignition` dos dispositivos com vínculo corrente e `last_contact_at < p_now − 180 s`. Sem coordenadas. Definição final em [04](04-dominio-e-dados.md).
2. Para cada candidato, transação com o contexto RLS do candidato e o lock do §3:
   - `signal_lost_moving` se `motion = 'moving'`, `ignition IS DISTINCT FROM false` e `p_now − last_contact_at > 180 s`; `started_at = last_contact_at + 180 s`.
   - `offline` se `p_now − last_contact_at > 1.800 s` e não há `signal_lost_moving` aberto; `started_at = last_contact_at + 1.800 s`.
3. Fecham com o próximo `device.state.updated.v1` que tenha `lastContact` em `changes` (`closeReason = 'contact_resumed'`).
4. **Incidente de plataforma:** nenhum `offline` ou `signal_lost_moving` novo é aberto enquanto valer qualquer condição abaixo e por mais 10 min depois dela; o fundador recebe page ([13](13-infra-e-operacao.md)). Depois, as regras voltam com `started_at = max(limiar cruzado, fim do incidente + 10 min)`.
   - (a) `GET /api/server` do Traccar falha em 2 checagens seguidas a cada 15 s [VALIDAR — DEC-02 rota];
   - (b) com ≥ 10 dispositivos com contato nas últimas 24 h, mais de 50% deles passam de 180 s sem contato dentro de 5 min;
   - (c) a ingestão não recebe nenhuma mensagem por > 120 s, tendo havido contato de ≥ 1 dispositivo nos 10 min anteriores.
5. O limiar de 180 s pressupõe intervalo de 30 s em movimento e o de 1.800 s, 300 s parado (`moving_interval_s`, `stopped_interval_s` do perfil) [VALIDAR — DEC-02]. Se o spike medir intervalo maior, o limiar em movimento passa a `max(180 s, 3 × moving_interval_s)`.

## 5. Modo vigilância (cerca âncora)

| Etapa | Regra |
|---|---|
| Ativar | `POST /api/v1/vehicles/{vehicleId}/watch-mode` com `{"radiusM": 150}` (opcional; 100–500, padrão 150). Papéis: `tenant_owner`, `tenant_member` com acesso ao veículo, `operator_admin`, `operator_agent`. Grava `audit_log` `watch_mode.activate` |
| Pré-condições (dispositivo primário) | Fix válido nas últimas 24 h, senão 409 `WATCH_MODE_NO_FIX`; `ignition` diferente de `true` e `motion` diferente de `moving`, senão 409 `WATCH_MODE_VEHICLE_ON`; já ativo → 200 com o registro existente |
| Âncora | `device_state.lat_e7`/`lon_e7` (último fix válido) gravados em `watch_mode`; resposta 201 `{watchModeId, anchor:{latitude, longitude}, radiusM, activatedAt}` |
| Violação por ignição | `state.ignition = true` com `observedAt > activated_at` (só com perfil `ignition = true`) |
| Violação por deslocamento | `location` e `previousLocation` do evento válidos, ambos com `fixTime > activated_at` e ambos a mais de `radius_m` da âncora (haversine, raio 6.371.008,8 m). Fix dentro do raio interrompe a sequência |
| Depois da violação | Modo continua ativo; 1 episódio por ativação. Para rearmar: desativar e ativar de novo |
| Desativar | `DELETE /api/v1/vehicles/{vehicleId}/watch-mode` → `deactivated_at`, fecha a violação aberta (`deactivated`), 204, `audit_log` `watch_mode.deactivate` |

Um modo ativo por veículo (índice único parcial `watch_mode (vehicle_id) WHERE deactivated_at IS NULL`, proposta para [04](04-dominio-e-dados.md)). Dois fixes e 150 m absorvem a deriva do GPS parado (tipicamente 10–50 m). Vigilância nunca dispara comando (INV-08).

## 6. Episódios

| Tipo | Abre | Fecha (`closeReason`) | Sinal repetido com episódio aberto | `episode_key` |
|---|---|---|---|---|
| `ignition_on` | Transição `false → true` | Transição `true → false` (`ignition_off`) | — | `ignition_on:{deviceId}:{revision}` |
| `watch_mode_breach` | §5 | Desativação (`deactivated`) ou reconhecimento (`acknowledged`) | Ignorado | `watch_mode_breach:{watchModeId}` |
| `power_cut` | Catálogo | Alarme `powerRestored`, ou `power_state = 'main'` observado ≥ 60 s após o último sinal (`power_restored`); perfil sem `power_source`: reconhecimento; 24 h sem sinal (`expired`) | `evidence.signalCount + 1`, sem novo push | `power_cut:{deviceId}:{revision}` |
| `sos` | Catálogo | Reconhecimento (`acknowledged`); 24 h (`expired`) | `signalCount + 1`; após reconhecer, novo sinal abre novo episódio | `sos:{deviceId}:{revision}` |
| `offline` | §4 | Contato (`contact_resumed`) | — | `offline:{deviceId}:{revision}` |
| `signal_lost_moving` | §4 | Contato (`contact_resumed`) | Impede `offline` | `signal_lost_moving:{deviceId}:{revision}` |
| `low_battery` | Catálogo | `batteryLevel ≥ 30` ou `power_state = 'main'` (`recovered`) | — | `low_battery:{deviceId}:{revision}` |
| `overspeed` | Catálogo | 2 fixes válidos consecutivos ≤ limite − 10 km/h, ignição `false` ou 10 min sem fix (`recovered`) | — | `overspeed:{deviceId}:{revision}` |
| `geofence` | Catálogo | Instantâneo: `ended_at = started_at` | — | `geofence:{geofenceId}:{revision}` |

1. `{revision}` é a do `device.state.updated.v1` que abriu, ou a de `device_state` na avaliação de silêncio: a mesma entrada gera a mesma chave (INV-01 aplicado aos alertas).
2. No máximo 1 episódio aberto por `(device_id, type)`: índice único parcial `alert (device_id, type) WHERE ended_at IS NULL` (proposta para [04](04-dominio-e-dados.md)).
3. Reconhecer grava `acknowledged_at`/`acknowledged_by` e só fecha onde a tabela diz.
4. `started_at` = instante do fato (`observedAt`, `fixTime` ou limiar cruzado); `ended_at` = instante do fato que fechou.
5. `alert.evidence`: `{openRevision, closeRevision, trigger, processingMode, stale, signalCount, lastSignalAt, closeReason, lastLocation: {latitude, longitude, fixTime} | null, timings: {originAt, receivedAt, projectedAt, openedAt}}`.

## 7. Entrega push (FCM)

1. **Destinatários:** usuários com membership ativa no cliente do veículo (`tenant_owner`; `tenant_member` com acesso ao veículo, [08](08-identidade-e-seguranca.md)), preferência ligada para (veículo, tipo) e ≥ 1 `push_token`. Equipe da operadora usa a fila do console (§9); sem push para ela no F0–F1.
2. **Chave:** `delivery_key = {alertId}:{userId}:push:{open|close}`; `INSERT … ON CONFLICT (delivery_key) DO NOTHING`. Uma `alert_delivery` por usuário; envio para até 5 tokens do usuário (os de `last_seen_at` mais recente, até 60 dias). `sent` quando ≥ 1 token recebe 200; `sent_at` = primeiro 200. Sem token → `no_token`.
3. **Status:** `pending`, `sent`, `failed`, `expired` (janela do §3 item 6 vencida), `suppressed` (`ALERT_DELIVERY_ENABLED=false`), `no_token`. [ADOTADO NA v2.0: variável `ALERT_DELIVERY_ENABLED`, padrão `true`, desligada em ensaio de restore e na standby antes da promoção, simétrica a `COMMAND_DISPATCH_ENABLED` de REQ-ARQ-016.]
4. **Retentativa:** até 5 tentativas, esperas de 2, 4, 8 e 16 s × fator em [0,8; 1,2], respeitando `Retry-After` maior; para quando a janela vence (`expired`).
5. **Colapso:** `collapseId` = 32 primeiros caracteres hex de SHA-256 da `episode_key`; o aviso de encerramento usa o mesmo id e substitui a notificação de abertura. TTL: 3.600 s (`critical`), 1.800 s (`warning`), 600 s (`info`).

```http
POST https://fcm.googleapis.com/v1/projects/{FCM_PROJECT_ID}/messages:send
{ "message": {
    "token": "<push_token.token>",
    "notification": { "title": "Pânico acionado", "body": "Gol prata: botão de pânico às 21:14. Toque para falar com a central." },
    "data": { "alertId": "0192a1b2-0011-7c3d-8e4f-5a6b7c8d9e11", "vehicleId": "0192a1b2-0000-7000-8000-0000000000f1", "type": "sos", "severity": "critical", "startedAt": "2026-10-21T00:14:03Z", "link": "tracksys://alerts/0192a1b2-0011-7c3d-8e4f-5a6b7c8d9e11" },
    "android": { "priority": "HIGH", "ttl": "3600s", "notification": { "channel_id": "alerts_high", "tag": "<collapseId>" } },
    "apns": { "headers": { "apns-priority": "10", "apns-push-type": "alert", "apns-collapse-id": "<collapseId>", "apns-expiration": "<epoch + 3600>" },
              "payload": { "aps": { "sound": "default", "interruption-level": "time-sensitive", "thread-id": "<vehicleId>" } } } } }
```

| Resposta do FCM | Ação |
|---|---|
| 200 | Token aceito |
| 404 `UNREGISTERED`, 403 `SENDER_ID_MISMATCH` | Apaga o `push_token` e tenta o próximo; sem tokens válidos → `failed` (`token_invalid`) |
| 400 `INVALID_ARGUMENT` | `failed`, sem retentativa; evento no Sentry |
| 401 `THIRD_PARTY_AUTH_ERROR` | `failed` e aviso ao fundador (credencial APNs) |
| 429 `QUOTA_EXCEEDED`, 500 `INTERNAL`, 503 `UNAVAILABLE`, timeout de 10 s, erro de rede | Retentativa (item 4) |

**Tokens:** `PUT /api/v1/me/push-tokens` com `{"token": "…", "platform": "android" | "ios"}` faz upsert pelo token (o token passa a pertencer ao usuário atual) e renova `last_seen_at`; o app chama no login, a cada abertura e na renovação do token. Logout chama `DELETE /api/v1/me/push-tokens` com `{"token": "…"}`. Job diário apaga tokens sem uso há 60 dias. Credenciais: `FCM_PROJECT_ID` e `FCM_SERVICE_ACCOUNT_JSON` (base64), validadas no boot do `worker` ([03 §13](03-arquitetura.md)). Canais Android e permissão Time Sensitive no iOS: [10](10-apps-e-ux.md).

## 8. Preferências por usuário

Tabela proposta para [04](04-dominio-e-dados.md): `alert_preference (id, operator_id, tenant_id, user_id, vehicle_id, type, enabled bool, params jsonb NULL, updated_at)`, `UNIQUE (user_id, vehicle_id, type)`, escopo de cliente. Sem linha = padrão do catálogo.

| Rota | Comportamento |
|---|---|
| `GET /api/v1/me/alert-preferences?vehicleId=<uuid>` | Lista `{type, enabled, locked, available, params}` para os tipos da fase em vigor |
| `PUT /api/v1/me/alert-preferences` com `{vehicleId, type, enabled, params?}` | 200; `sos` e `watch_mode_breach` com `enabled = false` → 422 `ALERT_PREFERENCE_LOCKED`; `overspeed.params.limitKmh` fora de 40–200 → 422; veículo fora do escopo → 404 |

A preferência só decide a entrega ao usuário. O episódio é sempre registrado e aparece na fila da central.

## 9. Fila de alertas no console da central

1. `GET /api/v1/alerts?status=open|acknowledged|closed&severity=&vehicleId=&from=&to=&cursor=`. Escopo operadora para `operator_admin`, `operator_agent` e `search_team`; usuários do cliente veem só os seus.
2. Ordem: abertos sem reconhecimento primeiro; depois severidade (`critical` > `warning` > `info`); depois `started_at` crescente.
3. Colunas: severidade, tipo (rótulo PT-BR), veículo (apelido e placa), cliente, início em BRT e duração, idade do último contato, reconhecido por e quando.
4. Ações: **Reconhecer** (`POST /api/v1/alerts/{id}/acknowledge`, `{"note": "…"}` opcional até 500 caracteres; idempotente; grava `audit_log` `alert.acknowledge`); ver no mapa; WhatsApp ou telefone do cliente por deep link ([10](10-apps-e-ux.md)); abrir atendimento com `alert_id` (F1).
5. Atualização ao vivo pelo evento SSE `alert` (§11); alerta `critical` novo toca som com a aba aberta ([10](10-apps-e-ux.md)).

## 10. Medição de latência

| Marco | Campo | Valor |
|---|---|---|
| t0 origem | `evidence.timings.originAt` | `serverTime` do Traccar na mensagem gatilho; no silêncio, `last_contact_at` + limiar |
| t1 recebido | `evidence.timings.receivedAt` | `ingest_inbox.received_at` |
| t2 projetado | `evidence.timings.projectedAt` | `occurredAt` do `device.state.updated.v1` |
| t3 aberto | `evidence.timings.openedAt` | Relógio do worker ao inserir o alerta |
| t4 enviado | `alert_delivery.sent_at` | Primeiro 200 do FCM |

1. **Latência do alerta** = t4 − t0 da primeira entrega `sent`. Meta: p95 ≤ 30 s (SLO interno, F1); G0: p95 ≤ 60 s ([02 G0-5](02-escopo-e-fases.md)). Entregas `expired`, `suppressed` e de modo não ao vivo ficam fora.
2. Métricas: `alert_latency_seconds{type,severity}` (t4 − t0); `alert_stage_seconds{stage}` com `ingest` (t1 − t0), `project` (t2 − t1), `evaluate` (t3 − t2), `deliver` (t4 − t3); `alerts_queue_oldest_age_seconds{queue}`; `alert_deliveries_total{status}`.
3. **Minuto ruim por latência** (entrada do SLO de [13](13-infra-e-operacao.md)): o minuto m é ruim se (a) o p95 de t4 − t0 das entregas com `sent_at` em m passa de 120 s; ou (b) ao fim de m existe entrega `pending` com idade (fim de m − t0) > 120 s; ou (c) o job mais antigo de `alerts.evaluate` ou `alerts.deliver` tem mais de 120 s.

```sql
-- p95 de latência numa janela (T-015)
SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY extract(epoch FROM d.sent_at - (a.evidence->'timings'->>'originAt')::timestamptz))
FROM app.alert_delivery d JOIN app.alert a ON a.id = d.alert_id AND a.tenant_id = d.tenant_id
WHERE d.status = 'sent' AND d.sent_at >= $1 AND d.sent_at < $2;
```

## 11. Tempo real: `GET /api/v1/stream` (SSE)

| Item | Regra |
|---|---|
| Autenticação | Sessão Better Auth por cookie (console) ou `Authorization: Bearer` (app). Token em query string nunca é aceito. Sem sessão → 401 |
| Escopo | `?vehicleIds=<uuid>,<uuid>` (até 200). Ausente: todo o escopo da membership se ≤ 200 veículos; senão 422 `STREAM_SCOPE_TOO_LARGE` com `maxVehicles: 200`. Qualquer id fora do escopo → 404 para o pedido inteiro |
| Limites | 200 veículos por conexão; 2 conexões por sessão (a 3ª abre e a mais antiga recebe `close` com `replaced`); vida máxima 60 min (`lifetime`); fila de saída > 500 eventos (`overflow`). Console com mais de 200 veículos divide o escopo em 2 conexões (Lider: ~300). [ADIADO PARA O F2: conexão de escopo operadora com até 1.000 veículos quando uma operadora passar de 400 veículos ativos (F2).] |
| Cabeçalhos | `Content-Type: text/event-stream; charset=utf-8`, `Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no` |
| Eventos | `vehicle.state` com `id: <revision>`; `alert` sem `id`; `ready` ao fim do snapshot; `close` antes de encerrar |
| Heartbeat | Comentário `: keep-alive <RFC 3339>` a cada 15 s ([03 §7](03-arquitetura.md)) |
| Origem | NOTIFY `device_state` (coalescido 250 ms por dispositivo) e NOTIFY `alert_changed`; o `api` relê sob o contexto RLS da conexão; nada passa pelo pg-boss |
| Revogação | Logout, troca de senha ou remoção de membership dispara NOTIFY `auth_changed` ([08](08-identidade-e-seguranca.md)); conexões afetadas recebem `close` com `session_revoked` em ≤ 5 s. Sessão revalidada a cada 60 s (`session_expired`) |

```text
retry: 5000

event: vehicle.state
id: 1048577
data: {"vehicleId":"0192a1b2-0000-7000-8000-0000000000f1","deviceId":"0192a1b2-0000-7000-8000-0000000000d1","isPrimary":true,"revision":1048577,"lastContactAt":"2026-10-20T15:20:00.000Z","lastFixAt":"2026-10-20T15:19:58.000Z","position":{"latitude":-5.089211,"longitude":-42.801892,"speedKmh":18.5,"courseDeg":179},"ignition":true,"motion":"moving","relayState":"unknown","powerState":"main","presence":"online"}

event: alert
data: {"alertId":"0192a1b2-0011-7c3d-8e4f-5a6b7c8d9e11","vehicleId":"0192a1b2-0000-7000-8000-0000000000f1","type":"sos","severity":"critical","status":"open","startedAt":"2026-10-20T15:18:40.000Z","endedAt":null,"acknowledgedAt":null,"title":"Pânico acionado","body":"Gol prata: botão de pânico às 12:18. Toque para falar com a central."}

event: ready
data: {"vehicles":1,"openAlerts":1,"serverTime":"2026-10-20T15:20:01.002Z"}

: keep-alive 2026-10-20T15:20:16Z
```

1. **Snapshot:** ao conectar, o servidor envia `retry: 5000`, um `vehicle.state` por veículo do escopo (revisão atual), os alertas abertos do escopo e `ready`. Depois, só mudanças.
2. **Reconexão:** o cliente manda `Last-Event-ID`; o servidor sempre reenvia o snapshot completo (a revisão é por dispositivo, não cursor global). O cliente descarta `vehicle.state` com o mesmo `(vehicleId, deviceId)` e revisão menor ou igual à exibida; `deviceId` diferente substitui. `alert` é deduplicado por `alertId` com precedência `closed` > `acknowledged` > `open` (INV-04).
3. **`close`:** `session_revoked` e `session_expired` levam ao login, sem reconexão; `replaced`, `lifetime`, `overflow` e `shutdown` reconectam com espera de 1 s dobrando até 30 s, ± 20%.
4. **Campos:** `position` é `null` sem fix válido; `ignition`, `relayState` e `powerState` seguem INV-03 (`null`/`unknown`, nunca `false` por ausência). `presence` é calculado na emissão por `packages/domain/src/alerts/presence.ts` e recalculado no cliente a cada 10 s com a mesma tabela: `lost_moving` (regra do `signal_lost_moving`), `offline` (contato > 1.800 s), `delayed` (contato > `stopped_interval_s` + 60 s; J16: 360 s), senão `online`.
5. O app usa SSE só em primeiro plano; em segundo plano, push ([ADR-008](../adr/ADR-008-contrato-primeiro-zod-openapi-sse.md)). Visitante de link compartilhado usa fluxo próprio ([08](08-identidade-e-seguranca.md)).

## 12. Invariantes aplicadas

| INV | Como este capítulo cumpre |
|---|---|
| INV-03 | Ignição NULL não abre `ignition_on` nem violação por ignição; `power_state` `unknown` não fecha `power_cut`; velocidade NULL não conta para `overspeed`; capacidade `null` torna o tipo indisponível; SSE envia `null`, nunca `false` por ausência |
| INV-04 | `id` do SSE = revisão; cliente descarta revisão menor ou igual; snapshot completo na reconexão |
| INV-05 | Modo diferente de `live` registra o episódio sem `alert_delivery`; `ALERT_DELIVERY_ENABLED=false` em restore e standby; job repetido não duplica (`episode_key`, `delivery_key`) |
| INV-07 | Fila, preferências e SSE leem sob o RLS da sessão; jobs releem sob o RLS do evento ([03 REQ-ARQ-010](03-arquitetura.md)) |

## 13. Requisitos

### REQ-ALR-001 — Catálogo e disponibilidade por hardware
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-03
**Regra.** O motor DEVE implementar os tipos do §2 com gatilho, severidade e texto da tabela, e NÃO DEVE abrir alerta de tipo indisponível para o perfil do dispositivo primário.
**Aceite.** CT-ALR-001 — Dado V1 com perfil `sos = null`, Quando chega posição com `alarm = "sos"`, Então nenhum alerta é aberto, `alerts_unexpected_alarm_total{alarm="sos"}` vale 1 e as preferências de V1 mostram `sos` com `available = false`; Dado perfil `sos = true`, Então abre 1 alerta `sos` com severidade `critical`.

### REQ-ALR-002 — Ignição ligada
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-03
**Regra.** `ignition_on` DEVE abrir só na transição `false → true` e fechar na transição `true → false`; a entrega segue a preferência (padrão desligado).
**Aceite.** CT-ALR-002 — Dado `dono.a1` com `ignition_on` ligado para V1 (apelido "Gol prata") e `device_state.ignition = false`, Quando chega posição com `ignition = true` e `serverTime = 2026-10-21T00:14:03Z`, Então abre 1 alerta e o fake de FCM recebe "Ignição ligada" — "Gol prata: ignição ligada às 21:14."; Dado `ignition` anterior NULL, Então nenhum alerta; Dado `dono.a1` sem linha de preferência, Então o alerta é registrado e 0 push sai.

### REQ-ALR-003 — Ativação e desativação do modo vigilância
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-03, INV-07
**Regra.** As rotas do §5 DEVEM aplicar pré-condições, âncora, idempotência e auditoria.
**Aceite.** CT-ALR-003 — Dado V1 parado, ignição `false` e último fix válido em (−5,0892110, −42,8018920) há 2 h, Quando `dono.a1` faz `POST /api/v1/vehicles/V1/watch-mode` com `{}`, Então 201 com essa âncora, `radiusM = 150` e `audit_log` `watch_mode.activate`; repetir o POST devolve 200 com o mesmo `watchModeId`; Dado ignição `true`, Então 409 `WATCH_MODE_VEHICLE_ON`; Dado `dono.a2`, Então 404.

### REQ-ALR-004 — Violação do modo vigilância
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-03, INV-05
**Regra.** `watch_mode_breach` DEVE abrir pela ignição observada após a ativação ou por 2 fixes válidos consecutivos fora do raio, 1 vez por ativação.
**Aceite.** CT-ALR-004 — Dado modo ativo com âncora (−5,0892110, −42,8018920), raio 150 m e perfil `ignition = null`, Quando chegam fixes válidos em (−5,0880110, …) a 133 m e depois em (−5,0874110, …) a 200 m, Então nenhum alerta; Quando chega o 2º fix seguido a 200 m, Então abre 1 `watch_mode_breach` com `evidence.trigger = "distance"` e push `critical`; Quando chega um 3º fix fora, Então nenhum alerta novo.

### REQ-ALR-005 — Corte de alimentação
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-03
**Regra.** `power_cut` DEVE seguir catálogo e episódios (§2, §6); sinais repetidos com episódio aberto NÃO DEVEM gerar novo push. Gatilho real do J16: [VALIDAR — DEC-02].
**Aceite.** CT-ALR-005 — Dado perfil `power_cut_alarm = true` e `power_source = "charge"`, Quando chega `alarm = "powerCut"` às 03:10:00Z, Então abre 1 alerta e 1 push; Quando chega outro `powerCut` às 03:12:00Z, Então `evidence.signalCount = 2` e 0 push novo; Quando chega `charge = true` às 03:20:00Z, Então fecha com `power_restored` e sai 1 push `info` "Gol prata: energia do veículo restabelecida às 00:20."

### REQ-ALR-006 — SOS
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-01
**Regra.** `sos` DEVE abrir por alarme de posição ou de evento, juntar sinais do mesmo episódio, fechar no reconhecimento e não ser desativável.
**Aceite.** CT-ALR-006 — Dado perfil `sos = true`, Quando a posição e o evento `alarm` do mesmo acionamento chegam com 2 s de diferença, Então existe 1 alerta e 1 push por usuário; Quando `agente.alfa` reconhece, Então `ended_at` é preenchido com `acknowledged`; Quando novo `sos` chega 1 min depois, Então abre novo alerta e novo push; `PUT` de preferência `sos` com `enabled = false` → 422 `ALERT_PREFERENCE_LOCKED`.

### REQ-ALR-007 — Sem comunicação e incidente de plataforma
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-03
**Regra.** O laço do §4 DEVE abrir `offline` após 1.800 s sem contato, fechar no contato seguinte e suspender aberturas durante incidente de plataforma.
**Aceite.** CT-ALR-007 — Dado V1 parado com `last_contact_at = 10:00:00Z`, Quando o laço roda às 10:30:14Z, Então abre `offline` com `started_at = 10:30:00Z`; Quando chega heartbeat às 10:41:00Z, Então fecha com `contact_resumed` e sai 1 push "Gol prata voltou a comunicar às 07:41."; Dado 20 dispositivos ativos e o Traccar parado às 10:00:00Z, Quando o laço roda até 10:45:00Z, Então 0 alertas `offline` e o fake de Pushover recebe 1 page.

### REQ-ALR-008 — Comunicação perdida em movimento
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-03
**Regra.** `signal_lost_moving` DEVE abrir após 180 s sem contato com `motion = 'moving'` e ignição diferente de `false`, e impedir `offline` enquanto aberto.
**Aceite.** CT-ALR-008 — Dado V1 com `motion = 'moving'`, `ignition = true` e `last_contact_at = 14:00:00Z`, Quando o laço roda às 14:03:14Z, Então abre `signal_lost_moving` com `started_at = 14:03:00Z` e o fake de FCM recebe o push em ≤ 30 s; Dado ignição `false` observada às 13:59:50Z, Então nenhum `signal_lost_moving` e, às 14:30:14Z, abre `offline`; Dado `signal_lost_moving` aberto há 40 min, Então nenhum `offline`.

### REQ-ALR-009 — Episódios idempotentes
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-01, INV-05
**Regra.** Abertura e entrega DEVEM usar `episode_key` e `delivery_key` únicos, com lock consultivo por dispositivo (§3, §6).
**Aceite.** CT-ALR-009 — Dado o job `alerts.evaluate` do `device.state.updated.v1` de revisão 1048577 com `transitions.ignition` `false → true`, Quando o job é entregue 3 vezes, 2 delas em paralelo, Então existe 1 alerta com `episode_key = "ignition_on:<deviceId>:1048577"`, 1 `alert.opened.v1` na outbox e 1 `alert_delivery` por usuário.

### REQ-ALR-010 — Fato antigo, modo não ao vivo e restore
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-05
**Regra.** A entrega DEVE obedecer o §3 item 6 e `ALERT_DELIVERY_ENABLED`.
**Aceite.** CT-ALR-010 — Dado posição com `alarm = "sos"` reprocessada da quarentena (`processingMode = "reprocess"`), Então abre 1 alerta com `evidence.processingMode = "reprocess"`, 0 `alert_delivery` e 0 chamadas ao fake de FCM; Dado `ignition_on` do buffer offline com `observedAt` 25 min antes da abertura, Então `evidence.stale = true` e 0 push; Dado `ALERT_DELIVERY_ENABLED=false`, Então as entregas ficam `suppressed`.

### REQ-ALR-011 — Push FCM com prioridade alta
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-07
**Regra.** O worker DEVE montar a mensagem do §7 por severidade e destinatário.
**Aceite.** CT-ALR-011 — Dado alerta `sos` para `dono.a1` com 1 token Android e 1 iOS, Quando entregue, Então o fake de FCM recebe 2 mensagens com `android.priority = "HIGH"`, `channel_id = "alerts_high"`, `apns-priority = "10"`, `interruption-level = "time-sensitive"`, `apns-collapse-id` igual aos 32 primeiros hex de SHA-256 da `episode_key`, e existe 1 `alert_delivery` `sent` com `delivery_key = "<alertId>:<userId>:push:open"`; `dono.a2` não recebe nada.

### REQ-ALR-012 — Retentativa e token inválido
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-01
**Regra.** Erros do FCM DEVEM seguir a tabela do §7, com até 5 tentativas dentro da janela.
**Aceite.** CT-ALR-012 — Dado o fake respondendo 503, 503 e 200, Então `sent` com `attempts = 3` e esperas de 1,6–2,4 s e 3,2–4,8 s; Dado 404 `UNREGISTERED` no token T1 e 200 no T2, Então T1 sai de `push_token` e a entrega fica `sent`; Dado 503 contínuo num alerta `warning`, Então após 5 tentativas o status é `failed` e nenhum envio ocorre depois.

### REQ-ALR-013 — Preferências por usuário
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-07
**Regra.** As rotas do §8 DEVEM devolver o valor efetivo (linha ou padrão) e só afetar a entrega do próprio usuário.
**Aceite.** CT-ALR-013 — Dado `dono.a1` sem linhas, Quando `GET /api/v1/me/alert-preferences?vehicleId=V1`, Então `ignition_on` tem `enabled = false` e `sos` tem `enabled = true, locked = true`; Quando faz `PUT` com `ignition_on` ligado, Então o próximo `ignition_on` de V1 gera push para ele; Dado `dono.a2` com `vehicleId = V1`, Então 404.

### REQ-ALR-014 — Fila de alertas e reconhecimento
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-07
**Regra.** A fila DEVE seguir o §9: escopo, ordem, colunas, reconhecimento auditado e atualização por SSE.
**Aceite.** CT-ALR-014 — Dado na Alfa um `offline` (warning) às 10:00, um `signal_lost_moving` (critical) às 10:05 e um `ignition_on` (warning) às 10:01, e 1 alerta da Beta, Quando `agente.alfa` lista `status=open`, Então recebe 3 na ordem `signal_lost_moving`, `offline`, `ignition_on`, e nenhum da Beta; Quando reconhece o `signal_lost_moving`, Então `acknowledged_by = agente.alfa`, `audit_log` registra `alert.acknowledge`, `ended_at` continua NULL e o SSE do console recebe `alert` com `status = "acknowledged"` em ≤ 2 s.

### REQ-ALR-015 — Latência medida por etapa
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** —
**Regra.** Todo alerta DEVE gravar `evidence.timings` e emitir as métricas do §10; a regra de minuto ruim por latência DEVE ser computável por consulta.
**Aceite.** CT-ALR-015 — Dado posição com `serverTime = 15:20:00.000Z` que abre `ignition_on` e o fake de FCM aceitando às 15:20:07.400Z, Então `originAt ≤ receivedAt ≤ projectedAt ≤ openedAt` e `alert_latency_seconds` registra 7,4 s; Dado o worker parado por 3 min com 1 job de `alerts.evaluate` (ignição ligada) na fila, Então os minutos em que esse job passou de 120 s saem como ruins na consulta de [13](13-infra-e-operacao.md).

### REQ-ALR-016 — SSE: autenticação e escopo
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N0 · **Invariantes:** INV-07
**Regra.** `GET /api/v1/stream` DEVE autenticar por cookie ou Bearer, rejeitar token em query e recusar por inteiro pedido com id fora do escopo.
**Aceite.** CT-ALR-016 — Dado `dono.a1`, Quando pede `?vehicleIds=V2` (da Beta), Então 404 sem conexão aberta; Quando pede `?vehicleIds=V1` com Bearer válido, Então 200 `text/event-stream`, primeira linha `retry: 5000`, 1 `vehicle.state` de V1 e `ready` com `vehicles = 1`; Quando pede sem credencial e com `?access_token=<válido>`, Então 401.

### REQ-ALR-017 — SSE: limites de veículos e conexões
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-07
**Regra.** O servidor DEVE aplicar 200 veículos por conexão, 2 conexões por sessão, vida de 60 min e fila de saída de 500 eventos.
**Aceite.** CT-ALR-017 — Dado `agente.alfa` com 250 veículos no escopo, Quando conecta sem `vehicleIds`, Então 422 `STREAM_SCOPE_TOO_LARGE` com `maxVehicles = 200`; Quando abre 3 conexões com 100 veículos cada na mesma sessão, Então a 1ª recebe `event: close` com `{"reason":"replaced"}` e é encerrada, e as outras 2 seguem.

### REQ-ALR-018 — SSE: revisão, snapshot e heartbeat
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-04
**Regra.** O stream DEVE enviar snapshot na conexão e na reconexão, `id` igual à revisão e heartbeat a cada 15 s; o redutor do cliente DEVE descartar revisão menor ou igual.
**Aceite.** CT-ALR-018 — Dado o cliente exibindo V1 na revisão 1048577, Quando reconecta com `Last-Event-ID: 1048577` e recebe o snapshot 1048577 seguido de um `vehicle.state` atrasado de revisão 1048512, Então continua exibindo 1048577; Quando chega 1048601, Então exibe 1048601; sem mudanças por 60 s, o cliente recebe 4 comentários `: keep-alive` (± 1).

### REQ-ALR-019 — SSE: revogação de sessão
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N0 · **Invariantes:** INV-07
**Regra.** Revogação de sessão ou de membership DEVE encerrar as conexões afetadas em ≤ 5 s (§11).
**Aceite.** CT-ALR-019 — Dado `dono.a1` com SSE aberto, Quando `admin.alfa` remove a membership de `dono.a1`, Então a conexão recebe `close` com `session_revoked` em ≤ 5 s, e nova conexão com o mesmo token recebe 401.

### REQ-ALR-020 — Bateria baixa
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-03
**Regra.** `low_battery` DEVE abrir em ≤ 20% fora da alimentação principal (ou alarme `lowBattery`) e fechar em ≥ 30% ou na volta da alimentação.
**Aceite.** CT-ALR-020 — Dado perfil com `batteryLevel` reportado e `power_state = 'battery'`, Quando chega `batteryLevel = 20`, Então abre `low_battery`; com 25, continua aberto; com 30, fecha com `recovered`; Dado mensagem sem `batteryLevel`, Então nada muda.

### REQ-ALR-021 — Excesso de velocidade
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-03
**Regra.** `overspeed` DEVE abrir com `location` e `previousLocation` acima do limite e fechar com ambos ≤ limite − 10 km/h, ignição `false` ou 10 min sem fix.
**Aceite.** CT-ALR-021 — Dado limite 110 km/h ligado, Quando chegam fixes válidos de 115 e 118 km/h às 18:20Z, Então abre 1 `overspeed` com corpo "Gol prata: 118 km/h às 15:20, acima do limite de 110 km/h."; Quando chega 105 km/h, Então continua aberto; Quando chegam 2 fixes de 98 km/h, Então fecha.

### REQ-ALR-022 — Cerca virtual
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-06, INV-07
**Regra.** O usuário DEVE poder criar até 10 cercas por veículo (círculo de 100–5.000 m ou polígono de 3–100 vértices; gatilho `enter`, `exit` ou `both`), avaliadas no worker com PostGIS (`ST_DWithin` para círculo, `ST_Covers` para polígono). Tabela `geofence` proposta para [04](04-dominio-e-dados.md).
**Aceite.** CT-ALR-022 — Dado a cerca circular "Casa" de 300 m centrada em (−5,0892110, −42,8018920) com gatilho `both` e V1 dentro, Quando chegam 2 fixes válidos seguidos em (−5,0856110, −42,8018920), a 400 m, com `fixTime` 12:00:00Z e 12:00:30Z, Então abre 1 `geofence` com corpo "Gol prata saiu de Casa às 09:00." e `ended_at = started_at = 12:00:30Z`; Quando 1 fix volta para dentro e o seguinte fica fora, Então nenhum alerta.

### REQ-ALR-023 — Crítico sem reconhecimento
**Fase:** F1 · **Prioridade:** P2 · **Risco:** N2 · **Invariantes:** —
**Regra.** Alerta `critical` aberto sem reconhecimento por 5 min DEVE ficar destacado na fila e gerar notificação do navegador no console aberto.
**Aceite.** CT-ALR-023 — Dado `signal_lost_moving` aberto às 02:00:00Z sem reconhecimento, Quando o relógio chega a 02:05:00Z, Então a linha fica destacada e o console aberto mostra a notificação "Alerta crítico sem resposta há 5 min".
