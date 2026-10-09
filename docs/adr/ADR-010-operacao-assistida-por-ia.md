# ADR-010 — Operação assistida por IA com cardápio fechado de ações e escalonamento humano

**Status:** Aceito em 07/10/2026

## Contexto

- Fundador solo; operar 24 h com uma pessoa só é possível com automação. SLO de 99,5% (≤ 3 h 36 min de minutos ruins por mês); 1 h fora do ar pesa o mesmo que alerta 5 min atrasado.
- Promessa às operadoras: agentes de IA monitoram e tentam reagir; o fundador é acionado a qualquer hora quando preciso. Suporte às operadoras por agente de IA com guardrails (F2).
- Riscos: IA com shell livre em produção, IA disparando bloqueio, prompt injection por dados de usuário (nome de veículo, texto de ticket), vazamento entre operadoras.

## Decisão

1. **Camadas:** (a) automação determinística primeiro — restart policy, healthcheck, reinício de contêiner `unhealthy`, rotação de log, alarmes de disco, memória e backup ([13](../spec/13-infra-e-operacao.md)); (b) agente SRE com cardápio fechado; (c) fundador.
2. **Agente SRE** roda na VM standby, fora da primária, como processo iniciado da imagem do `worker` com entrypoint próprio (`apps/worker/src/sre-agent/main.ts`). É acionado por webhook do Uptime Kuma e por alertas do Grafana Cloud. Lê métricas da réplica com o papel `tracksys_ops_ro`. F1: só A01 e A09. F2: cardápio completo.
3. **Execução:** cada ação é uma ferramenta do modelo que roda, via SSH pela Tailscale, um forced-command no host entrypoint `infra/scripts/ops-action.sh` que aceita só `<ação> <argumento da lista>`. Toda execução gera registro imutável no log de operação (Grafana Cloud) e entra no resumo do incidente.

| ID | Ação | Fase | Limite |
|---|---|---|---|
| A01 | Coletar diagnóstico: estado dos contêineres, health de cada processo, disco, memória, CPU, idade do último WAL arquivado, lag da réplica, idade do job mais antigo por fila, inbox `pending`/`quarantined`, últimas 200 linhas de log por contêiner | F1 | Sem limite (leitura) |
| A02 | Reiniciar `api` ou `worker` | F2 | 2 por serviço por hora |
| A03 | Reiniciar `caddy` | F2 | 2 por hora |
| A04 | Reiniciar `traccar` (todas as sessões reconectam) | F2 | 1 por hora |
| A05 | Liberar disco: rotacionar logs do Docker e remover imagens sem uso; nunca volumes | F2 | 1 por hora |
| A06 | Acordar o reprocessamento normal da inbox `pending` (quarentena fica de fora) | F2 | 1 a cada 15 min |
| A07 | Pausar por até 2 h os jobs de retenção e de export Parquet | F2 | 1 por incidente |
| A08 | Promover a standby com `infra/scripts/failover` | F2 | Só com Uptime Kuma e UptimeRobot falhando por ≥ 10 min e page de emergência sem reconhecimento em 10 min; 1 por incidente |
| A09 | Escrever o resumo do incidente (linha do tempo, hipótese, ações) e anexar ao page | F1 | — |

4. **Proibições (INV-11):** o agente SRE nunca (1) despacha, cancela ou altera comando físico nem envia SMS a rastreador; (2) altera cobrança, split, chave Asaas ou `platform_fee`; (3) lê telemetria, cadastro ou ticket — só métricas agregadas e logs sem dados pessoais (REQ-ARQ-014); (4) roda migration, DDL ou SQL de escrita; (5) apaga dados, volumes, backups ou partições; (6) altera firewall, security list, ACL da Tailscale ou DNS fora do script de failover; (7) faz deploy, rollback ou muda variáveis e segredos; (8) obtém shell interativo ou executa algo fora do cardápio; (9) comunica clientes ou operadoras.
5. **Escalonamento:** page Pushover de prioridade normal com o diagnóstico em ≤ 2 min do início do incidente; prioridade de emergência (repete até reconhecer) se não houver recuperação em 10 min, se a ação necessária não estiver no cardápio, se o limite da ação foi atingido, ou de imediato quando a VM primária estiver inacessível ou o backup estiver sem sucesso há mais de 24 h.
6. **Agente de suporte (F2):** roda no `worker` (REQ-ARQ-008), acionado por pergunta no console. Ferramentas só de leitura, executadas com o contexto RLS de quem pergunta; nenhuma ferramenta escreve. Dados do banco entram no prompt delimitados como dados, nunca como instrução. Proibido: comando físico, cobrança, dados fora do escopo de quem pergunta, resposta jurídica, promessa de prazo ou crédito. Escala para ticket com resumo. Liga só após conjunto de avaliação com ≥ 50 casos e resposta errada ≤ 5% [PREMISSA] ([14](../spec/14-qualidade-e-processo-ia.md)).
7. **Modelo e chamada (DEC-13):** `claude-opus-5-5` pela API Claude atrás de uma interface `AiProvider` agnóstica de fornecedor. `output_config.effort` sempre explícito (SRE `high`, suporte `medium`; o padrão do modelo é `medium`); thinking adaptativo (não pode ser desligado neste modelo); `fallbacks: "default"` com o beta `server-side-fallback-2026-07-01`; checar `stop_reason` antes de ler o conteúdo e tratar `"refusal"` como escalonamento humano; `tool_choice: auto` com `strict: true` nas ferramentas (escolha forçada de ferramenta é rejeitada por este modelo). Preço de tabela em 25/09/2026: US$ 4 por milhão de tokens de entrada e US$ 20 por milhão de saída.

## Alternativas consideradas

- **Agente com shell livre.** Por que não: uma alucinação vira `DROP` ou `rm`; nada é auditável por ação.
- **Só humano.** Por que não: fundador dormindo vira incidente longo; os minutos ruins estouram.
- **Só automação determinística.** Por que não: cobre reinício, não diagnóstico nem correlação.
- **Agente na VM primária.** Por que não: morre junto com ela.
- **Suporte com SQL gerado pelo modelo ou sem contexto RLS.** Por que não: quebra INV-07; injeção vira vazamento.

## Consequências

**Positivas:** diagnóstico pronto quando o fundador atende; ações seguras em minutos; IA sem poder físico ou financeiro; trilha completa por ação.
**Negativas:** custo de API por incidente e por pergunta; dados de suporte (nomes, placas) enviados à Anthropic, que entra como suboperador no DPA ([Anexo B](../anexos/B-juridico.md)); diagnóstico errado é possível (decisão fora do cardápio é humana); o cardápio precisa acompanhar cada runbook novo.

## Gatilho de revisão

- Ação fora do cardápio necessária em ≥ 3 incidentes em 30 dias → avaliar incluí-la com limite.
- Uma ação do agente piorar um incidente → ação suspensa até revisão.
- Resposta errada do suporte > 5% na amostra mensal de 50 → desligar o autoatendimento e revisar.
- Custo mensal de IA em operação > 10% do custo fixo → reavaliar o modelo (DEC-13).

## Relacionados

- INV-05, INV-07, INV-08, INV-11; DEC-13.
- REQ-ARQ-008, REQ-ARQ-014, REQ-ARQ-016.
- [08](../spec/08-identidade-e-seguranca.md); [13](../spec/13-infra-e-operacao.md); [14](../spec/14-qualidade-e-processo-ia.md); [Anexo C](../anexos/C-operacional.md).
- [ADR-004](ADR-004-isolamento-tres-niveis.md), [ADR-005](ADR-005-infra-oracle-always-free.md).
