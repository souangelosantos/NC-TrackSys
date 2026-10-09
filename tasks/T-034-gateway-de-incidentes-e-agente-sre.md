# T-034 — Gateway de incidentes e agente SRE de diagnóstico

> **Cartão resumido.** Escopo, requisitos e dependências já estão fixados; a especificação detalhada, os testes congelados e as "Decisões já tomadas" são escritos até o início da quinzena indicada, quando o cartão passa pelo DoR ([tasks/README.md](README.md)). Até lá, **não implemente** a partir deste cartão.

| Campo | Valor |
|---|---|
| Fase | F1 (quinzena 01–15/12/2026) |
| Requisitos | REQ-OPS-018, REQ-OPS-019, REQ-QLD-017, REQ-DAD-012 (só o teste de desempenho CT-DAD-012; os índices nascem na T-005 e na T-008) |
| Invariantes | INV-05, INV-11 |
| Risco de revisão | N0 |
| Depende de | T-028; DEC-13 (o CT-DAD-012 usa os índices de T-005 e T-008) |
| Estimativa | 2 sessões de agente |
| Bloqueado por decisão | DEC-13 |
| Status | Resumido — DoR pendente |

## Objetivo

Tirar o ponto de entrada de incidentes das duas VMs e anexar diagnóstico ao page: gateway em Cloudflare Worker com D1 que recebe as fontes de alerta, deduplica e envia os pages; agente SRE de IA somente leitura, que busca incidentes por long-poll e anexa o diagnóstico ao page, depois de avaliado (REQ-QLD-017). Inclui o teste de desempenho da consulta canônica do histórico (CT-DAD-012).

## Contexto obrigatório

[13 §12–§13](../docs/spec/13-infra-e-operacao.md#12-regras-de-alerta) (alertas, gateway e agente SRE); [04 §7.3](../docs/spec/04-dominio-e-dados.md#73-índices-por-consulta-prevista) (consulta canônica do histórico); [14](../docs/spec/14-qualidade-e-processo-ia.md) (REQ-QLD-017); [ADR-010](../docs/adr/ADR-010-operacao-assistida-por-ia.md); [Anexo C](../docs/anexos/C-operacional.md); [T-028](T-028-standby-failover-slo-e-agente-sre.md)

## Escopo — fazer

1. Gateway `tracksys-sre-gateway` (Cloudflare Worker com D1, código em `infra/sre-gateway/`): recebe as 3 fontes, deduplica por `ruleId:target`, envia os pages sem rebaixar um já enviado e funciona com as duas VMs fora.
2. Agente SRE somente leitura (`sre-agent`, usuário `opsagent`, papel `tracksys_ops_ro`): busca incidentes por long-poll, sem porta de entrada na standby, e anexa o diagnóstico ao page; auditoria em `ops.audit_log`.
3. Avaliação do agente antes de ligar e a cada troca de modelo ou prompt (REQ-QLD-017).
4. Teste de desempenho CT-DAD-012: 30 dias sintéticos de 300 veículos (~2,5 M posições), `EXPLAIN` da consulta canônica de [04 §7.3](../docs/spec/04-dominio-e-dados.md#73-índices-por-consulta-prevista) com varredura do `*_pkey` em no máximo 2 partições e ≤ 100 ms.

## Fora do escopo

- Cardápio de ações automáticas do agente SRE (F2, REQ-OPS-020).
- Agente de suporte (F2).
- Standby, failover, minuto ruim e status page (T-028).

## Para completar o DoR

1. Lacunas a fechar: esquema D1 do gateway e contrato das 3 fontes [VALIDAR limites do plano gratuito da Cloudflare]; protocolo de long-poll e autenticação do `sre-agent`; prompt, ferramentas de leitura e conjunto de avaliação do agente (REQ-QLD-017); limite de custo por incidente; gerador dos dados sintéticos do CT-DAD-012; resposta da DEC-13.
2. Testes de aceite com Dado/Quando/Então e arquivos em `tests/acceptance/T-034/`, congelados antes da implementação (risco N0: revisão adversarial por agente de outro fornecedor e leitura humana linha a linha).
3. Comandos de verificação e seção "Decisões já tomadas" com pelo menos 5 respostas (DoR de [14 §5](../docs/spec/14-qualidade-e-processo-ia.md#5-dor-e-dod)).
4. Conferir se os requisitos listados ainda batem com os capítulos ([16 — Rastreabilidade](../docs/spec/16-rastreabilidade.md)).
