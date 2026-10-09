# T-019 — Guardas de processo no CI

| Campo | Valor |
|---|---|
| Fase | F0 (semanas S1–S2: 07–20/10/2026) |
| Requisitos | REQ-QLD-001, REQ-QLD-002, REQ-QLD-003, REQ-QLD-004, REQ-QLD-006, REQ-QLD-007, REQ-QLD-008, REQ-QLD-011, REQ-QLD-015, REQ-QLD-016, REQ-QLD-018, REQ-QLD-020, REQ-QLD-021, REQ-DAD-021 |
| Invariantes | INV-07, INV-08, INV-11 (indiretas: as guardas protegem o processo que as garante; nenhum código de produto muda) |
| Risco de revisão | **N0** (alavancagem: `.github/**`) — modo de planejamento antes de editar; revisão adversarial por agente de outro fornecedor; leitura humana linha a linha |
| Depende de | T-001 |
| Estimativa | 3 sessões de agente, uma por fatia (ver "## Fatias") (1: biblioteca, `guards.yml`, `risk-label`, `pr-title`, `label-guard`, `acceptance-freeze`, `review-record`; 2: `acceptance-match`, `docs-check`, `tasks:lint`, `db:lint`; 3: `agent:env-check`, proteção de `main`, revisão semanal, perguntas, PR canário) |
| Bloqueado por decisão | nenhuma (pré-requisitos do fundador na seção própria; até o merge, o fundador confere os itens pelo checklist do template de PR, 14 §11) |

## Objetivo

Transformar as regras de processo da [14](../docs/spec/14-qualidade-e-processo-ia.md) em checagens que nenhum PR consegue desligar para si mesmo. Ao final existem: o nível de risco calculado pelo caminho e aplicado como rótulo; a revisão adversarial de outro fornecedor conferida no commit do head; título e template do PR validados; testes do cartão comparados byte a byte com `origin/main`; rótulos de exceção que só valem aplicados pelo fundador; links, DEC, cartões e `trace.py` conferidos; linter de migrations; ambiente de agente sem credencial de produção; proteção de `main` conferível por script; e a issue semanal de riscos. Workflow e scripts das guardas rodam sempre a partir de `main`; o head do PR é só dado.

## Contexto obrigatório

