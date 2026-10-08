# Anexo A — Comercial

> **Resumo:** Material de venda da TrackSys para operadoras de rastreamento. Reúne o pitch de 1 página, a tabela de preços, a paridade com o tracker-net e os diferenciais, a conta para a operadora e a proposta à Lider como parceira de design. Também traz perfil de cliente, funil e metas, roteiro de venda e onboarding, objeções com resposta e os materiais a produzir. Todos os números vêm de [01](../spec/01-visao-e-negocio.md); o que é hipótese está marcado.
> **Fases:** F1, F2  ·  **Status:** Aprovado para execução
> **Muda em relação à v1.1:**
> - A v1.1 não tinha material comercial. Este anexo transforma o modelo de receita de [01 §5](../spec/01-visao-e-negocio.md) em discurso, proposta e funil.
> - A Lider entra como parceira de design, com adesão condicionada ao G1.
> - A receita de indicações aparece só em exemplos marcados como ilustrativos. Não há número de mercado inventado.

## 1. Pitch de 1 página

> **TrackSys — o app de rastreamento que o seu cliente abre todo dia, com a marca da sua operadora.**
> Para operadoras de rastreamento que atendem pessoa física (carro e moto) e querem um app melhor sem pagar mais por veículo.
>
> 1. **Mesmo preço por veículo, adesão menor.** R$ 3,90 por veículo ativo por mês. Adesão única de R$ 2.500 a R$ 3.000.
> 2. **App com a sua marca.** Nome, logo e cores da operadora. O mapa ao vivo diz se a posição é atual, se o veículo está sem sinal ou se a posição é antiga. Histórico, alertas no celular e bloqueio confirmado por biometria.
> 3. **Proteção à noite sem depender do plantonista.** Modo vigilância para o carro estacionado. Alerta de alimentação cortada e botão de pânico (conforme o modelo do rastreador). Alerta de comunicação perdida em movimento, indício de bloqueador de sinal. Meta: 95% dos alertas no celular do cliente em até 30 s.
> 4. **Cliente paga pelo app.** A TrackSys conversa com o seu Asaas: a fatura e o PIX copia-e-cola aparecem dentro do app.
> 5. **Receita nova.** O cliente chama guincho, assistência e oficinas pelo app. A sua operadora recebe parte de cada indicação convertida.
> 6. **Troca sem visita ao veículo.** Migração por SMS em lotes de até 20 rastreadores. Se o rastreador não aparecer em 10 min, ele volta sozinho ao servidor antigo.
> 7. **Compromisso por escrito.** Disponibilidade de 99,5% ao mês, medida e publicada. Crédito de 10% ou 25% da mensalidade se falharmos. Plano de contingência por SMS para a sua central.
>
> **Operadora piloto:** Lider Rastreamento (160 clientes PF, ~300 veículos).
> **Próximo passo:** conversa de 30 min e demonstração ao vivo com um rastreador de verdade.

**Regras de comunicação comercial** (valem para pitch, site, proposta e conversa):
1. Nunca prometer recuperação de veículo. A plataforma transmite, registra e alerta ([01 §9](../spec/01-visao-e-negocio.md)).
2. Nunca prometer socorro automático, nem por colisão. O F3 oferece "alerta de possível impacto" só com hardware compatível ([12 §17](../spec/12-cobranca-e-svas.md)).
3. Bloqueio só é oferecido para rastreador homologado e instalação registrada. Na Lider, isso vale depois do G-CMD (meta: 2ª quinzena de novembro de 2026).
4. Recurso de fase futura sempre vem com a fase: "no F2" ou "a partir de jan/2027".
5. Números de mercado (tamanho do setor, taxa de furto nacional, preço da concorrência além do tracker-net) não entram no material.

## 2. Preços

