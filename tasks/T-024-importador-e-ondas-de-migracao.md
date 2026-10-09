# T-024 — Importador de planilha e ondas de migração por SMS

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–30/11/2026) |
| Requisitos | REQ-ONB-002 a REQ-ONB-007, REQ-ONB-010 a REQ-ONB-014, REQ-ONB-017, REQ-ONB-018, REQ-ONB-020, REQ-ONB-021, REQ-ONB-022, REQ-SEG-031; job automático de provisionamento no Traccar (sem REQ próprio; [03 §4](../docs/spec/03-arquitetura.md#4-módulos-do-monólito-e-donos-de-tabelas) módulo `fleet`) |
| Invariantes | INV-03, INV-07, INV-10 |
| Risco de revisão | N0 |
| Depende de | T-007, T-014, T-022 (só para veículos com bloqueio) |
| Estimativa | 3 sessões de agente |
| Bloqueado por decisão | DEC-01 (ondas automáticas), DEC-10 |
| Status | Resumido — DoR pendente |

## Objetivo

Importar a base da operadora a partir da planilha exportada do tracker-net (XLSX/CSV, mapeamento de colunas, validação por linha, prévia, commit idempotente) e migrar os rastreadores em ondas de até 20 veículos: SMS de troca de servidor (API emnify ou envio manual), espera do 1º contato por 10 min, rollback automático e disjuntor da onda.

## Contexto obrigatório

[11 — Onboarding e migração](../docs/spec/11-onboarding-e-migracao.md); [02 §4](../docs/spec/02-escopo-e-fases.md#4-f1--lançamento-lider-0111--31122026) (REQ-NEG-015); [02 §2.3](../docs/spec/02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0) (provisionamento no Traccar); [03 §4](../docs/spec/03-arquitetura.md#4-módulos-do-monólito-e-donos-de-tabelas) (módulo `fleet` no worker); [T-014](T-014-migracao-manual-sms-e-rollback.md) (procedimento manual do piloto e subcomando `pilot provision`)

## Escopo — fazer

1. Tabelas `import_job`, `migration_wave`, `migration_item` com RLS forçada.
2. Importador com relatório de erros por linha e idempotência por linha.
3. Ondas com pré-checagem (domínio definitivo, senha SMS, perfil homologado para quem tem bloqueio), janela só em dia útil sem feriado nacional (REQ-ONB-021; fora dela, 422 `WAVE_OUTSIDE_WINDOW`) e rotação da senha SMS antes do `set_server_domain`, com `migration_item.password_rotated_at` (REQ-ONB-022).
4. Mensagem pronta de aviso aos clientes da operadora.
5. Primeiro acesso por código de ativação (REQ-SEG-031, [08 §2](../docs/spec/08-identidade-e-seguranca.md#2-autenticação-better-auth)): na C03 a central gera o código de 8 caracteres (uso único, 72 h, só o SHA-256 persistido), enviado pelo link `wa.me`; o app troca código + CPF pela definição de senha (5 tentativas em 15 min) e o titular passa a entrar por CPF + senha. Vira P0 do F1 se a P-15 for falsa.
6. Job automático do `worker` que provisiona no Traccar todo rastreador criado no console ou pelo importador: cria o dispositivo pela API do Traccar e grava `device.traccar_device_id` como `tracksys_app` com contexto da operadora (`provisioning` de `pending` para `done`), idempotente por rastreador. Substitui, no F1, o subcomando manual `pilot provision` da T-014 e reutiliza `provisionDevice` de `apps/worker/src/fleet/provision-device.ts` (T-014), sem reescrever a chamada à API do Traccar nem a gravação de `device.traccar_device_id`; o item `traccar_not_provisioned` da pré-checagem da onda (CT-ONB-010) continua valendo.

## Fora do escopo

- Importadores de outras plataformas (F2).
- Migração de histórico do tracker-net (não migra).

## Para completar o DoR

1. Lacunas a fechar: DDL de `import_job`, `migration_wave` e `migration_item` (com `password_rotated_at`); mapeamento de colunas da planilha do tracker-net e CT-ONB em blocos; máquina de estados da onda e do disjuntor; sequência de SMS (`set_password`, `query_params`, `set_server_domain`) [VALIDAR — DEC-02]; formato do código de ativação e rota de troca; calendário `holidays-br.ts`; respostas da DEC-01 e da DEC-10 (isenção na sobreposição).
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-024/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md#5-dor-e-dod)).
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
