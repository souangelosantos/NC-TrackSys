# 05 — Ingestão e telemetria

> **Resumo:** Define como uma mensagem decodificada pelo Traccar vira fato durável na TrackSys: contrato do forward HTTP, rotas internas, normalização de unidades, identidade de origem e dedupe, janela de tempo, projeção síncrona com fallback, ordenação por revisão, compactação de parado, quarentena, reconciliação e backfill. Fecha com o checklist do spike do J16, os testes de propriedade de INV-01 a INV-04 e as métricas de ingestão.
> **Fases:** F0, F1  ·  **Status:** Aprovado para execução
> **Muda em relação à v1.1:**
> - Broker e fila de projeção saem: inbox e projeção na mesma transação, com savepoint e reprocessamento pelo worker.
> - Janela de tempo fechada [received_at − 30 dias, received_at + 120 s]; fora dela, quarentena (caso WNRO tratado).
> - Compactação de parado (> 50 m ou 30 min) e linha compacta em inteiros.
> - Heartbeat (`outdated`) e fix inválido atualizam contato e status, sem virar posição.
> - Reconciliação contínua com o Traccar a cada 15 min, sem efeito externo (INV-05).

## 1. Onde fica o código

Fluxo: `traccar` → `apps/api/src/ingestion/traccar.controller.ts` (listener `INTERNAL_PORT` 3001) → `normalizeTraccar` → `decideProjection` → `applyProjection` → `ingest_inbox`, `position`, `device_state`, `outbox` ([03 §5](03-arquitetura.md)). O `worker` reusa o mesmo aplicador para `pending`, reconciliação e backfill.

| Peça | Caminho |
|---|---|
| Schemas do envelope Traccar e dos eventos | `packages/contracts/src/internal/traccar.ts`, `packages/contracts/src/events/telemetry-position-accepted.v1.ts`, `device-state-updated.v1.ts` |
| Normalização, janela, movimento, compactação, decisão de projeção (puro) | `packages/domain/src/ingestion/{normalize,window,motion,compaction,decide}.ts` |
| Inbox e aplicador da projeção (usado por `api` e `worker`) | `packages/db/src/ingestion/{inbox,apply-projection}.ts` |
| Jobs | `apps/worker/src/ingestion/{reprocess-pending,reconcile,retention}.ts`; CLI `apps/worker/src/ingestion/cli.ts` |
| Traccar, capturas e fakes | `infra/traccar/traccar.xml.tpl`, `infra/traccar/render-config.sh`; `packages/testkit/fixtures/j16/`, `packages/testkit/src/capture-server.ts`, `packages/testkit/src/fakes/traccar.ts` |

## 2. Contrato com o Traccar

O Traccar envia cada posição e cada evento por HTTP POST JSON, na rede Docker interna, para o listener interno do `api` (porta 3001, sem publicação no host; [03 §10](03-arquitetura.md)). O segredo nunca fica no repositório: `render-config.sh` gera `traccar.xml` no start do contêiner a partir de `INGEST_SHARED_SECRET` (substituição com `sed`, sem dependências).

| Chave (Traccar 6.x) | Valor | Motivo |
|---|---|---|
| `forward.enable` | `true` | Liga o forward de posições |
| `forward.type` | `json` | Corpo `{ "position": {…}, "device": {…} }` |
| `forward.url` | `http://api:3001/internal/v1/traccar/positions` | Rota interna |
| `forward.header` | `X-Ingest-Token: ${INGEST_SHARED_SECRET}` | Autenticação da origem |
| `forward.retry.enable` / `.delay` / `.count` / `.limit` | `true` / `1000` (ms) / `10` / `20000` | Reentrega em erro ou timeout; fila em memória de ~200 s a 100 msg/s |
| `event.forward.enable` / `.url` / `.header` | `true` / `http://api:3001/internal/v1/traccar/events` / mesmo header | Forward de eventos (`alarm`, `commandResult`) |
| `database.registerUnknown` | `false` | IMEI não provisionado não vira dispositivo |
| `processing.copyAttributes` | vazio | Copiar atributo da mensagem anterior fabrica estado (INV-03) |
| `filter.enable` | `false` | Janela e validade são decididas só pela TrackSys |
| `gt06.port` | `5023` | Porta do protocolo do J16 |

Todos os nomes de chave acima são **[VALIDAR — DEC-02]**: o spike confirma cada um na versão fixada, inclusive se o forward de eventos tem retentativa (padrão seguro: tratar como sem retentativa; alarmes também chegam no atributo `alarm` da posição, que tem retentativa). Retenção de 7 dias no banco `traccar`: [ADR-003](../adr/ADR-003-traccar-borda-de-protocolos.md). Retentativas do forward ficam em memória: reinício do Traccar ou fila cheia viram lacuna, recuperada pela reconciliação (§12).

## 3. Rotas internas

| Item | `POST /internal/v1/traccar/positions` | `POST /internal/v1/traccar/events` |
|---|---|---|
| Corpo | `{ position, device }` | `{ event, position?, device }` |
| Identidade | `position.id` | `event.id` |
| Uso | Posições, heartbeats, alarmes em atributo | `alarm` (fluxo de status do §8, `cause = event`), `commandResult` (correlação em [06](06-comandos-e-bloqueio.md)); demais tipos: inbox `processed` sem projeção |

Ordem de verificação (a primeira falha decide a resposta):

| # | Verificação | Resposta | Grava? |
|---|---|---|---|
| 1 | Header `X-Ingest-Token` ausente ou diferente de `INGEST_SHARED_SECRET` (comparação de SHA-256 com `timingSafeEqual`) | 401 `INGEST_UNAUTHORIZED` | Não |
| 2 | Corpo > 262.144 bytes (256 KiB; `bodyLimit` do Fastify) | 413 `INGEST_PAYLOAD_TOO_LARGE` | Não |
| 3 | JSON ilegível ou envelope reprovado no schema Zod (ex.: sem `position.deviceId`, sem `fixTime` em posição não `outdated`) | 400 `INGEST_INVALID_ENVELOPE` com `errors[].path` | Não; métrica + log com SHA-256 do corpo |
| 4 | Banco indisponível, pool esgotado ou prazo de 5 s estourado antes do commit | 503 `INGEST_UNAVAILABLE` + `Retry-After: 5` | Não (rollback) |
| 5 | Commit feito | 202 `{"result":"processed"\|"pending"\|"quarantined"\|"duplicate","inboxId":"<uuid>"}` | Sim |

Erros seguem Problem Details ([09](09-api-e-contratos.md)), sem eco do payload nem do segredo. O prazo de 5 s cobre leitura, transação e commit. Exemplo de corpo de posição (ids e IMEI fictícios; formato exato [VALIDAR — DEC-02]):

