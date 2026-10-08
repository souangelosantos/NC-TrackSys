# T-022 — Homologação do perfil J16 em bancada e checklist do G-CMD (tarefa mista)

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 16–30/11/2026) |
| Requisitos | REQ-NEG-011, REQ-NEG-015, REQ-QLD-014 |
| Invariantes | INV-08, INV-10 |
| Risco de revisão | N0 |
| Depende de | T-020, T-021, T-002 |
| Estimativa | 1 (agente) + bancada do fundador sessões de agente |
| Bloqueado por decisão | DEC-07 |
| Status | Resumido — DoR pendente |

## Objetivo

Transformar o perfil J16 de `draft` em `homologated` com evidência: suíte CT-CMD verde, 20 ciclos de bloqueio/desbloqueio na bancada sem falsa confirmação, teste supervisionado em 1 veículo da Lider (parado e em movimento ≤ 20 km/h em área fechada) e registro em `docs/runbooks/gates/G-CMD.md`. O agente prepara roteiros, consultas e o relatório; o fundador executa a bancada e aprova.

## Contexto obrigatório

[02 §4.3](../docs/spec/02-escopo-e-fases.md) (G-CMD); [06 §13](../docs/spec/06-comandos-e-bloqueio.md) (homologação); [T-002](T-002-spike-j16-bancada.md)

## Escopo — fazer

1. Roteiro de bancada passo a passo e planilha de evidências.
2. Consultas que extraem `command_event` e velocidade no momento da decisão.
3. Regra de onda que exclui veículo com bloqueio enquanto o perfil não está homologado (REQ-NEG-015).
4. Mudança de `capability_profile.status` só pelo fundador, com `evidence_ref`.

## Fora do escopo

- Qualquer liberação automática de perfil.
- Outros modelos de rastreador (F2).

## Para completar o DoR

1. Especificação detalhada (tabelas com SQL, rotas, jobs e textos) a partir dos capítulos citados.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-022/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 6 respostas.
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
