# 01 — Visão e negócio

> **Resumo:** A Versix Solutions vende a TrackSys, plataforma SaaS de rastreamento veicular, para operadoras de rastreamento brasileiras que atendem pessoa física (B2B2C: Versix → operadora → cliente final). A operadora paga R$ 3,90 por veículo ativo por mês mais uma adesão única. A Versix também recebe por indicações de serviços de valor agregado (SVA). A operadora piloto é a Lider Rastreamento (160 clientes PF, ~300 veículos), que hoje usa o tracker-net. Este capítulo fixa atores, proposta de valor, receita, economia unitária, metas de 12 meses e os requisitos REQ-NEG-001 a REQ-NEG-005.
> **Fases:** F0, F1, F2, F3  ·  **Status:** Aprovado para execução
> **Muda em relação à v1.1:**
> - O público deixa de ser "empresa de rastreamento" genérica: é a operadora PF anti-furto, com a Lider como piloto nomeado.
> - A hierarquia passa de 1 nível (operadora → clientes) para 3 níveis (Versix → operadora → cliente).
> - A cobrança entra no escopo (Asaas com split), porque é paridade com o tracker-net.
> - Entram preço, custos, pontos de equilíbrio e metas com data.
> - SVA por indicação vira linha de receita. Gestão de frota vai para F3.

## 1. Problema e oportunidade

### 1.1 Problema da operadora

1. **Plataforma cara para o porte.** O tracker-net cobra R$ 3,90/veículo/mês e cobrou R$ 3.500 de adesão da Lider.
2. **App modesto.** Para o cliente final, o app é o produto. Um app fraco reduz o valor percebido do serviço de R$ 39,90–59,90/mês.
3. **Receita presa ao ticket.** A operadora não tem fonte de receita além da mensalidade.
4. **Noite reativa.** A central tem 1 plantonista que só atende quando o cliente liga. À noite, o caminho crítico é rastreador → plataforma → push no celular do cliente.
5. **Falha real é cobertura.** Em 4 anos, a Lider teve 5 furtos e nenhum incidente de bloqueio, exceto falta de cobertura do chip. O produto precisa ser honesto sobre sinal e idade da posição.

### 1.2 Oportunidade

- O mesmo R$ 3,90, adesão de R$ 2.500–3.000 e um app muito superior com a marca da operadora.
- Receita nova para a operadora: indicações de SVA divididas com ela ([12 — Cobrança e SVAs](12-cobranca-e-svas.md)).
- Custo de infraestrutura quase zero (Oracle Always Free, ADR-005) e equipe solo com agentes de IA. A margem é alta já com poucos milhares de veículos.
- Migração sem visita ao veículo: o J16 troca de servidor por SMS ([11 — Onboarding e migração](11-onboarding-e-migracao.md)).

## 2. Quem é quem

| Entidade | Papel | Fatos que importam para o produto |
|---|---|---|
| **Versix Solutions** | Plataforma, dona da TrackSys | Nome fantasia no CNPJ do fundador (CNAEs 6203-1/00 e 6201-5/01; DEC-14). Fundador solo + agentes de IA. Não atende cliente final. |
| **TrackSys** | Produto | Console web da operadora (React), app "TrackSys" com marca dinâmica da operadora (Flutter, ADR-007), processos `api` e `worker` (ADR-001). |
| **Lider Rastreamento** | Operadora piloto | MEI. 160 clientes, 100% PF, carro ou moto, 1 a 3 veículos cada (~300 veículos; faixa 160–480 até a planilha exportada). Ticket R$ 39,90–59,90/mês. Cobra pelo Asaas (boleto + PIX). Atende por WhatsApp Business. Central + equipe de busca 24h (1 plantonista à noite). Indica um guincho parceiro com desconto. |
| **SmartGPS (tracker-net)** | Plataforma atual da Lider | Rastreadores apontados para o servidor da SmartGPS. Contrato Lider × SmartGPS em DEC-10. |
| **Meta Telecom / emnify** | Chip M2M multi-operadora | Várias APNs. SMS e diagnóstico de chip por API (DEC-01). |
| **Traccar** | Borda de protocolos | Open source. Decodifica o J16 e envia comandos (ADR-003). |
| **Parceiros** | Guincho, assistência 24h, oficinas | Pagam a indicação à Versix ([12](12-cobranca-e-svas.md)). |

