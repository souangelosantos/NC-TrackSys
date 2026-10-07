# TrackSys

Plataforma SaaS de rastreamento veicular da **Versix Solutions**, vendida a operadoras de rastreamento. A operadora usa a TrackSys para atender seus clientes finais: app com a marca dela, central de atendimento, bloqueio remoto, alertas, cobrança e serviços de valor agregado.

**Status:** especificação v2.0 aprovada para execução da **Fase 0 — Piloto Zero** (primeiros veículos reais da Lider Rastreamento até 31/10/2026). O código começa pela tarefa [T-001](tasks/T-001-fundacao-monorepo-e-isolamento.md).

## Por onde começar

| Você é… | Leia |
|---|---|
| Agente de IA indo implementar | [AGENTS.md](AGENTS.md) e depois o cartão da tarefa em [tasks/](tasks/) |
| Fundador revisando escopo e prazos | [01 — Visão e negócio](docs/spec/01-visao-e-negocio.md) → [02 — Escopo e fases](docs/spec/02-escopo-e-fases.md) → [15 — Decisões, riscos e premissas](docs/spec/15-decisoes-riscos-premissas.md) |
| Quem revisa a arquitetura | [03 — Arquitetura](docs/spec/03-arquitetura.md) e [docs/adr/](docs/adr/) |
| Advogado | [Anexo B — Jurídico](docs/anexos/B-juridico.md) |
| Operadora (comercial) | [Anexo A — Comercial](docs/anexos/A-comercial.md) |
| Plantonista da central | [Anexo C — Operacional](docs/anexos/C-operacional.md), seção do plantonista |

Índice completo da especificação: [docs/spec/00-indice.md](docs/spec/00-indice.md).

## Estrutura do repositório

```
apps/        api (NestJS), worker (NestJS), console (React), mobile (Flutter)
packages/    contracts (Zod/OpenAPI), db (migrations, RLS, catálogo), domain (regras puras), testkit
infra/       docker compose, imagem do banco, Caddy, Traccar, scripts de provisão/deploy/backup/failover
docs/        spec (capítulos 00–16), adr (ADR-001..011), anexos (A–D), runbooks
tasks/       cartões de tarefa T-NNN
tests/       testes de aceite congelados por tarefa
```

## Desenvolvimento local (após a T-001)

```bash
corepack enable
pnpm install
cp .env.example .env
pnpm db:up
pnpm verify
```

## Licença

Software proprietário. © 2026 Versix Solutions. Todos os direitos reservados.
