# T-015 — Consultas do G0 e relatório de evidências

| Campo | Valor |
|---|---|
| Fase | F0 (semana S4: 28–31/10/2026; avaliação do G0 em 31/10/2026 após 12:00 BRT) |
| Requisitos | REQ-NEG-010 (G0-1, G0-2 e G0-5 por consultas versionadas; avaliação dos 9 itens), REQ-NEG-016 (registro de evidências), REQ-ALR-015 (latência computável por consulta), REQ-NEG-017 (cortes registrados lidos pelo relatório), REQ-ING-016 (parte F0: reconciliação Traccar × inbox por id, consultas e relatório, só leitura; o job `ingest.reconcile` que projeta em modo `backfill`, o CLI de backfill e o CT-ING-016 são da T-028, F1 [ADOTADO NA v2.0]) |
| Invariantes | INV-01 (reconciliação Traccar × inbox prova ausência de perda e de duplicata), INV-03 (sem medida → `pendente`, nunca `ok`; entrega sem `originAt` não vira latência zero), INV-07 (consultas filtram a operadora e devolvem só agregados), INV-12 (UTC, segundos) |
| Risco de revisão | N2 (tabela 2.3 de [02](../docs/spec/02-escopo-e-fases.md)). Esta tarefa **não** cria tabela, função, política nem migration; se a implementação precisar de uma, pare e registre no PR (vira N0). A revisão confere que os `.sql` só leem e só devolvem agregados |
| Depende de | T-005, T-012. Usa artefatos já entregues: T-011 (`evidence.timings.originAt`), T-013 (relatório de restore e artefato `acceptance-report`), T-014 (seções do piloto no `G0.md` e `g0-markdown.ts`) |
| Estimativa | 2 sessões de agente (15a consultas, coletor e testes de SQL; 15b avaliação, relatório e testes) + ~1 h do fundador em 31/10 |
| Bloqueado por decisão | DEC-02 (limiar de lacuna = 2 × intervalo parado medido no spike; padrão 600 s [VALIDAR — DEC-02]) |
| Tipo | **Mista:** o agente entrega consultas, coletor, avaliador e testes; o fundador roda o coletor na VM, preenche os itens manuais e aprova o G0 mergeando o PR (REQ-NEG-016) |

## Objetivo

Tornar o G0 medível e reexecutável: quatro consultas SQL versionadas em `infra/scripts/gates/` (lacunas por rastreador, reconciliação com o Traccar por contagem e por id, e latência de alerta), um coletor que as roda na VM e guarda só agregados, e um relatório que lê essas saídas, as seções do `G0.md` (piloto, termos, lacunas explicadas, cortes), o relatório de restore e o resultado do CI, avalia os itens G0-1 a G0-9 com as regras de [02 §2.5](../docs/spec/02-escopo-e-fases.md) e reescreve a tabela de itens do `docs/runbooks/gates/G0.md` no formato de [02 §10](../docs/spec/02-escopo-e-fases.md). Gate aprovado = 9 itens `ok`; só o fundador aprova.

## Contexto obrigatório

- [02 §2.4, §2.5, §10 e REQ-NEG-010, REQ-NEG-016, REQ-NEG-017](../docs/spec/02-escopo-e-fases.md).
- [07 §10](../docs/spec/07-alertas-e-tempo-real.md): marcos t0–t4 e consulta de referência do p95.
- [05 §12](../docs/spec/05-ingestao-e-telemetria.md) item 1 e REQ-ING-016: janela de reconciliação (`now − 80 min` a `now − 20 min`) e identidade `(source_instance, kind, source_event_id)` (INV-01).
- [T-013](T-013-deploy-backup-restore-sondas.md) (front matter do relatório de restore; artefato `acceptance-report`) e [T-014](T-014-migracao-manual-sms-e-rollback.md) (seções `## Migração do piloto` e `## Termos de participação (G0-9)`).

## Escopo — fazer

1. As 4 consultas SQL da seção 1 (lacunas, reconciliação por contagem, reconciliação por id e latência) e o renderizador de variáveis psql para testes (`packages/testkit/src/psql-vars.ts`).
2. Coletor `infra/scripts/gates/g0-collect.sh` (seção 2), com o modo `--recent` que roda só a reconciliação na janela de [05 §12](../docs/spec/05-ingestao-e-telemetria.md) (REQ-ING-016, parte F0), para o fundador conferir perda no forward durante o piloto.
3. Avaliador puro `evaluateG0` e esquemas Zod em `packages/domain/src/gates/g0.ts` (seção 3).
4. Extensão de `g0-markdown.ts` (itens, lacunas explicadas, cortes) e CLI `pnpm gates:g0` (seção 4).
5. `G0.md` com as seções que faltam, `evidencias/g0/manual.json` modelo e roteiro manual de G0-3/G0-4 (seção 5).
6. Testes de aceite em `tests/acceptance/T-015/`.

## Fora do escopo