**Risco fiscal da Lider [VALIDAR — contador da Lider].** O faturamento anual estimado vai de R$ 76.608 (160 × R$ 39,90 × 12) a R$ 215.640 (300 × R$ 59,90 × 12). A maior parte da faixa passa do limite anual do MEI (R$ 81.000). Se a Lider mudar de regime, pode passar a emitir NFS-e. O Asaas emite NFS-e ([12](12-cobranca-e-svas.md)).

## 3. Atores e personas

### 3.1 Atores

| Ator | Papel no sistema | Quem é | Objetivo | Dor hoje |
|---|---|---|---|---|
| Fundador Versix | `platform_admin` (fora de `membership`; dados de operadora só via `platform_support_grant`) | Dono, revisor dos agentes, vendedor, última linha de operação | Vender 12 operadoras e operar 3.000 veículos sozinho | Tempo de revisão e acionamento noturno são o gargalo |
| Administrador da operadora | `operator_admin` | Dono ou gerente da Lider | Carteira, cobrança, marca, política de bloqueio | Plataforma cara, app fraco, receita só do ticket |
| Atendente / plantonista | `operator_agent` | Central diurna; 1 plantonista noturno reativo | Localizar veículo, atender, registrar atendimento, bloquear/desbloquear com motivo | Painel sem contexto; sem plano B quando a plataforma cai |
| Instalador | `installer` | Técnico de campo | Registrar instalação (IMEI, ICCID, `cut_point`) e testar comunicação | Ponto de corte não registrado; cadastro por WhatsApp |
| Equipe de busca | `search_team` | Equipe 24h de recuperação | Seguir o veículo em ocorrência pelo celular | Posição sem idade visível; prints trocados por WhatsApp |
| Titular do cliente | `tenant_owner` | Pessoa física contratante | Ver o veículo, receber alerta, bloquear, pagar | App modesto; não sabe se a posição é atual |
| Membro do cliente | `tenant_member` | Familiar ou condutor convidado | Ver o veículo e receber alertas com login próprio | Usa a senha do titular |
| Parceiro | Sem `membership` (portal do parceiro no F2) | Guincho, assistência 24h, oficina | Receber chamado com localização e placa | Cliente liga sem localização precisa |
| Visitante de link | Sem `membership`; token de `share_link` | Familiar, polícia | Ver a localização por tempo limitado | Recebe print desatualizado |
| Agentes de IA | Codificação (Claude Code, Codex, Antigravity, OpenCode); SRE; suporte às operadoras. `actor_type = 'ai_agent'` no `audit_log` | Executores sob guardrails (ADR-010, INV-11) | Implementar e operar dentro de escopo fechado | Contexto ambíguo gera retrabalho; sem limite claro há risco de ação indevida |

### 3.2 Proposta de valor por ator

| Ator | O que a TrackSys entrega | Fase | Como medimos |
|---|---|---|---|
| Fundador | Poucas peças (ADR-002), deploy/backup/failover automáticos, agentes com cardápio fechado, tarefas com aceite congelado | F0–F2 | ≤ 216 min ruins/mês ([13](13-infra-e-operacao.md)); ≤ 2 acionamentos noturnos/mês [PREMISSA] |
| `operator_admin` | Mesmo R$ 3,90, adesão R$ 500–1.000 menor, app com a marca dela, PIX no app, receita de SVA, onboarding ≤ 14 dias | F1–F2 | Veículos migrados; receita de indicação da operadora (REQ-NEG-004) |
| `operator_agent` | Tela do veículo com estado, alertas, comandos e atendimentos; runbook de contingência de 1 página | F0–F1 | Contingência ensaiada no G1 ([02](02-escopo-e-fases.md)) |
| `installer` | Registro de instalação com `cut_point` obrigatório para bloqueio | F1 | 100% dos vínculos com bloqueio têm `cut_point` (INV-10) |
| `search_team` | Modo ocorrência, visão ao vivo com idade da posição, compartilhamento com polícia | F1 | Idade da posição sempre exibida ([10](10-apps-e-ux.md)) |
| `tenant_owner` | Mapa ao vivo com estados honestos, histórico, alertas push, modo vigilância, bloqueio com step-up, PIX, "Falar com a central" | F0–F1 | Alerta p95 ≤ 30 s ([07](07-alertas-e-tempo-real.md)) |
| `tenant_member` | Convite com acesso próprio aos veículos autorizados | F1 | Nenhum compartilhamento de senha necessário |
| Parceiro | Chamado com localização, placa e contato; portal com confirmação de conversão | F1 (guincho), F2 | Indicações convertidas/mês |
| Visitante de link | Link temporário, revogável, só com o escopo declarado | F1 | Link revogado deixa de responder ([08](08-identidade-e-seguranca.md)) |
| Agentes de IA | `AGENTS.md`, cartões de tarefa, testes de aceite congelados, ações de runbook pré-aprovadas | F0+ | Tarefa entregue sem pergunta ao fundador ([14](14-qualidade-e-processo-ia.md)) |

