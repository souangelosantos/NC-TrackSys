# 00 — Índice da especificação TrackSys v2.0

> **Resumo:** Ponto de entrada da especificação. Diz o que ler conforme o seu papel, como os IDs funcionam, quais são as invariantes do sistema e onde está cada decisão. A especificação vive no repositório em markdown; quando um PR muda comportamento, ele atualiza o capítulo, o contrato e o teste no mesmo commit.
> **Fases:** F0–F3  ·  **Status:** Aprovado para execução (v2.0, 07/10/2026)
> **Muda em relação à v1.1:**
> - O PDF de 45 páginas vira um pacote markdown versionado, com `AGENTS.md`, tarefas executáveis e verificação automática no CI.
> - O público e o produto foram validados com o fundador numa entrevista de 15 perguntas: a operadora piloto é a Lider Rastreamento, com carteira 100% pessoa física e foco em segurança veicular.
> - Cada número tem unidade, cada requisito tem teste de aceite e cada fase tem data e gate.

## O que ler primeiro

| Papel | Leitura em ordem | Tempo |
|---|---|---|
| Fundador (produto e vendas) | [01](01-visao-e-negocio.md) → [02](02-escopo-e-fases.md) → [15](15-decisoes-riscos-premissas.md) → [Anexo A](../anexos/A-comercial.md) | 40 min |
| Agente de IA implementando | [AGENTS.md](../../AGENTS.md) → cartão em [tasks/](../../tasks/) → só os capítulos citados no cartão | 10 min |
| Revisor de arquitetura | [03](03-arquitetura.md) → [ADRs](../adr/) → [04](04-dominio-e-dados.md) → [13](13-infra-e-operacao.md) | 60 min |
| Revisor de segurança | [06](06-comandos-e-bloqueio.md) → [08](08-identidade-e-seguranca.md) → [04 §4](04-dominio-e-dados.md) → [Anexo B](../anexos/B-juridico.md) | 60 min |
| Advogado | [Anexo B](../anexos/B-juridico.md) → [08](08-identidade-e-seguranca.md) | 45 min |
| Operadora / plantonista | [Anexo A](../anexos/A-comercial.md) → [Anexo C](../anexos/C-operacional.md) | 20 min |

## Mapa dos documentos

| Nº | Documento | Pergunta que responde |
|---|---|---|
| 01 | [Visão e negócio](01-visao-e-negocio.md) | Para quem, por que a Lider troca de plataforma, como a Versix ganha dinheiro, quanto custa operar |
| 02 | [Escopo e fases](02-escopo-e-fases.md) | O que entra em cada fase, com datas, gates, cronograma do Piloto Zero e plano de corte |
| 03 | [Arquitetura](03-arquitetura.md) | Componentes, fluxos, fronteiras de confiança, orçamento da VM e gatilhos de evolução |
| 04 | [Domínio e dados](04-dominio-e-dados.md) | Tabelas, isolamento por RLS em 3 níveis, verificador de catálogo, partições, retenção |
| 05 | [Ingestão e telemetria](05-ingestao-e-telemetria.md) | Contrato com o Traccar, normalização, idempotência, tempo, quarentena |
| 06 | [Comandos e bloqueio](06-comandos-e-bloqueio.md) | Política de corte por tipo de instalação, máquina de estados, confirmação, homologação |
| 07 | [Alertas e tempo real](07-alertas-e-tempo-real.md) | Catálogo de alertas, modo vigilância, push, latência, SSE |
| 08 | [Identidade e segurança](08-identidade-e-seguranca.md) | Login, papéis, step-up por chave do aparelho, links, segredos, LGPD técnica, ameaças |
| 09 | [API e contratos](09-api-e-contratos.md) | Contrato primeiro, rotas, erros, idempotência, paginação, evolução |
| 10 | [Apps e UX](10-apps-e-ux.md) | App Flutter com marca dinâmica, console React, estados honestos, metas de UX |
| 11 | [Onboarding e migração](11-onboarding-e-migracao.md) | Onboarding de operadora em até 14 dias, importador, ondas de migração por SMS |
| 12 | [Cobrança e SVAs](12-cobranca-e-svas.md) | Integração Asaas com split, inadimplência, serviços de valor agregado e indicações |
| 13 | [Infra e operação](13-infra-e-operacao.md) | VMs Oracle, deploy, backups, standby, SLO, monitoramento, agente SRE |
| 14 | [Qualidade e processo com IA](14-qualidade-e-processo-ia.md) | Como agentes de IA constroem com segurança: testes congelados, revisão cruzada, CI |
| 15 | [Decisões, riscos e premissas](15-decisoes-riscos-premissas.md) | O que falta decidir, com dono e prazo; riscos; premissas a validar |
| 16 | [Rastreabilidade](16-rastreabilidade.md) | Requisito → teste → tarefa (gerado automaticamente) |