| Item | Valor | Inclui / regra | Desde |
|---|---|---|---|
| Assinatura base | R$ 3,90 por veículo ativo/mês | Veículo ativo = vínculo primário em pelo menos 1 dia do mês (REQ-NEG-002). Inclui app com a marca, console, alertas, bloqueio, integração Asaas, atendimento com WhatsApp e suporte à operadora | F1 (nov/2026) |
| Adesão | R$ 2.500 a R$ 3.000, única | Operadora e marca configuradas; importação da planilha; ligação com o Asaas; treinamento da central e do plantonista; migração em ondas assistida; 30 dias de acompanhamento | Assinatura do contrato (Lider: §5) |
| Plano superior | R$ 5,90 por veículo ativo/mês (proposta) | Candidatos: gestão de custos, lembrete de revisões, histórico acima de 90 dias, cercas múltiplas, mais links simultâneos. Conteúdo e preço em DEC-09 | F2 |
| App dedicado na loja (opção B) | Setup + anuidade, a definir | App com o nome da operadora, publicado na conta de desenvolvedor dela. Preço junto com DEC-09 (proposta de prazo em [01 §5](../spec/01-visao-e-negocio.md): 31/03/2027) | F2 |
| Indicações (SVA) | Sem custo para a operadora | A operadora recebe parte: 20–30% em parceiro nacional (DEC-05) e 50% proposto em parceiro local ([12 §14](../spec/12-cobranca-e-svas.md)) | F1 (guincho), F2 |
| Créditos de SLA | 10% da mensalidade abaixo de 99,5%; 25% abaixo de 99,0% | Manutenção anunciada com 48 h fica fora da conta | 01/12/2026 |

**Como a mensalidade é paga.** Em cada cobrança paga pelo cliente final no Asaas da operadora, R$ 3,90 por veículo vão por split para a carteira da Versix. No dia 1 de cada mês, a TrackSys fecha a conta do mês anterior. Se o split não cobriu tudo, a Versix fatura a diferença com vencimento no dia 10. Sobra vira crédito no mês seguinte ([12 §10](../spec/12-cobranca-e-svas.md)). Veículo de cliente inadimplente segue a DEC-06.

**Fora do preço:** tarifas do Asaas (pagas pela operadora, na conta dela), chip e SMS (conta emnify/Meta Telecom da operadora) [VALIDAR — DEC-01], rastreador e instalação.

## 3. Paridade com o tracker-net e diferenciais

Paridade mínima pedida pela Lider para migrar. A coluna do tracker-net reflete o relato da Lider; a Versix não avaliou o produto diretamente.

| Necessidade | No tracker-net (relato da Lider) | Na TrackSys | Fase |
|---|---|---|---|
| Mapa ao vivo (app) | Tem | Tem, com idade da posição e estados "ao vivo", "sem sinal" e "posição antiga" | F0 |
| Histórico (app) | Tem | 90 dias na hora; até 12 meses por relatório | F0 |
| Bloqueio (app e central) | Tem | Por tipo de instalação, com biometria no app, segundo fator na central e confirmação do rastreador | F1, após G-CMD |
| Alertas (app) | Tem | Ignição, vigilância, alimentação cortada, pânico, sem comunicação, comunicação perdida em movimento; cerca e velocidade | F0, F1 |
| Carteira (central) | Tem | Clientes, veículos, rastreadores, chips (ICCID), instalações, usuários | F0 mínimo, F1 completo |
| Cobranças (central) | Tem | Integração com o Asaas da operadora, lista de inadimplência, PIX no app | F1 |
| Suporte (central) | Tem | Registro de atendimento com contexto do veículo + WhatsApp | F1 |