```json
{
  "position": {
    "id": 938441, "deviceId": 17, "protocol": "gt06", "outdated": false, "valid": true,
    "serverTime": "2026-10-20T15:20:00.000+00:00", "deviceTime": "2026-10-20T15:19:58.000+00:00", "fixTime": "2026-10-20T15:19:58.000+00:00",
    "latitude": -5.089211, "longitude": -42.801892, "altitude": 72.0, "speed": 10.0, "course": 178.5,
    "attributes": { "sat": 9, "ignition": true, "charge": true, "blocked": false, "batteryLevel": 100, "distance": 154.2, "totalDistance": 1520034.5, "hours": 3600000 }
  },
  "device": { "id": 17, "uniqueId": "860000000000001", "name": "V1" }
}
```

## 4. Normalização (fronteira única de unidades — INV-12)

Função pura `normalizeTraccar(envelope, profile)` em `packages/domain`. Campo ausente vira NULL ou `'unknown'`, nunca `false`/`0` (INV-03).

| Origem (Traccar) | Unidade | Destino | Regra | Ausente ou inválido |
|---|---|---|---|---|
| `position.fixTime` | RFC 3339 | `position.fix_time` | UTC, ms preservados | Posição não `outdated` sem `fixTime` → 400 |
| `position.deviceTime` | RFC 3339 | `observedAt` (§8) | Usado se dentro da janela | Usa `serverTime` |
| `position.serverTime` | RFC 3339 | `last_contact_at`; `source.serverTime` | Origem da latência de alerta ([07](07-alertas-e-tempo-real.md)) | Usa `received_at` |
| `latitude`, `longitude` | graus | `lat_e7`, `lon_e7` (int4) | `round(v × 10⁷)` | Fora de [−90, 90] ou [−180, 180] → quarentena `invalid_coordinates`; (0, 0) → fix inválido |
| `valid` | bool | `valid` | — | Ausente → `false` |
| `speed` | **nós** | `speed_kmh_x10` (int2) | `round(nós × 1,852 × 10)`: 10 nós = 18,52 km/h → **185** (18,5 km/h) | Ausente ou < 0 → NULL; > 300 km/h → NULL + flag `SPEED_DISCARDED` |
| `course` | graus | `course_deg` (int2) | `round(v) mod 360` | Fora de [0, 360] → NULL |
| `altitude` | m | `altitude_m` (int2) | `round(v)` | Fora de [−500, 9.000] → NULL |
| `attributes.sat` | — | `satellites` | inteiro | NULL |
| `attributes.ignition` | bool | `ignition` | Só se perfil `ignition = "yes"` | NULL |
| `attributes.alarm` | texto, vírgulas | `extra.alarms` (array) + flag `ALARM` | `split(',')`, nomes do Traccar (`sos`, `powerCut`, `powerRestored`, `lowBattery`, `jamming`…) | Sem alarme |
| `attributes.blocked` | bool | `device_state.relay_state` (`blocked`/`unblocked`) + `relay_observed_at`; `extra.blocked` na mudança | Só se perfil `relay_state_reported = "yes"` | `'unknown'` |
| `attributes.charge` ou `attributes.power` | bool / V | `device_state.power_state` | Conforme `power_source` do perfil (§13): `charge = true` ou `power ≥ power_main_min_v` → `main`; senão `battery` | `'unknown'` |
| `attributes.batteryLevel`, `attributes.battery` | %, V | `device_state.aux.batteryLevel`, `aux.batteryV`; `extra.batteryLevel` ao mudar de faixa de 10 pontos | 0–100; 1 casa | NULL |
| `attributes.distance`, `totalDistance`, `odometer` | m | `device_state.aux.totalDistanceM`, `odometerM` | inteiro | NULL |
| `attributes.hours` | **ms** | `device_state.aux.hoursS` | `÷ 1.000`: 3.600.000 ms = 3.600 s | NULL |
| `attributes.motion` | bool | Só se perfil `trust_motion_attribute = true` (§4.2) | — | Ignorado |
| `attributes.archive` | bool | flag `ARCHIVE` | Marca dado do buffer offline [VALIDAR — DEC-02] | — |
| Demais atributos | — | Descartados da linha | Ficam no payload da inbox por 7 dias | — |

`extra` é NULL na maioria das linhas; recebe só `alarms`, `blocked`, `powerState` e `batteryLevel` quando presentes ou mudados, até 1 KiB. `device_state.aux` (jsonb, 1 linha por dispositivo) guarda o estado auxiliar da projeção (§8, §9); DDL em [04](04-dominio-e-dados.md) §3.5.

### 4.1 Flags de `position.flags`

| Bit | Valor | Nome | Quando |
|---|---|---|---|
| 0 | 1 | `LATE` | `(fix_time, source_event_id)` ≤ posição atual: foi para o histórico (INV-02) |
| 1 | 2 | `ALARM` | `attributes.alarm` presente |
| 2 | 4 | `KEEPALIVE_30MIN` | Parado gravado pela regra de 30 min (§9) |
| 3 | 8 | `BACKFILL` | Gravado pela reconciliação ou backfill |
| 4 | 16 | `REPROCESSED` | Gravado por reprocessamento de quarentena |
| 5 | 32 | `ARCHIVE` | Perfil indica dado do buffer offline |
| 6 | 64 | `WNRO_CORRECTED` | `fix_time` corrigido em +1024 semanas (§6) |
| 7 | 128 | `SPEED_DISCARDED` | Velocidade > 300 km/h descartada |
| 8 | 256 | `JUMP_SUSPECT` | Velocidade implícita > 300 km/h e distância > 1 km desde o fix atual (anomalia/spoofing; ver [08](08-identidade-e-seguranca.md)) |
| 9 | 512 | `PREVIOUS_ASSIGNMENT` | Pertence a vínculo já encerrado (INV-06) |

### 4.2 Movimento (`device_state.motion`)

1. Fix válido com velocidade ≥ 5 km/h → `moving`; apaga `aux.slowSince`. Com `trust_motion_attribute = true`, `attributes.motion = true` com ignição `true` também leva a `moving`.
2. Fix válido com velocidade < 5 km/h: se o estado era `moving`, grava `aux.slowSince` (se vazio) e só passa a `stopped` quando `fix_time − slowSince ≥ 120 s` (semáforo não gera `stopped`; base do alerta de comunicação perdida em movimento, [07](07-alertas-e-tempo-real.md)); se era `stopped` ou `unknown`, vira `stopped`.
3. Ignição observada `false` → `stopped` imediatamente.
4. Sem fix válido nunca observado → `unknown`. Fix inválido e heartbeat não mudam `motion` (exceto a regra 3).

## 5. Identidade, inbox e dedupe (INV-01)