- Funções `ops.*` `SECURITY DEFINER`, métrica de minuto ruim e SLO mensal: F1 ([13 §10](../docs/spec/13-infra-e-operacao.md)).
- Bloqueio técnico da criação de onda antes do G0 (onda é F1); `G-CMD.md`, `G1.md`, `G2.md`.
- Executar o restore (T-013), migrar veículos (T-014) ou provocar alertas (roteiro do fundador).
- Projetar posição faltante (job `ingest.reconcile` em modo `backfill`, CLI `ingest:backfill`, métrica `ingest_reconciled_missing_total`) e o CT-ING-016: T-028 (F1). Aqui a reconciliação só lê e relata; nada é gravado no banco.

## Arquivos a criar/alterar

```
infra/scripts/gates/g0-lacunas.sql
infra/scripts/gates/g0-reconciliacao.sql
infra/scripts/gates/g0-reconciliacao-ids.sql
infra/scripts/gates/g0-latencia-alerta.sql
infra/scripts/gates/g0-collect.sh                 (executável)
infra/scripts/gates/g0-report.ts                  (CLI; roda com tsx)
packages/domain/src/gates/g0.ts
packages/domain/src/gates/g0-markdown.ts          (alterar: criado na T-014)
packages/domain/src/index.ts                      (alterar)
packages/testkit/src/psql-vars.ts
package.json                                      (alterar: "gates:g0": "tsx infra/scripts/gates/g0-report.ts")
docs/runbooks/gates/G0.md                         (alterar: ## Itens com marcadores, ## Lacunas explicadas, ## Cortes)
docs/runbooks/gates/evidencias/g0/manual.json     (modelo, itens `pendente`)
docs/runbooks/gates/g0-roteiro-manual.md
tests/acceptance/T-015/{queries,evaluate,markdown,report-cli}.test.ts
tests/acceptance/T-015/fixtures/**                (G0.md, evidências, restore, acceptance-report.json, manual.json)
```

## Especificação detalhada

### (1) Consultas versionadas — SQL exato

Variáveis no estilo psql `:'nome'`; cada arquivo devolve **um** valor JSON (`psql -At`). Identificação do veículo = IMEI mascarado (`***` + 4 últimos), igual à T-014. Mensagem atribuída ao rastreador pelo `payload.device.id` do envelope do Traccar (T-005); por isso o coletor roda dentro dos 7 dias do `historyDays` do Traccar. (No F0 o payload da inbox fica além de 7 dias, porque a retenção foi adiada para a T-027; o limite prático é o do Traccar.)

`infra/scripts/gates/g0-lacunas.sql` (G0-1):

```sql
-- T-015 · G0-1 (02 §2.5): maior intervalo entre mensagens consecutivas por rastreador do piloto. Só agregados.
-- Variáveis: operator_id (uuid), source_instance, from, to (RFC 3339), gap_threshold_s (inteiro).
WITH params AS (
  SELECT :'operator_id'::uuid AS operator_id, :'source_instance'::text AS source_instance,
         :'from'::timestamptz AS t_from, :'to'::timestamptz AS t_to, :'gap_threshold_s'::integer AS threshold_s
), pilot AS (
  SELECT DISTINCT d.id AS device_id, d.traccar_device_id, '***' || right(d.imei, 4) AS vehicle
  FROM params p
  JOIN app.device d ON d.operator_id = p.operator_id AND d.traccar_device_id IS NOT NULL
  JOIN app.device_assignment a ON a.operator_id = d.operator_id AND a.device_id = d.id AND a.is_primary
   AND tstzrange(a.valid_from, a.valid_to, '[)') && tstzrange(p.t_from, p.t_to, '[)')
), msgs AS (
  SELECT pl.device_id, x.msg_at
  FROM params p
  JOIN app.ingest_inbox i ON i.source_instance = p.source_instance
   AND i.received_at >= p.t_from - interval '1 hour' AND i.received_at < p.t_to + interval '1 hour'
  JOIN pilot pl ON i.payload #>> '{device,id}' = pl.traccar_device_id::text
  CROSS JOIN LATERAL (SELECT CASE WHEN i.payload #>> '{position,serverTime}' ~ '^\d{4}-\d{2}-\d{2}T'
    THEN (i.payload #>> '{position,serverTime}')::timestamptz ELSE i.received_at END AS msg_at) x
  WHERE x.msg_at >= p.t_from AND x.msg_at < p.t_to
), points AS (
  SELECT device_id, msg_at AS at FROM msgs
  UNION ALL SELECT pl.device_id, p.t_from FROM pilot pl CROSS JOIN params p
  UNION ALL SELECT pl.device_id, p.t_to FROM pilot pl CROSS JOIN params p
), gaps AS (
  SELECT device_id, at AS gap_start, lead(at) OVER (PARTITION BY device_id ORDER BY at) AS gap_end FROM points
), per_device AS (
  SELECT pl.vehicle,
    (SELECT count(*) FROM msgs m WHERE m.device_id = pl.device_id) AS messages,
    (SELECT coalesce(max(extract(epoch FROM g.gap_end - g.gap_start)), 0)::integer
       FROM gaps g WHERE g.device_id = pl.device_id AND g.gap_end IS NOT NULL) AS max_gap_s,
    (SELECT coalesce(json_agg(json_build_object(
        'start', to_char(g.gap_start AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        'end', to_char(g.gap_end AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        'seconds', extract(epoch FROM g.gap_end - g.gap_start)::integer) ORDER BY g.gap_start), '[]'::json)
       FROM gaps g CROSS JOIN params p
      WHERE g.device_id = pl.device_id AND g.gap_end IS NOT NULL
        AND extract(epoch FROM g.gap_end - g.gap_start) > p.threshold_s) AS gaps
  FROM pilot pl
)
SELECT json_build_object(
  'window', json_build_object('from', to_char(p.t_from AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                              'to', to_char(p.t_to AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')),
  'thresholdSeconds', p.threshold_s,
  'devices', coalesce((SELECT json_agg(json_build_object('vehicle', vehicle, 'messages', messages,
      'maxGapSeconds', max_gap_s, 'gaps', gaps) ORDER BY vehicle) FROM per_device), '[]'::json))
FROM params p;
```

