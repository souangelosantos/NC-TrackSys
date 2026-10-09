# 15 — Decisões, riscos e premissas

> **Resumo:** Registro vivo do que falta decidir (DEC-01 a DEC-15), dos riscos do plano e das premissas que sustentam números e prazos. Cada DEC tem dono, prazo, contexto, opções, recomendação, impacto do atraso e plano B, para que nenhuma tarefa espere uma decisão sem padrão seguro. Cada risco tem dono e gatilho objetivo de ação. Cada premissa diz como e até quando será validada e o que muda se for falsa.
> **Fases:** F0, F1, F2  ·  **Status:** Aprovado para execução
> **Muda em relação à v1.1:**
> - As DEC da v1.1 (stack, IdP, retenção, mapas, público) foram resolvidas pela entrevista e pelos ADR; as 15 DEC atuais tratam de hardware, contas, contrato, preço e jurídico, todas com data.
> - Todo risco ganha dono e gatilho mensurável; o plano B de cada DEC fica escrito antes do prazo.
> - Premissas numéricas (intervalo do J16, ~300 veículos, câmbio) viram tabela com validação, prazo e efeito se falsas.
> - As propostas de decisão espalhadas pelos capítulos ficam consolidadas num só lugar (§5).

## 1. Como usar este registro

1. DEC aberta não para trabalho independente. A tarefa usa o padrão seguro do plano B e isola a decisão atrás de configuração ou interface. Parâmetro crítico de produção nunca recebe valor presumido (lição da v1.1, p. 41).
2. Resolver uma DEC = um PR que muda a linha da §2 (status `Resolvida`, data, resultado) e, no mesmo PR, os capítulos afetados (REQ-QLD-020).
3. Revisão semanal, segunda-feira 09:00 BRT, ≤ 30 min [PREMISSA]: DEC vencidas ou com prazo na semana, gatilhos de risco disparados, premissas a validar. O fundador atualiza status e data neste arquivo. A conferência dos gatilhos fica registrada em `docs/runbooks/revisao-semanal/AAAA-MM-DD.md` (formato na T-019); a issue semanal `risk-review` (`weekly.yml`, segunda 07:47 BRT) serve de lembrete.
4. Decisão nova nasce como `[NOVA DECISÃO PROPOSTA: …]` no capítulo e como linha da §5 no mesmo PR. Só o fundador a promove a DEC, com o próximo número livre.

## 2. Decisões pendentes (DEC)

Situação em 09/10/2026. Dono: fundador, salvo indicação.

| ID | Decisão | Dono | Prazo | Bloqueia | Status |
|---|---|---|---|---|---|
| DEC-01 | Acesso à API emnify via Meta Telecom (SMS + diagnóstico de chip) | Fundador | 13/10/2026 | SMS automático de desbloqueio e ondas automáticas (F1); fallback: SMS manual no portal | Aberta |
| DEC-02 | Capacidades reais do J16 | Fundador | 13/10/2026 (spike S1) | Perfil J16, alertas do F0, migração | Aberta |
| DEC-03 | Conta Apple Developer: organização (D-U-N-S no CNPJ) ou individual | Fundador | 09/10/2026 | TestFlight do F0 | Aberta |
| DEC-04 | Marca e domínio: busca INPI "TrackSys"/"Versix" + registro do domínio | Fundador | 17/10/2026 | Publicação nas lojas (F1) | Aberta |
| DEC-05 | Participação da operadora em indicações de parceiros nacionais (proposta 20–30%) | Fundador | Antes do 1º parceiro nacional (F2) | Contrato de SVA | Aberta |
| DEC-06 | Tarifa Versix para veículo de cliente inadimplente (cobra ou não os R$ 3,90) | Fundador | 31/10/2026 | Contrato Lider | Aberta |
| DEC-07 | Teto de velocidade para corte em movimento (proposta 40 km/h) | Fundador | Antes do G-CMD | Habilitar bloqueio real | Aberta |
| DEC-08 | Contratar revisão jurídica do Anexo B (advogado de tecnologia/LGPD) | Fundador | Antes do G1; piloto usa termo simples | Contrato comercial | Aberta |
| DEC-09 | Preço e conteúdo do plano superior (proposta R$ 5,90) | Fundador | F2 | Plano superior | Aberta |
| DEC-10 | Contrato Lider × SmartGPS (aviso prévio, fidelidade, exportação, acesso ao histórico) | Lider | 17/10/2026 | Migração em massa | Aberta |
| DEC-11 | Mapas: OpenFreeMap ou PMTiles auto-hospedado (critério: disponibilidade medida no piloto) | Fundador | G1 | — | Aberta |
| DEC-12 | Conta Oracle: região, conversão para Pay As You Go, redistribuição 2 × 100 GB para a VM standby | Fundador | 10/10/2026 | Standby (F1) | Aberta |
| DEC-13 | Modelo de IA dos agentes de operação e suporte (padrão `claude-opus-5-5`) | Fundador | F1 (SRE diagnóstico), F2 (suporte) | Agentes | Aberta |
| DEC-14 | Nome fantasia "Versix Solutions" no CNPJ e regime tributário (contador) | Fundador | 31/10/2026 | Contrato, Asaas, Apple | Aberta |
| DEC-15 | Retenção e anonimização após encerramento de cliente (jurídico) | Fundador | Antes do G1 | Política de privacidade | Aberta |

### DEC-01 — API emnify via Meta Telecom
- **Contexto:** os chips da Lider são emnify, administrados pela Meta Telecom. A API permite SMS para o rastreador (desbloqueio de fallback após 2 min, ondas de migração) e diagnóstico (rastreador desligado × sem cobertura × chip suspenso). Custo por SMS [VALIDAR — DEC-01].
- **Padrão de segurança:** bloquear SMS MT P2P no chip; SMS só pela API ou pelo portal emnify, para que ninguém comande o rastreador de um celular comum.
- **Opções:** (a) credencial de API em sub-organização da conta emnify administrada pela Meta Telecom; (b) a Meta Telecom encaminha SMS por API própria; (c) sem API: SMS manual pelo portal.
- **Recomendação:** (a), com permissão mínima (envio de SMS e leitura de status do SIM) e só para os chips da Lider [VALIDAR — granularidade de permissões da emnify].
- **Impacto se atrasar:** ondas e desbloqueio por SMS ficam manuais; ~300 veículos em lotes de 20 = 15 ondas operadas à mão.
- **Plano B:** SMS manual pelo portal com checklist do runbook ([11](11-onboarding-e-migracao.md)); `migration_item` registra o envio manual; diagnóstico de chip fica para o F2.

