# Índice de tarefas (T-001 a T-031)

Lista de todos os cartões do F0 e do F1, com fase, janela, risco, dependências e status. Para o processo de cada cartão (DoR, DoD e template), veja [README.md](README.md).

**Quem é dono do quê.** No F0, fase, dependência e risco são os da tabela 2.3 de [02 — Escopo e fases](../docs/spec/02-escopo-e-fases.md). Se este índice divergir dela, vale o 02 e o índice é corrigido. Os donos de fronteira entre cartões (rotas compartilhadas, evento SSE `alert`, `G0.md`, provisionamento no Traccar) também estão em 02 §2.3. No F1, vale o cabeçalho de cada cartão. A janela da quinzena vem de [02 §4.2](../docs/spec/02-escopo-e-fases.md).

## Regra para cartão resumido

**Cartão resumido não é implementado antes de cumprir o DoR.** Os cartões T-020 a T-031 têm escopo, requisitos e dependências fixados, mas ainda não têm especificação detalhada, testes congelados nem "Decisões já tomadas". Até o início da quinzena indicada, cada um passa pelo [DoR](README.md) e perde a seção "Para completar o DoR". Antes disso, nenhum agente abre branch nem PR de implementação a partir dele. O `tasks:lint` da [T-019](T-019-guardas-de-processo-no-ci.md) trata esses cartões como rascunho.

## Tabela de cartões