## 4. Por que a Lider troca o tracker-net

### 4.1 Dores declaradas

1. **Preço:** R$ 3,90/veículo/mês + R$ 3.500 de adesão.
2. **App modesto, com poucos recursos.**

O preço por veículo fica igual. O argumento é: adesão menor, app muito melhor e receita nova.

### 4.2 Paridade mínima para migrar

| Necessidade (hoje no tracker-net) | Onde | Fase TrackSys | Capítulo |
|---|---|---|---|
| Mapa ao vivo | App | F0 | [10](10-apps-e-ux.md) |
| Histórico | App | F0 | [10](10-apps-e-ux.md) |
| Alertas | App | F0 (ignição, vigilância, corte de alimentação, SOS, sem comunicação); F1 (cerca, velocidade) | [07](07-alertas-e-tempo-real.md) |
| Bloqueio | App + central | F1, liberado só após G-CMD | [06](06-comandos-e-bloqueio.md) |
| Carteira | Central | F0 (cadastro mínimo); F1 (completa, com chips e instalações) | [04](04-dominio-e-dados.md), [10](10-apps-e-ux.md) |
| Cobranças | Central | F1 (Asaas) | [12](12-cobranca-e-svas.md) |
| Suporte | Central | F1 (atendimento com contexto + WhatsApp) | [10](10-apps-e-ux.md) |

### 4.3 Diferenciais

| Diferencial | Valor para a Lider | Fase |
|---|---|---|
| Adesão de R$ 2.500–3.000 contra R$ 3.500 | Economia de R$ 500–1.000 na entrada | Contrato |
| App com a marca da Lider e estados honestos (online, sem sinal, posição antiga) | Valor percebido do ticket | F0 |
| Modo vigilância, corte de alimentação, comunicação perdida em movimento (heurística de jammer) | Anti-furto ativo à noite, sem depender do plantonista | F0 |
| Modo ocorrência, visão da equipe de busca, pacote de evidências | Recuperação mais rápida, resposta à polícia | F1 |
| PIX copia-e-cola e QR no app | Menos atrito para pagar | F1 |
| Receita de SVA (guincho já existe; assistência, revisões e custos no F2) | Receita nova por cliente | F1, F2 |
| Migração por SMS em ondas, com rollback | Troca sem custo de campo | F0, F1 |
| SLO de 99,5%/mês medido, com créditos de 10% e 25% | Garantia contratual | F1 |
| Agente de suporte por IA para a central | Resposta 24h às dúvidas da operadora | F2 |

### 4.4 Condições da troca

1. **Contrato com a SmartGPS** (aviso prévio, fidelidade, exportação, acesso ao histórico): DEC-10, dono Lider, até 17/10/2026. Sem DEC-10, só o piloto de 5–10 veículos migra.
2. **Bloqueio é paridade.** Veículo com bloqueio instalado só migra em onda após o G-CMD (REQ-NEG-015 em [02](02-escopo-e-fases.md)).
3. **O histórico do tracker-net não migra.** O histórico TrackSys começa no dia da migração. O acesso de leitura ao histórico antigo é negociado em DEC-10.

## 5. Modelo de receita

