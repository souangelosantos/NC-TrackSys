# ADR-001 — Monólito modular TypeScript (NestJS) com processos `api` e `worker` no mesmo repositório

**Status:** Aceito em 07/10/2026

## Contexto

- Fundador solo + agentes de IA (Claude Code, Codex, Antigravity, OpenCode) escrevem a maior parte do código. O gargalo é revisão e operação, não geração.
- Carga do mês 12 (3.000 veículos): ~17 msg/s de média, ~37 msg/s de pico, ≤ 100 msg/s no pior caso. Cabe com folga em um processo Node.
- A v1.1 (p. 7–9) propunha núcleo NestJS com ~10 serviços implantáveis (`core-api`, `telemetry-worker`, `rules-worker`, `command-worker`…) ligados por RabbitMQ.
- Stack dominada: TypeScript/Node, React, Flutter, Postgres. Piloto Zero em 31/10/2026.
- Há dois perfis de trabalho: requisição HTTP curta (latência de API, SSE e ingestão) e jobs (alertas, despacho de comando, sync Asaas, retenção, export Parquet) que não podem disputar o mesmo event loop.

## Decisão

1. Um repositório pnpm com a estrutura canônica de [03 §12](../spec/03-arquitetura.md) e um monólito modular NestJS 11 (adaptador Fastify) com dois entrypoints:
   - `apps/api`: duas aplicações Nest no mesmo processo. A pública escuta em 3000 (via Caddy) e carrega todos os módulos de requisição; a interna escuta em 3001 (só rede Docker) e carrega só o módulo `ingestion` com as rotas `/internal/v1`.
   - `apps/worker`: `NestFactory.createApplicationContext` (sem HTTP de negócio) mais servidor mínimo de health na 3002; consome as filas pg-boss.
2. Módulos por contexto, cada um dono das suas tabelas ([03 §4](../spec/03-arquitetura.md)). Um módulo expõe um serviço público; os outros não escrevem nas tabelas dele.
3. Lógica pura em `packages/domain`; acesso a dados compartilhado (repositórios Kysely, aplicador de projeção, outbox, auditoria) em `packages/db`; contratos em `packages/contracts`. `apps/api` e `apps/worker` nunca importam um ao outro.
4. Os dois processos são construídos do mesmo commit e tag (`TRACKSYS_VERSION`) e sempre implantados juntos por `infra/scripts/deploy.sh`.
5. F0–F2: uma instância de cada processo. Mais de um `worker` funciona sem mudança (pg-boss usa `SKIP LOCKED`); mais de um `api` funciona porque cada processo mantém seu próprio LISTEN.

## Alternativas consideradas

- **Microsserviços (proposta da v1.1).** Por que não: 10 deploys, 10 healthchecks, contratos internos por rede, ~10 processos Node ocupando RAM ociosa e um runbook por serviço, para 37 msg/s e uma pessoa operando.
- **Processo único (HTTP e jobs juntos).** Por que não: export Parquet ou sync Asaas bloqueiam o event loop e pioram o p95 da ingestão e do SSE; um reinício derruba tudo.
- **Serverless (funções).** Por que não: Traccar e TCP exigem servidor sempre ligado; LISTEN/NOTIFY e SSE longos não combinam com funções; cold start; sai do Always Free.
- **Go ou Elixir.** Por que não: fora da stack dominada; o fundador revisa TypeScript com mais segurança; perde o compartilhamento de tipos com o console.
- **Fastify ou Express sem NestJS.** Por que não: sem DI e módulos padronizados, cada agente inventa uma estrutura e a revisão cresce; NestJS oferece contexto standalone pronto para o worker.
- **Repositórios separados por app.** Por que não: mudança de contrato atravessa api, console e app; PR atômico com CI único evita deriva.

## Consequências

**Positivas**
- Uma build, um deploy, uma versão, um rollback.
- Chamada entre módulos é chamada de função com transação compartilhada: outbox e auditoria entram no mesmo commit.
- Dois processos de 1 GB cabem no orçamento de RAM ([03 §11](../spec/03-arquitetura.md)).
- Agentes repetem um padrão só: módulo NestJS + Kysely + Zod.
- Rotas internas em listener próprio já preparam uma extração futura da ingestão.

**Negativas**
- Fronteira de módulo depende de lint e revisão, não de rede. Mitigação: tabela de donos em 03 §4 e `noRestrictedImports` bloqueando `modules/*/internal` fora do próprio módulo.
- Bug em código compartilhado (`packages/db`, `packages/domain`) atinge os dois processos.
- NestJS traz decorators e boot mais lento (1–3 s [PREMISSA]); aceitável com healthcheck.
- Escalar um módulo isolado exige extrair um serviço; não é grátis.

## Gatilho de revisão

- Um módulo responde por > 50% do tempo de CPU de um processo que fica > 70% de CPU por 1 h, em 3 de 7 dias → extrair esse módulo (começando pela ingestão).
- Um módulo passa a exigir SLO diferente do resto (ex.: ingestão com 99,9% e console com 99,5%).
- Mais de 5 desenvolvedores humanos trabalhando em paralelo no mesmo processo.

## Relacionados

- REQ-ARQ-001, REQ-ARQ-002, REQ-ARQ-007, REQ-ARQ-008.
- [03 — Arquitetura](../spec/03-arquitetura.md) §3, §4, §12; [14 — Qualidade e processo de IA](../spec/14-qualidade-e-processo-ia.md) (revisão por nível de risco).
- [ADR-002](ADR-002-postgres-unico-fila-barramento.md), [ADR-008](ADR-008-contrato-primeiro-zod-openapi-sse.md).