1. Chave: `(source_instance, kind, source_event_id)`. `source_instance` = `INGEST_SOURCE_INSTANCE` (ex.: `traccar-01`, [03 REQ-ARQ-013](03-arquitetura.md)); `kind` = `position` ou `event`; `source_event_id` = id do Traccar em texto decimal (`"938441"`).
2. Sem `id` na mensagem: se o perfil tem `source_id_strategy = 'fingerprint_v1'`, a chave é `fp1:` + SHA-256 hex de `deviceId|fixTime|latitude|longitude|speed|course|atributos ordenados`; senão, quarentena `missing_source_id`. Padrão: `traccar_id` [VALIDAR — DEC-02 se o forward traz `position.id`].
3. `payload_sha256` = SHA-256 do JSON canônico (chaves ordenadas) do objeto `position` ou `event`, sem o objeto `device`.
4. `INSERT … ON CONFLICT (source_instance, kind, source_event_id) DO NOTHING`. Conflito = duplicata: commit, 202 `duplicate`, nenhum efeito. Hash diferente na mesma chave: métrica `ingest_conflicting_duplicates_total` e log `warn` com a chave e os dois hashes; a linha original não muda.
5. Regressão de id: o `api` mantém em memória o maior id numérico visto por `(source_instance, kind)`, carregado no boot das últimas 24 h da inbox. Id mais de 10.000 abaixo desse máximo, fora de backfill, vai para quarentena `source_id_regression` com alerta ao fundador (REQ-ARQ-013).
6. Defesa em profundidade em `position`: a PK `(assignment_id, fix_time)` de [04](04-dominio-e-dados.md) §3.5 (não há índice por `source_event_id`). O mesmo `fix_time` no mesmo vínculo com outro id do Traccar grava 1 linha (a primeira) via `ON CONFLICT (assignment_id, fix_time) DO NOTHING`; sem linha nova, não há `telemetry.position.accepted.v1`. A localização de `device_state` continua usando o desempate por id (§8).

## 6. Resolução do dispositivo e janela de tempo

`app.resolve_device_for_ingest(source_instance text, unique_id text)` — SECURITY DEFINER, dono `tracksys_owner`, executável só por `tracksys_ingest`, assinatura e corpo em [04](04-dominio-e-dados.md) §4.4 — devolve 0 ou 1 linha `(device_id, operator_id)` do rastreador não aposentado com `imei = device.uniqueId`. Com o `operator_id`, a projeção abre o contexto `operator` (§7), trava `device_state`, confere `device.traccar_device_id` e lê sob RLS o vínculo com `p_at ∈ [valid_from, valid_to)` e o perfil. O tenant vem sempre do vínculo no servidor, nunca do payload (INV-07).

| Situação | Resultado |
|---|---|
| `device.uniqueId` não resolvido (função devolve 0 linhas) | Quarentena `unknown_device` |
| Resolvido, mas `device.traccar_device_id` NULL ou ≠ `position.deviceId` do envelope | Quarentena `device_identity_mismatch` (rastreador ainda não provisionado no Traccar, ver [02](02-escopo-e-fases.md) §2.3) |
| Sem vínculo em `p_at` | Quarentena `no_assignment` (instalador vê o status por função de [11](11-onboarding-e-migracao.md)) |
| Vínculo encerrado em `p_at` | Só histórico, flag `PREVIOUS_ASSIGNMENT`; `device_state` intocado (INV-06) |

**Janela aceita para `fix_time`:** `[received_at − 30 dias, received_at + 120 s]`, com `received_at` = relógio do `api` na chegada (no reprocessamento, o `received_at` original da inbox). Heartbeat (`outdated = true`) ignora `fixTime` e usa `serverTime` como `p_at`.

| Caso | Regra | Resultado |
|---|---|---|
| `fix_time > received_at + 120 s` | Relógio adiantado | Quarentena `fix_time_in_future` |
| `fix_time < received_at − 30 dias` e `fix_time + 1024 semanas` ∈ [received_at − 1 dia, received_at + 120 s] | Suspeita de **WNRO** (GPS week rollover: contador de 10 bits zera a cada 1024 semanas = 619.315.200 s ≈ 19,6 anos) | Perfil com `wnro_correction = true`: soma 619.315.200 s e grava com flag `WNRO_CORRECTED`. Senão: quarentena `wnro_suspect` |
| `fix_time < received_at − 30 dias`, outros casos | Dado velho demais | Quarentena `fix_time_too_old` |

Exemplo WNRO: `received_at = 2026-10-20T15:20:00Z` e `fix_time = 2007-03-06T15:20:00Z` (diferença exata de 7.168 dias). Padrão seguro: correção desligada até o spike provar o defeito no firmware [VALIDAR — DEC-02]. A janela de 30 dias cabe nas partições diárias de `position` (90 dias quentes, 7 à frente; [ADR-009](../adr/ADR-009-retencao-quente-frio.md)).

## 7. Projeção síncrona com fallback (passo a passo)

Papel `tracksys_ingest`, uma transação por mensagem:

```sql
BEGIN;
SET LOCAL statement_timeout = '4000ms'; SET LOCAL lock_timeout = '1000ms';
-- 1. Custódia
INSERT INTO app.ingest_inbox (source_instance, kind, source_event_id, payload, payload_sha256, received_at, status, attempts)
VALUES ($1, $2, $3, $4, $5, $6, 'pending', 1)
ON CONFLICT (source_instance, kind, source_event_id) DO NOTHING RETURNING id;
-- 0 linhas: duplicata → COMMIT → 202 duplicate
SAVEPOINT projection;
-- 2. Resolução e quarentena (§6): se quarentenar → UPDATE inbox SET status='quarantined', error='<código>' → RELEASE → COMMIT → 202
SELECT device_id, operator_id FROM app.resolve_device_for_ingest($source_instance, $unique_id);
-- 3. Contexto RLS da operadora dona (04 §4.1 item 4): tabelas tipo B só aceitam escrita no escopo operator
SELECT set_config('app.operator_id', $op, true), set_config('app.scope', 'operator', true), set_config('app.tenant_ids', '', true);
-- 4. Lock por dispositivo. A linha nasce com o device (04 §3.5); sem INSERT defensivo aqui
SELECT * FROM app.device_state WHERE device_id = $dev FOR UPDATE;   -- 0 linhas: erro device_state_missing (fica pending)
-- confere device.traccar_device_id = position.deviceId (§6); lê vínculo com p_at ∈ [valid_from, valid_to) e perfil, sob RLS
-- vínculo corrente ≠ device_state.assignment_id: erro device_state_binding_mismatch (fica pending; quem religa é o módulo fleet)
-- 5. decideProjection(estado, mensagem normalizada, perfil) → plano (packages/domain, puro)
INSERT INTO app.position (...) VALUES (...)
  ON CONFLICT (assignment_id, fix_time) DO NOTHING;                   -- se o plano grava posição (§5 item 6)
UPDATE app.device_state SET ...                                        -- sem revision: o gatilho device_state_revision atribui
 WHERE device_id = $dev RETURNING revision;                           -- se o plano muda estado
INSERT INTO app.outbox (operator_id, tenant_id, type, entity_id, payload) VALUES (...) RETURNING id;   -- §10
SELECT pg_notify('outbox_new', $outbox_id::text), pg_notify('device_state', $json_ids);
-- 6. Fecha a custódia
UPDATE app.ingest_inbox SET status = 'processed', processed_at = now(), error = NULL WHERE id = $inbox;
RELEASE SAVEPOINT projection;
COMMIT;   -- só então 202
```