| Fonte | Quem paga → recebe | Valor | Liquidação | Fase | Status |
|---|---|---|---|---|---|
| Assinatura | Operadora → Versix | R$ 3,90 por veículo ativo/mês (390 centavos) | Split Asaas em cada pagamento do cliente final; fallback: fatura mensal (`platform_fee.settled_via` = `'split'` ou `'invoice'`) | F1 | Canônico |
| Adesão | Operadora → Versix | R$ 2.500 a R$ 3.000, única | Fatura na assinatura do contrato | Contrato | Canônico; Lider em [Anexo A](../anexos/A-comercial.md) |
| Plano superior | Operadora → Versix | R$ 5,90 por veículo ativo/mês (proposta) | Igual à assinatura | F2 | DEC-09 |
| Indicação de SVA | Parceiro → Versix | Valor por indicação convertida, no contrato com o parceiro | Cobrança mensal ao parceiro a partir do relatório | F1 (guincho), F2 | Parceiro nacional: participação da operadora de 20–30% (DEC-05). Parceiro local: ver abaixo |
| App dedicado na loja (opção B) | Operadora → Versix | Setup + anuidade | Fatura | F2 | Ver abaixo |

**Regras de receita.**

1. A Versix nunca cobra o cliente final. A operadora cobra, na própria conta Asaas ([12](12-cobranca-e-svas.md)).
2. Todo valor é armazenado em centavos inteiros de BRL (INV-12).
3. Inadimplência do cliente final: a tarifa da Versix segue DEC-06 (prazo 31/10/2026). Inadimplência nunca dispara bloqueio (INV-09).
4. Créditos de SLA: 10% da mensalidade se a disponibilidade do mês ficar abaixo de 99,5%; 25% se ficar abaixo de 99,0% ([13](13-infra-e-operacao.md)).
5. Indicação remunerada é informada ao cliente final e exige consentimento por parceiro e finalidade ([08](08-identidade-e-seguranca.md), [Anexo B](../anexos/B-juridico.md)).
6. Parceiro local fechado pela operadora: o ganho é dividido. [NOVA DECISÃO PROPOSTA: em indicação de parceiro local, Versix fica com 20–30% e a operadora com 70–80%, espelhando DEC-05.]
7. App dedicado (opção B, ADR-007): [NOVA DECISÃO PROPOSTA: preço de setup e anuidade do app dedicado, definido até 31/03/2027, antes da oferta no F2.]
8. Lider como parceira de design: [NOVA DECISÃO PROPOSTA: adesão da Lider faturada só após o G1, como contrapartida por ser caso de referência.]

**Candidatos ao plano superior (DEC-09).** Gestão de custos PF, lembrete de revisões, histórico acima de 90 dias sob demanda, cercas múltiplas, mais links de compartilhamento simultâneos. A lista final sai em DEC-09.

## 6. Economia unitária

### 6.1 Receita com a Lider

| Cenário | Veículos | Receita mensal | Receita anual |
|---|---|---|---|
| Mínimo (1 veículo por cliente) | 160 | R$ 624,00 | R$ 7.488,00 |
| Estimativa | 300 | R$ 1.170,00 | R$ 14.040,00 |
| Máximo (3 veículos por cliente) | 480 | R$ 1.872,00 | R$ 22.464,00 |

Mais a adesão única de R$ 2.500–3.000. A plataforma pesa 6,5% (R$ 3,90 / R$ 59,90) a 9,8% (R$ 3,90 / R$ 39,90) do ticket do cliente final. A contagem real vem da planilha exportada do tracker-net ([11](11-onboarding-e-migracao.md)).

### 6.2 Custo fixo no F0–F1 (câmbio premissa US$ 1 = R$ 5,50)

| Item | Referência | R$/mês |
|---|---|---|
| Ferramentas de IA (Claude Code, Codex e outras) | US$ 200–600/mês | 1.100,00–3.300,00 |
| Oracle Cloud, 2 VMs Ampere A1 Always Free | R$ 0 | 0,00 |
| Apple Developer | US$ 99/ano | 45,38 |
| Domínio .com.br | ~R$ 40/ano | 3,33 |
| Google Play | US$ 25 único (R$ 137,50) | — (não recorrente) |
| Uptime Kuma, UptimeRobot, Sentry, Grafana Cloud, Cloudflare R2, Resend/Brevo, FCM | Open source ou free tier | 0,00 |
| Pushover | Licença única por plataforma [VALIDAR] | ~0,00 |
| Reserva variável: SMS, CI macOS para build iOS, imprevistos [PREMISSA] | — | 350,00–650,00 |
| **Total** | | **~1.500,00–4.000,00** |

