# 16 — Rastreabilidade

> **Resumo:** matriz gerada automaticamente a partir dos capítulos 01–15 e dos cartões em `tasks/`. Liga cada requisito à fase, prioridade, risco, invariantes, testes de aceite (CT) e tarefas que o implementam. Não edite à mão: rode o gerador.
> **Fases:** F0–F3  ·  **Status:** Aprovado para execução
> **Muda em relação à v1.1:** matriz por requisito (não por faixa), com tarefa responsável e verificação automática de IDs.

## Como usar na revisão de PR

1. Ache o REQ que o PR implementa e confira se o CT correspondente está nos testes do PR.
2. Confira as invariantes listadas: o revisor tenta quebrar cada uma.
3. Requisito sem tarefa no F0/F1 é lacuna: abra um cartão antes de implementar.

## Totais

| Fase | Requisitos |
|---|---|
| F0 | 155 |
| F1 | 127 |
| F2 | 8 |
| F3 | 1 |
| **Total** | **292** |

## Matriz requisito → teste → tarefa

| REQ | Título | Capítulo | Fase | Prior. | Risco | Invariantes | CT | Tarefas |
|---|---|---|---|---|---|---|---|---|
| REQ-NEG-001 | Preço configurável por operadora | [01](01-visao-e-negocio.md) | F1 | P1 | N0 | INV-12 | CT-NEG-001, CT-NEG-002 | T-023 |
| REQ-NEG-002 | Veículo ativo para faturamento | [01](01-visao-e-negocio.md) | F1 | P0 | N0 | INV-06, INV-09, INV-12 | CT-NEG-003 | T-023 |
| REQ-NEG-003 | Custo de infraestrutura por veículo | [01](01-visao-e-negocio.md) | F1 | P1 | N2 | INV-12 | CT-NEG-004, CT-NEG-005 | T-031 |
| REQ-NEG-004 | Relatório mensal de unidade econômica | [01](01-visao-e-negocio.md) | F1 | P1 | N1 | INV-07, INV-12 | CT-NEG-006 | T-031 |
| REQ-NEG-005 | Tempo de onboarding de operadora | [01](01-visao-e-negocio.md) | F2 | P1 | N1 | — | CT-NEG-007, CT-NEG-008 | — |
| REQ-NEG-010 | Gate G0 | [02](02-escopo-e-fases.md) | F0 | P0 | N0 | INV-01, INV-05, INV-07 | CT-NEG-010, CT-NEG-011 | T-013, T-014, T-015 |
| REQ-NEG-011 | Gate G-CMD trava o bloqueio real | [02](02-escopo-e-fases.md) | F1 | P0 | N0 | INV-08, INV-10, INV-11 | CT-NEG-012, CT-NEG-013 | T-022 |
| REQ-NEG-012 | Gate G1 | [02](02-escopo-e-fases.md) | F1 | P0 | N0 | INV-10 | CT-NEG-014, CT-NEG-015 | T-028 |
| REQ-NEG-013 | Gate G2 | [02](02-escopo-e-fases.md) | F2 | P1 | N1 | — | CT-NEG-016 | — |
| REQ-NEG-014 | Primeira fatia vertical | [02](02-escopo-e-fases.md) | F0 | P0 | N0 | INV-01, INV-02, INV-04, INV-05, INV-07 | CT-NEG-017 | T-005, T-008 |
| REQ-NEG-015 | Veículo com bloqueio só migra em onda após o G-CMD | [02](02-escopo-e-fases.md) | F1 | P0 | N0 | INV-03, INV-10 | CT-NEG-018 | T-022 |
| REQ-NEG-016 | Registro de evidências dos gates | [02](02-escopo-e-fases.md) | F0 | P1 | N2 | — | CT-NEG-019 | T-015 |
| REQ-NEG-017 | Plano de corte do F0 | [02](02-escopo-e-fases.md) | F0 | P1 | N2 | — | CT-NEG-020 | T-015 |
| REQ-ARQ-001 | Dois processos do mesmo artefato | [03](03-arquitetura.md) | F0 | P0 | N1 | — | CT-ARQ-001 | T-004 |
| REQ-ARQ-002 | Rotas internas fora da borda pública | [03](03-arquitetura.md) | F0 | P0 | N0 | INV-07 | CT-ARQ-002 | T-004 |
| REQ-ARQ-003 | Superfície pública mínima | [03](03-arquitetura.md) | F0 | P0 | N0 | — | CT-ARQ-003 | T-003 |
| REQ-ARQ-004 | Banco sem porta pública e papéis mínimos | [03](03-arquitetura.md) | F0 | P0 | N0 | INV-07 | CT-ARQ-004 | T-003 |
| REQ-ARQ-005 | Health e readiness por processo | [03](03-arquitetura.md) | F0 | P0 | N1 | — | CT-ARQ-005 | T-004 |
| REQ-ARQ-006 | Configuração por ambiente validada no boot | [03](03-arquitetura.md) | F0 | P0 | N1 | — | CT-ARQ-006 | T-004 |
| REQ-ARQ-007 | Monorepo canônico com dependências verificadas | [03](03-arquitetura.md) | F0 | P0 | N1 | — | CT-ARQ-007 | T-004 |
| REQ-ARQ-008 | `api` sem I/O externo na requisição | [03](03-arquitetura.md) | F0 | P1 | N1 | — | CT-ARQ-008 | T-006 |
| REQ-ARQ-009 | Outbox transacional e relay com varredura | [03](03-arquitetura.md) | F0 | P0 | N1 | INV-01, INV-05 | CT-ARQ-009 | — |
| REQ-ARQ-010 | Job com ids e releitura sob RLS | [03](03-arquitetura.md) | F0 | P0 | N0 | INV-07 | CT-ARQ-010 | T-006 |
| REQ-ARQ-011 | SSE com filtro de escopo | [03](03-arquitetura.md) | F0 | P0 | N1 | INV-04, INV-07 | CT-ARQ-011 | — |
| REQ-ARQ-012 | Limites de recurso e carga de pior caso | [03](03-arquitetura.md) | F0 | P1 | N1 | — | CT-ARQ-012 | — |
| REQ-ARQ-013 | Identidade da instância de origem | [03](03-arquitetura.md) | F0 | P1 | N1 | INV-01 | CT-ARQ-013 | — |
| REQ-ARQ-014 | Logs estruturados e correlação | [03](03-arquitetura.md) | F0 | P1 | N1 | — | CT-ARQ-014 | T-004, T-013 |
| REQ-ARQ-015 | Gatilhos de evolução medidos | [03](03-arquitetura.md) | F1 | P1 | N1 | — | CT-ARQ-015 | T-028 |
| REQ-ARQ-016 | Promoção ou restore sem reenvio físico | [03](03-arquitetura.md) | F1 | P0 | N0 | INV-05, INV-08 | CT-ARQ-016 | T-020 |
| REQ-DAD-001 | Colunas de escopo obrigatórias e imutáveis | [04](04-dominio-e-dados.md) | F0 | P0 | N0 | INV-06, INV-07 | CT-DAD-001 | T-005, T-006, T-017 |
| REQ-DAD-002 | Contexto RLS por transação, fechado por padrão | [04](04-dominio-e-dados.md) | F0 | P0 | N0 | INV-07 | CT-DAD-002 | T-001 |
| REQ-DAD-003 | Políticas por tipo de tabela | [04](04-dominio-e-dados.md) | F0 | P0 | N0 | INV-07 | CT-DAD-003 | T-001, T-006, T-017 |
| REQ-DAD-004 | Papéis de banco e privilégios mínimos | [04](04-dominio-e-dados.md) | F0 | P0 | N0 | INV-07, INV-11 | CT-DAD-004 | T-001, T-005 |
| REQ-DAD-005 | Verificador de catálogo no CI | [04](04-dominio-e-dados.md) | F0 | P0 | N0 | INV-07 | CT-DAD-005 | T-001, T-005 |
| REQ-DAD-006 | Funções `SECURITY DEFINER` em lista fechada | [04](04-dominio-e-dados.md) | F0 | P0 | N0 | INV-07 | CT-DAD-006 | T-005, T-006, T-012 |
| REQ-DAD-007 | Vínculo temporal sem sobreposição | [04](04-dominio-e-dados.md) | F0 | P0 | N1 | INV-06, INV-10 | CT-DAD-007 | T-005, T-007 |
| REQ-DAD-008 | Posição compacta, particionada e append-only | [04](04-dominio-e-dados.md) | F0 | P0 | N1 | INV-03, INV-06, INV-12 | CT-DAD-008 | T-005 |
| REQ-DAD-009 | Partições diárias antecipadas, sem default | [04](04-dominio-e-dados.md) | F0 | P0 | N1 | INV-02 | CT-DAD-009 | T-005 |
| REQ-DAD-010 | Compactação de parado | [04](04-dominio-e-dados.md) | F0 | P1 | N1 | INV-02, INV-03 | CT-DAD-010 | T-005 |
| REQ-DAD-011 | `device_state` com revisão monotônica e reset no vínculo | [04](04-dominio-e-dados.md) | F0 | P0 | N1 | INV-02, INV-03, INV-04, INV-06 | CT-DAD-011 | T-005, T-007 |
| REQ-DAD-012 | Índices por consulta prevista | [04](04-dominio-e-dados.md) | F0 | P1 | N1 | — | CT-DAD-012 | — |
| REQ-DAD-013 | Retenção da inbox, outbox e filas | [04](04-dominio-e-dados.md) | F0 | P1 | N1 | INV-01 | CT-DAD-013 | — |
| REQ-DAD-014 | Exportação quente → frio verificada | [04](04-dominio-e-dados.md) | F1 | P0 | N1 | INV-07 | CT-DAD-014 | T-027 |
| REQ-DAD-015 | Legal hold sobre a retenção | [04](04-dominio-e-dados.md) | F1 | P0 | N1 | INV-06 | CT-DAD-015 | T-027 |
| REQ-DAD-016 | Consulta fria sob demanda | [04](04-dominio-e-dados.md) | F1 | P1 | N1 | INV-07 | CT-DAD-016 | T-027 |
| REQ-DAD-017 | Retenção do banco do Traccar | [04](04-dominio-e-dados.md) | F0 | P1 | N1 | — | CT-DAD-017 | T-003 |
| REQ-DAD-018 | Transferência sem mover histórico | [04](04-dominio-e-dados.md) | F0 | P0 | N1 | INV-06, INV-07 | CT-DAD-018 | — |
| REQ-DAD-019 | Encerramento, tombstone e anonimização | [04](04-dominio-e-dados.md) | F1 | P1 | N1 | INV-06, INV-09 | CT-DAD-019 | T-027 |
| REQ-DAD-020 | Migrations expand/contract | [04](04-dominio-e-dados.md) | F0 | P0 | N0 | INV-07 | CT-DAD-020 | — |
| REQ-DAD-021 | Linter de migrations | [04](04-dominio-e-dados.md) | F1 | P1 | N1 | — | CT-DAD-021 | — |
| REQ-DAD-022 | Unicidade de IMEI e ICCID sem revelar a outra operadora | [04](04-dominio-e-dados.md) | F0 | P1 | N1 | INV-07 | CT-DAD-022 | T-007 |
| REQ-DAD-023 | Acesso de suporte da plataforma | [04](04-dominio-e-dados.md) | F1 | P0 | N0 | INV-07, INV-11 | CT-DAD-023 | T-027 |
| REQ-DAD-024 | Conta de armazenamento medida | [04](04-dominio-e-dados.md) | F1 | P1 | N1 | — | CT-DAD-024 | T-031 |
| REQ-ING-001 | Forward do Traccar configurado e versionado | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-01, INV-03 | CT-ING-001 | T-003 |
| REQ-ING-002 | Autenticação da origem | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N0 | INV-07 | CT-ING-002 | T-005 |
| REQ-ING-003 | Limite de tamanho e prazo | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-01 | CT-ING-003 | T-005 |
| REQ-ING-004 | Envelope ilegível × semântica inválida | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-01 | CT-ING-004 | T-005 |
| REQ-ING-005 | Identidade de origem e dedupe | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-01 | CT-ING-005 | T-005 |
| REQ-ING-006 | Unidades canônicas | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-03, INV-12 | CT-ING-006 | T-005 |
| REQ-ING-007 | Desconhecido não vira zero | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-03 | CT-ING-007 | T-005 |
| REQ-ING-008 | Dono resolvido no servidor pelo vínculo no tempo | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N0 | INV-06, INV-07 | CT-ING-008 | T-005 |
| REQ-ING-009 | Janela de tempo e WNRO | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-02, INV-06 | CT-ING-009 | T-005 |
| REQ-ING-010 | Projeção síncrona com savepoint | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-01, INV-05 | CT-ING-010, CT-ING-022 | T-005 |
| REQ-ING-011 | Ordenação, revisão e atualidade | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-02, INV-04 | CT-ING-011 | T-005 |
| REQ-ING-012 | Heartbeat e fix inválido | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-02, INV-03 | CT-ING-012 | T-005 |
| REQ-ING-013 | Compactação de parado | [05](05-ingestao-e-telemetria.md) | F0 | P1 | N1 | INV-02 | CT-ING-013 | T-005 |
| REQ-ING-014 | Eventos de outbox da ingestão | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-01, INV-04 | CT-ING-014 | T-005 |
| REQ-ING-015 | Reprocessamento e quarentena sem efeito externo | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-05 | CT-ING-015 | T-005 |
| REQ-ING-016 | Reconciliação e backfill | [05](05-ingestao-e-telemetria.md) | F0 | P1 | N1 | INV-01, INV-05 | CT-ING-016 | — |
| REQ-ING-017 | Perfil de normalização | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-03 | CT-ING-017 | T-005 |
| REQ-ING-018 | Retenção da inbox | [05](05-ingestao-e-telemetria.md) | F0 | P1 | N1 | INV-01 | CT-ING-018 | — |
| REQ-ING-019 | Spike do J16 registrado como fixture | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-03, INV-12 | CT-ING-019 | T-002 |
| REQ-ING-020 | Propriedades INV-01 a INV-04 | [05](05-ingestao-e-telemetria.md) | F0 | P0 | N1 | INV-01, INV-02, INV-03, INV-04 | CT-ING-020 | T-005 |
| REQ-ING-021 | Métricas e alarmes de ingestão | [05](05-ingestao-e-telemetria.md) | F0 | P1 | N1 | — | CT-ING-021 | — |
| REQ-CMD-001 | Disponibilidade do bloqueio | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-03, INV-10 | CT-CMD-001 | T-018 |
| REQ-CMD-002 | Avaliação por `cut_point` | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-03, INV-08 | CT-CMD-002 | T-016 |
| REQ-CMD-003 | Evidência inválida nunca autoriza | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-03, INV-05, INV-08 | CT-CMD-003 | T-016 |
| REQ-CMD-004 | `command_policy` versionada | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-08 | CT-CMD-004 | T-017, T-018 |
| REQ-CMD-005 | Trava no dispositivo e posição sob demanda | [06](06-comandos-e-bloqueio.md) | F1 | P1 | N0 | INV-08 | CT-CMD-005 | T-016 |
| REQ-CMD-006 | ARMED com TTL, visível e cancelável | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-08 | CT-CMD-006 | T-018 |
| REQ-CMD-007 | Autorização por papel | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-07, INV-11 | CT-CMD-007 | T-018 |
| REQ-CMD-008 | Step-up e idempotência | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-01 | CT-CMD-008 | T-018 |
| REQ-CMD-009 | Máquina de estados garantida no banco | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-08 | CT-CMD-009 | T-016, T-017 |
| REQ-CMD-010 | Um comando de relé ativo por rastreador | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-08 | CT-CMD-010 | T-017, T-018 |
| REQ-CMD-011 | Tentativa gravada antes do I/O, despacho sem fila | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-05, INV-08 | CT-CMD-011 | T-020 |
| REQ-CMD-012 | Confirmação só por evidência homologada | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-03, INV-08 | CT-CMD-012 | T-016 |
| REQ-CMD-013 | UNKNOWN sem repetição; evidência tardia anexada | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-05, INV-08 | CT-CMD-013 | T-020 |
| REQ-CMD-014 | Reconciliação após reinício do worker | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-08 | CT-CMD-014 | T-020 |
| REQ-CMD-015 | Desbloqueio assimétrico | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-08 | CT-CMD-015 | T-016 |
| REQ-CMD-016 | Contingência registrada | [06](06-comandos-e-bloqueio.md) | F1 | P1 | N0 | INV-08 | CT-CMD-016 | T-018 |
| REQ-CMD-017 | Comercial e IA sem poder físico | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-09, INV-11 | CT-CMD-017 | T-018 |
| REQ-CMD-018 | Homologação de perfil em bancada | [06](06-comandos-e-bloqueio.md) | F0 (bancada), F1 | P0 | N0 | INV-10 | CT-CMD-018 | T-016 |
| REQ-CMD-019 | Termo de ciência | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-10 | CT-CMD-019 | T-018 |
| REQ-CMD-020 | Auditoria | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-06 | CT-CMD-020 | T-017 |
| REQ-CMD-021 | UX mínima obrigatória | [06](06-comandos-e-bloqueio.md) | F1 | P0 | N0 | INV-03 | CT-CMD-021 | T-016 |
| REQ-CMD-022 | Ocorrência e comandos | [06](06-comandos-e-bloqueio.md) | F1 | P1 | N0 | INV-08 | CT-CMD-022 | T-017 |
| REQ-ALR-001 | Catálogo e disponibilidade por hardware | [07](07-alertas-e-tempo-real.md) | F0 | P0 | N1 | INV-03 | CT-ALR-001 | T-011, T-012 |
| REQ-ALR-002 | Ignição ligada | [07](07-alertas-e-tempo-real.md) | F0 | P0 | N1 | INV-03 | CT-ALR-002 | T-011, T-012 |
| REQ-ALR-003 | Ativação e desativação do modo vigilância | [07](07-alertas-e-tempo-real.md) | F0 | P1 | N1 | INV-03, INV-07 | CT-ALR-003 | T-011 |
| REQ-ALR-004 | Violação do modo vigilância | [07](07-alertas-e-tempo-real.md) | F0 | P1 | N1 | INV-03, INV-05 | CT-ALR-004 | T-011 |
| REQ-ALR-005 | Corte de alimentação | [07](07-alertas-e-tempo-real.md) | F0 | P0 | N1 | INV-03 | CT-ALR-005 | T-011, T-012 |
| REQ-ALR-006 | SOS | [07](07-alertas-e-tempo-real.md) | F0 | P0 | N1 | INV-01 | CT-ALR-006 | T-011, T-012 |
| REQ-ALR-007 | Sem comunicação e incidente de plataforma | [07](07-alertas-e-tempo-real.md) | F0 | P0 | N1 | INV-03 | CT-ALR-007 | T-011, T-012 |
| REQ-ALR-008 | Comunicação perdida em movimento | [07](07-alertas-e-tempo-real.md) | F0 | P1 | N1 | INV-03 | CT-ALR-008 | T-011 |
| REQ-ALR-009 | Episódios idempotentes | [07](07-alertas-e-tempo-real.md) | F0 | P0 | N1 | INV-01, INV-05 | CT-ALR-009 | T-011, T-012 |
| REQ-ALR-010 | Fato antigo, modo não ao vivo e restore | [07](07-alertas-e-tempo-real.md) | F0 | P0 | N1 | INV-05 | CT-ALR-010 | T-011, T-012 |
| REQ-ALR-011 | Push FCM com prioridade alta | [07](07-alertas-e-tempo-real.md) | F0 | P0 | N1 | INV-07 | CT-ALR-011 | T-012 |
| REQ-ALR-012 | Retentativa e token inválido | [07](07-alertas-e-tempo-real.md) | F0 | P0 | N1 | INV-01 | CT-ALR-012 | T-012 |
| REQ-ALR-013 | Preferências por usuário | [07](07-alertas-e-tempo-real.md) | F0 | P1 | N1 | INV-07 | CT-ALR-013 | T-012 |
| REQ-ALR-014 | Fila de alertas e reconhecimento | [07](07-alertas-e-tempo-real.md) | F0 | P1 | N1 | INV-07 | CT-ALR-014 | T-011 |
| REQ-ALR-015 | Latência medida por etapa | [07](07-alertas-e-tempo-real.md) | F0 | P0 | N1 | — | CT-ALR-015 | T-011, T-012, T-015 |
| REQ-ALR-016 | SSE: autenticação e escopo | [07](07-alertas-e-tempo-real.md) | F0 | P0 | N0 | INV-07 | CT-ALR-016 | T-008 |
| REQ-ALR-017 | SSE: limites de veículos e conexões | [07](07-alertas-e-tempo-real.md) | F0 | P1 | N1 | INV-07 | CT-ALR-017 | T-008 |
| REQ-ALR-018 | SSE: revisão, snapshot e heartbeat | [07](07-alertas-e-tempo-real.md) | F0 | P0 | N1 | INV-04 | CT-ALR-018 | T-008 |
| REQ-ALR-019 | SSE: revogação de sessão | [07](07-alertas-e-tempo-real.md) | F0 | P1 | N0 | INV-07 | CT-ALR-019 | T-008 |
| REQ-ALR-020 | Bateria baixa | [07](07-alertas-e-tempo-real.md) | F1 | P1 | N1 | INV-03 | CT-ALR-020 | T-029 |
| REQ-ALR-021 | Excesso de velocidade | [07](07-alertas-e-tempo-real.md) | F1 | P1 | N1 | INV-03 | CT-ALR-021 | T-029 |
| REQ-ALR-022 | Cerca virtual | [07](07-alertas-e-tempo-real.md) | F1 | P1 | N1 | INV-06, INV-07 | CT-ALR-022 | T-029 |
| REQ-ALR-023 | Crítico sem reconhecimento | [07](07-alertas-e-tempo-real.md) | F1 | P2 | N2 | — | CT-ALR-023 | T-029 |
| REQ-SEG-001 | Autenticação embutida sem cadastro público | [08](08-identidade-e-seguranca.md) | F0 | P0 | N0 | INV-07 | CT-SEG-001 | T-006 |
| REQ-SEG-002 | Política de senha e redefinição | [08](08-identidade-e-seguranca.md) | F0 | P1 | N0 | — | CT-SEG-002 | T-006 |
| REQ-SEG-003 | Sessão do app por bearer, 30 dias deslizante | [08](08-identidade-e-seguranca.md) | F0 | P0 | N0 | — | CT-SEG-003 | T-006, T-009 |
| REQ-SEG-004 | Sessão do console por cookie, 12 h absoluta | [08](08-identidade-e-seguranca.md) | F0 | P0 | N0 | — | CT-SEG-004 | T-006 |
| REQ-SEG-005 | CSRF nas mutações do console | [08](08-identidade-e-seguranca.md) | F0 | P0 | N0 | — | CT-SEG-005 | T-006 |
| REQ-SEG-006 | TOTP obrigatório para administradores | [08](08-identidade-e-seguranca.md) | F0 | P1 | N0 | — | CT-SEG-006 | T-006 |
| REQ-SEG-007 | Revogação efetiva em até 60 s | [08](08-identidade-e-seguranca.md) | F0 | P0 | N0 | INV-07 | CT-SEG-007 | T-006 |
| REQ-SEG-008 | Contexto RLS a partir da membership | [08](08-identidade-e-seguranca.md) | F0 | P0 | N0 | INV-07 | CT-SEG-008 | T-006 |
| REQ-SEG-009 | Matriz de permissões aplicada e testada | [08](08-identidade-e-seguranca.md) | F0 | P0 | N0 | INV-07, INV-11 | CT-SEG-009 | T-006, T-007 |
| REQ-SEG-010 | Convite e ciclo de vida da membership | [08](08-identidade-e-seguranca.md) | F0 | P1 | N0 | INV-07 | CT-SEG-010 | T-006 |
| REQ-SEG-011 | Acesso de suporte da plataforma | [08](08-identidade-e-seguranca.md) | F1 | P0 | N0 | INV-07, INV-11 | CT-SEG-011 | T-027 |
| REQ-SEG-012 | Cadastro da chave do aparelho | [08](08-identidade-e-seguranca.md) | F1 | P0 | N0 | INV-08 | CT-SEG-012 | T-018 |
| REQ-SEG-013 | Desafio de comando | [08](08-identidade-e-seguranca.md) | F1 | P0 | N0 | INV-07, INV-08 | CT-SEG-013 | T-018 |
| REQ-SEG-014 | Verificação da assinatura com consumo atômico | [08](08-identidade-e-seguranca.md) | F1 | P0 | N0 | INV-08 | CT-SEG-014 | T-018 |
| REQ-SEG-015 | Step-up do console por TOTP com motivo | [08](08-identidade-e-seguranca.md) | F1 | P0 | N0 | INV-08 | CT-SEG-015 | T-018 |
| REQ-SEG-016 | Revogação da chave do aparelho | [08](08-identidade-e-seguranca.md) | F1 | P0 | N0 | INV-08 | CT-SEG-016 | T-018 |
| REQ-SEG-017 | Link temporário | [08](08-identidade-e-seguranca.md) | F1 | P1 | N0 | INV-07 | CT-SEG-017 | T-025 |
| REQ-SEG-018 | Sessão pública vinculada ao link | [08](08-identidade-e-seguranca.md) | F1 | P1 | N0 | INV-07 | CT-SEG-018 | T-025 |
| REQ-SEG-019 | Segredos versionados com SOPS + age | [08](08-identidade-e-seguranca.md) | F0 | P0 | N0 | — | CT-SEG-019 | T-003 |
| REQ-SEG-020 | Credenciais Asaas cifradas e rotacionáveis | [08](08-identidade-e-seguranca.md) | F1 | P0 | N0 | INV-07, INV-11 | CT-SEG-020 | T-017 |
| REQ-SEG-021 | Nenhum segredo ou dado sensível em log | [08](08-identidade-e-seguranca.md) | F0 | P0 | N1 | — | CT-SEG-021 | T-004 |
| REQ-SEG-022 | Webhook do Asaas autenticado | [08](08-identidade-e-seguranca.md) | F1 | P0 | N0 | INV-07, INV-09 | CT-SEG-022 | T-023 |
| REQ-SEG-023 | Limites de taxa e bloqueio progressivo | [08](08-identidade-e-seguranca.md) | F0 | P0 | N0 | — | CT-SEG-023 | T-006 |
| REQ-SEG-024 | Porta TCP limitada e salto impossível | [08](08-identidade-e-seguranca.md) | F0 | P1 | N1 | INV-08 | CT-SEG-024 | T-003 |
| REQ-SEG-025 | CORS por allowlist e headers de segurança | [08](08-identidade-e-seguranca.md) | F0 | P0 | N1 | — | CT-SEG-025 | T-004 |
| REQ-SEG-026 | Registros de acesso e auditoria | [08](08-identidade-e-seguranca.md) | F0 | P1 | N1 | INV-07 | CT-SEG-026 | T-006, T-007 |
| REQ-SEG-027 | Legal hold e pacote de evidências | [08](08-identidade-e-seguranca.md) | F1 | P0 | N1 | INV-06, INV-07 | CT-SEG-027 | T-027 |
| REQ-SEG-028 | Agentes de IA no escopo de quem pergunta | [08](08-identidade-e-seguranca.md) | F1 | P0 | N0 | INV-07, INV-11 | CT-SEG-028 | T-028 |
| REQ-SEG-029 | Consentimento por finalidade e direitos do titular | [08](08-identidade-e-seguranca.md) | F1 | P1 | N1 | INV-07 | CT-SEG-029 | T-018 |
| REQ-API-001 | Contrato único e registro de rotas | [09](09-api-e-contratos.md) | F0 | P0 | N1 | INV-12 | CT-API-001 | T-004 |
| REQ-API-002 | OpenAPI e clientes gerados e versionados | [09](09-api-e-contratos.md) | F0 | P0 | N1 | — | CT-API-002 | T-004 |
| REQ-API-003 | Mudança incompatível barrada | [09](09-api-e-contratos.md) | F0 | P0 | N1 | — | CT-API-003 | T-004 |
| REQ-API-004 | Validação de entrada e de saída | [09](09-api-e-contratos.md) | F0 | P0 | N1 | INV-03, INV-12 | CT-API-004 | T-004, T-007 |
| REQ-API-005 | Convenções de formato verificadas | [09](09-api-e-contratos.md) | F0 | P1 | N1 | INV-12 | CT-API-005 | T-004 |
| REQ-API-006 | Paginação por cursor | [09](09-api-e-contratos.md) | F0 | P1 | N1 | INV-07 | CT-API-006 | T-007, T-008 |
| REQ-API-007 | Problem Details com `code` estável | [09](09-api-e-contratos.md) | F0 | P0 | N1 | — | CT-API-007 | T-004 |
| REQ-API-008 | 404 para recurso fora do escopo | [09](09-api-e-contratos.md) | F0 | P0 | N0 | INV-07 | CT-API-008 | T-006, T-007, T-008 |
| REQ-API-009 | Idempotency-Key | [09](09-api-e-contratos.md) | F0 | P0 | N0 | INV-08 | CT-API-009 | T-006 |
| REQ-API-010 | ETag e If-Match | [09](09-api-e-contratos.md) | F0 | P1 | N1 | — | CT-API-010 | T-007 |
| REQ-API-011 | Lista de veículos com estados honestos | [09](09-api-e-contratos.md) | F0 | P0 | N1 | INV-03, INV-04, INV-07 | CT-API-011 | T-008 |
| REQ-API-012 | Histórico síncrono limitado | [09](09-api-e-contratos.md) | F0 | P0 | N1 | INV-02, INV-03, INV-06, INV-07 | CT-API-012 | T-008 |
| REQ-API-013 | Exportação assíncrona de histórico | [09](09-api-e-contratos.md) | F1 | P1 | N1 | INV-07 | CT-API-013 | T-025 |
| REQ-API-014 | Criação de comando com resposta 202 | [09](09-api-e-contratos.md) | F1 | P0 | N0 | INV-08, INV-09, INV-10 | CT-API-014 | T-018 |
| REQ-API-015 | Contratos internos validados pelas capturas reais | [09](09-api-e-contratos.md) | F0 | P0 | N1 | INV-01 | CT-API-015 | — |
| REQ-API-016 | Versão mínima do app | [09](09-api-e-contratos.md) | F1 | P1 | N1 | — | CT-API-016 | T-030 |
| REQ-API-017 | Depreciação com prazo | [09](09-api-e-contratos.md) | F1 | P2 | N1 | — | CT-API-017 | T-030 |
| REQ-API-018 | Teste de autenticação e isolamento por rota | [09](09-api-e-contratos.md) | F0 | P0 | N0 | INV-07 | CT-API-018 | T-006, T-007, T-008 |
| REQ-API-019 | Limites de corpo e de tempo | [09](09-api-e-contratos.md) | F0 | P1 | N1 | — | CT-API-019 | T-004 |
| REQ-UX-001 | Tokens únicos e gerados | [10](10-apps-e-ux.md) | F0 | P1 | N2 | — | CT-UX-001 | T-007, T-009 |
| REQ-UX-002 | Tela neutra e marca após o login | [10](10-apps-e-ux.md) | F0 | P1 | N2 | INV-07 | CT-UX-002 | T-009 |
| REQ-UX-003 | Contraste mínimo com ajuste automático | [10](10-apps-e-ux.md) | F0 | P1 | N2 | — | CT-UX-003 | T-009 |
| REQ-UX-004 | Estado de apresentação honesto | [10](10-apps-e-ux.md) | F0 | P0 | N2 | INV-03, INV-04 | CT-UX-004 | T-008, T-009 |
| REQ-UX-005 | Idade da última posição válida | [10](10-apps-e-ux.md) | F0 | P0 | N2 | INV-03 | CT-UX-005 | T-008, T-009 |
| REQ-UX-006 | Início com mapa ao vivo | [10](10-apps-e-ux.md) | F0 | P0 | N2 | INV-04, INV-07 | CT-UX-006 | T-009 |
| REQ-UX-007 | Detalhe do veículo | [10](10-apps-e-ux.md) | F0 | P0 | N2 | INV-03 | CT-UX-007 | T-009 |
| REQ-UX-008 | Histórico do dia | [10](10-apps-e-ux.md) | F0 | P0 | N2 | INV-03, INV-06 | CT-UX-008 | T-008, T-010 |
| REQ-UX-009 | Alerta a partir do push em até 2 toques | [10](10-apps-e-ux.md) | F0 | P0 | N2 | INV-07 | CT-UX-009 | — |
| REQ-UX-010 | Modo vigilância no app | [10](10-apps-e-ux.md) | F0 | P1 | N2 | INV-03 | CT-UX-010 | — |
| REQ-UX-011 | Falar com a central e navegar até o veículo | [10](10-apps-e-ux.md) | F0 | P0 | N2 | — | CT-UX-011 | T-010 |
| REQ-UX-012 | Notificações | [10](10-apps-e-ux.md) | F0 | P0 | N2 | — | CT-UX-012 | — |
| REQ-UX-013 | Desempenho do app | [10](10-apps-e-ux.md) | F0 | P1 | N2 | — | CT-UX-013 | T-009 |
| REQ-UX-014 | Estabilidade | [10](10-apps-e-ux.md) | F1 | P1 | N2 | — | CT-UX-014 | T-030 |
| REQ-UX-015 | Acessibilidade | [10](10-apps-e-ux.md) | F0 | P1 | N2 | — | CT-UX-015 | T-009 |
| REQ-UX-016 | Offline somente leitura | [10](10-apps-e-ux.md) | F0 | P0 | N2 | INV-03, INV-08 | CT-UX-016 | T-009 |
| REQ-UX-017 | Disponibilidade e confirmação do comando | [10](10-apps-e-ux.md) | F1 | P0 | N0 | INV-08, INV-10 | CT-UX-017 | T-021 |
| REQ-UX-018 | Estados do comando com textos distintos | [10](10-apps-e-ux.md) | F1 | P0 | N0 | INV-03, INV-08 | CT-UX-018 | T-021 |
| REQ-UX-019 | Nunca enfileirar comando offline | [10](10-apps-e-ux.md) | F1 | P0 | N0 | INV-08 | CT-UX-019 | T-021 |
| REQ-UX-020 | Ocorrência no app | [10](10-apps-e-ux.md) | F1 | P1 | N1 | INV-08 | CT-UX-020 | T-025 |
| REQ-UX-021 | Faturas e PIX | [10](10-apps-e-ux.md) | F1 | P1 | N1 | INV-09, INV-12 | CT-UX-021 | T-023 |
| REQ-UX-022 | Chamar guincho | [10](10-apps-e-ux.md) | F1 | P1 | N1 | INV-07 | CT-UX-022 | T-026 |
| REQ-UX-023 | Compartilhar localização | [10](10-apps-e-ux.md) | F1 | P1 | N1 | INV-07 | CT-UX-023 | T-025 |
| REQ-UX-024 | Cercas no app | [10](10-apps-e-ux.md) | F1 | P2 | N2 | INV-07 | CT-UX-024 | T-029 |
| REQ-UX-025 | Console: cadastro e vínculo com ponto de corte | [10](10-apps-e-ux.md) | F0 | P0 | N1 | INV-07, INV-10 | CT-UX-025 | T-007 |
| REQ-UX-026 | Console: mapa da operadora e histórico | [10](10-apps-e-ux.md) | F0 | P0 | N2 | INV-04, INV-07 | CT-UX-026 | T-008 |
| REQ-UX-027 | Console F1: telas operacionais e papéis | [10](10-apps-e-ux.md) | F1 | P1 | N2 | INV-07 | CT-UX-027 | T-029 |
| REQ-UX-028 | Atendimento | [10](10-apps-e-ux.md) | F1 | P1 | N1 | INV-07 | CT-UX-028 | T-029 |
| REQ-UX-029 | Visão da equipe de busca | [10](10-apps-e-ux.md) | F1 | P1 | N1 | INV-07, INV-08 | CT-UX-029 | T-025 |
| REQ-UX-030 | Distribuição F0/F1 | [10](10-apps-e-ux.md) | F0 | P0 | N2 | — | CT-UX-030 | T-010 |
| REQ-UX-031 | Portal web e opção B | [10](10-apps-e-ux.md) | F2 | P2 | N2 | INV-07 | CT-UX-031 | — |
| REQ-ONB-001 | Checklist de onboarding com dono e prazo | [11](11-onboarding-e-migracao.md) | F2 | P1 | N2 | — | CT-ONB-001 | — |
| REQ-ONB-002 | Upload: formatos e limites | [11](11-onboarding-e-migracao.md) | F1 | P0 | N1 | — | CT-ONB-002 | T-024 |
| REQ-ONB-003 | Mapeamento de colunas | [11](11-onboarding-e-migracao.md) | F1 | P1 | N1 | — | CT-ONB-003 | T-024 |
| REQ-ONB-004 | Validação e normalização por linha | [11](11-onboarding-e-migracao.md) | F1 | P0 | N1 | INV-03, INV-10, INV-12 | CT-ONB-004 | T-024 |
| REQ-ONB-005 | Prévia e relatório de erros | [11](11-onboarding-e-migracao.md) | F1 | P0 | N1 | — | CT-ONB-005 | T-024 |
| REQ-ONB-006 | Commit idempotente por linha | [11](11-onboarding-e-migracao.md) | F1 | P0 | N1 | INV-06, INV-07 | CT-ONB-006 | T-024 |
| REQ-ONB-007 | Isolamento do importador | [11](11-onboarding-e-migracao.md) | F1 | P0 | N0 | INV-07 | CT-ONB-007 | T-024 |
| REQ-ONB-008 | Migração manual do piloto | [11](11-onboarding-e-migracao.md) | F0 | P0 | N1 | INV-06 | CT-ONB-008 | T-014 |
| REQ-ONB-009 | Rollback testado antes do piloto | [11](11-onboarding-e-migracao.md) | F0 | P0 | N1 | — | CT-ONB-009 | T-014 |
| REQ-ONB-010 | Criação de onda e pré-checagem | [11](11-onboarding-e-migracao.md) | F1 | P0 | N1 | INV-07 | CT-ONB-010 | T-024 |
| REQ-ONB-011 | Envio de SMS e segredo da senha | [11](11-onboarding-e-migracao.md) | F1 | P0 | N0 | INV-05 | CT-ONB-011 | T-024 |
| REQ-ONB-012 | 1º contato em 10 min e rollback automático | [11](11-onboarding-e-migracao.md) | F1 | P0 | N1 | INV-05 | CT-ONB-012 | T-024 |
| REQ-ONB-013 | Disjuntor da onda | [11](11-onboarding-e-migracao.md) | F1 | P1 | N1 | — | CT-ONB-013 | T-024 |
| REQ-ONB-014 | Liberação por operadora e janela | [11](11-onboarding-e-migracao.md) | F1 | P0 | N1 | — | CT-ONB-014 | T-024 |
| REQ-ONB-015 | Modelos de SMS versionados por perfil | [11](11-onboarding-e-migracao.md) | F0 | P0 | N1 | — | CT-ONB-015 | T-014 |
| REQ-ONB-016 | Domínio e plano B | [11](11-onboarding-e-migracao.md) | F0 | P0 | N1 | — | CT-ONB-016 | T-014 |
| REQ-ONB-017 | Métricas de migração | [11](11-onboarding-e-migracao.md) | F1 | P1 | N2 | — | CT-ONB-017 | T-024 |
| REQ-ONB-018 | Avisos aos clientes | [11](11-onboarding-e-migracao.md) | F1 | P1 | N2 | — | CT-ONB-018 | T-024 |
| REQ-ONB-019 | Rastreador comunicando sem vínculo | [11](11-onboarding-e-migracao.md) | F0 | P1 | N0 | INV-07 | CT-ONB-019 | — |
| REQ-ONB-020 | Histórico anterior à migração | [11](11-onboarding-e-migracao.md) | F1 | P1 | N2 | INV-06 | CT-ONB-020 | T-024 |
| REQ-COB-001 | Asaas da operadora como fonte da cobrança | [12](12-cobranca-e-svas.md) | F1 | P0 | N0 | INV-12 | CT-COB-001 | T-023 |
| REQ-COB-002 | Vínculo da conta verificado | [12](12-cobranca-e-svas.md) | F1 | P0 | N0 | INV-07, INV-11 | CT-COB-002 | T-023 |
| REQ-COB-003 | Webhook autenticado e idempotente | [12](12-cobranca-e-svas.md) | F1 | P0 | N0 | INV-01, INV-09 | CT-COB-003 | T-023 |
| REQ-COB-004 | Mapeamento de status sem regressão | [12](12-cobranca-e-svas.md) | F1 | P0 | N0 | INV-03, INV-12 | CT-COB-004 | T-023 |
| REQ-COB-005 | Vínculo de clientes por documento | [12](12-cobranca-e-svas.md) | F1 | P1 | N1 | INV-07 | CT-COB-005 | T-023 |
| REQ-COB-006 | Reconciliação diária | [12](12-cobranca-e-svas.md) | F1 | P0 | N0 | INV-05 | CT-COB-006 | T-023 |
| REQ-COB-007 | Inadimplência sem efeito físico | [12](12-cobranca-e-svas.md) | F1 | P0 | N0 | INV-09 | CT-COB-007 | T-023 |
| REQ-COB-008 | Aviso de pagamento sem degradar a segurança | [12](12-cobranca-e-svas.md) | F1 | P1 | N1 | INV-09 | CT-COB-008 | T-023 |
| REQ-COB-009 | PIX no app com dados do Asaas | [12](12-cobranca-e-svas.md) | F1 | P1 | N1 | INV-07, INV-12 | CT-COB-009 | T-023 |
| REQ-COB-010 | Split de R$ 3,90 por veículo em cobrança de rastreamento | [12](12-cobranca-e-svas.md) | F1 | P0 | N0 | INV-11, INV-12 | CT-COB-010 | T-023 |
| REQ-COB-011 | Fechamento mensal da tarifa | [12](12-cobranca-e-svas.md) | F1 | P0 | N0 | INV-06, INV-12 | CT-COB-011 | T-023 |
| REQ-COB-012 | Crédito, estorno e split tardio entre períodos | [12](12-cobranca-e-svas.md) | F1 | P1 | N0 | INV-11, INV-12 | CT-COB-012 | T-023 |
| REQ-COB-013 | Dinheiro em centavos na fronteira do Asaas | [12](12-cobranca-e-svas.md) | F1 | P0 | N0 | INV-12 | CT-COB-013 | T-023 |
| REQ-COB-014 | Lembretes de fatura por push | [12](12-cobranca-e-svas.md) | F1 | P2 | N1 | INV-05 | CT-COB-014 | T-023 |
| REQ-COB-015 | NFS-e opcional por operadora | [12](12-cobranca-e-svas.md) | F1 | P2 | N1 | — | CT-COB-015 | T-023 |
| REQ-COB-016 | Isolamento e fronteiras da cobrança | [12](12-cobranca-e-svas.md) | F1 | P0 | N0 | INV-07, INV-09, INV-11 | CT-COB-016 | T-023 |
| REQ-SVA-001 | Parceiros por escopo e habilitação | [12](12-cobranca-e-svas.md) | F1 | P1 | N1 | INV-07 | CT-SVA-001 | T-026 |
| REQ-SVA-002 | Botão do parceiro nunca bloqueia o contato | [12](12-cobranca-e-svas.md) | F1 | P1 | N1 | INV-07 | CT-SVA-002 | T-026 |
| REQ-SVA-003 | Consentimento por parceiro e finalidade | [12](12-cobranca-e-svas.md) | F1 | P0 | N1 | INV-07 | CT-SVA-003 | T-026 |
| REQ-SVA-004 | Transparência da indicação remunerada | [12](12-cobranca-e-svas.md) | F1 | P1 | N2 | — | CT-SVA-004 | T-026 |
| REQ-SVA-005 | Estados e conversão da indicação | [12](12-cobranca-e-svas.md) | F1 | P1 | N1 | INV-11 | CT-SVA-005 | T-026 |
| REQ-SVA-006 | Antifraude de indicações | [12](12-cobranca-e-svas.md) | F1 | P1 | N1 | — | CT-SVA-006 | T-026 |
| REQ-SVA-007 | Repartição com snapshot | [12](12-cobranca-e-svas.md) | F1 | P1 | N0 | INV-11, INV-12 | CT-SVA-007 | T-026 |
| REQ-SVA-008 | Relatório mensal e repasse | [12](12-cobranca-e-svas.md) | F1 | P1 | N0 | INV-07, INV-12 | CT-SVA-008 | T-026 |
| REQ-SVA-009 | Indicação só por ação humana | [12](12-cobranca-e-svas.md) | F1 | P0 | N1 | INV-05, INV-11 | CT-SVA-009 | T-026 |
| REQ-SVA-010 | Assistência 24h com parceiro integrado | [12](12-cobranca-e-svas.md) | F2 | P1 | N1 | INV-05, INV-07 | CT-SVA-010 | — |
| REQ-SVA-011 | Revisões por km e tempo com odômetro GPS calibrado | [12](12-cobranca-e-svas.md) | F2 | P1 | N1 | INV-01, INV-03, INV-05 | CT-SVA-011 | — |
| REQ-SVA-012 | Gestão de custos PF com km real | [12](12-cobranca-e-svas.md) | F2 | P2 | N2 | INV-03, INV-12 | CT-SVA-012 | — |
| REQ-SVA-013 | Alerta de possível impacto | [12](12-cobranca-e-svas.md) | F3 | P1 | N1 | INV-03 | CT-SVA-013 | — |
| REQ-OPS-001 | Provisionamento reproduzível | [13](13-infra-e-operacao.md) | F0 | P0 | N1 | — | CT-OPS-001 | T-003 |
| REQ-OPS-002 | Firewall em duas camadas e SSH só pela Tailscale | [13](13-infra-e-operacao.md) | F0 | P0 | N1 | — | CT-OPS-002 | T-003 |
| REQ-OPS-003 | Compose de produção com limites e autoheal | [13](13-infra-e-operacao.md) | F0 | P0 | N1 | — | CT-OPS-003 | T-003 |
| REQ-OPS-004 | Postgres de produção sem dado sensível no log | [13](13-infra-e-operacao.md) | F0 | P0 | N1 | INV-07 | CT-OPS-004 | T-003 |
| REQ-OPS-005 | Imagem do banco multi-arquitetura com WAL-G | [13](13-infra-e-operacao.md) | F0 | P0 | N1 | — | CT-OPS-005 | T-003 |
| REQ-OPS-006 | Deploy por tag com rollback automático | [13](13-infra-e-operacao.md) | F0 | P0 | N1 | — | CT-OPS-006 | T-013 |
| REQ-OPS-007 | Migrations expand/contract no deploy | [13](13-infra-e-operacao.md) | F0 | P0 | N0 | INV-07 | CT-OPS-007 | T-013 |
| REQ-OPS-008 | Backup contínuo cifrado com cópia fora da Oracle | [13](13-infra-e-operacao.md) | F0 | P0 | N1 | — | CT-OPS-008 | T-013 |
| REQ-OPS-009 | Restore ensaiado sem efeito externo | [13](13-infra-e-operacao.md) | F0 | P0 | N1 | INV-05 | CT-OPS-009 | T-013 |
| REQ-OPS-010 | Standby por streaming com WAL limitado | [13](13-infra-e-operacao.md) | F1 | P0 | N0 | — | CT-OPS-010 | T-028 |
| REQ-OPS-011 | Failover com fencing antes da promoção | [13](13-infra-e-operacao.md) | F1 | P0 | N0 | INV-05, INV-08 | CT-OPS-011 | T-028 |
| REQ-OPS-012 | Ex-primária não sobe como primária | [13](13-infra-e-operacao.md) | F1 | P0 | N0 | — | CT-OPS-012 | T-028 |
| REQ-OPS-013 | SLO por minuto ruim | [13](13-infra-e-operacao.md) | F1 | P0 | N1 | INV-03 | CT-OPS-013 | T-028 |
| REQ-OPS-014 | Manutenção anunciada e créditos | [13](13-infra-e-operacao.md) | F1 | P1 | N1 | INV-12 | CT-OPS-014 | T-028 |
| REQ-OPS-015 | Status page pública | [13](13-infra-e-operacao.md) | F1 | P0 | N2 | — | CT-OPS-015 | T-028 |
| REQ-OPS-016 | Observabilidade sem dado pessoal | [13](13-infra-e-operacao.md) | F0 | P1 | N1 | — | CT-OPS-016 | T-013 |
| REQ-OPS-017 | Regras de alerta e paging | [13](13-infra-e-operacao.md) | F0 | P0 | N1 | — | CT-OPS-017 | T-013 |
| REQ-OPS-018 | Gateway de incidentes independente das VMs | [13](13-infra-e-operacao.md) | F1 | P1 | N1 | — | CT-OPS-018 | T-028 |
| REQ-OPS-019 | Agente SRE do F1: diagnóstico somente leitura | [13](13-infra-e-operacao.md) | F1 | P1 | N1 | INV-07, INV-11 | CT-OPS-019 | T-028 |
| REQ-OPS-020 | Cardápio fechado do F2 por forced-command | [13](13-infra-e-operacao.md) | F2 | P1 | N0 | INV-08, INV-11 | CT-OPS-020 | — |
| REQ-OPS-021 | Auditoria de operação mesmo com o banco fora | [13](13-infra-e-operacao.md) | F1 | P0 | N1 | — | CT-OPS-021 | T-028 |
| REQ-OPS-022 | Severidade, comunicação e postmortem | [13](13-infra-e-operacao.md) | F1 | P1 | N2 | — | CT-OPS-022 | T-028 |
| REQ-OPS-023 | Dados no Brasil e transferências registradas | [13](13-infra-e-operacao.md) | F0 | P0 | N1 | — | CT-OPS-023 | T-003 |
| REQ-OPS-024 | Runbook do plantonista e ensaio de contingência | [13](13-infra-e-operacao.md) | F1 | P0 | N2 | INV-08, INV-09 | CT-OPS-024 | T-028 |
| REQ-QLD-001 | `AGENTS.md` como regra única e links verificados | [14](14-qualidade-e-processo-ia.md) | F0 | P0 | N0 | — | CT-QLD-001 | — |
| REQ-QLD-002 | Cartão no template canônico com DoR verificável | [14](14-qualidade-e-processo-ia.md) | F0 | P0 | N2 | — | CT-QLD-002 | — |
| REQ-QLD-003 | Nível de risco calculado pelo caminho | [14](14-qualidade-e-processo-ia.md) | F0 | P0 | N0 | INV-07, INV-08 | CT-QLD-003 | — |
| REQ-QLD-004 | Testes do cartão copiados sem alteração | [14](14-qualidade-e-processo-ia.md) | F0 | P1 | N0 | — | CT-QLD-004 | — |
| REQ-QLD-005 | Testes existentes protegidos | [14](14-qualidade-e-processo-ia.md) | F0 | P0 | N0 | INV-07 | CT-QLD-005 | T-001 |
| REQ-QLD-006 | Rótulos de exceção só pelo fundador | [14](14-qualidade-e-processo-ia.md) | F1 | P1 | N0 | — | CT-QLD-006 | — |
| REQ-QLD-007 | Revisão adversarial por outro fornecedor registrada | [14](14-qualidade-e-processo-ia.md) | F0 | P0 | N0 | INV-07, INV-08, INV-11 | CT-QLD-007 | — |
| REQ-QLD-008 | Merge só pelo fundador, com `main` protegida | [14](14-qualidade-e-processo-ia.md) | F0 | P0 | N0 | — | CT-QLD-008 | — |
| REQ-QLD-009 | Propriedades para INV-01 a INV-05 | [14](14-qualidade-e-processo-ia.md) | F0 | P0 | N1 | INV-01, INV-02, INV-03, INV-04, INV-05 | CT-QLD-009 | — |
| REQ-QLD-010 | Propriedades e mutação na política de comando | [14](14-qualidade-e-processo-ia.md) | F1 | P0 | N0 | INV-08, INV-10 | CT-QLD-010 | T-016 |
| REQ-QLD-011 | Isolamento repetido em toda tabela nova, com Postgres real | [14](14-qualidade-e-processo-ia.md) | F0 | P0 | N0 | INV-07 | CT-QLD-011 | T-017 |
| REQ-QLD-012 | E2E do console e do app | [14](14-qualidade-e-processo-ia.md) | F1 | P1 | N2 | INV-04, INV-07 | CT-QLD-012 | T-030 |
| REQ-QLD-013 | Carga sustentada e rajada | [14](14-qualidade-e-processo-ia.md) | F1 | P1 | N1 | INV-01 | CT-QLD-013 | T-030 |
| REQ-QLD-014 | Bancada a cada mudança do caminho físico | [14](14-qualidade-e-processo-ia.md) | F1 | P0 | N0 | INV-08, INV-10 | CT-QLD-014 | T-022 |
| REQ-QLD-015 | Conventional Commits e template de PR | [14](14-qualidade-e-processo-ia.md) | F0 | P1 | N2 | — | CT-QLD-015 | — |
| REQ-QLD-016 | Agentes sem segredo, dado pessoal real ou credencial de produção | [14](14-qualidade-e-processo-ia.md) | F0 | P0 | N0 | INV-07, INV-11 | CT-QLD-016 | — |
| REQ-QLD-017 | Avaliação dos agentes de IA antes de ligar e a cada troca | [14](14-qualidade-e-processo-ia.md) | F1 | P0 | N0 | INV-07, INV-11 | CT-QLD-017 | T-028 |
| REQ-QLD-018 | Primeira tarefa sem perguntas; pergunta vira resposta registrada | [14](14-qualidade-e-processo-ia.md) | F0 | P0 | N2 | — | CT-QLD-018 | — |
| REQ-QLD-019 | Métricas do processo e tempo de CI | [14](14-qualidade-e-processo-ia.md) | F1 | P1 | N2 | — | CT-QLD-019 | T-031 |
| REQ-QLD-020 | Registro de decisões atualizado na resolução | [15](15-decisoes-riscos-premissas.md) | F0 | P1 | N2 | — | CT-QLD-020 | — |
| REQ-QLD-021 | Gatilhos de risco verificados toda semana | [15](15-decisoes-riscos-premissas.md) | F0 | P1 | N2 | — | CT-QLD-021 | — |

