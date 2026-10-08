# T-021 — UX de comando no app e no console

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/11/2026) |
| Requisitos | REQ-UX-017, REQ-UX-018, REQ-UX-019 |
| Invariantes | INV-08, INV-10 |
| Risco de revisão | N0 |
| Depende de | T-018, T-009, T-007 |
| Estimativa | 2 sessões de agente |
| Bloqueado por decisão | nenhuma |
| Status | Resumido — DoR pendente |

## Objetivo

Entregar a experiência de bloqueio e desbloqueio: disponibilidade explicada, deslizar para confirmar, biometria liberando a chave do aparelho (Secure Enclave/Android Keystore), texto do efeito físico conforme o `cut_point`, estados REQUESTED/ARMED/AWAITING_CONFIRMATION/CONFIRMED/UNKNOWN/FAILED com textos distintos e proibição de enfileirar comando com o celular offline. No console, o mesmo fluxo com 2º fator recente e motivo.

## Contexto obrigatório

[10 — Apps e UX](../docs/spec/10-apps-e-ux.md) (UX de comando); [08 §5](../docs/spec/08-identidade-e-seguranca.md) (chave do aparelho); textos de `packages/domain/src/commands/texts.ts` ([T-016](T-016-dominio-de-comandos.md))

## Escopo — fazer

1. Cadastro e revogação da chave do aparelho no Flutter (T-018 expõe as rotas).
2. Tela de comando no app e no console com textos vindos do domínio, nunca escritos na UI.
3. Acompanhamento do estado por SSE e por consulta, com idade da confirmação.
4. Testes de widget/E2E para cada estado e para o bloqueio com o celular offline (botão desabilitado, nada enfileirado).

## Fora do escopo

- Despacho e confirmação (T-020).
- Homologação física (T-022).

## Para completar o DoR

1. Especificação detalhada (tabelas com SQL, rotas, jobs e textos) a partir dos capítulos citados.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-021/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 6 respostas.
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