**Decisões de arquitetura (ADR):**
- [ADR-001 Monólito modular NestJS](../adr/ADR-001-monolito-modular-nestjs.md)
- [ADR-002 Postgres único como banco, fila e barramento](../adr/ADR-002-postgres-unico-fila-barramento.md)
- [ADR-003 Traccar como borda de protocolos](../adr/ADR-003-traccar-borda-de-protocolos.md)
- [ADR-004 Isolamento em 3 níveis](../adr/ADR-004-isolamento-tres-niveis.md)
- [ADR-005 Infra Oracle Always Free](../adr/ADR-005-infra-oracle-always-free.md)
- [ADR-006 Better Auth e chave do aparelho](../adr/ADR-006-identidade-better-auth-chave-aparelho.md)
- [ADR-007 App único Flutter com marca dinâmica](../adr/ADR-007-app-unico-flutter-marca-dinamica.md)
- [ADR-008 Contrato primeiro e SSE](../adr/ADR-008-contrato-primeiro-zod-openapi-sse.md)
- [ADR-009 Retenção quente/frio](../adr/ADR-009-retencao-quente-frio.md)
- [ADR-010 Operação assistida por IA](../adr/ADR-010-operacao-assistida-por-ia.md)
- [ADR-011 Integrar em vez de construir](../adr/ADR-011-integrar-em-vez-de-construir.md)

**Anexos:** [A — Comercial](../anexos/A-comercial.md) · [B — Jurídico](../anexos/B-juridico.md) · [C — Operacional](../anexos/C-operacional.md) · [D — Glossário](../anexos/D-glossario.md)

**Tarefas:** [tasks/INDEX.md](../../tasks/INDEX.md). A primeira é a [T-001](../../tasks/T-001-fundacao-monorepo-e-isolamento.md).

## Convenções

| Prefixo | Significado | Onde é definido |
|---|---|---|
| `REQ-<ÁREA>-NNN` | Requisito com regra normativa (DEVE, NÃO DEVE, PODE) | No capítulo da área. Áreas: NEG, ARQ, DAD, ING, CMD, ALR, SEG, API, UX, ONB, COB, SVA, OPS, QLD |
| `CT-<ÁREA>-NNN` | Teste de aceite (Dado / Quando / Então) | Logo abaixo do requisito |
| `INV-NN` | Invariante: propriedade que nenhuma mudança pode violar | Nesta página, seção "Invariantes" |
| `DEC-NN` | Decisão pendente com dono e prazo | [15](15-decisoes-riscos-premissas.md) |
| `ADR-NNN` | Decisão de arquitetura aceita | [docs/adr/](../adr/) |
| `CAT-NN` / `ISO-NN` | Regra do verificador de catálogo / teste de isolamento | [04 §5](04-dominio-e-dados.md) |
| `T-NNN` | Cartão de tarefa | [tasks/](../../tasks/) |
| `F0`–`F3` | Fases | [02](02-escopo-e-fases.md) |
| `G0`, `G-CMD`, `G1`, `G2` | Gates de saída e de liberação do bloqueio | [02](02-escopo-e-fases.md) |
| `P0` / `P1` / `P2` | Prioridade: bloqueia a fase / necessário na fase / desejável | Em cada requisito |
| `N0` / `N1` / `N2` | Nível de risco de revisão | [14](14-qualidade-e-processo-ia.md) |
| `[PREMISSA]` | Premissa assumida; validação listada em [15](15-decisoes-riscos-premissas.md) | No texto |
| `[VALIDAR — DEC-02]` | Comportamento a confirmar no spike do J16; o texto diz o padrão seguro até lá | No texto |