Falha em qualquer ponto entre `SAVEPOINT` e `RELEASE`: `ROLLBACK TO SAVEPOINT projection` (desfaz posição, estado, outbox, NOTIFY e contexto RLS), depois `UPDATE ingest_inbox SET error = '<código>: <mensagem ≤ 500 caracteres>', next_attempt_at = now() + backoff(1)` com status `pending`, `COMMIT` e 202 `pending`. Queda do processo antes do `COMMIT` não grava nada: o Traccar não recebe 202 e reenvia. Queda depois do `COMMIT` e antes da resposta: a reentrega cai no passo 1 como duplicata.

A revisão vem do gatilho `device_state_revision` ([04](04-dominio-e-dados.md) §3.5), que usa a sequência global `app.device_state_revision_seq` sob o lock da linha: quem atualiza não passa `revision` e lê o valor com `RETURNING`. Ela é estritamente crescente por dispositivo e continua crescendo após troca de vínculo. A linha de `device_state` nunca é apagada: ao abrir ou encerrar vínculo, o módulo `fleet` zera a telemetria para NULL/`'unknown'` e religa `tenant_id`, `vehicle_id` e `assignment_id` na mesma transação (REQ-DAD-011). Para INV-04 equivale ao "revision + 1" de [03 §5](03-arquitetura.md), sem reiniciar em 1.

## 8. Ordenação e estado atual (INV-02, INV-04)

O plano separa três fluxos, cada um com sua ordem:

| Fluxo | Campos | Ordem | Atualiza quando |
|---|---|---|---|
| Localização | `lat_e7`, `lon_e7`, `speed_kmh_x10`, `course_deg`, `last_fix_at`, `motion` | `(fix_time, source_event_id numérico)` | Fix válido estritamente maior que `(last_fix_at, aux.fixSourceEventId)` |
| Status | `ignition`, `relay_state`, `relay_observed_at`, `power_state`, `aux.batteryLevel`, `aux.lastAlarm` | `(observedAt, source_event_id)`; `observedAt` = `deviceTime` dentro da janela, senão `serverTime` | Maior que `(aux.statusAt, aux.statusSourceEventId)` e campo presente (ausente não apaga valor anterior) |
| Contato | `last_contact_at` | `serverTime` | `greatest(last_contact_at, serverTime)` |

1. Fix com `(fix_time, id)` menor ou igual ao atual vai só para `position` com flag `LATE`; `device_state` não regride.
2. Revisão sobe uma vez por mensagem que mude qualquer campo; mensagem que não muda nada (ex.: backfill de dado velho) não sobe revisão nem emite `device.state.updated.v1`. Exceção: mensagem com alarme sempre sobe a revisão e emite o evento com `alarms`, mesmo fora de ordem (alarme é fato pontual; `aux.lastAlarm` só muda se mais novo). A deduplicação fica no episódio ([07](07-alertas-e-tempo-real.md)).
3. Resultado independe da ordem de chegada: para qualquer permutação, a localização final é a do fix válido de maior `(fix_time, id)` (propriedade P2, §16). Clientes descartam revisão menor ou igual à exibida ([07](07-alertas-e-tempo-real.md)).

## 9. Heartbeat, fix inválido e compactação de parado

| Mensagem | Grava `position`? | Atualiza `device_state` |
|---|---|---|
| `outdated = true` (heartbeat com localização copiada pelo Traccar [VALIDAR — DEC-02]) | Não | Contato e status |
| `valid = false` ou (0, 0) | Não (perfil com `store_invalid_fix = true` grava com `valid = false`) | Contato e status |
| Fix válido em movimento (`motion = moving` após o plano) | Sim | Localização, status, contato |
| Fix válido parado | Só se: deslocamento > 50 m da última posição **gravada**; ou ≥ 30 min desde ela (flag `KEEPALIVE_30MIN`); ou ignição mudou; ou há alarme | Sempre |
| Fix `LATE` | Sim (sem compactação) | Status e contato, se mais novos |

A última posição gravada fica em `aux.lastStored` (`latE7`, `lonE7`, `fixTime`), sem consulta a `position`. Distância por haversine com raio 6.371.008,8 m (exemplo numérico em CT-ING-013).

## 10. Eventos de outbox

Posição gravada → `telemetry.position.accepted.v1`. Revisão nova → `device.state.updated.v1`. Exemplos com ids fictícios:

```json
{
  "type": "telemetry.position.accepted.v1",
  "eventId": "0192a1b2-0001-7c3d-8e4f-5a6b7c8d9e01", "occurredAt": "2026-10-20T15:20:00.131Z", "processingMode": "live",
  "operatorId": "0192a1b2-0000-7000-8000-00000000a1fa", "tenantId": "0192a1b2-0000-7000-8000-0000000000a1",
  "vehicleId": "0192a1b2-0000-7000-8000-0000000000f1", "deviceId": "0192a1b2-0000-7000-8000-0000000000d1",
  "assignmentId": "0192a1b2-0000-7000-8000-0000000000b1",
  "source": { "sourceInstance": "traccar-01", "kind": "position", "sourceEventId": "938441", "protocol": "gt06", "serverTime": "2026-10-20T15:20:00.000Z", "inboxId": "0192a1b2-0002-7c3d-8e4f-5a6b7c8d9e02" },
  "fixTime": "2026-10-20T15:19:58.000Z", "receivedAt": "2026-10-20T15:20:00.120Z", "valid": true,
  "latitude": -5.089211, "longitude": -42.801892, "speedKmh": 18.5, "courseDeg": 179, "altitudeM": 72, "satellites": 9,
  "ignition": true, "alarms": [], "flags": [], "currentUpdated": true, "normalizationProfile": "j16-gt06/1"
}
```

```json
{
  "type": "device.state.updated.v1",
  "eventId": "0192a1b2-0003-7c3d-8e4f-5a6b7c8d9e03", "occurredAt": "2026-10-20T15:20:00.131Z", "processingMode": "live",
  "operatorId": "0192a1b2-0000-7000-8000-00000000a1fa", "tenantId": "0192a1b2-0000-7000-8000-0000000000a1",
  "vehicleId": "0192a1b2-0000-7000-8000-0000000000f1", "deviceId": "0192a1b2-0000-7000-8000-0000000000d1", "isPrimary": true,
  "revision": 1048577, "previousRevision": 1048512, "cause": "position",
  "source": { "sourceInstance": "traccar-01", "kind": "position", "sourceEventId": "938441", "serverTime": "2026-10-20T15:20:00.000Z", "receivedAt": "2026-10-20T15:20:00.120Z" },
  "observedAt": "2026-10-20T15:19:58.000Z", "changes": ["location", "ignition", "motion", "lastContact"],
  "transitions": { "ignition": { "from": false, "to": true }, "motion": { "from": "stopped", "to": "moving" } },
  "location": { "fixTime": "2026-10-20T15:19:58.000Z", "latitude": -5.089211, "longitude": -42.801892, "speedKmh": 18.5, "courseDeg": 179, "valid": true },
  "previousLocation": { "fixTime": "2026-10-20T15:19:28.000Z", "latitude": -5.089102, "longitude": -42.801850, "speedKmh": 0.0, "courseDeg": 178, "valid": true },
  "state": { "lastContactAt": "2026-10-20T15:20:00.000Z", "lastFixAt": "2026-10-20T15:19:58.000Z", "ignition": true, "motion": "moving", "relayState": "unknown", "powerState": "main", "batteryLevel": 100 }, "alarms": []
}
```

