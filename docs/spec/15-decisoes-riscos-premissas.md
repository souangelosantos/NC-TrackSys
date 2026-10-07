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
3. Revisão semanal, segunda-feira 09:00 BRT, ≤ 30 min [PREMISSA]: DEC vencidas ou com prazo na semana, gatilhos de risco disparados, premissas a validar. O fundador atualiza status e data neste arquivo.
4. Decisão nova nasce como `[NOVA DECISÃO PROPOSTA: …]` no capítulo e como linha da §5 no mesmo PR. Só o fundador a promove a DEC, com o próximo número livre.

## 2. Decisões pendentes (DEC)

Situação em 07/10/2026. Dono: fundador, salvo indicação.

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
- **Opções:** (a) credencial de API em sub-organização da conta emnify administrada pela Meta Telecom; (b) a Meta Telecom encaminha SMS por API própria; (c) sem API: SMS manual pelo portal.
- **Recomendação:** (a), com permissão mínima (envio de SMS e leitura de status do SIM) e só para os chips da Lider [VALIDAR — granularidade de permissões da emnify].
- **Impacto se atrasar:** ondas e desbloqueio por SMS ficam manuais; ~300 veículos em lotes de 20 = 15 ondas operadas à mão.
- **Plano B:** SMS manual pelo portal com checklist do runbook ([11](11-onboarding-e-migracao.md)); `migration_item` registra o envio manual; diagnóstico de chip fica para o F2.

### DEC-02 — Capacidades reais do J16
- **Contexto:** a base da Lider é quase toda J16. É preciso confirmar protocolo e porta, relé, estado do relé reportado, ignição, alarme de corte de alimentação, SOS, servidor secundário, aceite de domínio e quando o DNS é resolvido, posição por SMS, buffer offline, acelerômetro, intervalos e senha SMS.
- **Opções:** é validação, não escolha. Fontes: bancada com Traccar e captura (T-002, roteiro de [05 §15](05-ingestao-e-telemetria.md)); manual do fabricante; instalador da Lider.
- **Recomendação:** bancada como fonte única de verdade; cada capacidade vira `yes`, `no` ou `unknown` no `capability_profile` (`draft`) com evidência em `packages/testkit/fixtures/j16/`.
- **Impacto se atrasar:** é o primeiro elo do caminho crítico (T-002 → T-005 → T-011 → T-012 → T-014 → G0); cada dia empurra o G0, no limite até 07/11/2026 ([02 §2.4](02-escopo-e-fases.md)).
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
- **Opções:** 0 km/h (só parado); 20 km/h; 40 km/h (prática da Lider).
- **Recomendação:** teto da plataforma 40 km/h; Lider 40 km/h; operadora nova nasce com 0 km/h e só sobe por versão nova de `command_policy` ([06 §3.3](06-comandos-e-bloqueio.md)).
- **Impacto se atrasar:** bloqueio real indisponível (GC-1 do G-CMD).
- **Plano B:** `max_moving_cut_kmh = 0` na Lider até a decisão; `fuel_pump` vira "só parado".

### DEC-08 — Revisão jurídica do Anexo B
- **Contexto:** sem advogado e sem minuta. Faltam contrato SaaS, DPA, termos de uso, política de privacidade, termo de ciência do bloqueio e consentimentos de SVA; o histórico já foi pedido pela polícia. As lojas exigem política de privacidade publicada para app que trata localização.
- **Opções:** (a) advogado de tecnologia/LGPD com escopo fechado (revisão do [Anexo B](../anexos/B-juridico.md)); (b) modelos prontos com revisão parcial; (c) sem revisão.
- **Recomendação:** (a): cotar 2 a 3 profissionais até 15/11/2026, contratar até 30/11/2026, revisão entregue até 20/12/2026 [VALIDAR — honorários].
- **Impacto se atrasar:** G1-4 reprovado; lojas sem política de privacidade revisada.
- **Plano B:** termo simples do piloto prorrogado; nenhuma operadora além da Lider até a revisão.