| ID | Título | Fase | Semana / quinzena | Risco | Depende de | Status |
|---|---|---|---|---|---|---|
| [T-001](T-001-fundacao-monorepo-e-isolamento.md) | Fundação: monorepo, Postgres local e isolamento em 3 níveis | F0 | S1 (07–13/10) | N0 | — | Pronto (DoR) |
| [T-002](T-002-spike-j16-bancada.md) | Spike J16 em bancada: capturas, `capability_profile` draft | F0 | S1 (07–13/10) | N1 | Hardware na bancada | Pronto (DoR) |
| [T-003](T-003-vm-primaria-compose-firewall-dns.md) | VM primária, Docker Compose, firewall e DNS | F0 | S1 (07–13/10) | N1 | DEC-12 | Pronto (DoR) |
| [T-004](T-004-contratos-e-esqueleto-api-worker.md) | Contratos iniciais (Zod → OpenAPI 3.1 → clientes TS e Dart) e esqueleto de `api` e `worker` | F0 | S1 (07–13/10) | N1 | T-001 | Pronto (DoR) |
| [T-005](T-005-ingestao-traccar-inbox-projecao.md) | Ingestão Traccar → `ingest_inbox` → `position`/`device_state`/`outbox` | F0 | S2 (14–20/10) | N1; trechos N0 | T-001, T-002, T-004 | Pronto (DoR) |
| [T-006](T-006-autenticacao-e-contexto-rls.md) | Autenticação (Better Auth) e contexto RLS por requisição | F0 | S2 (14–20/10) | N0 | T-001, T-004 | Pronto (DoR) |
| [T-007](T-007-console-login-e-cadastro.md) | Console: login e cadastro de cliente, veículo, rastreador e vínculo | F0 | S2 (14–20/10) | N2 na UI; N1 no módulo `fleet` da API | T-004, T-005, T-006 | Pronto (DoR) |
| [T-008](T-008-console-mapa-ao-vivo-e-historico.md) | Console: mapa ao vivo (SSE) e histórico por veículo/dia | F0 | S2 (14–20/10) | N2 na UI; N0 no servidor | T-005, T-006, T-007 | Pronto (DoR) |
| [T-009](T-009-app-login-lista-mapa-ao-vivo-marca.md) | App: login, lista, mapa ao vivo com estados honestos e marca básica da operadora | F0 | S2 (14–20/10) | N2 | T-004, T-006, T-008 | Pronto (DoR) |
| [T-010](T-010-app-historico-e-deep-links.md) | App: histórico do dia e deep links (WhatsApp da central e navegação) | F0 | S3 (21–27/10) | N2 | T-008, T-009 | Pronto (DoR) |
| [T-011](T-011-motor-de-alertas-f0.md) | Motor de alertas do F0 | F0 | S3 (21–27/10) | N1 | T-002, T-005, T-006 | Pronto (DoR) |
| [T-012](T-012-push-fcm-tokens-e-entregas.md) | Push FCM: tokens, `alert_delivery`, recebimento no app | F0 | S3 (21–27/10) | N1; trechos N0 | T-011, T-009 | Pronto (DoR) |
| [T-013](T-013-deploy-backup-restore-sondas.md) | Deploy, backup WAL-G, restore testado e sondas | F0 | S3 (21–27/10) | N1 | T-003 | Pronto (DoR) |
| [T-014](T-014-migracao-manual-sms-e-rollback.md) | Migração manual por SMS e rollback | F0 | S3–S4 (22/10 a 29/10, 12:00 BRT) | N1 | T-005, DEC-02, DEC-04 | Pronto (DoR) |
| [T-015](T-015-consultas-g0-e-relatorio-de-evidencias.md) | Consultas do G0 e relatório de evidências | F0 | S4 (28–31/10) | N2 | T-005, T-012 | Pronto (DoR) |
| [T-016](T-016-dominio-de-comandos.md) | Domínio de comandos puro: avaliador, máquina de estados e textos | F1 | 01–15/11 | N0 | T-002, T-004 | Pronto (DoR) |
| [T-017](T-017-migration-f1-comandos.md) | Migration do F1 de comandos, chave do aparelho, consentimento e segredos da operadora | F1 | 01–15/11 | N0 | T-005, T-006, T-016 | Pronto (DoR) |
| [T-018](T-018-api-de-comandos-e-step-up.md) | API de comandos com step-up, chave do aparelho e termo de ciência | F1 | 01–15/11 | N0 | T-004, T-006, T-016, T-017 | Pronto (DoR) |
| [T-019](T-019-guardas-de-processo-no-ci.md) | Guardas de processo no CI | F0 | S1–S2 (07–20/10) | N0 | T-001 | Pronto (DoR) |
| [T-020](T-020-despachante-de-comandos-no-worker.md) | Despachante de comandos no worker | F1 | 01–15/11 | N0 | T-005, T-016, T-017, T-018; DEC-01 (só SMS automático) | Resumido — DoR pendente |
| [T-021](T-021-ux-de-comando-app-e-console.md) | UX de comando no app e no console | F1 | 01–15/11 | N0 | T-007, T-009, T-018 | Resumido — DoR pendente |
| [T-022](T-022-homologacao-j16-e-g-cmd.md) | Homologação do perfil J16 em bancada e checklist do G-CMD (tarefa mista) | F1 | 16–30/11 | N0 | T-002, T-020, T-021; DEC-07 | Resumido — DoR pendente |
| [T-023](T-023-cobranca-asaas-split-pix.md) | Cobrança Asaas: vínculo, webhooks, inadimplência, PIX no app e split | F1 | 01–15/11 | N0 | T-006, T-007, T-017; DEC-06, DEC-14 | Resumido — DoR pendente |
| [T-024](T-024-importador-e-ondas-de-migracao.md) | Importador de planilha e ondas de migração por SMS | F1 | 01–30/11 | N0 | T-007, T-014, T-022 (só veículos com bloqueio); DEC-01, DEC-10 | Resumido — DoR pendente |
| [T-025](T-025-ocorrencia-busca-e-compartilhamento.md) | Modo ocorrência, visão da equipe de busca e compartilhamento temporário | F1 | 16–30/11 | N0 | T-008, T-009, T-017, T-020 | Resumido — DoR pendente |
| [T-026](T-026-guincho-parceiro-e-indicacoes.md) | Guincho parceiro: botão no app, indicação, consentimento e relatório mensal | F1 | 16–30/11 | N0 | T-009, T-017, T-023; DEC-05 | Resumido — DoR pendente |
| [T-027](T-027-auditoria-suporte-legal-hold-e-retencao.md) | Auditoria, acesso de suporte, legal hold e retenção quente/frio | F1 | 01–15/12 (retenção quente/frio até 31/01/2027) | N0 | T-005, T-006, T-012; DEC-15 | Resumido — DoR pendente |
| [T-028](T-028-standby-failover-slo-e-agente-sre.md) | Standby, failover com fencing, SLO, status page e agente SRE de diagnóstico | F1 | 01–15/11 (SLO medido desde 01/12) | N0 | T-003, T-005, T-013, T-015; DEC-12, DEC-13 | Resumido — DoR pendente |
| [T-029](T-029-console-f1-carteira-atendimento-e-alertas.md) | Console do F1: carteira completa, atendimento, marca, cercas e alertas novos | F1 | 01–30/11 | N1 | T-007, T-008, T-011 | Resumido — DoR pendente |
| [T-030](T-030-lojas-qualidade-e-versao-minima.md) | Publicação nas lojas, versão mínima do app, E2E e carga | F1 | 16–30/11 | N1 | T-009, T-010, T-012; DEC-03, DEC-04 | Resumido — DoR pendente |
| [T-031](T-031-unidade-economica-e-custos.md) | Relatório de unidade econômica e conta de armazenamento | F1 | 01–15/12 | N1 | T-023, T-027 | Resumido — DoR pendente |