`infra/scripts/gates/g0-reconciliacao.sql` (G0-2; o coletor acrescenta `traccar` por rastreador):

```sql
-- T-015 · G0-2: posições na inbox por rastreador (kind = 'position', fixTime na janela) e estado da fila.
-- Variáveis: operator_id, source_instance, from, to. Só agregados.
WITH params AS (
  SELECT :'operator_id'::uuid AS operator_id, :'source_instance'::text AS source_instance,
         :'from'::timestamptz AS t_from, :'to'::timestamptz AS t_to
), pilot AS (
  SELECT DISTINCT d.id AS device_id, d.traccar_device_id, '***' || right(d.imei, 4) AS vehicle
  FROM params p
  JOIN app.device d ON d.operator_id = p.operator_id AND d.traccar_device_id IS NOT NULL
  JOIN app.device_assignment a ON a.operator_id = d.operator_id AND a.device_id = d.id AND a.is_primary
   AND tstzrange(a.valid_from, a.valid_to, '[)') && tstzrange(p.t_from, p.t_to, '[)')
), inbox AS (
  SELECT pl.device_id, i.status, nullif(split_part(coalesce(i.error, ''), ':', 1), '') AS reason
  FROM params p
  JOIN app.ingest_inbox i ON i.source_instance = p.source_instance AND i.kind = 'position'
   AND i.received_at >= p.t_from - interval '5 minutes'
  JOIN pilot pl ON i.payload #>> '{device,id}' = pl.traccar_device_id::text
  WHERE i.payload #>> '{position,fixTime}' ~ '^\d{4}-\d{2}-\d{2}T'
    AND (i.payload #>> '{position,fixTime}')::timestamptz >= p.t_from
    AND (i.payload #>> '{position,fixTime}')::timestamptz < p.t_to
), per_device AS (
  SELECT pl.vehicle, pl.traccar_device_id, count(x.status) AS inbox,
    count(*) FILTER (WHERE x.status = 'processed') AS processed,
    count(*) FILTER (WHERE x.status = 'quarantined') AS quarantined,
    count(*) FILTER (WHERE x.status = 'quarantined' AND x.reason IS NULL) AS quarantined_without_reason
  FROM pilot pl LEFT JOIN inbox x ON x.device_id = pl.device_id
  GROUP BY pl.vehicle, pl.traccar_device_id
), reasons AS (
  SELECT pl.vehicle, json_object_agg(r.reason, r.n) AS by_reason
  FROM (SELECT device_id, reason, count(*) AS n FROM inbox
        WHERE status = 'quarantined' AND reason IS NOT NULL GROUP BY device_id, reason) r
  JOIN pilot pl ON pl.device_id = r.device_id
  GROUP BY pl.vehicle
)
SELECT json_build_object(
  'devices', coalesce((SELECT json_agg(json_build_object('vehicle', d.vehicle, 'traccarDeviceId', d.traccar_device_id,
      'inbox', d.inbox, 'processed', d.processed, 'quarantined', d.quarantined,
      'quarantinedWithoutReason', d.quarantined_without_reason,
      'quarantineReasons', coalesce(r.by_reason, '{}'::json)) ORDER BY d.vehicle)
    FROM per_device d LEFT JOIN reasons r ON r.vehicle = d.vehicle), '[]'::json),
  'failed', (SELECT count(*) FROM app.ingest_inbox i WHERE i.source_instance = p.source_instance
     AND i.status = 'failed' AND i.received_at >= p.t_from AND i.received_at < p.t_to),
  'pendingOver5Min', (SELECT count(*) FROM app.ingest_inbox i WHERE i.source_instance = p.source_instance
     AND i.status = 'pending' AND i.received_at >= p.t_from AND i.received_at < least(p.t_to, now() - interval '5 minutes')))
FROM params p;
```

`infra/scripts/gates/g0-reconciliacao-ids.sql` (G0-2 e REQ-ING-016, parte F0; uma execução por rastreador, com os ids de posição que o Traccar devolveu na janela):

