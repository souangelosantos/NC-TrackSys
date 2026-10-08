# Anexo B — Jurídico e LGPD

> **Resumo:** Base jurídica de engenharia e produto da TrackSys: papéis LGPD, bases legais por finalidade, retenção, encarregado e direitos do titular, mais rascunhos estruturados dos 10 documentos de que a operação precisa (termo do Piloto Zero, contrato SaaS, DPA, termos de uso, política de privacidade, termo de ciência do bloqueio, consentimentos, procedimento para autoridades, comunicação de incidente e perguntas ao advogado). Cada cláusula aponta o capítulo técnico que a sustenta.
> **Fases:** F0, F1, F2  ·  **Status:** Aprovado para execução (engenharia); rascunho para revisão jurídica (DEC-08)
> **Muda em relação à v1.1:**
> - A v1.1 dizia "governança a validar" sem nomear papéis. Aqui há controladora, operadora, encarregado, bases legais e prazos.
> - Entram Marco Civil (6 meses), auditoria de 5 anos, legal hold, pacote de evidências e procedimento para a polícia, que já pediu histórico à Lider.
> - Bloqueio em movimento ganha cláusula contratual de responsabilidades e termo de ciência do cliente final.

> **Aviso.** Este anexo é base de engenharia e produto para revisão por advogado de tecnologia/LGPD (DEC-08). **Não é parecer jurídico.** Toda referência normativa traz [VALIDAR]. Antes da revisão, só entram em uso real os textos marcados "uso antes da revisão" na §1; cada um ganha nova versão depois dela, com novo aceite quando houver.

## 1. Prontidão jurídica por marco

| Marco | Data | Documento | Mínimo exigido | Evidência |
|---|---|---|---|---|
| S2 | até 20/10/2026 | Política de privacidade da plataforma v0 (§9.1) | Publicada em `https://app.<domínio>/privacidade`; as lojas exigem URL de política e formulário de dados antes de distribuir a testadores externos [VALIDAR] | URL cadastrada no TestFlight e no Google Play |
| G0 | 31/10/2026 | Termo de participação (§5.1) e acordo de piloto Versix–Lider (§5.2) | Uso antes da revisão. 1 termo por titular, assinado antes do SMS de migração (G0-9) | Termos digitalizados em pasta privada da Lider; lista no `docs/runbooks/gates/G0.md` sem dados pessoais |
| G-CMD | 2ª quinzena de novembro | Termo de ciência `block-terms-v1` (§10) | Uso antes da revisão. Publicado em `packages/contracts/src/consent/texts/block-terms-v1.md`; aceito pelo titular do veículo do teste supervisionado (GC-4) | Linha em `consent` + SHA-256 no `consent/manifest.json` |
| F1 (guincho) | quando o botão entrar | `sva-referral-v1` ([12 §16](../spec/12-cobranca-e-svas.md)) | Uso antes da revisão | Idem |
| G1 | 31/12/2026 | Contrato SaaS (§6), DPA (§7), termos de uso (§8), políticas revisadas (§9), DEC-15 | Revisados e assinados pela Lider; política da Lider publicada no app (G1-4) | Contrato assinado; URLs publicadas |
| F2 | antes da 2ª operadora | Pacote revisado | Plano B da DEC-08: nenhuma operadora além da Lider sem revisão | — |
| F2 | antes do agente de suporte IA | DPA com Anthropic como suboperador e mecanismo de transferência (§7.2) | Lista de suboperadores atualizada e avisada com 30 dias | Aviso enviado às operadoras |

## 2. Papéis LGPD

| Tratamento | Controladora | Operadora (processadora) | Observação |
|---|---|---|---|
| Serviço de rastreamento ao cliente final: posição, histórico, alertas, comandos, ocorrência, compartilhamento, atendimento, cobrança | Operadora de rastreamento | Versix (TrackSys) e suboperadores da §7.2 | Versix trata só por instrução documentada: contrato, DPA e configuração feita pela operadora no console (LGPD art. 39 [VALIDAR]) |
| Indicação de SVA (registro, apuração, repasse) | Versix, para a finalidade própria de receber do parceiro; operadora, para a parte dela | — | Base: consentimento por parceiro (§11). Controladoria conjunta ou independente: pergunta Q-02 |
| Atendimento pelo parceiro após indicação consentida | Parceiro, controlador independente | — | Recebe só o que o titular enviou ou consentiu ([12 §15](../spec/12-cobranca-e-svas.md)) |
| Registros de acesso (Marco Civil) | Versix, como provedora da aplicação TrackSys publicada nas lojas [VALIDAR — Q-04] | — | `access_log`, 6 meses |
| Segurança da plataforma e antifraude (IMEI forjado, limites de taxa, salto impossível) | Versix (legítimo interesse) [VALIDAR] | — | [08 §10](../spec/08-identidade-e-seguranca.md) |
| Cobrança no Asaas | Operadora; o Asaas é contratado por ela | Versix acessa a conta por conta e ordem da operadora | Chave cifrada ([08 §8](../spec/08-identidade-e-seguranca.md)) |
| Tarifa da Versix (`platform_fee`, split) | Versix | Asaas (conta da Versix) | Operadora MEI é pessoa natural: dados dela são pessoais [VALIDAR] |
| Operação da plataforma (métricas, sondas, agente SRE) | Versix | — | Sem dado pessoal (INV-11; [13 §11](../spec/13-infra-e-operacao.md)) |

**Titulares:** cliente final (`tenant_owner`); familiares e condutores (`tenant_member` e condutores sem conta); equipe da operadora (`operator_admin`, `operator_agent`, `installer`, `search_team`); visitante de link compartilhado (IP e horário); contato do parceiro. O contratante declara nos termos de uso (§8) que informou os condutores habituais de que o veículo é rastreado.

## 3. Finalidades, bases legais e retenção

Serve de registro das operações de tratamento (LGPD art. 37 [VALIDAR]). Base legal pelo art. 7º da LGPD [VALIDAR]. Prazos canônicos de [04 §8.1](../spec/04-dominio-e-dados.md).