### DEC-09 — Plano superior
- **Contexto:** R$ 3,90 é paridade. Cada 10% da base no plano superior soma R$ 600/mês no mês 12 ([01 §6.4](01-visao-e-negocio.md)).
- **Opções:** R$ 4,90; R$ 5,90; R$ 6,90. Conteúdo candidato: relatório histórico acima de 90 dias sob demanda, compartilhamento sem limite, gestão de custos PF, revisões com oficinas, várias cercas.
- **Recomendação:** R$ 5,90, com conteúdo definido após 3 meses de uso real do F1.
- **Impacto se atrasar:** nenhum no F0 e no F1.
- **Plano B:** só o plano de R$ 3,90.

### DEC-10 — Contrato Lider × SmartGPS (dono: Lider)
- **Contexto:** aviso prévio, fidelidade, direito de exportação e acesso ao histórico de 12 meses, que a polícia já pediu.
- **Opções:** (a) migrar após cumprir o aviso prévio; (b) migrar em paralelo e pagar a sobreposição; (c) negociar a saída.
- **Recomendação:** a Lider lê o contrato até 17/10/2026, não anuncia a troca antes e negocia exportação em CSV de 12 meses ou leitura por 12 meses ([11 §8](11-onboarding-e-migracao.md)).
- **Impacto se atrasar:** ondas do F1 atrasam; a Lider paga as duas plataformas por mais tempo.
- **Plano B:** só o piloto de até 10 veículos; ondas depois do fim do aviso prévio.

### DEC-11 — Mapas
- **Contexto:** OpenFreeMap é gratuito e sem SLA [VALIDAR]; PMTiles do Brasil auto-hospedado custa disco e banda da VM [VALIDAR — tamanho do arquivo]. Provedor com cobrança por carga sem teto é proibido ([01 §6.3](01-visao-e-negocio.md)).
- **Opções:** (a) OpenFreeMap; (b) PMTiles auto-hospedado; (c) provedor pago com teto [VALIDAR — preço].
- **Recomendação:** (a) no piloto, com sonda de tile a cada 5 min; migrar para (b) se a disponibilidade medida ficar < 99,5% em 30 dias ou houver indisponibilidade > 30 min.
- **Impacto se atrasar:** nenhum bloqueio; risco de mapa em branco.
- **Plano B:** (b). Sem tiles, app e console mostram coordenadas, idade da posição e "Navegar até o veículo" (deep link).

### DEC-12 — Conta Oracle
- **Contexto:** recursos Always Free ficam na região de origem, que não muda depois [VALIDAR — DEC-12]; instâncias Always Free ociosas podem ser recuperadas pela Oracle; Pay As You Go mantém a gratuidade dentro dos limites [VALIDAR]. Capacidade A1 pode faltar em regiões concorridas [VALIDAR].
- **Opções:** região de origem São Paulo ou Vinhedo; conta Free ou Pay As You Go.
- **Recomendação:** a região brasileira com capacidade A1 disponível no dia; converter para Pay As You Go com alerta de orçamento no menor valor aceito; 2 VMs de 2 OCPU, 12 GB e 100 GB ([ADR-005](../adr/ADR-005-infra-oracle-always-free.md)).
- **Impacto se atrasar:** a VM primária não nasce (T-003); F1 sem standby.
- **Plano B:** primária na região disponível; F0 sem standby (RTO ≤ 2 h); reconstrução em outro provedor por `infra/scripts/provision.sh` com custo lançado no [01](01-visao-e-negocio.md).

### DEC-13 — Modelo dos agentes de operação e suporte
- **Contexto:** agentes chamam o modelo por uma interface `AiProvider` agnóstica ([ADR-010](../adr/ADR-010-operacao-assistida-por-ia.md)). Custo cresce por incidente e por pergunta; dados de suporte vão ao fornecedor do modelo (suboperador no DPA).
- **Opções (preço de tabela em 25/09/2026, US$ por milhão de tokens de entrada / saída):** `claude-opus-5-5` 4,00 / 20,00 (padrão); `claude-sonnet-5-5` 2,00 / 10,00; `claude-haiku-4-5` 1,00 / 5,00; modelo de outro fornecedor pela mesma interface.
- **Recomendação:** manter `claude-opus-5-5` nos dois agentes. Troca por custo só depois que o modelo alternativo passar nos mesmos limiares da avaliação de [14 §9.4](14-qualidade-e-processo-ia.md) (REQ-QLD-017).
- **Impacto se atrasar:** nenhum; o padrão vale.
- **Plano B:** o padrão. Gatilho de reavaliação: custo mensal dos agentes de operação > 10% do custo fixo (ADR-010).