| Diferencial | O que a operadora ganha | Fase |
|---|---|---|
| App superior | Marca da operadora, estados honestos, push de alta prioridade, "Navegar até o veículo", "Falar com a central" | F0 |
| PIX no app | Menos atrito para o cliente pagar; fatura e PIX vêm do Asaas da operadora | F1 |
| Receita de indicações | Guincho no F1; assistência 24h e oficinas no F2; parte de cada conversão | F1, F2 |
| Modo vigilância | Cerca de 150 m em volta do carro estacionado; alerta com ignição ou movimento | F0 |
| Modo ocorrência | Furto ou roubo: visão da equipe de busca, link temporário para a polícia, BO, linha do tempo, pacote de evidências | F1 |
| Contingência | Runbook de 1 página: o plantonista localiza e desbloqueia por SMS se a plataforma cair ([Anexo C](C-operacional.md)) | F1 |
| Disponibilidade com crédito | 99,5% ao mês, página de status pública, créditos de 10% e 25% | F1 |
| Migração por SMS | Ondas de até 20 rastreadores, volta automática em 10 min, sem custo de campo | F0, F1 |
| Agente de suporte por IA | Respostas 24h às dúvidas da central, só com os dados da própria operadora | F2 |

## 4. A conta para a operadora

| Veículos ativos | Mensalidade TrackSys | Em 12 meses |
|---|---|---|
| 100 | R$ 390,00 | R$ 4.680,00 |
| 300 (Lider, estimativa) | R$ 1.170,00 | R$ 14.040,00 |
| 1.000 | R$ 3.900,00 | R$ 46.800,00 |

- **Peso no ticket do cliente final:** R$ 3,90 / R$ 59,90 = 6,5% e R$ 3,90 / R$ 39,90 = 9,8%.
- **Comparação honesta com o tracker-net:** a mensalidade por veículo é a mesma. Para uma operadora nova, a adesão fica R$ 500 a R$ 1.000 abaixo dos R$ 3.500 cobrados da Lider. A troca se paga por app, PIX, indicações e operação, não por desconto na mensalidade.
- **Plano superior (F2, DEC-09):** custa R$ 2,00 a mais por veículo. Faz sentido para a operadora que vender um plano premium ao cliente final por mais do que isso.

**Receita nova com indicações — EXEMPLOS ILUSTRATIVOS, NÃO SÃO PREVISÃO.** Ainda não existe valor contratado com parceiros. Fórmula: receita da operadora por mês = conversões por mês × valor pago pelo parceiro por conversão × parte da operadora.

| Exemplo ilustrativo | Conversões/mês | Valor por conversão (hipotético) | Parte da operadora | Receita da operadora/mês |
|---|---|---|---|---|
| A | 2 | R$ 20,00 | 50% (local) | R$ 20,00 |
| B | 5 | R$ 30,00 | 50% (local) | R$ 75,00 |
| C | 10 | R$ 50,00 | 25% (nacional) | R$ 125,00 |

O volume real aparece no relatório mensal de indicações desde o F1 ([12 §15.4](../spec/12-cobranca-e-svas.md)). Só depois de 3 meses de relatório o material comercial pode citar números de indicação, e só os da própria operadora, com autorização.

## 5. Proposta para a Lider (parceira de design)

**Contexto.** O F0 (out/2026) é gratuito: períodos anteriores a 2026-11 não geram tarifa (REQ-NEG-002). Datas: G0 em 31/10/2026 (5–10 veículos), G-CMD na 2ª quinzena de novembro e G1 em 31/12/2026 (base migrada, 30 dias de SLO ≥ 99,5%, contrato e DPA revisados).

| Opção | Adesão | Mensalidade | Contrapartida da Lider | Efeito para a Versix |
|---|---|---|---|---|
| **A — Adesão após o G1 (recomendada)** | R$ 2.500, faturados só depois do G1, em 3 parcelas mensais (R$ 833,33, R$ 833,33 e R$ 833,34). Sem G1, nada é cobrado | R$ 3,90 por veículo ativo desde 11/2026 | Feedback quinzenal de 30 min; case público com números autorizados; referência para 3 operadoras; voluntários e veículos do Piloto Zero | Caixa da adesão só a partir de jan/2027 |
| B — Adesão zero com fidelidade | R$ 0 | Igual | Tudo da opção A + fidelidade de 12 meses; saída antecipada paga R$ 2.500 × meses restantes / 12 | Perde a adesão se a Lider cumprir os 12 meses |
| C — Padrão | R$ 2.500 na assinatura | Igual | Nenhuma | Caixa imediato; menor alinhamento |