## Invariante → requisitos

| Invariante | Requisitos que a protegem |
|---|---|
| INV-01 | REQ-NEG-010, REQ-NEG-014, REQ-ARQ-009, REQ-ARQ-013, REQ-DAD-013, REQ-ING-001, REQ-ING-003, REQ-ING-004, REQ-ING-005, REQ-ING-010, REQ-ING-014, REQ-ING-016, REQ-ING-018, REQ-ING-020, REQ-CMD-008, REQ-ALR-006, REQ-ALR-009, REQ-ALR-012, REQ-API-015, REQ-COB-003, REQ-SVA-011, REQ-QLD-009, REQ-QLD-013 |
| INV-02 | REQ-NEG-014, REQ-DAD-009, REQ-DAD-010, REQ-DAD-011, REQ-ING-009, REQ-ING-011, REQ-ING-012, REQ-ING-013, REQ-ING-020, REQ-API-012, REQ-QLD-009 |
| INV-03 | REQ-NEG-015, REQ-DAD-008, REQ-DAD-010, REQ-DAD-011, REQ-ING-001, REQ-ING-006, REQ-ING-007, REQ-ING-012, REQ-ING-017, REQ-ING-019, REQ-ING-020, REQ-CMD-001, REQ-CMD-002, REQ-CMD-003, REQ-CMD-012, REQ-CMD-021, REQ-ALR-001, REQ-ALR-002, REQ-ALR-003, REQ-ALR-004, REQ-ALR-005, REQ-ALR-007, REQ-ALR-008, REQ-ALR-020, REQ-ALR-021, REQ-API-004, REQ-API-011, REQ-API-012, REQ-UX-004, REQ-UX-005, REQ-UX-007, REQ-UX-008, REQ-UX-010, REQ-UX-016, REQ-UX-018, REQ-ONB-004, REQ-COB-004, REQ-SVA-011, REQ-SVA-012, REQ-SVA-013, REQ-OPS-013, REQ-QLD-009 |
| INV-04 | REQ-NEG-014, REQ-ARQ-011, REQ-DAD-011, REQ-ING-011, REQ-ING-014, REQ-ING-020, REQ-ALR-018, REQ-API-011, REQ-UX-004, REQ-UX-006, REQ-UX-026, REQ-QLD-009, REQ-QLD-012 |
| INV-05 | REQ-NEG-010, REQ-NEG-014, REQ-ARQ-009, REQ-ARQ-016, REQ-ING-010, REQ-ING-015, REQ-ING-016, REQ-CMD-003, REQ-CMD-011, REQ-CMD-013, REQ-ALR-004, REQ-ALR-009, REQ-ALR-010, REQ-ONB-011, REQ-ONB-012, REQ-COB-006, REQ-COB-014, REQ-SVA-009, REQ-SVA-010, REQ-SVA-011, REQ-OPS-009, REQ-OPS-011, REQ-QLD-009 |
| INV-06 | REQ-NEG-002, REQ-DAD-001, REQ-DAD-007, REQ-DAD-008, REQ-DAD-011, REQ-DAD-015, REQ-DAD-018, REQ-DAD-019, REQ-ING-008, REQ-ING-009, REQ-CMD-020, REQ-ALR-022, REQ-SEG-027, REQ-API-012, REQ-UX-008, REQ-ONB-006, REQ-ONB-008, REQ-ONB-020, REQ-COB-011 |
| INV-07 | REQ-NEG-004, REQ-NEG-010, REQ-NEG-014, REQ-ARQ-002, REQ-ARQ-004, REQ-ARQ-010, REQ-ARQ-011, REQ-DAD-001, REQ-DAD-002, REQ-DAD-003, REQ-DAD-004, REQ-DAD-005, REQ-DAD-006, REQ-DAD-014, REQ-DAD-016, REQ-DAD-018, REQ-DAD-020, REQ-DAD-022, REQ-DAD-023, REQ-ING-002, REQ-ING-008, REQ-CMD-007, REQ-ALR-003, REQ-ALR-011, REQ-ALR-013, REQ-ALR-014, REQ-ALR-016, REQ-ALR-017, REQ-ALR-019, REQ-ALR-022, REQ-SEG-001, REQ-SEG-007, REQ-SEG-008, REQ-SEG-009, REQ-SEG-010, REQ-SEG-011, REQ-SEG-013, REQ-SEG-017, REQ-SEG-018, REQ-SEG-020, REQ-SEG-022, REQ-SEG-026, REQ-SEG-027, REQ-SEG-028, REQ-SEG-029, REQ-API-006, REQ-API-008, REQ-API-011, REQ-API-012, REQ-API-013, REQ-API-018, REQ-UX-002, REQ-UX-006, REQ-UX-009, REQ-UX-022, REQ-UX-023, REQ-UX-024, REQ-UX-025, REQ-UX-026, REQ-UX-027, REQ-UX-028, REQ-UX-029, REQ-UX-031, REQ-ONB-006, REQ-ONB-007, REQ-ONB-010, REQ-ONB-019, REQ-COB-002, REQ-COB-005, REQ-COB-009, REQ-COB-016, REQ-SVA-001, REQ-SVA-002, REQ-SVA-003, REQ-SVA-008, REQ-SVA-010, REQ-OPS-004, REQ-OPS-007, REQ-OPS-019, REQ-QLD-003, REQ-QLD-005, REQ-QLD-007, REQ-QLD-011, REQ-QLD-012, REQ-QLD-016, REQ-QLD-017 |
| INV-08 | REQ-NEG-011, REQ-ARQ-016, REQ-CMD-002, REQ-CMD-003, REQ-CMD-004, REQ-CMD-005, REQ-CMD-006, REQ-CMD-009, REQ-CMD-010, REQ-CMD-011, REQ-CMD-012, REQ-CMD-013, REQ-CMD-014, REQ-CMD-015, REQ-CMD-016, REQ-CMD-022, REQ-SEG-012, REQ-SEG-013, REQ-SEG-014, REQ-SEG-015, REQ-SEG-016, REQ-SEG-024, REQ-API-009, REQ-API-014, REQ-UX-016, REQ-UX-017, REQ-UX-018, REQ-UX-019, REQ-UX-020, REQ-UX-029, REQ-OPS-011, REQ-OPS-020, REQ-OPS-024, REQ-QLD-003, REQ-QLD-007, REQ-QLD-010, REQ-QLD-014 |
| INV-09 | REQ-NEG-002, REQ-DAD-019, REQ-CMD-017, REQ-SEG-022, REQ-API-014, REQ-UX-021, REQ-COB-003, REQ-COB-007, REQ-COB-008, REQ-COB-016, REQ-OPS-024 |
| INV-10 | REQ-NEG-011, REQ-NEG-012, REQ-NEG-015, REQ-DAD-007, REQ-CMD-001, REQ-CMD-018, REQ-CMD-019, REQ-API-014, REQ-UX-017, REQ-UX-025, REQ-ONB-004, REQ-QLD-010, REQ-QLD-014 |
| INV-11 | REQ-NEG-011, REQ-DAD-004, REQ-DAD-023, REQ-CMD-007, REQ-CMD-017, REQ-SEG-009, REQ-SEG-011, REQ-SEG-020, REQ-SEG-028, REQ-COB-002, REQ-COB-010, REQ-COB-012, REQ-COB-016, REQ-SVA-005, REQ-SVA-007, REQ-SVA-009, REQ-OPS-019, REQ-OPS-020, REQ-QLD-007, REQ-QLD-016, REQ-QLD-017 |
| INV-12 | REQ-NEG-001, REQ-NEG-002, REQ-NEG-003, REQ-NEG-004, REQ-DAD-008, REQ-ING-006, REQ-ING-019, REQ-API-001, REQ-API-004, REQ-API-005, REQ-UX-021, REQ-ONB-004, REQ-COB-001, REQ-COB-004, REQ-COB-009, REQ-COB-010, REQ-COB-011, REQ-COB-012, REQ-COB-013, REQ-SVA-007, REQ-SVA-008, REQ-SVA-012, REQ-OPS-014 |