| # | Finalidade | Dados | Base legal | Retenção |
|---|---|---|---|---|
| T1 | Rastreamento: mapa ao vivo e histórico | Posição, velocidade, rumo, ignição, estado do rastreador | Execução de contrato (V) | 12 meses: 90 dias quentes + 9 meses frios em Parquet |
| T2 | Alertas e push | Tipo, horário, veículo, token de push | Execução de contrato (V) | Alertas 12 meses [PREMISSA de 04]; token sem uso 60 dias |
| T3 | Bloqueio e desbloqueio | Pedido, evidência de velocidade e ignição, tentativas, resultado | Execução de contrato (V) | 5 anos |
| T4 | Auditoria de comandos e ações administrativas | `audit_log`, `command_event` | Exercício regular de direitos (VI) [VALIDAR — Q-05] | 5 anos (prescrição do CDC art. 27 [VALIDAR]) |
| T5 | Ocorrência, equipe de busca e link para a polícia | Posição ao vivo, linha do tempo, número do BO | Execução de contrato (V) a pedido do titular; risco iminente à vida: proteção da vida (VII) [VALIDAR] | Como T1 e T3 |
| T6 | Compartilhamento temporário (família) | Posição atual, modelo, cor, placa opcional | Execução de contrato (V), por ação do titular | Link ≤ 24 h |
| T7 | Segurança e antifraude | Envelope bruto do Traccar, identidade de dedupe, IP, limites | Legítimo interesse (IX), com teste de balanceamento registrado (art. 10 [VALIDAR]) | Bruto 7 dias; identidade 90 dias |
| T8 | Registros de acesso | IP, porta de origem, data e hora UTC, user agent | Obrigação legal (II): Marco Civil art. 15 [VALIDAR] | 6 meses |
| T9 | Cobrança e PIX | Nome, CPF, faturas, código PIX | Execução de contrato (V); obrigação legal fiscal (II) [VALIDAR] | 5 anos |
| T10 | Atendimento | Ticket, notas, veículo, alerta | Execução de contrato (V) | Até a anonimização do cliente |
| T11 | Indicação de SVA | Veículo, serviço, localização enviada, valores | Consentimento (I) por parceiro e finalidade | 5 anos como registro financeiro; localização zerada em 90 dias |
| T12 | Termo de ciência do bloqueio | Versão aceita, data, usuário | Não é consentimento como base legal: é aceite informado ligado ao contrato (V) e prova do dever de informar (CDC art. 6º, III [VALIDAR]) | 5 anos |
| T13 | Agente de IA de suporte (F2) | Dados no escopo de quem pergunta | Execução de contrato (V) com a operadora | [DECISÃO DO FUNDADOR PENDENTE: conversas por 90 dias] |
| T14 | Cliente encerrado | Cadastro e veículos | — | Anonimização após 12 meses, salvo legal hold ou obrigação legal (DEC-15; [04 §9.2](../spec/04-dominio-e-dados.md)) |

**Fora de escopo:** marketing a clientes finais, venda ou cessão de dados, perfilamento para seguradora. O score de risco (M10, F3) exige nova avaliação, RIPD e base legal própria. Localização não é dado sensível na LGPD (art. 5º, II [VALIDAR]), mas revela rotina: vale a minimização de [08 §11](../spec/08-identidade-e-seguranca.md).

## 4. Encarregado, canal e direitos do titular

1. **Encarregado da Versix:** o fundador ({nome do fundador}), `privacidade@<domínio>` [PREMISSA até DEC-04], publicado na política da plataforma. É nomeado mesmo se a Versix for dispensada como agente de pequeno porte (Res. CD/ANPD 2/2022 [VALIDAR]), porque rastreamento contínuo pode ser tratamento de alto risco (Q-01). Atuação do encarregado: Res. CD/ANPD 18/2024 [VALIDAR].
2. **Encarregado da operadora:** cada operadora indica o seu ou o canal equivalente; aparece na política da marca (§9.2). Lider: o titular da MEI [PREMISSA].
3. **Canal no app:** Conta (A10) › Privacidade ([08 §11](../spec/08-identidade-e-seguranca.md)): baixar meus dados (ZIP pronto em ≤ 24 h), revogar consentimentos, pedir correção ou eliminação (atendimento `lgpd` com vencimento em 15 dias) e excluir conta.
4. **Identidade:** pedido feito dentro da sessão do app vale como identificado. Pedido por e-mail ou WhatsApp é confirmado pelo canal cadastrado; dados nunca vão para endereço diferente do cadastrado.

| Direito (LGPD art. 18 [VALIDAR]) | Como a TrackSys atende | Quem responde | Prazo |
|---|---|---|---|
| Confirmação e acesso | ZIP self-service (cadastro, memberships, consentimentos, alertas, posições de 90 dias); período anterior: relatório frio ([04 §8.3](../spec/04-dominio-e-dados.md)) | Operadora; Versix gera | 15 dias (art. 19, II [VALIDAR]); self-service ≤ 24 h |
| Correção | Atendimento `lgpd`; a central corrige no console | Operadora | 15 dias |
| Anonimização, bloqueio ou eliminação de dado excessivo | Atendimento `lgpd`; avaliação pela operadora | Operadora | 15 dias |
| Portabilidade | Mesmo ZIP, em CSV e JSON | Operadora | 15 dias [VALIDAR: regulamentação pendente na ANPD] |
| Eliminação de dado tratado com consentimento | Revogar `sva_referral` interrompe novas indicações; registros financeiros ficam 5 anos | Versix e operadora | Imediato |
| Informação sobre compartilhamento | Política de privacidade (§9) | Controladora | 15 dias |
| Revogação do consentimento | `DELETE /api/v1/me/consents/{id}` | — | Imediato |
| Oposição a tratamento por legítimo interesse | Atendimento `lgpd` | Controladora do tratamento | 15 dias |
| Revisão de decisão automatizada (art. 20 [VALIDAR]) | Não se aplica: comando nasce de pedido humano; a política só recusa ou adia | — | — |

**Excluir conta:** revoga sessões e chave do aparelho na hora e abre atendimento `lgpd` de eliminação; a eliminação segue o encerramento e a anonimização de [04 §9.2](../spec/04-dominio-e-dados.md). As lojas exigem caminho de exclusão de conta dentro do app (Apple 5.1.1(v); política do Google Play) [VALIDAR].

## 5. Rascunho 1 — Piloto Zero (uso antes da revisão)

### 5.1 Termo de participação (titular ↔ operadora; Versix como plataforma)

Minuta simples, 1 página, para assinar até 27/10/2026, antes do SMS de migração.
1. **Partes.** {operadora: razão social, CPF/CNPJ}; participante {nome, CPF}; veículo {placa, modelo, cor}. Versix Solutions ({CNPJ do fundador}, DEC-14) aparece como fornecedora da plataforma TrackSys.
2. **Objeto.** Testar a TrackSys com o rastreador já instalado, de {data} até a assinatura dos termos de uso definitivos ou 31/01/2027, o que vier primeiro.
3. **Gratuidade.** A participação não gera cobrança. A mensalidade com a {operadora} não muda, salvo acordo entre as partes.
4. **O que muda.** O rastreador é reconfigurado por SMS para o servidor da TrackSys. O participante usa o app TrackSys em teste (TestFlight ou teste fechado do Google Play), com a marca da {operadora}. O veículo deixa de aparecer no tracker-net.
5. **Bloqueio.** Marcar uma: ( ) o veículo fica **sem bloqueio remoto** pelo app e pela central durante o piloto; ( ) o bloqueio continua pelo tracker-net, só se o J16 aceitar servidor secundário [VALIDAR — DEC-02]. Em furto ou roubo: ligar 190 e avisar a central; a localização continua no app.
6. **Riscos.** App em teste: pode falhar ou ficar fora do ar. Alertas podem atrasar ou não chegar. Tudo depende de sinal celular, GPS e energia do veículo. Não é serviço de emergência.
7. **Saída.** O participante sai quando quiser, pelo WhatsApp da central. A {operadora} devolve o rastreador ao tracker-net por SMS em até 48 h [PREMISSA].
8. **Dados.** Cadastro (nome, e-mail, telefone), veículo, posições, alertas e registros de acesso, para prestar o rastreamento e avaliar o piloto. A {operadora} é controladora; a Versix é operadora. Servidores no Brasil (Oracle); push por Google e Apple; cópia de backup cifrada fora do Brasil. Retenção de 12 meses. Direitos: central da {operadora} ou `privacidade@<domínio>`. Sem marketing. Números do piloto só entram no case de forma agregada, sem identificar o participante.
9. **Condutores.** O participante informa os condutores habituais de que o veículo é rastreado. Veículo da frota da {operadora}: o funcionário que dirige assina a ciência dos itens 6 e 8.
10. **Assinatura.** Eletrônica (gov.br ou plataforma de assinatura) ou em papel, 1 via para cada parte (Lei 14.063/2020 [VALIDAR — Q-17]).