A opção A é a [DECISÃO DO FUNDADOR PENDENTE] registrada em [01 §5](../spec/01-visao-e-negocio.md): adesão faturada só após o G1, em troca do caso de referência.

**O que a Lider recebe além do produto:** canal direto com o fundador, prioridade no backlog de paridade e nome no case.

**O que a Versix precisa da Lider (com data):**

| Item | Para quê | Até |
|---|---|---|
| Planilha exportada do tracker-net | Contagem real de veículos e importação | 13/10/2026 |
| J16 para bancada + senha SMS | Spike e homologação (DEC-02) | 13/10/2026 |
| Contrato com a SmartGPS revisado (DEC-10) | Aviso prévio, fidelidade e exportação antes de anunciar a troca | 17/10/2026 |
| 5–10 veículos voluntários e termo de participação assinado | Piloto Zero e G0 | 27/10/2026 |
| Chave Asaas (sandbox, depois produção) e contato do guincho parceiro | Cobrança e 1º SVA no F1 | 01/11/2026 |
| Plantonista disponível para o ensaio | Contingência ensaiada no G1 | 16–31/12/2026 |
| Acordo sobre a tarifa de veículo de cliente inadimplente (DEC-06, decisão do fundador negociada com a Lider) | Contrato | 31/10/2026 |

## 6. Perfil de cliente e funil

**Operadora no perfil:**
1. Atende pessoa física (carro e moto), com foco anti-furto.
2. Tem de 100 a 1.000 veículos [PREMISSA].
3. Usa rastreadores reconfiguráveis por SMS e com protocolo suportado pelo Traccar: J16/GT06 primeiro, outros após homologação no F2.
4. Cobra por boleto ou PIX. O Asaas é o caminho mais curto; sem Asaas, a mensalidade vai por fatura.
5. Está na região do fundador, para permitir visita [PREMISSA].

**Fora do perfil até out/2027:** frotas com telemetria avançada (F3), vídeo, leitura de rede CAN, integração com ERP.

**Meta:** 12 operadoras ativas até 31/10/2027, cerca de 1 nova por mês ([01 §8](../spec/01-visao-e-negocio.md)). Operadora ativa = contrato assinado, ≥ 1 veículo ativo no mês e tarifa do mês anterior liquidada.

| Data | Operadoras ativas | Veículos ativos | MRR |
|---|---|---|---|
| 31/12/2026 (G1) | 1 | 300 | R$ 1.170 |
| 31/03/2027 | 4 | 1.000 | R$ 3.900 |
| 30/06/2027 (G2: 6+) | 7 | 1.750 | R$ 6.825 |
| 30/09/2027 | 10 | 2.500 | R$ 9.750 |
| 31/10/2027 | 12 | 3.000 | R$ 11.700 |

**Funil mensal para fechar 1 contrato por mês** [PREMISSA — hipóteses de planejamento, não dados de mercado; revisar no fim de cada trimestre com os números reais]:

| Etapa | Definição | Meta/mês |
|---|---|---|
| Contato | Operadora no perfil contactada | 15 |
| Diagnóstico | Conversa de 30 min feita | 8 |
| Demonstração | Demonstração ao vivo feita | 5 |
| Proposta | Proposta enviada | 3 |
| Contrato | Contrato assinado | 1 |

**Canais a testar** [PREMISSA]:
- indicação da Lider;
- Meta Telecom, que administra chips de várias operadoras;
- distribuidores e instaladores de J16;
- busca local por "rastreamento veicular" + cidade;
- grupos e eventos do setor.

Cada contato vai para o CRM com origem, etapa, data e motivo de perda.

## 7. Roteiro de venda