## Tarefa → requisitos

| Tarefa | Fase | Risco | Requisitos |
|---|---|---|---|
| [T-001 — Fundação: monorepo, Postgres local e isolamento em 3 níveis](../../tasks/T-001-fundacao-monorepo-e-isolamento.md) | F0 | N0 | REQ-DAD-002, REQ-DAD-003, REQ-DAD-004, REQ-DAD-005, REQ-QLD-005 |
| [T-002 — Spike J16 em bancada: capturas, `capability_profile` draft](../../tasks/T-002-spike-j16-bancada.md) | F0 | N1 | REQ-ING-019 |
| [T-003 — VM primária, Docker Compose, firewall e DNS](../../tasks/T-003-vm-primaria-compose-firewall-dns.md) | F0 | N1 | REQ-OPS-001, REQ-OPS-002, REQ-OPS-003, REQ-OPS-004, REQ-OPS-005, REQ-OPS-023, REQ-ARQ-003, REQ-ARQ-004, REQ-ING-001, REQ-DAD-017, REQ-SEG-019, REQ-SEG-024 |
| [T-004 — Contratos iniciais (Zod → OpenAPI 3.1 → clientes TS e Dart) e esqueleto de `api` e `worker`](../../tasks/T-004-contratos-e-esqueleto-api-worker.md) | F0 | N1 | REQ-API-001, REQ-API-002, REQ-API-003, REQ-API-004, REQ-API-005, REQ-API-007, REQ-API-019, REQ-ARQ-001, REQ-ARQ-002, REQ-ARQ-005, REQ-ARQ-006, REQ-ARQ-007, REQ-ARQ-014, REQ-SEG-021, REQ-SEG-025 |
| [T-005 — Ingestão Traccar → `ingest_inbox` → `position`/`device_state`/`outbox`](../../tasks/T-005-ingestao-traccar-inbox-projecao.md) | F0 | N1 | REQ-ING-002, REQ-ING-015, REQ-ING-017, REQ-ING-020, REQ-DAD-001, REQ-DAD-004, REQ-DAD-006, REQ-DAD-011, REQ-DAD-005, REQ-NEG-014, REQ-ING-003, REQ-ING-004, REQ-ING-005, REQ-ING-006, REQ-ING-007, REQ-ING-008, REQ-ING-009, REQ-ING-010, REQ-ING-011, REQ-ING-012, REQ-ING-013, REQ-ING-014, REQ-DAD-007, REQ-DAD-008, REQ-DAD-009, REQ-DAD-010 |
| [T-006 — Autenticação (Better Auth) e contexto RLS por requisição](../../tasks/T-006-autenticacao-e-contexto-rls.md) | F0 | N0 | REQ-SEG-001, REQ-SEG-002, REQ-SEG-003, REQ-SEG-004, REQ-SEG-005, REQ-SEG-006, REQ-SEG-007, REQ-SEG-008, REQ-SEG-009, REQ-SEG-010, REQ-SEG-023, REQ-SEG-026, REQ-API-008, REQ-API-009, REQ-API-018, REQ-ARQ-008, REQ-ARQ-010, REQ-DAD-001, REQ-DAD-003, REQ-DAD-006 |
| [T-007 — Console: login e cadastro de cliente, veículo, rastreador e vínculo](../../tasks/T-007-console-login-e-cadastro.md) | F0 | N2 | REQ-UX-025, REQ-UX-001, REQ-API-004, REQ-API-006, REQ-API-008, REQ-API-010, REQ-API-018, REQ-DAD-007, REQ-DAD-011, REQ-DAD-022, REQ-SEG-009, REQ-SEG-026 |
| [T-008 — Console: mapa ao vivo (SSE) e histórico por veículo/dia](../../tasks/T-008-console-mapa-ao-vivo-e-historico.md) | F0 | N2 | REQ-ALR-016, REQ-ALR-017, REQ-ALR-018, REQ-ALR-019, REQ-API-011, REQ-API-012, REQ-API-006, REQ-API-008, REQ-API-018, REQ-NEG-014, REQ-UX-004, REQ-UX-005, REQ-UX-008, REQ-UX-026 |
| [T-009 — App: login, lista, mapa ao vivo com estados honestos e marca básica da operadora](../../tasks/T-009-app-login-lista-mapa-ao-vivo-marca.md) | F0 | N2 | REQ-UX-001, REQ-UX-002, REQ-UX-003, REQ-UX-004, REQ-UX-005, REQ-UX-006, REQ-UX-007, REQ-UX-013, REQ-UX-015, REQ-UX-016, REQ-SEG-003 |
| [T-010 — App: histórico do dia e deep links (WhatsApp da central e navegação)](../../tasks/T-010-app-historico-e-deep-links.md) | F0 | N2 | REQ-UX-008, REQ-UX-011, REQ-UX-030 |
| [T-011 — Motor de alertas do F0](../../tasks/T-011-motor-de-alertas-f0.md) | F0 | N1 | REQ-ALR-001, REQ-ALR-010, REQ-ALR-014, REQ-ALR-015, REQ-ALR-002, REQ-ALR-003, REQ-ALR-004, REQ-ALR-005, REQ-ALR-006, REQ-ALR-007, REQ-ALR-008, REQ-ALR-009 |
| [T-012 — Push FCM: tokens, `alert_delivery`, recebimento no app](../../tasks/T-012-push-fcm-tokens-e-entregas.md) | F0 | N1 | REQ-ALR-011, REQ-ALR-012, REQ-ALR-013, REQ-ALR-002, REQ-ALR-005, REQ-ALR-006, REQ-ALR-007, REQ-ALR-009, REQ-ALR-010, REQ-ALR-001, REQ-ALR-015, REQ-DAD-006 |
| [T-013 — Deploy, backup WAL-G, restore testado e sondas](../../tasks/T-013-deploy-backup-restore-sondas.md) | F0 | N1 | REQ-OPS-006, REQ-OPS-007, REQ-OPS-008, REQ-OPS-009, REQ-OPS-016, REQ-OPS-017, REQ-ARQ-014, REQ-NEG-010 |
| [T-014 — Migração manual por SMS e rollback](../../tasks/T-014-migracao-manual-sms-e-rollback.md) | F0 | N1 | REQ-ONB-008, REQ-ONB-009, REQ-ONB-015, REQ-ONB-016, REQ-NEG-010 |
| [T-015 — Consultas do G0 e relatório de evidências](../../tasks/T-015-consultas-g0-e-relatorio-de-evidencias.md) | F0 | N2 | REQ-NEG-010, REQ-NEG-016, REQ-ALR-015, REQ-NEG-017 |
| [T-016 — Domínio de comandos puro: avaliador, máquina de estados e textos](../../tasks/T-016-dominio-de-comandos.md) | F1 | N0 | REQ-CMD-002, REQ-CMD-003, REQ-CMD-005, REQ-CMD-009, REQ-CMD-012, REQ-CMD-015, REQ-CMD-018, REQ-CMD-021, REQ-QLD-010 |
| [T-017 — Migration do F1 de comandos, chave do aparelho, consentimento e segredos da operadora](../../tasks/T-017-migration-f1-comandos.md) | F1 | N0 | REQ-CMD-004, REQ-CMD-009, REQ-CMD-010, REQ-CMD-020, REQ-CMD-022, REQ-DAD-001, REQ-DAD-003, REQ-SEG-020, REQ-QLD-011 |
| [T-018 — API de comandos com step-up, chave do aparelho e termo de ciência](../../tasks/T-018-api-de-comandos-e-step-up.md) | F1 | N0 | REQ-CMD-001, REQ-CMD-004, REQ-CMD-006, REQ-CMD-007, REQ-CMD-008, REQ-CMD-010, REQ-CMD-016, REQ-CMD-017, REQ-CMD-019, REQ-SEG-012, REQ-SEG-013, REQ-SEG-014, REQ-SEG-015, REQ-SEG-016, REQ-SEG-029, REQ-API-014 |
| [T-020 — Despachante de comandos no worker](../../tasks/T-020-despachante-de-comandos-no-worker.md) | F1 | N0 | REQ-CMD-011, REQ-CMD-013, REQ-CMD-014, REQ-ARQ-016 |
| [T-021 — UX de comando no app e no console](../../tasks/T-021-ux-de-comando-app-e-console.md) | F1 | N0 | REQ-UX-017, REQ-UX-018, REQ-UX-019 |
| [T-022 — Homologação do perfil J16 em bancada e checklist do G-CMD (tarefa mista)](../../tasks/T-022-homologacao-j16-e-g-cmd.md) | F1 | N0 | REQ-NEG-011, REQ-NEG-015, REQ-QLD-014 |
| [T-023 — Cobrança Asaas: vínculo, webhooks, inadimplência, PIX no app e split](../../tasks/T-023-cobranca-asaas-split-pix.md) | F1 | N0 | REQ-COB-001, REQ-COB-016, REQ-SEG-022, REQ-UX-021, REQ-NEG-001, REQ-NEG-002, REQ-COB-002, REQ-COB-003, REQ-COB-004, REQ-COB-005, REQ-COB-006, REQ-COB-007, REQ-COB-008, REQ-COB-009, REQ-COB-010, REQ-COB-011, REQ-COB-012, REQ-COB-013, REQ-COB-014, REQ-COB-015 |
| [T-024 — Importador de planilha e ondas de migração por SMS](../../tasks/T-024-importador-e-ondas-de-migracao.md) | F1 | N0 | REQ-ONB-002, REQ-ONB-007, REQ-ONB-010, REQ-ONB-014, REQ-ONB-017, REQ-ONB-018, REQ-ONB-020, REQ-ONB-003, REQ-ONB-004, REQ-ONB-005, REQ-ONB-006, REQ-ONB-011, REQ-ONB-012, REQ-ONB-013 |
| [T-025 — Modo ocorrência, visão da equipe de busca e compartilhamento temporário](../../tasks/T-025-ocorrencia-busca-e-compartilhamento.md) | F1 | N0 | REQ-UX-020, REQ-UX-023, REQ-UX-029, REQ-SEG-017, REQ-SEG-018, REQ-API-013 |
| [T-026 — Guincho parceiro: botão no app, indicação, consentimento e relatório mensal](../../tasks/T-026-guincho-parceiro-e-indicacoes.md) | F1 | N0 | REQ-SVA-001, REQ-SVA-009, REQ-UX-022, REQ-SVA-002, REQ-SVA-003, REQ-SVA-004, REQ-SVA-005, REQ-SVA-006, REQ-SVA-007, REQ-SVA-008 |
| [T-027 — Auditoria, acesso de suporte, legal hold e retenção quente/frio](../../tasks/T-027-auditoria-suporte-legal-hold-e-retencao.md) | F1 | N0 | REQ-DAD-014, REQ-DAD-015, REQ-DAD-016, REQ-DAD-019, REQ-DAD-023, REQ-SEG-011, REQ-SEG-027 |
| [T-028 — Standby, failover com fencing, SLO, status page e agente SRE de diagnóstico](../../tasks/T-028-standby-failover-slo-e-agente-sre.md) | F1 | N0 | REQ-NEG-012, REQ-OPS-010, REQ-OPS-015, REQ-OPS-018, REQ-OPS-019, REQ-OPS-021, REQ-OPS-022, REQ-OPS-024, REQ-SEG-028, REQ-QLD-017, REQ-ARQ-015, REQ-OPS-011, REQ-OPS-012, REQ-OPS-013, REQ-OPS-014 |
| [T-029 — Console do F1: carteira completa, atendimento, marca, cercas e alertas novos](../../tasks/T-029-console-f1-carteira-atendimento-e-alertas.md) | F1 | N1 | REQ-UX-024, REQ-UX-027, REQ-UX-028, REQ-ALR-020, REQ-ALR-021, REQ-ALR-022, REQ-ALR-023 |
| [T-030 — Publicação nas lojas, versão mínima do app, E2E e carga](../../tasks/T-030-lojas-qualidade-e-versao-minima.md) | F1 | N1 | REQ-UX-014, REQ-API-016, REQ-API-017, REQ-QLD-012, REQ-QLD-013 |
| [T-031 — Relatório de unidade econômica e conta de armazenamento](../../tasks/T-031-unidade-economica-e-custos.md) | F1 | N1 | REQ-NEG-003, REQ-NEG-004, REQ-DAD-024, REQ-QLD-019 |