Regras: `cause` ∈ `position | heartbeat | event`; `processingMode` ∈ `live | reprocess | backfill | replay` (§11); `latitude`/`longitude` = `lat_e7 / 10⁷` e `speedKmh` = `speed_kmh_x10 / 10`, ou seja, os valores gravados; `transitions` traz, para cada campo de status que mudou (`ignition`, `motion`, `powerState`, `relayState`), `from` e `to`, calculados sob o lock (exatos, sem estado no consumidor). O consumidor lê o payload pela `outbox` com o contexto RLS do job ([03 §6](03-arquitetura.md)). Schemas em `packages/contracts`.

## 11. Reprocessamento e quarentena (INV-05)

| Situação | Quem | Modo | Regra |
|---|---|---|---|
| Inbox `pending` | Laço do worker a cada 5 s: `SELECT … WHERE status = 'pending' AND next_attempt_at <= now() ORDER BY received_at LIMIT 100 FOR UPDATE SKIP LOCKED` | `live` | Mesma transação do §7. Espera após a falha n: 2 s, 8 s, 32 s, 120 s, cada uma × fator aleatório em [0,75; 1,25]. 5ª falha (≈ 2,7 min) → `quarantined` com `projection_failed: <último erro>` e alerta |
| Inbox `quarantined` | Fundador, CLI `pnpm --filter @tracksys/worker ingest:reprocess -- --reason <código> --since <RFC 3339> [--device <uuid>] [--dry-run]` | `reprocess` | Só linhas com payload (≤ 7 dias); flag `REPROCESSED`; sucesso → `processed`; falha → continua `quarantined` com erro atualizado |
| Reconciliação e backfill | Worker (§12) | `backfill` | Flag `BACKFILL` |
| Republicação de eventos da outbox | CLI `ingest:republish` | `replay` | Só para recuperar consumidor; mesmo `eventId` |

Eventos em modo diferente de `live` levam `processingMode` no payload; todo consumidor com efeito externo (push, comando, SMS, cobrança, indicação) o ignora para efeito, podendo só registrar ([07](07-alertas-e-tempo-real.md), [06](06-comandos-e-bloqueio.md)). Mensagens `processed` nunca são reprojetadas. Colunas `attempts` e `next_attempt_at` da inbox: [04](04-dominio-e-dados.md) §3.5. Códigos de quarentena: `unknown_device`, `device_identity_mismatch`, `no_assignment`, `fix_time_in_future`, `fix_time_too_old`, `wnro_suspect`, `invalid_coordinates`, `missing_source_id`, `source_id_regression`, `projection_failed`.

## 12. Queda prolongada, reconciliação e backfill

1. **Reconciliação contínua:** job `ingest.reconcile` (pg-boss, `*/15 * * * *`). Para cada dispositivo com vínculo corrente, `GET /api/positions?deviceId=<traccar_device_id>&from=<now − 80 min>&to=<now − 20 min>` na API do Traccar (rota e parâmetros [VALIDAR — DEC-02]; se `from`/`to` filtram por `fixTime`, fix do buffer offline com `fix_time` antigo fica fora da janela e só o backfill manual o recupera [VALIDAR — DEC-02]), até 4 requisições simultâneas. Ids ausentes na inbox são projetados em modo `backfill`. A janela sobreposta torna o job idempotente; o atraso de 20 min evita disputar com as retentativas do forward. `ingest_reconciled_missing_total > 0` fora de queda conhecida indica perda no forward e gera aviso.
2. **Backfill manual** (queda > 1 h do `api` ou do banco): `ingest:backfill -- --from <RFC 3339> --to <RFC 3339> [--device <uuid>]`, limitado aos 7 dias retidos no Traccar (runbook em [13](13-infra-e-operacao.md)). Lacuna sem recuperação (fora dos 7 dias ou buffer perdido) não é inventada: histórico e relatórios a mostram ([10](10-apps-e-ux.md)).
3. **Buffer offline do J16:** sem cobertura, o J16 guarda fixes e os envia ao reconectar [VALIDAR — DEC-02]. Chegam ao vivo com `fix_time` antigo: viram histórico (`LATE` ou atual, conforme §8), dentro da janela de 30 dias. Alertas sobre fato antigo seguem a regra de atraso de [07](07-alertas-e-tempo-real.md).

## 13. Perfil de normalização (por `capability_profile`)

O perfil vem de `device.capability_profile_id`; a seção `normalization` vive dentro de `capability_profile.capabilities` e é versionada com o perfil (mudança cria nova `version`; o evento registra `normalizationProfile` = `<modelo>/<versão>`). As 11 capacidades de [04](04-dominio-e-dados.md) §3.3 usam `"yes"`, `"no"` ou `"unknown"` (INV-03); só `"yes"` habilita o uso do atributo, e `"unknown"` = não validada = tratada como ausente. Sem perfil, vale o embutido `generic-traccar/1`: todas as capacidades `"unknown"`, `source_id_strategy = 'traccar_id'`. Os campos de `normalization` mantêm os tipos da tabela abaixo. Formato do rascunho do J16 (T-002; cada capacidade só vira `"yes"`/`"no"` com arquivo de captura do §15 em `evidence`, o resto fica `"unknown"`):

```json
{
  "relay": "yes", "relay_state_reported": "unknown", "ignition": "yes", "power_cut_alarm": "unknown", "sos": "unknown",
  "accelerometer": "unknown", "device_speed_gate": "unknown", "secondary_server": "unknown", "domain_support": "unknown",
  "sms_position": "unknown", "offline_buffer": "unknown",
  "normalization": {
    "version": 1, "source_id_strategy": "traccar_id", "power_source": null, "power_main_min_v": null,
    "wnro_correction": false, "store_invalid_fix": false, "trust_motion_attribute": false,
    "archive_attribute": null, "moving_interval_s": 30, "stopped_interval_s": 300
  }
}
```

| Campo de `normalization` | Valores | Efeito |
|---|---|---|
| `source_id_strategy` | `traccar_id` \| `fingerprint_v1` | Identidade (§5) |
| `power_source` / `power_main_min_v` | `charge` \| `power_voltage` \| `null` / volts | `power_state` (§4) |
| `wnro_correction`, `store_invalid_fix`, `trust_motion_attribute` | bool | §6, §9, §4.2 |
| `archive_attribute` | nome do atributo ou `null` | Flag `ARCHIVE` |
| `moving_interval_s`, `stopped_interval_s` | segundos | Limiares de presença e lacuna ([07](07-alertas-e-tempo-real.md), [02 G0-1](02-escopo-e-fases.md)) |

## 14. Retenção da inbox