### 5.2 Acordo de piloto Versix–Lider (1 página)

1. **Vigência:** da assinatura até a assinatura do contrato SaaS revisado ou 31/01/2027, o que vier primeiro.
2. **Preço:** F0 gratuito. Desde 01/11/2026, R$ 3,90 por veículo ativo por mês ([REQ-NEG-002](../spec/01-visao-e-negocio.md)); adesão conforme a opção escolhida em [Anexo A §5](A-comercial.md); veículo de cliente inadimplente conforme DEC-06.
3. **Dados:** Lider controladora, Versix operadora. Valem desde já as cláusulas 1, 3, 4, 5, 7 e 11 do DPA (§7.1).
4. **Comandos (a partir do G-CMD):** valem os itens 1 a 9 da §6.3. A Lider aprova por escrito a `command_policy` com o teto escolhido (DEC-07).
5. **Saída:** exportação completa em 30 dias (§6.5, cláusula de portabilidade); a Lider reaponta os rastreadores.
6. **Case:** a Lider autoriza ( ) nome e logo ( ) números agregados no material comercial da Versix.

## 6. Rascunho 2 — Contrato SaaS Versix–Operadora

### 6.1 Cláusulas-chave

| Cláusula | Proposta | Base técnica |
|---|---|---|
| Partes | Versix Solutions (nome fantasia no CNPJ do fundador, DEC-14) e a operadora | — |
| Objeto | Licença de uso, como serviço, da TrackSys: recepção de dados de rastreadores homologados, app com a marca da operadora (opção C), console, alertas, comandos, integração Asaas e SVA. Fora do objeto: rastreador, chip, instalação, central de monitoramento, atendimento ao cliente final, recuperação de veículo | [02](../spec/02-escopo-e-fases.md) |
| Licença | Não exclusiva, intransferível, enquanto durar o contrato. A operadora licencia à Versix nome e logo para exibição no app | [ADR-007](../adr/ADR-007-app-unico-flutter-marca-dinamica.md) |
| Preço | R$ 3,90 por veículo ativo por mês; adesão única de R$ 2.500 a R$ 3.000; plano superior proposto de R$ 5,90 (DEC-09). Reajuste anual pelo IPCA [PREMISSA] | [REQ-NEG-002](../spec/01-visao-e-negocio.md) |
| Pagamento | Split no Asaas de cada cobrança paga pelo cliente final; diferença faturada pela Versix com vencimento no dia 10; sobra vira crédito | [12 §10](../spec/12-cobranca-e-svas.md) |
| SLA | 99,5% ao mês = até 3 h 36 min de minutos ruins em 30 dias. Minuto ruim: sonda externa falhou (TCP em `gps.<domínio>` ou HTTPS da API) ou p95 de alerta (Traccar recebe → push enviado ao FCM) > 120 s. Manutenção anunciada com 48 h fica fora. Medição na status page | [13](../spec/13-infra-e-operacao.md) |
| Créditos | 10% da mensalidade se < 99,5%; 25% se < 99,0%; abatidos na tarifa do mês seguinte; crédito é o remédio exclusivo da indisponibilidade [VALIDAR] | [12 §10.2](../spec/12-cobranca-e-svas.md) |
| Exclusões do SLA | Cobertura celular, chip suspenso, rastreador desligado ou com defeito, instalação, entrega do FCM/APNs ao aparelho, internet do usuário, lojas de app, atos da operadora, força maior (Código Civil art. 393 [VALIDAR]) | — |
| Suporte | SEV1 24 × 7 com fundador em ≤ 15 min; SEV2 no mesmo dia; SEV3 em horário comercial. Canal: WhatsApp e e-mail da Versix; agente de IA no F2. O atendimento ao cliente final é da operadora | [13 §14](../spec/13-infra-e-operacao.md) |
| Responsabilidades | Matriz da §6.2 | — |
| Comandos físicos | §6.3 | [06](../spec/06-comandos-e-bloqueio.md) |
| Contingência | Status page; runbook de 1 página do plantonista; SMS pelo portal emnify/Meta Telecom. A operadora mantém acesso ao portal e as senhas SMS; ensaio no G1 (G1-6) | [Anexo C](C-operacional.md) |
| Limitação de responsabilidade | §6.4 | — |
| Dados | DPA anexo (§7). Dados da operadora e dos clientes pertencem a eles. Estatísticas agregadas e anonimizadas para operar e melhorar a plataforma são permitidas [VALIDAR] | — |
| Confidencialidade | Durante o contrato e 5 anos depois [PREMISSA] | — |
| Propriedade intelectual | Plataforma, código, app e documentação são da Versix. Marca e dados são da operadora. Proibida engenharia reversa | Q-18 |
| Não aliciamento | A Versix não oferece rastreamento diretamente aos clientes da operadora nem usa a base dela para levá-los a outra operadora, durante o contrato e 12 meses depois [PREMISSA]. SVA no app segue a cláusula SVA | Q-19 |
| SVA e repartição | Parceiro nacional: Versix fecha, operadora recebe 20–30% (DEC-05). Parceiro local: operadora fecha, divisão proposta de 50% (proposta registrada em [12 §14](../spec/12-cobranca-e-svas.md)). Operadora liga e desliga cada SVA; indicação remunerada informada ao cliente; relatório mensal; repasse por PIX | [12 §13–15](../spec/12-cobranca-e-svas.md) |
| Vigência e término | 12 meses com renovação automática [PREMISSA]; rescisão sem motivo com 30 dias de aviso [PREMISSA]; com motivo, imediata após 15 dias sem correção. Inadimplência da operadora suspende o acesso ao console, nunca dispara bloqueio de veículos (INV-09) | — |
| Portabilidade e saída | §6.5 | [04 §8](../spec/04-dominio-e-dados.md) |
| Continuidade | §6.5 | [15 §3.1](../spec/15-decisoes-riscos-premissas.md) |
| Foro | Comarca da sede da Versix [PREMISSA] | Q-07 |

### 6.2 Matriz de responsabilidades