| Etapa | Duração | Objetivo | Saída |
|---|---|---|---|
| 1. Primeiro contato | 5 min | Marcar o diagnóstico | Data marcada |
| 2. Diagnóstico | 30 min | Preencher a ficha de qualificação (abaixo) | Ficha completa; segue ou descarta |
| 3. Demonstração | 45 min | Mostrar o produto com a marca da operadora | Interesse confirmado e pedido de proposta |
| 4. Proposta | Enviada em ≤ 48 h | Preço, adesão, cronograma de 14 dias, SLA | Proposta de 1 página + minuta de contrato |
| 5. Piloto (opcional) | ≤ 14 dias | 5 veículos migrados por SMS, sem custo [PREMISSA] | Seguir ou não |
| 6. Contrato | — | Contrato SaaS + DPA + termo de ciência do bloqueio ([Anexo B](B-juridico.md)) | Assinatura e adesão |
| 7. Onboarding | ≤ 14 dias até o 1º veículo real | §8 | 1º veículo real |
| 8. Acompanhamento | 30 dias | Ondas de migração, ajustes, treinamento | Base migrada; case |

**Ficha de qualificação:**
- clientes e veículos (PF/PJ, carro/moto);
- plataforma atual, contrato (aviso prévio, fidelidade, exportação) e preço pago;
- modelos e firmwares de rastreador; chip, operadora M2M e APN; reconfiguração por SMS (sim/não);
- tipo de bloqueio instalado (bomba, ignição, arranque);
- meio de cobrança e conta Asaas (sim/não);
- atendimento: horário, plantão noturno, equipe de busca;
- parceiros atuais (guincho, assistência);
- três maiores dores, decisor e prazo.

**Demonstração em 45 min:**
1. App com a marca da operadora (operadora de demonstração).
2. Mapa ao vivo com estados honestos.
3. Ativar o modo vigilância e ligar a ignição do rastreador de bancada: o push chega durante a reunião.
4. Histórico do dia.
5. Bloqueio e desbloqueio na bancada, com a lâmpada do relé.
6. Console: carteira, fila de alertas, atendimento.
7. Fatura e PIX no app.
8. Botão de guincho e relatório de indicações.
9. Página de status e runbook de contingência.
10. Perguntas.

## 8. Onboarding em até 14 dias

Meta: ≤ 14 dias do contrato ao 1º veículo real (REQ-NEG-005), com alvo no 7º dia. Processo detalhado em [11](../spec/11-onboarding-e-migracao.md).

| Dia | Entrega | Responsável |
|---|---|---|
| D0 | Contrato e DPA assinados; adesão conforme a proposta | Fundador e operadora |
| D1 | Operadora criada; marca (nome, logo, cores, WhatsApp da central); equipe convidada | Fundador |
| D2–D3 | Planilha da plataforma atual importada, com prévia e correção de erros | Operadora e fundador |
| D3 | Conta Asaas ligada; clientes casados por CPF/CNPJ | `operator_admin` |
| D4 | Modelos de rastreador conferidos com os perfis homologados; senha SMS e APN confirmadas | Fundador |
| D5 | Treinamento da central (2 h) e do plantonista (runbook de contingência, 30 min) [PREMISSA] | Fundador |
| D6–D7 | 1ª onda: 5 veículos por SMS; 1º veículo real transmitindo | Operadora |
| D8–D14 | Ondas de até 20 veículos com volta automática | Operadora |

Bloqueio só para modelo homologado e vínculo com ponto de corte registrado (INV-10).

## 9. Objeções e respostas

