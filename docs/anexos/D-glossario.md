# Anexo D — Glossário

> **Resumo:** Termos usados na especificação, em ordem alfabética, com definição curta e o capítulo dono. Quando um termo tem nome técnico no código (tabela, coluna, papel), ele aparece em `código`.
> **Fases:** F0–F3  ·  **Status:** Aprovado para execução
> **Muda em relação à v1.1:** glossário ampliado com os termos de negócio (operadora, SVA, split), de operação (minuto ruim, fencing) e de processo com IA (N0, testes congelados).

| Termo | Definição | Dono |
|---|---|---|
| **ADR** | Registro de decisão de arquitetura aceita, com contexto, alternativas e gatilho de revisão (ADR-001 a ADR-011). | [adr/](../adr/) |
| **Agente de suporte** | Agente de IA que atende as equipes das operadoras dentro de guardrails: só lê, com o escopo de quem pergunta (INV-11). F2. | [13](../spec/13-infra-e-operacao.md) |
| **Agente SRE** | Agente de IA de operação, fora da VM, que diagnostica incidentes (F1, só leitura) e executa ações do cardápio fechado (F2). | [13](../spec/13-infra-e-operacao.md), [ADR-010](../adr/ADR-010-operacao-assistida-por-ia.md) |
| **Always Free** | Cota gratuita permanente da Oracle Cloud usada pela TrackSys: até 4 OCPU Ampere, 24 GB de RAM e 200 GB de disco no total. | [13](../spec/13-infra-e-operacao.md) |
| **APN** | Ponto de acesso da rede móvel do chip. APN privada restringe quem fala com o servidor e mitiga spoofing de IMEI. | [08](../spec/08-identidade-e-seguranca.md) |
| **APNs** | Serviço de push da Apple, usado via FCM. | [07](../spec/07-alertas-e-tempo-real.md) |
| **ARMED** | Estado do comando que aguarda a condição do perfil (ex.: veículo parar) dentro de um prazo de 5 min (30 min em modo ocorrência); visível e cancelável. | [06](../spec/06-comandos-e-bloqueio.md) |
| **Backfill** | Recuperação de fatos de um período a partir da origem (ex.: buffer do rastreador após queda). Não gera efeito externo (INV-05). | [05](../spec/05-ingestao-e-telemetria.md) |
| **Bomba de combustível** | Ponto de corte mais comum no Brasil (~80%). Corta o motor em movimento; permitido até o teto da operadora (40 km/h). `cut_point = 'fuel_pump'`. | [06](../spec/06-comandos-e-bloqueio.md) |
| **CAT** | Regra do verificador de catálogo do banco (CAT-01 a CAT-07): RLS forçada, políticas, colunas de escopo, FK composta, papel da aplicação, tabelas append-only, funções privilegiadas. | [04](../spec/04-dominio-e-dados.md) |
| **Cardápio de ações** | Lista fechada de ações que o agente SRE pode executar (reiniciar serviço, rotacionar logs, reprocessar fila, coletar diagnóstico, promover standby com pré-condições). | [ADR-010](../adr/ADR-010-operacao-assistida-por-ia.md) |
| **Chave do aparelho** | Par de chaves criado no chip seguro do celular (Secure Enclave/Android Keystore), liberado por biometria, que assina a intenção do comando. | [08](../spec/08-identidade-e-seguranca.md) |
| **Chip M2M** | Chip de dados para máquinas. Na Lider: emnify multi-operadora, administrado pela Meta Telecom. Identificado pelo ICCID. | [11](../spec/11-onboarding-e-migracao.md) |
| **Cliente (tenant)** | Cliente final da operadora (pessoa física ou jurídica), dono dos veículos e dos dados de rastreamento. `tenant`. | [04](../spec/04-dominio-e-dados.md) |
| **Compactação de parado** | Regra que só grava posição parada se houver deslocamento > 50 m ou a cada 30 min; os demais sinais só atualizam o "visto por último". | [05](../spec/05-ingestao-e-telemetria.md) |
| **Controlador (LGPD)** | Quem decide sobre o tratamento de dados pessoais. No serviço principal, a operadora. | [Anexo B](B-juridico.md) |
| **CT** | Teste de aceite (Dado / Quando / Então), ligado a um requisito. | [00](../spec/00-indice.md) |
| **`cut_point`** | Ponto onde o relé de bloqueio foi instalado: `fuel_pump`, `ignition` ou `starter`. Sem registro, o bloqueio fica indisponível (INV-10). | [06](../spec/06-comandos-e-bloqueio.md) |
| **DEC** | Decisão pendente com dono, prazo, impacto e plano B (DEC-01 a DEC-15). | [15](../spec/15-decisoes-riscos-premissas.md) |
| **Deep link** | Link que abre outro app já com contexto: WhatsApp da central com placa e posição, Google Maps/Waze até o veículo. Custo zero. | [10](../spec/10-apps-e-ux.md) |
| **Design partner** | Operadora piloto que ajuda a construir o produto em troca de condições especiais (proposta para a Lider: adesão após o G1). | [Anexo A](A-comercial.md) |
| **DoD / DoR** | Definition of Done / Definition of Ready: critérios para encerrar e para iniciar um cartão de tarefa. | [tasks/](../../tasks/README.md) |
| **DPA** | Acordo de tratamento de dados entre a operadora (controladora) e a Versix (operadora de dados), com a lista de suboperadores. | [Anexo B](B-juridico.md) |
| **DuckDB** | Motor de consulta analítica usado para ler o histórico frio em Parquet sob demanda. | [ADR-009](../adr/ADR-009-retencao-quente-frio.md) |
| **Encarregado** | Pessoa responsável pelo canal com titulares e com a ANPD (LGPD). Na Versix, o fundador. | [Anexo B](B-juridico.md) |
| **Equipe de busca** | Equipe da operadora que vai a campo recuperar veículo furtado. Usa a visão de ocorrência no celular. `search_team`. | [10](../spec/10-apps-e-ux.md) |
| **F0, F1, F2, F3** | Fases: Piloto Zero (até 31/10/2026), Lançamento Lider (nov–dez/2026), Escala de operadoras (jan–jun/2027), Frotas e inteligência (a partir de out/2027). | [02](../spec/02-escopo-e-fases.md) |
| **Failover** | Troca da VM primária pela standby quando a primária cai. RTO ≤ 30 min a partir do F1. | [13](../spec/13-infra-e-operacao.md) |
| **FCM** | Firebase Cloud Messaging, serviço gratuito de push para Android e iOS. | [07](../spec/07-alertas-e-tempo-real.md) |
| **Fencing** | Isolar a primária (parar a VM pela API da OCI) antes de promover a standby, para nunca haver dois primários. | [13](../spec/13-infra-e-operacao.md) |
| **FK composta** | Chave estrangeira que inclui `operator_id` e `tenant_id`, tornando impossível ligar dados de clientes ou operadoras diferentes. | [04](../spec/04-dominio-e-dados.md) |
| **G0, G-CMD, G1, G2** | Gates: saída do F0, liberação do bloqueio real, saída do F1, saída do F2. Cada item tem critério, medida e evidência. | [02](../spec/02-escopo-e-fases.md) |
| **Heartbeat** | Sinal periódico do rastreador sem mudança relevante (ex.: parado a cada 300 s). | [05](../spec/05-ingestao-e-telemetria.md) |
| **ICCID** | Número de série do chip. Fica em `sim_card.iccid`. | [04](../spec/04-dominio-e-dados.md) |
| **IMEI** | Identificador do rastreador. Atributo de inventário, nunca chave de autorização. `device.imei`. | [04](../spec/04-dominio-e-dados.md) |
| **Inbox** | Tabela `ingest_inbox`: guarda cada mensagem recebida do Traccar antes do 202, com a chave de identidade de origem (INV-01). | [05](../spec/05-ingestao-e-telemetria.md) |
| **Indicação** | Encaminhamento do cliente a um parceiro (guincho, oficina, assistência) registrado para atribuição e repasse. `referral`. | [12](../spec/12-cobranca-e-svas.md) |
| **INV** | Invariante: propriedade que nenhum código, operação ou agente pode violar (INV-01 a INV-12). | [00](../spec/00-indice.md#invariantes) |
| **ISO** | Teste de comportamento do isolamento no banco (ISO-01 a ISO-09). | [04](../spec/04-dominio-e-dados.md) |
| **J16** | Modelo de rastreador mais usado pela Lider. Protocolo compatível com GT06 a confirmar no spike (DEC-02). | [05](../spec/05-ingestao-e-telemetria.md) |
| **Legal hold** | Congelamento do expurgo de um veículo/período enquanto houver requisição de autoridade ou disputa. `legal_hold`. | [04](../spec/04-dominio-e-dados.md) |
| **Marca dinâmica** | O app único TrackSys assume nome, logo, cores e contato da operadora após o login. | [10](../spec/10-apps-e-ux.md), [ADR-007](../adr/ADR-007-app-unico-flutter-marca-dinamica.md) |
| **Marco Civil** | Lei 12.965/2014. Pelo art. 15, o provedor de aplicação guarda IP, porta de origem e data/hora de acesso por 6 meses. | [08](../spec/08-identidade-e-seguranca.md) |
| **Minuto ruim** | Minuto em que a sonda externa falhou ou em que o p95 da latência de alerta passou de 120 s. A meta de 99,5% admite ≤ 216 min ruins em 30 dias. | [13](../spec/13-infra-e-operacao.md) |
| **Modo ocorrência** | Fluxo de furto/roubo: intervalo de transmissão reduzido, visão da equipe de busca, compartilhamento com a polícia, BO e pacote de evidências. F1. | [06](../spec/06-comandos-e-bloqueio.md), [10](../spec/10-apps-e-ux.md) |
| **Modo vigilância** | Cerca âncora ativada pelo cliente ao estacionar: ignição ligada ou deslocamento > 150 m dispara alerta crítico. | [07](../spec/07-alertas-e-tempo-real.md) |
| **Motor de arranque** | Ponto de corte que só impede a próxima partida (~5% das instalações). `cut_point = 'starter'`. | [06](../spec/06-comandos-e-bloqueio.md) |
| **N0, N1, N2** | Níveis de risco de revisão: N0 (comandos, isolamento, cobrança, autenticação, failover), N1 (domínio e integrações), N2 (UI e documentação). | [14](../spec/14-qualidade-e-processo-ia.md) |
| **Operador (LGPD)** | Quem trata dados em nome do controlador. No serviço principal, a Versix. | [Anexo B](B-juridico.md) |
| **Operadora** | Empresa de rastreamento cliente da Versix (ex.: Lider Rastreamento). Raiz do isolamento. `operator`. | [01](../spec/01-visao-e-negocio.md) |
| **Opção C** | Estratégia de distribuição: app único TrackSys com marca dinâmica agora; app dedicado por operadora depois, como opcional pago. | [ADR-007](../adr/ADR-007-app-unico-flutter-marca-dinamica.md) |
| **Outbox** | Tabela `outbox` gravada na mesma transação do fato; publica eventos de domínio para o worker (alertas, tempo real). | [05](../spec/05-ingestao-e-telemetria.md) |
| **Pacote de evidências** | PDF + CSV de um período/veículo com hash SHA-256, quem exportou e quando; usado em ocorrências e requisições de autoridades. | [08](../spec/08-identidade-e-seguranca.md) |
| **Parquet** | Formato colunar compactado usado para o histórico frio (posições com mais de 90 dias). | [ADR-009](../adr/ADR-009-retencao-quente-frio.md) |
| **Pay As You Go** | Tipo de conta da Oracle que mantém os recursos Always Free sem custo e reduz o risco de recuperação de instância ociosa. | [ADR-005](../adr/ADR-005-infra-oracle-always-free.md) |
| **Piloto Zero** | Fase F0: 5 a 10 veículos reais da Lider com rastreamento apenas, até 31/10/2026. | [02](../spec/02-escopo-e-fases.md) |
| **PITR** | Recuperação para um instante: backup base + WAL. RPO ≤ 5 min. | [13](../spec/13-infra-e-operacao.md) |
| **`platform_fee`** | Fechamento mensal da tarifa da Versix por operadora (veículos ativos × R$ 3,90), liquidada por split ou fatura. | [12](../spec/12-cobranca-e-svas.md) |
| **Pós-chave (ignição)** | Ponto de corte na linha de ignição (~15%). Só pode atuar com o veículo parado. `cut_point = 'ignition'`. | [06](../spec/06-comandos-e-bloqueio.md) |
| **Quarentena** | Mensagem legível que não pode ser projetada (sem vínculo, fora da janela de tempo, falhas repetidas). Não alimenta mapa, alertas nem comandos. | [05](../spec/05-ingestao-e-telemetria.md) |
| **Replay** | Reprocessamento de fatos já conhecidos. Preserva identidade e nunca gera efeito externo (INV-05). | [05](../spec/05-ingestao-e-telemetria.md) |
| **REQ** | Requisito normativo com fase, prioridade, risco, invariantes e CT. | [00](../spec/00-indice.md) |
| **`revision`** | Contador do estado atual de cada rastreador (`device_state.revision`). Só cresce; clientes descartam revisão menor (INV-04). | [05](../spec/05-ingestao-e-telemetria.md) |
| **RLS** | Row-Level Security do PostgreSQL: o banco filtra as linhas pela operadora e pelos clientes do contexto da transação. Na TrackSys é sempre forçada (FORCE). | [04](../spec/04-dominio-e-dados.md) |
| **RPO / RTO** | Perda máxima de dados (≤ 5 min) / tempo máximo de recuperação (≤ 30 min com standby, ≤ 2 h sem). | [13](../spec/13-infra-e-operacao.md) |
| **SLO** | Objetivo de serviço: 99,5% ao mês, medido em minutos ruins. | [13](../spec/13-infra-e-operacao.md) |
| **Split** | Divisão automática do pagamento no Asaas: dos R$ 49,90 pagos pelo cliente à operadora, R$ 3,90 vão direto para a carteira da Versix. | [12](../spec/12-cobranca-e-svas.md) |
| **Standby** | Segunda VM Always Free com réplica do banco, pronta para assumir no failover. F1. | [13](../spec/13-infra-e-operacao.md) |
| **Step-up** | Autenticação extra exigida no momento do comando: assinatura pela chave do aparelho (app) ou segundo fator recente + motivo (console). | [08](../spec/08-identidade-e-seguranca.md) |
| **SVA** | Serviço de valor agregado vendido via indicação a parceiros: guincho, assistência 24h, revisões, gestão de custos, colisão. | [12](../spec/12-cobranca-e-svas.md) |
| **Tailscale** | Rede privada usada para acesso SSH administrativo às VMs; a porta 22 não fica aberta na internet. | [13](../spec/13-infra-e-operacao.md) |
| **Testes congelados** | Testes de aceite em `tests/acceptance/T-NNN/`, escritos antes da implementação; um PR de implementação não pode alterá-los. | [14](../spec/14-qualidade-e-processo-ia.md) |
| **Traccar** | Servidor open source que decodifica os protocolos dos rastreadores e envia comandos; é a borda de protocolos da TrackSys. | [ADR-003](../adr/ADR-003-traccar-borda-de-protocolos.md) |
| **UNKNOWN** | Estado de comando com resultado indeterminado. Nunca dispara repetição automática de bloqueio (INV-08). | [06](../spec/06-comandos-e-bloqueio.md) |
| **WAL** | Log de escrita do PostgreSQL, arquivado continuamente (WAL-G) para backup e réplica. | [13](../spec/13-infra-e-operacao.md) |
| **WNRO** | Bug de "virada da semana GPS" em rastreadores baratos: datas ~19,6 anos no passado. Barrado pela janela de tempo aceita. | [05](../spec/05-ingestao-e-telemetria.md) |