| Tema | Versix (plataforma) | Operadora | Instalador (sob responsabilidade da operadora) | Cliente final |
|---|---|---|---|---|
| Disponibilidade, backup, segurança e isolamento | Executa e mede | — | — | — |
| Política de comando (`command_policy`) | Teto da plataforma e salvaguardas | Define valores ≤ teto e quem da central comanda | — | — |
| Ligação física do relé e `cut_point` | Bloqueio indisponível sem `cut_point` (INV-10) | Responde pelo registro correto | Faz a ligação e registra o tipo real | — |
| Homologação do rastreador | Bancada, 20 ciclos, perfil versionado | Fornece aparelho e senha SMS | — | — |
| Termo de ciência do bloqueio | Exibe, versiona e registra | Informa e treina a central | — | Aceita e usa com responsabilidade |
| Pedido de comando | Transmite e registra; nunca decide por conta própria | Responde pelos atos da central e da equipe de busca | — | Responde pelos próprios pedidos e dos familiares que autorizou |
| Chips, APN, contrato com Meta Telecom | Usa a API por delegação (DEC-01) | Contrata e paga | — | — |
| Conta Asaas e cobrança do cliente | Integra e sincroniza | Titular da conta e da relação de cobrança | — | Paga |
| Atendimento, recuperação, polícia | Ferramentas (ocorrência, link, pacote de evidências) | Executa | — | Aciona |
| Incidente com dado pessoal | Avisa a operadora em ≤ 24 h | Comunica ANPD e titulares | — | — |

### 6.3 Cláusula de comandos físicos

1. A plataforma transmite ao rastreador pedidos de usuários autorizados e registra cada etapa. Não garante a atuação física: "confirmado" exige evidência homologada; "não confirmado" (UNKNOWN) significa efeito não comprovado.
2. Teto da plataforma para corte de bomba em movimento: 40 km/h (DEC-07). A operadora configura valor ≤ teto. Ignição só com o veículo parado; motor de arranque a qualquer momento ([06 §3.2](../spec/06-comandos-e-bloqueio.md)).
3. Bloqueio só com `cut_point` registrado, perfil homologado com relé, termo de ciência do titular e step-up (INV-10; [06 §2](../spec/06-comandos-e-bloqueio.md)).
4. A Versix mantém as salvaguardas técnicas: evidência de no máximo 60 s, ARMED com TTL de 5 min (30 min em ocorrência), nenhuma repetição automática de bloqueio, desbloqueio com retentativa a cada 60 s até 5 tentativas e SMS após 2 min.
5. A operadora NÃO PODE usar bloqueio como meio de cobrança. A plataforma não liga inadimplência a comando (INV-09).
6. A operadora define quem da central e da equipe de busca pode comandar, treina essas pessoas e responde pelos atos delas.
7. O instalador define a ligação física sob responsabilidade da operadora. Registro de `cut_point` diferente da instalação real é responsabilidade da operadora.
8. A Versix pode desligar o bloqueio de um perfil ou da plataforma por risco de segurança, avisando a operadora em até 1 h [PREMISSA]. O desbloqueio continua disponível. Agentes de IA da Versix nunca despacham comandos (INV-11).
9. Contingência por SMS manual é executada pela central da operadora e registrada em até 72 h ([06 §10](../spec/06-comandos-e-bloqueio.md)). A Versix guarda a auditoria por 5 anos e fornece os registros para perícia.

### 6.4 Limitação de responsabilidade

1. Teto proposto: soma das tarifas pagas pela operadora nos 12 meses anteriores ao evento (12 mensalidades) [VALIDAR — Q-07]. Exemplo Lider: 300 veículos × R$ 3,90 × 12 = R$ 14.040.
2. Sem danos indiretos nem lucros cessantes [VALIDAR].
3. Fora do teto: dolo, culpa grave, violação de confidencialidade e descumprimento do DPA [VALIDAR].
4. Entre as partes vale o direito de regresso conforme a matriz da §6.2. Perante o cliente final, a solidariedade da cadeia de fornecimento do CDC pode prevalecer (arts. 7º, parágrafo único, e 25, §1º [VALIDAR — Q-08]).
5. Seguro de responsabilidade civil e cibernético: cotar antes do G1 (Q-08).

### 6.5 Portabilidade, saída e continuidade

1. **Exportação completa em até 30 dias** do pedido ou do término: CSV e JSON (clientes, veículos, rastreadores, chips, vínculos com `cut_point`, alertas, comandos, auditoria, consentimentos, indicações) e Parquet (posições dos últimos 12 meses, quentes e frias), com `manifest.json` e SHA-256 por arquivo; entrega por link temporário.
2. **Ingestão estendida:** a Versix mantém a recepção por até 60 dias após o término, com tarifa normal, para a operadora reapontar os rastreadores por SMS [PREMISSA]. A Versix fornece os modelos de SMS do perfil.
3. **Eliminação:** em até 30 dias após a operadora confirmar o recebimento da exportação; backups cifrados expiram pela rotação em até 35 dias ([13](../spec/13-infra-e-operacao.md)). Ficam só legal hold ativo e o que a lei obrigar [VALIDAR — Q-05]. A Versix envia declaração de eliminação.
4. **Continuidade:** encerramento do serviço pela Versix exige aviso de 90 dias [PREMISSA] e exportação. Em impedimento do fundador, o contato de emergência entrega a exportação seguindo `docs/runbooks/emergencia.md` ([15 §3.1](../spec/15-decisoes-riscos-premissas.md)). Depósito do código em custódia de terceiro: Q-18.

## 7. Rascunho 3 — DPA (acordo de tratamento de dados)

### 7.1 Cláusulas

1. **Instruções.** A Versix trata dados só para T1–T10 e T13 da §3, conforme o contrato e a configuração da operadora no console. Avisa a operadora se uma instrução violar a LGPD (art. 39 [VALIDAR]).
2. **Escopo.** Titulares e dados das §2 e §3; duração = contrato + prazo de eliminação (§6.5).
3. **Confidencialidade.** Fundador e freelancers com termo de confidencialidade. Agentes de IA de codificação não acessam dados de produção ([REQ-QLD-016](../spec/14-qualidade-e-processo-ia.md)).
4. **Segurança.** RLS forçada e FK composta (INV-07); TLS; TOTP para administradores; segredos com SOPS e AES-256-GCM; logs sem dado pessoal; backups cifrados com restore mensal; `access_log`; `audit_log` de 5 anos; acesso de suporte só com grant de até 72 h, somente leitura e auditado ([08](../spec/08-identidade-e-seguranca.md), [04 §4.5](../spec/04-dominio-e-dados.md)).
5. **Suboperadores.** Lista da §7.2. Mudança avisada com 30 dias; objeção fundamentada permite rescindir sem multa. A Versix responde pelos suboperadores [VALIDAR].
6. **Transferência internacional.** Só para os fornecedores da §7.2, com o mecanismo da Res. CD/ANPD 19/2024 (cláusulas-padrão contratuais) [VALIDAR — Q-06].
7. **Incidentes.** A Versix avisa a operadora em até 24 h da ciência (modelo da §13) e atualiza a cada 24 h. A operadora comunica a ANPD e os titulares em 3 dias úteis (Res. CD/ANPD 15/2024 [VALIDAR — Q-13]); a Versix fornece os dados técnicos.
8. **Direitos do titular.** A Versix mantém as ferramentas da §4 e responde em até 5 dias úteis [PREMISSA] ao pedido da operadora que depender dela.
9. **Autoridades.** A Versix encaminha à operadora em até 24 h a requisição que receber (§12).
10. **Auditoria.** 1 vez por ano, aviso de 30 dias, documental: questionário e evidências (CI com CAT e ISO verdes, relatório de restore, lista de suboperadores, registro de incidentes, relatório de SLO). Auditoria técnica no local só após incidente com dado pessoal, a custo da operadora [PREMISSA].
11. **Devolução e eliminação.** §6.5.
12. **RIPD.** A Versix fornece as informações técnicas deste anexo e do [08](../spec/08-identidade-e-seguranca.md) para o relatório de impacto da operadora (art. 38 [VALIDAR]).
13. **Responsabilidade.** Operador responde solidariamente se descumprir a LGPD ou as instruções (art. 42 [VALIDAR]).