### DEC-14 — Nome fantasia e regime tributário
- **Contexto:** o fundador tem CNPJ com CNAEs 6203-1/00 e 6201-5/01. Simples Nacional: Anexo III (6% na faixa 1) ou V (15,5%) conforme o Fator R [VALIDAR — contador]. D-U-N-S, conta Asaas da Versix (split) e conta Apple de organização dependem do CNPJ final.
- **Opções:** (a) incluir "Versix Solutions" como nome fantasia no CNPJ existente; (b) abrir CNPJ novo; (c) operar sem nome fantasia.
- **Recomendação:** (a): rápida e sem custo de empresa nova; o contador confirma regime e Fator R até 31/10/2026.
- **Impacto se atrasar:** split desligado e fechamento faturando 100% ([12](12-cobranca-e-svas.md)); contrato no nome do fundador.
- **Plano B:** piloto sem cobrança; contrato no CNPJ atual sem nome fantasia.

### DEC-15 — Retenção e anonimização após encerramento
- **Contexto:** proposta de anonimizar 12 meses após o encerramento, salvo legal hold ou obrigação legal. Auditoria de comandos e registros financeiros ficam 5 anos; registros de acesso, 6 meses ([04 §8.1](04-dominio-e-dados.md)).
- **Opções:** 6 meses; 12 meses; 5 anos.
- **Recomendação:** 12 meses para cadastro e posições, igual à retenção praticada pela Lider; validar na revisão jurídica (DEC-08).
- **Impacto se atrasar:** anonimização automática desligada (REQ-DAD-019); dados acumulam.
- **Plano B:** anonimização desligada; eliminação manual a pedido do titular ([08](08-identidade-e-seguranca.md)).

## 3. Riscos

Escalas. Probabilidade em 12 meses: **Baixa** < 10%, **Média** 10–50%, **Alta** > 50%. Impacto: **Médio** = atrasa uma fase ou custa até R$ 5 mil; **Alto** = reprova um gate, perde um cliente ou custa mais de R$ 5 mil; **Crítico** = risco à vida, vazamento de dados ou perda da Lider [PREMISSA].