```sql
-- T-015 · REQ-ING-016 (parte F0) e G0-2: ids de posição do Traccar ausentes na inbox. Só contagens e até 5 ids de amostra.
-- Variáveis: source_instance, traccar_device_id (bigint), traccar_ids (array bigint; '{}' = nenhum).
WITH params AS (
  SELECT :'source_instance'::text AS source_instance, :'traccar_device_id'::bigint AS traccar_device_id,
         :'traccar_ids'::bigint[] AS ids
), t AS (
  SELECT DISTINCT unnest(p.ids) AS id FROM params p
), found AS (
  SELECT t.id FROM t CROSS JOIN params p
  WHERE EXISTS (SELECT 1 FROM app.ingest_inbox i
                 WHERE i.source_instance = p.source_instance AND i.kind = 'position'
                   AND i.source_event_id = t.id::text)
)
SELECT json_build_object(
  'traccarDeviceId', p.traccar_device_id,
  'traccar', (SELECT count(*) FROM t),
  'matched', (SELECT count(*) FROM found),
  'missingFromInbox', (SELECT count(*) FROM t) - (SELECT count(*) FROM found),
  'missingSample', coalesce((SELECT json_agg(m.id ORDER BY m.id)
      FROM (SELECT id FROM t EXCEPT SELECT id FROM found ORDER BY id LIMIT 5) m), '[]'::json))
FROM params p;
```

Usa o índice único `ingest_inbox_identity_key` (INV-01). Ids de posição do Traccar não são dado pessoal; nenhum IMEI, coordenada ou payload sai da consulta.

`infra/scripts/gates/g0-latencia-alerta.sql` (G0-5; mesma definição de [07 §10](../docs/spec/07-alertas-e-tempo-real.md), por entrega como em G0-5):

```sql
-- T-015 · G0-5: latência t4 − t0 (sent_at − evidence.timings.originAt) por entrega 'sent' na janela. Só agregados.
-- Variáveis: from, to, operator_ids (array uuid; '{}' = todas).
WITH params AS (
  SELECT :'from'::timestamptz AS t_from, :'to'::timestamptz AS t_to, :'operator_ids'::uuid[] AS operator_ids
), sent AS (
  SELECT a.type, a.evidence #>> '{timings,originAt}' AS origin_txt, dl.sent_at
  FROM params p
  JOIN app.alert_delivery dl ON dl.status = 'sent' AND dl.sent_at >= p.t_from AND dl.sent_at < p.t_to
   AND (cardinality(p.operator_ids) = 0 OR dl.operator_id = ANY (p.operator_ids))
  JOIN app.alert a ON a.operator_id = dl.operator_id AND a.tenant_id = dl.tenant_id AND a.id = dl.alert_id
  WHERE coalesce(a.evidence ->> 'processingMode', 'live') NOT IN ('reprocess', 'replay', 'backfill')
), d AS (
  SELECT type, extract(epoch FROM sent_at - origin_txt::timestamptz)::double precision AS latency_s
  FROM sent WHERE origin_txt ~ '^\d{4}-\d{2}-\d{2}T'
)
SELECT json_build_object(
  'deliveries', (SELECT count(*) FROM d),
  'withoutOrigin', (SELECT count(*) FROM sent WHERE origin_txt IS NULL OR origin_txt !~ '^\d{4}-\d{2}-\d{2}T'),
  'p50Seconds', (SELECT round(percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_s)::numeric, 1) FROM d),
  'p95Seconds', (SELECT round(percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_s)::numeric, 1) FROM d),
  'maxSeconds', (SELECT round(max(latency_s)::numeric, 1) FROM d),
  'byType', coalesce((SELECT json_object_agg(type, n) FROM (SELECT type, count(*) AS n FROM d GROUP BY type) t), '{}'::json));
```

`packages/testkit/src/psql-vars.ts`: `renderPsqlVars(sql, vars)` troca cada `:'nome'` por literal SQL (aspas simples duplicadas), como o psql faz; variável sem valor → erro; usado só pelos testes.

### (2) Coletor — `g0-collect.sh` (na VM, como root pela Tailscale)

`g0-collect.sh --operator <uuid> --from <RFC 3339 Z> --to <RFC 3339 Z> [--gap-threshold-s 600] [--alert-operators <uuid,uuid>] [--out /var/lib/tracksys/gates/g0]`:
1. Valida argumentos (uuid, `Z`, `from < to`); janela ≠ 48 h imprime "janela ≠ 48 h: só ensaio". Lê `INGEST_SOURCE_INSTANCE`, `TRACCAR_API_USER` e `TRACCAR_API_PASSWORD` de `/run/tracksys/prod.env` sem ecoar.
2. Para cada `.sql`: `docker compose -f /opt/tracksys/infra/docker-compose.yml exec -T -u postgres -e PGOPTIONS='-c default_transaction_read_only=on -c statement_timeout=120s -c TimeZone=UTC' db psql -X -At -v ON_ERROR_STOP=1 -d tracksys -v operator_id=… -v source_instance=… -v from=… -v to=… [-v gap_threshold_s=… | -v operator_ids='{…}'] -f - < arquivo`. `--alert-operators` ausente = `{<operator>}`; o fundador acrescenta a operadora da bancada quando os alertas provocados saíram do J16 de bancada.
3. Para cada `traccarDeviceId`: `GET http://172.30.0.6:8082/api/positions?deviceId=<id>&from=<from>&to=<to>` com `Accept: application/json` e credencial passada por `curl -K -` (nunca na linha de comando); da resposta só se extraem os ids (`jq -c '[.[].id]'`, convertidos para `{…}`), e o resto é descartado sem ir a disco; roda `g0-reconciliacao-ids.sql` com `-v traccar_device_id=<id> -v traccar_ids='{…}'` (ids acima de 100 KB vão por arquivo temporário em `/run/tracksys`, modo 0600, apagado no fim) e acrescenta `traccar`, `matched`, `missingFromInbox` e `missingSample` ao rastreador em `reconciliacao.json` [VALIDAR — DEC-02: o Traccar filtra por `fixTime`].
   - **Modo `--recent`** (REQ-ING-016, parte F0): `g0-collect.sh --operator <uuid> --recent` usa `from = now − 80 min` e `to = now − 20 min` arredondados ao minuto ([05 §12](../docs/spec/05-ingestao-e-telemetria.md) item 1), roda só a reconciliação (contagem e ids), grava `reconciliacao.json` e `meta.json` com `mode: "recent"` e imprime `N rastreadores; M posições ausentes na inbox`; sai 3 se `M > 0`. Nada é gravado no banco; a recuperação é o backfill da T-028 (F1) ou, no F0, a lacuna explicada.