- [14 §4](../docs/spec/14-qualidade-e-processo-ia.md#4-cartão-de-tarefa) (cartão), §5 (DoR/DoD), §6 (níveis e globs), §7 (testes congelados), §8.2 e §8.5 (formato e registro da revisão), §11 (pipeline, proteção de `main`, conta `versix-agent`), §12 (título, rótulos, hotfix, template de PR), §15 (REQ-QLD-001 a 008, 015, 016 e 018).
- [15 §1](../docs/spec/15-decisoes-riscos-premissas.md#1-como-usar-este-registro) (revisão semanal), §2 (tabela de DEC), §3 (riscos e gatilhos), §6 (REQ-QLD-020 e 021).
- [04 §10](../docs/spec/04-dominio-e-dados.md#10-migrations-expandcontract) (regras de migration) e REQ-DAD-021.
- Cartão [T-001](T-001-fundacao-monorepo-e-isolamento.md): seção (1) (`package.json`, `tsx`) e seção (6) (`ci.yml`, `acceptance-freeze`). Ferramenta existente: [`scripts/trace.py`](../scripts/trace.py).

## Fatias

Três PRs sequenciais, um por sessão (`t-019-1-guardas-base`, `t-019-2-docs-e-migrations`, `t-019-3-ambiente-e-semanal`), cada um com no máximo 400 linhas de produção e com o subconjunto dos testes que ele torna verdes. Cada fatia segue o rito N0 inteiro.

| Fatia | Entrega | Testes que ficam verdes |
|---|---|---|
| 1 | Biblioteca `scripts/ci/lib/`, `guards.yml`, `risk-label`, `pr-title`, `label-guard`, `acceptance-freeze`, `review-record`, `risk-paths.yml`, `required-checks.txt`, `CODEOWNERS`, template de PR e a alteração do `ci.yml` | `risk-label`, `pr-title`, `labels`, `review-record` |
| 2 | `acceptance-match`, `docs-check`, `tasks:lint` (com ISO-01..ISO-05), `migration-lint`, `rollback-new-migrations` e o lint de `vi.mock` de banco | `acceptance-match`, `docs-check`, `tasks-lint`, `migration-lint` |
| 3 | `agent:env-check`, `branch-protection`, `risk-review`, `weekly.yml`, perguntas (`Q#`) e o PR canário | `agent-env`, `branch-protection`, `risk-review`, `questions` |

Corte 0a ([02 §2.4](../docs/spec/02-escopo-e-fases.md#24-plano-de-corte)): se o cronograma apertar, as fatias 2 e 3 passam para o F1 (01–15/11, antes do 1º PR da T-016). Ficam no F0 só a fatia 1, o `acceptance-freeze` da T-001 e o checklist do template de PR conferido pelo fundador.

## Pré-requisitos do fundador (antes da sessão 1)

1. Variável de repositório `FOUNDER_LOGIN` com o login GitHub do fundador (`gh variable set FOUNDER_LOGIN`).
2. Conta de máquina `versix-agent` (ou GitHub App) com escrita e sem administrador (14 §11 regra 4).
3. Rótulos criados: `risk:N0`, `risk:N1`, `risk:N2`, `acceptance-change`, `api-breaking`, `hotfix`, `question`, `nightly-failure`, `risk-review`.
4. Depois do merge: proteção de `main` da 14 §11 regra 3 com os checks de `.github/required-checks.txt`, conferida por `infra/scripts/check-branch-protection.sh`.

## Escopo — fazer

1. Biblioteca `scripts/ci/lib/` (entradas validadas por Zod, glob, Markdown, risco, rótulos efetivos, git, perguntas) e um script por guarda em `scripts/ci/`, executados com `tsx`, no contrato da seção (1).
2. `.github/workflows/guards.yml` (seção 2): `pull_request_target` e `issue_comment`, código das guardas sempre de `main`, head só como dado, um status de commit por guarda.
3. `.github/workflows/ci.yml` (alterar): `acceptance-freeze` passa a exigir o rótulo aplicado pelo fundador e roda em `labeled`/`unlabeled`; `verify` ganha `pnpm agent:env-check`, e o `pnpm verify` ganha `db:lint` antes de `db:migrate`. No job `verify` do CI, o passo `pnpm db:rollback` é substituído por `pnpm db:rollback-new`, que desfaz com `dbmate rollback` cada migration nova do PR (todas as ausentes em `origin/main`, no mínimo 1) e deixa o `db:migrate` seguinte reaplicá-las.
4. `.github/workflows/weekly.yml`: issue semanal de riscos, DEC e perguntas (REQ-QLD-021).
5. `.github/risk-paths.yml` (seção 4), `.github/required-checks.txt`, `.github/CODEOWNERS` (`* @<FOUNDER_LOGIN>`) e `.github/pull_request_template.md` (conteúdo exato da 14 §12).
6. As guardas da tabela da seção (3), com as regras da seção (5).
7. `infra/scripts/check-branch-protection.sh` + `scripts/ci/branch-protection.ts` (REQ-QLD-008).
8. `docs/runbooks/revisao-semanal/README.md` com o formato da seção 5.6.
9. `package.json` da raiz: scripts `docs:check`, `tasks:lint`, `db:lint`, `db:rollback-new` (executa `scripts/ci/rollback-new-migrations.ts`), `agent:env-check` e `risk:review`; `lint` passa a rodar também `tsx scripts/ci/no-db-mock.ts`; `verify` = `lint && typecheck && db:lint && db:migrate && db:rollback && db:migrate && db:check && test:acceptance`; `typecheck` também com `tsc -p scripts/ci/tsconfig.json`; `zod` em `devDependencies`, na versão de `packages/db`.
10. Deixar `main` verde nas checagens novas: corrigir só a forma de cartões e links apontados (cabeçalho de seção, caminho relativo), listando cada correção no PR.
11. Testes de `tests/acceptance/T-019/` no 1º commit de cada PR de fatia (`test(ci): aceite congelado (T-019)`), escritos por agente de fornecedor diferente do implementador e lidos pelo fundador linha a linha antes dos commits de implementação.
12. REQ-QLD-011: `tasks:lint` exige ISO-01..ISO-05 para cada `CREATE TABLE` citado em cartão que lista `packages/db/migrations/`; `scripts/ci/no-db-mock.ts` (dentro do `pnpm lint`) barra `vi.mock('pg'|'kysely'|'@tracksys/db')` em `tests/acceptance/**`.
13. `acceptance-match` em modo tabela: o 1º commit do PR `test(<escopo>): aceite congelado (T-NNN)` só toca `tests/acceptance/T-NNN/**`, é escrito por outro fornecedor, e `tests/acceptance/T-NNN/**` do head é comparado byte a byte com ele (14 §7 item 3), com caso de teste em `acceptance-match.test.ts`. Entende fatias: branch `t-NNN-<k>-slug` e 1º commit `test(...): aceite congelado (T-NNN)` em cada PR de fatia (seção 5.3).
14. `docs-check` compara o 16 gerado com o do head e valida as âncoras `#...` dos links (seção 5.5).
15. PR canário depois do merge da fatia 3 (Definição de pronto).
16. Arquivo de regras do Antigravity apontando para o `AGENTS.md`.
17. Regra de legibilidade de 14 §4 item 5 (parágrafo ≤ 400 caracteres), se for verificada pelo `docs-check`; senão, o PR registra que não é verificada.

## Fora do escopo

- Job `secrets` com gitleaks e `check-secret-files.sh` (T-003, CT-QLD-016 parte 2); teste do manifest das capturas (T-002, CT-QLD-016 parte 3); job `contracts-breaking` (T-004), que só passa a depender do `label-guard`.
- `acceptance-red`, `mutation`, `e2e-*`, `bench-evidence` e `nightly.yml` (F1); `process:report` (REQ-QLD-019, T-031).
- Conferir `-- rls: X` (DoD manual), reescrever o 16 (a guarda só compara) e inserir âncoras nos links existentes (feito por script do orquestrador).
- Autenticar o fornecedor declarado pelo revisor (o cabeçalho é declarativo; quem confere é o fundador, 14 §8.4). Regras de tag `v*`.
- Mudar o conteúdo de cartão, capítulo ou teste congelado existente.

## Arquivos a criar/alterar

```
criar    .github/workflows/{guards.yml,weekly.yml}  .github/{risk-paths.yml,required-checks.txt,CODEOWNERS,pull_request_template.md}
alterar  .github/workflows/ci.yml  package.json  pnpm-lock.yaml  .gitignore (.ci-input/)
criar    scripts/ci/lib/{inputs.ts,glob.ts,markdown.ts,risk.ts,labels.ts,git.ts,questions.ts}  scripts/ci/tsconfig.json
criar    scripts/ci/{collect-inputs.sh,run-guards.sh,rollback-new-migrations.ts,no-db-mock.ts,risk-label.ts,pr-title.ts,label-guard.ts,acceptance-freeze.ts,review-record.ts,
         acceptance-match.ts,docs-check.ts,tasks-lint.ts,migration-lint.ts,agent-env-check.ts,risk-review.ts,branch-protection.ts}
criar    infra/scripts/check-branch-protection.sh  docs/runbooks/revisao-semanal/README.md
criar    tests/acceptance/T-019/harness.ts
criar    tests/acceptance/T-019/{risk-label,pr-title,labels,review-record,acceptance-match,docs-check,tasks-lint,
         migration-lint,agent-env,branch-protection,risk-review,questions}.test.ts
```

## Especificação detalhada

### (1) Contrato comum dos scripts

- Execução: `pnpm exec tsx scripts/ci/<guarda>.ts`. Sem rede: o que vem do GitHub chega em arquivos de `CI_INPUT_DIR` (padrão `.ci-input/`), gerados por `collect-inputs.sh` com `gh` e `jq -c`.
- Entradas (camelCase, `z.strictObject`; NDJSON = um objeto por linha): `pr.json` `{ number, title, body, headSha, baseRef, labels: string[] }`; `changes.txt` = `git diff --name-status -M origin/<baseRef>...HEAD` (se faltar, o script calcula no `HEAD_DIR`); `events.ndjson` `{ event: 'labeled'|'unlabeled', label, actor, createdAt }`; `comments.ndjson` `{ author, body, createdAt }`; `questions.ndjson` `{ number, title, state }`.
- Ambiente: `HEAD_DIR` (árvore analisada; padrão: cwd), `BASE_REF` (padrão `origin/main`), `FOUNDER_LOGIN`, `DOCS_ROOT` (padrão `HEAD_DIR`), `DOCS_CHECK_TODAY` (`AAAA-MM-DD`; padrão: data civil de `America/Sao_Paulo`), `GITHUB_OUTPUT` (opcional).
- Saída: sucesso numa linha em stdout; cada violação numa linha em stderr; avisos em stdout começando por `aviso:`. Tudo em PT-BR, sem valor de variável, token ou corpo de comentário.
- Código de saída: `0` passa; `1` violação; `2` entrada ausente ou inválida (falha fechada, `entrada inválida: <arquivo>: <erro Zod>`).
- `run-guards.sh` roda cada guarda de `$GUARDS` a partir de `base/` (`HEAD_DIR=$GITHUB_WORKSPACE/head`, `BASE_REF=origin/main`) e publica `POST /repos/{repo}/statuses/{headSha}` com `context` = nome da guarda, `state` = `success`/`failure`, `description` = 1ª linha de erro (≤ 140 caracteres) e `target_url` = a execução; escreve o resumo em `$GITHUB_STEP_SUMMARY`; sai com 1 se alguma falhou.

### (2) Workflows

`.github/workflows/guards.yml` (estrutura fixa):

```yaml
name: guards
on:
  pull_request_target:
    types: [opened, synchronize, reopened, edited, labeled, unlabeled, ready_for_review]
  issue_comment:
    types: [created, edited, deleted]
permissions: { contents: read, issues: write, pull-requests: write, statuses: write }
concurrency:
  group: guards-${{ github.event_name }}-${{ github.event.pull_request.number || github.event.issue.number }}
  cancel-in-progress: true
jobs:
  guards:
    if: github.event_name == 'pull_request_target' || github.event.issue.pull_request
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    env:
      GH_TOKEN: ${{ github.token }}
      FOUNDER_LOGIN: ${{ vars.FOUNDER_LOGIN }}
      PR_NUMBER: ${{ github.event.pull_request.number || github.event.issue.number }}
      GUARDS: ${{ github.event_name == 'issue_comment' && 'review-record' || 'risk-label pr-title label-guard review-record acceptance-match docs-check migration-lint' }}
    steps:
      - uses: actions/checkout@v4   # código das guardas: sempre main
        with: { ref: main, path: base, persist-credentials: false }
      - uses: actions/checkout@v4   # head do PR: só lido, nunca instalado nem executado
        with: { ref: "refs/pull/${{ github.event.pull_request.number || github.event.issue.number }}/head", path: head, fetch-depth: 0, persist-credentials: false }
      - uses: pnpm/action-setup@v4
        with: { package_json_file: base/package.json }
      - uses: actions/setup-node@v4
        with: { node-version-file: base/.nvmrc, cache: pnpm, cache-dependency-path: base/pnpm-lock.yaml }
      - run: pnpm --dir base install --frozen-lockfile
      - run: bash base/scripts/ci/collect-inputs.sh
      - run: bash base/scripts/ci/run-guards.sh
```

`.github/workflows/ci.yml` (só estas mudanças): `on.pull_request.types: [opened, synchronize, reopened, labeled, unlabeled]`; em `verify`, passo `pnpm agent:env-check` logo após `pnpm install --frozen-lockfile` e antes de `cp .env.example .env`; em `acceptance-freeze`, `permissions: { contents: read, issues: read, pull-requests: read }`, `env` com `GH_TOKEN`, `FOUNDER_LOGIN` e `PR_NUMBER`, setup de pnpm/node com install, `bash scripts/ci/collect-inputs.sh --events-only` (gera `pr.json` e `events.ndjson`) e o passo "Testes de aceite existentes não podem ser alterados sem o rótulo acceptance-change aplicado pelo fundador" com `pnpm exec tsx scripts/ci/acceptance-freeze.ts`. O nome do job continua `acceptance-freeze`.

`.github/workflows/weekly.yml`: `schedule: [{ cron: '47 10 * * 1' }]` (segunda 07:47 BRT, antes da revisão das 09:00) e `workflow_dispatch`; `permissions: { contents: read, issues: write }`; checkout de `main`, install, `collect-inputs.sh --questions-only`, `pnpm risk:review --issue .ci-input/issue.md` e `gh issue create --label risk-review --title "Revisão semanal DD/MM/AAAA" --body-file .ci-input/issue.md`.

### (3) Guardas

| Guarda (status) | Script | Entrada | Passa (stdout, código 0) | Falha (stderr, código 1) |
|---|---|---|---|---|
| `risk-label` | `risk-label.ts` | `changes.txt`; linha `Risco declarado:` do `pr.json`; `.github/risk-paths.yml` de `main` | `risco: calculado N0, declarado N0` e `label=risk:N0` em `$GITHUB_OUTPUT`; `run-guards.sh` aplica o rótulo e tira os outros `risk:*` | `declarado N2 < calculado N0 (<1º arquivo N0>)`; `Risco declarado ausente ou ambíguo: use "Risco declarado: N0", "N1" ou "N2"` |
| `pr-title` | `pr-title.ts` | `pr.json` | `título OK` | `título fora do padrão (14 §12): "<título>"`; `descrição sem "Implementado por: <fornecedor>/<ferramenta>/<modelo>"`; `descrição sem a linha "REQ: … · INV: … · CT: …" com ≥ 1 REQ` (linha dispensada em `(hotfix)` e `(deps)`) |
| `label-guard` | `label-guard.ts` | `pr.json`, `events.ndjson`, `FOUNDER_LOGIN` | `rótulos de exceção: nenhum` ou `acceptance-change aplicado por <fundador>` | `rótulo api-breaking aplicado por versix-agent; exige o fundador`; `FOUNDER_LOGIN não configurada: rótulos de exceção sem efeito` |
| `acceptance-freeze` (no `ci.yml`) | `acceptance-freeze.ts` | `changes.txt` (M, D ou R em `tests/acceptance/**` e `packages/testkit/fixtures/**`), `pr.json`, `events.ndjson` | `nenhum arquivo congelado alterado` ou `alteração permitida: acceptance-change aplicado por <fundador>` | `Arquivos congelados alterados (exige rótulo acceptance-change aplicado pelo fundador):` + um caminho por linha; `rótulo acceptance-change aplicado por versix-agent; exige o fundador` |
| `review-record` | `review-record.ts` | `pr.json`, `comments.ndjson`, `changes.txt`, `events.ndjson` | `N2: revisão cruzada opcional`; `revisão openai/codex/<modelo> em <sha7>: APROVAR`; `hotfix N1: revisão pendente` (`hotfix_issue=true`; `run-guards.sh` abre "Revisão cruzada pendente — PR #N" se não existir) | `sem revisão cruzada no formato da 14 §8.2`; `revisor do mesmo fornecedor (anthropic)`; `revisão desatualizada: revisado <sha7>, head <sha7>`; `veredito BLOQUEAR`; `veredito PEDIR MUDANÇAS` |
| `acceptance-match` | `acceptance-match.ts` | `changes.txt`, `HEAD_DIR`, cartões em `BASE_REF` (`git show`) | `acceptance-match: <n> arquivos idênticos ao cartão`; `aviso: tasks/T-006-….md sem blocos (modo tabela); conferência humana` | `<arquivo> difere do bloco do cartão em origin/main`; `<arquivo> ausente (há bloco no cartão)`; `<arquivo> sem bloco no cartão em origin/main`; `cartão T-NNN ausente em origin/main`; `.todo( proibido: <arquivo>:<linha>`; `retry: proibido: <arquivo>:<linha>` |
| `docs-check` (`pnpm docs:check`) | `docs-check.ts` | `DOCS_ROOT`; `questions.ndjson`, se houver; `scripts/trace.py` de `main` | `Docs OK: <n> arquivos, <m> links; DEC, cartões, revisões, perguntas e trace.py sem problema.` + avisos | `<arquivo>:<linha>: link quebrado → <alvo>`; `CLAUDE.md sem a linha @AGENTS.md`; `AGENTS.md com <n> linhas (máx. 150)`; `DEC-03: Resolvida sem data ou sem resultado (formato: Resolvida — DD/MM/AAAA — resultado)`; erros de `tasks:lint`, revisões e perguntas; `trace.py: <linha PROBLEMA>` |
| `tasks:lint` (dentro do `docs-check`) | `tasks-lint.ts` | `tasks/T-*.md`; REQ definidos em `docs/spec/*.md` | `Cartões OK: <n> cartões (<r> rascunhos)` | `T-099: estimativa 4 > 3 — dividir`; `T-099: falta a linha "<campo>"`; `T-099: falta a seção "## Decisões já tomadas"`; `T-099: seção "## <título>" fora de ordem`; `T-099: REQ-XYZ-999 não definido nos capítulos` |
| `migration-lint` (`pnpm db:lint`) | `migration-lint.ts` | `packages/db/migrations/*.sql` do `HEAD_DIR`; `BASE_REF` | `Migrations OK: <n> arquivos (<k> novos)`; sem base: `aviso: regra 1 não conferida (base ausente); todas contam como novas` | `<caminho>: regra 1 — <motivo>`; `<caminho>: regra 2 — falta SET LOCAL lock_timeout`; `<caminho>: regra 6 — <operação> em app.<tabela> (04 §10)` |
| `agent:env-check` (passo do `verify`; 1º comando de toda sessão de agente) | `agent-env-check.ts` | `process.env` | `Ambiente do agente sem credencial de produção.` | `variáveis proibidas no ambiente do agente: <NOMES> (valores omitidos)` |
| `risk-review` (`weekly.yml`; `--check` dentro do `docs-check`) | `risk-review.ts` | 15 §2 e §3; `docs/runbooks/revisao-semanal/*.md`; `questions.ndjson` | `--issue <arq>`: corpo da seção 5.6; `--check`: `R-16 disparado — ação: recrutar na Lider` por gatilho disparado | `revisão 2026-11-02: falta R-07`; `R-16 disparado sem ação em 26/10/2026 e 02/11/2026: exige cartão de tarefa ou DEC`; `revisão 2026-10-26: "Disparado" deve ser sim ou não (R-03)` |
| `branch-protection` (manual, fundador; lembrete na issue semanal) | `check-branch-protection.sh` → `branch-protection.ts` | `gh api repos/{owner}/{repo}/branches/main/protection`, `gh api repos/{owner}/{repo}`, `.github/required-checks.txt` | `proteção de main OK` | `desvio: allow_force_pushes.enabled = true (esperado false)`; `desvio: check obrigatório ausente: review-record`; `desvio: allow_merge_commit = true (esperado false)` |

`.github/required-checks.txt`, um por linha: `verify`, `acceptance-freeze`, `risk-label`, `review-record`, `pr-title`, `acceptance-match`, `docs-check`, `migration-lint`, `label-guard`; mais `secrets` e `contracts-breaking` se já existirem no `ci.yml` quando a T-019 for implementada.

### (4) `.github/risk-paths.yml` — conteúdo exato

```yaml
# Níveis de risco por caminho (docs/spec/14-qualidade-e-processo-ia.md §6). Lido por scripts/ci/lib/risk.ts.
# Formato fechado: chaves N0, N0-alterado, N2 e N1, cada uma seguida de itens "  - <glob>".
# Ordem: N0 → N0-alterado (só status M, D ou R) → N2 → N1. Sem regra = N1. O nível do PR é o maior.
N0:
  - packages/db/migrations/**
  - packages/db/src/context.ts
  - packages/db/catalog-allowlist.json
  - packages/domain/**/commands/**
  - apps/api/src/commands/**
  - apps/worker/src/commands/**
  - apps/api/src/auth/**
  - apps/api/src/identity/**
  - apps/api/src/billing/**
  - apps/worker/src/billing/**
  - packages/domain/**/billing/**
  - apps/mobile/lib/security/**
  - infra/scripts/failover*
  - infra/scripts/deploy.sh
  - infra/scripts/check-branch-protection.sh
  - infra/secrets/**
  - .sops.yaml
  - .github/**
  - AGENTS.md
  - CLAUDE.md
  - scripts/ci/**
  - scripts/trace.py
  - tests/vitest.config.ts
N0-alterado:
  - tests/acceptance/**
  - packages/testkit/fixtures/**
N2:
  - apps/console/**
  - apps/mobile/**
  - docs/**
  - tasks/**
  - README.md
N1:
  - apps/api/**
  - apps/worker/**
  - packages/**
  - infra/**
  - scripts/**
```

Regra fixa em `risk.ts`: `package.json` da raiz com `scripts` alterado ou removido em relação a `main` → N0 (`package.json: scripts alterados`); alteração só aditiva (chaves novas em `scripts`, nenhum valor existente mudado) → N1. `biome.json`: regra nova sem mudar nem desligar (`"off"`) regra existente → N1; qualquer outra mudança → N0. `.github/workflows/**` e `packages/db/migrations/**` são sempre N0. Linha fora do formato → código 2 com `risk-paths.yml:<linha>: fora do formato`.

### (5) Regras de detalhe

**5.1 risk-label.** Nível por arquivo = 1ª chave que casa na ordem da seção (4); em R vale o maior entre caminho antigo e novo. Glob: `**` = zero ou mais segmentos; `*` e `?` não cruzam `/`. Declarado: exatamente uma linha casando `^Risco declarado:\s*(N[012])\s*(\(|$)` (a linha do template sem edição é ambígua e falha).

**5.2 review-record.** Nível = máximo entre calculado e declarado. Comentário de revisão = corpo com `## Revisão cruzada — <fornecedor>/<ferramenta>/<modelo> — <AAAA-MM-DD>`, `Commit revisado: <sha de 40>` e `Veredito: APROVAR|PEDIR MUDANÇAS|BLOQUEAR`. Vale o mais recente por `createdAt`; ordem das checagens: formato → fornecedor (1º segmento, minúsculo, diferente do de "Implementado por") → SHA igual a `headSha` → veredito. `hotfix` efetivo dispensa em N1 e N2, nunca em N0.

**5.3 acceptance-match.** Bloco = linha só com `` `tests/acceptance/T-NNN/<arquivo>` ``, linhas em branco opcionais e a cerca de abertura (≥ 3 crases ou tis) até a de fechamento do mesmo tipo e tamanho ≥; o arquivo esperado = linhas do bloco + `\n` final, byte a byte.

- **Modo bloco** (cartão com blocos, como T-001 e T-016): aplica-se (a) a todo arquivo A, M ou R em `tests/acceptance/T-XXX/**`, contra `tasks/T-XXX-*.md` em `BASE_REF`; (b) quando o título termina em `(T-NNN)` e o PR muda algo fora de `docs/**` e `tasks/**`, todo bloco do cartão precisa existir no head.
- **Modo tabela** (cartão sem blocos, N0 e N1): o 1º commit do PR, `test(<escopo>): aceite congelado (T-NNN)`, só toca `tests/acceptance/T-NNN/**` e é escrito por agente de fornecedor diferente do implementador. O `acceptance-match` identifica esse commit pelo título e compara byte a byte `tests/acceptance/T-NNN/**` do head com ele; qualquer diferença sem `acceptance-change` falha e lista os arquivos. Sem esse commit, ou com commit que toca outro caminho: `1º commit do PR não é o de aceite congelado (T-NNN)`. Em N0, o fundador lê esse commit linha a linha antes dos seguintes.
- `.todo(` e `retry:` são barrados em todo `tests/acceptance/**` do head.

**5.4 migration-lint.** "Nova" = ausente em `BASE_REF`. Regra 1: nome `^\d{14}_[a-z0-9_]+\.sql$`; `-- migrate:up` antes de `-- migrate:down`; arquivo presente na base idêntico byte a byte. Regra 2 (novas): o `up` tem `SET LOCAL lock_timeout` e `SET LOCAL statement_timeout` (com `-- migrate:up transaction:false`, os `SET` de sessão). Regra 6 (novas, só no `up`, sem comentários, por comando separado em `;`), para `position`, `ingest_inbox`, `outbox`, `audit_log` e `access_log` (com ou sem `app.`, inclusive partições `_pAAAAMM`), salvo tabela criada no mesmo arquivo: `CREATE [UNIQUE] INDEX` sem `CONCURRENTLY` e sem `ON ONLY`; `ALTER COLUMN … TYPE`; `ADD COLUMN … DEFAULT` com `now(`, `clock_timestamp(`, `current_timestamp`, `gen_random_uuid(`, `random(` ou `nextval(`; `ADD CONSTRAINT … CHECK|FOREIGN KEY` sem `NOT VALID`. Exceção única, por nome: `position_vehicle_fix_idx` (04 §10 regra 6).

**5.5 docs-check.** Links `[texto](alvo)` em `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/**/*.md` e `tasks/**/*.md`, fora de blocos e trechos de código; ignora `http(s):`, `mailto:` e âncora pura; tira `#…`; alvo relativo ao arquivo, arquivo ou diretório existente. DEC: linhas `| DEC-NN |` da 15 §2; `Resolvida` exige `Resolvida — DD/MM/AAAA — <resultado>`; `Aberta` com a 1ª data da coluna Prazo anterior a hoje → `aviso: DEC-12 vencida em 10/10/2026`. `trace.py` roda sobre cópia temporária de `docs/` e `tasks/`; qualquer `PROBLEMA:` falha. Depois, o 16 gerado na cópia é comparado com `docs/spec/16-rastreabilidade.md` do head: diferença falha com `16-rastreabilidade.md desatualizado: rode python3 scripts/trace.py .` (a guarda não reescreve o arquivo). Âncoras: em links `arquivo.md#slug`, o `slug` precisa existir entre os títulos do arquivo de destino (slug do GitHub: minúsculas, sem pontuação, espaços em hífens, sufixo `-1`, `-2` em repetidos); senão `<arquivo>:<linha>: âncora inexistente → <alvo>#<slug>`. Âncora pura (`#slug`) vale contra o próprio arquivo. Perguntas: cada item de `questions.ndjson` precisa de `Q#<número>` em `tasks/*.md` ou `AGENTS.md`, senão `pergunta #12 (T-005) sem resposta registrada em tasks/ ou AGENTS.md (cite Q#12)` (a tarefa vem do sufixo do título).

**5.6 Revisão semanal.** Arquivo `docs/runbooks/revisao-semanal/AAAA-MM-DD.md` (data da segunda-feira) com a tabela `| Risco | Disparado | Ação | Cartão ou DEC |`, uma linha por `R-NN` da 15 §3, `Disparado` = `sim`/`não`, `—` = vazio. `--check` olha as duas revisões mais recentes: risco faltando → erro; disparado sem ação nas duas e sem `T-NNN` (cartão existente) ou `DEC-NN` (linha da 15 §2) na mais recente → erro; última revisão com mais de 8 dias → aviso. A issue semanal lista `- [ ] R-NN — <gatilho>` para cada risco, as DEC vencidas ou com prazo nos próximos 7 dias, os riscos disparados sem ação na última revisão, as perguntas sem `Q#` e o lembrete `bash infra/scripts/check-branch-protection.sh`.

**5.7 tasks:lint.** Título `# T-NNN — …` com o número do arquivo; as 7 linhas da tabela (`Fase` começa com `F0`–`F3`; `Requisitos` com ≥ 1 REQ, todos definidos como `### REQ-…` em `docs/spec/*.md`; `Risco de revisão` começa com `N0`/`N1`/`N2`, com ou sem negrito; `Estimativa` = o número imediatamente antes de "sess", ou o maior de um intervalo como `2–3`, ou, sem ele, o 1º número da linha; de 1 a 3); seções canônicas da 14 §4 na ordem, reconhecidas pelo início do título, extras aceitas em qualquer posição. Cartão com `## Para completar o DoR` é rascunho: só título e tabela, mais `aviso: T-020: rascunho (DoR incompleto)`. "Decisões já tomadas" com menos de 5 linhas → aviso. Cartão cujo texto lista `packages/db/migrations/` e contém `CREATE TABLE` (REQ-QLD-011) precisa citar ISO-01 a ISO-05; falta → `T-099: cria app.alert sem citar ISO-02, ISO-04, ISO-05`.

## Testes de aceite (congelados)

`tests/acceptance/T-019/`, sem banco e sem rede. `harness.ts` exporta `runScript(nome, { env, cwd, inputs })` (spawn de `tsx` com `env` explícito: só `PATH`, `HOME` e o que o caso define), `inputDir(arquivos)` e `gitRepo({ base, head })` (repositório temporário com `refs/remotes/origin/main` na base). `FOUNDER_LOGIN=fundador-versix`; head `a…a` e outro commit `b…b` (40 caracteres).

| Arquivo | Dado / Quando / Então |
|---|---|
| `risk-label.test.ts` (CT-QLD-003) | `A packages/db/migrations/20261020090000_device.sql` + `M apps/console/src/routes/vehicles.tsx` com `Risco declarado: N2` → código 1, stderr `declarado N2 < calculado N0` e `label=risk:N0`; só `M docs/spec/10-apps-e-ux.md` com N2 → 0 e `label=risk:N2`; `M .github/workflows/ci.yml` → `risk:N0`; `M tests/acceptance/T-001/catalog.test.ts` → N0; `A tests/acceptance/T-005/inbox.test.ts` → N1; `M scripts/ci/review-record.ts` → N0; `package.json` com `scripts.verify` diferente da base → N0; corpo `Risco declarado: N0 \| N1 \| N2` → 1 `Risco declarado ausente ou ambíguo` |
| `pr-title.test.ts` (CT-QLD-015) | `feat(db): fundação do monorepo e isolamento em 3 níveis (T-001)` → 0; `Fundação do banco` → 1 `título fora do padrão`; `feat(db): fundação` → 1; `fix(ingestion): reabre pool após queda (hotfix)` sem linha `REQ:` → 0; título válido com corpo sem `Implementado por:` → 1 |
| `labels.test.ts` (CT-QLD-006; CT-QLD-005 preservado) | `M tests/acceptance/T-001/catalog.test.ts` com `acceptance-change` cujo último `labeled` é de `versix-agent` → `acceptance-freeze` 1 com `rótulo acceptance-change aplicado por versix-agent; exige o fundador`; de `fundador-versix` → 0; `fundador-versix` às 12:00 e `versix-agent` reaplica às 12:05 → 1; sem rótulo → 1 listando o arquivo; só `A tests/acceptance/T-005/inbox.test.ts` → 0; `R100 tests/acceptance/T-001/world.ts → tests/acceptance/T-001/mundo.ts` sem rótulo → 1. `label-guard`: `api-breaking` de `versix-agent` → 1 `rótulo api-breaking aplicado por versix-agent; exige o fundador`; `FOUNDER_LOGIN` vazio e `hotfix` presente → 1 `FOUNDER_LOGIN não configurada` |
| `review-record.test.ts` (CT-QLD-007) | PR N0 (`M packages/db/src/context.ts`) com "Implementado por: anthropic/claude-code/claude-opus-5-5": única revisão `## Revisão cruzada — anthropic/claude-code/claude-opus-5-5 — 2026-10-20` → 1 `revisor do mesmo fornecedor`; `openai/codex/modelo-x` com `Commit revisado: b…b` → 1 `revisão desatualizada`; com `a…a` e `APROVAR` → 0; com `BLOQUEAR` → 1 `veredito BLOQUEAR`; `APROVAR` às 10:00 e `BLOQUEAR` às 11:00, ambos em `a…a` → 1; PR só com `docs/spec/10-apps-e-ux.md` e sem revisão → 0 `N2: revisão cruzada opcional`; N1 (`M apps/api/src/fleet/vehicles.ts`) com `hotfix` do fundador e sem revisão → 0 e `hotfix_issue=true`; N0 com `hotfix` → 1 |
| `acceptance-match.test.ts` (CT-QLD-004) | Base com `tasks/T-005-ingestao.md` cujo bloco de `tests/acceptance/T-005/dedupe.test.ts` contém `expect(rows).toBe(1)`; head com o arquivo trazendo `expect(rows).toBeGreaterThanOrEqual(1)` → 1 listando `tests/acceptance/T-005/dedupe.test.ts`; head que também troca o bloco no cartão → continua 1; arquivo idêntico (bloco + `\n`) → 0; `tests/acceptance/T-005/extra.test.ts` → 1 `sem bloco no cartão em origin/main`; `it.todo(` num arquivo novo → 1; cartão T-006 só com tabela e arquivo novo em `tests/acceptance/T-006/` → 0 com `aviso:` contendo `modo tabela`; arquivo de `T-077` sem cartão na base → 1 `cartão T-077 ausente em origin/main`. Modo tabela: PR cujo 1º commit `test(ci): aceite congelado (T-006)` cria `tests/acceptance/T-006/a.test.ts` e cujo head tem o mesmo arquivo byte a byte → 0; head com o arquivo alterado num commit posterior → 1 listando `tests/acceptance/T-006/a.test.ts`; o mesmo com `acceptance-change` do fundador → 0; 1º commit que também toca `apps/api/x.ts` → 1 `1º commit do PR não é o de aceite congelado (T-006)` |
| `docs-check.test.ts` (CT-QLD-001, CT-QLD-020) | `docs-check` na raiz deste repositório → 0. Árvore mínima temporária (`AGENTS.md`, `CLAUDE.md` com `@AGENTS.md`, 15 com DEC-03 e DEC-12): `[x](99-inexistente.md)` na linha 3 de `docs/spec/07-alertas-e-tempo-real.md` → 1 com `docs/spec/07-alertas-e-tempo-real.md:3: link quebrado → 99-inexistente.md`; o mesmo link dentro de bloco de código → 0; `CLAUDE.md` sem `@AGENTS.md` → 1. DEC-03 `Resolvida` → 1 citando `DEC-03`; `Resolvida — 09/10/2026 — conta individual` → 0; DEC-12 `Aberta` com prazo `10/10/2026` e `DOCS_CHECK_TODAY=2026-10-11` → 0 e stdout `aviso: DEC-12 vencida em 10/10/2026`. 16 do head diferente do gerado pelo `trace.py` → 1 `16-rastreabilidade.md desatualizado`; igual → 0. Link `[x](04-dominio.md#44-funcoes)` com título `## 4.4 Funcoes` no destino → 0; `#99-inexistente` → 1 `âncora inexistente` |
| `tasks-lint.test.ts` (CT-QLD-002, CT-QLD-011) | Árvore com `docs/spec/05-ingestao.md` definindo `### REQ-ING-005 — Exemplo` e `tasks/T-099-exemplo.md` completo → 0; `\| Estimativa \| 4 sessões de agente \|` → 1 `T-099: estimativa 4 > 3 — dividir`; sem `## Decisões já tomadas` → 1; `Requisitos` com `REQ-XYZ-999` → 1 citando `REQ-XYZ-999`; `## Fora do escopo` antes de `## Escopo — fazer` → 1 `fora de ordem`; seção extra `## Pré-requisitos do ambiente` → 0; rascunho com `## Para completar o DoR` e sem as seções finais → 0 com `aviso: T-099: rascunho`. Cartão que lista `packages/db/migrations/`, contém `CREATE TABLE app.alert` e cita só ISO-01 e ISO-03 → 1 citando `ISO-02`, `ISO-04` e `ISO-05`; citando as cinco → 0. `vi.mock('pg')` em `tests/acceptance/T-011/alerts.test.ts` → `no-db-mock` sai com 1 citando o arquivo e a linha |
| `migration-lint.test.ts` (CT-DAD-021) | `rollback-new-migrations`: base com 1 migration e head com 3 → stdout `rollback: 2 migrations novas` e `dbmate rollback` chamado 2 vezes (`dbmate` falso no `PATH`); head sem migration nova → 1 chamada. Base com `packages/db/migrations/20261007120000_fundacao_isolamento.sql` válida (cabeçalhos e os dois `SET LOCAL`); head acrescenta `20261020090000_position_idx.sql` com cabeçalhos e `CREATE INDEX position_vehicle_idx ON app.position (vehicle_id);` → 1, stderr com `regra 6` e `20261020090000_position_idx.sql`; com `CREATE INDEX CONCURRENTLY`, `transaction:false` e `SET lock_timeout` → 0; um espaço alterado em `20261007120000_fundacao_isolamento.sql` → 1 citando `regra 1`; nova sem `lock_timeout` → `regra 2`; nova sem `-- migrate:down` → `regra 1`; `CREATE TABLE app.outbox` com índice no mesmo arquivo → 0; `ALTER TABLE app.audit_log ADD COLUMN x timestamptz DEFAULT now()` → `regra 6` |
| `agent-env.test.ts` (CT-QLD-016 parte 1) | `agent-env-check` com env `{ PATH, HOME }` → 0 `Ambiente do agente sem credencial de produção.`; com `ASAAS_API_KEY=chave-de-teste-0123456789abcdef` → 1, stderr contém `ASAAS_API_KEY` e não contém `chave-de-teste`; idem para `SOPS_AGE_KEY`, `BETTER_AUTH_SECRET`, `DATABASE_URL_APP` e `MIGRATE_DATABASE_URL`; `OUTRA=AGE-SECRET-KEY-1QQQQ` → 1 citando `OUTRA`. Todo `.github/workflows/*.yml` com gatilho `pull_request`, `pull_request_target` ou `issue_comment` só referencia `secrets.GITHUB_TOKEN` |
| `branch-protection.test.ts` (CT-QLD-008) | `gh` falso no `PATH` devolvendo JSON fixo: proteção com `required_approving_review_count = 1`, `require_code_owner_reviews = true`, `required_linear_history.enabled = true`, `allow_force_pushes.enabled = false`, `enforce_admins.enabled = true`, `contexts` com todos os de `.github/required-checks.txt` e repositório só com squash → `check-branch-protection.sh` sai 0 com `proteção de main OK`; `allow_force_pushes.enabled = true` → 1 `desvio: allow_force_pushes.enabled = true (esperado false)`; sem `review-record` em `contexts` → 1; `allow_merge_commit = true` → 1 |
| `risk-review.test.ts` (CT-QLD-021) | 15 mínimo com R-07 e R-16 (gatilho `< 12 testadores ativos em 24/10/2026 → recrutar na Lider e entre conhecidos`). `2026-10-26.md` com R-16 `sim`, ação `recrutar na Lider`, e R-07 `não` → `--check` 0 e stdout `R-16 disparado — ação: recrutar na Lider`; 26/10 e `2026-11-02.md` com R-16 `sim`, ação `—` e `Cartão ou DEC` `—` → 1 `R-16 disparado sem ação em 26/10/2026 e 02/11/2026: exige cartão de tarefa ou DEC`; o mesmo com `T-032` e `tasks/T-032-recrutar-testadores.md` existente → 0; com `T-099` inexistente → 1; 02/11 sem R-07 → 1 `revisão 2026-11-02: falta R-07`. `--issue` gera `- [ ] R-16 — < 12 testadores ativos em 24/10/2026 → recrutar na Lider e entre conhecidos` |
| `questions.test.ts` (CT-QLD-018) | `questions.ndjson` vazio → `docs-check` sem erro de perguntas e stdout `perguntas: 0` (estado exigido no merge da T-001); `{"number":12,"title":"feat(ingestion): inbox e projeção (T-005)","state":"CLOSED"}` sem `Q#12` → 1 `pergunta #12 (T-005) sem resposta registrada em tasks/ ou AGENTS.md (cite Q#12)`; com `\| O 202 sai antes ou depois do savepoint? (Q#12) \| Depois do COMMIT do savepoint. \|` em `tasks/T-011-motor.md` → 0 e `perguntas: 1, todas registradas` |

## Comandos de verificação

```bash
pnpm install && cp .env.example .env && pnpm db:up
pnpm agent:env-check     # Ambiente do agente sem credencial de produção.
pnpm lint && pnpm typecheck
pnpm db:lint             # Migrations OK: <n> arquivos (0 novos)
pnpm tasks:lint          # Cartões OK: <n> cartões (<r> rascunhos)
pnpm docs:check          # Docs OK: … sem problema. (avisos de DEC vencida não falham)
pnpm risk:review --check # Revisões semanais OK (ou: nenhuma revisão registrada)
pnpm exec vitest run --config tests/vitest.config.ts tests/acceptance/T-019   # Test Files 12 passed
pnpm verify              # T-001 e T-019 verdes
# depois do merge, pelo fundador:
bash infra/scripts/check-branch-protection.sh   # proteção de main OK
```

## Definição de pronto

- Testes de `tests/acceptance/T-019/` no 1º commit, lidos pelo fundador antes da implementação e intactos depois; comandos acima verdes, local e no CI.
- Revisão adversarial de outro fornecedor focada em: guarda que o PR consegue desligar para si; `guards.yml` executando código do head; falha aberta em entrada inválida ou `FOUNDER_LOGIN` vazio. Leitura humana linha a linha de `.github/**` e `scripts/ci/**`.
- PR canário (rascunho, fechado sem merge) com evidência em comentário no PR da T-019: (a) N2 declarado N2 → tudo verde; (b) migration declarada N2 → `risk-label` vermelho; (c) `tests/acceptance/T-001/catalog.test.ts` alterado com `acceptance-change` de `versix-agent` → `acceptance-freeze` e `label-guard` vermelhos, verdes depois que o fundador reaplica; (d) revisão do mesmo fornecedor → `review-record` vermelho; (e) comentário de revisão novo atualiza `review-record` sem push.
- Proteção de `main` configurada com `.github/required-checks.txt` e o script saindo com 0. `CODEOWNERS` com `* @<FOUNDER_LOGIN>`.
- PR `ci: guardas de processo no CI (T-019)`, branch `t-019-guardas-de-processo-no-ci`, REQ/CT listados, risco N0 e as respostas dos [VALIDAR].

## Plano de rollback

1. Falso positivo bloqueando trabalho: o fundador tira só o contexto daquela guarda da proteção de `main` (nunca `verify` nem `acceptance-freeze`), registra no PR afetado e abre `fix(ci): … (T-019)`; recoloca o contexto no merge da correção.
2. Defeito geral: PR `revert: … (T-019)` (N0) do squash. Volta o `ci.yml` da T-001 e remove `guards.yml` e `weekly.yml`; antes do merge do revert, o fundador tira da proteção os contextos que só a T-019 publica (senão todo PR fica esperando status).
3. Achado de segurança em `guards.yml`: `gh workflow disable guards` imediato pelo fundador, retirada dos contextos e correção por PR N0.
4. Banco e produção não mudam: o rollback não toca dado.

## Decisões já tomadas

| Dúvida provável | Resposta |
|---|---|
| Como identificar o fundador? | Variável de repositório `FOUNDER_LOGIN` (`vars.FOUNDER_LOGIN`), não segredo. Vazia = nenhum rótulo de exceção vale (falha fechada). |
| Quais caminhos são N0? | Os globs da 14 §6, mais `scripts/ci/**`, `scripts/trace.py`, `biome.json`, `tests/vitest.config.ts`, `infra/scripts/check-branch-protection.sh`, `biome.json` e `package.json` com `scripts` alterados: todos desligariam guardas (alavancagem). Exceção aditiva: `package.json` só com scripts novos e `biome.json` só com regra nova (sem desligar nenhuma) são N1 (seção 4). A 14 §6 recebe a mesma lista e a exceção. |
| Ferramentas? | TypeScript em `scripts/ci/` com `tsx` (T-001); `zod` na raiz com a versão de `packages/db` (não é biblioteca nova). Sem `yaml` nem `minimatch`: `risk-paths.yml` tem formato fechado e o glob é próprio (`**`, `*`, `?`). `gh`, `jq`, `git` e `python3` do runner. |
| Por que `pull_request_target`? | Para o PR não desligar a guarda que o julga: workflow e scripts vêm de `main`; o head é só lido (sem `pnpm install` do head, `persist-credentials: false`). Status publicado no SHA do head. [VALIDAR — status de commit publicado por `pull_request_target`/`issue_comment` satisfaz o check obrigatório de mesmo nome; `issue_comment` roda o workflow de `main`.] |
| Por que `acceptance-freeze` fica no `ci.yml`? | Compatibilidade com a T-001 e bootstrap: no PR da T-019 a base ainda não tem `guards.yml`, então só `verify` e `acceptance-freeze` o julgam. Ganha `labeled`/`unlabeled`; `verify` roda de novo nesses eventos (rótulo manual é raro e rótulo do `GITHUB_TOKEN` não dispara workflow). Nunca pular `verify` por `if:` em evento de rótulo: job pulado conta como verde. |
| Quando um rótulo de exceção vale? | Presente no PR e com o `labeled` mais recente feito por `FOUNDER_LOGIN` (REQ-QLD-006). Rótulo de outra conta não é removido, só ignorado; o `label-guard` fica vermelho até o fundador reaplicar. Vale para `acceptance-change`, `api-breaking` e `hotfix`. |
| A T-002 já estendeu o `acceptance-freeze` para as fixtures? | O script cobre `tests/acceptance/**` e `packages/testkit/fixtures/**` de qualquer forma; o passo antigo é substituído. |
| REQ-QLD-006 e REQ-DAD-021 são F1 nos capítulos | A T-019 os antecipa para o F0 : custo baixo e proteção desde a primeira migration do piloto. |
| Cartão em modo tabela (sem blocos)? | O 1º commit do PR (`test(<escopo>): aceite congelado (T-NNN)`) só toca `tests/acceptance/T-NNN/**`, é escrito por agente de outro fornecedor e vale como referência: o `acceptance-match` compara o head com ele byte a byte. Cartão com blocos (T-001, T-016) compara com o cartão de `origin/main`. Em N0, o fundador lê o 1º commit linha a linha. |
| O Biome reformatou um teste copiado? | Defeito do cartão: o bloco já tem de estar formatado. Corrige-se o cartão com `acceptance-change`; nunca deixar o arquivo divergir do bloco. |
| Tamanho do PR? | `scripts/ci/**` ≈ 600 linhas, acima das 400 da 14 §4 regra 3: três fatias em PRs sequenciais ("## Fatias"), scripts independentes, ≤ 80 linhas cada, um teste por guarda. Se o fundador recusar, a fatia 3 (REQ-QLD-008, 016, 018 e 021) segue sozinha em PR próprio. |
| Testes antes da implementação (N0) sem quebrar `main`? | 1º commit de cada PR de fatia com os testes dela (vermelhos), lido pelo fundador; depois a implementação. PR de testes separado quebraria o `verify` de `main`. |
| Qual é "hoje" para prazos de DEC e revisão? | Data civil de `America/Sao_Paulo` (os prazos da 15 são datas de Brasília); `DOCS_CHECK_TODAY` só em teste. |
| `DATABASE_URL_APP` existe no `.env` local; o `agent:env-check` acusa? | Não. A checagem é por nome no ambiente do processo, antes de qualquer `.env`; o `.env` é lido dentro do processo (`loadDbEnv`, T-001) e não aparece no `env` da sessão. Nunca dar `export` do `.env` no shell do agente. |
| Onde fica o registro da revisão semanal? | `docs/runbooks/revisao-semanal/AAAA-MM-DD.md` (seção 5.6), em PR N2 do fundador. A issue semanal é o lembrete; o arquivo é o registro. |
| Como ligar a pergunta ao "próximo cartão do mesmo assunto"? | O CI não infere assunto: exige `Q#<n>` em algum cartão ou no `AGENTS.md` antes de qualquer merge (`docs-check`); escolher o cartão certo é do fundador (CT-QLD-018 parte 2). |
| Proteção de `main` pelo CI? | Não: ler a proteção exige administrador; o script roda com o `gh` do fundador e é lembrado toda semana [VALIDAR — permissão do endpoint de proteção]. |
| `migration-compat` e `migration-safety` entram aqui? | Não. O job `migration-compat` (REQ-DAD-020: aceite do commit base contra o schema novo) e o `migration-safety` são da T-013; esta tarefa não os duplica. O `migration-lint` (REQ-DAD-021) é daqui. |
| Commits | `test(ci): aceite congelado (T-019)`, `ci: guardas e workflows (T-019)`; título do PR `ci: guardas de processo no CI (T-019)`. |