| ID | Risco | P | I | Mitigação | Dono | Gatilho de ação |
|---|---|---|---|---|---|---|
| R-01 | Atraso do F0 (G0 depois de 31/10/2026) | Alta | Alto | Plano de corte com checkpoints em 23/10 e 27/10 ([02 §2.4](02-escopo-e-fases.md)); tarefas de 1–3 sessões; caminho crítico explícito | Fundador | Trabalho restante > dias restantes num checkpoint → aplicar cortes; < 5 veículos transmitindo em 29/10 12:00 BRT → G0 para o fim da janela de 48 h, no máximo 07/11/2026 |
| R-02 | J16 sem as capacidades esperadas (protocolo, relé reportado, domínio, servidor secundário) | Média | Alto | Spike na S1 (DEC-02); `unknown` por padrão (INV-03); bloqueio só com perfil homologado (INV-10) | Fundador | 13/10/2026 sem captura decodificada → outro decodificador ou outro modelo; J16 sem suporte a domínio → `gps.` por IP reservado (proposta do ADR-005) |
| R-03 | SmartGPS dificulta a migração (senha SMS trocada, exportação negada, cláusula contratual) | Média | Alto | DEC-10; `query_server` e senha conferidos antes de cada onda; cadastro pela planilha já exportada; rollback por SMS testado (G0-8) | Lider | Senha rejeitada em > 2 veículos de uma onda ou recusa formal de exportação → pausar ondas e negociar |
| R-04 | Falta de cobertura do chip (garagem subterrânea, área rural): comando e alerta não chegam | Alta | Médio | Chip multi-operadora; alerta "sem comunicação" e "comunicação perdida em movimento"; UX "aguardando sinal"; desbloqueio com fallback por SMS; diagnóstico emnify (F2) | Fundador | > 5% dos comandos em UNKNOWN em 30 dias ou > 10% dos veículos com lacuna > 30 min por dia → revisar APN e cobertura com a Meta Telecom |
| R-05 | Instabilidade ou recuperação da VM Oracle | Média | Alto | Pay As You Go (DEC-12); standby no F1; WAL-G para Oracle e Cloudflare R2; restore testado (G0-7); rastreadores por domínio | Fundador | Aviso de recuperação da Oracle, 2 incidentes de VM em 30 dias ou > 108 min ruins no mês (50% do orçamento) → executar o plano B da DEC-12 |
| R-06 | Fundador indisponível (fator ônibus = 1) | Média | Crítico | Automação e failover; agente SRE com cardápio fechado; cofre de acesso de emergência e contingência da operadora (§3.1) | Fundador | Até 15/12/2026: cofre montado e ensaiado; page de emergência sem reconhecimento em 30 min → a Lider segue a contingência do [Anexo C](../anexos/C-operacional.md) |
| R-07 | Bloqueio causa acidente | Baixa | Crítico | Política por `cut_point`, teto 40 km/h, evidência `live` ≤ 60 s, ARMED com TTL, step-up, G-CMD (bancada + teste supervisionado), termo de ciência, sem repetição de bloqueio (INV-08/09/10); responsabilidades no [Anexo B](../anexos/B-juridico.md) | Fundador (técnico); Lider (política) | Qualquer relato de reação inesperada → `COMMAND_BLOCK_SCOPE=none` ([06](06-comandos-e-bloqueio.md)) em ≤ 15 min e investigação; CONFIRMED sem atuação na bancada → G-CMD reprovado |
| R-08 | Vazamento entre operadoras ou entre clientes | Baixa | Crítico | INV-07: RLS forçada, FK composta, CAT-01..CAT-06 e ISO em todo PR; revisão N0; agentes de IA no escopo de quem pergunta; 404 fora do escopo | Fundador | Qualquer CAT ou ISO vermelho em `main` → congelar deploy; qualquer relato → incidente de segurança com comunicação no prazo regulamentar ([Anexo B](../anexos/B-juridico.md)) |
| R-09 | Regressão por código gerado por IA | Alta | Alto | Testes congelados, revisão de outro fornecedor, propriedades, mutação, nível de risco por caminho, rollback automático do deploy ([14](14-qualidade-e-processo-ia.md)) | Fundador | 1 escape de INV em produção → merges N0 congelados até o postmortem; 2 escapes N1 em 30 dias → revisar o checklist do revisor |
| R-10 | Mudança de termos de free tier (Oracle, Cloudflare R2, Grafana Cloud, Sentry, UptimeRobot, OpenFreeMap, FCM, GitHub Actions) | Média | Médio | Peças portáveis (Docker Compose, S3 compatível, Alloy); custo por item em [01 §6](01-visao-e-negocio.md); meta de infra ≤ 10% da receita | Fundador | Aviso de mudança → plano de troca em 30 dias; custo de infra > 10% da receita de assinatura no mês |
| R-11 | LGPD/ANPD: incidente, fiscalização ou pedido de titular não atendido | Média | Alto | Encarregado nomeado; DPA; minimização; registros de acesso e auditoria; procedimento de incidente; DEC-08 | Fundador | Incidente com dado pessoal → runbook de incidente; pedido de titular → resposta em 15 dias ([08](08-identidade-e-seguranca.md)) |
| R-12 | Marca indisponível no INPI | Média | Médio | Busca antes de investir na marca (DEC-04); `gps.` em domínio neutro; nome do app trocável até a publicação | Fundador | Colidência nas classes 9 ou 42 → nome alternativo decidido até 17/10/2026 |
| R-13 | Churn da Lider (única operadora no F1) | Baixa | Crítico | Termos de parceira de design ([Anexo A](../anexos/A-comercial.md)); paridade com o tracker-net; app superior; canal direto com o fundador; exportação de dados como garantia contra aprisionamento | Fundador | 2 reclamações formais da Lider no mês, G1 atrasado > 30 dias ou aviso de rescisão → plano de recuperação em 7 dias |
| R-14 | Preço insuficiente: R$ 3,90 não paga a operação e o SVA não decola | Média | Alto | Plano superior (DEC-09); SVA; adesões; custo fixo baixo; equilíbrio de custos em 385–1.026 veículos ([01 §6.5](01-visao-e-negocio.md)) | Fundador | < 1.000 veículos em 31/03/2027 ou receita de indicação = R$ 0 em mai/2027 (G2-3) → revisar preço e planos |
| R-15 | Push no iOS não entregue (permissão negada, modo foco, app encerrado, falha APNs) | Média | Alto | FCM alta prioridade com chave APNs; alerta crítico como Time Sensitive [VALIDAR — entitlement]; app confere permissão; `alert_delivery` com status; iPhone no roteiro do G0 | Fundador | Entrega iOS < 95% em 7 dias [PREMISSA] ou falha do iPhone em G0-3/G0-5 → investigar antes do G0 |
| R-16 | Prazo de 14 dias de teste fechado do Google Play (conta pessoal nova exige 12 testadores por 14 dias) [VALIDAR — regra vigente] | Alta | Médio | Teste fechado iniciado até 27/10/2026 com ≥ 12 testadores do piloto ([02 §2.2](02-escopo-e-fases.md)); conta de organização é isenta [VALIDAR] | Fundador | < 12 testadores ativos em 24/10/2026 → recrutar na Lider e entre conhecidos |
| R-17 | Custo de IA cresce (ferramentas de codificação US$ 200–600/mês + API dos agentes) | Média | Médio | Sessões curtas e cartões pequenos ([14 §13](14-qualidade-e-processo-ia.md)); custo por tarefa medido; DEC-13 | Fundador | > US$ 600/mês (R$ 3.300) por 2 meses seguidos, ou agentes de operação > 10% do custo fixo → cortar ferramentas redundantes e reavaliar modelos |
| R-18 | Prompt injection nos agentes (codificação: issue, PR, fixture, página web; operação e suporte: apelido, ticket) | Média | Alto | Agentes de codificação sem credencial de produção; IA sem poder físico nem financeiro (INV-11); ferramentas só de leitura com RLS; revisor trata instrução em dado como achado bloqueante; ≥ 20 casos de injeção na avaliação | Fundador | 1 injeção bem-sucedida na avaliação → agente desligado até a correção; instrução embutida encontrada em PR → PR bloqueado e origem investigada |
| R-19 | Gargalo de revisão humana: PRs acumulam e o fundador encurta a leitura de N0 | Alta | Alto | Nível de risco por caminho; leitura dirigida em N1; cartões ≤ 400 linhas de produção; métricas de tempo de revisão ([14 §14](14-qualidade-e-processo-ia.md)) | Fundador | > 5 PRs N0/N1 esperando revisão por > 2 dias úteis → parar de abrir cartões novos até zerar a fila |
| R-20 | Backup não restaurável descoberto só no incidente | Baixa | Crítico | Restore testado no G0 (G0-7); restore de ensaio mensal com contagens e perda medidas ([13](13-infra-e-operacao.md)); alerta de WAL atrasado | Fundador | Alerta A05 (WAL sem arquivar > 5 min com escrita) ou A14 (último ensaio com sucesso > 35 dias) → incidente prioritário |