### 6.3 Custo variável por veículo

| Item | Custo | Regra |
|---|---|---|
| Infraestrutura (VMs, disco, backup) | R$ 0 dentro do Always Free | Meta ≤ R$ 0,39/veículo/mês (REQ-NEG-003) |
| Mapas (MapLibre + OpenFreeMap; fallback PMTiles auto-hospedado, DEC-11) | R$ 0 | Proibido provedor com custo por carga de mapa sem teto |
| Push (FCM) | R$ 0 | Alertas sempre por push |
| SMS (desbloqueio de fallback, migração) | Por envio [VALIDAR — DEC-01] | SMS de onda de migração é custo único, fora do indicador recorrente |
| WhatsApp | R$ 0 com deep link (F0/F1); Cloud API cobra por mensagem no F2 [VALIDAR] | Bibliotecas não oficiais são proibidas |
| Geocodificação | Adiada para o F2, com cache | — |
| Tarifa do Asaas por boleto/PIX | Paga pela operadora, na conta dela | Custo do split [VALIDAR] |

### 6.4 Mês 12 (out/2027)

| Linha | Valor mensal |
|---|---|
| MRR (3.000 × R$ 3,90) | R$ 11.700,00 |
| Imposto sobre a receita: Simples Nacional faixa 1, 6% (Anexo III) ou 15,5% (Anexo V) [VALIDAR — DEC-14] | R$ 702,00 a R$ 1.813,50 |
| Custo fixo | R$ 1.500,00 a R$ 4.000,00 |
| Teto de infraestrutura (10% da receita) | até R$ 1.170,00 |
| **Sobra para pró-labore e reinvestimento** | **R$ 4.716,50 a R$ 9.498,00** |

Adesões no ano: ~11 operadoras novas × R$ 2.500–3.000 ≈ R$ 27.500–33.000 (caixa não recorrente; a adesão da Lider segue o [Anexo A](../anexos/A-comercial.md)). Sensibilidade: cada 10% da base no plano superior soma R$ 600/mês no mês 12 (3.000 × 10% × R$ 2,00).

### 6.5 Pontos de equilíbrio

Fórmula (receita bruta, sem imposto, infraestrutura paga = 0): `veículos = ⌈(custo fixo + pró-labore) / R$ 3,90⌉`.

| Alvo | Custo fixo R$ 1.500 | Custo fixo R$ 4.000 |
|---|---|---|
| Só custos | 385 veículos | 1.026 veículos |
| Só custos, com imposto (6% no custo mínimo; 15,5% no máximo) | 410 veículos | 1.214 veículos |
| Custos + pró-labore R$ 5.000 [PREMISSA] | 1.667 veículos | 2.308 veículos |
| Custos + pró-labore R$ 10.000 [PREMISSA] | 2.949 veículos | 3.590 veículos |
| Custos + pró-labore R$ 15.000 [PREMISSA] | 4.231 veículos | 4.872 veículos |

Conclusões:

1. A Lider sozinha (R$ 1.170/mês) não cobre o custo fixo mínimo. O equilíbrio de custos exige 385–1.026 veículos, ou 2 a 4 operadoras do porte da Lider.
2. Um pró-labore de R$ 10.000 exige 2.949–3.590 veículos. A meta do mês 12 fica no limite. SVA e plano superior pagam o que vier além disso.
3. Um time de 3 pessoas (R$ 50–70 mil/mês) exigiria 12.821–17.949 veículos, fora do horizonte de 12 meses. A operação solo com IA é condição do plano.
4. As adesões (~R$ 27.500–33.000 no ano) cobrem o déficit até o equilíbrio.

### 6.6 Meta de infraestrutura

Custo de infraestrutura e serviços de terceiros recorrentes ≤ 10% da receita de assinatura: R$ 0,39/veículo/mês, ou até R$ 1.170/mês no mês 12. Os gatilhos objetivos para gastar mais (fila dedicada, Redis, compressão colunar, múltiplos Traccar) estão no ADR-002 e em [03 — Arquitetura](03-arquitetura.md).