4. Grava em `<out>/<AAAAMMDDTHHMMZ>/`: `lacunas.json`, `reconciliacao.json`, `latencia.json` e `meta.json` (`window`, `thresholdSeconds`, `sourceInstance`, `operatorId`, `alertOperatorIds`, `deployedTag` de `/etc/tracksys/current-version`, `generatedAt`, `sqlSha256` por arquivo). Imprime só o diretório e totais. Dois IMEIs mascarados iguais no piloto → `exit 2` "colisão de IMEI mascarado".

O fundador copia o diretório para `docs/runbooks/gates/evidencias/g0/` (`scp` pela Tailscale) e commita.

### (3) Avaliação — `packages/domain/src/gates/g0.ts`

`evaluateG0(input: G0Input, ctx: {date: 'DD/MM/AAAA', verifiedBy: string}): {items: G0Item[], approved: boolean, status: 'aprovado' | 'reprovado' | 'pendente'}`; `G0Item = {id, criterion, measure, result: 'ok' | 'falhou' | 'pendente', evidence, date, verifiedBy}`. `G0Input` (Zod): `window`, `gaps?` (= `lacunas.json`), `explainedGaps[]`, `reconciliation?` (com `traccar`), `latency?`, `activeAlertTypes[]`, `ci?` (`{runUrl, tag, total, failed, skipped, files[]}`), `restore?` (front matter da T-013), `pilotLog[]` e `terms[]` (T-014), `cuts: number[]`, `manual: {g0_3?, g0_4?}` (`{result, evidence: {android?, ios?}, verifiedBy, date}`). Ausente → item `pendente`.

| Item | `ok` quando | `falhou` quando | `pendente` quando |
|---|---|---|---|
| G0-1 | Janela ≥ 172.800 s; toda lacuna de `gaps` coberta por linha de `## Lacunas explicadas` (mesmo veículo, início ≤ lacuna + 60 s, fim ≥ fim da lacuna − 60 s, causa e evidência não vazias); ≥ 5 veículos com `messages > 0` | Alguma lacuna acima do limiar sem causa, ou < 5 veículos | Sem `gaps`; janela < 48 h |
| G0-2 | Por veículo `traccar = inbox`, `missingFromInbox = 0` e `quarantinedWithoutReason = 0`; `failed = 0`; `pendingOver5Min = 0` | Qualquer condição violada | Sem `reconciliation` ou rastreador sem `missingFromInbox` |
| G0-3, G0-4 | `manual.result = ok` com `evidence.android` e (`evidence.ios` ou corte 6 em `cuts`) | `manual.result = falhou` | Sem registro; `ok` sem vídeo exigido |
| G0-5 | `withoutOrigin = 0`, `p95Seconds ≤ 60`, `deliveries ≥ 20` e `byType` com ≥ 1 de cada `activeAlertTypes` | `withoutOrigin > 0` ou `p95Seconds > 60` (avaliados antes da amostra) | Sem `latency`; amostra < 20; tipo ativo sem entrega |
| G0-6 | `failed = 0`, `skipped = 0` e `files` com caminhos em `tests/acceptance/T-001/`, `T-005/`, `T-006/` e `T-008/` (a metade HTTP/SSE do CT-NEG-017 está na T-008, [02 §3](../docs/spec/02-escopo-e-fases.md)) | `failed > 0`, `skipped > 0` ou suíte ausente | Sem `ci` |
| G0-7 | `durationSeconds ≤ 7200`, `lossSeconds ≤ 300`, `countsMatch`, `catalogOk`, `externalCalls = 0` | Qualquer condição violada | Sem `restore` |
| G0-8 | Linha `rollback` `de volta no tracker-net` com duração ≤ 600 s **e** linha `migrar` `migrado` posterior do mesmo veículo | Só há rollback acima de 600 s ou `não voltou` | Nenhuma linha `rollback` |
| G0-9 | Todo veículo com linha `migrar` aparece num termo com `Assinado em` anterior ao 1º SMS dele | Algum SMS antes do termo, ou veículo sem termo | Nenhuma linha `migrar` |

