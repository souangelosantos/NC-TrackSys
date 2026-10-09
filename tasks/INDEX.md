# Índice de tarefas (T-001 a T-034)

Lista de todos os cartões do F0 e do F1. No F0 o índice traz só ID, título, status e link; fase, dependência e risco estão em 02 §2.3. No F1 a tabela é completa. Para o processo de cada cartão (DoR, DoD e template), veja [README.md](README.md).

**Quem é dono do quê.** No F0, fase, dependência, risco, caminho crítico e donos de fronteira estão em [02 §2.3](../docs/spec/02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0). No F1, vale o cabeçalho de cada cartão. A janela da quinzena vem de [02 §4.2](../docs/spec/02-escopo-e-fases.md#42-plano-por-quinzena). Risco usa só N0, N1 e N2; "(caminho)" é N0 pelo caminho dos arquivos ([14 §6](../docs/spec/14-qualidade-e-processo-ia.md#6-níveis-de-risco)).

## Regra para cartão resumido

**Cartão resumido não é implementado antes de cumprir o DoR.** Vale para T-020 a T-031, T-033 e T-034.
- Têm escopo, requisitos e dependências fixados, mas não têm especificação detalhada, testes congelados nem "Decisões já tomadas".
- Cada um passa pelo [DoR](README.md) nas datas do calendário abaixo e perde a seção "Para completar o DoR", que lista as lacunas concretas dele.
- Antes disso, nenhum agente abre branch nem PR de implementação a partir dele.
- O `tasks:lint` da [T-019](T-019-guardas-de-processo-no-ci.md) trata esses cartões como rascunho.

## Cartões do F0

Fase, dependência e risco: [02 §2.3](../docs/spec/02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0).

| ID | Título | Status |
|---|---|---|
| [T-001](T-001-fundacao-monorepo-e-isolamento.md) | Fundação: monorepo, Postgres local e isolamento em 3 níveis | Pronto (DoR) |
| [T-002](T-002-spike-j16-bancada.md) | Spike J16 em bancada: capturas, `capability_profile` draft | Pronto (DoR) |
| [T-003](T-003-vm-primaria-compose-firewall-dns.md) | VM primária, Docker Compose, firewall e DNS | Pronto (DoR) |
| [T-004](T-004-contratos-e-esqueleto-api-worker.md) | Contratos iniciais (Zod → OpenAPI 3.1 → clientes TS e Dart) e esqueleto de `api` e `worker` | Pronto (DoR) |
| [T-005](T-005-ingestao-traccar-inbox-projecao.md) | Ingestão Traccar → `ingest_inbox` → `position`/`device_state`/`outbox` | Pronto (DoR) |
| [T-006](T-006-autenticacao-e-contexto-rls.md) | Autenticação (Better Auth) e contexto RLS por requisição | Pronto (DoR) |
| [T-007](T-007-console-login-e-cadastro.md) | Console: login e cadastro de cliente, veículo, rastreador e vínculo | Pronto (DoR) |
| [T-008](T-008-console-mapa-ao-vivo-e-historico.md) | Console: mapa ao vivo (SSE) e histórico por veículo/dia | Pronto (DoR) |
| [T-009](T-009-app-login-lista-mapa-ao-vivo-marca.md) | App: login, lista, mapa ao vivo com estados honestos e marca básica da operadora | Pronto (DoR) |
| [T-010](T-010-app-historico-e-deep-links.md) | App: histórico do dia e deep links (WhatsApp da central e navegação) | Pronto (DoR) |
| [T-011](T-011-motor-de-alertas-f0.md) | Motor de alertas do F0 | Pronto (DoR) |
| [T-012](T-012-push-fcm-tokens-e-entregas.md) | Push no servidor: migration, `claim_push_token`, rotas, `alerts.deliver` e FCM | Pronto (DoR) |
| [T-032](T-032-app-push-alertas-vigilancia-notificacoes.md) | App: push, telas de alertas (A05), modo vigilância (A06) e notificações (A09) | Pronto (DoR) |
| [T-013](T-013-deploy-backup-restore-sondas.md) | Deploy por tag, backup WAL-G, restore testado, sondas e limites de recurso | Pronto (DoR) |
| [T-014](T-014-migracao-manual-sms-e-rollback.md) | Migração manual por SMS, rollback e `pilot provision` | Pronto (DoR) |
| [T-015](T-015-consultas-g0-e-relatorio-de-evidencias.md) | Consultas do G0 e relatório de evidências | Pronto (DoR) |
| [T-019](T-019-guardas-de-processo-no-ci.md) | Guardas de processo no CI | Pronto (DoR); 3 fatias (`t-019-1`, `t-019-2`, `t-019-3`) e corte 0a |

## Cartões do F1

| ID | Título | Quinzena | Risco | Depende de | Status |
|---|---|---|---|---|---|
| [T-016](T-016-dominio-de-comandos.md) | Domínio de comandos puro: avaliador, máquina de estados e textos | 01–15/11 | N0 | T-002, T-004 | Pronto (DoR) |
| [T-017](T-017-migration-f1-comandos.md) | Migration do F1 de comandos, chave do aparelho, consentimento e segredos da operadora | 01–15/11 | N0 | T-005, T-006, T-016 | Pronto (DoR) |
| [T-018](T-018-api-de-comandos-e-step-up.md) | API de comandos com step-up, chave do aparelho e termo de ciência | 01–15/11 | N0 | T-004, T-006, T-016, T-017 | Pronto (DoR) |
| [T-020](T-020-despachante-de-comandos-no-worker.md) | Despachante de comandos no worker | 01–15/11 | N0 | T-005, T-016, T-017, T-018; DEC-01 (só SMS automático) | Resumido — DoR pendente |
| [T-021](T-021-ux-de-comando-app-e-console.md) | UX de comando no app e no console | 01–15/11 | N0 | T-007, T-009, T-018 | Resumido — DoR pendente |
| [T-022](T-022-homologacao-j16-e-g-cmd.md) | Homologação do perfil J16 em bancada e checklist do G-CMD (tarefa mista) | 16–30/11 | N0 | T-002, T-020, T-021; DEC-07 | Resumido — DoR pendente |
| [T-023](T-023-cobranca-asaas-split-pix.md) | Cobrança Asaas: vínculo, webhooks, inadimplência, PIX no app e split | 01–15/11 | N0 | T-006, T-007, T-017; DEC-06, DEC-14 | Resumido — DoR pendente |
| [T-024](T-024-importador-e-ondas-de-migracao.md) | Importador de planilha, ondas de migração por SMS e código de ativação para titular sem e-mail | 01–30/11 | N0 | T-007, T-014, T-022 (só veículos com bloqueio); DEC-01, DEC-10 | Resumido — DoR pendente |
| [T-025](T-025-ocorrencia-busca-e-compartilhamento.md) | Modo ocorrência, visão da equipe de busca e compartilhamento temporário | 16–30/11 | N0 | T-008, T-009, T-017, T-020 | Resumido — DoR pendente |
| [T-026](T-026-guincho-parceiro-e-indicacoes.md) | Guincho parceiro: botão no app, indicação, consentimento e relatório mensal | 16–30/11 | N0 | T-009, T-017, T-023; DEC-05 | Resumido — DoR pendente |
| [T-027](T-027-auditoria-suporte-legal-hold-e-retencao.md) | Auditoria, acesso de suporte, legal hold, `access_log` para ordem judicial e retenção quente/frio | 01–15/12 (retenção quente/frio até 31/01/2027) | N0 | T-005, T-006, T-012; DEC-15 | Resumido — DoR pendente |
| [T-028](T-028-standby-failover-slo-e-agente-sre.md) | Standby, failover com fencing, sonda, minuto ruim e status page | 01–15/11 (SLO medido desde 01/12) | N0 | T-003, T-005, T-013, T-015; DEC-12 | Resumido — DoR pendente |
| [T-029](T-029-console-f1-carteira-atendimento-e-alertas.md) | Console do F1: carteira completa, atendimento, marca, cercas, alertas novos, crítico à central (Pushover) e lista "sem comunicação" | 01–30/11 | N0 (caminho) | T-007, T-008, T-011, T-012, T-013 | Resumido — DoR pendente |
| [T-030](T-030-lojas-qualidade-e-versao-minima.md) | Publicação nas lojas, versão mínima do app e E2E | 16–30/11 | N1 | T-009, T-010, T-012, T-032; DEC-03, DEC-04 | Resumido — DoR pendente |
| [T-031](T-031-unidade-economica-e-custos.md) | Relatório de unidade econômica e conta de armazenamento | 01–15/12 | N0 (caminho) | T-023, T-027 | Resumido — DoR pendente |
| [T-033](T-033-operacao-avancada-deploy-observabilidade-carga.md) | Operação avançada: deploy automatizado com rollback, Alloy/Grafana/Alertmanager, migration-compat, teste de carga e cópia R2 | 01–15/11 ou 16–30/11 | N0 (caminho) | T-013, T-019 | Resumido — DoR pendente |
| [T-034](T-034-gateway-de-incidentes-e-agente-sre.md) | Gateway de incidentes e agente SRE de diagnóstico | 01–15/12 | N0 | T-028; DEC-13 | Resumido — DoR pendente |

## Calendário do DoR do F1

Cada cartão resumido tem um redator (agente de fornecedor diferente do que vai implementá-lo), uma data de rascunho e uma data até a qual o fundador lê os testes. No máximo 3 cartões N0 ficam em revisão ao mesmo tempo ([15](../docs/spec/15-decisoes-riscos-premissas.md) R-19). T-020, T-021, T-023 e T-028 são redigidos em paralelo ao S3, sem tocar arquivos do F0.

| Cartão | Redator (agente/fornecedor) | Rascunho até | Fundador lê testes até | Lacunas a fechar |
|---|---|---|---|---|
| T-020 | Codex / OpenAI | 23/10 | 27/10 | Contrato do despachante (`command_attempt`, `command_event`), retries no `pg-boss`, `COMMAND_DISPATCH_ENABLED`, SMS automático só com DEC-01, CT de idempotência, UNKNOWN e não repetição de bloqueio |
| T-021 | Claude Code / Anthropic | 23/10 | 27/10 | Estados e textos de comando (`texts.ts`), step-up no app e no console, aviso de moto e de chave nova, testes de widget e de E2E |
| T-023 | Codex / OpenAI | 23/10 | 27/10 | DDL de `billing_account`, `billing_customer`, `invoice`, `platform_fee` e `operator_price` com `suspended_fee_policy`; webhooks Asaas; CT-COB-NNN em blocos |
| T-028 | Claude Code / Anthropic | 23/10 | 27/10 | Replicação e fencing da standby, runbook de failover, sonda externa, minuto ruim, status page, DDL de `ops`, CT |
| T-022 | Codex / OpenAI | 06/11 | 12/11 | Formato do `manifest.json`, kit `homologation:check`, migration N0 do perfil J16, `G-CMD.md` com GC-1 a GC-8, DEC-07 |
| T-024 | Claude Code / Anthropic | 06/11 | 12/11 | DDL de `migration_wave` e `migration_item` (`password_rotated_at`), layout da planilha do tracker-net, código de ativação, janela de onda com feriados, CT-ONB |
| T-025 | Codex / OpenAI | 06/11 | 12/11 | DDL de `occurrence` e do link de compartilhamento, permissões da equipe de busca, TOTP do console, CT |
| T-026 | Claude Code / Anthropic | 06/11 | 12/11 | DDL de indicação, consentimento, relatório mensal, regra de divisão (DEC-05), CT |
| T-029 | Codex / OpenAI | 06/11 | 12/11 | Rotas e telas C02 (filtro > 24 h / > 7 dias, CSV), atendimento, cercas, Pushover de emergência (REQ-ALR-024), fila C08, CT-ALR-024 |
| T-030 | Claude Code / Anthropic | 06/11 | 12/11 | Checklists das lojas, versão mínima do app, roteiros de E2E; sem SQL nem rotas novas |
| T-033 | Codex / OpenAI | 06/11 | 12/11 | `deploy.yml` com rollback, Alloy/Grafana/Alertmanager, `migration-compat`, `load-test.yml` e cópia R2 |
| T-027 | Claude Code / Anthropic | 20/11 | 26/11 | `retention_purge`, legal hold, `app.export_access_log`, Parquet cifrado com age, DDL, CT, DEC-15 |
| T-031 | Codex / OpenAI | 20/11 | 26/11 | DDL de `platform_cost`, fórmulas do relatório, conta de armazenamento |
| T-034 | Claude Code / Anthropic | 20/11 | 26/11 | Gateway Worker com D1, cardápio somente leitura do agente, CT-DAD-012 |

## Ordem sugerida de execução no F0

Segue o cronograma de [02 §2.2](../docs/spec/02-escopo-e-fases.md#22-cronograma-semanal) e as dependências de [02 §2.3](../docs/spec/02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0), que também traz o caminho crítico (duas cadeias que se juntam). Na mesma linha, as tarefas podem correr em paralelo, cada uma na sua branch (ou fatia).

| Semana | Ordem | Marco de fim |
|---|---|---|
| **S1** 07–13/10 | 1. T-001 (primeira tarefa do repositório). Em paralelo, desde o 1º dia: T-002 (bancada do fundador) e T-003 (depois da DEC-12, 10/10). 2. Depois da T-001: T-004 e a fatia 1 da T-019. | 13/10: resultado do spike registrado; posição do J16 de bancada visível no Traccar da VM |
| **S2** 14–20/10 | 1. T-005 e T-006 em paralelo (as duas dependem da T-004; a T-005 também da T-002). 2. T-007 (precisa das tabelas da T-005 e da fatia 1 da T-006). 3. T-008 (usa o esqueleto do console da T-007; plano B: esqueleto mínimo) e T-009 em paralelo (plano B da T-009: fixtures até a T-008 entregar estado e SSE). 4. T-019 fatias 2 e 3, até 20/10 (corte 0a as leva ao F1). | 20/10: primeira fatia vertical demonstrada (REQ-NEG-014) |
| **S3** 21–27/10 | 1. T-011 (caminho crítico; precisa da T-007 e da T-008) e, em paralelo, T-010 e T-013. 2. T-014 começa: 1º veículo e rollback em 22/10. 3. T-012 depois da T-011 (caminho crítico) e T-032 depois da T-012 e da T-009. | 27/10: alerta provocado chega ao celular; restore registrado |
| **S4** 28–31/10 | 1. T-014 em execução: 5 a 10 veículos transmitindo até 29/10, 12:00 BRT (prazo duro da janela de 48 h). 2. T-015 (consultas e relatório). 3. Avaliação do G0 em 31/10, depois das 12:00 BRT. | 31/10: G0 |

## Ordem de referência no F1

Os cartões do F1 só entram em execução depois do DoR (regra acima). A ordem abaixo é referência. Quem manda nas entregas por quinzena é [02 §4.2](../docs/spec/02-escopo-e-fases.md#42-plano-por-quinzena).

| Quinzena | Ordem |
|---|---|
| 01–15/11 | Cadeia de comandos: T-016 → T-017 → T-018 → T-020, com a T-021 depois da T-018. Em paralelo: T-023, T-028 (a sonda, a latência de alerta e o minuto ruim precisam estar ativos até 01/12) e o início da T-024 e da T-029 (crítico à central por Pushover, REQ-ALR-024). |
| 16–30/11 | T-022 (G-CMD; libera o bloqueio na Lider e as ondas com veículos que têm bloqueio), T-024 (ondas), T-025, T-026, T-029, T-030 e T-033. |
| 01–15/12 | T-027 (auditoria, legal hold e retenção), T-031 e T-034 (gateway de incidentes e agente SRE). |
| até 31/01/2027 | T-027: retenção quente/frio operando (1º Parquet mensal exportado). |

## Manutenção

Quem cria, divide ou renumera um cartão atualiza este índice e a tabela de [02 §2.3](../docs/spec/02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0) no mesmo PR. O `docs-check` da T-019 confere os links.