### 3.1 Fator ônibus = 1: cofre e contingência

1. **Cofre de acesso de emergência:** gerenciador de senhas com acesso de emergência para um contato de confiança nomeado pelo fundador, com espera de 48 h [PREMISSA]. Contém: conta raiz da Oracle Cloud, registrador do domínio, Cloudflare, GitHub (dono da organização), cópia da chave age de produção, conta Asaas da Versix, contas Apple e Google Play, Pushover, emnify/Meta Telecom e os códigos de recuperação de 2FA de cada uma.
2. **Instruções sem segredo** em `docs/runbooks/emergencia.md`: o que funciona sozinho (ingestão, alertas, failover), como publicar aviso na status page, como entregar à operadora a exportação dos dados dela, quem contratar (freelancer técnico pré-identificado com acesso aos runbooks) e como encerrar o serviço de forma ordenada.
3. **Contingência da operadora:** o plantonista da Lider consulta a status page, localiza o veículo por SMS e desbloqueia por SMS pelo portal emnify/Meta Telecom ([Anexo C](../anexos/C-operacional.md)); ensaiada no G1 (G1-6).
4. **Contrato:** cláusula de continuidade e portabilidade dos dados da operadora (proposta para o [Anexo B](../anexos/B-juridico.md)).
5. **Ensaio:** o contato de emergência abre o cofre numa simulação até 15/12/2026 e confirma que encontra cada credencial; resultado registrado em `docs/runbooks/gates/G1.md`.

## 4. Premissas