### 7.2 Suboperadores

| Fornecedor | Serviço | Dados pessoais | Onde processa | Transferência internacional | Desde |
|---|---|---|---|---|---|
| Oracle Cloud (OCI) | VMs, banco, Traccar, object storage (backup primário, Parquet frio) | Todos | Brasil: `sa-saopaulo-1` ou `sa-vinhedo-1` (DEC-12) | Não | F0 |
| Cloudflare R2 | Cópia de backup | Todos, cifrados pelo WAL-G antes do envio; chave só com a Versix | Fora do Brasil [VALIDAR] | Sim, cifrada [VALIDAR — Q-06] | F0 |
| Google Firebase (FCM), com entrega iOS pela Apple (APNs) | Push | Token do aparelho; título e texto (tipo, apelido ou placa, hora); sem coordenadas nem endereço ([07](../spec/07-alertas-e-tempo-real.md)) | EUA [VALIDAR] | Sim | F0 |
| Sentry | Erros e saúde de versão (`api`, `worker`, console, app) | Identificadores técnicos; `sendDefaultPii: false` e `beforeSend` removem corpo, query string e headers de autenticação | Região escolhida na criação [VALIDAR] | Sim | F0 |
| Grafana Cloud | Métricas e logs | Sem dado pessoal: o Alloy mascara IMEI e remove coordenadas | Região mais próxima do Brasil [VALIDAR] | Só se a redação falhar | F0 |
| Provedor de e-mail: Resend no F0 ([13 §6](../spec/13-infra-e-operacao.md)); Brevo como alternativa | Convites, redefinição de senha, avisos | E-mail e conteúdo da mensagem | EUA (Resend) [VALIDAR]; UE se trocar para Brevo | Sim | F0 |
| Anthropic (API Claude) | Agente SRE (F1): métricas e logs sem dado pessoal. Agente de suporte (F2): dados mínimos no escopo de quem pergunta (nomes, placas, texto de atendimento) | Ver serviço | EUA [VALIDAR]; retenção e uso para treino conforme os termos comerciais da API [VALIDAR] | Sim | F1 / F2 |
| emnify, via Meta Telecom | SMS (desbloqueio, migração), diagnóstico de chip | ICCID, MSISDN, conteúdo do SMS de comando, status de conexão | [VALIDAR] | Provável [VALIDAR] | F1. Contratado pela operadora; Versix usa a API por delegação (DEC-01) |
| Meta Telecom | Administração dos chips | Idem | Brasil [VALIDAR] | [VALIDAR] | Contratado pela operadora |
| Asaas | Cobrança e split | Nome, CPF/CNPJ, e-mail, telefone, valores | Brasil [VALIDAR] | Não [VALIDAR] | F1. Contratado pela operadora; a conta Asaas da Versix só recebe o split |
| Cloudflare (DNS, Worker), Pushover, UptimeRobot, Tailscale, GitHub | DNS, gateway de incidentes, paging, sondas, rede de administração, código | Sem dado pessoal de titulares | EUA e outros [VALIDAR] | — | F0 (listados por transparência) |

**Terceiros acionados pelo titular (não são suboperadores; constam da política):** WhatsApp (deep link para a central e o parceiro, com placa e link de posição); Google Maps e Waze ("Navegar até o veículo"); parceiros de SVA; OpenFreeMap, que recebe o IP do aparelho e a área do mapa exibida ao baixar os tiles [VALIDAR] (DEC-11: PMTiles auto-hospedado elimina esse fluxo).

## 8. Rascunho 4 — Termos de uso do app

Relação: cliente final ↔ operadora, que presta o serviço. A Versix aparece como fornecedora da tecnologia. Texto versionado `terms-of-use-v{N}` [ADOTADO NA v2.0: aceite registrado em `consent` com `purpose = 'terms_of_use'` no 1º login e a cada versão nova, como clickwrap com `text_version` e SHA-256 do texto].

| Tópico | Cláusula-chave |
|---|---|
| Conta | Criada por convite da operadora; credenciais pessoais; celular perdido → avisar a central, que revoga sessões e chave do aparelho |
| Uso permitido | Só veículos próprios ou com autorização do proprietário; condutores habituais informados; proibido usar para perseguir pessoa (Código Penal art. 147-A [VALIDAR]) |
| Limites do serviço | Depende de GPS, sinal celular e energia; a posição pode estar atrasada e o app mostra a idade; garagem subterrânea e áreas sem sinal; não é serviço de emergência: em perigo, ligar 190 |
| Alertas | Melhor esforço, sem garantia de entrega; dependem das notificações e do modo de economia do celular |
| Bloqueio | Só após o termo de ciência (§10); atraso de pagamento nunca causa bloqueio |
| Compartilhamento | Links de 1 h, 4 h ou 24 h, revogáveis; quem compartilha responde por quem recebe |
| Ocorrência | Abrir ocorrência não aciona a polícia; central e equipe de busca agem conforme o contrato com a operadora |
| Familiares | O titular convida, revoga e define quem pode comandar; responde pelos convidados |
| Pagamento | Com a operadora (PIX ou boleto); atraso leva a suspensão comercial, sem efeito no veículo |
| SVA | Parceiros independentes respondem pelo serviço; indicação remunerada informada; consentimento por parceiro |
| Dados | Política de privacidade da operadora (§9.2) |
| Mudanças | Aviso no app 15 dias antes [PREMISSA]; nova versão exige aceite |
| Foro | Domicílio do consumidor (CDC art. 101, I [VALIDAR]) |

## 9. Rascunho 5 — Políticas de privacidade

### 9.1 Política da plataforma (Versix)

Exigida pelas lojas para o app único TrackSys. URL `https://app.<domínio>/privacidade`. Cobre a Versix como operadora do serviço das operadoras e como controladora de T7, T8 e T11; lista a §7.2; aponta para a política de cada operadora.

### 9.2 Modelo da operadora (campos)

Exibida no app da marca (A10). [ADOTADO NA v2.0: quando `operator_brand.privacy_policy_url` (proposta de [08 §11](../spec/08-identidade-e-seguranca.md)) for NULL, o app abre a página padrão `https://app.<domínio>/privacidade/{operatorId}`, gerada deste modelo com os campos abaixo.]

