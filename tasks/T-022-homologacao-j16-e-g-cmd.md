# T-022 — Homologação do perfil J16 em bancada e checklist do G-CMD (tarefa mista)

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 16–30/11/2026) |
| Requisitos | REQ-NEG-011, REQ-NEG-015, REQ-QLD-014, REQ-CMD-018 (parte de bancada: kit `homologation:check`; o schema do perfil é da T-016) |
| Invariantes | INV-08, INV-10 |
| Risco de revisão | N0 |
| Depende de | T-020, T-021, T-002 |
| Estimativa | 1 sessão de agente + bancada do fundador |
| Bloqueado por decisão | DEC-07 |
| Status | Resumido — DoR pendente |

## Objetivo

Homologar o perfil J16 com evidência, na sequência de [06 §13.5](../docs/spec/06-comandos-e-bloqueio.md#135-g-cmd): GC-2 aprovado (20 ciclos na bancada sem falsa confirmação; medição pedido → atuação conforme [06 §3.2](../docs/spec/06-comandos-e-bloqueio.md#32-regra-por-cut_point), regra 3) → migration N0 do fundador cria o perfil `homologated` com `evidence_ref` = `manifest.json` + SHA-256 → deploy N0 com `COMMAND_BLOCK_SCOPE=pilot:<veículo>` → GC-6 (teste supervisionado em 1 veículo da Lider, parado e em movimento ≤ 20 km/h em área fechada, com a mesma medição pedido → atuação) → `docs/runbooks/gates/G-CMD.md` com GC-1..GC-8 `ok` (inclui GC-7, senha SMS antiga não comanda mais, com a evidência do `pilot password` / `pilot preflight --step migrate` da T-014, e GC-8, allowlist da APN na porta 5023 ou risco aceito por escrito em [15](../docs/spec/15-decisoes-riscos-premissas.md)) → deploy N0 com `COMMAND_BLOCK_SCOPE=all`. O agente prepara roteiros, consultas e o relatório; o fundador executa a bancada e aprova.

## Contexto obrigatório

[02 §4.3](../docs/spec/02-escopo-e-fases.md#43-gate-g-cmd-meta-1630112026) (G-CMD); [06 §13](../docs/spec/06-comandos-e-bloqueio.md#13-homologação-do-perfil-e-g-cmd) (homologação); [T-002](T-002-spike-j16-bancada.md)

## Escopo — fazer

1. Roteiro de bancada passo a passo e planilha de evidências.
2. Consultas que extraem `command_event` e velocidade no momento da decisão.
3. Regra de onda que exclui veículo com bloqueio enquanto `COMMAND_BLOCK_SCOPE` não for `all` (REQ-NEG-015).
4. Mudança de `capability_profile.status` só pelo fundador, com `evidence_ref`.
5. Kit de bancada `pnpm --filter @tracksys/testkit homologation:check <dir>` sobre `cycles.csv` e `manifest.json` ([06 §13](../docs/spec/06-comandos-e-bloqueio.md#13-homologação-do-perfil-e-g-cmd); CT-CMD-018, parte de bancada) e runbook `docs/runbooks/gates/G-CMD.md` com GC-1..GC-8 (GC-7 com a evidência da troca de senha da T-014; GC-8 com a allowlist da APN 5023 ou risco aceito) e a medição pedido → atuação de GC-2 e GC-6 (a T-016 deixa os dois fora do escopo dela).

## Fora do escopo

- Qualquer liberação automática de perfil.
- Outros modelos de rastreador (F2).

## Para completar o DoR

1. Lacunas a fechar: texto da migration N0 do perfil J16 `homologated` (campos de `capability_profile` e do `evidence_ref`); roteiros e planilha para GC-1..GC-8, com a consulta de GC-7 (SMS com senha antiga ignorado) e o registro de GC-8; formato de `cycles.csv` e `manifest.json` e os limiares de `homologation:check`; valores de `COMMAND_BLOCK_SCOPE` por etapa; resposta da DEC-07 (moto).
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-022/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md#5-dor-e-dod)).
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