`approved` = 9 `ok`; `status` = `reprovado` se algum `falhou`, senão `pendente` se algum `pendente`, senão `aprovado`. Medidas (texto exato, decimal com vírgula, durações por `formatElapsed` da T-014 e `H h M min` acima de 1 h): G0-1 `6 veículos; maior lacuna sem causa: 7 min` (maior lacuna não explicada entre os veículos) ou `6 veículos; 2 lacunas sem causa (maior: 30 min)`; G0-2 `6 veículos; 0 divergência; 0 failed; 0 pending > 5 min; 21 quarantined com motivo`; G0-5 `34 entregas; p95 = 41 s` ou `34 entregas; p95 = 75 s (limite 60 s)` ou `amostra insuficiente: 12 < 20` ou `falta alerta provocado: power_cut`; G0-6 `412 testes; 0 falha; 0 pulado (tag v0.9.0)`; G0-7 `restore em 1 h 20 min; perda 3 min`; G0-8 `rollback em 6 min; veículo migrado de novo`; G0-9 `6 termos; 6 titulares; 0 SMS antes do termo`. Critérios fixos: os textos da coluna "Critério" de [02 §2.5](../docs/spec/02-escopo-e-fases.md) resumidos como no modelo de §10.

### (4) Relatório — `pnpm gates:g0`

`pnpm gates:g0 --evidence <dir> [--g0 docs/runbooks/gates/G0.md] [--restore <arquivo.md>] [--ci-report <acceptance-report.json>] [--manual <manual.json>] [--date DD/MM/AAAA] [--verified-by gates:g0] [--check]`:
- Lê os JSON do coletor, o front matter do restore, o JSON do Vitest (`numFailedTests`, `numPendingTests + numTodoTests`, `testResults[].name`) [VALIDAR formato na versão fixada], o `manual.json` (`activeAlertTypes`, `ci.runUrl`, `ci.tag`, `g0_3`, `g0_4`) e as seções do `G0.md`.
- Reescreve só o trecho entre `<!-- g0:itens:inicio -->` e `<!-- g0:itens:fim -->` com a tabela `| Item | Critério | Medida obtida | Resultado | Evidência | Data | Verificado por |` (G0-1 a G0-9, nessa ordem); itens G0-3/G0-4 levam `verifiedBy` e data do `manual.json`. Segunda execução com as mesmas entradas não altera o arquivo.
- Imprime `G0: aprovado`, `G0: reprovado (G0-5 falhou)` ou `G0: pendente (G0-7 pendente)` (ids não `ok` separados por vírgula). `--check` não escreve e sai 0 só com `aprovado` e a tabela do arquivo igual à calculada; senão sai 1. Entrada inválida (Zod) → sai 2 citando o arquivo e o campo.

### (5) `G0.md` e roteiro manual

`g0-markdown.ts` ganha `renderItemsBlock`, `parseExplainedGaps` e `parseCuts`. Seções criadas se ausentes (nada é apagado; as da T-014 ficam como estão):

```markdown
## Itens

<!-- g0:itens:inicio -->
<!-- g0:itens:fim -->

## Cortes

- Corte 6 aplicado em 27/10/2026 18:00 BRT: G0 só com Android (DEC-03 atrasou).

## Lacunas explicadas

| Veículo | Início (UTC) | Fim (UTC) | Causa | Evidência |
|---|---|---|---|---|
| ***0025 | 2026-10-30T02:10:00Z | 2026-10-30T05:40:00Z | Garagem subterrânea sem sinal (titular confirmou) | WhatsApp da Lider 30/10 08:12 |
```

`parseCuts` aceita linhas `- Corte <n> …` (REQ-NEG-017). `docs/runbooks/gates/g0-roteiro-manual.md`: passos de G0-3 e G0-4 de [02 §2.5](../docs/spec/02-escopo-e-fases.md) com 2 contas `tenant_owner` de clientes diferentes, vídeo ≤ 2 min por plataforma, link guardado fora do git quando mostrar dado pessoal, e como preencher `manual.json`. Roteiro do fundador em 31/10: `g0-collect.sh --operator <Lider> --from 2026-10-29T15:00:00Z --to 2026-10-31T15:00:00Z` (12:00 BRT = 15:00Z) → copiar evidências → `gh run download <run do deploy da tag implantada> -n acceptance-report` → `pnpm gates:g0 …` → PR de aprovação com `pnpm gates:g0 --check` verde.

## Testes de aceite (congelados)

`tests/acceptance/T-015/` (CI; banco real; datas no dia UTC anterior ao da execução, mantendo as horas; `source_instance = traccar-t015-<aleatório>`; seed com o pool admin do testkit, como as fixtures da T-001; consultas rodadas por `renderPsqlVars` dentro de `BEGIN READ ONLY`):