Os riscos "N1; trechos N0" e "N0 no servidor" seguem as regras de 02 §2.3: os trechos N0 (migration, `catalog-allowlist.json`, CAT-07, funções `SECURITY DEFINER` e o servidor de tempo real da T-008) exigem revisão adversarial de outro fornecedor e leitura humana linha a linha.

## Caminho crítico do F0

Copiado de [02 §2.3](../docs/spec/02-escopo-e-fases.md):

**Caminho crítico:** T-002 → T-005 → T-011 → T-012 → T-014 → 48 h → G0. Atraso em qualquer elo aciona o plano de corte ([02 §2.4](../docs/spec/02-escopo-e-fases.md)).

## Ordem sugerida de execução no F0

Segue o cronograma de [02 §2.2](../docs/spec/02-escopo-e-fases.md) e as dependências da tabela acima. Na mesma linha, as tarefas podem correr em paralelo, cada uma na sua branch.

| Semana | Ordem | Marco de fim |
|---|---|---|
| **S1** 07–13/10 | 1. T-001 (primeira tarefa do repositório). Em paralelo, desde o 1º dia: T-002 (bancada do fundador) e T-003 (depois da DEC-12, 10/10). 2. Depois da T-001: T-004 e a sessão 1 da T-019. | 13/10: resultado do spike registrado; posição do J16 de bancada visível no Traccar da VM |
| **S2** 14–20/10 | 1. T-005 e T-006 em paralelo (as duas dependem da T-004; a T-005 também da T-002). 2. T-007 (precisa das tabelas da T-005 e da sessão da T-006). 3. T-008 (usa o esqueleto do console da T-007; plano B: esqueleto mínimo) e T-009 em paralelo (plano B da T-009: fixtures até a T-008 entregar estado e SSE). 4. T-019 sessões 2 e 3, até 20/10. | 20/10: primeira fatia vertical demonstrada (REQ-NEG-014) |
| **S3** 21–27/10 | 1. T-011 (caminho crítico) e, em paralelo, T-010 e T-013. 2. T-014 começa: 1º veículo e rollback em 22/10. 3. T-012 depois da T-011 (caminho crítico). | 27/10: alerta provocado chega ao celular; restore registrado |
| **S4** 28–31/10 | 1. T-014 em execução: 5 a 10 veículos transmitindo até 29/10, 12:00 BRT (prazo duro da janela de 48 h). 2. T-015 (consultas e relatório). 3. Avaliação do G0 em 31/10, depois das 12:00 BRT. | 31/10: G0 |

## Ordem de referência no F1

Os cartões do F1 só entram em execução depois do DoR (regra acima). A ordem abaixo é referência. Quem manda nas entregas por quinzena é [02 §4.2](../docs/spec/02-escopo-e-fases.md).

| Quinzena | Ordem |
|---|---|
| 01–15/11 | Cadeia de comandos: T-016 → T-017 → T-018 → T-020, com a T-021 depois da T-018. Em paralelo: T-023, T-028 (a sonda, a latência de alerta e o minuto ruim precisam estar ativos até 01/12) e o início da T-024 e da T-029. |
| 16–30/11 | T-022 (G-CMD; libera o bloqueio na Lider e as ondas com veículos que têm bloqueio), T-024 (ondas), T-025, T-026, T-029 e T-030. |
| 01–15/12 | T-027 (auditoria, legal hold e retenção) e T-031. |
| até 31/01/2027 | T-027: retenção quente/frio operando (1º Parquet mensal exportado). |

## Manutenção

Quem cria, divide ou renumera um cartão atualiza este índice no mesmo PR. O `docs-check` da T-019 confere os links.