**Regras de escrita:**
- Unidades: velocidade em km/h, distância em metros, duração em segundos, tempo em UTC (RFC 3339) no sistema e BRT só na interface, dinheiro em centavos inteiros (BRL).
- Formatos: JSON em camelCase, banco em snake_case.
- Datas por extenso no formato 31/10/2026.

## Invariantes

Valem para todo código, toda migration, todo agente de IA e toda operação manual. Uma regressão em qualquer invariante bloqueia a versão.

| ID | Invariante |
|---|---|
| **INV-01** | **Identidade de origem:** todo fato recebido tem chave (source_instance, kind, source_event_id); reentrega com a mesma chave não gera novo fato nem novo efeito. |
| **INV-02** | **Atualidade não regride:** posição com fix_time anterior ao estado atual vai para o histórico e não substitui a posição atual. |
| **INV-03** | **Desconhecido não é zero:** ausência de ignição, velocidade, posição válida ou estado do relé é registrada como desconhecida (NULL/'unknown'), nunca como false/0/desbloqueado. |
| **INV-04** | **Revisão monotônica:** device_state.revision só cresce, sob lock por dispositivo; app, console e SSE descartam revisão menor ou igual à exibida. |
| **INV-05** | **Reprocessamento sem efeito externo:** replay, backfill ou reprocessamento de quarentena não envia push, comando, SMS, cobrança nem indicação. |
| **INV-06** | **Propriedade histórica imutável:** todo fato pertence ao operator_id/tenant_id/vínculo vigente no fix_time; transferência nunca move histórico entre clientes. |
| **INV-07** | **Isolamento:** nenhum caminho de leitura, escrita, exportação, tempo real ou agente de IA cruza a fronteira de operadora ou de cliente; o banco garante (RLS FORCE + FK composta) mesmo se a aplicação errar. |
| **INV-08** | **Comando físico só com evidência:** telemetria ausente, antiga, inválida, replay, falha de cache ou erro nunca autorizam bloqueio; estado desconhecido nunca autoriza repetir bloqueio automaticamente. |
| **INV-09** | **Comercial não aciona físico:** inadimplência, suspensão comercial ou cancelamento nunca disparam bloqueio. |
| **INV-10** | **Bloqueio exige instalação registrada e perfil homologado:** sem cut_point no vínculo ativo e capability_profile homologado com relé, o bloqueio fica indisponível. |
| **INV-11** | **IA sem poder físico nem financeiro:** agentes de IA nunca despacham comandos físicos, nunca alteram cobrança/split e só leem dados no escopo de quem os aciona. |
| **INV-12** | **Unidades e dinheiro canônicos:** km/h, metros, segundos, UTC (RFC 3339), dinheiro em centavos inteiros (BRL); conversões só na fronteira. |

## Como a especificação muda

1. Mudança de comportamento: PR que altera capítulo, contrato (`packages/contracts`), migration e testes juntos; nova linha no histórico abaixo.
2. Mudança de decisão de arquitetura: novo ADR (ou ADR existente marcado como "Substituído por ADR-0NN").
3. Decisão pendente resolvida: atualizar a linha da DEC em [15](15-decisoes-riscos-premissas.md) com data, resultado e capítulos afetados.
4. Rastreabilidade: rodar `python3 scripts/trace.py .` e commitar o [16](16-rastreabilidade.md) regenerado.

## Histórico

| Versão | Data | Mudança |
|---|---|---|
| 1.0.0-RC | 10/2026 | Especificação original (`specdriven.pdf`, 9 páginas) |
| 1.1 | 06/10/2026 | Revisão técnica (PDF, 45 páginas): confiabilidade, isolamento, comandos |
| **2.0** | **07/10/2026** | Reescrita a partir da entrevista com o fundador: operadora piloto e público PF, segurança primeiro, Piloto Zero em 31/10/2026, stack enxuta em VM Oracle gratuita, fundador solo com agentes de IA, SVA e cobrança via Asaas, pacote markdown executável |