- `queries.test.ts` — Janela `D−1 15:00:00Z` a `D−1 16:00:00Z`, limiar 600, operadora L nova com 3 rastreadores `***0017`, `***0025`, `***0033` vinculados (vínculo primário aberto antes da janela), 1 rastreador da Beta com mensagens e 1 de L com vínculo encerrado em `D−1 14:00Z`. Os blocos G0-1 e G0-2 usam `source_instance` próprias (as linhas de um não entram no outro). Valores conferidos em PostgreSQL 16 em 08/10/2026 com o SQL desta seção.
  - G0-1: `***0017` com posições a cada 60 s de 15:00:00 a 15:59:00 sem 15:21–15:26 e 1 evento sem `serverTime` recebido às 15:24:00 → `{vehicle: "***0017", messages: 55, maxGapSeconds: 240, gaps: []}`; `***0025` de 15:00:00 a 15:30:00 → `messages: 31`, `maxGapSeconds: 1800`, `gaps: [{start: "<D−1>T15:30:00Z", end: "<D−1>T16:00:00Z", seconds: 1800}]`; `***0033` sem mensagem → `messages: 0`, `maxGapSeconds: 3600`, 1 lacuna de 3600; a Beta e o vínculo encerrado não aparecem; `devices` em ordem de veículo.
  - G0-2: `***0017` com 10 posições de `fixTime` na janela (8 `processed`, 1 `quarantined` com `error = 'invalid_coordinates: latitude fora da faixa'`, 1 `quarantined` com `error` nulo), 1 com `fixTime` em 14:59:59 e 1 `event` → `inbox: 10, processed: 8, quarantined: 2, quarantinedWithoutReason: 1, quarantineReasons: {"invalid_coordinates": 1}`; 1 linha `failed` recebida às 15:10 → `failed: 1`; 1 `pending` recebida às 15:20 → `pendingOver5Min: 1`; linhas de outra `source_instance` não contam.
  - G0-5: 21 entregas `sent` de L com latências de 10 a 30 s (18 `ignition_on`, 3 `offline`) → `deliveries: 21, p50Seconds: 20.0, p95Seconds: 29.0, maxSeconds: 30.0, byType: {"ignition_on": 18, "offline": 3}`; mais 1 `reprocess`, 1 `failed`, 1 fora da janela e 1 da Beta (filtrada por `operator_ids = {L}`) que não contam; 1 `sent` sem `originAt` → `withoutOrigin: 1`.
  - Reconciliação por id (REQ-ING-016, parte F0): `***0017` com `traccar_ids = {1001,…,1010}` e a inbox da mesma `source_instance` com `source_event_id` 1001 a 1008 `processed` e 1009 `pending` (1010 nunca chegou; 1010 existe só em outra `source_instance`) → `{traccar: 10, matched: 9, missingFromInbox: 1, missingSample: [1010]}`; ids repetidos no array contam uma vez; `traccar_ids = '{}'` → `{traccar: 0, matched: 0, missingFromInbox: 0, missingSample: []}`. Depois da consulta, `count(*)` de `app.ingest_inbox` é o mesmo de antes (nada gravado).
  - Estático: os 4 arquivos não contêm `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER`, `DROP`, `GRANT`, `TRUNCATE` nem `COPY` fora de comentários; as variáveis usadas são exatamente as listadas no cabeçalho de cada arquivo.
- `evaluate.test.ts` — CT-NEG-010: janela `2026-10-29T15:00:00Z`–`2026-10-31T15:00:00Z`, 6 veículos com maior lacuna de 420 s e `gaps` vazios, reconciliação sem divergência, 34 entregas com p95 = 41 s cobrindo os 4 tipos ativos, CI com 0 falha e 0 pulado nas suítes T-001/T-005/T-006/T-008, restore de 4.800 s com perda de 180 s, rollback de 360 s seguido de nova migração, 6 termos anteriores aos SMS e G0-3/G0-4 `ok` com vídeos → 9 itens `ok`, `approved = true`, `status = 'aprovado'`, medidas `6 veículos; maior lacuna sem causa: 7 min`, `34 entregas; p95 = 41 s`, `restore em 1 h 20 min; perda 3 min`, `rollback em 6 min; veículo migrado de novo`. CT-NEG-011: o mesmo com p95 = 75 s → G0-5 `falhou` com `34 entregas; p95 = 75 s (limite 60 s)` e `status = 'reprovado'`. CT-NEG-019: o mesmo sem `restore` → G0-7 `pendente`, 8 `ok`, `approved = false`, `status = 'pendente'`. Bordas: `missingFromInbox = 1` num veículo com `traccar = inbox` (uma perda compensada por uma duplicata na contagem) → G0-2 `falhou` com `1 divergência`; `files` sem `tests/acceptance/T-008/` → G0-6 `falhou`; lacuna de 1.800 s explicada → G0-1 `ok`; não explicada → `falhou`; janela de 36 h → `pendente`; `power_cut` ativo sem entrega → G0-5 `pendente`; termo assinado depois do SMS → G0-9 `falhou`; rollback de 660 s → G0-8 `falhou`; G0-3 `ok` sem vídeo do iPhone e sem corte 6 → `pendente`, com corte 6 → `ok`.
- `markdown.test.ts` — `parseExplainedGaps` e `parseCuts` sobre `fixtures/G0.md` devolvem 1 lacuna de `***0025` e `[6]`; `renderItemsBlock` troca só o trecho entre os marcadores (resto idêntico, byte a byte); arquivo sem as seções ganha `## Itens`, `## Cortes` e `## Lacunas explicadas` sem perder as seções da T-014 nem as demonstrações registradas pela T-005, T-008 e T-012 ([02 §2.3](../docs/spec/02-escopo-e-fases.md), "Donos de fronteira").
- `report-cli.test.ts` — Dado `fixtures/caso-aprovado/` (cópia de `G0.md`, evidências, restore, `acceptance-report.json` e `manual.json` do CT-NEG-010), Quando `pnpm gates:g0 --evidence … --g0 <cópia temporária> …`, Então sai 0, imprime `G0: aprovado` e a tabela tem 9 linhas `ok`; Quando roda de novo, Então o arquivo não muda; Quando `--check`, Então sai 0. Dado `fixtures/caso-sem-restore/`, Então imprime `G0: pendente (G0-7 pendente)` e `--check` sai 1. Dado `latencia.json` sem `p95Seconds`, Então sai 2 citando `latencia.json`. `g0-collect.sh --recent` com fakes de `docker`, `curl` e `date` (fixado em `D 12:00:00Z`) → chama o Traccar com `from=D 10:40:00Z` e `to=D 11:40:00Z`, não roda `g0-lacunas.sql` nem `g0-latencia-alerta.sql`, grava `meta.json` com `mode: "recent"` e sai 3 quando o fake de `psql` devolve `missingFromInbox: 2`.

