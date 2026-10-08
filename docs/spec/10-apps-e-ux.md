# 10 — Apps e UX

> **Resumo:** Define o app Flutter do cliente final (`apps/mobile`) e o console React da operadora (`apps/console`): telas por fase, marca dinâmica da operadora com contraste garantido, estados honestos com tokens únicos, UX de comando físico, metas de desempenho e estabilidade, acessibilidade, comportamento offline, atendimento, visão da equipe de busca e distribuição. O app é o que o cliente da Lider compara com o tracker-net: cada tela mostra a idade e a qualidade do dado em vez de esconder incerteza.
> **Fases:** F0, F1, F2  ·  **Status:** Aprovado para execução
> **Muda em relação à v1.1:**
> - Mobile sobe para o F0 (era E2); portal web do cliente vira build Flutter Web do mesmo app (F2).
> - Marca da operadora carregada após o login, com ajuste automático de cor para contraste ≥ 4,5:1.
> - Estado de apresentação vira função pura com vetores de teste compartilhados por app e console.
> - Metas medidas: cold start ≤ 2,5 s, veículo no mapa ≤ 3 s em 4G, sessões sem crash ≥ 99,5%, alerta em ≤ 2 toques.
> - Equipe de busca usa o console responsivo no celular; não existe terceiro app.

## 1. Onde fica o código

| Peça | Caminho |
|---|---|
| Tokens de design (fonte única) | `packages/contracts/design/tokens.json` → `packages/contracts/src/design/tokens.ts` (console) e `apps/mobile/lib/theme/tokens.g.dart`, gerado por `pnpm --filter @tracksys/contracts gen:dart-tokens` |
| Estado de apresentação, idade, contraste (TS, console) | `packages/domain/src/ux/{presentation-state,age-format,brand-contrast}.ts` |
| Mesmas funções no app (Dart) | `apps/mobile/lib/ux/{presentation_state,age_format,brand_contrast}.dart` |
| Vetores de teste compartilhados | `packages/testkit/fixtures/ux/{presentation-vectors,age-vectors,contrast-vectors}.json`; o teste Dart lê o arquivo por caminho relativo |
| App: telas, SSE, cache | `apps/mobile/lib/features/<tela>/`, `apps/mobile/lib/api/sse_client.dart`, `apps/mobile/lib/cache/` |
| Console: rotas | `apps/console/src/routes/` (TanStack Router, um arquivo por rota) |
| Textos de efeito do comando | `packages/domain/src/commands/texts.ts` ([06](06-comandos-e-bloqueio.md) §15); o app recebe `effectText` pronto da API |
| Atendimento (módulo `support`) | `apps/api/src/support/`, contratos em `packages/contracts/src/support/` |
| Testes | `apps/mobile/test/`, `apps/mobile/integration_test/`, `apps/console/src/**/*.test.tsx` (Vitest) |

Pacotes do app além dos do [ADR-007](../adr/ADR-007-app-unico-flutter-marca-dinamica.md): `go_router`, `url_launcher`, `path_provider`, `intl` (pt_BR), `sentry_flutter`, `qr_flutter` (F1). Cliente HTTP `dart-dio` gerado ([ADR-008](../adr/ADR-008-contrato-primeiro-zod-openapi-sse.md)). SSE: parser próprio de `text/event-stream` sobre `dio` com `ResponseType.stream`.

## 2. Princípios

1. Quatro eixos separados: conexão do celular, comunicação do rastreador (`presence`), idade e qualidade da posição, ignição/movimento. Alerta e comando aparecem por cima, sem trocar o estado.
2. Estado nunca só por cor: sempre cor + ícone + texto.
3. Desconhecido aparece como desconhecido (INV-03). Rastreador sem comunicação nunca vira "Estacionado".
4. A marca muda logo, nome e cor de destaque. Cores de estado e textos de segurança não mudam.
5. Celular offline = leitura do último dado com a idade visível; nenhuma ação que escreve.
6. Horário na UI em BRT (UTC−03:00, sem horário de verão [PREMISSA]); no sistema, UTC.
7. Tema escuro único no F0–F1; tema claro é F2 (P2).

## 3. Tokens

```json
{ "color": { "canvas": "#0B0F17", "surface": "#1E293B", "textPrimary": "#F1F5F9", "textSecondary": "#94A3B8",
    "moving": "#10B981", "idle": "#F59E0B", "parked": "#3B82F6", "offline": "#64748B", "danger": "#EF4444",
    "onStatus": "#0B0F17", "onOffline": "#FFFFFF", "brandDefault": "#3B82F6" },
  "marker": { "sizePx": 36, "outlinePx": 2, "outline": "#FFFFFF", "interpolationMaxMs": 1000 },
  "sheet": { "snaps": [0.15, 0.45, 0.90] }, "touchTargetMinDp": 48 }
```

Contrastes medidos (WCAG 2.2): `onStatus` sobre moving 7,56:1, idle 8,93:1, parked 5,21:1, danger 5,10:1; `onOffline` sobre offline 4,76:1; `textPrimary` sobre surface 13,35:1; `textSecondary` sobre surface 5,71:1. Cor de estado como elemento gráfico sobre surface fica ≥ 3:1 (WCAG 1.4.11: parked 3,98, offline 3,07, danger 3,89). Cor de estado nunca é cor de texto sobre surface ou canvas: o rótulo usa `textPrimary`; o chip usa fundo da cor de estado com `onStatus`/`onOffline`.

## 4. Marca dinâmica

1. **Sem sessão:** tela neutra TrackSys (logo TrackSys, `brandDefault`), sem nome, logo ou contato de operadora.
2. **Login:** `GET /api/v1/me` devolve `operator` e `brand` (`displayName`, `logoUrl`, `primaryColor`, `secondaryColor`, `supportWhatsapp`, `supportPhone`) ([09](09-api-e-contratos.md) §6). Usuário com memberships em mais de uma operadora recebe 400 `OPERATOR_SELECTION_REQUIRED` com a lista: tela "Escolha a operadora" e, daí em diante, `X-Operator-Id` em toda requisição ([08](08-identidade-e-seguranca.md) §4).
3. **Cache:** `brand-<operatorId>.json` e `logo-<operatorId>.<png|webp>` no diretório de suporte do app. Abertura com sessão válida aplica o cache no 1º quadro e revalida em segundo plano por `GET /api/v1/operator/brand` com `If-None-Match`; marca nova vale na próxima troca de tela.
4. **Logo:** `https://`, PNG ou WebP, ≤ 256 KiB, ≤ 512 × 512 px. Falhou: iniciais do `displayName` sobre `brandFill`.
5. **Logout:** apaga cache de marca, cache de dados e tokens; volta à tela neutra.
6. **Contato:** sem `supportWhatsapp` e sem `supportPhone`, "Falar com a central" some e o detalhe mostra "Contato da central não cadastrado".
7. **Gravação:** F0 por script `pnpm --filter @tracksys/db seed:brand -- --operator <id> --name … --color … --logo-url … --whatsapp …`, executado como `tracksys_app` com o contexto da operadora; F1 pela tela Marca do console (C13).