Job diário `ingest.retention` (pg-boss, `7 3 * * *` UTC, o horário de [04](04-dominio-e-dados.md) §8.1), em lotes de 10.000 linhas com pausa de 100 ms: `payload = NULL` quando `received_at < now() − 7 dias`; `DELETE` quando `received_at < now() − 90 dias`. `payload_sha256` fica com a identidade de dedupe até o DELETE, para que o conflito de hash do §5 continue detectável sem o payload [ADOTADO NA v2.0]. Vale para todos os status, salvo `pending`, que nunca é apagada. No F0, este job não tem cartão ([02](02-escopo-e-fases.md) §2.3). No mês 12 a inbox guarda ~135 milhões de identidades (~1,5 milhão por dia); o dimensionamento de disco entra em [04](04-dominio-e-dados.md) e [13](13-infra-e-operacao.md).

## 15. Spike do J16 (T-002): o que capturar

Ferramenta: `pnpm --filter @tracksys/testkit capture -- --port 3001` sobe um servidor que responde 202 e grava cada corpo recebido; o Traccar da bancada aponta o forward para ele. Cada arquivo vai para `packages/testkit/fixtures/j16/<cenário>/<NNN>-<position|event>.json`, com IMEI trocado por `860000000000001` e coordenadas transladadas para a origem fictícia (−5,089211, −42,801892), preservando tempos, velocidades e distâncias. Hex bruto do protocolo fica fora do repositório (bucket privado), citado por SHA-256 no `packages/testkit/fixtures/j16/manifest.json` (modelo, firmware, versão e digest do Traccar, data, cenário → arquivos → resultado esperado).

| Cenário | Procedimento | Decide |
|---|---|---|
| S01 parado-desligado | 20 min parado, ignição desligada | `stopped_interval_s`; heartbeat vem `outdated`? |
| S02 parado-ligado | 5 min parado, ignição ligada | Intervalo com ignição; `ignition` |
| S03 movimento | Rodar a 30 e 60 km/h estáveis (velocímetro + GPS do celular) | `moving_interval_s`; conversão nós → km/h (30 km/h ≈ 16,2 nós) |
| S04 ignição | 3 ciclos liga/desliga | `ignition` confiável |
| S05 corte de alimentação | Desligar o 12 V por 5 min e religar | `power_cut_alarm`, `power_source`, `powerRestored`, `batteryLevel` |
| S06 SOS | Acionar o botão (se instalado) | `sos` |
| S07 relé | Bloqueio/desbloqueio em bancada via Traccar | `relay`, `relay_state_reported` (`blocked`), `commandResult` ([06](06-comandos-e-bloqueio.md)) |
| S08 sem GSM | Caixa blindada 10 min em movimento simulado | `offline_buffer`, `archive_attribute`, ordem de reenvio |
| S09 sem GPS | Ambiente fechado 10 min | `valid = false`, comportamento de `fixTime` |
| S10 reinício | Desligar e ligar o rastreador | Login, ids |
| S11 SMS | Posição por SMS; troca de servidor por domínio; servidor secundário | `sms_position`, `domain_support`, `secondary_server` ([11](11-onboarding-e-migracao.md)) |
| S12 relógio | Comparar `deviceTime`, `fixTime` e `serverTime` em 50 mensagens | WNRO, deriva |
| S13 duplicidade | Derrubar o servidor de captura por 60 s | Retentativa do forward, `position.id`, chaves do §2 |
| S14 eventos | Conferir corpo do forward de eventos | `event.id`, tipos emitidos |

## 16. Testes de propriedade (fast-check)

Domínio puro em `packages/domain/test/ingestion.property.test.ts` (`numRuns: 1000`); versão com Postgres real em `tests/acceptance/T-005/ingestion.property.test.ts` (`numRuns: 25`, 1 operadora, 2 dispositivos).

| Prop. | INV | Gerador | Propriedade |
|---|---|---|---|
| P1 | INV-01 | Conjunto de 1–50 mensagens; cada uma entregue 1–5 vezes em ordem aleatória | Linhas na inbox = chaves distintas; `position` = fixes aceitos distintos; eventos na outbox e subidas de revisão iguais ao caso sem duplicata |
| P2 | INV-02 | Permutação de 2–30 fixes válidos com velocidade ≥ 5 km/h | Localização final = fix de maior `(fix_time, id)`; conjunto de `(fix_time, source_event_id)` em `position` idêntico para toda permutação |
| P3 | INV-03 | Mensagem válida com subconjunto aleatório de atributos removido | Cada atributo removido sai NULL/`unknown`; nunca `false`, `0` ou `unblocked`; estado anterior não é apagado |
| P4 | INV-04 | 2–8 projeções concorrentes do mesmo dispositivo; sequência de eventos SSE com duplicatas e reordenação | Revisões gravadas estritamente crescentes; o redutor do cliente nunca exibe revisão menor e termina na maior |

## 17. Métricas de ingestão

| Métrica | Tipo | Aviso (Grafana) | Page (Pushover) |
|---|---|---|---|
| `ingest_requests_total{route,status}`, `ingest_request_duration_seconds{route}` | contador, histograma | 4xx > 1% em 10 min; p95 > 500 ms em 5 min | — |
| `ingest_messages_total{kind,outcome}` (`processed`, `pending`, `quarantined`, `duplicate`) | contador | — | — |
| `ingest_quarantine_total{reason}` | contador | > 1% das mensagens em 10 min | `source_id_regression` ≥ 1 |
| `ingest_pending_oldest_age_seconds` (calculado pelo `api` a cada 15 s, funciona com o `worker` parado) | gauge | > 60 s | > 300 s |
| `ingest_last_received_age_seconds` | gauge | > 120 s com ≥ 1 sessão no Traccar | > 300 s |
| `ingest_lag_seconds` (`received_at − serverTime`) e `ingest_fix_age_seconds` (`received_at − fix_time`) | histograma | p95 lag > 5 s | — |
| `ingest_late_positions_total`, `ingest_compacted_total`, `ingest_jump_suspect_total`; `ingest_conflicting_duplicates_total` e `ingest_reconciled_missing_total` | contador | Os dois últimos: > 0 | — |

Logs: nunca coordenadas, IMEI completo, segredo ou payload ([03 REQ-ARQ-014](03-arquitetura.md)); o `correlationId` da ingestão é o id da inbox.

## 18. Requisitos

### REQ-ING-001 — Forward do Traccar configurado e versionado
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-01, INV-03
**Regra.** `infra/traccar/traccar.xml.tpl` DEVE conter as chaves do §2 com os valores da tabela, sem segredo; `render-config.sh` DEVE gerar `traccar.xml` no start a partir de `INGEST_SHARED_SECRET`. `processing.copyAttributes` NÃO DEVE ter valor.
**Aceite.** CT-ING-001 — Dado o contêiner `traccar` iniciado com `INGEST_SHARED_SECRET` de 40 caracteres, Quando se lê `/opt/traccar/conf/traccar.xml`, Então `forward.url` é `http://api:3001/internal/v1/traccar/positions`, `forward.header` contém o segredo, `database.registerUnknown` é `false`, e `git grep` do segredo no repositório retorna 0 ocorrências.

