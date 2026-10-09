# ADR-002 — PostgreSQL único (+ PostGIS) como banco, fila (pg-boss) e barramento (outbox + LISTEN/NOTIFY); sem RabbitMQ, Redis e Timescale até gatilhos objetivos

**Status:** Aceito em 07/10/2026

## Contexto

- A v1.1 (p. 7–8, 12) usava PostgreSQL com TimescaleDB e PostGIS, RabbitMQ com exchanges e filas quorum, e Redis para cache e distribuição ao vivo: três componentes com estado além do Traccar, para uma carga de referência de ~33 msg/s.
- Carga da v2.0 no mês 12: ~17 msg/s de média, ~37 msg/s de pico, ≤ 100 msg/s no pior caso; ~1,47 milhão de posições/dia antes da compactação.
- Uma VM de 12 GB, com 5 GB para o banco. Cada componente com estado exige backup, restore ensaiado, monitoramento, runbook e réplica no standby.
- Exigências que o barramento precisa cumprir: 202 só após commit da inbox; efeitos pelo menos uma vez com idempotência; estado atual monotônico (INV-04); tempo real p95 ≤ 2 s; alerta p95 ≤ 30 s.

## Decisão

1. **Banco:** PostgreSQL 17 + PostGIS 3.5 em imagem própria (`infra/db/Dockerfile`: `FROM postgres:17` + `postgresql-17-postgis-3`, amd64 e arm64), única fonte de verdade.
2. **Fila:** pg-boss 10 no schema `pgboss`, uma fila por consumidor. O schema é criado e migrado no deploy pelo papel `tracksys_owner`; em runtime o pg-boss roda sem migrar e com o papel `tracksys_app` (opção de construtor confirmada na versão 10 [VALIDAR]). O `api` usa pg-boss só para enfileirar. Montagem única, na T-004: o schema nasce por migration dbmate com a saída de `getConstructionPlans` da versão fixada (troca de versão = migration nova), e o runtime usa `migrate: false`. Criar fila cria partição e exige o dono [VALIDAR — pg-boss 10]. Por isso, cada fila nasce na migration da tarefa que a consome, com `SELECT pgboss.create_queue(...)` (padrão da T-006); o runtime nunca chama `createQueue`. Script do dono fora do dbmate (`db:boss`) só entra como plano B se a função SQL não existir na versão fixada. O publicador da outbox cria os jobs na mesma transação do `outbox_claim` (opção `db` do `send` [VALIDAR — T-011]); plano B: `send` antes do claim, com o mesmo `singletonKey`, e consumidor idempotente.
3. **Barramento:** `app.outbox` gravada na mesma transação da mudança, mais `pg_notify('outbox_new', <id>)`. O publicador da outbox do worker escuta o canal, varre a outbox a cada 5 s e cria jobs por consumidor ([03 §6](../spec/03-arquitetura.md#6-eventos-de-domínio-e-barramento)).
4. **Tempo real:** `pg_notify('device_state', …)` na projeção e LISTEN no `api`, que serve SSE ([ADR-008](ADR-008-contrato-primeiro-zod-openapi-sse.md)).
5. **Estado atual** em `device_state`, tabela comum com `revision` sob lock por dispositivo, lida direto do banco, sem cache.
6. Payloads de NOTIFY e de job carregam só ids e escopo; o consumidor relê sob RLS (tabelas do pg-boss ficam fora do RLS).
7. **Gatilhos de evolução** (cada um abre ADR nova; medição em [03 §14](../spec/03-arquitetura.md#14-gatilhos-objetivos-de-evolução)):
   - fila dedicada (RabbitMQ ou NATS) quando a ingestão sustentada passar de **300 msg/s por 1 h** ou o lag da fila passar de **60 s** de forma recorrente;
   - Redis quando o p95 de leitura do estado atual passar de **100 ms** sob carga;
   - compressão ou armazenamento colunar (Timescale ou Citus) quando as posições quentes passarem de **150 GB**;
   - Traccar em múltiplas instâncias (particionado por porta ou operadora) acima de **~20.000 dispositivos** conectados ou CPU do Traccar acima de **70%** sustentado.

## Alternativas consideradas

- **RabbitMQ (v1.1).** Por que não: mais um estado para backup e failover; fila quorum de verdade pede 3 nós; a outbox continua necessária para atomicidade com o banco, então o broker só se soma a ela.
- **Redis para estado atual e pub/sub.** Por que não: segunda cópia do estado, com o risco de regressão que a própria v1.1 apontou; leitura por chave primária no Postgres responde em poucos milissegundos; pub/sub já coberto por LISTEN/NOTIFY.
- **Kafka ou Redpanda.** Por que não: log distribuído para volumes três ordens de grandeza acima; RAM e operação incompatíveis com uma VM.
- **NATS JetStream.** Por que não agora: leve, mas é mais um estado persistente. Fica como candidato no gatilho de fila dedicada.
- **TimescaleDB.** Por que não: a compressão vem sob licença Timescale (TSL) e não existe em todo Postgres gerenciado, o que amarra a hospedagem; particionamento nativo + linha compacta + Parquet atende ([ADR-009](ADR-009-retencao-quente-frio.md)).
- **graphile-worker em vez de pg-boss.** Equivalente técnico. pg-boss fica pelas filas nomeadas com políticas e agendamento cron embutido; trocar não muda a outbox.

## Consequências

**Positivas**
- Um backup (WAL-G do cluster) cobre inbox, outbox, jobs, sessões e o banco do Traccar.
- Outbox atômica sem transação distribuída.
- Um único alvo de réplica e de failover; menos RAM; agentes usam SQL para tudo.

**Negativas**
- O Postgres é ponto único: queda derruba ingestão, fila e tempo real juntos. Mitigação: standby ([ADR-005](ADR-005-infra-oracle-always-free.md)), RPO ≤ 5 min.
- Fila e barramento consomem IO e CPU do mesmo banco: ~2,5 milhões de linhas/dia entre outbox e jobs no mês 12, com retenção curta e autovacuum ajustado ([04](../spec/04-dominio-e-dados.md)).
- NOTIFY sem ouvinte se perde (a varredura de 5 s cobre); payload limitado a 8.000 bytes; commits com NOTIFY passam por um lock global da fila de notificações e se serializam. Irrelevante a 37 msg/s, relevante perto do gatilho de 300 msg/s.
- pg-boss busca jobs por polling (intervalo configurável [VALIDAR mínimo na versão 10]); ~1 s de espera cabe no alerta p95 ≤ 30 s.

## Gatilho de revisão

Os quatro gatilhos da Decisão, item 7, mais os gatilhos operacionais complementares de [03 §14](../spec/03-arquitetura.md#14-gatilhos-objetivos-de-evolução) (disco > 70%, memória do `db` > 90% por 1 h, CPU da VM > 70% em 3 de 7 dias).

## Relacionados

- INV-01, INV-02, INV-04, INV-05.
- REQ-ARQ-009, REQ-ARQ-010, REQ-ARQ-011, REQ-ARQ-012, REQ-ARQ-015.
- [03 §5](../spec/03-arquitetura.md#5-ingestão-síncrona-com-fallback)–§7 e §14; [04](../spec/04-dominio-e-dados.md); [05](../spec/05-ingestao-e-telemetria.md); [07](../spec/07-alertas-e-tempo-real.md).
- [ADR-001](ADR-001-monolito-modular-nestjs.md), [ADR-009](ADR-009-retencao-quente-frio.md).