**Contraste (`resolveBrandColors(primary)`)**, mesma função em TS e Dart:
1. Luminância relativa WCAG 2.2 (sRGB, limiar 0,04045); contraste = (Lmaior + 0,05) / (Lmenor + 0,05).
2. `brandFill`/`onBrand`: se contraste(primary, #FFFFFF) ≥ 4,5 → texto #FFFFFF; senão, se contraste(primary, #0B0F17) ≥ 4,5 → texto #0B0F17; senão escurece em HSL (CSS Color 4), L − 0,01 por passo, canais arredondados ao inteiro (meio para cima), até contraste com #FFFFFF ≥ 4,5.
3. `brandAccent` (cor da marca como texto, ícone ou borda sobre surface/canvas): primary se contraste(primary, #1E293B) ≥ 4,5; senão clareia, L + 0,01 por passo, até ≥ 4,5.
4. `secondary_color` só decora, sem texto por cima.
5. A operadora grava a cor que escolheu; app e console ajustam na exibição. A tela Marca mostra a prévia resolvida e "Ajustamos a cor para garantir leitura" quando houve ajuste.

| `primary_color` | `brandFill` | `onBrand` (contraste) | `brandAccent` (sobre #1E293B) |
|---|---|---|---|
| #3B82F6 (padrão do banco) | #3B82F6 | #0B0F17 (5,21:1) | #4F8EF7 (4,56:1) |
| #777777 | #747474 | #FFFFFF (4,67:1) | #919191 (4,64:1) |
| #E30613 | #E30613 | #FFFFFF (4,88:1) | #FA555E (4,55:1) |
| #FFD400 | #FFD400 | #0B0F17 (13,40:1) | #FFD400 (10,22:1) |
| #0B3D91 | #0B3D91 | #FFFFFF (10,04:1) | #528EF2 (4,53:1) |

## 5. Estados honestos

Entradas: `vehicle.state` do SSE ([07](07-alertas-e-tempo-real.md) §11) e, por veículo, `presenceThresholds` de `GET /api/v1/vehicles` ([09](09-api-e-contratos.md) §9.1: `delayedAfterS` = `stopped_interval_s` + 60 — J16: 360; `offlineAfterS` 1.800; `lostMovingAfterS` = `max(180, 3 × moving_interval_s)` — J16: 180; perfil não legível no escopo do cliente → padrão 360/1.800/180). `presence` é recalculada no cliente a cada 10 s com a tabela de [07](07-alertas-e-tempo-real.md) §11, limiares inclusivos (`≥`). Primeira linha que casa:

| Estado | Condição | Texto principal | Cor | Ícone (Flutter / lucide) |
|---|---|---|---|---|
| `lost_moving` | `presence = lost_moving` | "Comunicação perdida em movimento" · "Pode ser bloqueador de sinal" | danger | `signal_cellular_off` / `signal-zero` |
| `offline` | `presence = offline` | "Sem comunicação desde {hora}" · "Estava {estado anterior}" | offline | `cloud_off` / `cloud-off` |
| `no_position` | `position = null` | "Comunicando, ainda sem posição GPS" | offline | `location_disabled` / `map-pin-off` |
| `moving` | `motion = moving` | "Em movimento · {v} km/h" (sem velocidade: "Em movimento") | moving | `navigation` girado por `courseDeg` / `navigation` |
| `idle` | `stopped` e `ignition = true` | "Parado com ignição ligada" | idle | `pause_circle_filled` / `circle-pause` |
| `parked` | `stopped` e `ignition = false` | "Estacionado" | parked | `local_parking` / `square-parking` |
| `stopped` | `stopped` e `ignition = null` | "Parado · ignição desconhecida" | parked | `stop_circle` / `circle-stop` |
| `unknown` | demais | "Situação desconhecida" | offline | `help_outline` / `circle-help` |

`{estado anterior}` = rótulo do estado de movimento em minúsculas ("estacionado", "em movimento", "parado com ignição ligada", "parado", "em situação desconhecida"). `{hora}` = `HH:mm` BRT; se não for hoje, `dd/MM HH:mm`.

**Selos** (somam ao estado, não o trocam):
- `delayed` (`presence = delayed`): `schedule`, "Última informação há {idade}".
- `gps_stale` (presença `online`/`delayed`, `lastFixAt` não nulo e `lastContactAt − lastFixAt > delayedAfterS`): `location_disabled`, "GPS sem sinal desde {hora}". O fix é comparado com o **último contato**, não com agora: rastreador que não comunica já tem o selo `delayed` ou o estado `offline` (vetores 5 e 12) [ADOTADO NA v2.0: T-008].
- `alert`: alerta `critical` aberto do veículo → anel danger no marcador e faixa com o título do alerta.
- `relay` (F1): "Relé: bloqueado · observado há {idade}", "Relé: desbloqueado · observado há {idade}" ou "Relé: estado desconhecido".
- Global: "Sem internet no celular · dados de {hora}"; SSE caído há > 10 s: "Reconectando…".

**Idade.** Lista, detalhe, sheet do mapa e console mostram "Última posição válida há {idade}" (`lastFixAt`). Formato: < 10 s "agora"; 10–59 s "há {s} s"; 1–59 min "há {m} min"; 1–23 h "há {h} h {mm} min" ("há 3 h" com 0 min); ≥ 24 h "em {dd/MM} às {HH:mm}". Relógio de 1 s só em tela visível; para em segundo plano.

**Vetores** (`presentation-vectors.json`; agora = 2026-10-20T15:20:00Z = 12:20 BRT; limiares 360/1.800/180 s):

| # | motion | ignition | Posição | Último contato | Último fix | Resultado |
|---|---|---|---|---|---|---|
| 1 | moving | true | 48 km/h | 15:19:50Z | 15:19:50Z | `moving` "Em movimento · 48 km/h" |
| 2 | stopped | true | sim | 15:19:00Z | 15:19:00Z | `idle` |
| 3 | stopped | false | sim | 15:16:00Z | 15:16:00Z | `parked` |
| 4 | stopped | null | sim | 15:19:00Z | 15:19:00Z | `stopped` "Parado · ignição desconhecida" |
| 5 | stopped | false | sim | 15:12:00Z | 15:12:00Z | `parked` + `delayed` "Última informação há 8 min" |
| 6 | moving | true | sim | 15:16:30Z | 15:16:30Z | `lost_moving` |
| 7 | moving | null | sim | 14:40:00Z | 14:40:00Z | `lost_moving` (ignição desconhecida ≠ desligada) |
| 8 | moving | false | 12 km/h | 15:16:30Z | 15:16:30Z | `moving` "Em movimento · 12 km/h" |
| 9 | stopped | false | sim | 14:40:00Z | 14:40:00Z | `offline` "Sem comunicação desde 11:40" · "Estava estacionado" |
| 10 | unknown | null | null | 15:19:30Z | null | `no_position` |
| 11 | unknown | null | sim | 15:19:30Z | 15:19:30Z | `unknown` |
| 12 | stopped | false | sim | 15:19:40Z | 14:00:00Z | `parked` + `gps_stale` "GPS sem sinal desde 11:00" |

**Mapa.** Marcador de 36 px na cor do estado com contorno branco de 2 px; seta girada por `courseDeg` só em `moving`. Entre duas posições válidas do mesmo dispositivo com revisão maior, interpolação linear de até 1.000 ms; sem extrapolação; com `MediaQuery.disableAnimations` (ou `prefers-reduced-motion` no console), salto direto. Veículo `offline`/`lost_moving` fica na última posição válida com contorno tracejado. Sheet com paradas em 15%, 45% e 90%.

## 6. App — telas

| ID | Tela | Fase | Regra | Dados |
|---|---|---|---|---|
| A01 | Entrada e login | F0 | Tela neutra (§4); e-mail + senha; "Esqueci minha senha"; 1º acesso pelo link de convite enviado por e-mail (72 h, [08](08-identidade-e-seguranca.md) §2); erro genérico "E-mail ou senha incorretos" | Better Auth |
| A02 | Início: mapa + lista | F0 | Mapa ao vivo com a lista no sheet. Card: apelido (senão placa), placa, chip de estado, "Última posição válida há X", selos. Ordem: alerta crítico aberto primeiro, depois apelido A→Z. 1 veículo: centraliza com zoom 16; 2+: enquadra todos com margem de 64 px | `GET /api/v1/vehicles`, SSE |
| A03 | Detalhe do veículo | F0 | Apelido, placa, marca/modelo/cor; estado e selos; última posição válida (idade + hora); ignição "Ligada/Desligada/Desconhecida"; alimentação "Veículo/Bateria interna/Desconhecida" (bateria em cor idle); velocidade; ações da fase | SSE |
| A04 | Histórico do dia | F0 | Seletor: hoje, ontem, calendário até 90 dias. Dia BRT = 03:00Z a 03:00Z do dia seguinte. Trajeto na cor moving; início e fim marcados; toque mostra hora e velocidade do ponto mais próximo. Lacunas vêm prontas em `gaps` da API (o app não calcula nem interpola): trecho tracejado com "Sem dados {HH:mm}–{HH:mm}". Resumo: hora do 1º e do último ponto; distância "{x} km", ou "≥ {x} km (há lacunas)" quando `gaps` não está vazio. Dia anterior ao 1º vínculo: "Histórico disponível a partir de {data}" ([11](11-onboarding-e-migracao.md) §8). Mais de 90 dias: "Solicitar relatório" no F1 ([ADR-009](../adr/ADR-009-retencao-quente-frio.md)) | `GET /api/v1/vehicles/{vehicleId}/history?from=&to=&limit=5000` ([09](09-api-e-contratos.md) §9.4) |
| A05 | Alertas | F0 | Lista de 30 dias, abertos primeiro. Detalhe: título, corpo, hora, veículo, mini-mapa com `evidence.lastLocation`, estado atual; ações "Ver no mapa", "Falar com a central", "Navegar até o veículo" | `GET /api/v1/alerts`, SSE `alert` |
| A06 | Modo vigilância | F0 | Interruptor no detalhe. Confirmação: "Avisaremos se o veículo sair 150 m deste local ou se a ignição ligar". Ativo: círculo de 150 m e "Vigilância ativa desde {hora}". 409 `WATCH_MODE_VEHICLE_ON` → "Desligue o veículo para ativar a vigilância"; 409 `WATCH_MODE_NO_FIX` → "Sem posição válida nas últimas 24 h. Não é possível ativar." | [07](07-alertas-e-tempo-real.md) §5 |
| A07 | Falar com a central | F0 | `https://wa.me/{supportWhatsapp sem +}?text={texto}`; texto: "Olá, {operadora}. Sou {nome}. Veículo {apelido}, placa {placa}. Última posição ({HH:mm}): https://maps.google.com/?q={lat},{lon}" (6 casas decimais, ponto). Sem WhatsApp: `tel:{supportPhone}` | Marca |
| A08 | Navegar até o veículo | F0 | Folha com "Google Maps" (`https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving`) e "Waze" (`https://waze.com/ul?ll={lat},{lon}&navigate=yes`). Fix com mais de 10 min: aviso "Posição de há {idade}. O veículo pode ter se movido." | Último fix válido |
| A09 | Notificações | F0 | Canais Android `alerts_high` (alta) e `alerts_info` (padrão) criados no 1º início. Explicação antes do pedido de permissão (Android 13+ `POST_NOTIFICATIONS`; iOS com Time Sensitive). Negada: faixa "Alertas desligados neste celular" + "Ativar". Preferências por veículo × tipo: `locked` → travado "Sempre ativo"; `available = false` → "Indisponível neste rastreador". Cartão no 1º acesso: "Quer ser avisado quando a ignição ligar?" | [07](07-alertas-e-tempo-real.md) §7–8 |
| A10 | Conta | F0 | Nome, e-mail, operadora, versão, termos e privacidade, Sair (apaga o token de push, [07](07-alertas-e-tempo-real.md) §7) | `GET /api/v1/me` |
| A11 | Bloquear / desbloquear | F1 | §7 | [06](06-comandos-e-bloqueio.md) §14 |
| A12 | Termo de ciência do bloqueio | F1 | Texto do [Anexo B](../anexos/B-juridico.md) com operadora, `cut_point` de cada veículo, teto e TTL; botão "Li e aceito" | `POST /api/v1/tenants/{tenantId}/block-terms` |
| A13 | Ocorrência ("Fui roubado") | F1 | Confirmação → abre ocorrência. Tela: "Ligar 190" (`tel:190`), "Falar com a central", "Bloquear" (fluxo normal da §7, se disponível), "Compartilhar com a polícia" (A16), número do BO (≤ 40 caracteres), linha do tempo (alertas, comandos, posições). Abrir ocorrência não cria comando (INV-08) | [06](06-comandos-e-bloqueio.md) §11 |
| A14 | Faturas e PIX | F1 | Lista: valor (centavos → "R$ 49,90"), vencimento, status. PIX: "Copiar código PIX" (`pix_payload` exato) e QR do mesmo conteúdo. Fatura vencida: "Venceu em {data}. Pague com PIX ou fale com a central." Nenhum texto liga cobrança a bloqueio (INV-09) | [12](12-cobranca-e-svas.md) |
| A15 | Chamar guincho | F1 | Parceiros `tow` disponíveis. 1º uso: consentimento por parceiro ([12](12-cobranca-e-svas.md)). `POST /api/v1/referrals` (201) antes de abrir WhatsApp ou telefone do parceiro com placa, modelo, cor e link da posição. Sem internet: mostra o telefone do parceiro, sem indicação registrada | [12](12-cobranca-e-svas.md) |
| A16 | Compartilhar localização | F1 | Duração 1 h, 4 h ou 24 h (`ttlS` 3.600, 14.400 ou 86.400); folha de compartilhamento do sistema com a URL devolvida pela API, exibida uma única vez; lista de links ativos com "Expira às {hora}" e "Revogar" | [08](08-identidade-e-seguranca.md) §7 |
| A17 | Cercas | F1 | Círculo no mapa com raio arrastável de 100 a 5.000 m (trava nos limites), nome, gatilho entrar/sair/ambos; até 10 por veículo, sem requisição na 11ª | [07](07-alertas-e-tempo-real.md) REQ-ALR-022 |
| A18 | Familiares | F1 (P2) | Titular convida e revoga `tenant_member` e define `can_command` | [06](06-comandos-e-bloqueio.md) §4.1, [08](08-identidade-e-seguranca.md) |
| A19 | Serviços (SVA) | F2 | Catálogo habilitado pela operadora: assistência 24h, revisões, custos | [12](12-cobranca-e-svas.md) |

[DECISÃO DO FUNDADOR PENDENTE: A05 (REQ-UX-009, P0) e A06 (REQ-UX-010, P1) são F0 nesta tabela, mas nenhum cartão do F0 as entrega, e a T-012 abre o mapa ao vivo do veículo ao tocar o push, tratando o detalhe do alerta como F1. Recomendação: cartão pequeno no S3 com o detalhe mínimo do alerta (A05, só a partir do push) e o interruptor da vigilância (A06), sobre as rotas da T-011; se não couber até 27/10/2026, registrar o corte no plano de [02](02-escopo-e-fases.md) §2.4, com o comportamento da T-012 valendo no G0 e REQ-UX-009/010 passando para o F1. Registro em [15](15-decisoes-riscos-premissas.md) §5.]

Rotas internas do app: `/inicio`, `/veiculos/:id`, `/veiculos/:id/historico?dia=AAAA-MM-DD`, `/alertas`, `/alertas/:id`, `/conta`. O link do push `tracksys://alerts/{id}` ([07](07-alertas-e-tempo-real.md) §7) abre `/alertas/:id` com o app encerrado, em segundo plano ou aberto; sessão expirada passa pelo login e volta ao alerta.

## 7. UX de comando (F1)

1. **Disponibilidade** por `GET /api/v1/vehicles/{vehicleId}/command-availability` ao abrir o detalhe e após cada estado final. `available = true` → botão "Bloquear" (ou "Desbloquear"). `COMMAND_TERMS_NOT_ACCEPTED` → "Aceitar termo para habilitar bloqueio" (A12). `COMMAND_DISPATCH_DISABLED` → "Bloqueio temporariamente indisponível". Demais códigos de [06](06-comandos-e-bloqueio.md) §14 → sem botão e a linha "Bloqueio pelo app indisponível neste veículo. Fale com a central." `activeCommandId` → mostra o cartão de estado em vez do botão.
2. **Confirmação:** apelido, placa, modelo e cor; `effectText` da API exibido literalmente; aviso de SMS de desbloqueio pendente quando a API o enviar ([06](06-comandos-e-bloqueio.md) §9 item 5); motivo: "Suspeita de furto ou roubo" (`theft_suspected`), "Preventivo" (`preventive`), "Outro" (`other`, texto opcional ≤ 500).
3. **Deslizar para confirmar:** alça de 56 dp; confirma ao chegar a 90% da largura; soltar antes volta ao início. Com leitor de tela, a ação de acessibilidade "Confirmar bloqueio" substitui o gesto.
4. **Biometria + chave do aparelho:** `POST /api/v1/vehicles/{vehicleId}/commands/challenges` ([08](08-identidade-e-seguranca.md) §6, [09](09-api-e-contratos.md)) → prompt nativo "Confirme para bloquear {placa}" → assinatura ([08](08-identidade-e-seguranca.md)) → `POST …/commands` com `Idempotency-Key` UUID criado ao abrir a tela de confirmação, reutilizado só em "Tentar de novo" na mesma tela e descartado ao sair dela. Biometria cancelada ou falha: "Bloqueio não enviado", nenhuma requisição a `/commands`. Sem `device_key`: fluxo "Ativar confirmação por biometria neste celular" antes do 1º comando.
5. **Nunca enfileirar:** sem conexão (última requisição sem resposta de rede ou SSE caído há > 10 s), o controle fica desativado com "Sem internet. O pedido não pode ser enviado. Ligue para a central: {telefone}" (`tel:`). POST sem resposta: "Sem resposta do servidor"; ao reconectar, o app consulta `GET /api/v1/vehicles/{vehicleId}/commands?limit=1` e mostra o comando existente ou "O pedido não chegou ao servidor". Nunca reenvia sozinho, nunca guarda pedido em disco, nunca envia ao reabrir.
6. **Acompanhamento:** SSE `command.state` ([09](09-api-e-contratos.md)); com o SSE caído e o cartão visível, `GET /api/v1/commands/{commandId}` a cada 5 s.

| Estado | Título (textos de [06](06-comandos-e-bloqueio.md) §15) | Cor | Ícone | Ações |
|---|---|---|---|---|
| REQUESTED | "Pedido registrado" · "Verificando condições de segurança" | parked | `hourglass_empty` | — |
| ARMED | "Aguardando condição segura — {motivo}" · "Expira às {hora}" com contagem regressiva | idle | `timer` | Cancelar |
| READY, DISPATCHING | "Enviando ao rastreador" | parked | `send` | — |
| AWAITING_CONFIRMATION | "Aguardando confirmação do rastreador" | parked | `sync` | — |
| CONFIRMED | "Bloqueio confirmado às {hora}" / "Desbloqueio confirmado às {hora}" | moving | `check_circle` | — |
| UNKNOWN | "Não foi possível confirmar. O veículo pode ou não estar bloqueado" | danger | `help` | Falar com a central |
| FAILED | "O rastreador não executou" | danger | `error` | Tentar de novo (novo pedido com step-up), Falar com a central |
| REJECTED | "Recusado: {motivo}" | offline | `block` | — |
| EXPIRED | "Expirou sem condição segura. Nada foi enviado" | offline | `timer_off` | — |
| CANCELLED | "Cancelado. Nada foi enviado" | offline | `cancel` | — |

`{motivo}` do ARMED: `awaiting_speed` "veículo acima de {teto} km/h"; `awaiting_stop` "o veículo precisa parar"; `awaiting_evidence` "aguardando posição atual do rastreador"; `awaiting_contact` "aguardando sinal do rastreador"; `awaiting_on_demand_fix` "pedindo posição ao rastreador". O selo `relay` (§5) fica separado do cartão; nenhum título de UNKNOWN contém "bloqueado".

## 8. Desempenho, estabilidade, acessibilidade e offline

| Meta | Valor | Medição |
|---|---|---|
| Cold start | p90 ≤ 2.500 ms | Build release, sessão válida e cache presente; 20 execuções de `adb shell am start -S -W br.com.versix.tracksys/.MainActivity`; `TotalTime`. Aparelho de referência: Samsung Galaxy A15, 4 GB, Android 14 [PREMISSA] |
| Veículo visível no mapa | p90 ≤ 3.000 ms em 4G | Span Sentry `map.first_vehicle`: início do processo → 1º marcador desenhado com dado da rede; 20 aberturas no aparelho de referência em 4G real |
| Sessões sem crash | ≥ 99,5% por versão | Sentry release health, janela de 7 dias, mínimo de 200 sessões. Abaixo: versão não passa de 20% na loja; 2 semanas seguidas abaixo aciona o gatilho do [ADR-007](../adr/ADR-007-app-unico-flutter-marca-dinamica.md) |
| Alerta a partir do push | ≤ 2 toques | Toque 1: notificação → detalhe do alerta; toque 2: mapa completo |

F0: as medidas de cold start e mapa são informativas e vão para o PR da versão; F1: bloqueiam a publicação nas lojas.

**Acessibilidade.** (1) Todo elemento interativo com `Semantics`/`aria-label`; card lido como "{apelido}, placa {placa}, {estado}, {velocidade}, última posição válida há {idade}". (2) Mudança de estado de comando anunciada (`SemanticsService.announce`; `aria-live="polite"` no console). (3) Fonte do sistema até 200% sem cortar estado e idade em 360 × 800 dp. (4) Alvos ≥ 48 dp. (5) Daltonismo: estado sempre com ícone e texto. (6) Contraste ≥ 4,5:1 para texto (§3, §4). Testes de widget usam `androidTapTargetGuideline`, `iOSTapTargetGuideline`, `labeledTapTargetGuideline` e `textContrastGuideline`.

**Offline (somente leitura).** Cache por usuário em arquivo no diretório de suporte do app: lista de veículos, último `vehicle.state` de cada um, alertas abertos, marca e `syncedAt`. Sem rede, o app mostra o cache com a faixa global; estado e selos são calculados com agora = `syncedAt` (o celular não sabe se o rastreador parou de comunicar), e as idades contam do relógio real. Vigilância, comandos, BO, cercas e compartilhamento ficam desativados. Cache com mais de 7 dias não é exibido; logout apaga tudo.

## 9. Console — telas

| ID | Rota | Fase | Regra |
|---|---|---|---|
| C01 | `/login` | F0 | E-mail + senha; TOTP obrigatório para a equipe da operadora no F1 ([08](08-identidade-e-seguranca.md)) |
| C02 | `/mapa` | F0 | Todos os veículos da operadora; mesma derivação de estado (§5); filtros por estado ("Sem comunicação" = `offline` + `lost_moving`); busca por placa, apelido ou cliente; lista virtualizada; acima de 200 veículos, conexões SSE de até 200 cada ([07](07-alertas-e-tempo-real.md) §11) |
| C03 | `/clientes`, `/clientes/:id` | F0 | Nome, CPF/CNPJ com dígito verificador, convite do titular ([08](08-identidade-e-seguranca.md)); veículos do cliente. Telefone E.164 e e-mail de contato (`tenant.contact_phone`/`contact_email`, [11](11-onboarding-e-migracao.md) §3.2) entram no F1 com o importador: as colunas não existem no F0 ([04](04-dominio-e-dados.md) §3.1, `POST /api/v1/tenants` de [09](09-api-e-contratos.md) §6); no F0 o contato do titular é o e-mail do convite |
| C04 | `/veiculos/:id` | F0 | Placa normalizada (maiúsculas, sem hífen; regex de [04](04-dominio-e-dados.md) §3.1), tipo, marca, modelo, cor, ano, apelido; vínculo atual e anteriores |
| C05 | `/rastreadores`, `/rastreadores/:id` | F0 | IMEI (15 dígitos), modelo, perfil e status do perfil, ICCID e MSISDN, status, "Último contato: nunca / há X", vínculo atual; aviso "Comunicando sem vínculo" ([11](11-onboarding-e-migracao.md) REQ-ONB-019) |
| C06 | `/veiculos/:id/vinculo` | F0 | Rastreador em estoque; "Relé de bloqueio instalado?" Sim/Não sem padrão; Sim → ponto de corte obrigatório (bomba de combustível, ignição pós-chave, motor de arranque) com o texto de efeito de [06](06-comandos-e-bloqueio.md) §15 (se `packages/domain/src/commands/texts.ts` ainda não existir no F0, mostra só o nome do ponto de corte; nenhum texto de segurança é escrito fora de 06 [ADOTADO NA v2.0: T-007]); Não → "Sem bloqueio instalado". `POST /api/v1/device-assignments` exige a chave `cutPoint` (valor ou `null` explícito, [09](09-api-e-contratos.md) §6); ausente → 422 `VALIDATION_FAILED` com `errors[0].path = "cutPoint"`. Encerrar vínculo devolve o rastreador a `stock` ou `maintenance` (campo `deviceStatus` de `POST /api/v1/device-assignments/{assignmentId}/close`, [09](09-api-e-contratos.md) §6) |
| C07 | `/veiculos/:id/historico?dia=` | F0 | Regras da A04 + tabela de pontos (hora BRT, velocidade, ignição, válido) |
| C08 | `/alertas` | F1 | Fila de [07](07-alertas-e-tempo-real.md) §9 |
| C09 | `/comandos` e painel no veículo | F1 | Pedido com TOTP ≤ 5 min + motivo ≥ 10 caracteres; mesmos textos da §7; registro de contingência ([06](06-comandos-e-bloqueio.md) §10) |
| C10 | `/ocorrencias` | F1 | Abrir e fechar, BO, linha do tempo, pacote de evidências ([08](08-identidade-e-seguranca.md)) |
| C11 | `/cobranca` | F1 | [12](12-cobranca-e-svas.md) |
| C12 | `/atendimentos` | F1 | §11 |
| C13 | `/marca` | F1 | Campos de `operator_brand` com prévia resolvida (§4) no app e no console |
| C14 | `/usuarios` | F1 | Convidar, mudar papel, revogar ([08](08-identidade-e-seguranca.md)) |
| C15 | `/importacoes`, `/migracao` | F1 | [11](11-onboarding-e-migracao.md) |
| C16 | `/auditoria` | F1 | `audit_log` filtrável por ator, ação, alvo e período |
| C17 | `/chips` | F1 | `sim_card`: ICCID, MSISDN, APN, status, rastreador |
| C18 | `/politica-de-comando` | F1 | Nova versão de `command_policy` ([06](06-comandos-e-bloqueio.md) §3.3) |
| C19 | `/busca`, `/busca/:occurrenceId` | F1 | §10 |
| C20 | `/plataforma/operadoras` | F2 | Só `platform_admin`: operadoras em onboarding com `onboarding_days` (REQ-NEG-005), destaque no 10º dia sem 1º fix válido; checklist no runbook de [11](11-onboarding-e-migracao.md) §2 |

Menu por papel (autorização no `api`, [08](08-identidade-e-seguranca.md)): `operator_admin` todas; `operator_agent` todas menos C13, C14, C16, C18; `installer` C05, C06 e C04 em leitura; `search_team` só C19. Navegadores: duas últimas versões de Chrome, Edge, Firefox e Safari; C19 também em Chrome Android e Safari iOS.

## 10. Visão da equipe de busca (web responsiva)

1. `/busca` lista as ocorrências abertas da operadora; `search_team` só enxerga veículos com ocorrência aberta (404 nos demais, [08](08-identidade-e-seguranca.md)).
2. `/busca/:occurrenceId` em layout de celular (≤ 480 px): mapa em tela cheia seguindo o veículo; cartão com placa, modelo, cor, estado e "Última posição válida há X" em fonte ≥ 20 px; trajeto dos últimos 30 min; "Navegar" (links da A08); "Ligar para a central"; "Compartilhar com a polícia" (link de [08](08-identidade-e-seguranca.md)).
3. Tela ligada com a Screen Wake Lock API enquanto a página está visível.
4. Ocorrência encerrada: "Ocorrência encerrada" e fim do recebimento de posições em ≤ 5 s.
5. Pedido de bloqueio pela visão de busca usa o step-up do console (TOTP ≤ 5 min + motivo) [ADOTADO NA v2.0: `search_team` no navegador usa step-up de console; [06](06-comandos-e-bloqueio.md) §4.1 prevê chave do aparelho, que não existe na web].

## 11. Atendimento (`ticket`, módulo `support`)

Tabela tipo A ([04](04-dominio-e-dados.md) §4.2), F1. A API recusa papéis do cliente (403); só a equipe da operadora lê e escreve.

```sql
CREATE TABLE app.ticket (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), operator_id uuid NOT NULL, tenant_id uuid NOT NULL,
  vehicle_id uuid NULL, alert_id uuid NULL, opened_by uuid NULL REFERENCES auth."user" (id),
  channel text NOT NULL CHECK (channel IN ('whatsapp', 'phone', 'app', 'in_person', 'system')),
  subject text NOT NULL CHECK (length(subject) BETWEEN 3 AND 120),
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'waiting_customer', 'resolved')),
  notes text NOT NULL DEFAULT '' CHECK (length(notes) <= 4000), version integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), resolved_at timestamptz NULL,
  CONSTRAINT ticket_tenant_fk FOREIGN KEY (operator_id, tenant_id) REFERENCES app.tenant (operator_id, id),
  CONSTRAINT ticket_vehicle_fk FOREIGN KEY (operator_id, tenant_id, vehicle_id) REFERENCES app.vehicle (operator_id, tenant_id, id),
  CONSTRAINT ticket_system_chk CHECK ((channel = 'system') = (opened_by IS NULL)));  -- 'system': aberto por job (ex.: rollback_failed de 11)
-- alert_id: FK composta para app.alert quando a tabela expuser UNIQUE (operator_id, tenant_id, id) [alinhar com 04]
```

Rotas ([09](09-api-e-contratos.md) §7): `POST /api/v1/tickets` (`tenantId`, `vehicleId?`, `alertId?`, `channel`, `subject`, `notes?`); `GET /api/v1/tickets?status=&tenantId=&cursor=`; `PATCH /api/v1/tickets/{ticketId}` com `If-Match: "<version>"`. Abrir a partir de cliente, veículo ou alerta preenche o contexto: cliente, veículo, alerta, estado atual e últimos 5 comandos. Ação "Abrir WhatsApp do cliente": `https://wa.me/{telefone}?text=` "Olá, {nome}. Aqui é a {operadora}, sobre o veículo {placa}." `audit_log`: `ticket.create`, `ticket.update`.

## 12. Distribuição

| Item | F0 | F1 | F2 |
|---|---|---|---|
| Android | Teste fechado do Google Play: ≥ 12 testadores por 14 dias seguidos antes da produção (conta pessoal) [VALIDAR — regra vigente]; início até 27/10/2026 | Produção após os 14 dias | Opção B por operadora |
| iOS | TestFlight (DEC-03); testadores externos passam pela revisão beta da Apple [VALIDAR prazo] | App Store (G1-5) | Opção B |
| Identificador | [ADOTADO NA v2.0: `br.com.versix.tracksys` como `applicationId` e bundle id, fixado antes do 1º envio (S2) e independente de DEC-04] | — | Opção B: identificador da operadora |
| Versões mínimas | Android 8.0 (API 26) e iOS 15 [PREMISSA] | Idem | Idem |
| Build | Tag `mobile-vX.Y.Z` → GitHub Actions: `flutter test`, AAB assinado (`versionName` X.Y.Z, `versionCode` = número da execução), envio à faixa de teste, release no Sentry; iOS em runner macOS ou Codemagic [VALIDAR custo] | + envio às lojas | Flavors |
| Configuração | `--dart-define=API_BASE_URL=https://api.{TRACKSYS_DOMAIN}`, mais os `--dart-define=FIREBASE_*` públicos do cliente FCM quando a T-012 entrar; nenhum segredo no binário. Workflow `mobile-release.yml` entregue pela T-010 | Idem | Idem |

1. Link único de download: `https://app.{TRACKSYS_DOMAIN}/baixar`, página estática do Caddy que redireciona para a loja pelo sistema do celular (usado nas mensagens de [11](11-onboarding-e-migracao.md) §7).
2. O app não pede localização do celular, câmera nem contatos; pede só notificações e biometria (`NSFaceIDUsageDescription`: "Usamos o Face ID para confirmar bloqueio e desbloqueio do veículo."). Declarações de privacidade das lojas seguem o [Anexo B](../anexos/B-juridico.md).
3. **Opção B (F2):** `flutter build --flavor <slug>` com ativos em `apps/mobile/assets/flavors/<slug>/`, operadora fixa (sem tela de escolha), publicado na conta da operadora com a Versix como membro (diretriz 4.2.6). Login de usuário sem membership na operadora do flavor: "Esta conta não pertence à {operadora}".
4. **Portal web do cliente (F2):** build Flutter Web do mesmo app em `https://meu.{TRACKSYS_DOMAIN}` [ADIADO PARA O F2: subdomínio `meu.`]; mapa, histórico, alertas, faturas e compartilhamento; sem comandos físicos até existir step-up web [ADIADO PARA O F2: WebAuthn como step-up do portal, decisão no F2].

## 13. Requisitos

### REQ-UX-001 — Tokens únicos e gerados
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** —
**Regra.** Cores, tamanhos e paradas do sheet DEVEM vir de `tokens.json` (§3). O arquivo Dart DEVE ser gerado e o CI DEVE falhar se estiver desatualizado. Hex de estado NÃO DEVE aparecer em `apps/mobile/lib/` nem em `apps/console/src/` fora dos arquivos de tokens.
**Aceite.** CT-UX-001 — Dado `moving` alterado para #10B982 em `tokens.json` sem rodar o gerador, Quando o CI roda `gen:dart-tokens` seguido de `git diff --exit-code`, Então falha; Dado `Color(0xFF10B981)` em `apps/mobile/lib/features/home/marker.dart`, Então a checagem `tokens-only` do CI falha citando o arquivo.

### REQ-UX-002 — Tela neutra e marca após o login
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** INV-07
**Regra.** O app NÃO DEVE mostrar marca, nome ou contato de operadora sem sessão válida e DEVE aplicar só a marca das operadoras das memberships do usuário, com cache e revalidação da §4.
**Aceite.** CT-UX-002 — Dado app recém-instalado, Quando abre, Então aparecem o logo TrackSys e a cor #3B82F6, sem o nome "Alfa"; Quando `dono.a1` entra, Então o cabeçalho mostra nome e logo da Alfa; Quando sai, Então o diretório de suporte não tem arquivo `brand-*` e a tela volta à neutra; Dado a cor da Alfa alterada no servidor, Quando o app reabre, Então `GET /api/v1/operator/brand` sai com `If-None-Match` e a cor nova aparece na troca de tela seguinte.

### REQ-UX-003 — Contraste mínimo com ajuste automático
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** —
**Regra.** Todo uso da cor da marca no app e no console DEVE passar por `resolveBrandColors` (§4); TS e Dart DEVEM passar os mesmos vetores.
**Aceite.** CT-UX-003 — Dado `primary_color = '#777777'`, Então `brandFill = #747474` com texto #FFFFFF (4,67:1) e `brandAccent = #919191` (4,64:1 sobre #1E293B); Dado #3B82F6, Então texto #0B0F17 (5,21:1) e acento #4F8EF7; Dado #FFD400, Então nenhum ajuste; os 5 vetores de `contrast-vectors.json` passam em Vitest e em `flutter test`.

### REQ-UX-004 — Estado de apresentação honesto
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N2 · **Invariantes:** INV-03, INV-04
**Regra.** App e console DEVEM derivar estado e selos pela tabela e precedência da §5 e recalcular a cada 10 s sem evento novo. Rastreador sem comunicação NÃO DEVE aparecer como estacionado. Cor NÃO DEVE ser o único sinal.
**Aceite.** CT-UX-004 — Os 12 vetores de `presentation-vectors.json` passam em TS e Dart; em particular, o vetor 9 nunca produz o texto "Estacionado" como estado principal e o vetor 7 produz `lost_moving` com cor #EF4444; Dado V1 `parked` com último contato às 15:14:01Z e nenhum evento novo, Quando o relógio chega a 15:20:01Z, Então aparece o selo "Última informação há 6 min".

### REQ-UX-005 — Idade da última posição válida
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N2 · **Invariantes:** INV-03
**Regra.** Lista, detalhe, sheet do mapa e console DEVEM mostrar "Última posição válida há {idade}" no formato da §5, atualizado a cada 1 s em tela visível.
**Aceite.** CT-UX-005 — Dado agora 15:20:00Z: `lastFixAt` 15:19:55Z → "agora"; 15:19:15Z → "há 45 s"; 15:07:00Z → "há 13 min"; 12:20:00Z → "há 3 h"; 12:05:00Z → "há 3 h 15 min"; 2026-10-18T22:10:00Z → "em 18/10 às 19:10"; Dado a tela aberta 15 s sem eventos a partir de "há 45 s", Então o texto vira "há 1 min" sem interação.

### REQ-UX-006 — Início com mapa ao vivo
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N2 · **Invariantes:** INV-04, INV-07
**Regra.** A02 DEVE usar SSE só em primeiro plano, descartar revisão menor ou igual à exibida e animar o marcador conforme a §5.
**Aceite.** CT-UX-006 — Dado V1 exibido na revisão 1048577, Quando chega `vehicle.state` 1048512, Então o marcador não se move; Quando chega 1048601 com posição 120 m adiante, Então o marcador chega ao destino em ≤ 1.000 ms e para; com "Remover animações" ligado, Então salta; Dado o app em segundo plano, Então a conexão SSE fecha em ≤ 5 s e, ao voltar, reabre e recebe o snapshot.

### REQ-UX-007 — Detalhe do veículo
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N2 · **Invariantes:** INV-03
**Regra.** A03 DEVE mostrar ignição, alimentação e relé com o valor desconhecido explícito.
**Aceite.** CT-UX-007 — Dado `ignition = null` e `powerState = 'unknown'`, Então aparecem "Ignição: desconhecida" e "Alimentação: desconhecida" e nenhum "Desligada"; Dado `powerState = 'battery'`, Então "Alimentação: bateria interna" com ícone e cor idle.

### REQ-UX-008 — Histórico do dia
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N2 · **Invariantes:** INV-03, INV-06
**Regra.** A04 e C07 DEVEM usar o dia BRT, marcar lacunas, qualificar a distância e avisar dias anteriores ao 1º vínculo.
**Aceite.** CT-UX-008 — Dado 20/10/2026 escolhido, Então a requisição usa `from=2026-10-20T03:00:00Z&to=2026-10-21T03:00:00Z`; Dado a resposta do exemplo de [09](09-api-e-contratos.md) §9.4 (lacuna de 11:03:00Z a 11:09:40Z), Então o trecho entre esses pontos fica tracejado com "Sem dados 08:03–08:09" e o resumo começa com "≥"; Dado `gaps` vazio com pontos às 10:58:12Z e 11:02:30Z, Então trecho contínuo; Dado `nextCursor` preenchido, Então o app busca a página seguinte antes de desenhar o resumo; Dado 1º vínculo em 22/10/2026 e o dia 21/10 escolhido, Então "Histórico disponível a partir de 22/10/2026".

### REQ-UX-009 — Alerta a partir do push em até 2 toques
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N2 · **Invariantes:** INV-07
**Regra.** Tocar a notificação DEVE abrir o detalhe do alerta; o mapa completo DEVE estar a 1 toque dali.
**Aceite.** CT-UX-009 — Dado push `sos` de V1 com o app encerrado, Quando `dono.a1` toca a notificação, Então abre o detalhe com o título "Pânico acionado" (1 toque) e "Ver no mapa" abre o mapa com V1 centralizado (2 toques); Dado link para alerta fora do escopo, Então "Alerta não encontrado", sem dados; Dado sessão expirada, Então login e, depois, o detalhe do alerta.

### REQ-UX-010 — Modo vigilância no app
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** INV-03
**Regra.** A06 DEVE seguir [07](07-alertas-e-tempo-real.md) §5 e mapear os erros para os textos da tabela.
**Aceite.** CT-UX-010 — Dado V1 estacionado com fix válido, Quando `dono.a1` ativa às 00:14:00Z, Então o mapa mostra círculo de 150 m e "Vigilância ativa desde 21:14"; Dado 409 `WATCH_MODE_VEHICLE_ON`, Então "Desligue o veículo para ativar a vigilância".

### REQ-UX-011 — Falar com a central e navegar até o veículo
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N2 · **Invariantes:** —
**Regra.** A07 e A08 DEVEM gerar exatamente os links da §6.
**Aceite.** CT-UX-011 — Dado `supportWhatsapp` +5586999990000, V1 "Gol prata" TST1A23 e último fix (−5,089211, −42,801892) às 18:14 BRT, Quando toca "Falar com a central", Então abre `https://wa.me/5586999990000?text=…` cujo texto decodificado é "Olá, Alfa. Sou Dono A1. Veículo Gol prata, placa TST1A23. Última posição (18:14): https://maps.google.com/?q=-5.089211,-42.801892"; Quando escolhe Waze, Então `https://waze.com/ul?ll=-5.089211,-42.801892&navigate=yes`; Dado fix de há 25 min, Então antes aparece "Posição de há 25 min. O veículo pode ter se movido."

### REQ-UX-012 — Notificações
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N2 · **Invariantes:** —
**Regra.** A09 DEVE criar os canais, explicar antes de pedir permissão, tratar recusa e mostrar preferências com `locked` e `available`.
**Aceite.** CT-UX-012 — Dado Android 14 recém-instalado, Quando o usuário entra, Então a explicação aparece antes do diálogo `POST_NOTIFICATIONS` e existem os canais `alerts_high` (importância alta) e `alerts_info`; Quando nega, Então o início mostra "Alertas desligados neste celular"; Dado `sos`, Então interruptor travado "Sempre ativo"; Dado perfil sem `power_cut_alarm`, Então `power_cut` aparece "Indisponível neste rastreador".

### REQ-UX-013 — Desempenho do app
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** —
**Regra.** O app DEVE cumprir cold start p90 ≤ 2.500 ms e veículo no mapa p90 ≤ 3.000 ms em 4G, medidos como na §8; no F1 a medida bloqueia a publicação.
**Aceite.** CT-UX-013 — Dado build release no aparelho de referência, Quando roda 20 vezes `adb shell am start -S -W br.com.versix.tracksys/.MainActivity`, Então o p90 de `TotalTime` ≤ 2.500 ms; Dado 4G real e 20 aberturas, Então o p90 do span `map.first_vehicle` ≤ 3.000 ms; as duas medidas constam do PR da versão.

### REQ-UX-014 — Estabilidade
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** —
**Regra.** Versão com sessões sem crash < 99,5% (7 dias, ≥ 200 sessões) NÃO DEVE passar de 20% na loja.
**Aceite.** CT-UX-014 — Dado a versão 1.2.0 com 1.000 sessões em 7 dias e 6 com crash (99,4%), Quando o fundador aplica a regra da §8 ao painel de release health do Sentry, Então a versão fica em 20% na loja e abre-se issue P0; com 4 crashes (99,6%), Então a versão segue para 100%.

### REQ-UX-015 — Acessibilidade
**Fase:** F0 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** —
**Regra.** App e console DEVEM cumprir os 6 itens de acessibilidade da §8.
**Aceite.** CT-UX-015 — Dado TalkBack no início, Quando o foco chega ao card de V1, Então lê "Gol prata, placa TST1A23, Em movimento, 48 quilômetros por hora, última posição válida há 12 segundos"; Dado fonte em 200% em 360 × 800 dp, Então estado e idade aparecem sem reticências; os testes de widget de A02, A03 e A11 passam em `androidTapTargetGuideline`, `labeledTapTargetGuideline` e `textContrastGuideline`.

### REQ-UX-016 — Offline somente leitura
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N2 · **Invariantes:** INV-03, INV-08
**Regra.** Sem rede, o app DEVE exibir o cache com a faixa global, calcular estados com agora = `syncedAt`, desativar ações que escrevem e ignorar cache com mais de 7 dias.
**Aceite.** CT-UX-016 — Dado V1 `parked` com último fix às 15:00:00Z, sincronizado às 15:00:00Z, e o celular em modo avião, Quando o app reabre às 15:40:00Z, Então mostra "Sem internet no celular · dados de 12:00", V1 continua `parked` (não `offline`), a linha diz "Última posição válida há 40 min" e Vigilância e Bloquear estão desativados; Dado cache de 8 dias, Então não é exibido.

### REQ-UX-017 — Disponibilidade e confirmação do comando
**Fase:** F1 · **Prioridade:** P0 · **Risco:** N0 · **Invariantes:** INV-08, INV-10
**Regra.** A11 DEVE seguir a §7 itens 1–4: botão só com `available = true`, `effectText` literal, deslizar até 90% e biometria com chave do aparelho.
**Aceite.** CT-UX-017 — Dado `block.available = false` com `CUT_POINT_MISSING` (código de [09](09-api-e-contratos.md) §3), Então o detalhe não tem "Bloquear" e mostra "Bloqueio pelo app indisponível neste veículo. Fale com a central."; Dado `available = true`, Então a confirmação mostra o `effectText` recebido sem alteração; Quando solta a alça a 80%, Então nenhuma requisição; Quando desliza até o fim e cancela a biometria, Então 0 requisições a `/commands` e "Bloqueio não enviado"; Quando confirma, Então 1 POST com `Idempotency-Key` e `stepUp.kind = "device_key"`.

### REQ-UX-018 — Estados do comando com textos distintos
**Fase:** F1 · **Prioridade:** P0 · **Risco:** N0 · **Invariantes:** INV-03, INV-08
**Regra.** App e console DEVEM usar os títulos da tabela da §7; UNKNOWN NÃO DEVE parecer bloqueado; o relé observado DEVE aparecer separado.
**Aceite.** CT-UX-018 — Dado `block` em REQUESTED, ARMED (`awaiting_speed`, teto 40), AWAITING_CONFIRMATION e UNKNOWN, Então os títulos são "Pedido registrado", "Aguardando condição segura — veículo acima de 40 km/h", "Aguardando confirmação do rastreador" e "Não foi possível confirmar. O veículo pode ou não estar bloqueado"; Dado UNKNOWN e `relayState = 'blocked'` observado há 3 h, Então o selo mostra "Relé: bloqueado · observado há 3 h" fora do cartão.

### REQ-UX-019 — Nunca enfileirar comando offline
**Fase:** F1 · **Prioridade:** P0 · **Risco:** N0 · **Invariantes:** INV-08
**Regra.** O app DEVE seguir a §7 item 5: sem reenvio automático, sem fila em disco, sem envio ao reabrir.
**Aceite.** CT-UX-019 — Dado modo avião, Quando abre a confirmação, Então a alça está desativada com "Sem internet. O pedido não pode ser enviado. Ligue para a central: (86) 99999-0000"; Dado POST sem resposta de rede, Quando a rede volta 2 min depois, Então 0 POST novo e 1 `GET /api/v1/vehicles/V1/commands?limit=1`; Quando o app é encerrado e reaberto, Então 0 POST a `/commands`.

### REQ-UX-020 — Ocorrência no app
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-08
**Regra.** A13 DEVE abrir a ocorrência sem criar comando e oferecer 190, central, bloqueio (se disponível), compartilhamento e BO.
**Aceite.** CT-UX-020 — Dado V1 sem ocorrência, Quando `dono.a1` confirma "Fui roubado", Então 1 POST de ocorrência, 0 POST de comando e a tela mostra "Ligar 190", "Falar com a central" e o campo BO; Quando grava BO "2026/123456", Então ele aparece na linha do tempo; com 41 caracteres, Então "Até 40 caracteres".

### REQ-UX-021 — Faturas e PIX
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-09, INV-12
**Regra.** A14 DEVE formatar centavos em reais, copiar o `pix_payload` exato e NÃO DEVE associar fatura a bloqueio.
**Aceite.** CT-UX-021 — Dado fatura de `value_cents = 4990` vencida em 10/11/2026, Então aparece "R$ 49,90" e "Venceu em 10/11/2026. Pague com PIX ou fale com a central." e nenhum texto da tela contém "bloque"; Quando toca "Copiar código PIX", Então a área de transferência tem o `pix_payload` exato.

### REQ-UX-022 — Chamar guincho
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-07
**Regra.** A15 DEVE pedir consentimento no 1º uso e registrar a indicação antes de abrir o canal do parceiro.
**Aceite.** CT-UX-022 — Dado parceiro "Guincho Rápido" da Alfa e consentimento ausente, Quando `dono.a1` toca "Chamar guincho", Então aparece o texto de consentimento; Quando aceita e escolhe WhatsApp, Então `POST /api/v1/referrals` recebe 201 antes de abrir `https://wa.me/…` com TST1A23 e o link da posição; Dado sem internet, Então mostra o telefone do parceiro e 0 indicações.

### REQ-UX-023 — Compartilhar localização
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-07
**Regra.** A16 DEVE oferecer 1 h, 4 h e 24 h, listar links ativos e revogar.
**Aceite.** CT-UX-023 — Dado `dono.a1`, Quando cria link de 4 h às 14:00:00Z, Então a folha do sistema abre com a URL da API e a lista mostra "Expira às 15:00"; Quando revoga, Então o link sai da lista e a API devolve `revokedAt` preenchido.

### REQ-UX-024 — Cercas no app
**Fase:** F1 · **Prioridade:** P2 · **Risco:** N2 · **Invariantes:** INV-07
**Regra.** A17 DEVE travar o raio em 100–5.000 m e o total em 10 cercas por veículo.
**Aceite.** CT-UX-024 — Dado 10 cercas em V1, Quando tenta criar a 11ª, Então "Limite de 10 cercas por veículo" e 0 requisições; Dado raio arrastado para 80 m, Então fica em 100 m.

### REQ-UX-025 — Console: cadastro e vínculo com ponto de corte
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N1 · **Invariantes:** INV-10, INV-07
**Regra.** C03–C06 DEVEM validar os formatos de [04](04-dominio-e-dados.md) e exigir resposta explícita sobre o relé; a API DEVE exigir a chave `cutPoint`.
**Aceite.** CT-UX-025 — Dado o vínculo sem resposta em "Relé de bloqueio instalado?", Então "Salvar" fica desativado; com "Sim" e sem ponto de corte, Então "Escolha o ponto de corte"; Dado `POST /api/v1/device-assignments` para V1 sem a chave `cutPoint`, Então 422 `VALIDATION_FAILED` com `errors[0].path = "cutPoint"`; com `"cutPoint": null`, Então 201 e o detalhe mostra "Sem bloqueio instalado"; Dado placa "tst-1a23", Então grava TST1A23.

### REQ-UX-026 — Console: mapa da operadora e histórico
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N2 · **Invariantes:** INV-07, INV-04
**Regra.** C02 e C07 DEVEM usar a derivação da §5 e dividir o SSE em conexões de até 200 veículos.
**Aceite.** CT-UX-026 — Dado `agente.alfa` com 250 veículos, Quando abre `/mapa`, Então existem 2 conexões SSE (200 e 50), 250 marcadores e nenhum veículo da Beta; Dado o filtro "Sem comunicação", Então só aparecem veículos `offline` e `lost_moving`.

### REQ-UX-027 — Console F1: telas operacionais e papéis
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N2 · **Invariantes:** INV-07
**Regra.** C08–C19 DEVEM seguir o menu por papel da §9; o pedido de comando no console DEVE exigir TOTP ≤ 5 min e motivo ≥ 10 caracteres.
**Aceite.** CT-UX-027 — Dado `agente.alfa`, Quando abre `/usuarios`, Então "Sem permissão" e a API responde 403; Dado motivo "furto" (5 caracteres), Então "Motivo com pelo menos 10 caracteres" e 0 POST; Dado `installer`, Então o menu mostra só Rastreadores, Vínculos e Veículos.

### REQ-UX-028 — Atendimento
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-07
**Regra.** O módulo `support` DEVE implementar a §11 com contexto automático, auditoria e 403 para papéis do cliente.
**Aceite.** CT-UX-028 — Dado alerta `signal_lost_moving` de V1, Quando `agente.alfa` clica "Abrir atendimento", Então existe `ticket` com `alert_id`, `vehicle_id` e `tenant_id` de A1, `status = 'open'` e `audit_log` `ticket.create`; Quando `dono.a1` chama `GET /api/v1/tickets`, Então 403; Quando `admin.beta` busca o id, Então 404; `PATCH` com `If-Match` antigo → 412.

### REQ-UX-029 — Visão da equipe de busca
**Fase:** F1 · **Prioridade:** P1 · **Risco:** N1 · **Invariantes:** INV-07, INV-08
**Regra.** C19 DEVE seguir a §10.
**Aceite.** CT-UX-029 — Dado ocorrência aberta em V1 e `busca.alfa` (`search_team`) no Chrome Android a 390 px, Quando abre `/busca/{id}`, Então vê o mapa em tela cheia com V1, a idade da posição em fonte ≥ 20 px e "Navegar"; Quando abre `/veiculos/V2` (sem ocorrência), Então 404; Quando a ocorrência fecha, Então aparece "Ocorrência encerrada" e nenhuma posição chega após 5 s.

### REQ-UX-030 — Distribuição F0/F1
**Fase:** F0 · **Prioridade:** P0 · **Risco:** N2 · **Invariantes:** —
**Regra.** O build e a distribuição DEVEM seguir a §12: teste fechado e TestFlight no F0, lojas no F1, sem segredo no binário.
**Aceite.** CT-UX-030 — Dado a tag `mobile-v0.3.0`, Quando o workflow roda, Então gera AAB com `versionName 0.3.0` e `versionCode` igual ao número da execução, envia à faixa de teste fechado e cria a release 0.3.0 no Sentry; `strings` sobre o AAB não encontra `FCM_SERVICE_ACCOUNT` nem chave privada.

### REQ-UX-031 — Portal web e opção B
**Fase:** F2 · **Prioridade:** P2 · **Risco:** N2 · **Invariantes:** INV-07
**Regra.** O portal web e o app dedicado DEVEM reutilizar o código do app e seguir a §12 itens 3 e 4.
**Aceite.** CT-UX-031 — Dado o portal web, Quando `dono.a1` entra, Então vê mapa, histórico e faturas e não há "Bloquear"; Dado o build `--flavor lider`, Quando entra um usuário sem membership na Lider, Então "Esta conta não pertence à Lider" e nenhuma sessão é criada.