## Lacunas (F0/F1 sem tarefa)

- REQ-ARQ-009 — Outbox transacional e relay com varredura (F0)
- REQ-ARQ-011 — SSE com filtro de escopo (F0)
- REQ-ARQ-012 — Limites de recurso e carga de pior caso (F0)
- REQ-ARQ-013 — Identidade da instância de origem (F0)
- REQ-DAD-012 — Índices por consulta prevista (F0)
- REQ-DAD-013 — Retenção da inbox, outbox e filas (F0)
- REQ-DAD-018 — Transferência sem mover histórico (F0)
- REQ-DAD-020 — Migrations expand/contract (F0)
- REQ-DAD-021 — Linter de migrations (F1)
- REQ-ING-016 — Reconciliação e backfill (F0)
- REQ-ING-018 — Retenção da inbox (F0)
- REQ-ING-021 — Métricas e alarmes de ingestão (F0)
- REQ-API-015 — Contratos internos validados pelas capturas reais (F0)
- REQ-UX-009 — Alerta a partir do push em até 2 toques (F0)
- REQ-UX-010 — Modo vigilância no app (F0)
- REQ-UX-012 — Notificações (F0)
- REQ-ONB-019 — Rastreador comunicando sem vínculo (F0)
- REQ-QLD-001 — `AGENTS.md` como regra única e links verificados (F0)
- REQ-QLD-002 — Cartão no template canônico com DoR verificável (F0)
- REQ-QLD-003 — Nível de risco calculado pelo caminho (F0)
- REQ-QLD-004 — Testes do cartão copiados sem alteração (F0)
- REQ-QLD-006 — Rótulos de exceção só pelo fundador (F1)
- REQ-QLD-007 — Revisão adversarial por outro fornecedor registrada (F0)
- REQ-QLD-008 — Merge só pelo fundador, com `main` protegida (F0)
- REQ-QLD-009 — Propriedades para INV-01 a INV-05 (F0)
- REQ-QLD-015 — Conventional Commits e template de PR (F0)
- REQ-QLD-016 — Agentes sem segredo, dado pessoal real ou credencial de produção (F0)
- REQ-QLD-018 — Primeira tarefa sem perguntas; pergunta vira resposta registrada (F0)
- REQ-QLD-020 — Registro de decisões atualizado na resolução (F0)
- REQ-QLD-021 — Gatilhos de risco verificados toda semana (F0)

## Como regenerar

```bash
python3 scripts/trace.py .   # a partir da raiz do repositório
```