## 7. Operação solo e consequências

| Restrição | Consequência no produto | Onde |
|---|---|---|
| Uma pessoa revisa todo o código | Revisão por risco (N0, N1, N2); testes de aceite congelados em `tests/acceptance/T-NNN/`; tarefas do tamanho de uma sessão de agente | [14](14-qualidade-e-processo-ia.md) |
| Uma pessoa não vigia 24h | VM standby, sondas externas, paging Pushover que repete até reconhecer, agente SRE fora da VM com cardápio fechado, runbook do plantonista | [13](13-infra-e-operacao.md), [Anexo C](../anexos/C-operacional.md), ADR-010 |
| Uma pessoa não atende 12 operadoras | A Versix não atende cliente final. Agente de suporte por IA às operadoras no F2, com o escopo de quem pergunta | INV-07, INV-11, [08](08-identidade-e-seguranca.md) |
| Pouco tempo para construir | Integrar em vez de construir: Asaas, emnify, FCM, WhatsApp por deep link | ADR-011 |
| Pouco dinheiro | Postgres único como banco, fila e barramento; Oracle Always Free; free tiers | ADR-002, ADR-005 |
| Pouca capacidade de manutenção | Monólito modular; contrato primeiro com clientes TS e Dart gerados | ADR-001, ADR-008 |
| Acionamento noturno tem custo alto | Só acorda o fundador o que a automação não resolve. 1 h fora do ar pesa o mesmo que alerta 5 min atrasado ("minuto ruim") | [13](13-infra-e-operacao.md) |

## 8. Metas de 12 meses

**Operadora ativa** (definição usada aqui e no G2): operadora com contrato assinado, ≥ 1 veículo ativo no mês (REQ-NEG-002) e tarifa do mês anterior liquidada (split recebido ou fatura paga).

| Meta | Valor | Data | Como medir |
|---|---|---|---|
| Operadoras ativas | 12 | 31/10/2027 | Definição acima |
| Veículos ativos | 3.000 | 31/10/2027 | REQ-NEG-002 |
| MRR | R$ 11.700 | out/2027 | REQ-NEG-004 |
| Adesões no ano | R$ 27.500–33.000 | nov/2026–out/2027 | REQ-NEG-004 |
| Disponibilidade | 99,5%/mês (≤ 216 min ruins em 30 dias) | Medida desde 01/12/2026 | [13](13-infra-e-operacao.md) |
| Latência de alerta | p95 ≤ 30 s | F1 | [07](07-alertas-e-tempo-real.md) |
| Infraestrutura | ≤ 10% da receita de assinatura | Todo mês | REQ-NEG-003 |
| Onboarding de operadora | ≤ 14 dias do contrato ao 1º veículo real | F2 | REQ-NEG-005 |
| SVA | Receita de indicação > R$ 0 em mai/2027 e jun/2027 | G2 | REQ-NEG-004 |
| Base Lider | Migrada | 31/12/2026 (G1) | [02](02-escopo-e-fases.md) |

**Trajetória intermediária [PREMISSA]** (média de 250 veículos por operadora, ~1 operadora nova por mês):

| Data | Operadoras ativas | Veículos ativos | MRR |
|---|---|---|---|
| 31/12/2026 (G1) | 1 | 300 | R$ 1.170 |
| 31/03/2027 | 4 | 1.000 | R$ 3.900 |
| 30/06/2027 (G2) | 7 | 1.750 | R$ 6.825 |
| 30/09/2027 | 10 | 2.500 | R$ 9.750 |
| 31/10/2027 | 12 | 3.000 | R$ 11.700 |

## 9. O que não somos