| ID | Premissa | Origem | Como validar | Prazo | Efeito se falsa |
|---|---|---|---|---|---|
| P-01 | J16 envia a cada 30 s em movimento e 300 s parado; ~8% do tempo em movimento | Entrevista (Q8, não respondida) | Spike de bancada (T-002) e 48 h dos veículos do piloto | 13/10/2026 (bancada); 31/10/2026 (piloto) | Refazer carga e disco ([03 §11](03-arquitetura.md), [04 §8.6](04-dominio-e-dados.md)); 10 s em movimento triplica as posições em movimento; parado a 60 s só pesa em `device_state` (compactação) |
| P-02 | Lider tem ~300 veículos (faixa 160–480) | Entrevista (Q2) | Planilha exportada do tracker-net ([11](11-onboarding-e-migracao.md)) | 17/10/2026 | Receita com a Lider de R$ 624 a R$ 1.872/mês; 8 a 24 ondas; base do G1-2 |
| P-03 | Expansão começa pela região do fundador | Entrevista (Q8) | Lista de operadoras-alvo da região com contato feito ([Anexo A §6](../anexos/A-comercial.md)) | 30/11/2026 | Onboarding continua remoto (SMS, sem visita); cobertura de chip e venda presencial mudam |
| P-04 | Frotas só depois do mês 12 (out/2027) | Entrevista (Q2, Q8) | Pedidos de frota no funil de operadoras | Revisão trimestral | Antecipar M1/M5 PF e reordenar o F3; F0 e F1 não mudam |
| P-05 | Câmbio US$ 1 = R$ 5,50 | Briefing | Cotação no fechamento de cada mês | Mensal | Cada R$ 0,50 de alta soma R$ 100–300/mês ao custo de IA (US$ 200–600) |
| P-06 | Better Auth atende ao app Flutter via plugin bearer | [ADR-006](../adr/ADR-006-identidade-better-auth-chave-aparelho.md) | T-006: login com `Authorization: Bearer`, sessão de 30 dias deslizante e revogação ≤ 60 s ([08](08-identidade-e-seguranca.md)) | 20/10/2026 | Token opaco próprio (hash SHA-256 em tabela) verificado pelo `api` para o app, mantendo o Better Auth no console; +1 sessão de agente |
| P-07 | OpenFreeMap disponível para o piloto | Stack; DEC-11 | Sonda de tile a cada 5 min | G1 | PMTiles auto-hospedado (plano B da DEC-11) |
| P-08 | J16 aceita domínio e resolve o DNS a cada reconexão | Entrevista (Q10); ADR-005 | Spike: trocar o registro A e observar a reconexão | 13/10/2026 | Failover por IP reservado reatribuído à standby ou por SMS em massa; RTO maior |
| P-09 | A senha SMS dos J16 da Lider é conhecida (padrão ou instalador) | Entrevista (Q7) | `query_params` em 1 J16 da Lider ([11](11-onboarding-e-migracao.md)) | 13/10/2026 | Migração depende de visita ou da SmartGPS (R-03) |
| P-10 | Ferramentas de IA custam US$ 200–600/mês | Briefing | Faturas mensais | Mensal | Custo fixo fora da faixa de R$ 1.500–4.000/mês; R-17 |
| P-11 | Exceções de migração ≤ 5% da base | [02 §4.4](02-escopo-e-fases.md) (G1-2) | `migration_item` das primeiras 3 ondas | 30/11/2026 | Mais visitas técnicas; G1-2 em risco |
| P-12 | Clientes da Lider aceitam trocar de app | Entrevista (Q3, Q5) | ≥ 80% dos titulares do piloto entram no app em 7 dias [PREMISSA] | 07/11/2026 | Reforçar onboarding no app e o roteiro da central antes das ondas |
| P-13 | Clientes usam o bloqueio como trava diária | Entrevista (Q6, hipótese) | Comandos por veículo por semana no 1º mês após o G-CMD | 31/12/2026 | Custo de SMS e UNKNOWN em garagem sobem; revisar UX "aguardando sinal" e orçamento de SMS |
| P-14 | O plantonista executa a contingência por SMS em ≤ 15 min | [02 §4.4](02-escopo-e-fases.md) (G1-6) | Ensaio com cronômetro | 31/12/2026 | Simplificar o runbook do plantonista e repetir o ensaio |

## 5. Propostas de decisão registradas nos capítulos