| Campo | Origem | Exemplo |
|---|---|---|
| `{razaoSocial}`, `{documento}` | `operator.legal_name`, `operator.document` | Lider Rastreamento, CNPJ MEI |
| `{nomeFantasia}`, `{whatsapp}` | `operator_brand.display_name`, `support_whatsapp` | Lider, +55 86 9xxxx-xxxx |
| `{endereco}`, `{encarregadoNome}`, `{encarregadoEmail}` | Campos novos de `operator_brand` [proposta para [04](../spec/04-dominio-e-dados.md)] | — |
| `{versaoTexto}`, `{vigenteDesde}` | Arquivo versionado | `privacy-operator-v1`, 31/12/2026 |

Seções: (1) quem somos: operadora controladora e Versix operadora; (2) dados coletados (§3); (3) de onde vêm: rastreador, app, central, Asaas; (4) finalidades e bases (§3); (5) compartilhamento: suboperadores, terceiros acionados pelo titular, parceiros com consentimento, autoridades (§12); (6) transferência internacional; (7) retenção (§3); (8) direitos e como exercer, prazo de 15 dias (§4); (9) segurança; (10) uso só por maiores de 18 anos; (11) mudanças; (12) contato e encarregado.

### 9.3 Declarações das lojas

Nomes das categorias conforme Apple App Privacy e Google Play Data safety [VALIDAR].

| Dado | Coletado | Vinculado ao usuário | Finalidade | Observação |
|---|---|---|---|---|
| Localização precisa | Sim | Sim | Funcionalidade | Do veículo, via rastreador; o app não lê o GPS do celular ([10](../spec/10-apps-e-ux.md)) |
| Nome, e-mail, telefone | Sim | Sim | Funcionalidade (conta) | — |
| Identificadores (ID de usuário, token de push) | Sim | Sim | Funcionalidade | — |
| Informações financeiras (faturas, código PIX) | Sim (F1) | Sim | Funcionalidade | Sem cartão |
| Diagnóstico (falhas, desempenho) | Sim | Não [VALIDAR] | Funcionalidade e análise | Sentry |
| Rastreamento para publicidade | Não | — | — | Sem SDK de anúncios |

Dados cifrados em trânsito: sim. Exclusão de conta: sim (§4).

## 10. Rascunho 6 — Termo de ciência do bloqueio (uso antes da revisão)

Regras de [06 §12](../spec/06-comandos-e-bloqueio.md): arquivo `packages/contracts/src/consent/texts/block-terms-v1.md`; `text_version = 'block-terms-v1/{kmh}kmh'`; aceita o `tenant_owner` na tela A12; nova versão ou teto maior exige novo aceite; revogado → bloqueio indisponível, desbloqueio continua. Variáveis preenchidas pelo app: `{operadora}`, `{kmh}` (`max_moving_cut_kmh` vigente), `{armedTtlMin}` (`armed_ttl_s` / 60), `{occurrenceTtlMin}` (`occurrence_armed_ttl_s` / 60) e a lista de veículos com o `cut_point` de cada um. O texto abaixo é o conteúdo da v1; depois da revisão (DEC-08) vira v2, com novo aceite.

> **Termo de ciência do bloqueio remoto — {operadora}**
> 1. **O que o bloqueio faz em cada veículo.** {para cada veículo: "{apelido} ({placa}): {efeito}"}. Bomba de combustível: corta o combustível e o motor apaga em poucos segundos; com o veículo em movimento, o pedido só é enviado até {kmh} km/h (com {kmh} = 0: "só com o veículo parado"). Ignição: desliga a ignição; só é enviado com o veículo parado. Motor de arranque: impede a próxima partida; o motor ligado continua funcionando.
> 2. **Riscos.** Com o motor desligado em movimento, o veículo perde força e a direção e o freio podem ficar mais pesados [VALIDAR — revisão técnica e jurídica]. Quem estiver dirigindo precisa parar com segurança. Por isso o corte em movimento é limitado a {kmh} km/h e exige posição de no máximo 60 segundos.
> 3. **Sinal e atraso.** O bloqueio depende de sinal celular e GPS. Se a condição de segurança não estiver atendida, o pedido aguarda por até {armedTtlMin} minutos ({occurrenceTtlMin} minutos em ocorrência de roubo ou furto) e pode ser cancelado. Sem confirmação do rastreador, o app mostra "não confirmado" e não repete o bloqueio sozinho.
> 4. **Desbloqueio.** O app tenta de novo por até 5 minutos e pode usar SMS. Sem sinal (por exemplo, em garagem subterrânea), o desbloqueio só acontece quando o rastreador voltar a ter sinal. Evite bloquear o veículo onde não há sinal.
> 5. **Quem pode acionar.** Você; familiares que você autorizar no app; a central da {operadora}; e, em ocorrência de roubo ou furto, a equipe de busca da {operadora}. Cada pedido exige biometria (app) ou segundo fator (central), e você recebe notificação de cada comando.
> 6. **Uso responsável.** Em roubo com pessoas no veículo ou perto dele, ligue 190 primeiro. Não persiga nem confronte. O bloqueio não substitui a polícia.
> 7. **Pagamento.** Atraso de pagamento nunca causa bloqueio do veículo.
> 8. **Registro.** Cada pedido fica registrado por 5 anos com quem pediu, quando, de onde, a posição e a velocidade usadas na decisão e o resultado, e pode ser usado para esclarecer ocorrências.
> 9. **Revogação.** Você pode revogar este aceite em Conta › Privacidade. Sem ele, o bloqueio fica indisponível e o desbloqueio continua.

## 11. Rascunho 7 — Consentimento por parceiro e finalidade

Elementos obrigatórios de todo texto (LGPD arts. 8º e 9º [VALIDAR]): finalidade específica; quem trata (operadora, Versix, parceiro); dados enviados; frase de remuneração ([REQ-SVA-004](../spec/12-cobranca-e-svas.md)); como revogar; o que acontece sem aceite (sempre há caminho sem registro). Um aceite por parceiro e finalidade, revogável, texto imutável por versão ([REQ-SVA-003](../spec/12-cobranca-e-svas.md)). Texto canônico `sva-referral-v1`: [12 §16](../spec/12-cobranca-e-svas.md). Rascunho de `sva-partner-share-v1` (F2):

> Ao aceitar, você autoriza a {operadora} e a Versix Solutions (TrackSys) a enviar automaticamente ao parceiro {parceiro}, a cada pedido seu: placa, modelo e cor do veículo, serviço pedido, localização do veículo no momento do pedido, seu primeiro nome e telefone. O parceiro passa a responder por esses dados no atendimento. A {operadora} e a Versix podem receber remuneração deste parceiro pela indicação. Você pode revogar em Conta › Privacidade; sem este aceite, você ainda pode chamar o parceiro por WhatsApp ou telefone.

## 12. Rascunho 8 — Requisições de autoridades