## Comandos de verificação

```bash
pnpm install
pnpm lint && pnpm typecheck
pnpm db:up && pnpm db:migrate && pnpm db:check
pnpm test:acceptance -- tests/acceptance/T-015
docker run --rm -v "$PWD/infra":/infra koalaman/shellcheck:v0.10.0 /infra/scripts/gates/g0-collect.sh
pnpm gates:g0 --evidence tests/acceptance/T-015/fixtures/caso-aprovado/evidencias --g0 "$(mktemp -d)/G0.md" --manual tests/acceptance/T-015/fixtures/caso-aprovado/manual.json --restore tests/acceptance/T-015/fixtures/caso-aprovado/restore.md --ci-report tests/acceptance/T-015/fixtures/caso-aprovado/acceptance-report.json
pnpm verify
```

## Definição de pronto

- [ ] Testes da T-015 verdes; `pnpm verify` verde no PR.
- [ ] Ensaio do coletor na VM em 28/10 com janela de 6 h (J16 de bancada + veículo de 22/10), saída anexada ao PR.
- [ ] Em 31/10, evidências do G0 em `docs/runbooks/gates/evidencias/g0/` e tabela de itens gerada; PR de aprovação do fundador com `pnpm gates:g0 --check` verde, ou itens pendentes/reprovados listados.
- [ ] PR `feat(gates): consultas do G0 e relatório de evidências (T-015)` com REQ/INV/risco e revisão cruzada.

## Decisões já tomadas (não pergunte, siga)

| Dúvida provável | Resposta |
|---|---|
| Com que papel as consultas rodam em produção? | Como `postgres` pelo socket local, com `default_transaction_read_only=on` e `statement_timeout=120s`, só agregados. `tracksys_ops_ro` não tem USAGE em `app` e as funções `ops.*` (que exigiriam `SECURITY DEFINER`, CAT-07 e N0) são do F1. É o mesmo caminho do ensaio de restore da T-013. |
| Lacuna medida por `serverTime` ou `received_at`? | `serverTime` do Traccar (recebimento da mensagem), com `received_at` como reserva; janelas tratadas como `[from, to)` e com as bordas contando como pontos, para pegar silêncio no início ou no fim. |
| Latência por entrega ou só a 1ª entrega do alerta? | Por entrega `sent`, como o G0-5 e a consulta de [07 §10](../docs/spec/07-alertas-e-tempo-real.md); a frase "primeira entrega" de 07 §10 item 1 fica registrada no PR para alinhar o capítulo. |
| Placa no relatório ou nas evidências? | Não. Veículo = IMEI mascarado, como na T-014 (REQ-QLD-016: o repositório é lido por agentes). |
| Quando rodar o coletor? | Até 7 dias após o início da janela: depois disso o Traccar descarta posições (`historyDays = 7`) e G0-2 fica sem medida. O payload da inbox fica além de 7 dias no F0 (retenção adiada para a T-027, risco aceito em [15](../docs/spec/15-decisoes-riscos-premissas.md)), mas o G0 não depende disso. Durante a janela de 48 h, `--recent` 3 vezes ao dia junto com o `pilot status` da T-014. |
| Reconciliação por contagem não basta? | Não: uma perda e uma duplicata se anulam na contagem. O id do Traccar contra `(source_instance, kind, source_event_id)` prova as duas coisas (INV-01); a contagem fica como conferência rápida. |
| Amostra de alertas abaixo de 20 é `falhou`? | `pendente`: o fundador provoca mais alertas e roda de novo. p95 acima de 60 s ou entrega sem `originAt` é `falhou` mesmo com amostra pequena. |
| Quais tipos de alerta são "ativos no F0"? | Os listados em `manual.json` → `activeAlertTypes`, conforme DEC-02 e os cortes 2 e 3 aplicados; o relatório não deduz. |
| O agente pode marcar o G0 como aprovado? | Não. Agentes preenchem medidas; só o fundador aprova, mergeando o PR (REQ-NEG-016). Nenhum item é dispensado. |
| Precisa de dependência nova (YAML, CSV)? | Não. Front matter do restore com parser plano (o mesmo da T-014) e JSON nativo. |