Toda `[NOVA DECISÃO PROPOSTA: …]` entra aqui no PR que a cria. O fundador aprova, rejeita ou promove a DEC.

| Origem | Proposta | Recomendação | Decidir até |
|---|---|---|---|
| [01](01-visao-e-negocio.md) | Parceiro local: Versix 20–30%, operadora 70–80% | Unificar com a de [12] pela regra espelho da DEC-05 (quem fecha fica com 75%) | Antes do 1º parceiro local pago |
| [01](01-visao-e-negocio.md) | Preço de setup e anuidade do app dedicado até 31/03/2027 | Aprovar o prazo | 31/03/2027 |
| [01](01-visao-e-negocio.md) | Adesão da Lider faturada só após o G1 | Aprovar (parceira de design) | 31/10/2026 |
| [02](02-escopo-e-fases.md) | `gps.` em domínio Versix independente da marca | Aprovar | 17/10/2026 (com DEC-04) |
| [03](03-arquitetura.md) | `COMMAND_DISPATCH_ENABLED=false` após failover ou restore até a reconciliação | Aprovar | Antes do standby (15/11/2026) |
| [04](04-dominio-e-dados.md) | CAT-07: funções `SECURITY DEFINER` iguais à allowlist, `search_path` fixo, sem PUBLIC | Aprovar | Cartão da T-005 |
| [04](04-dominio-e-dados.md) | Identidade de dedupe por 14 dias em vez de 90 | Manter 90 dias (número canônico) até medir o disco (REQ-DAD-024) | Antes de 1.500 veículos ativos |
| [06](06-comandos-e-bloqueio.md) | `COMMAND_BLOCK_SCOPE` = `none` / `pilot:<ids>` / `all`, mudado só por deploy N0 | Aprovar | Antes da bancada |
| [06](06-comandos-e-bloqueio.md) | `COMMAND_BENCH_OPERATOR_ID` aceita perfil `draft` só na operadora de bancada | Aprovar | Antes da bancada |
| [06](06-comandos-e-bloqueio.md) | Instalador testa bloqueio só em vínculo aberto por ele há ≤ 2 h, até existir OS formal | Aprovar | Antes do G-CMD |
| [06](06-comandos-e-bloqueio.md) | `membership.can_command` (padrão `false`), concedido pelo titular | Aprovar | Antes do G-CMD |
| [06](06-comandos-e-bloqueio.md) | Termo de ciência de titular sem app registrado pela central com anexo | Aprovar com a revisão jurídica (DEC-08) | Antes do G-CMD |
| [07](07-alertas-e-tempo-real.md) | `ALERT_DELIVERY_ENABLED=false` em restore e na standby antes da promoção | Aprovar | Antes do 1º ensaio de restore (G0-7) |
| [07](07-alertas-e-tempo-real.md) | Conexão SSE de escopo operadora com até 1.000 veículos acima de 400 veículos ativos | Decidir no F2 | F2 |
| [08](08-identidade-e-seguranca.md) | `membership.vehicle_ids` (NULL = todos os veículos do cliente) | Aprovar junto com `can_command` | Antes do G-CMD |
| [08](08-identidade-e-seguranca.md) | 4º parâmetro `{ readOnly: true }` em `withContext`, compatível com a T-001 | Aprovar | Cartão do acesso de suporte (F1) |
| [09](09-api-e-contratos.md) | `block` com rastreador `offline` (> 1.800 s) recusado com 409 `TELEMETRY_STALE` em vez de ARMED | Aprovar: resposta imediata e honesta | Antes do G-CMD |
| [10](10-apps-e-ux.md) | `search_team` no navegador usa step-up de console (TOTP + motivo) | Aprovar; alinhar [06 §4.1](06-comandos-e-bloqueio.md) | Antes do G-CMD |
| [10](10-apps-e-ux.md) | `br.com.versix.tracksys` como `applicationId` e bundle id | Aprovar | 14/10/2026 (antes do 1º envio às lojas) |
| [10](10-apps-e-ux.md) | Subdomínio `meu.` para o portal web do cliente | Decidir no F2 | F2 |
| [10](10-apps-e-ux.md) | WebAuthn como step-up do portal | Decidir no F2 | F2 |
| [11](11-onboarding-e-migracao.md) | Nova função `SECURITY DEFINER` para a sonda de quarentena por rastreador | Aprovar com revisão N0 e CAT-07 | Antes do cartão que a usar (F0) |
| [12](12-cobranca-e-svas.md) | DEC-05 ampliada ao parceiro local, proposta 50% | Unificar com [01] pela regra espelho | Antes do 1º parceiro local pago |
| [12](12-cobranca-e-svas.md) | Parte da operadora vira crédito no fechamento; saldo > R$ 100,00 pago por PIX até o dia 10 | Aprovar | Antes do 1º fechamento (dez/2026) |
| [ADR-005](../adr/ADR-005-infra-oracle-always-free.md) | `gps.` em IP público reservado da OCI, reatribuído à standby no failover | Aprovar se a DEC-12 confirmar a reatribuição entre VMs [VALIDAR] | 10/10/2026 (com DEC-12) |
| [ADR-010](../adr/ADR-010-operacao-assistida-por-ia.md) | Entrypoint `infra/scripts/ops-action.sh` para as ações do agente SRE | Aprovar | F1 (agente SRE) |
| [13](13-infra-e-operacao.md) | Ações de operação de plataforma (agente SRE, deploy, failover) auditadas em `ops.audit_log`, fora do schema `app` | Aprovar | Antes da T-013 (deploy) |
| [13](13-infra-e-operacao.md) | `EXTERNAL_EFFECTS=off` troca FCM, emnify, Asaas, e-mail e comandos do Traccar por adaptadores nulos; obrigatório no restore de ensaio | Aprovar; unificar com `ALERT_DELIVERY_ENABLED` de [07] e `COMMAND_DISPATCH_ENABLED` de [03] numa matriz única | Antes do G0-7 |
| [13](13-infra-e-operacao.md) | Deploy automático só de segunda a sexta, 08:00–20:00 BRT; fora disso, `workflow_dispatch` com `force: true` | Aprovar; N0 segue a janela mais estreita de [14 §6](14-qualidade-e-processo-ia.md) | Antes da T-013 |
| [13](13-infra-e-operacao.md) | `tracksys-sre-gateway` em Cloudflare Worker com D1 gratuito como entrada de alertas fora das VMs | Aprovar após confirmar os limites do plano gratuito [VALIDAR] | F1 (agente SRE) |
| [14](14-qualidade-e-processo-ia.md) | Cartão "Guardas de processo no CI" no S1–S2 do F0 | Aprovar | 13/10/2026 |
| [14](14-qualidade-e-processo-ia.md) | Todo PR aberto pela conta de máquina `versix-agent`; só o fundador aprova, rotula exceções, cria tags e faz merge | Aprovar | 09/10/2026 (antes do PR da T-001) |