1. **Não somos gestão de frota até o F3.** Manutenção de frota, condução, ociosidade, viagens e BLE ficam para depois de out/2027 ([02](02-escopo-e-fases.md)).
2. **Não fazemos sub-revenda multinível.** A hierarquia é fixa em 3 níveis: plataforma → operadora → cliente. Uma operadora não revende para outra.
3. **Não somos central de monitoramento.** Quem atende o cliente final é a operadora. A Versix atende a operadora.
4. **Não somos seguradora nem assistência.** Indicamos parceiros. Nunca prometemos socorro automático, nem por colisão.
5. **Não cobramos o cliente final.** A cobrança roda na conta Asaas da operadora.
6. **Não fabricamos rastreador nem vendemos chip.** Homologamos modelos por `capability_profile` e integramos a emnify.
7. **Não garantimos recuperação de veículo.** A plataforma transmite, registra e alerta. A operadora define a política de bloqueio. O instalador define a ligação.
8. **Não usamos inadimplência como alavanca física.** Comercial não aciona físico (INV-09).

## 10. Requisitos de negócio

### REQ-NEG-001 — Preço configurável por operadora
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N0 · **Invariantes:** INV-12
**Regra.** O sistema DEVE guardar, por operadora e por plano (`'base'`, `'superior'`), o preço por veículo ativo e a adesão em centavos inteiros, com data de início de vigência no 1º dia de um mês civil (estrutura `operator_price`: `operator_id`, `plan`, `price_cents`, `setup_fee_cents`, `valid_from`; tabela a incorporar em [04](04-dominio-e-dados.md)). O padrão do plano `'base'` é 390 centavos. O valor de um período DEVE usar o preço vigente no 1º dia daquele período. Alterar preço NÃO DEVE recalcular `platform_fee` de período já fechado. Valor com casas decimais ou em ponto flutuante DEVE ser rejeitado na fronteira.
**Aceite.** CT-NEG-001 — Dado a Lider com `price_cents = 390` vigente desde 01/11/2026 e `price_cents = 350` vigente desde 01/02/2027, Quando a tarifa de 2027-01 e a de 2027-02 são calculadas com 300 veículos ativos cada, Então `platform_fee.amount_cents` de 2027-01 = 117000 e o de 2027-02 = 105000, e reprocessar 2027-01 depois da mudança mantém 117000.
CT-NEG-002 — Dado uma requisição de cadastro de preço com `priceCents = 3.9`, Quando a API valida, Então responde 422 e nada é gravado.

### REQ-NEG-002 — Veículo ativo para faturamento
**Fase:** F1 · **Prioridade:** P0 · **Risco:** N0 · **Invariantes:** INV-06, INV-09, INV-12
**Regra.** Veículo ativo no período `YYYY-MM` DEVE ser o veículo com ao menos um `device_assignment` com `is_primary = true` cuja vigência `[valid_from, valid_to)` intercepta o mês civil em `America/Sao_Paulo` (UTC−03:00). A contagem é por `vehicle_id`: veículo com dois rastreadores conta 1. Não há rateio por dias: interceptar o mês por qualquer intervalo conta o mês inteiro. Veículo de cliente `'suspended_commercial'` DEVE ser contado à parte (`active_vehicles_suspended`); se entra no valor cobrado segue DEC-06. Períodos anteriores a 2026-11 não geram tarifa (piloto F0 gratuito) [PREMISSA]. A regra de cálculo da `platform_fee` está em [12](12-cobranca-e-svas.md).
**Aceite.** CT-NEG-003 — Dado V1 com vínculo primário de 10/11/2026 a 20/11/2026, V2 com um rastreador primário e um secundário durante todo o mês, e V3 com vínculo primário encerrado em 31/10/2026 23:00 BRT (01/11/2026 02:00 UTC), Quando a contagem de 2026-11 roda, Então `active_vehicles = 2` (V1 e V2) e V3 não é contado.

