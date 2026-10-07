# AGENTS.md — Regras para agentes de codificação

> Vale para **todos** os agentes que trabalham neste repositório: Claude Code, Codex, Antigravity, OpenCode e qualquer outro. O `CLAUDE.md` importa este arquivo. Em caso de conflito, a ordem de autoridade é: **INV (invariantes) → ADR → cartão da tarefa → capítulo da spec → este arquivo → seu julgamento**.

## O que é este projeto

**TrackSys** é uma plataforma SaaS de rastreamento veicular da **Versix Solutions**, vendida a operadoras de rastreamento (B2B2C: Versix → operadora → cliente final). A operadora piloto é a Lider Rastreamento (~160 clientes pessoa física, rastreadores J16). O produto prioriza **segurança veicular** (mapa ao vivo, histórico, alertas, bloqueio) e é construído por um fundador solo com agentes de IA.

Especificação completa: [docs/spec/00-indice.md](docs/spec/00-indice.md). Decisões de arquitetura: [docs/adr/](docs/adr/). Tarefas: [tasks/](tasks/).

## Como pegar uma tarefa

1. Leia o cartão `tasks/T-NNN-*.md` inteiro. Ele é a fonte do escopo.
2. Leia **só** os capítulos e ADRs citados em "Contexto". Não varra a spec inteira.
3. Implemente exatamente o "Escopo — fazer". O "Fora do escopo" é proibido nesta tarefa.
4. A seção "Decisões já tomadas" responde às dúvidas prováveis: siga, não reabra.
5. Rode os "Comandos de verificação" e só abra o PR com tudo verde.
6. Se o cartão contradizer um INV, um ADR ou outro cartão já entregue, **pare e registre a contradição no PR** em vez de escolher sozinho. Para tarefas de risco **N0**, nunca adivinhe.

## Comandos do repositório

| Comando | Para quê |
|---|---|
| `pnpm install` | Instala dependências (pnpm 10, Node ≥ 22.12; `.nvmrc` = 24) |
| `cp .env.example .env` | Variáveis locais de desenvolvimento |
| `pnpm db:up` / `pnpm db:down` / `pnpm db:reset` | Sobe, para e recria o Postgres local (porta 54329) |
| `pnpm db:migrate` | Aplica as migrations (dbmate, SQL puro) |
| `pnpm db:check` | Verificador de catálogo CAT-01..CAT-06 (isolamento) |
| `pnpm test:acceptance` | Testes de aceite congelados (`tests/acceptance/`) |
| `pnpm lint` / `pnpm format` / `pnpm typecheck` | Biome e TypeScript |
| `pnpm verify` | Tudo acima, na ordem do CI |

## Invariantes que nenhum código pode violar

| ID | Regra curta |
|---|---|
| INV-01 | Reentrega do mesmo fato (source_instance, kind, source_event_id) não gera novo fato nem efeito |
| INV-02 | Posição atrasada vai para o histórico e não substitui a posição atual |
| INV-03 | Desconhecido não é zero: ausente vira NULL/`unknown`, nunca `false`/`0`/desbloqueado |
| INV-04 | `device_state.revision` só cresce; clientes descartam revisão menor ou igual |
| INV-05 | Replay, backfill e reprocessamento não enviam push, comando, SMS, cobrança nem indicação |
| INV-06 | Fato pertence ao cliente/vínculo vigente no `fix_time`; histórico nunca muda de dono |
| INV-07 | Nada cruza a fronteira de operadora ou cliente; o banco garante (RLS FORCE + FK composta) |
| INV-08 | Telemetria ausente, antiga ou inválida nunca autoriza bloqueio; UNKNOWN nunca repete bloqueio |
| INV-09 | Inadimplência ou suspensão comercial nunca disparam bloqueio |
| INV-10 | Bloqueio exige `cut_point` registrado e perfil de hardware homologado |
| INV-11 | Agente de IA nunca despacha comando físico nem altera cobrança; só lê no escopo de quem pede |
| INV-12 | km/h, metros, segundos, UTC (RFC 3339), dinheiro em centavos inteiros |

Texto completo: [docs/spec/00-indice.md](docs/spec/00-indice.md#invariantes).

## Regras de código

- **TypeScript estrito**, ESM, Biome para lint e formatação. Rode `pnpm format` antes de commitar.
- **Identificadores em inglês**; comentários, mensagens de teste, textos de UI e documentação em **PT-BR**.
- **JSON da API e dos eventos em camelCase; banco em snake_case.** Unidades canônicas na fronteira (INV-12).
- **Validação com Zod** em toda fronteira: HTTP, variáveis de ambiente, mensagens da fila, webhooks.
- **Banco:**
  - migrations em `packages/db/migrations`, SQL puro (`-- migrate:up` / `-- migrate:down`), padrão expand/contract;
  - **nunca edite uma migration já aplicada em `main`**;
  - toda tabela nova no schema `app` nasce com `ENABLE` + `FORCE ROW LEVEL SECURITY`, pelo menos uma política e FK composta para tabelas de cliente/operadora. O `pnpm db:check` barra o contrário;
  - acesso a dados sempre dentro de `withContext(...)`. Nunca use o papel dono nem o superusuário na aplicação.
- **Segredos:** nunca no código, em fixtures ou em logs. Nada de IMEI completo, token, senha ou coordenada em log de nível info.
- **Dependências:** não adicione bibliotecas fora do cartão sem justificar no PR. Não troque versões major.
- **Proibido** (ADRs e INVs):
  - RabbitMQ, Redis ou Timescale antes dos gatilhos do ADR-002;
  - escrever no banco do Traccar;
  - `float` para dinheiro;
  - enfileirar comando físico no celular offline;
  - bibliotecas não oficiais de WhatsApp;
  - repetir bloqueio automaticamente.

## Testes e revisão

- **Testes congelados:** os arquivos existentes em `tests/acceptance/**` não podem ser alterados, apagados ou renomeados por um PR de implementação. O CI barra sem o rótulo `acceptance-change`. Faça o código passar no teste; nunca o contrário.
- **Níveis de risco:**
  - **N0** = comandos/bloqueio, isolamento/RLS/migrations, cobrança/split, autenticação/step-up, failover. Exige revisão adversarial por um agente de **outro fornecedor** e leitura humana linha a linha;
  - **N1** = domínio e integrações;
  - **N2** = UI e documentação.

  Detalhes em [docs/spec/14-qualidade-e-processo-ia.md](docs/spec/14-qualidade-e-processo-ia.md).
- **Uma tarefa por branch e por PR.** Título em Conventional Commits com o ID da tarefa, ex.: `feat(db): ... (T-001)`. A descrição lista REQ, INV e CT afetados e o nível de risco.

## O que fazer quando faltar informação

1. Procure em "Decisões já tomadas" do cartão, depois no capítulo citado, depois no ADR.
2. Se for N1/N2 e a escolha for reversível, escolha a opção mais simples coerente com a spec e **registre a escolha no PR**.
3. Se for N0, ou se a escolha contradisser a spec, pare e registre a pergunta no PR. Não invente regra de segurança.