Regra prática: **histórico de localização só com autorização do titular (vítima) ou ordem judicial.** Dados cadastrais têm regra própria. A operadora (controladora) responde; a Versix executa a parte técnica. Passos no console: [08 §11](../spec/08-identidade-e-seguranca.md) e [Anexo C](C-operacional.md).

| Pedido | Exigência mínima | Quem entrega | Como |
|---|---|---|---|
| Localização ao vivo em ocorrência, a pedido do titular | Pedido do titular no app ou à central pelo canal cadastrado | Titular ou central | Link `police` de até 24 h ([08 §7](../spec/08-identidade-e-seguranca.md)) |
| Risco iminente à vida sem o titular conseguir pedir (ex.: sequestro com vítima no veículo) | Pedido identificado da autoridade, motivo registrado | `operator_admin` | Link de até 4 h só da posição atual [VALIDAR — Q-11] |
| Histórico de localização | Ordem judicial **ou** autorização escrita do titular do veículo, limitada a veículo e período | `operator_admin` | Pacote de evidências |
| Registros de acesso | Ordem judicial (Marco Civil arts. 10, §1º, e 22 [VALIDAR]) | Versix com a operadora | CSV no pacote, com SHA-256 |
| Dados cadastrais (qualificação pessoal, filiação, endereço) | Requisição de autoridade com competência legal expressa e fundamento citado (Marco Civil art. 10, §3º; Decreto 8.771/2016 art. 11 [VALIDAR — Q-11]) | `operator_admin` | Ofício só com os campos pedidos |
| Pedido informal (telefone, WhatsApp, balcão) de histórico | Não entrega; orienta a formalizar; preserva | Central | Modelo abaixo |
| Período anterior à migração | Fora da TrackSys | Lider, pelo tracker-net ou arquivo exportado ([11 §8](../spec/11-onboarding-e-migracao.md)) | — |
| Período com mais de 12 meses | Dado eliminado pela retenção, salvo legal hold | — | Responder "inexistente pela política de retenção" |

1. **Registrar** em atendimento [ADOTADO NA v2.0: `ticket.category = 'authority'`, junto da proposta de `ticket.category` de [08 §11](../spec/08-identidade-e-seguranca.md)]: data e hora de recebimento, órgão, autoridade, número do ofício ou processo, canal, dados pedidos, veículo, período, prazo, decisão, base e SHA-256 entregue.
2. **Autenticar:** confirmar pelo telefone oficial do órgão (nunca o do próprio ofício) ou e-mail institucional; ordem judicial conferida no sistema do tribunal [VALIDAR].
3. **Preservar:** criar `legal_hold` já no recebimento ([REQ-SEG-027](../spec/08-identidade-e-seguranca.md), [REQ-DAD-015](../spec/04-dominio-e-dados.md)). Preservar não é entregar. Hold sem ordem judicial nem autorização do titular é revisto em 60 dias, por analogia ao Marco Civil art. 15, §2º [VALIDAR — Q-12], e liberado com registro se nada chegar.
4. **Decidir** pela tabela; em dúvida, advogado. Registrar base e decisão.
5. **Gerar** o pacote de evidências só com o veículo, o período e os tipos autorizados (ZIP com CSVs, `resumo.pdf` e `manifest.json` com SHA-256 por arquivo).
6. **Entregar** por link temporário (7 dias, cada download auditado) enviado ao e-mail institucional, ou em mídia com recibo. Nunca por WhatsApp.
7. **Responder** com o ofício abaixo, citando o SHA-256 do ZIP, em até 5 dias úteis ou no prazo do ofício, o que for menor [PREMISSA].
8. **Avisar o titular**, salvo sigilo determinado [VALIDAR — Q-11].
9. Requisição recebida pela Versix: encaminhar à operadora em até 24 h. Ordem judicial dirigida à Versix: cumprir no prazo e informar a operadora, salvo sigilo.

> **Modelo de resposta.** "Ref.: {ofício/processo} — {órgão}. A {operadora}, em atenção à requisição recebida em {data}, encaminha {descrição dos dados} do veículo placa {placa}, período de {início} a {fim} (horários em UTC e em Brasília), com base em {ordem judicial nº / autorização do titular de {data}}. Arquivo: {nome do ZIP}, SHA-256 {hash}, disponível em {link} até {data} ou entregue em mídia mediante recibo. Os registros foram gerados pelo sistema TrackSys a partir de dados recebidos do rastreador; a precisão depende de sinal GPS e celular. Contato: {nome}, {e-mail institucional}." / Negativa: "... informa que histórico de localização é fornecido mediante ordem judicial ou autorização do titular. Os dados do período foram preservados até {data} para eventual ordem."

## 13. Rascunho 9 — Comunicação de incidente

Incidente com dado pessoal é SEV1 ([13 §14](../spec/13-infra-e-operacao.md)) e segue o [Anexo C](C-operacional.md) para contenção. Prazos: T0 = ciência pela Versix; aviso à operadora até T0 + 24 h; atualização a cada 24 h; comunicação da controladora à ANPD e aos titulares em 3 dias úteis quando houver risco ou dano relevante (Res. CD/ANPD 15/2024 [VALIDAR — Q-13]). Todo incidente, comunicado ou não, entra no registro interno de incidentes, guardado por 5 anos [VALIDAR].

**Versix → operadora (e-mail ao `operator_admin` + WhatsApp):**
1. Identificação: número do incidente, data e hora do fato e da ciência (UTC e BRT).
2. O que aconteceu, em 3 linhas, e a causa provável.
3. Dados e titulares afetados: categorias (§3), quantidade estimada, clientes da operadora envolvidos.
4. Contenção feita e próximos passos, com horários.
5. Riscos para os titulares e o que a operadora deve fazer (comunicar ANPD, avisar clientes, trocar senhas).
6. Contato do fundador e do encarregado; horário da próxima atualização.

**Controladora → ANPD** (campos do formulário da ANPD [VALIDAR]): natureza e categorias dos dados; número de titulares; medidas técnicas e de segurança; riscos; motivo de eventual demora; medidas para reverter ou mitigar; datas do incidente e da ciência; contato do encarregado.

**Controladora → titulares** (push, e-mail e WhatsApp da operadora):
> "{operadora} informa: em {data}, um incidente de segurança na plataforma TrackSys pode ter exposto {dados}. Já fizemos {medida}. Recomendamos {ação: trocar a senha do app / atenção a mensagens falsas em nome da {operadora}}. Dúvidas: {canal} ou {encarregadoEmail}."

## 14. Rascunho 10 — Perguntas ao advogado