### REQ-NEG-003 — Custo de infraestrutura por veículo
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** INV-12
**Regra.** O `platform_admin` DEVE registrar, por mês, cada custo recorrente de infraestrutura e serviço de terceiro (Oracle, Cloudflare R2, Grafana, Sentry, e-mail, SMS recorrente, mapas, WhatsApp) em centavos, com categoria e fornecedor (tabela de plataforma `platform_cost`, a incorporar em [04](04-dominio-e-dados.md)). O indicador mensal DEVE ser `infra_por_veiculo_cents = round(custo_total_cents / veículos_ativos)` e `razao = custo_total_cents / receita_assinatura_cents`. Meta: `razao ≤ 10%`. Com ≥ 1.000 veículos ativos e `razao > 10%` em 2 meses consecutivos, o worker DEVE alertar o fundador. SMS de onda de migração DEVE ser registrado como custo único (categoria `'migration'`), fora do indicador. A arquitetura NÃO DEVE adotar serviço com custo por requisição sem teto configurado.
**Aceite.** CT-NEG-004 — Dado 2027-10 com 3.000 veículos ativos, receita de assinatura de R$ 11.700,00 e custos de R$ 180,00 (SMS recorrente), Quando o indicador é calculado, Então `infra_por_veiculo_cents = 6`, `razao = 1,5%` e o status é "dentro da meta".
CT-NEG-005 — Dado 2027-09 com `razao = 10,6%` e 2027-10 com custos de R$ 1.300,00 para receita de R$ 11.700,00 (`razao = 11,1%`), ambos com 3.000 veículos, Quando o indicador de 2027-10 é calculado, Então o fundador recebe 1 alerta "infra acima de 10% por 2 meses".

### REQ-NEG-004 — Relatório mensal de unidade econômica
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-07, INV-12
**Regra.** O worker DEVE gerar, no dia 1 de cada mês às 09:00 UTC (06:00 BRT), o relatório do mês anterior com uma linha por operadora e uma linha consolidada: veículos ativos (total e suspensos), receita de assinatura e forma de liquidação, adesões recebidas, indicações (criadas, convertidas, receita bruta, parte da operadora, parte da Versix), custo de infraestrutura rateado por veículos ativos, custo de SMS atribuído à operadora e margem de contribuição. O job DEVE ler cada operadora em transação própria com o contexto RLS dela (`app.scope = 'operator'`) e gravar só agregados (contagens e centavos), sem dado pessoal. A saída é um CSV `unit-economics-YYYY-MM.csv` em bucket privado, enviado por e-mail ao fundador. Reexecutar para o mesmo período DEVE sobrescrever o arquivo sem duplicar linhas. O `operator_admin` vê só a própria tarifa e as próprias indicações no console ([12](12-cobranca-e-svas.md)); custos da Versix não aparecem para a operadora.
**Aceite.** CT-NEG-006 — Dado 2027-03 com a Lider (300 veículos, R$ 1.170,00 via split), a operadora B (200 veículos, R$ 780,00 via fatura), 4 indicações convertidas de R$ 50,00 cada com regra de 25% para a operadora e custo de infraestrutura de R$ 100,00, Quando o job roda em 01/04/2027 09:00 UTC e roda de novo 5 min depois, Então o CSV tem 3 linhas (Lider, B, consolidado), receita de assinatura consolidada de R$ 1.950,00, indicações com R$ 50,00 para operadoras e R$ 150,00 para a Versix, infraestrutura rateada de R$ 60,00 (Lider) e R$ 40,00 (B), e a 2ª execução não acrescenta linhas.

### REQ-NEG-005 — Tempo de onboarding de operadora
**Fase:** F2 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** —
**Regra.** O sistema DEVE registrar a data de assinatura do contrato da operadora (`operator.contract_signed_on`, coluna a incorporar em [04](04-dominio-e-dados.md)) e calcular `onboarding_days` = data (BRT) do 1º `position` com `valid = true` da operadora − `contract_signed_on`, em dias corridos. Rastreador de bancada DEVE ficar em operadora de teste, nunca na operadora real. Meta: `onboarding_days ≤ 14`. O console de plataforma DEVE listar operadoras em onboarding com dias decorridos e alertar o fundador no 10º dia sem 1º fix válido. O processo de onboarding está em [11](11-onboarding-e-migracao.md).
**Aceite.** CT-NEG-007 — Dado a operadora C com contrato em 05/03/2027 e 1º fix válido em 18/03/2027 14:00 BRT, Quando o indicador é calculado, Então `onboarding_days = 13` e o status é "dentro da meta"; com 1º fix em 20/03/2027, Então `onboarding_days = 15` e o status é "fora da meta".
CT-NEG-008 — Dado a operadora D com contrato em 05/03/2027 e nenhum fix válido, Quando o job diário roda em 15/03/2027, Então o fundador recebe 1 alerta "operadora D: 10 dias sem 1º veículo real" e o job de 16/03/2027 não repete o alerta.