### REQ-ING-002 — Autenticação da origem
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N0 · **Invariantes:** INV-07
**Regra.** As rotas do §3 DEVEM exigir `X-Ingest-Token` igual a `INGEST_SHARED_SECRET`, comparado em tempo constante, antes de ler o corpo. Falha DEVE responder 401 sem gravar e sem logar o valor recebido.
**Aceite.** CT-ING-002 — Dado um corpo válido, Quando o POST chega com `X-Ingest-Token: errado`, Então a resposta é 401 em ≤ 100 ms, `ingest_inbox` continua com 0 linhas e nenhum log contém `errado`.

### REQ-ING-003 — Limite de tamanho e prazo
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-01
**Regra.** Corpo acima de 262.144 bytes DEVE receber 413. A requisição DEVE terminar em ≤ 5 s; sem commit nesse prazo, rollback e 503 com `Retry-After: 5`.
**Aceite.** CT-ING-003 — Dado um corpo de 262.145 bytes, Então 413 e 0 linhas na inbox; Dado um lock externo segurando `device_state` do dispositivo por 10 s, Quando a posição chega, Então a resposta é 202 `pending` em ≤ 2 s (lock_timeout de 1 s dentro do savepoint); Dado o `db` parado, Então 503 em ≤ 5 s.

### REQ-ING-004 — Envelope ilegível × semântica inválida
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-01
**Regra.** Envelope sem identidade extraível ou reprovado no schema DEVE receber 400 sem gravar. Envelope legível com semântica inválida (§6, §11) DEVE ser gravado como `quarantined` com código e responder 202.
**Aceite.** CT-ING-004 — Dado `{"device":{"id":17}}` sem `position`, Então 400 com `errors[0].path = "position"` e 0 linhas; Dado uma posição com `latitude = 91.2`, Então 202 `quarantined`, `error` começa com `invalid_coordinates` e `position` não ganha linha.

### REQ-ING-005 — Identidade de origem e dedupe
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-01
**Regra.** A ingestão DEVE aplicar o §5: chave `(source_instance, kind, source_event_id)`, `ON CONFLICT DO NOTHING`, duplicata sem efeito, conflito de hash medido.
**Aceite.** CT-ING-005 — Dado a posição `traccar-01/position/938441`, Quando ela é enviada 10 vezes, Então há 10 respostas 202 (1 `processed` e 9 `duplicate`), 1 linha na inbox, 1 em `position`, a revisão de `device_state` sobe 1 vez e a outbox ganha exatamente 2 eventos (1 `telemetry.position.accepted.v1` e 1 `device.state.updated.v1`).

### REQ-ING-006 — Unidades canônicas
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-12, INV-03
**Regra.** `normalizeTraccar` DEVE aplicar a tabela do §4 e ser o único ponto de conversão de unidade da ingestão.
**Aceite.** CT-ING-006 — Dado `speed = 10.0` (nós), `course = 359.6`, `hours = 3600000`, Quando normalizado, Então `speed_kmh_x10 = 185`, `speedKmh = 18.5` no evento, `course_deg = 0`, `aux.hoursS = 3600`; Dado `speed = 170.0` nós (314,8 km/h), Então `speed_kmh_x10` é NULL e a flag `SPEED_DISCARDED` (128) está ligada.

### REQ-ING-007 — Desconhecido não vira zero
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-03
**Regra.** Atributo ausente, perfil sem a capacidade ou valor inválido DEVEM resultar em NULL/`unknown`; a ausência NÃO DEVE apagar valor observado antes.
**Aceite.** CT-ING-007 — Dado um dispositivo novo e uma posição sem `ignition` nem `blocked`, Então `position.ignition` é NULL, `device_state.ignition` é NULL e `relay_state = 'unknown'`; Dado `device_state.ignition = true` e um heartbeat sem `ignition`, Então `device_state.ignition` continua `true`; Dado perfil com `ignition = "unknown"` e `attributes.ignition = false`, Então `position.ignition` é NULL.

### REQ-ING-008 — Dono resolvido no servidor pelo vínculo no tempo
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N0 · **Invariantes:** INV-06, INV-07
**Regra.** A operadora dona DEVE vir de `app.resolve_device_for_ingest`, e o cliente dono, do vínculo vigente em `p_at` lido sob RLS no escopo `operator` (§6, §7); ids de tenant no payload NÃO DEVEM ser lidos. Fato de vínculo encerrado DEVE ir só para o histórico do dono antigo.
**Aceite.** CT-ING-008 — Dado o dispositivo D vinculado ao cliente A1 até 2026-10-20T12:00:00Z e ao cliente A2 desde então, Quando chega posição de D com `fix_time = 2026-10-20T11:59:00Z` às 12:05, Então a linha em `position` tem `tenant_id` de A1 e flag `PREVIOUS_ASSIGNMENT` (512), e o `device_state` de A2 não muda; Dado IMEI sem `device`, Então quarentena `unknown_device`.

### REQ-ING-009 — Janela de tempo e WNRO
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-02, INV-06
**Regra.** `fix_time` fora de `[received_at − 30 dias, received_at + 120 s]` DEVE ir para quarentena com o código do §6; a correção WNRO só PODE ocorrer com `wnro_correction = true` no perfil.
**Aceite.** CT-ING-009 — Dado `received_at = 2026-10-20T15:20:00Z`, Quando chega `fix_time = 2007-03-06T15:20:00Z` com perfil `wnro_correction = false`, Então quarentena `wnro_suspect`; com `wnro_correction = true`, Então a linha tem `fix_time = 2026-10-20T15:20:00Z` e flag 64; Quando chega `fix_time = 2026-10-20T15:22:01Z`, Então quarentena `fix_time_in_future`; `fix_time = 2026-09-19T15:19:59Z`, Então `fix_time_too_old`.

### REQ-ING-010 — Projeção síncrona com savepoint
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-01, INV-05
**Regra.** A rota DEVE executar o §7: inbox e projeção na mesma transação; falha da projeção DEVE desfazer só o savepoint, deixando a inbox `pending`; 202 só após o commit.
**Aceite.** CT-ING-010 — Dado uma falha injetada no `INSERT` em `position`, Quando a posição chega, Então 202 `pending`, inbox `pending` com `attempts = 1` e `error` preenchido, 0 linhas em `position` e na outbox, nenhum NOTIFY recebido.
CT-ING-022 — Dado o processo `api` morto (SIGKILL) depois do INSERT na inbox e antes do COMMIT, Quando o Traccar reenvia a mesma posição ao `api` reiniciado, Então há 1 linha na inbox `processed` e 1 em `position`; Dado o processo morto após o COMMIT e antes da resposta, Quando há reenvio, Então a resposta é 202 `duplicate` e as contagens não mudam.