| # | Pergunta | Proposta atual |
|---|---|---|
| Q-01 | Versix (CNPJ do fundador) e Lider (MEI) são agentes de pequeno porte (Res. CD/ANPD 2/2022 [VALIDAR])? Rastreamento contínuo de ~3.000 veículos é tratamento de alto risco (larga escala, vigilância) e tira os benefícios? | Nomear encarregado mesmo assim; RIPD simplificado a partir da §3 |
| Q-02 | Papéis: Versix operadora no serviço e controladora na indicação; operadora e Versix na indicação são controladoras conjuntas ou independentes? | §2 |
| Q-03 | Termo de ciência do bloqueio como aceite contratual (não base de consentimento) é adequado? A revogação pode tornar o bloqueio indisponível? | §3 T12; §10 |
| Q-04 | Marco Civil art. 15 [VALIDAR]: quem é o provedor de aplicação obrigado (Versix, que publica o app; operadora; ambas)? IP + porta + data/hora UTC por 6 meses atende o Decreto 8.771/2016 [VALIDAR]? | Versix controladora do `access_log` |
| Q-05 | Auditoria de 5 anos com base no CDC art. 27 [VALIDAR]: base legal (exercício regular de direitos)? A Versix pode reter a auditoria após o término para defesa própria? | §3 T4; §6.5 |
| Q-06 | Transferências internacionais (Res. CD/ANPD 19/2024 [VALIDAR]): mecanismo por fornecedor da §7.2; backup cifrado com chave só da Versix é transferência? | Cláusulas-padrão onde o fornecedor aceitar |
| Q-07 | Teto de 12 mensalidades é válido entre empresas? Operadora MEI pode ser tratada como consumidora (finalismo mitigado [VALIDAR])? Exclusão de lucros cessantes? Foro na sede da Versix ou arbitragem? | §6.4 |
| Q-08 | Responsabilidade por acidente após corte em movimento ≤ 40 km/h: como se distribui entre Versix, operadora, instalador e quem acionou (CDC art. 14 [VALIDAR])? O termo de ciência reduz o risco? Vale contratar seguro de responsabilidade civil? | §6.2–§6.4; §10 |
| Q-09 | Termos de uso ao cliente final: a Versix entra na cadeia de fornecimento do CDC? Que cláusulas evitar como abusivas (CDC art. 51 [VALIDAR])? | §8 |
| Q-10 | Contratos atuais da Lider com clientes preveem bloqueio por inadimplência? Confirmar vedação (CDC art. 42; Código Penal art. 345 [VALIDAR]) | INV-09 |
| Q-11 | Matriz da §12 está correta? Quais autoridades obtêm dados cadastrais sem ordem e com qual fundamento (Lei 12.850/2013 art. 15; CPP art. 13-A [VALIDAR])? Avisar o titular? Risco iminente à vida sem ordem (LGPD art. 7º, VII [VALIDAR])? | §12 |
| Q-12 | Prazo de 60 dias para hold de preservação sem ordem judicial, por analogia ao Marco Civil art. 15, §2º [VALIDAR]? | §12 passo 3 |
| Q-13 | Comunicação de incidente em 3 dias úteis (Res. CD/ANPD 15/2024 [VALIDAR]); prazo em dobro para agente de pequeno porte [VALIDAR]? Vazamento de localização é "risco ou dano relevante"? Aviso da Versix em 24 h é adequado? | §13 |
| Q-14 | DEC-15: posições por 12 meses e anonimização 12 meses após o encerramento, com tombstone que mantém registros financeiros e de auditoria por 5 anos | [04 §9.2](../spec/04-dominio-e-dados.md) |
| Q-15 | Lider como MEI: receita estimada de ~R$ 143.640 a R$ 215.640/ano (300 veículos × R$ 39,90 a R$ 59,90 × 12, se o ticket for por veículo [PREMISSA]) passa do teto do MEI (R$ 81.000/ano [VALIDAR])? Efeito no contrato e na nota fiscal (MEI dispensado para pessoa física [VALIDAR]) | Lider consulta contador antes do contrato |
| Q-16 | Versix: CNAE 6203-1/00 cobre o SaaS; receita de indicação exige CNAE de intermediação (ex.: 7490-1/04 [VALIDAR])? NFS-e sobre o valor recebido por split? | DEC-14 |
| Q-17 | Assinatura eletrônica simples do termo do piloto e aceite por clique no app têm prova suficiente (Lei 14.063/2020 [VALIDAR]) com `audit_log`, `text_version` e SHA-256 do texto? | §5.1; §10 |
| Q-18 | Titularidade do código escrito por agentes de IA (Lei 9.609/1998; Lei 9.610/1998 [VALIDAR]); cessão de direitos de freelancers; depósito do código em custódia para continuidade | §6.1 |
| Q-19 | Não aliciamento de clientes da operadora por 12 meses após o término é válido? Conflito com SVA nacional no app da operadora? | §6.1 |
| Q-20 | Envio de SMS pela API emnify e uso de chips M2M pela plataforma caracterizam serviço de telecomunicações ou serviço de valor adicionado (Lei 9.472/1997 art. 61 [VALIDAR])? | ADR-011 |
| Q-21 | Contrato Lider × SmartGPS (DEC-10): aviso prévio, fidelidade, exportação do histórico e quem é controlador do histórico no tracker-net | [11 §8](../spec/11-onboarding-e-migracao.md) |
| Q-22 | Conta Apple individual (DEC-03) com o fundador como vendedor de um app que exibe marcas de operadoras: requisitos de política de privacidade, exclusão de conta e marca de terceiros nas lojas [VALIDAR] | §9.3 |

## 15. Referências normativas citadas (todas [VALIDAR])

| Norma | Uso neste anexo |
|---|---|
| Lei 13.709/2018 (LGPD): arts. 5º, 7º, 8º, 9º, 10, 18, 19, 20, 37, 38, 39, 42 | Papéis, bases legais, direitos, registro, RIPD, operador [VALIDAR] |
| Res. CD/ANPD 2/2022 (agentes de pequeno porte) | Q-01, Q-13 [VALIDAR] |
| Res. CD/ANPD 15/2024 (comunicação de incidente) | §7.1 item 7, §13 [VALIDAR] |
| Res. CD/ANPD 18/2024 (encarregado) | §4 [VALIDAR] |
| Res. CD/ANPD 19/2024 (transferência internacional) | §7.1 item 6, Q-06 [VALIDAR] |
| Lei 12.965/2014 (Marco Civil): arts. 10, 15 e 22; Decreto 8.771/2016 art. 11 | Registros de acesso, autoridades [VALIDAR] |
| Lei 8.078/1990 (CDC): arts. 6º, 7º, 14, 25, 27, 42, 51, 101 | Informação, solidariedade, prescrição de 5 anos, cobrança, cláusulas, foro [VALIDAR] |
| Código Penal arts. 147-A e 345; Código Civil art. 393 | Perseguição, exercício arbitrário, força maior [VALIDAR] |
| Lei 12.850/2013 art. 15; CPP art. 13-A | Dados cadastrais sem ordem [VALIDAR] |
| Lei 14.063/2020 | Assinatura eletrônica [VALIDAR] |
| Lei 9.609/1998 e Lei 9.610/1998 | Software e direito autoral [VALIDAR] |
| Lei 9.472/1997 art. 61 | Serviço de valor adicionado em telecom [VALIDAR] |
| LC 123/2006 (MEI) | Teto e nota fiscal da Lider [VALIDAR] |
| Apple App Review Guidelines 5.1.1(v); política de dados do Google Play | Exclusão de conta, declarações das lojas [VALIDAR] |