| Objeção | Resposta | Prova |
|---|---|---|
| "O preço é o mesmo. Por que trocar?" | Adesão menor, app muito melhor com a sua marca, PIX no app e receita de indicações. A mensalidade não é o argumento | Demonstração; §3 |
| "Migrar dá trabalho e posso perder cliente." | A troca é por SMS, sem visita, em lotes de até 20, com volta automática em 10 min. Começa com 5 veículos | Rollback testado no G0 da Lider |
| "E se a plataforma cair?" | Meta de 99,5%/mês com crédito, VM reserva, página de status e runbook para o plantonista localizar e desbloquear por SMS | Status page; [Anexo C](C-operacional.md) |
| "É uma empresa de uma pessoa só." | Sim: fundador com agentes de IA, arquitetura com poucas peças, backup fora do servidor e restauração testada. Os dados são da operadora e podem ser exportados a qualquer momento | Contrato ([Anexo B](B-juridico.md)); [13](../spec/13-infra-e-operacao.md) |
| "Meu rastreador não é J16." | Homologamos por modelo. J16/GT06 primeiro; outros modelos entram no F2, depois de teste em bancada | Matriz de perfis homologados |
| "Bloqueio em movimento é perigoso." | Política por tipo de instalação, teto de 40 km/h configurável para baixo, ignição só parado, biometria, auditoria e termo de ciência do cliente | [06](../spec/06-comandos-e-bloqueio.md) |
| "Vou perder o histórico do tracker-net." | O histórico não migra. A TrackSys começa um histórico novo no dia da troca. O acesso de leitura ao antigo se negocia com a plataforma atual | Cláusula a negociar (modelo DEC-10) |
| "E a LGPD? Vocês vão ver os dados dos meus clientes?" | A operadora é controladora e a Versix processadora, com DPA. Cada operadora é isolada no banco. A Versix só acessa com concessão temporária, somente leitura e auditada, criada pela própria operadora | [08](../spec/08-identidade-e-seguranca.md) |
| "Tenho contrato com a plataforma atual." | Rodamos o piloto de 5 veículos em paralelo. A troca em massa só acontece depois de conferir aviso prévio e fidelidade | Cronograma da Lider |
| "Não uso o Asaas." | A TrackSys funciona sem Asaas. Nesse caso, a mensalidade vai por fatura mensal e o PIX no app não fica disponível | [12 §10](../spec/12-cobranca-e-svas.md) |
| "Meus clientes vão achar que vendo os dados deles." | Indicação só com consentimento por parceiro, aviso claro de "indicação remunerada" e opção de chamar sem registrar | [12 §16](../spec/12-cobranca-e-svas.md) |
| "Não emito nota fiscal." | A NFS-e é opcional por operadora e, quando ligada, é emitida pelo próprio Asaas | [12 §11](../spec/12-cobranca-e-svas.md) |

## 10. Materiais necessários

| Material | Uso | Responsável | Prazo [PREMISSA] |
|---|---|---|---|
| Marca e domínio registrados | Base de todo material | Fundador (DEC-04) | 17/10/2026 |
| Página de status pública e relatório mensal de disponibilidade | Prova do SLA | Fundador | 01/12/2026 |
| Pitch de 1 página em PDF (a partir da §1) | Primeiro contato | Fundador | 31/12/2026 |
| Operadora de demonstração com marca fictícia ("Operadora Demo") + rastreador de bancada | Demonstração ao vivo | Fundador | 31/12/2026 |
| Minuta de proposta, contrato SaaS, DPA e termo de ciência do bloqueio | Fechamento | Fundador + advogado (DEC-08) | G1 |
| FAQ da operadora e runbook do plantonista | Onboarding | Fundador ([Anexo C](C-operacional.md)) | G1 |
| Vídeo de 2 min do app (vigilância, PIX, bloqueio) | Prospecção | Fundador | 31/01/2027 |
| Deck de 8 slides | Reunião | Fundador | 31/01/2027 |
| Calculadora em planilha (mensalidade, peso no ticket, exemplo de indicações) | Proposta | Fundador | 31/01/2027 |
| Ficha de qualificação e CRM | Funil | Fundador | 31/01/2027 |
| Case Lider (texto, números autorizados, depoimento) | Prova social | Fundador + Lider | 28/02/2027 |