### REQ-ING-011 — Ordenação, revisão e atualidade
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-02, INV-04
**Regra.** A projeção DEVE aplicar o §8 sob `SELECT … FOR UPDATE` em `device_state`, com revisão da sequência global e desempate por `source_event_id`.
**Aceite.** CT-ING-011 — Dado o fix A (`fix_time = 15:10:00Z`, id 900, `serverTime = 15:10:02Z`) e o fix B (`fix_time = 15:00:00Z`, id 901, `serverTime = 15:10:05Z`, buffer offline), Quando B chega depois de A, Então `device_state.last_fix_at = 15:10:00Z` com as coordenadas de A, B está em `position` com flag `LATE` (1), `last_contact_at = 15:10:05Z`, e os campos de localização, status e contato de `device_state` são iguais aos obtidos na ordem B→A.

### REQ-ING-012 — Heartbeat e fix inválido
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-02, INV-03
**Regra.** Mensagem `outdated = true`, `valid = false` ou em (0, 0) NÃO DEVE gravar `position` nem mudar localização; DEVE atualizar contato e status conforme o §8.
**Aceite.** CT-ING-012 — Dado `device_state.last_fix_at = 14:00:00Z` e um heartbeat `outdated = true` com `serverTime = 15:00:00Z`, `fixTime = 14:00:00Z` e `ignition = false`, Então `last_contact_at = 15:00:00Z`, `last_fix_at` continua 14:00:00Z, `ignition = false`, `motion = 'stopped'`, e `position` não ganha linha.

### REQ-ING-013 — Compactação de parado
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-02
**Regra.** Fix válido parado DEVE ser gravado só nas condições do §9; os demais atualizam só `device_state`.
**Aceite.** CT-ING-013 — Dado a última posição gravada às 10:00:00Z em P0 (−5,0892110, −42,8018920) e o veículo parado, Quando chegam fixes parados a cada 300 s em P1 (−5,0895710, −42,8018920; 40 m de P0) até 10:35:00Z, Então só o fix de 10:30:00Z é gravado (flag 4); Quando chega às 10:36:00Z um fix parado em P2 (−5,0901110, −42,8018920; 60 m de P1), Então ele é gravado.

### REQ-ING-014 — Eventos de outbox da ingestão
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-01, INV-04
**Regra.** A projeção DEVE gravar `telemetry.position.accepted.v1` por posição gravada e `device.state.updated.v1` por revisão nova, com os campos do §10 validados pelo schema de `packages/contracts`, na mesma transação.
**Aceite.** CT-ING-014 — Dado um fix que liga a ignição (antes `false`), Quando projetado, Então o `device.state.updated.v1` tem `transitions.ignition = {"from": false, "to": true}`, `revision` igual à de `device_state` e `previousRevision` igual à anterior, e o payload passa no schema Zod.

### REQ-ING-015 — Reprocessamento e quarentena sem efeito externo
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-05
**Regra.** O worker DEVE reprocessar `pending` conforme o §11 e quarentenar na 5ª falha; reprocessamento de quarentena DEVE rodar em modo `reprocess`.
**Aceite.** CT-ING-015 — Dado uma falha permanente injetada na projeção, Quando o tempo passa, Então há 5 tentativas com esperas de ~2, 8, 32 e 120 s (± 25%), a linha termina `quarantined` com `projection_failed` e o fake de Pushover/Sentry recebe 1 aviso; Dado uma posição em quarentena `unknown_device` com `alarm = sos` reprocessada após o cadastro do dispositivo, Então `position` ganha a linha com flag 16 e o fake de FCM recebe 0 chamadas.

### REQ-ING-016 — Reconciliação e backfill
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-01, INV-05
**Regra.** O job `ingest.reconcile` DEVE comparar a janela do §12 com a inbox e projetar o que faltar em modo `backfill`; o CLI de backfill DEVE aceitar até 7 dias.
**Aceite.** CT-ING-016 — Dado o fake de Traccar com 120 posições do dispositivo D entre 10:00 e 11:00Z, das quais 30 nunca chegaram pelo forward, Quando `ingest.reconcile` roda às 11:25Z, Então a inbox passa a ter 120 linhas, as 30 novas têm flag 8, nenhum push é enviado, e uma segunda execução não cria linhas.

### REQ-ING-017 — Perfil de normalização
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-03
**Regra.** A normalização DEVE ler `capabilities.normalization` do perfil do dispositivo (§13); sem perfil, `generic-traccar/1`; capacidade `"unknown"` ou `"no"` DEVE ser tratada como ausente.
**Aceite.** CT-ING-017 — Dado um dispositivo sem `capability_profile_id` e `attributes.blocked = true`, Então `relay_state = 'unknown'`; Dado perfil J16 com `relay_state_reported = "yes"`, Então `relay_state = 'blocked'` e `relay_observed_at = observedAt`; Dado `power_source = 'charge'` e `charge = false`, Então `power_state = 'battery'`.

### REQ-ING-018 — Retenção da inbox
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-01
**Regra.** O job do §14 DEVE anular o payload após 7 dias, manter `payload_sha256` com a identidade e apagar a linha após 90 dias, em lotes (mesma regra de CT-DAD-013, [04](04-dominio-e-dados.md)).
**Aceite.** CT-ING-018 — Dado linhas com `received_at` há 6, 8 e 91 dias, Quando `ingest.retention` roda, Então a de 6 dias mantém o payload, a de 8 tem `payload` NULL e `payload_sha256` intacto, a de 91 não existe; e reenviar a chave da linha de 8 dias responde `duplicate`.

### REQ-ING-019 — Spike do J16 registrado como fixture
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-03, INV-12
**Regra.** A T-002 DEVE executar os cenários S01–S14 do §15, gravar fixtures anonimizadas e o manifesto, e preencher o perfil J16 `draft` com `evidence_ref` por capacidade.
**Aceite.** CT-ING-019 — Dado `packages/testkit/fixtures/j16/manifest.json`, Quando o teste de fixtures roda, Então cada cenário S01–S14 tem ≥ 1 arquivo ou o motivo `not_applicable`, nenhum arquivo contém IMEI diferente de `860000000000001`, e normalizar S03 dá velocidade média entre 27 e 33 km/h no trecho de 30 km/h.

### REQ-ING-020 — Propriedades INV-01 a INV-04
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-01, INV-02, INV-03, INV-04
**Regra.** O repositório DEVE conter P1–P4 do §16 no CI, nos dois níveis (puro e Postgres).
**Aceite.** CT-ING-020 — Dado o CI de um PR que remove o desempate por `source_event_id` do §8 (fix com `fix_time` igual ao atual passa a substituí-lo), Quando `pnpm test` roda, Então P2 falha com contraexemplo reduzido de 2 fixes com o mesmo `fix_time`.

### REQ-ING-021 — Métricas e alarmes de ingestão
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** —
**Regra.** `api` e `worker` DEVEM emitir as métricas do §17 com os limiares de aviso e page.
**Aceite.** CT-ING-021 — Dado o worker parado e uma falha injetada que deixa 1 linha `pending`, Quando passam 301 s, Então `ingest_pending_oldest_age_seconds > 300` e o fake de Pushover recebe 1 page.
