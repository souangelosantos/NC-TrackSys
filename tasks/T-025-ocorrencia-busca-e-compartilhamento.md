# T-025 — Modo ocorrência, visão da equipe de busca e compartilhamento temporário

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 16–30/11/2026) |
| Requisitos | REQ-UX-020, REQ-UX-023, REQ-UX-029, REQ-SEG-017, REQ-SEG-018, REQ-API-013 |
| Invariantes | INV-05, INV-07, INV-08 |
| Risco de revisão | N0 |
| Depende de | T-008, T-009, T-017 (tabela `occurrence`), T-020 |
| Estimativa | 2–3 sessões de agente |
| Bloqueado por decisão | nenhuma |
| Status | Resumido — DoR pendente |

## Objetivo

Dar à central e à equipe de busca o fluxo de furto/roubo: abrir ocorrência, reduzir o intervalo de transmissão quando o perfil suportar, acompanhar ao vivo na visão móvel da equipe de busca, registrar BO e linha do tempo, compartilhar a localização com família ou polícia por link temporário (token opaco ≥ 256 bits, só hash gravado, TTL padrão 1 h e máximo 24 h, revogação em ≤ 60 s) e exportar histórico de forma assíncrona.

## Contexto obrigatório

[06](../docs/spec/06-comandos-e-bloqueio.md) (ARMED em ocorrência); [08 §6](../docs/spec/08-identidade-e-seguranca.md) (links); [10](../docs/spec/10-apps-e-ux.md) (telas de ocorrência e busca)

## Escopo — fazer

1. Tabela `share_link`; a `occurrence` já nasce na T-017 (com o índice de uma ocorrência aberta por veículo) e aqui só ganha rotas e regras.
2. Rotas de ocorrência, link e sessão pública; página pública sem analytics de terceiros.
3. Visão web responsiva da equipe de busca.
4. Exportação assíncrona de histórico (REQ-API-013).

## Fora do escopo

- Pacote de evidências e legal hold (T-027).
- Bloqueio em si (T-020/T-021).

## Para completar o DoR

1. Especificação detalhada (tabelas com SQL, rotas, jobs e textos) a partir dos capítulos citados.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-025/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 6 respostas.
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