## 6. Requisitos

### REQ-QLD-020 — Registro de decisões atualizado na resolução
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** —
**Regra.** A resolução de uma DEC DEVE ser um PR que muda a linha da §2 para `Resolvida`, com data e resultado, e altera no mesmo PR os capítulos afetados. `pnpm docs:check` DEVE falhar com DEC `Resolvida` sem data ou sem resultado, e listar como aviso as DEC `Aberta` com prazo vencido.
**Aceite.** CT-QLD-020 — Dado a linha da DEC-03 com `Resolvida` e sem data, Quando `pnpm docs:check` roda, Então sai com 1 citando `DEC-03`; com `Resolvida — 09/10/2026 — conta individual`, Então sai com 0; Dado a DEC-12 `Aberta` e a data de execução 11/10/2026, Então sai com 0 e imprime `aviso: DEC-12 vencida em 10/10/2026`.

### REQ-QLD-021 — Gatilhos de risco verificados toda semana
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** —
**Regra.** Na revisão semanal (§1), o fundador DEVE conferir cada gatilho da §3 e registrar ação para todo gatilho disparado; risco com gatilho disparado por 2 revisões seguidas sem ação DEVE virar cartão de tarefa ou DEC.
**Aceite.** CT-QLD-021 — Dado a revisão de 26/10/2026 com 10 testadores ativos no teste fechado do Google Play, Quando o gatilho da R-16 é conferido, Então ele consta como disparado (< 12 em 24/10/2026) com a ação "recrutar na Lider" registrada; Dado a mesma R-16 disparada e sem ação nas revisões de 26/10 e 02/11/2026, Então existe cartão de tarefa ou DEC para ela em 02/11/2026.
