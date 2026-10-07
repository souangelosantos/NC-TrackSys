# ADR-011 — Integrar em vez de construir: Asaas (cobrança/split), emnify (chips/SMS), FCM (push), WhatsApp por deep link

**Status:** Aceito em 07/10/2026

## Contexto

- Paridade com o tracker-net exige cobranças e suporte na central; o SVA começa por indicação de parceiro (guincho).
- A Lider já cobra pelo Asaas (boleto + PIX), atende por WhatsApp Business e usa chips emnify administrados pela Meta Telecom.
- Fundador solo: cada capacidade construída em casa vira código N0 para manter (dinheiro, SMS ao rastreador, push).
- Margem de R$ 3,90 por veículo não comporta custo variável alto (mapas pagos, SMS em massa, mensagens pagas).

## Decisão

| Capacidade | Integração | Como | Fase | Fallback |
|---|---|---|---|---|
| Cobrança e split | Asaas API v3, conta da própria operadora | `worker` sincroniza clientes e cobranças; `api` recebe webhooks (token validado, processamento idempotente); app mostra fatura e PIX; split de R$ 3,90 por veículo ativo para a carteira Versix (campos de split da API [VALIDAR]); chave da operadora cifrada ([08](../spec/08-identidade-e-seguranca.md)) | F1 | Fatura mensal da Versix à operadora (`platform_fee.settled_via = 'invoice'`) |
| Chips e SMS | emnify API via Meta Telecom (DEC-01) | SMS de desbloqueio após 2 min sem confirmação; SMS de troca de servidor nas ondas; diagnóstico de chip (F2) | F1 | SMS manual no portal emnify/Meta Telecom |
| Push | FCM HTTP v1 (Android; iOS via chave APNs no Firebase) | `worker` envia alertas com prioridade alta; `delivery_key` único | F0 | SSE em primeiro plano; reenvio com backoff |
| Atendimento | WhatsApp por deep link `https://wa.me/<número E.164 sem +>?text=<mensagem>` | Mensagem com placa e link da última posição para `operator_brand.support_whatsapp` | F0 | Telefone da central |
| Navegação | Deep link | `https://www.google.com/maps/dir/?api=1&destination=<lat>,<lon>` e `https://waze.com/ul?ll=<lat>,<lon>&navigate=yes` | F0 | Coordenadas copiáveis |
| Mapas | MapLibre + OpenFreeMap (DEC-11) | Tiles carregados direto pelo app e pelo console | F0 | PMTiles do Brasil auto-hospedado |
| E-mail | Resend ou Brevo (free tier) | `worker` envia | F0 | O outro provedor, pela mesma interface |
| WhatsApp ativo | WhatsApp Cloud API oficial | Cobrança e avisos | F2 | — |

Regras:
1. Cada integração tem uma interface (porta) em `apps/worker/src/integrations/<nome>/` e um fake em `packages/testkit`. Nenhum teste automatizado chama serviço real.
2. Só o `worker` chama APIs externas (REQ-ARQ-008). Webhooks entram pelo `api` e viram jobs.
3. Toda chamada tem timeout de 10 s, retentativa com backoff exponencial e jitter, e chave de idempotência do provedor quando existir.
4. Dinheiro em centavos inteiros dentro do sistema; conversão para reais só no adaptador do Asaas (INV-12).
5. Proibido usar bibliotecas não oficiais de WhatsApp (Baileys, whatsapp-web.js e similares).
6. Integração não aciona físico: evento de cobrança nunca chega ao módulo `commands` (INV-09).

## Alternativas consideradas

- **Cobrança própria (boleto registrado, PIX, conciliação).** Por que não: convênio bancário, regulação e meses de trabalho; a Lider já usa Asaas.
- **Outro PSP (Iugu, Pagar.me).** Por que não agora: obrigaria a Lider a migrar a cobrança; integrar o que a operadora já usa reduz atrito. A interface permite um segundo provedor depois.
- **Agregador genérico de SMS.** Por que não: o SMS precisa chegar ao número do chip M2M, e o caminho natural é a API do provedor do chip; agregador pode não entregar a esse número [VALIDAR].
- **OneSignal ou serviço similar de push.** Por que não: fornecedor extra sobre o FCM, que é gratuito.
- **WhatsApp por biblioteca não oficial.** Proibido: viola os termos, e um banimento derruba o principal canal de atendimento da operadora.
- **Google Maps SDK e tiles.** Por que não: custo por carregamento incompatível com a margem de R$ 3,90.

## Consequências

**Positivas**
- Cobrança, push e SMS sem construir núcleo regulado; custo variável zero ou por uso; deep links sem custo.
- PIX dentro do app, diferencial sobre o tracker-net, sem a Versix tocar no dinheiro da operadora.

**Negativas**
- Terceiros no caminho crítico: FCM no alerta, Asaas no split.
- Mudanças de API dos fornecedores exigem manutenção dos adaptadores.
- Suboperadores com dados pessoais (Oracle, Firebase, Asaas, emnify/Meta Telecom, Sentry, provedor de e-mail, Anthropic) listados no DPA ([Anexo B](../anexos/B-juridico.md)).
- A chave Asaas da operadora é segredo de alto valor; todo código que a toca é N0.

## Gatilho de revisão

- Operadora com outro PSP e ≥ 500 veículos → segundo adaptador de cobrança.
- DEC-01 negada → SMS manual permanente e avaliação de contrato direto com a emnify.
- Falha de push > 2% em 7 dias [PREMISSA] → revisar o canal (APNs direto).
- Disponibilidade do OpenFreeMap insuficiente no piloto → DEC-11.
- Volume de mensagens ativas de WhatsApp que justifique a Cloud API (F2).

## Relacionados

- INV-09, INV-11, INV-12; DEC-01, DEC-05, DEC-06, DEC-11.
- REQ-ARQ-008.
- [06](../spec/06-comandos-e-bloqueio.md) (SMS de desbloqueio); [07](../spec/07-alertas-e-tempo-real.md) (push); [10](../spec/10-apps-e-ux.md) (deep links); [11](../spec/11-onboarding-e-migracao.md) (ondas por SMS); [12](../spec/12-cobranca-e-svas.md) (Asaas, split, indicação); [Anexo B](../anexos/B-juridico.md).
- [ADR-010](ADR-010-operacao-assistida-por-ia.md).
