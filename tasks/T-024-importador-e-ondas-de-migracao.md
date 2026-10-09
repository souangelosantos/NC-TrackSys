# T-024 — Importador de planilha e ondas de migração por SMS

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–30/11/2026) |
| Requisitos | REQ-ONB-002 a REQ-ONB-007, REQ-ONB-010 a REQ-ONB-014, REQ-ONB-017, REQ-ONB-018, REQ-ONB-020; job automático de provisionamento no Traccar (sem REQ próprio; [03 §4](../docs/spec/03-arquitetura.md) módulo `fleet`) [ADOTADO NA v2.0] |
| Invariantes | INV-03, INV-07, INV-10 |
| Risco de revisão | N0 |
| Depende de | T-007, T-014, T-022 (só para veículos com bloqueio) |
| Estimativa | 3 sessões de agente |
| Bloqueado por decisão | DEC-01 (ondas automáticas), DEC-10 |
| Status | Resumido — DoR pendente |

## Objetivo

Importar a base da operadora a partir da planilha exportada do tracker-net (XLSX/CSV, mapeamento de colunas, validação por linha, prévia, commit idempotente) e migrar os rastreadores em ondas de até 20 veículos: SMS de troca de servidor (API emnify ou envio manual), espera do 1º contato por 10 min, rollback automático e disjuntor da onda.

## Contexto obrigatório

[11 — Onboarding e migração](../docs/spec/11-onboarding-e-migracao.md); [02 §4](../docs/spec/02-escopo-e-fases.md) (REQ-NEG-015); [02 §2.3](../docs/spec/02-escopo-e-fases.md) (provisionamento no Traccar); [03 §4](../docs/spec/03-arquitetura.md) (módulo `fleet` no worker); [T-014](T-014-migracao-manual-sms-e-rollback.md) (procedimento manual do piloto e subcomando `pilot provision`)

## Escopo — fazer

1. Tabelas `import_job`, `migration_wave`, `migration_item` com RLS forçada.
2. Importador com relatório de erros por linha e idempotência por linha.
3. Ondas com pré-checagem (domínio definitivo, senha SMS, perfil homologado para quem tem bloqueio).
4. Mensagem pronta de aviso aos clientes da operadora.
5. Job automático do `worker` que provisiona no Traccar todo rastreador criado no console ou pelo importador: cria o dispositivo pela API do Traccar e grava `device.traccar_device_id` como `tracksys_app` com contexto da operadora (`provisioning` de `pending` para `done`), idempotente por rastreador. Substitui, no F1, o subcomando manual `pilot provision` da T-014 e reutiliza `provisionDevice` de `apps/worker/src/fleet/provision-device.ts` (T-014), sem reescrever a chamada à API do Traccar nem a gravação de `device.traccar_device_id`; o item `traccar_not_provisioned` da pré-checagem da onda (CT-ONB-010) continua valendo.

## Fora do escopo

- Importadores de outras plataformas (F2).
- Migração de histórico do tracker-net (não migra).

## Para completar o DoR

1. Especificação detalhada (tabelas com SQL, rotas, jobs e textos) a partir dos capítulos citados.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-024/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md)).
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