### DEC-02 — Capacidades reais do J16
- **Contexto:** a base da Lider é quase toda J16. É preciso confirmar protocolo e porta, relé, estado do relé reportado, ignição, alarme de corte de alimentação, SOS, servidor secundário, aceite de domínio e quando o DNS é resolvido, posição por SMS, buffer offline, acelerômetro, intervalos e senha SMS.
- **Senha SMS:** o comando `set_password` por SMS [VALIDAR — DEC-02] troca a senha de fábrica ou da SmartGPS antes do `set_server_domain`.
- **Opções:** é validação, não escolha. Fontes: bancada com Traccar e captura (T-002, roteiro de [05 §15](05-ingestao-e-telemetria.md#15-spike-do-j16-t-002-o-que-capturar)); manual do fabricante; instalador da Lider.
- **Recomendação:** bancada como fonte única de verdade; cada capacidade vira `yes`, `no` ou `unknown` no `capability_profile` (`draft`) com evidência em `packages/testkit/fixtures/j16/`.
- **Impacto se atrasar:** é o primeiro elo do caminho crítico (T-002 → T-005 → T-011 → T-012 → T-014 → G0); cada dia empurra o G0, no limite até 07/11/2026 ([02 §2.4](02-escopo-e-fases.md#24-plano-de-corte)).
- **Plano B:** capacidade não confirmada = `unknown` (INV-03): alerta correspondente desligado, bloqueio indisponível (INV-10), nenhum veículo real migra. Se o Traccar não decodificar o J16, testar outro decodificador do Traccar; se nenhum servir, homologar outro modelo para o piloto.

### DEC-03 — Conta Apple Developer
- **Contexto:** conta de organização exige D-U-N-S do CNPJ, que pode levar dias ou semanas [VALIDAR]; conta individual sai mais rápido, mas mostra o nome do fundador como vendedor. US$ 99/ano em qualquer caso.
- **Opções:** (a) organização já; (b) individual agora e migração para organização depois [VALIDAR — processo de migração da Apple]; (c) individual permanente.
- **Recomendação:** (b): individual até 09/10/2026 para o TestFlight do F0, pedido de D-U-N-S no mesmo dia; organização antes da publicação na App Store (F1), depois da DEC-14.
- **Impacto se atrasar:** G0 só com Android (corte 6 do plano de corte).
- **Plano B:** corte 6; TestFlight no F1.

### DEC-04 — Marca e domínio
- **Contexto:** busca no INPI nas classes 9 e 42 (possivelmente 38 e 45). Os rastreadores apontam por domínio (`gps.`); trocar o domínio depois exige SMS a cada rastreador. Domínio .com.br ~R$ 40/ano.
- **Opções:** (a) TrackSys e `tracksys.com.br`, se livres; (b) nome alternativo se houver colidência; (c) app com a marca Versix.
- **Recomendação:** busca até 14/10/2026; registrar o domínio do nome escolhido e um domínio Versix para `gps.` (proposta de [02](02-escopo-e-fases.md); ver §5); depositar o pedido de marca no INPI [VALIDAR — taxa vigente].
- **Impacto se atrasar:** o 1º SMS de servidor a veículo real (22/10/2026) exige o domínio definitivo de `gps.`; publicação nas lojas atrasa.
- **Plano B:** `gps.` em domínio Versix neutro, registrado já; app no TestFlight com nome provisório.

### DEC-05 — Participação da operadora em indicações nacionais
- **Contexto:** o app tem a marca da operadora. Se só a Versix ganhar com parceiros nacionais, a operadora não promove o SVA (conflito de canal).
- **Opções:** 0%; 20–30%; 50%.
- **Recomendação:** 25% para a operadora em parceiro nacional, revisado após 6 meses de dados. Para parceiro local, unificar as propostas divergentes de [01](01-visao-e-negocio.md) (operadora 70–80%) e [12](12-cobranca-e-svas.md) (50%) numa regra espelho: quem fecha a parceria fica com 75%.
- **Impacto se atrasar:** nenhum parceiro nacional no F2. O guincho local da Lider não depende desta DEC.
- **Plano B:** só parceiros locais.

### DEC-06 — Tarifa de veículo de cliente inadimplente
- **Contexto:** inadimplência nunca bloqueia (INV-09); o veículo segue transmitindo e custando. Com split, a Versix recebe os R$ 3,90 só quando o cliente paga. [12](12-cobranca-e-svas.md) guarda a escolha em `operator_price.suspended_fee_policy` (`charge` ou `waive`).
- **Opções:** (a) `charge`: cobra sempre; (b) `waive`: não cobra enquanto o cliente estiver `suspended_commercial`.
- **Recomendação:** (b) para a Lider: "a Versix recebe quando a operadora recebe" segue a mecânica do split e reforça o pitch de parceira de design. Revisar no G1 com a taxa real de inadimplência.
- **Impacto se atrasar:** contrato da Lider sem a cláusula; 1º fechamento de `platform_fee` (nov/2026) sem regra.
- **Plano B:** o relatório já separa `active_vehicles_suspended` (REQ-NEG-002); a decisão vale retroativamente no 1º fechamento.

### DEC-07 — Teto para corte em movimento
- **Contexto:** a Lider corta a bomba de combustível com o veículo a até 40 km/h; ignição só parado. Com envio a cada 30 s, a velocidade conhecida tem até 60 s (evidência máxima). O risco físico é o motor apagar em movimento.
- **Opções:** 0 km/h (só parado); 20 km/h; 40 km/h (prática da Lider); 40 km/h só com posição sob demanda ou trava no dispositivo, senão 20 km/h. Moto (`vehicle.kind = 'motorcycle'`): teto efetivo 0 (corte só parado ou por IGN_OFF) até decisão explícita aqui.
- **Recomendação:** teto da plataforma 40 km/h; Lider 40 km/h; operadora nova nasce com 0 km/h e só sobe por versão nova de `command_policy` ([06 §3.3](06-comandos-e-bloqueio.md#33-política-da-operadora-command_policy)).
- **Impacto se atrasar:** bloqueio real indisponível (GC-1 do G-CMD).
- **Plano B:** `max_moving_cut_kmh = 0` na Lider até a decisão; `fuel_pump` vira "só parado".

### DEC-08 — Revisão jurídica do Anexo B
- **Contexto:** sem advogado e sem minuta. Faltam contrato SaaS, DPA, termos de uso, política de privacidade, termo de ciência do bloqueio e consentimentos de SVA; o histórico já foi pedido pela polícia. As lojas exigem política de privacidade publicada para app que trata localização.
- **Opções:** (a) advogado de tecnologia/LGPD com escopo fechado (revisão do [Anexo B](../anexos/B-juridico.md)); (b) modelos prontos com revisão parcial; (c) sem revisão.
- **Recomendação:** (a): cotar 2 a 3 profissionais até 15/11/2026, contratar até 30/11/2026, revisão entregue até 20/12/2026 [VALIDAR — honorários].
- **Impacto se atrasar:** G1-4 reprovado; lojas sem política de privacidade revisada.
- **Plano B:** termo simples do piloto prorrogado; nenhuma operadora além da Lider até a revisão.

### DEC-09 — Plano superior
- **Contexto:** R$ 3,90 é paridade. Cada 10% da base no plano superior soma R$ 600/mês no mês 12 ([01 §6.4](01-visao-e-negocio.md#64-mês-12-out2027)).
- **Opções:** R$ 4,90; R$ 5,90; R$ 6,90. Conteúdo candidato: relatório histórico acima de 90 dias sob demanda, compartilhamento sem limite, gestão de custos PF, revisões com oficinas, várias cercas.
- **Recomendação:** R$ 5,90, com conteúdo definido após 3 meses de uso real do F1.
- **Impacto se atrasar:** nenhum no F0 e no F1.
- **Plano B:** só o plano de R$ 3,90.

### DEC-10 — Contrato Lider × SmartGPS (dono: Lider)
- **Contexto:** aviso prévio, fidelidade, direito de exportação e acesso ao histórico de 12 meses, que a polícia já pediu.
- **Opções:** (a) migrar após cumprir o aviso prévio; (b) migrar em paralelo e pagar a sobreposição; (c) negociar a saída.
- **Recomendação:** a Lider lê o contrato até 17/10/2026, não anuncia a troca antes e negocia exportação em CSV de 12 meses ou leitura por 12 meses ([11 §8](11-onboarding-e-migracao.md#8-histórico-do-tracker-net)).
- **Isenção na sobreposição:** [DECISÃO DO FUNDADOR PENDENTE — recomendação: mensalidade isenta por veículo migrado enquanto a Lider pagar o tracker-net pelo mesmo veículo no aviso prévio, por até 60 dias]. Prazo: 31/10/2026. Registro: `adjustment_cents` com motivo `overlap_waiver` ([12 §10.2](12-cobranca-e-svas.md#102-fechamento-mensal-platform_fee)).
- **Impacto se atrasar:** ondas do F1 atrasam; a Lider paga as duas plataformas por mais tempo.
- **Plano B:** só o piloto de até 10 veículos; ondas depois do fim do aviso prévio.

### DEC-11 — Mapas
- **Contexto:** OpenFreeMap é gratuito e sem SLA [VALIDAR]; PMTiles do Brasil auto-hospedado custa disco e banda da VM [VALIDAR — tamanho do arquivo]. Provedor com cobrança por carga sem teto é proibido ([01 §6.3](01-visao-e-negocio.md#63-custo-variável-por-veículo)).
- **Opções:** (a) OpenFreeMap; (b) PMTiles auto-hospedado; (c) provedor pago com teto [VALIDAR — preço].
- **Recomendação:** (a) no piloto, com sonda de tile a cada 5 min; migrar para (b) se a disponibilidade medida ficar < 99,5% em 30 dias ou houver indisponibilidade > 30 min.
- **Impacto se atrasar:** nenhum bloqueio; risco de mapa em branco.
- **Plano B:** (b). Sem tiles, app e console mostram coordenadas, idade da posição e "Navegar até o veículo" (deep link).

### DEC-12 — Conta Oracle
- **Contexto:** recursos Always Free ficam na região de origem, que não muda depois [VALIDAR — DEC-12]; instâncias Always Free ociosas podem ser recuperadas pela Oracle; Pay As You Go mantém a gratuidade dentro dos limites [VALIDAR]. Capacidade A1 pode faltar em regiões concorridas [VALIDAR].
- **Opções:** região de origem São Paulo ou Vinhedo; conta Free ou Pay As You Go.
- **Recomendação:** a região brasileira com capacidade A1 disponível no dia; converter para Pay As You Go com alerta de orçamento no menor valor aceito; 2 VMs de 2 OCPU, 12 GB e 100 GB ([ADR-005](../adr/ADR-005-infra-oracle-always-free.md)).
- **Impacto se atrasar:** a VM primária não nasce (T-003); F1 sem standby.
- **Plano B:** primária na região disponível; F0 sem standby (RTO ≤ 2 h).
- **Contingência de capacidade:** sem A1 em sa-saopaulo-1 ou sa-vinhedo-1 até 11/10/2026 18:00 BRT, a primária nasce numa VM paga de 2–4 vCPU e 8 GB (arm64 ou amd64), com o mesmo `provision.sh`, teto de R$ 150/mês [VALIDAR preço]. Volta à OCI quando houver capacidade; custo em [01 §6.2](01-visao-e-negocio.md#62-custo-fixo-no-f0f1-câmbio-premissa-us-1--r-550).

### DEC-13 — Modelo dos agentes de operação e suporte
- **Contexto:** agentes chamam o modelo por uma interface `AiProvider` agnóstica ([ADR-010](../adr/ADR-010-operacao-assistida-por-ia.md)). Custo cresce por incidente e por pergunta; dados de suporte vão ao fornecedor do modelo (suboperador no DPA).
- **Opções (preço de tabela em 25/09/2026, US$ por milhão de tokens de entrada / saída):** `claude-opus-5-5` 4,00 / 20,00 (padrão); `claude-sonnet-5-5` 2,00 / 10,00; `claude-haiku-4-5` 1,00 / 5,00; modelo de outro fornecedor pela mesma interface.
- **Recomendação:** manter `claude-opus-5-5` nos dois agentes. Troca por custo só depois que o modelo alternativo passar nos mesmos limiares da avaliação de [14 §9.4](14-qualidade-e-processo-ia.md#94-avaliação-dos-agentes-de-ia-adr-010-08-12) (REQ-QLD-017).
- **Impacto se atrasar:** nenhum; o padrão vale.
- **Plano B:** o padrão. Gatilho de reavaliação: custo mensal dos agentes de operação > 10% do custo fixo (ADR-010).

### DEC-14 — Nome fantasia e regime tributário
- **Contexto:** o fundador tem CNPJ com CNAEs 6203-1/00 e 6201-5/01. Simples Nacional: Anexo III (6% na faixa 1) ou V (15,5%) conforme o Fator R [VALIDAR — contador]. D-U-N-S, conta Asaas da Versix (split) e conta Apple de organização dependem do CNPJ final.
- **Opções:** (a) incluir "Versix Solutions" como nome fantasia no CNPJ existente; (b) abrir CNPJ novo; (c) operar sem nome fantasia.
- **Recomendação:** (a): rápida e sem custo de empresa nova; o contador confirma regime e Fator R até 31/10/2026.
- **Impacto se atrasar:** split desligado e fechamento faturando 100% ([12](12-cobranca-e-svas.md)); contrato no nome do fundador.
- **Plano B:** piloto sem cobrança; contrato no CNPJ atual sem nome fantasia.

### DEC-15 — Retenção e anonimização após encerramento
- **Contexto:** proposta de anonimizar 12 meses após o encerramento, salvo legal hold ou obrigação legal. Auditoria de comandos e registros financeiros ficam 5 anos; registros de acesso, 6 meses ([04 §8.1](04-dominio-e-dados.md#81-prazos)).
- **Opções:** 6 meses; 12 meses; 5 anos.
- **Recomendação:** 12 meses para cadastro e posições, igual à retenção praticada pela Lider; validar na revisão jurídica (DEC-08).
- **Impacto se atrasar:** anonimização automática desligada (REQ-DAD-019); dados acumulam.
- **Plano B:** anonimização desligada; eliminação manual a pedido do titular ([08](08-identidade-e-seguranca.md)).

## 3. Riscos

Escalas. Probabilidade em 12 meses: **Baixa** < 10%, **Média** 10–50%, **Alta** > 50%. Impacto: **Médio** = atrasa uma fase ou custa até R$ 5 mil; **Alto** = reprova um gate, perde um cliente ou custa mais de R$ 5 mil; **Crítico** = risco à vida, vazamento de dados ou perda da Lider [PREMISSA].

| ID | Risco | P | I | Mitigação | Dono | Gatilho de ação |
|---|---|---|---|---|---|---|
| R-01 | Atraso do F0 (G0 depois de 31/10/2026) | Alta | Alto | Plano de corte com checkpoints em 13/10, 16/10, 23/10 e 27/10 ([02 §2.4](02-escopo-e-fases.md#24-plano-de-corte)); tarefas de 1–3 sessões; caminho crítico explícito | Fundador | Critério de checkpoint falho, trabalho restante > dias restantes ou semana prevista > 60 h do fundador → aplicar os cortes 0a–0d e depois os demais; < 5 veículos transmitindo em 29/10 12:00 BRT → G0 para o fim da janela de 48 h, no máximo 07/11/2026 |
| R-02 | J16 sem as capacidades esperadas (protocolo, relé reportado, domínio, servidor secundário) | Média | Alto | Spike na S1 (DEC-02); `unknown` por padrão (INV-03); bloqueio só com perfil homologado (INV-10) | Fundador | 13/10/2026 sem captura decodificada → outro decodificador ou outro modelo; J16 sem suporte a domínio → `gps.` por IP reservado (proposta do ADR-005) |
| R-03 | SmartGPS dificulta a migração (senha SMS trocada, exportação negada, cláusula contratual) | Média | Alto | DEC-10; `query_server` e senha conferidos antes de cada onda; cadastro pela planilha já exportada; rollback por SMS testado (G0-8) | Lider | Senha rejeitada em > 2 veículos de uma onda ou recusa formal de exportação → pausar ondas e negociar |
| R-04 | Falta de cobertura do chip (garagem subterrânea, área rural): comando e alerta não chegam | Alta | Médio | Chip multi-operadora; alerta "sem comunicação" e "comunicação perdida em movimento"; UX "aguardando sinal"; desbloqueio com fallback por SMS; diagnóstico emnify (F2) | Fundador | > 5% dos comandos em UNKNOWN em 30 dias ou > 10% dos veículos com lacuna > 30 min por dia → revisar APN e cobertura com a Meta Telecom |
| R-05 | Instabilidade ou recuperação da VM Oracle | Média | Alto | Pay As You Go (DEC-12); standby no F1; WAL-G para Oracle e Cloudflare R2; restore testado (G0-7); rastreadores por domínio | Fundador | Aviso de recuperação da Oracle, 2 incidentes de VM em 30 dias ou > 108 min ruins no mês (50% do orçamento) → executar o plano B da DEC-12 |
| R-06 | Fundador indisponível (fator ônibus = 1) | Média | Crítico | Automação e failover; agente SRE com cardápio fechado; cofre de acesso de emergência e contingência da operadora (§3.1) | Fundador | Até 15/12/2026: cofre montado e ensaiado; page de emergência sem reconhecimento em 30 min → a Lider segue a contingência do [Anexo C](../anexos/C-operacional.md) |
| R-07 | Bloqueio causa acidente | Baixa | Crítico | Política por `cut_point`, teto 40 km/h, evidência `live` ≤ 60 s, ARMED com TTL, step-up, G-CMD (bancada + teste supervisionado), termo de ciência, sem repetição de bloqueio (INV-08/09/10); responsabilidades no [Anexo B](../anexos/B-juridico.md) | Fundador (técnico); Lider (política) | Qualquer relato de reação inesperada → `COMMAND_BLOCK_SCOPE=none` ([06](06-comandos-e-bloqueio.md)) em ≤ 15 min e investigação; CONFIRMED sem atuação na bancada → G-CMD reprovado |
| R-08 | Vazamento entre operadoras ou entre clientes | Baixa | Crítico | INV-07: RLS forçada, FK composta, CAT-01..CAT-07 e ISO em todo PR; revisão N0; agentes de IA no escopo de quem pergunta; 404 fora do escopo | Fundador | Qualquer CAT ou ISO vermelho em `main` → congelar deploy; qualquer relato → incidente de segurança com comunicação no prazo regulamentar ([Anexo B](../anexos/B-juridico.md)) |
| R-09 | Regressão por código gerado por IA | Alta | Alto | Testes congelados, revisão de outro fornecedor, propriedades, mutação, nível de risco por caminho, rollback automático do deploy ([14](14-qualidade-e-processo-ia.md)) | Fundador | 1 escape de INV em produção → merges N0 congelados até o postmortem; 2 escapes N1 em 30 dias → revisar o checklist do revisor |
| R-10 | Mudança de termos de free tier (Oracle, Cloudflare R2, Grafana Cloud, Sentry, UptimeRobot, OpenFreeMap, FCM, GitHub Actions) | Média | Médio | Peças portáveis (Docker Compose, S3 compatível, Alloy); custo por item em [01 §6](01-visao-e-negocio.md#6-economia-unitária); meta de infra ≤ 10% da receita | Fundador | Aviso de mudança → plano de troca em 30 dias; custo de infra > 10% da receita de assinatura no mês |
| R-11 | LGPD/ANPD: incidente, fiscalização ou pedido de titular não atendido | Média | Alto | Encarregado nomeado; DPA; minimização; registros de acesso e auditoria; procedimento de incidente; DEC-08 | Fundador | Incidente com dado pessoal → runbook de incidente; pedido de titular → resposta em 15 dias ([08](08-identidade-e-seguranca.md)) |
| R-12 | Marca indisponível no INPI | Média | Médio | Busca antes de investir na marca (DEC-04); `gps.` em domínio neutro; nome do app trocável até a publicação | Fundador | Colidência nas classes 9 ou 42 → nome alternativo decidido até 17/10/2026 |
| R-13 | Churn da Lider (única operadora no F1) | Baixa | Crítico | Termos de parceira de design ([Anexo A](../anexos/A-comercial.md)); paridade com o tracker-net; app superior; canal direto com o fundador; exportação de dados como garantia contra aprisionamento | Fundador | 2 reclamações formais da Lider no mês, G1 atrasado > 30 dias ou aviso de rescisão → plano de recuperação em 7 dias |
| R-14 | Preço insuficiente: R$ 3,90 não paga a operação e o SVA não decola | Média | Alto | Plano superior (DEC-09); SVA; adesões; custo fixo baixo; equilíbrio de custos em 385–1.026 veículos ([01 §6.5](01-visao-e-negocio.md#65-pontos-de-equilíbrio)) | Fundador | < 1.000 veículos em 31/03/2027 ou receita de indicação = R$ 0 em mai/2027 (G2-3) → revisar preço e planos |
| R-15 | Push no iOS não entregue (permissão negada, modo foco, app encerrado, falha APNs) | Média | Alto | FCM alta prioridade com chave APNs; alerta crítico como Time Sensitive [VALIDAR — entitlement]; app confere permissão; `alert_delivery` com status; iPhone no roteiro do G0 | Fundador | Entrega iOS < 95% em 7 dias [PREMISSA] ou falha do iPhone em G0-3/G0-5 → investigar antes do G0 |
| R-16 | Prazo de 14 dias de teste fechado do Google Play (conta pessoal nova exige 12 testadores por 14 dias) [VALIDAR — regra vigente] | Alta | Médio | Teste fechado iniciado até 27/10/2026 com ≥ 12 testadores do piloto ([02 §2.2](02-escopo-e-fases.md#22-cronograma-semanal)); conta de organização é isenta [VALIDAR] | Fundador | < 12 testadores ativos em 24/10/2026 → recrutar na Lider e entre conhecidos |
| R-17 | Custo de IA cresce (ferramentas de codificação US$ 200–600/mês + API dos agentes) | Média | Médio | Sessões curtas e cartões pequenos ([14 §13](14-qualidade-e-processo-ia.md#13-gestão-de-contexto-dos-agentes)); custo por tarefa medido; DEC-13 | Fundador | > US$ 600/mês (R$ 3.300) por 2 meses seguidos, ou agentes de operação > 10% do custo fixo → cortar ferramentas redundantes e reavaliar modelos |
| R-18 | Prompt injection nos agentes (codificação: issue, PR, fixture, página web; operação e suporte: apelido, ticket) | Média | Alto | Agentes de codificação sem credencial de produção; IA sem poder físico nem financeiro (INV-11); ferramentas só de leitura com RLS; revisor trata instrução em dado como achado bloqueante; ≥ 20 casos de injeção na avaliação | Fundador | 1 injeção bem-sucedida na avaliação → agente desligado até a correção; instrução embutida encontrada em PR → PR bloqueado e origem investigada |
| R-19 | Gargalo de revisão humana: PRs acumulam e o fundador encurta a leitura de N0 | Alta | Alto | Nível de risco por caminho; leitura dirigida em N1; cartões ≤ 400 linhas de produção; métricas de tempo de revisão ([14 §14](14-qualidade-e-processo-ia.md#14--qualidade-e-processo-com-ia)) | Fundador | > 5 PRs N0/N1 esperando revisão por > 2 dias úteis → parar de abrir cartões novos até zerar a fila |
| R-20 | Backup não restaurável descoberto só no incidente | Baixa | Crítico | Restore testado no G0 (G0-7); restore de ensaio mensal com contagens e perda medidas ([13](13-infra-e-operacao.md)); alerta de WAL atrasado | Fundador | Alerta A05 (WAL sem arquivar > 5 min com escrita) ou A14 (último ensaio com sucesso > 35 dias) → incidente prioritário |
| R-21 | Payload bruto da inbox (IMEI e coordenadas) guardado além de 7 dias enquanto a retenção não existe (REQ-ING-018 e REQ-DAD-013 adiados para a T-027, F1) risco aceito; fundador confirma | Alta | Médio | Piloto com ≤ 10 veículos no F0 (volume pequeno); só `tracksys_ingest` lê `ingest_inbox`; backup cifrado (WAL-G com libsodium, [13 §8](13-infra-e-operacao.md#8-backups-e-restore)); `payload_sha256` e identidade preservados, para o expurgo posterior não quebrar o dedupe (INV-01) | Fundador | 1ª onda de migração do F1 sem a T-027 mergeada, ou `pg_total_relation_size('app.ingest_inbox')` > 5 GB [PREMISSA] → a T-027 passa à frente dos cartões do F1 ainda não iniciados |

### 3.1 Fator ônibus = 1: cofre e contingência

1. **Cofre de acesso de emergência:** gerenciador de senhas com acesso de emergência para um contato de confiança nomeado pelo fundador, com espera de 48 h [PREMISSA]. Contém: conta raiz da Oracle Cloud, registrador do domínio, Cloudflare, GitHub (dono da organização), cópia da chave age de produção, conta Asaas da Versix, contas Apple e Google Play, Pushover, emnify/Meta Telecom e os códigos de recuperação de 2FA de cada uma.
2. **Instruções sem segredo** em `docs/runbooks/emergencia.md`: o que funciona sozinho (ingestão, alertas, failover), como publicar aviso na status page, como entregar à operadora a exportação dos dados dela, quem contratar (freelancer técnico pré-identificado com acesso aos runbooks) e como encerrar o serviço de forma ordenada.
3. **Contingência da operadora:** o plantonista da Lider consulta a status page, localiza o veículo por SMS e desbloqueia por SMS pelo portal emnify/Meta Telecom ([Anexo C](../anexos/C-operacional.md)); ensaiada no G1 (G1-6).
4. **Contrato:** cláusula de continuidade e portabilidade dos dados da operadora (proposta para o [Anexo B](../anexos/B-juridico.md)).
5. **Ensaio:** o contato de emergência abre o cofre numa simulação até 15/12/2026 e confirma que encontra cada credencial; resultado registrado em `docs/runbooks/gates/G1.md`.

## 4. Premissas

| ID | Premissa | Origem | Como validar | Prazo | Efeito se falsa |
|---|---|---|---|---|---|
| P-01 | J16 envia a cada 30 s em movimento e 300 s parado; ~8% do tempo em movimento | Entrevista (Q8, não respondida) | Spike de bancada (T-002) e 48 h dos veículos do piloto | 13/10/2026 (bancada); 31/10/2026 (piloto) | Refazer carga e disco ([03 §11](03-arquitetura.md#11-orçamento-de-recursos-vm-de-12-gb-2-ocpu-ampere), [04 §8.6](04-dominio-e-dados.md#86-conta-de-armazenamento-mês-12-3000-veículos)); 10 s em movimento triplica as posições em movimento; parado a 60 s só pesa em `device_state` (compactação) |
| P-02 | Lider tem ~300 veículos (faixa 160–480) | Entrevista (Q2) | Planilha exportada do tracker-net ([11](11-onboarding-e-migracao.md)) | 17/10/2026 | Receita com a Lider de R$ 624 a R$ 1.872/mês; 8 a 24 ondas; base do G1-2 |
| P-03 | Expansão começa pela região do fundador | Entrevista (Q8) | Lista de operadoras-alvo da região com contato feito ([Anexo A §6](../anexos/A-comercial.md#6-perfil-de-cliente-e-funil)) | 30/11/2026 | Onboarding continua remoto (SMS, sem visita); cobertura de chip e venda presencial mudam |
| P-04 | Frotas só depois do mês 12 (out/2027) | Entrevista (Q2, Q8) | Pedidos de frota no funil de operadoras | Revisão trimestral | Antecipar M1/M5 PF e reordenar o F3; F0 e F1 não mudam |
| P-05 | Câmbio US$ 1 = R$ 5,50 | Briefing | Cotação no fechamento de cada mês | Mensal | Cada R$ 0,50 de alta soma R$ 100–300/mês ao custo de IA (US$ 200–600) |
| P-06 | Better Auth atende ao app Flutter via plugin bearer | [ADR-006](../adr/ADR-006-identidade-better-auth-chave-aparelho.md) | T-006: login com `Authorization: Bearer`, sessão de 30 dias deslizante e revogação ≤ 60 s ([08](08-identidade-e-seguranca.md)) | 20/10/2026 | Token opaco próprio (hash SHA-256 em tabela) verificado pelo `api` para o app, mantendo o Better Auth no console; +1 sessão de agente |
| P-07 | OpenFreeMap disponível para o piloto | Stack; DEC-11 | Sonda de tile a cada 5 min | G1 | PMTiles auto-hospedado (plano B da DEC-11) |
| P-08 | J16 aceita domínio e resolve o DNS a cada reconexão | Entrevista (Q10); ADR-005 | Spike: trocar o registro A e observar a reconexão | 13/10/2026 | Failover por IP reservado reatribuído à standby ou por SMS em massa; RTO maior |
| P-09 | A senha SMS dos J16 da Lider é conhecida (padrão ou instalador) | Entrevista (Q7) | `query_params` em 1 J16 da Lider ([11](11-onboarding-e-migracao.md)) | 13/10/2026 | Migração depende de visita ou da SmartGPS (R-03) |
| P-10 | Ferramentas de IA custam US$ 200–600/mês | Briefing | Faturas mensais | Mensal | Custo fixo fora da faixa de R$ 1.500–4.000/mês; R-17 |
| P-11 | Exceções de migração ≤ 5% da base | [02 §4.4](02-escopo-e-fases.md#44-gate-g1-31122026-meta) (G1-2) | `migration_item` das primeiras 3 ondas | 30/11/2026 | Mais visitas técnicas; G1-2 em risco |
| P-12 | Clientes da Lider aceitam trocar de app | Entrevista (Q3, Q5) | ≥ 80% dos titulares do piloto entram no app em 7 dias [PREMISSA] | 07/11/2026 | Reforçar onboarding no app e o roteiro da central antes das ondas |
| P-13 | Clientes usam o bloqueio como trava diária | Entrevista (Q6, hipótese) | Comandos por veículo por semana no 1º mês após o G-CMD | 31/12/2026 | Custo de SMS e UNKNOWN em garagem sobem; revisar UX "aguardando sinal" e orçamento de SMS |
| P-14 | O plantonista executa a contingência por SMS em ≤ 15 min | [02 §4.4](02-escopo-e-fases.md#44-gate-g1-31122026-meta) (G1-6) | Ensaio com cronômetro | 31/12/2026 | Simplificar o runbook do plantonista e repetir o ensaio |
| P-15 | ≥ 70% dos titulares da Lider têm e-mail válido | Entrevista (Q3); [08 §2](08-identidade-e-seguranca.md#2-autenticação-better-auth) | Contagem na planilha exportada do tracker-net | 17/10/2026 | O código de ativação (login por CPF + senha, T-024) vira P0 do F1 |
| P-16 | Entrada (R$ 3,90 por veículo + adesão de R$ 2.500–3.000) é aceitável para operadoras de 100–1.000 veículos | Q3 | Preço e adesão pagos hoje, registrados em 5 diagnósticos (campo obrigatório da ficha do [Anexo A](../anexos/A-comercial.md) §7) | 31/01/2027 | Adesão escalonada por porte (proposta de R$ 1.000 até 150 veículos), via DEC-09 |
| P-17 | Paridade com o tracker-net = os 7 itens de [01 §4.2](01-visao-e-negocio.md#42-paridade-mínima-para-migrar) | Entrevista da Lider | Inventário de 1 h com a Lider operando o tracker-net (`docs/runbooks/onboarding/lider-paridade.md`) | 20/10/2026 | Item semanal sem equivalente vira cartão F1 antes da 1ª onda |

## 5. Propostas de decisão registradas nos capítulos

Toda `[NOVA DECISÃO PROPOSTA: …]` entra aqui no PR que a cria. O fundador aprova, rejeita ou promove a DEC. Na consolidação da v2.0 (08/10/2026):

- as propostas técnicas foram **adotadas como padrão** (o fundador pode reverter por PR);
- as comerciais e jurídicas ficaram **pendentes** (`[DECISÃO DO FUNDADOR PENDENTE]`);
- as de escala ficaram para o F2 (`[ADIADO PARA O F2]`). As escolhas reversíveis que os cartões do F0 fizeram (T-NNN na coluna Seção) também entram aqui, adotadas como padrão até o fundador confirmar ou reverter por PR. A coluna Seção é a única proveniência: o corpo dos capítulos não carrega marcador de adoção.

**Confirmação tácita.** Os itens "Adotada na v2.0 — fundador confirma" valem como confirmados se não houver PR de reversão até 31/10/2026. Exceção: os de risco N0 (comandos, isolamento, cobrança, autenticação, failover) exigem confirmação explícita no PR do cartão que os usa.

| Seção | Proposta | Recomendação | Decidir até | Status |
|---|---|---|---|---|
| [01 §5](01-visao-e-negocio.md#5-modelo-de-receita) | Parceiro local: Versix 20–30%, operadora 70–80% | Unificar com a de [12] e com o Anexo A pela regra espelho da DEC-05 (quem fecha fica com 75%) | Antes do 1º parceiro local pago | **Pendente — fundador** (comercial) |
| [01](01-visao-e-negocio.md) | Preço de setup e anuidade do app dedicado até 31/03/2027 | Aprovar o prazo | 31/03/2027 | **Pendente — fundador** (comercial) |
| [01](01-visao-e-negocio.md) | Adesão da Lider faturada só após o G1 | Aprovar (parceira de design) | 31/10/2026 | **Pendente — fundador** (comercial, até 31/10/2026) |
| [02](02-escopo-e-fases.md) | `gps.` em domínio Versix independente da marca | Aprovar | 17/10/2026 (com DEC-04) | Adotada na v2.0 |
| [03](03-arquitetura.md) | `COMMAND_DISPATCH_ENABLED=false` após failover ou restore até a reconciliação | Aprovar | Antes do standby (15/11/2026) | Adotada na v2.0 |
| [04](04-dominio-e-dados.md) | CAT-07: funções `SECURITY DEFINER` iguais à allowlist, `search_path` fixo, sem PUBLIC | Aprovar | Cartão da T-004 | Adotada na v2.0 |
| [04](04-dominio-e-dados.md) | Identidade de dedupe por 14 dias em vez de 90 | Manter 90 dias (número canônico) até medir o disco (REQ-DAD-024) | Antes de 1.500 veículos ativos | Não adotada (manter 90 dias) |
| [06](06-comandos-e-bloqueio.md) | `COMMAND_BLOCK_SCOPE` = `none` / `pilot:<ids>` / `all`, mudado só por deploy N0 | Aprovar | Antes da bancada | Adotada na v2.0 |
| [06](06-comandos-e-bloqueio.md) | `COMMAND_BENCH_OPERATOR_ID` aceita perfil `draft` só na operadora de bancada | Aprovar | Antes da bancada | Adotada na v2.0 |
| [06](06-comandos-e-bloqueio.md) | Instalador testa bloqueio só em vínculo aberto por ele há ≤ 2 h, até existir OS formal | Aprovar | Antes do G-CMD | Adotada na v2.0 |
| [06](06-comandos-e-bloqueio.md) | `membership.can_command` (padrão `false`), concedido pelo titular | Aprovar | Antes do G-CMD | Adotada na v2.0 |
| [06](06-comandos-e-bloqueio.md) | Termo de ciência de titular sem app registrado pela central com anexo | Aprovar com a revisão jurídica (DEC-08) | Antes do G-CMD | **Pendente — fundador + advogado** (DEC-08) |
| [07](07-alertas-e-tempo-real.md) | `ALERT_DELIVERY_ENABLED=false` em restore e na standby antes da promoção | Aprovar | Antes do 1º ensaio de restore (G0-7) | Adotada na v2.0 |
| [07](07-alertas-e-tempo-real.md) | Conexão SSE de escopo operadora com até 1.000 veículos acima de 400 veículos ativos | Decidir no F2 | F2 | Adiada para o F2 |
| [08](08-identidade-e-seguranca.md) | `membership.vehicle_ids` (NULL = todos os veículos do cliente) | Fora da v2.0: `can_command` vale para todos os veículos do cliente (T-017); o limite de segurança no banco continua sendo o cliente | — | Não adotada (decisão do cartão T-017 vence) |
| [08](08-identidade-e-seguranca.md) | 4º parâmetro `{ readOnly: true }` em `withContext`, compatível com a T-001 | Aprovar | Cartão do acesso de suporte (F1) | Adotada na v2.0 |
| [09](09-api-e-contratos.md) | `block` com rastreador `offline` (> 1.800 s) recusado com 409 `TELEMETRY_STALE` em vez de ARMED | Não adotar: o pedido fica ARMED até a evidência (T-018 vence) | — | Não adotada |
| [10](10-apps-e-ux.md) | `search_team` no navegador usa step-up de console (TOTP + motivo) | Aprovar; alinhar [06 §4.1](06-comandos-e-bloqueio.md#41-papéis) | Antes do G-CMD | Adotada na v2.0 |
| [10](10-apps-e-ux.md) | `br.com.versix.tracksys` como `applicationId` e bundle id | Aprovar | 14/10/2026 (antes do 1º envio às lojas) | Adotada na v2.0 |
| [10](10-apps-e-ux.md) | Subdomínio `meu.` para o portal web do cliente | Decidir no F2 | F2 | Adiada para o F2 |
| [10](10-apps-e-ux.md) | WebAuthn como step-up do portal | Decidir no F2 | F2 | Adiada para o F2 |
| [11](11-onboarding-e-migracao.md) | Nova função `SECURITY DEFINER` para a sonda de quarentena por rastreador | Aprovar com revisão N0 e CAT-07 | Antes do cartão que a usar (F0) | Adotada na v2.0 |
| [12 §14](12-cobranca-e-svas.md#14-parceiros-e-repartição) · [Anexo A](../anexos/A-comercial.md) §2 e §4 | DEC-05 ampliada ao parceiro local: proposta de 75% para quem fecha a parceria (substitui os 50%) | Unificar com [01] e com a recomendação da DEC-05 | Antes do 1º parceiro local pago | **Pendente — fundador** (comercial) |
| [12](12-cobranca-e-svas.md) | Parte da operadora vira crédito no fechamento; saldo > R$ 100,00 pago por PIX até o dia 10 | Aprovar | Antes do 1º fechamento (dez/2026) | **Pendente — fundador** (financeiro) |
| [ADR-005](../adr/ADR-005-infra-oracle-always-free.md) | `gps.` em IP público reservado da OCI, reatribuído à standby no failover | Aprovar se a DEC-12 confirmar a reatribuição entre VMs [VALIDAR] | 10/10/2026 (com DEC-12) | Adotada na v2.0 |
| [ADR-010](../adr/ADR-010-operacao-assistida-por-ia.md) | Entrypoint `infra/scripts/ops-action.sh` para as ações do agente SRE | Aprovar | F1 (agente SRE) | Adotada na v2.0 |
| [13](13-infra-e-operacao.md) | Ações de operação de plataforma (agente SRE, deploy, failover) auditadas em `ops.audit_log`, fora do schema `app` | Aprovar | Antes da T-013 (deploy) | Adotada na v2.0 |
| [13](13-infra-e-operacao.md) | `EXTERNAL_EFFECTS=off` troca FCM, emnify, Asaas, e-mail e comandos do Traccar por adaptadores nulos; obrigatório no restore de ensaio | Aprovar; unificar com `ALERT_DELIVERY_ENABLED` de [07] e `COMMAND_DISPATCH_ENABLED` de [03] numa matriz única | Antes do G0-7 | Adotada na v2.0 |
| [13](13-infra-e-operacao.md) | Deploy automático só de segunda a sexta, 08:00–20:00 BRT; fora disso, `workflow_dispatch` com `force: true` | Aprovar; N0 segue a janela mais estreita de [14 §6](14-qualidade-e-processo-ia.md#6-níveis-de-risco) | Antes da T-013 | Adotada na v2.0 |
| [13](13-infra-e-operacao.md) · T-034 | `tracksys-sre-gateway` em Cloudflare Worker com D1 gratuito como entrada de alertas fora das VMs | Aprovar após confirmar os limites do plano gratuito [VALIDAR] | F1 (01–15/12, agente SRE) | Adotada na v2.0 |
| [14](14-qualidade-e-processo-ia.md) | Cartão T-019 "Guardas de processo no CI" no S1–S2 do F0 | Aprovar | 13/10/2026 | Adotada na v2.0 |
| [14](14-qualidade-e-processo-ia.md) | Todo PR aberto pela conta de máquina `versix-agent`; só o fundador aprova, rotula exceções, cria tags e faz merge | Aprovar | 09/10/2026 (antes do PR da T-001) | Adotada na v2.0 |
| [11](11-onboarding-e-migracao.md) | Colunas `tenant.contact_phone` e `tenant.contact_email` preenchidas pelo importador | Aprovar | Cartão do importador (F1) | Adotada na v2.0 |
| [11](11-onboarding-e-migracao.md) | `MIGRATION_WAVES_OPERATORS` habilita ondas por operadora, alterada por deploy N1 | Aprovar | Antes da 1ª onda (F1) | Adotada na v2.0 |
| [Anexo C](../anexos/C-operacional.md) | Console exporta a lista de contingência (PDF e CSV) para o `operator_admin`, com `audit_log` | Aprovar | F1 | Adotada na v2.0 |
| [Anexo B](../anexos/B-juridico.md) | Aceite dos termos como clickwrap em `consent` (`purpose = 'terms_of_use'`), com versão e SHA-256 do texto | Aprovar | Antes das lojas (F1) | Adotada na v2.0 |
| [Anexo B](../anexos/B-juridico.md) | `operator_brand.privacy_policy_url` para a política da operadora | Aprovar | F1 | Adotada na v2.0 |
| [Anexo B](../anexos/B-juridico.md) | `ticket.category = 'authority'` para requisições de autoridades | Aprovar | F1 | Adotada na v2.0 |
| [Anexo B](../anexos/B-juridico.md) | Retenção de conversas de atendimento por 90 dias | Validar com o advogado | Antes do G1 | **Pendente — fundador + advogado** (DEC-08) |
| [07 §7](07-alertas-e-tempo-real.md#7-entrega-push-fcm) · T-012 | Push do F0 só para `tenant_owner`; `tenant_member` não recebe push no F0–F1 (sem acesso por veículo) | Confirmar: não vaza alerta de veículo sem acesso | Antes do G0 (31/10/2026) | Adotada na v2.0 |
| [07 §9](07-alertas-e-tempo-real.md#9-fila-de-alertas-no-console-da-central) · [08 §3](08-identidade-e-seguranca.md#3-papéis-e-permissões) · T-011 | Reconhecimento de alerta só pela equipe da operadora no F0 (cliente → 403) | Confirmar: a central trata o SOS | Antes do G0 | Adotada na v2.0 |
| [07 §8](07-alertas-e-tempo-real.md#8-preferências-por-usuário) · T-012 | Preferências de alerta fechadas (403) para a equipe da operadora; a equipe `on_call` recebe os críticos por Pushover desde 01–15/11 (REQ-ALR-024) | Confirmar | Antes do G0 | Adotada na v2.0 |
| [07 §4](07-alertas-e-tempo-real.md#4-sem-comunicação-e-comunicação-perdida-em-movimento) · T-011 | Fórmulas computáveis das condições (b) e (c) do incidente de plataforma | Confirmar após 48 h de piloto | G0 | Adotada na v2.0 |
| [07 §11](07-alertas-e-tempo-real.md#11-tempo-real-get-apiv1stream-sse) · [10 §5](10-apps-e-ux.md#5-estados-honestos) · T-008 | Limiares de presença inclusivos (`≥`) e selo `gps_stale` comparando o fix com o último contato | Confirmar | Antes do G0 | Adotada na v2.0 |
| [08 §2](08-identidade-e-seguranca.md#2-autenticação-better-auth) · T-006 | Convite e redefinição por tabela própria `auth.email_token` (só SHA-256; token gerado no `worker`); último passo TOTP em `auth.totp_last_step` | Confirmar | PR da T-006 | Adotada na v2.0 |
| [08 §2](08-identidade-e-seguranca.md#2-autenticação-better-auth) · T-006 | No F0, login no app de usuário com 2FA ativo recusado com 403 `two_factor_app_unsupported` | Confirmar; rever no F1 para `installer` e `search_team` | F1 | Adotada na v2.0 |
| [08 §4](08-identidade-e-seguranca.md#4-do-request-ao-banco) · T-008 | `GET /api/v1/stream` sem membership ativa responde 401 (CT-ALR-019), não 404 | Confirmar | PR da T-008 | Adotada na v2.0 |
| [13 §6](13-infra-e-operacao.md#6-configuração-e-segredos) · T-006 | Resend como provedor de e-mail (`EMAIL_DRIVER=resend`; a stack admitia Resend ou Brevo) [PREMISSA: plano gratuito basta ao piloto] | Confirmar | Antes do 1º convite real | Adotada na v2.0 |
| [13 §6](13-infra-e-operacao.md#6-configuração-e-segredos) · T-006 | `TRUSTED_PROXY_CIDRS=172.30.0.2/32` (só o `caddy`) em produção | Confirmar | PR da T-013 | Adotada na v2.0 |
| [13 §8](13-infra-e-operacao.md#8-backups-e-restore) · T-013 | Ensaio de restore do F0 (G0-7) na primária, no projeto isolado `tracksys-drill`, com `archive_mode=off`; o mensal volta à standby no F1 | Confirmar: a standby não roda contêiner no F0 (T-003) | Antes do G0-7 | Adotada na v2.0 |
| [13 §7](13-infra-e-operacao.md#7-deploy) · T-013 | `DEPLOY_FAULT=smoke\|catalog`, só para root direto e auditado, para ensaiar rollback na VM sem release quebrada em `main` | Confirmar | PR da T-013 | Adotada na v2.0 |
| [13 §4.4](13-infra-e-operacao.md#44-papéis-e-schema-ops) · T-013 · T-015 | Exceção do F0: consultas do G0 e contagens do restore como `postgres` pelo socket, `READ ONLY`, só agregados | Confirmar; no F1 trocar pelas funções `ops.*` (N0) | F1 | Adotada na v2.0 |
| [13 §6](13-infra-e-operacao.md#6-configuração-e-segredos) · T-013 | `EXTERNAL_EFFECTS=off` cobre também as leituras do Traccar; variável obrigatória, sem padrão | Confirmar | Antes do G0-7 | Adotada na v2.0 |
| [11 §4.6](11-onboarding-e-migracao.md#46-procedimento-manual-do-piloto-f0-t-014) · T-014 · T-015 | `G0.md` sem placa nem nome: IMEI mascarado e código do titular; correspondência no cofre do fundador | Confirmar (REQ-QLD-016) | Antes da 1ª migração do piloto | Adotada na v2.0 |
| [11 §5](11-onboarding-e-migracao.md#5-modelos-de-sms-e-senha-do-dispositivo) · T-014 | Host do SMS limitado a 60 caracteres (`SMS_HOST_TOO_LONG`) | Confirmar | Antes da 1ª migração do piloto | Adotada na v2.0 |
| [14 §9](14-qualidade-e-processo-ia.md#9-estratégia-de-testes) · T-008 · T-011 · T-012 | Datas dos CTs deslocadas para o dia UTC corrente nos testes congelados | Confirmar | — | Adotada na v2.0 |
| [10 §6](10-apps-e-ux.md#6-app--telas) · [02 §2.3](02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0) · T-032 | A05 (detalhe do alerta, REQ-UX-009), A06 (vigilância, REQ-UX-010) e A09 (notificações, REQ-UX-012) entram na T-032 (cartão novo, N2), sobre as rotas da T-012; A06 sai junto com o corte 3 de [02 §2.4](02-escopo-e-fases.md#24-plano-de-corte) | Confirmar; se a T-032 não couber até 27/10/2026, aplicar o corte 3 e registrar | 13/10/2026 | Adotada na v2.0 — fundador confirma |
| [02 §2.3](02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0) · T-014 | Provisionamento no Traccar pelo subcomando `pilot provision` da T-014: cria o dispositivo pela API do Traccar e grava `device.traccar_device_id` como `tracksys_app` com contexto da operadora; passo manual documentado para a demonstração de 20/10; job automático no F1, com o importador (T-024) | Confirmar | 16/10/2026 | Adotada na v2.0 — fundador confirma |
| [02 §2.3](02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0) · [04 §8.1](04-dominio-e-dados.md#81-prazos) · [05 §14](05-ingestao-e-telemetria.md#14-retenção-da-inbox) · T-027 | Retenção da inbox, da outbox e das filas e `app.retention_purge` (REQ-ING-018, REQ-DAD-013) adiadas do F0 para a T-027 (F1); até lá o payload da inbox fica além de 7 dias (risco aceito R-21, §3) | Confirmar o risco aceito | Antes da 1ª onda de migração (F1) | Adotada na v2.0 — fundador confirma |
| [02 §2.3](02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0) · [05](05-ingestao-e-telemetria.md) · [04](04-dominio-e-dados.md) · T-028 | Backfill automático (parte de REQ-ING-016 exercida pelo CT-ING-016), métricas Prometheus da ingestão (REQ-ING-021) vão para a T-028 (F1); o teste de desempenho CT-DAD-012 vai para a T-034 (F1); no F0 ficam a reconciliação e o relatório (T-015), a sonda de atraso da ingestão (T-013) e os índices com a consulta (T-005, T-008) | Confirmar | G0 (31/10/2026) | Adotada na v2.0 — fundador confirma |
| [02 §2.3](02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0) | Donos dos requisitos que estavam sem cartão no F0 (tabela "Donos dos requisitos" de [02 §2.3](02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0): T-005, T-007, T-008, T-013, T-015, T-019 e T-032) | Confirmar | 13/10/2026 | Adotada na v2.0 — fundador confirma |
| [03 §13](03-arquitetura.md#13-configuração) · T-001 | Nomes canônicos das variáveis de banco: `DATABASE_URL` (papel dono; só dbmate, `db:check` e `db:types`), `DATABASE_URL_APP`, `DATABASE_URL_INGEST` e `DATABASE_URL_ADMIN` (superusuário local, só testes e semeadura); somem `APP_DATABASE_URL`, `ADMIN_DATABASE_URL` e `INGEST_DATABASE_URL`; `MIGRATE_DATABASE_URL` do compose de produção é injetada como `DATABASE_URL` no contêiner `migrate` | Confirmar | PR da T-001 | Adotada na v2.0 — fundador confirma |
| [04 §5.1](04-dominio-e-dados.md#51-regras-cat-pnpm-dbcheck-ci-em-todo-pr) · [14 §10](14-qualidade-e-processo-ia.md#10-verificador-de-catálogo-e-testes-de-isolamento) · T-001 | Chave `withoutOperatorId` na allowlist do catálogo (validada por `z.strictObject`): tabela do schema `app` sem `operator_id` NOT NULL só com justificativa ≥ 10 caracteres (CAT-03 nova); junto, CAT-04 por posição de `conkey`/`confkey`, CAT-05 com papéis herdados e CAT-06 com UPDATE de coluna e TRUNCATE | Confirmar (N0) | PR da T-001 | Adotada na v2.0 — fundador confirma |
| [13 §11](13-infra-e-operacao.md#11-observabilidade) · T-007 | SDK do Sentry no console na T-007: inicialização mínima, `VITE_SENTRY_DSN` opcional (sem DSN, desligado) | Confirmar | PR da T-007 | Adotada na v2.0 — fundador confirma |
| [14 §11](14-qualidade-e-processo-ia.md#11-pipeline-de-ci) · T-019 | T-019 com 3 sessões e cerca de 600 linhas em `scripts/ci/**`, acima do teto de 400 da 14 §4 regra 3; plano B: dividir em fatias de 1 PR (T-019 declara `## Fatias`); a fatia 3 (REQ-QLD-008, 016, 018 e 021) sai no corte 0a | Confirmar | Merge do cartão T-019 | Adotada na v2.0 — fundador confirma |
| [14 §15](14-qualidade-e-processo-ia.md#15-requisitos) · [04 §11](04-dominio-e-dados.md#11-requisitos) · T-019 | REQ-QLD-006 e REQ-DAD-021 antecipados do F1 para o F0 | Confirmar | Merge do cartão T-019 | Adotada na v2.0 — fundador confirma |
| [14 §6](14-qualidade-e-processo-ia.md#6-níveis-de-risco) · T-019 | N0 de alavancagem ampliado: `scripts/ci/**`, `scripts/trace.py`, `biome.json`, `tests/vitest.config.ts`, `infra/scripts/check-branch-protection.sh`, `package.json` com `scripts` existentes alterados e fixtures alteradas (alteração só aditiva em `package.json` e `biome.json` é N1) | Confirmar | Merge do cartão T-019 | Adotada na v2.0 — fundador confirma |
| [03 §6](03-arquitetura.md#6-eventos-de-domínio-e-barramento) · T-005 · T-011 | Publicador da outbox (`outbox-publisher`) entregue pela T-005 com `OUTBOX_ROUTES` sem rota de produção; a T-011 só acrescenta a rota `device.state.updated.v1` | Confirmar | PR da T-005 | Adotada na v2.0 — fundador confirma |
| [04 §9.1](04-dominio-e-dados.md#91-transferência-sem-mover-histórico-inv-06) · [09 §6](09-api-e-contratos.md#6-rotas-do-f0) · T-007 · T-011 | Transferência de veículo pela rota `vehicles.transfer` da T-007 (passos 1–6 e 8); o passo 7 (alertas e vigilância) entra com a T-011 | Confirmar | PR da T-007 | Adotada na v2.0 — fundador confirma |
| [04 §3.7](04-dominio-e-dados.md#37-conformidade) · T-005 · T-006 | Migration da T-006 com versão `20261014130000_identidade.sql`, porque a T-005 usa `20261014120000_ingestao.sql` e o dbmate identifica a migration pela versão | Confirmar | PR da T-006 | Adotada na v2.0 — fundador confirma |
| [04 §4.4](04-dominio-e-dados.md#44-funções-security-definer-lista-fechada) · T-004 · T-005 · T-006 | CAT-07 sem `grantees` na allowlist: o catálogo confere o dono `tracksys_owner`, o `search_path` fixo e a ausência de PUBLIC; qual papel executa cada função é provado por teste de aceite | Confirmar | PR da T-004 (dona da CAT-07) | Adotada na v2.0 — fundador confirma |
| [09 §6](09-api-e-contratos.md#6-rotas-do-f0) · T-012 | Leituras aditivas `GET /api/v1/alerts/{alertId}` e `GET /api/v1/vehicles/{vehicleId}/watch-mode` para as telas A05 e A06 | Confirmar | PR da T-012 | Adotada na v2.0 — fundador confirma |
| [13 §12](13-infra-e-operacao.md#12-regras-de-alerta) · [05 §17](05-ingestao-e-telemetria.md#17-métricas-de-ingestão) · T-013 | Sonda de atraso da ingestão do F0 por timer na primária (`tracksys-ingest-lag`), com page direto no Pushover; o Uptime Kuma da standby assume no F1 (T-028) | Confirmar | PR da T-013 | Adotada na v2.0 — fundador confirma |
| [03 §11](03-arquitetura.md#11-orçamento-de-recursos-vm-de-12-gb-2-ocpu-ampere) · T-033 | CT-ARQ-012 (a parte de limites de recurso fica na T-013, no F0) no workflow manual `load-test.yml` (runner arm64, `cpuset` de 2 núcleos, limites de 03 §11), nunca na VM de produção | Confirmar | PR da T-033 | Adotada na v2.0 — fundador confirma |
| [02 §2.3](02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0) · T-014 | `pilot provision` roda na VM pela imagem `tracksys-app` do `worker`, como `tracksys_app` com contexto da operadora | Confirmar | 16/10/2026 | Adotada na v2.0 — fundador confirma |
| [05 §12](05-ingestao-e-telemetria.md#12-queda-prolongada-reconciliação-e-backfill) · T-015 | Reconciliação do G0-2 e de REQ-ING-016 (parte F0) por id do Traccar contra `(source_instance, kind, source_event_id)`, com o modo `--recent` na janela de 05 §12 | Confirmar | PR da T-015 | Adotada na v2.0 — fundador confirma |
| [06 §2](06-comandos-e-bloqueio.md#2-disponibilidade) · [09 §3](09-api-e-contratos.md#3-erros-problem-details) · T-016 · T-018 | Veículo sem vínculo primário aberto: motivo `NO_PRIMARY_DEVICE` no domínio e 422 `COMMAND_NOT_ALLOWED` com `reason = no_primary_device` na API | Confirmar | PR da T-016 | Adotada na v2.0 — fundador confirma |
| [06 §13](06-comandos-e-bloqueio.md#13-homologação-do-perfil-e-g-cmd) · T-022 | Kit `homologation:check` e runbook `docs/runbooks/gates/G-CMD.md` ficam com a T-022 | Confirmar | DoR da T-022 | Adotada na v2.0 — fundador confirma |
| [02 §4.1](02-escopo-e-fases.md#41-conteúdo) · T-017 · T-023 · T-025 · T-026 | A T-025 e a T-026 usam `occurrence` e `consent` criadas pela T-017; a T-023 assume o job `secrets.rewrap` e a rota da chave Asaas | Confirmar | DoR da T-023, T-025 e T-026 | Adotada na v2.0 — fundador confirma |
| [06 §3.1](06-comandos-e-bloqueio.md#31-evidência-válida) · T-016 | `IGN_OFF` exige evidência positiva: ≥ 1 fix válido ao vivo do vínculo com velocidade ≤ `stopped_speed_max_kmh_x10`, `fix_time ≥ observedAt da ignição − 30 s`, `motion = 'stopped'` derivado de fix; `unknown` ou parado só pela regra de ignição não valem | Confirmar no PR da T-016 (N0) | PR da T-016 | Adotada na v2.0 — fundador confirma |
| [06 §3.2](06-comandos-e-bloqueio.md#32-regra-por-cut_point) · T-016 | `fuel_pump` em movimento: 2 fixes em E, o mais recente com `received_at ≥ t − (moving_interval_s + 10 s)`, velocidades ≤ `max_moving_cut_kmh − 10` e a do mais recente ≤ a do anterior; com `position_request_type`, o corte em movimento usa posição sob demanda; pedido → atuação medido no GC-2 e no GC-6 | Confirmar no PR da T-016 (N0) | PR da T-016 | Adotada na v2.0 — fundador confirma |
| [06 §3.2](06-comandos-e-bloqueio.md#32-regra-por-cut_point) · DEC-07 | Moto (`vehicle.kind = 'motorcycle'`): teto efetivo 0 (corte só parado ou por IGN_OFF) até decisão explícita na DEC-07; texto próprio no termo ([Anexo B](../anexos/B-juridico.md) §10) | Confirmar no PR da T-016 (N0) | Antes do G-CMD | Adotada na v2.0 — fundador confirma |
| [Anexo C](../anexos/C-operacional.md) §1 | Contingência por SMS com a mesma janela de 60 s do app (`WHERE#` → resposta → bloqueio em até 60 s); sem a premissa de 5 min; tempo `WHERE#` → resposta medido no G1-6 | Confirmar (N0) | Antes do G1-6 | Adotada na v2.0 — fundador confirma |
| [11 §5](11-onboarding-e-migracao.md#5-modelos-de-sms-e-senha-do-dispositivo) · [08 §10](08-identidade-e-seguranca.md#10-ameaças) · DEC-01 · T-017 | Senha SMS por operadora, diferente da de fábrica e da SmartGPS, trocada por `set_password` antes do `set_server_domain`; `migration_item.password_rotated_at`; item sem rotação não conclui a onda; nova rotação a cada saída de pessoa com acesso; bloquear SMS MT P2P no chip | Confirmar no PR do cartão que a usa (N0) | Antes da 1ª migração do piloto | Adotada na v2.0 — fundador confirma |
| [02 §4.3](02-escopo-e-fases.md#43-gate-g-cmd-meta-1630112026) · [06 §13.5](06-comandos-e-bloqueio.md#135-g-cmd) · T-022 | Sequência do G-CMD: GC-2 → perfil J16 `homologated` por migration N0 (`manifest.json` + SHA-256) → deploy N0 com `COMMAND_BLOCK_SCOPE=pilot:<veículo>` → GC-6 → `G-CMD.md` com GC-1 a GC-8 → `COMMAND_BLOCK_SCOPE=all`; GC-7 (senha SMS rotacionada) e GC-8 (allowlist da APN na 5023 ou risco aceito por escrito) | Confirmar no PR da T-022 (N0) | Antes do G-CMD | Adotada na v2.0 — fundador confirma |
| [06](06-comandos-e-bloqueio.md) · T-016 · T-017 · T-018 | O capítulo 06 absorve as decisões dos cartões (`ARMED > FAILED`, `command_event` tipo A append-only, rota `/api/v1/vehicles/{vehicleId}/commands/challenges`, 202 com `Idempotent-Replayed`, 409 `IDEMPOTENCY_CONFLICT`, `COMMAND_NOT_ALLOWED`/`block_terms_missing`, evidência do pedido só de `position`, `search_team` com TOTP do console, `request_sha256` com `vehicleId`, `PLATFORM_DEFAULT_POLICY`, `TELEMETRY_STALE` não adotado, sem `membership.vehicle_ids`); nesses pontos o cartão vence o capítulo | Confirmar (N0) | PR da T-016 | Adotada na v2.0 — fundador confirma |
| [07](07-alertas-e-tempo-real.md) · [04 §3.6](04-dominio-e-dados.md#36-alertas) | Alertas `command_unknown` (critical, não desativável) e `command_failed` (warning); tipos `command_%` usam `episode_key` único | Confirmar (N0) | PR da T-020 | Adotada na v2.0 — fundador confirma |
| [04](04-dominio-e-dados.md) · [11](11-onboarding-e-migracao.md) · T-017 | Encerrar cliente ou fechar vínculo com relé não desbloqueado → 409 `RELAY_NOT_UNBLOCKED`; a equipe desbloqueia, com step-up, vínculo fechado há ≤ 30 dias de cliente encerrado | Confirmar (N0) | PR da T-018 | Adotada na v2.0 — fundador confirma |
| [08 §6.1](08-identidade-e-seguranca.md#61-chave-do-aparelho-cadastro-f1) · T-018 | Chave de aparelho nova: carência de 24 h para `block` (só `unblock`), 422 `COMMAND_NOT_ALLOWED` com `reason = device_key_cooldown`; push ao aparelho da chave anterior e e-mail "Não fui eu" | Confirmar (N0) | PR da T-018 | Adotada na v2.0 — fundador confirma |
| [04 §4.2](04-dominio-e-dados.md#42-tipos-de-tabela-e-políticas) · T-006 · T-017 | Contexto ganha `app.user_id` (`withContext` com `userId` opcional); política `device_key_self`; gatilho `device_key_revoke_once`; revogação pela central via `app.revoke_device_keys(p_user_id)` (CAT-07); `membership_tenant_manage` exige `tenant_owner` ativo | Confirmar (N0) | PR da T-006 | Adotada na v2.0 — fundador confirma |
| [13 §5](13-infra-e-operacao.md#5-traccar-operacional) · [06 §8.3](06-comandos-e-bloqueio.md#83-evidência-tardia) · [ADR-003](../adr/ADR-003-traccar-borda-de-protocolos.md) | Traccar com `registration=false`; só `TRACCAR_API_USER` comanda; usuário humano do painel `readonly`/`limitCommands` [VALIDAR nomes]; `commandResult` sem comando da plataforma gera `command_outside_platform` (critical) e page ao fundador | Confirmar (N0) | PR da T-003 | Adotada na v2.0 — fundador confirma |
| [08 §10](08-identidade-e-seguranca.md#10-ameaças) · T-028 | Ameaça DNS e contas: FIDO2, bloqueio de transferência, DNSSEC, token Cloudflare restrito e monitor que resolve `gps.` a cada 60 s (REQ-SEG novo, F1) | Confirmar | 01–15/11 | Adotada na v2.0 — fundador confirma |
| [04 §8.2](04-dominio-e-dados.md#82-quente--frio-adr-009) | Frio cifrado no cliente: Parquet com age antes do upload, bucket `tracksys-cold` separado e sem permissão da standby | Confirmar | PR da T-027 | Adotada na v2.0 — fundador confirma |
| [08](08-identidade-e-seguranca.md) · T-027 | `access_log` só para ordem judicial; histórico de localização por ordem judicial ou autorização escrita do titular vítima; CLI `access-log:export` via `app.export_access_log(...)` (CAT-07), CSV + SHA-256 e `audit_log` | Confirmar (N0) | PR da T-027 | Adotada na v2.0 — fundador confirma |
| [07](07-alertas-e-tempo-real.md) · T-029 | REQ-ALR-024: `sos`, `power_cut` e `signal_lost_moving` disparam Pushover com prioridade de emergência (repete a cada 60 s por até 30 min; recibo vira `alert.ack`) para a equipe `on_call`, além do push ao titular; REQ-ALR-023 sobe para P1; no F0 o termo diz que a central não é acionada automaticamente | Confirmar | 01–15/11 | Adotada na v2.0 — fundador confirma |
| [08 §2](08-identidade-e-seguranca.md#2-autenticação-better-auth) · [11 §3.3](11-onboarding-e-migracao.md#33-códigos-por-linha) · T-024 | Titular sem e-mail: código de ativação de 8 caracteres (uso único, 72 h, só SHA-256, 5 tentativas/15 min) enviado pelo `wa.me`; troca código + CPF pela senha; login também por CPF + senha (REQ-SEG novo, M2b) | Confirmar (N0: autenticação) | PR da T-024 | Adotada na v2.0 — fundador confirma |
| [02 §2.2](02-escopo-e-fases.md#22-cronograma-semanal) · [10 §9](10-apps-e-ux.md#9-console--telas) · T-029 | Inventário de paridade com o tracker-net (1 h no S2); filtro "sem comunicação > 24 h / > 7 dias" com CSV na C02 (F1); ordem de serviço só no F2 | Confirmar | 20/10/2026 | Adotada na v2.0 — fundador confirma |
| [02 §2.4](02-escopo-e-fases.md#24-plano-de-corte) | Checkpoints de 13/10 e 16/10 além de 23/10 e 27/10; cortes de processo 0a–0d antes dos de produto; lead time N0 do F0 ≤ 2 dias úteis ([14 §14](14-qualidade-e-processo-ia.md#14--qualidade-e-processo-com-ia)) | Confirmar | 13/10/2026 | Adotada na v2.0 — fundador confirma |
| [02 §2.2](02-escopo-e-fases.md#22-cronograma-semanal) · [11 §4.1](11-onboarding-e-migracao.md#41-liberação-modo-e-janela) | Feriados nacionais 12/10, 02/11, 20/11 e 25/12/2026; janela de onda e de deploy N0 só em dia útil sem feriado (`holidays-br.ts`; 422 `WAVE_OUTSIDE_WINDOW`) | Confirmar | 13/10/2026 | Adotada na v2.0 — fundador confirma |
| [02 §2.2](02-escopo-e-fases.md#22-cronograma-semanal) | Horas do fundador por semana; semana prevista acima de 60 h aciona os cortes 0a–0d; confirmação tácita dos itens desta seção até 31/10/2026 | Confirmar | 13/10/2026 | Adotada na v2.0 — fundador confirma |
| [02 §2.3](02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0) · T-032 · T-033 · T-034 | Divisão de cartões: T-012 fica com o servidor do push e a T-032 com o app (A05, A06, A09); T-013 fica com o essencial e a T-033 (F1) com deploy automatizado, observabilidade avançada, migration-compat, teste de carga e cópia R2; T-028 fica com standby e failover e a T-034 (F1, 01–15/12) com gateway de incidentes e agente SRE | Confirmar | 13/10/2026 | Adotada na v2.0 — fundador confirma |
| [02 §2.3](02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0) · [14 §6](14-qualidade-e-processo-ia.md#6-níveis-de-risco) · T-005 · T-006 · T-019 | Fatias (PRs sequenciais, `## Fatias`, branch `t-NNN-<k>-slug`, ≤ 400 linhas de produção em N0) nos cartões de até 3 sessões T-005, T-006 e T-019, sem ID novo | Confirmar | 13/10/2026 | Adotada na v2.0 — fundador confirma |
| [02 §2.3](02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0) · [14 §6](14-qualidade-e-processo-ia.md#6-níveis-de-risco) | Risco declarado = calculado pelo caminho (maior nível entre os arquivos); alteração só aditiva em `package.json` e `biome.json` é N1; rito N0 só nos arquivos N0; T-004, T-008 a T-013 e T-032 declaram "N0 pelo caminho" | Confirmar | 13/10/2026 | Adotada na v2.0 — fundador confirma |
| [02 §2.3](02-escopo-e-fases.md#23-cartões-de-tarefa-do-f0) | Dependências corrigidas: T-011 depende de T-005, T-006, T-007, T-008 e T-002; T-013 de T-003 e T-004; T-014 acrescenta T-007 e T-013; caminho crítico em duas cadeias | Confirmar | 13/10/2026 | Adotada na v2.0 — fundador confirma |
| [04 §4.4](04-dominio-e-dados.md#44-funções-security-definer-lista-fechada) · T-004 | CAT-07, `app.tg_immutable_columns()` e as políticas `*_definer_read` compartilhadas têm dono único, a T-004; T-005 e T-006 só acrescentam entradas em `securityDefiner` | Confirmar (N0) | PR da T-004 | Adotada na v2.0 — fundador confirma |
| [14](14-qualidade-e-processo-ia.md) · T-019 | REQ-QLD-011 (ISO por tabela; sem `vi.mock` de banco) com dono T-019; `docs-check` compara o 16 gerado e valida âncoras; o `verify` do CI desfaz com `dbmate rollback` cada migration nova do PR | Confirmar | Merge do cartão T-019 | Adotada na v2.0 — fundador confirma |
| [14 §7](14-qualidade-e-processo-ia.md#7-testes-congelados) · [T-019](../../tasks/T-019-guardas-de-processo-no-ci.md) | Teste congelado no modo tabela: 1º commit `test(<escopo>): aceite congelado (T-NNN)`, só em `tests/acceptance/T-NNN/**`, por agente de outro fornecedor; o `acceptance-match` compara byte a byte; em N0, o fundador lê esse commit antes dos demais | Confirmar (N0) | Merge do cartão T-019 | Adotada na v2.0 — fundador confirma |
| `AGENTS.md` · [tasks/README.md](../../tasks/README.md) | Seção "Antes de abrir o PR", coluna "Existe a partir de" nos comandos, regra de segredos para todos os agentes; DoR, DoD e template do `tasks/README.md` viram link para [14 §4](14-qualidade-e-processo-ia.md#4-cartão-de-tarefa)–§5 | Confirmar | 13/10/2026 | Adotada na v2.0 — fundador confirma |
| [00](00-indice.md) · [14 §4](14-qualidade-e-processo-ia.md#4-cartão-de-tarefa) | Parágrafo de prosa ≤ 400 caracteres (acima disso, lista ou tabela); publicador da outbox (`outbox-publisher`) separado de "relé" (hardware); numeração de CT sequencial por área, independente do REQ | Confirmar | 13/10/2026 | Adotada na v2.0 — fundador confirma |
| [Anexo A](../anexos/A-comercial.md) §5 · DEC-10 | Isenção da mensalidade na sobreposição do aviso prévio: [DECISÃO DO FUNDADOR PENDENTE — recomendação: isenta por veículo migrado enquanto a Lider pagar o tracker-net pelo mesmo veículo, por até 60 dias]; `adjustment_cents` com motivo `overlap_waiver` | Decidir com a Lider | 31/10/2026 | **Pendente — fundador** (comercial, até 31/10/2026) |
| [01 §6.2](01-visao-e-negocio.md#62-custo-fixo-no-f0f1-câmbio-premissa-us-1--r-550) · DEC-12 | Plano B de capacidade da OCI: sem A1 até 11/10/2026 18:00 BRT, VM paga de 2–4 vCPU/8 GB com o mesmo `provision.sh`, teto de R$ 150/mês [VALIDAR preço] | Confirmar | 11/10/2026 | Adotada na v2.0 — fundador confirma |
| [tasks/INDEX.md](../../tasks/INDEX.md) | Calendário do DoR do F1: T-020, T-021, T-023 e T-028 com rascunho até 23/10 e leitura até 27/10; T-022, T-024, T-025, T-026, T-029, T-030 e T-033 até 06/11 e 12/11; T-027, T-031 e T-034 até 20/11 e 26/11; no máximo 3 cartões N0 em revisão ao mesmo tempo | Confirmar | 23/10/2026 | Adotada na v2.0 — fundador confirma |

Itens adicionais da consolidação de 09/10/2026 (aguardam confirmação do fundador):

- **Adotada na v2.0 — fundador confirma:** deploy do F0 manual assistido por ssh forced-command (a Action `deploy.yml` vem na T-033); regras AL-03/AL-04/AL-05/AL-07 do F0 por sonda local `host-watch.sh` com Pushover (Grafana na T-033).
- **Adotada na v2.0 — fundador confirma:** cópia do backup na R2 movida para a T-033 (até 15/11/2026); no F0 o backup fica só no Object Storage da Oracle, risco aceito até 15/11/2026. O corte 0d fica redundante com isso.
- **Adotada na v2.0 — fundador confirma:** escolha de dono da REQ-ALR-025 (T-020).

## 6. Requisitos

### REQ-QLD-020 — Registro de decisões atualizado na resolução
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** —
**Regra.** A resolução de uma DEC DEVE ser um PR que muda a linha da §2 para `Resolvida`, com data e resultado, e altera no mesmo PR os capítulos afetados. `pnpm docs:check` DEVE falhar com DEC `Resolvida` sem data ou sem resultado, e listar como aviso as DEC `Aberta` com prazo vencido.
**Aceite.** CT-QLD-020 — Dado a linha da DEC-03 com `Resolvida` e sem data, Quando `pnpm docs:check` roda, Então sai com 1 citando `DEC-03`; com `Resolvida — 09/10/2026 — conta individual`, Então sai com 0; Dado a DEC-12 `Aberta` e a data de execução 11/10/2026, Então sai com 0 e imprime `aviso: DEC-12 vencida em 10/10/2026`.

### REQ-QLD-021 — Gatilhos de risco verificados toda semana
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** —
**Regra.** Na revisão semanal (§1), o fundador DEVE conferir cada gatilho da §3 e registrar ação para todo gatilho disparado; risco com gatilho disparado por 2 revisões seguidas sem ação DEVE virar cartão de tarefa ou DEC.
**Aceite.** CT-QLD-021 — Dado a revisão de 26/10/2026 com 10 testadores ativos no teste fechado do Google Play, Quando o gatilho da R-16 é conferido, Então ele consta como disparado (< 12 em 24/10/2026) com a ação "recrutar na Lider" registrada; Dado a mesma R-16 disparada e sem ação nas revisões de 26/10 e 02/11/2026, Então existe cartão de tarefa ou DEC para ela em 02/11/2026.
