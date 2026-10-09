# T-009 — App: login, lista, mapa ao vivo com estados honestos e marca básica da operadora

| Campo | Valor |
|---|---|
| Fase | F0 (semana S2: 14–20/10/2026; marco de 20/10: `dono.a1` vê V1 no app) |
| Requisitos | REQ-UX-001, REQ-UX-002, REQ-UX-003, REQ-UX-004 e REQ-UX-005 (lado Dart), REQ-UX-006, REQ-UX-007, REQ-UX-013 (medida informativa no F0), REQ-UX-015 (A02 e A03), REQ-UX-016; REQ-SEG-003 (lado do app) |
| Invariantes | INV-03, INV-04, INV-07, INV-08 (offline sem ação que escreve), INV-12 |
| Risco de revisão | N2 |
| Depende de | T-004 (cliente Dart `tracksys_api`; `build_runner` roda no app), T-006 (login Bearer, `GET /api/v1/me`, `sign-out`). Integração real com `GET /api/v1/vehicles` (estado) e `GET /api/v1/stream` da T-008, que corre na mesma semana: plano B na decisão 1 |
| Estimativa | 3 sessões de agente (1: projeto, tokens, UX puro, sessão e marca; 2: SSE, Início e Detalhe; 3: offline, acessibilidade, testes e CI) |
| Bloqueado por decisão | nenhuma para Android e desenvolvimento. DEC-03 só para instalar no iPhone por TestFlight (distribuição é da T-010). DEC-04 não bloqueia (`API_BASE_URL` por `--dart-define`) |

## Objetivo

Criar o app Flutter único (`apps/mobile`, [ADR-007](../docs/adr/ADR-007-app-unico-flutter-marca-dinamica.md)) com o que o cliente final compara primeiro com o tracker-net: entrar com e-mail e senha, ver os próprios veículos numa lista e num mapa ao vivo que mostra idade e qualidade do dado, abrir o detalhe com o desconhecido explícito e reconhecer a marca da operadora (nome, logo e cor com contraste garantido). O app funciona sem rede em modo leitura com o último dado e a idade visível. Ao fim, `dono.a1` vê V1 se mover sem recarregar e `dono.a2` não vê nada de V1.

## Contexto obrigatório

- [10 §1–§6, §8, §12](../docs/spec/10-apps-e-ux.md): caminhos, princípios, tokens, marca, estados honestos, telas A01–A03 e A10, desempenho, acessibilidade, offline, identificador e versões mínimas.
- [07 §11](../docs/spec/07-alertas-e-tempo-real.md) itens 1–5: snapshot, reconexão, `close`, campos e uso só em primeiro plano.
- [08 §2](../docs/spec/08-identidade-e-seguranca.md): sessão `app` só por Bearer (30 dias, renovação ≤ 1 vez/24 h), token fora de URL e log.
- [09 §2, §6, §9.1](../docs/spec/09-api-e-contratos.md): `GET /api/v1/me`, `GET /api/v1/operator/brand`, item de veículo.
- Cartão T-008: contratos `VehicleItem`/`VehicleStateEvent`, `presentationOf` em TS e os vetores que este cartão reproduz em Dart.

## Escopo — fazer

1. Projeto Flutter `apps/mobile` (seção 1) e preparação do cliente gerado (seção 2).
2. Tokens: gerador `gen:dart-tokens` e checagem `check:tokens-only` (seção 3).
3. UX puro em Dart, `brand-contrast.ts` e `contrast-vectors.json` (seção 4).
4. API: `GET /api/v1/operator/brand`, `brand` em `/me` e script `seed:brand` (seção 5).
5. Sessão: A01 Entrada e login, escolha de operadora, A10 Conta com "Sair" (seção 6).
6. Marca dinâmica com cache e revalidação (seção 7).
7. Tempo real: cliente SSE, estado e ciclo de vida (seção 8).
8. A02 Início (mapa + lista) e A03 Detalhe do veículo (seção 9).
9. Offline somente leitura (seção 10) e Sentry opcional com o span `map.first_vehicle` (seção 11).
10. Job `mobile` no CI (seção 12) e testes de aceite em `tests/acceptance/T-009/`.

## Fora do escopo

- A04 Histórico, A07 "Falar com a central", A08 "Navegar até o veículo" e o workflow de distribuição (T-010).
- Push, canais, A09 e `firebase_messaging` (T-012). A05 Alertas e A06 Modo vigilância também são da T-012 [ADOTADO NA v2.0]; este cartão só deixa a rota `/inicio?veiculo=` e o A03 prontos para ela acrescentar o interruptor.
- Comandos, `local_auth` e chave do aparelho (F1). `PUT /api/v1/operator/brand` e tela C13 (F1). Tema claro e flavors (F2).
- Pedir localização, câmera ou contatos do celular (proibido, 10 §12 item 2).

## Arquivos a criar/alterar

```
criar    apps/mobile/** (flutter create; pubspec.yaml, analysis_options.yaml, android/, ios/, assets/brand/tracksys.png)
criar    apps/mobile/lib/{main,app,config,router}.dart
gerar    apps/mobile/lib/theme/tokens.g.dart ; criar apps/mobile/lib/theme/{app_theme,brand_theme}.dart
criar    apps/mobile/lib/ux/{presence,presentation_state,age_format,brand_contrast,brt}.dart
criar    apps/mobile/lib/api/{api_client,request_id,sse_parser,sse_client}.dart  apps/mobile/lib/api/models/{vehicle_state_event,alert_event}.dart
criar    apps/mobile/lib/auth/{token_store,session_controller}.dart
criar    apps/mobile/lib/brand/{brand_repository,brand_cache,logo_loader,initials}.dart
criar    apps/mobile/lib/cache/data_cache.dart  apps/mobile/lib/live/{live_store,live_controller,marker_animator,connectivity_state}.dart
criar    apps/mobile/lib/features/{login/login_screen,login/operator_picker_screen,home/home_screen,home/vehicle_sheet,home/vehicle_card,home/live_map,home/marker_icons,vehicle/vehicle_detail_screen,account/account_screen}.dart
criar    apps/mobile/lib/widgets/{state_chip,badge_row,global_banner,age_text,brand_header}.dart
criar    apps/mobile/tool/prepare_api.sh  apps/mobile/test/** (unitários, não congelados)
criar    packages/contracts/scripts/gen-dart-tokens.ts  scripts/check-tokens-only.ts
alterar  packages/contracts/package.json (gen:dart-tokens)  package.json (check:tokens-only)  .gitignore  .github/workflows/ci.yml
criar    packages/contracts/design/tokens.json (só se a T-008 ainda não criou; conteúdo exato de 10 §3)
criar    packages/domain/src/ux/brand-contrast.ts  packages/testkit/fixtures/ux/contrast-vectors.json
criar    packages/contracts/src/http/brand.ts ; alterar packages/contracts/src/routes/{types,registry}.ts (304; operator-brand.get)
criar    apps/api/src/brand/{brand.module,brand.controller,brand.repo}.ts ; alterar apps/api/test/scope-fixtures.ts
criar    packages/db/scripts/seed-brand.ts ; alterar packages/db/package.json (seed:brand)
criar    tests/acceptance/T-009/{brand-api,tokens,contrast}.test.ts
criar    tests/acceptance/T-009/mobile/pubspec.yaml  tests/acceptance/T-009/mobile/test/*_test.dart
```

## Especificação detalhada

### (1) Projeto

- `flutter create --org br.com.versix --project-name tracksys_mobile --platforms android,ios apps/mobile`; depois `applicationId` e `namespace` = `br.com.versix.tracksys` em `android/app/build.gradle.kts`, `MainActivity.kt` em `android/app/src/main/kotlin/br/com/versix/tracksys/` (a T-012 edita esse arquivo), `PRODUCT_BUNDLE_IDENTIFIER = br.com.versix.tracksys`. Nome exibido "TrackSys"; `minSdk 26`; iOS 15.0; só retrato; `Info.plist` sem chaves de localização, câmera ou contatos.
- Dependências (versão estável mais recente no dia, registrada no PR; nenhuma outra): `maplibre_gl`, `dio`, `go_router`, `flutter_secure_storage`, `path_provider`, `intl`, `sentry_flutter`, `flutter_localizations` (SDK), `tracksys_api: { path: ../../packages/contracts/generated/dart }`; dev: `flutter_lints`. Versão do Flutter fixada em `environment.flutter` do `pubspec.yaml`.
- `config.dart` (`String.fromEnvironment`): `API_BASE_URL` obrigatório (`https://`; `http://` só em debug), `WEB_BASE_URL` (link de termos), `APP_VERSION` (padrão `0.0.0-dev`), `SENTRY_DSN` (vazio = desligado), `MAP_STYLE_URL` (padrão `https://tiles.openfreemap.org/styles/liberty`). Nenhum segredo no binário.
- Rotas (`go_router`): `/entrar`, `/operadora`, `/inicio` (aceita `?veiculo=<uuid>`: centraliza e abre o card), `/veiculos/:id`, `/conta`. Sem sessão → `/entrar` guardando o destino; após o login, volta a ele. Tema escuro único, `pt_BR`.

### (2) Cliente gerado

- `tool/prepare_api.sh`: `cd packages/contracts/generated/dart && dart pub get && dart run build_runner build --delete-conflicting-outputs`. Os `*.g.dart`, `.dart_tool/` e `pubspec.lock` dessa pasta entram no `.gitignore` (o `contracts:check` da T-004 continua limpo).
- `api_client.dart`: um `Dio` com `baseUrl`, timeouts de 10 s (conexão) e 15 s (leitura) fora do SSE e interceptadores: `Authorization: Bearer <token>`, `X-App-Version`, `X-Request-Id` (UUID v4 de `Random.secure()`), `X-Operator-Id` quando escolhido. 401 em rota autenticada → `SessionController.expire()`. Nenhum log com token, e-mail, coordenada ou corpo de resposta.
- Eventos SSE não estão no OpenAPI: `VehicleStateEvent` e `AlertEvent` à mão em `api/models/`, campo a campo do contrato da T-008; enum desconhecido vira `unknown` (09 §2); evento inválido é descartado com breadcrumb sem dados pessoais.

### (3) Tokens

- `gen-dart-tokens.ts` (`pnpm --filter @tracksys/contracts gen:dart-tokens`) valida `tokens.json` com Zod e grava `apps/mobile/lib/theme/tokens.g.dart` de forma determinística: cabeçalho `// GERADO por pnpm --filter @tracksys/contracts gen:dart-tokens. Não edite.`, `abstract final class TsColors { static const Color moving = Color(0xFF10B981); … }` (uma constante por chave de `color`, na ordem do JSON), `TsMarker` (`sizePx`, `outlinePx`, `outline`, `interpolationMaxMs`), `TsSheet.snaps = <double>[0.15, 0.45, 0.90]`, `TsTouch.minDp = 48`. Exporta `renderDartTokens(tokens): string`.
- `scripts/check-tokens-only.ts` (`pnpm check:tokens-only`) varre `apps/mobile/lib/**/*.dart` e `apps/console/src/**/*.{ts,tsx,css}`, exceto `apps/mobile/lib/theme/tokens.g.dart`, procurando qualquer cor de `tokens.json` como `#RRGGBB` ou `0xFFRRGGBB` (sem diferenciar maiúsculas); achou → sai com 1 e lista `arquivo:linha`. Exporta `findTokenHexViolations(files, tokens)`.

### (4) UX puro em Dart e contraste

- `lib/ux/*.dart` reproduzem `presenceFrom`, `presentationOf`, `formatAge`, `formatAgeSpoken` e as funções BRT da T-008 com saída idêntica sobre os mesmos vetores (`presentation-vectors.json`, `age-vectors.json`), lidos por caminho relativo. Limiar inclusivo e selo `gps_stale` relativo ao último contato, como nas decisões 3 e 4 da T-008.
- `resolveBrandColors(primaryHex)` em Dart e em `packages/domain/src/ux/brand-contrast.ts` → `{ brandFill, onBrand, brandAccent, adjusted }`: luminância WCAG 2.2 (sRGB, limiar 0,04045); contraste (Lmaior + 0,05)/(Lmenor + 0,05); conversão HSL do CSS Color 4; no passo k, a cor é recalculada **a partir do HSL original** com L ∓ 0,01·k (limitado a [0, 1]) e canais arredondados ao inteiro (meio para cima); regras de 10 §4. `adjusted = true` se `brandFill` ou `brandAccent` ≠ primária.
- `contrast-vectors.json` (conferido com essa implementação):

```json
[ { "primary": "#3B82F6", "brandFill": "#3B82F6", "onBrand": "#0B0F17", "onBrandRatio": 5.21, "brandAccent": "#4F8EF7", "accentRatio": 4.56 },
  { "primary": "#777777", "brandFill": "#747474", "onBrand": "#FFFFFF", "onBrandRatio": 4.67, "brandAccent": "#919191", "accentRatio": 4.64 },
  { "primary": "#E30613", "brandFill": "#E30613", "onBrand": "#FFFFFF", "onBrandRatio": 4.88, "brandAccent": "#FA555E", "accentRatio": 4.55 },
  { "primary": "#FFD400", "brandFill": "#FFD400", "onBrand": "#0B0F17", "onBrandRatio": 13.40, "brandAccent": "#FFD400", "accentRatio": 10.22 },
  { "primary": "#0B3D91", "brandFill": "#0B3D91", "onBrand": "#FFFFFF", "onBrandRatio": 10.04, "brandAccent": "#528EF2", "accentRatio": 4.53 } ]
```

### (5) API: marca da operadora

| Rota (id) | Permissão | Comportamento |
|---|---|---|
| `GET /api/v1/operator/brand` (`operator-brand.get`) | sessão (`permission: null`) | Sob `withContext(…, { readOnly: true })`: `SELECT o.display_name, b.* FROM app.operator o LEFT JOIN app.operator_brand b ON b.operator_id = o.id WHERE o.id = app.current_operator_id()`. 200 `{ displayName, logoUrl, primaryColor, secondaryColor, supportWhatsapp, supportPhone }` + `ETag: "u<microssegundos de b.updated_at>"`. Sem linha de marca: `displayName` da operadora, `primaryColor` `#3B82F6`, demais `null`, `ETag: "u0"`. `If-None-Match` igual → 304 sem corpo. Sem contexto → 404 |

- `RouteDef.responses` aceita 304 (alteração aditiva no tipo da T-004). `BrandDto` em `packages/contracts/src/http/brand.ts`; `GET /api/v1/me` usa o mesmo `loadBrand(client)` no campo `brand` (se a T-006 já o preenche, só reutilize o DTO).
- `seed:brand` (10 §4 item 7): `pnpm --filter @tracksys/db seed:brand -- --operator <uuid> --name "Lider Rastreamento" --color "#E30613" [--secondary "#RRGGBB"] [--logo-url https://…] [--whatsapp +5586999990000] [--phone +558632220000]`. Zod com as mesmas regras dos `CHECK` de `app.operator_brand` (T-001); executa como `tracksys_app` com `{ scope: 'operator', operatorId }` (nunca `tracksys_owner`): `INSERT … ON CONFLICT (operator_id) DO UPDATE SET …, updated_at = now()`. Imprime `brandFill`, `onBrand` e `brandAccent` resolvidos e "Ajustamos a cor para garantir leitura" quando `adjusted`.

### (6) Sessão (A01, escolha de operadora, A10)

- **A01 `/entrar`**: tela neutra (logo TrackSys, `brandDefault`, sem nome, logo ou contato de operadora); e-mail, senha, "Entrar", "Esqueci minha senha". `POST /api/v1/auth/sign-in/email` → 200: token do header `set-auth-token` salvo **só** em `flutter_secure_storage` (chave `session_token`; iOS `first_unlock_this_device`); 401 → "E-mail ou senha incorretos"; 429 → "Muitas tentativas. Tente de novo em {n} min" (`Retry-After`); erro de rede → "Sem internet. Verifique a conexão."; `twoFactorRedirect = true` → "Esta conta exige verificação em duas etapas. Use o console." sem seguir. "Esqueci minha senha" → `POST /api/v1/auth/request-password-reset` e sempre "Se o e-mail estiver cadastrado, enviaremos um link." O 1º acesso é pelo link de convite (página web da T-006/T-007); o app só entra.
- **Operadora**: `/me` com 400 `OPERATOR_SELECTION_REQUIRED` → `/operadora` lista as operadoras da resposta; a escolhida vai para o armazenamento seguro e para `X-Operator-Id`. `/me` com `memberships` vazio → "Sua conta não tem veículos ativos. Fale com a sua operadora." + "Sair".
- **Expiração** (401 ou `close` `session_expired`): vai a `/entrar` mantendo caches; outro usuário entrando apaga os caches do anterior. **Revogação** (`close` `session_revoked`): igual a "Sair".
- **A10 `/conta`**: nome, e-mail, operadora, versão (`APP_VERSION`), "Termos e privacidade" (`{WEB_BASE_URL}/privacidade`), "Sair". Sair: `POST /api/v1/auth/sign-out` (falha de rede ignorada) → executa os ganchos `beforeLogout` (a T-012 registra o `DELETE` do token de push) → apaga token, operadora, `brand-*`, `logo-*`, `cache-*` → `/entrar`.

### (7) Marca no app

1. Login: `brand` de `/me` → `brand-<operatorId>.json` (`{ etag: null, brand }`) no diretório de suporte; logo baixado para `logo-<operatorId>.png|webp`.
2. Abertura com sessão: `main()` lê o JSON de marca antes de `runApp` (1º quadro já com a marca) e, em segundo plano, `GET /api/v1/operator/brand` com `If-None-Match` (quando houver `etag`). 304 → nada; 200 → grava e guarda como pendente; a marca pendente vale na **próxima troca de rota** (observer do `go_router`), nunca no meio da tela.
3. Uso: `brandFill`/`onBrand` em botões primários e cabeçalho, `brandAccent` em ícones, links e aba selecionada; `secondaryColor` só decora. Cores de estado e textos de segurança nunca mudam. Cabeçalho (`brand_header.dart`): logo de 32 dp + `displayName`.
4. `logo_loader.dart`: `Dio` **separado, sem interceptadores** (o Bearer nunca vai a host de terceiro); só `https://`; aborta acima de 262.144 bytes; `Content-Type` `image/png` ou `image/webp`; decodifica e recusa acima de 512 × 512 px. Falhou → iniciais sobre `brandFill` com `onBrand` (uma palavra → 1ª letra; duas ou mais → 1ª letra das duas primeiras: "Lider Rastreamento" → "LR").
5. Ordem de entrega dentro da tarefa: nome → cor → logo, para que o corte 1 do plano de corte ([02 §2.4](../docs/spec/02-escopo-e-fases.md)) retire só a cauda.

### (8) Tempo real

- `sse_parser.dart`: `utf8.decoder` + divisor de linhas sobre o stream do `dio` (`ResponseType.stream`); trata `retry:`, `event:`, `id:`, `data:` multilinha, comentários (`: keep-alive <RFC 3339>` atualiza `syncedAt`), LF e CRLF, caractere UTF-8 partido entre blocos.
- `sse_client.dart`: `GET /api/v1/stream?vehicleIds=<ids da lista, até 200>` com `Accept: text/event-stream` e `Last-Event-ID` (último `id` recebido). Lista com mais de 200 (conta de equipe) → transmite os 200 primeiros da ordem da lista e mostra "Atualização ao vivo limitada a 200 veículos". `close` `replaced`/`lifetime`/`overflow`/`shutdown` e queda de rede → espera de 1 s dobrando até 30 s, ± 20%.
- `live_store.dart` (puro): mesmas regras do redutor da T-008 (só `isPrimary = true`; descarta mesma `(vehicleId, deviceId)` com revisão ≤ exibida; `deviceId` diferente substitui; `alert` por `alertId` com `closed` > `acknowledged` > `open`).
- `live_controller.dart`: `WidgetsBindingObserver`; `paused`/`hidden`/`detached` → cancela o stream na hora (meta ≤ 5 s, REQ-UX-006); `resumed` → reabre e recebe o snapshot; lista recarregada se a última leitura tiver mais de 60 s. Apresentação recalculada a cada 10 s; `AgeText` com relógio de 1 s só quando visível (`TickerMode`).
- `marker_animator.dart` (puro, relógio injetado): nova revisão com posição diferente → interpolação linear de até `TsMarker.interpolationMaxMs` (1.000 ms) a partir da posição exibida no instante; sem extrapolação; `MediaQuery.disableAnimationsOf(context)` → salto.

### (9) A02 Início e A03 Detalhe

- **A02 `/inicio`**: `GET /api/v1/vehicles?limit=200` (todas as páginas) + SSE. `live_map.dart` (MapLibre, estilo de `MAP_STYLE_URL`) atrás da interface `LiveMapController` (os testes usam um falso). Ícones por estado gerados com `dart:ui` (36 dp, contorno branco de 2 dp, tracejado em `offline`/`lost_moving`, seta girada por `courseDeg` só em `moving`, anel `danger` com selo `alert`). Enquadramento: 1 veículo com posição → centro com zoom 16; 2+ → todos com margem de 64 dp; nenhum → Brasil inteiro. `DraggableScrollableSheet` com `TsSheet.snaps`. Card: apelido (senão placa), placa, chip (cor + ícone + texto), "Última posição válida {idade}", selos; ordem: alerta crítico aberto primeiro, depois apelido (senão placa) A→Z sem acento. Toque no card → `/veiculos/:id`; toque no marcador → card em destaque. Faixas globais: "Sem internet no celular · dados de {HH:mm}" e "Reconectando…" (SSE caído há > 10 s com HTTP respondendo).
- **A03 `/veiculos/:id`**: apelido, placa, marca/modelo/cor; chip e selos; "Última posição válida {idade} ({relógio BRT})"; "Ignição: ligada/desligada/desconhecida"; "Alimentação: veículo/bateria interna/desconhecida" (bateria com ícone `battery_alert` na cor `idle`); "Velocidade: {v} km/h" ou "Velocidade: desconhecida"; "Ver no mapa" → `/inicio?veiculo=:id`. Área de ações vazia, preenchida pela T-010.
- **Acessibilidade**: card com `Semantics(label: "{apelido}, placa {placa}, {estado}, {velocidade falada}, última posição válida {formatAgeSpoken}")`, ex.: "Gol prata, placa TST1A23, Em movimento, 48 quilômetros por hora, última posição válida há 12 segundos" (velocidade só em `moving` com valor); alvos ≥ `TsTouch.minDp`; fonte até 200% em 360 × 800 dp sem cortar estado e idade (quebra de linha, nunca reticências).

### (10) Offline somente leitura

- `cache-<userId>.json` no diretório de suporte: `{ "schema": 1, "userId", "operatorId", "syncedAt", "vehicles": [VehicleItem], "states": { "<vehicleId>": VehicleStateEvent }, "openAlerts": [AlertEvent] }`; gravado após cada lista e, no máximo, 1 vez a cada 10 s com eventos SSE. `syncedAt` = maior horário de servidor conhecido (`serverTime` da lista, `ready.serverTime`, horário do `keep-alive`). Token nunca entra no cache.
- Modo offline = a última requisição (HTTP ou abertura do SSE) terminou sem resposta de rede; sai no 1º sucesso. Offline: faixa global, estado e selos com agora = `syncedAt`, idades pelo relógio real, `OfflineGate.canWrite = false` (as ações que escrevem das próximas tarefas leem esse portão). Cache com `syncedAt` de mais de 7 dias → apagado e "Sem internet e sem dados recentes neste celular".

### (11) Sentry e medida de desempenho

`SentryFlutter.init` só com `SENTRY_DSN` não vazio; `sendDefaultPii: false`; `release = tracksys-mobile@<APP_VERSION>`; breadcrumbs sem coordenada, e-mail, placa ou token. Transação `map.first_vehicle` do início do processo ao 1º marcador desenhado com dado da rede (não do cache). No F0, cold start e `map.first_vehicle` medidos como em 10 §8 vão para o PR (informativos, CT-UX-013).

### (12) CI

Job `mobile` em `.github/workflows/ci.yml` (Ubuntu, `subosito/flutter-action` com `flutter-version-file: apps/mobile/pubspec.yaml`): `pnpm --filter @tracksys/contracts gen:dart-tokens && git diff --exit-code -- apps/mobile/lib/theme/tokens.g.dart`, `pnpm check:tokens-only`, `bash apps/mobile/tool/prepare_api.sh`, `flutter analyze` e `flutter test` em `apps/mobile`, `flutter test` em `tests/acceptance/T-009/mobile`.

## Testes de aceite (congelados)

**TS** (`pnpm test:acceptance`), base `seedVerticalSlice` (T-005) e sessões de teste da T-006:

- `tokens.test.ts` — **CT-UX-001**: `renderDartTokens(tokens.json)` igual byte a byte ao `tokens.g.dart` versionado; com `moving` = `#10B982`, a saída difere; `findTokenHexViolations` com `Color(0xFF10B981)` em `apps/mobile/lib/features/home/marker.dart` → 1 violação citando o arquivo; o mesmo texto em `apps/mobile/lib/theme/tokens.g.dart` → 0; `#10b981` em `apps/console/src/x.tsx` → 1.
- `contrast.test.ts` — **CT-UX-003** (TS): os 5 vetores, razões com 2 casas; `#777777` → `#747474`/`#FFFFFF` 4,67 e `#919191` 4,64; `#FFD400` → `adjusted = false`.
- `brand-api.test.ts` — após `seed:brand --operator <Alfa> --name Alfa --color "#E30613" --whatsapp +5586999990000`: `dono.a1` em `GET /api/v1/operator/brand` → 200 com `displayName "Alfa"`, `primaryColor "#E30613"` e `ETag` `"u…"`; com `If-None-Match` igual → 304 sem corpo; novo seed com `#0B3D91` → 200 e `ETag` diferente; `GET /api/v1/me` de `dono.a1` traz `brand.displayName = "Alfa"`; `admin.beta` recebe a marca da Beta, nunca "Alfa"; operadora sem linha de marca → `displayName` da operadora e `#3B82F6`; sem credencial → 401; seed com `--color "#12345"` ou `--whatsapp 5586999990000` → sai com 1 e a linha não muda.

**Dart** (pacote `tests/acceptance/T-009/mobile`, `pubspec.yaml` com `tracksys_mobile: { path: ../../../../apps/mobile }` e `flutter_test`; vetores por caminho relativo; API e armazenamento falsos):

- `presentation_state_test.dart` — **CT-UX-004** (Dart): 12 vetores; contato 15:14:01Z com relógio 15:20:01Z → "Última informação há 6 min".
- `age_format_test.dart` — **CT-UX-005** (Dart): todos os vetores (texto e falado); `AgeText` em "há 45 s" + 15 s de `fakeAsync` → "há 1 min".
- `brand_contrast_test.dart` — **CT-UX-003** (Dart): os 5 vetores.
- `live_store_test.dart` e `marker_animator_test.dart` — **CT-UX-006** e **CT-ALR-018** (cliente): exibindo 1048577, chega 1048512 → marcador parado; chega 1048601 com posição 120 m adiante → em 500 ms está a 60 ± 1 m e em 1.000 ms no destino, sem atualização depois; com animações desativadas → salto em 0 ms; `isPrimary = false` ignorado.
- `sse_parser_test.dart` — blocos partidos no meio de "Pânico" e no meio da linha, CRLF, `data` em 2 linhas, comentário e `retry` → eventos corretos.
- `live_controller_test.dart` — **CT-UX-006** (ciclo de vida): `paused` → stream cancelado em ≤ 5 s; `resumed` → nova conexão com `Last-Event-ID` e snapshot aplicado; `replaced` → nova tentativa em 0,8–1,2 s e depois 1,6–2,4 s; `session_revoked` → token e `cache-*`/`brand-*` apagados e rota `/entrar`; `session_expired` → `/entrar` com `cache-<userId>.json` preservado.
- `brand_flow_test.dart` — **CT-UX-002**: instalação nova → `/entrar` com logo TrackSys e botão `#3B82F6`, sem o texto "Alfa"; `dono.a1` entra → cabeçalho "Alfa" com logo; "Sair" → nenhum arquivo `brand-*` e tela neutra; reabertura com sessão e cache `#E30613` → 1º quadro em `#E30613`, requisição de marca com `If-None-Match: "u1"`, resposta 200 `#0B3D91` → tela atual segue `#E30613` e, ao abrir `/conta`, `brandFill` = `#0B3D91`; logo de 300 KiB → iniciais "A"; o falso de logo registra 0 cabeçalhos `Authorization`.
- `home_test.dart` — 2 veículos ("Gol prata" TST1A23 `parked`; sem apelido TST2B34 com `alert` `critical` aberto) → TST2B34 primeiro; 1 veículo → `LiveMapController` recebe centro com zoom 16; 2 → enquadramento com margem 64; paradas 0,15/0,45/0,90.
- `detail_test.dart` — **CT-UX-007**: `ignition = null` e `powerState = 'unknown'` → "Ignição: desconhecida" e "Alimentação: desconhecida", nenhum "desligada"; `battery` → "Alimentação: bateria interna" com ícone e cor `idle`.
- `offline_test.dart` — **CT-UX-016**: cache com V1 `parked`, fix e `syncedAt` 15:00:00Z, API falsa sem rede e relógio 15:40:00Z → "Sem internet no celular · dados de 12:00", V1 "Estacionado" (não `offline`), "Última posição válida há 40 min" e `OfflineGate.canWrite = false`; cache de 8 dias → não exibido e arquivo apagado; HTTP ok com SSE caído há 11 s → "Reconectando…".
- `session_test.dart` — **REQ-SEG-003** (cliente): token só no `TokenStore`; nenhum arquivo do diretório de suporte contém o token; toda requisição leva `Authorization: Bearer`; 401 em `/vehicles` → `/entrar` com caches preservados; login de outro usuário → cache do anterior apagado.
- `accessibility_test.dart` — **CT-UX-015**: card de V1 `moving` a 48 km/h com fix há 12 s → rótulo "Gol prata, placa TST1A23, Em movimento, 48 quilômetros por hora, última posição válida há 12 segundos"; `textScaler` 2,0 em 360 × 800 → estado e idade sem reticências; A02 e A03 passam em `androidTapTargetGuideline`, `iOSTapTargetGuideline`, `labeledTapTargetGuideline` e `textContrastGuideline`.

## Comandos de verificação

```bash
pnpm install
pnpm --filter @tracksys/contracts gen:dart-tokens && git diff --exit-code -- apps/mobile/lib/theme/tokens.g.dart
pnpm check:tokens-only
pnpm db:up && pnpm db:migrate && pnpm test:acceptance -- tests/acceptance/T-009
bash apps/mobile/tool/prepare_api.sh
(cd apps/mobile && flutter pub get && flutter analyze && flutter test)
(cd tests/acceptance/T-009/mobile && flutter pub get && flutter test)
(cd apps/mobile && flutter build apk --debug --dart-define=API_BASE_URL=https://api.example.invalid)
pnpm verify
```

Roteiro manual (registrar no PR; ensaio do G0-3 em Android, build debug apontando para o ambiente da VM): `dono.a1` entra e vê V1 com marca da Alfa; posição nova aparece sem recarregar; J16 de bancada desligado → após 6 min, selo "Última informação há 6 min" e, após 30 min, "Sem comunicação desde {hora}" (G0-3, estado "sem sinal"); modo avião → faixa "Sem internet no celular"; `dono.a2` entra e vê lista vazia. Medidas de cold start e `map.first_vehicle` (20 execuções no aparelho de referência) anexadas.

## Definição de pronto

- [ ] Comandos de verificação verdes local e no CI (job `mobile` incluído); testes congelados intactos.
- [ ] `operator-brand.get` no registro com caso em `scope-fixtures.ts`; `seed:brand` executado para a Alfa (teste) e a Lider.
- [ ] Nenhum hex de token fora de `tokens.g.dart`/`tokens.json`/`tokens.ts`; nenhum segredo no binário.
- [ ] PR `feat(mobile): login, lista, mapa ao vivo e marca da operadora (T-009)` com REQ, INV, CT, risco N2, medidas de desempenho e as pendências das decisões 1 e 12.

## Decisões já tomadas (não pergunte, siga)

| # | Dúvida provável | Resposta |
|---|---|---|
| 1 | A T-008 ainda não entrou e não há `GET /api/v1/vehicles` com estado nem SSE? | Desenvolva contra fixtures copiadas dos exemplos de 09 §9.1 e 07 §11 (`apps/mobile/test/fixtures/`) e o falso de transporte SSE; a integração real e o roteiro manual vêm quando a T-008 estiver em `main`. Se `presentation-vectors.json` e `age-vectors.json` ainda não existirem, crie-os com o conteúdo exato da seção 3 da T-008 (mesmo arquivo, sem variação). Registre no PR. |
| 2 | Biblioteca de estado (provider, riverpod, bloc)? | Nenhuma: `ChangeNotifier`, `ListenableBuilder` e um `InheritedNotifier` (`AppScope`). Dependência fora da lista da seção 1 exige justificativa no PR. |
| 3 | `connectivity_plus` para saber se está offline? | Não. Offline = última requisição sem resposta de rede (seção 10); é o que importa para o dado. |
| 4 | Onde ficam os testes Dart congelados? | Em `tests/acceptance/T-009/mobile`, pacote Flutter com dependência por caminho do app; `flutter test` roda de dentro dele. Testes não congelados ficam em `apps/mobile/test/`. |
| 5 | Comitar os `*.g.dart` do cliente gerado? | Não (T-004: `generated/dart` guarda só a saída do gerador). `prepare_api.sh` roda o `build_runner` local e no CI. |
| 6 | O app passa `vehicleIds` ou abre o escopo inteiro? | Sempre `vehicleIds` da lista (até 200): evita 422 para contas de equipe e deixa o pedido explícito. |
| 7 | Expiração apaga o cache? | Não: vai ao login mantendo cache. `session_revoked` (membership removida, senha trocada) apaga tudo, como "Sair" (INV-07). |
| 8 | Marca nova no meio da tela? | Não; vale na próxima troca de rota (10 §4 item 3). |
| 9 | Fuso de exibição? | UTC−03:00 fixo, igual à T-008 (sem pacote de fuso). |
| 10 | Rota que a T-012 usa ao tocar o push? | O toque abre `/alertas/:id` (A05, T-012); o "Ver no mapa" do detalhe usa `/inicio?veiculo=<vehicleId>`, que este cartão entrega: centraliza o veículo e abre o card. |
| 11 | Conta de equipe (`operator_*`) no app? | Pode entrar; `operator_admin` com 2FA recebe a mensagem de usar o console (o app não implementa TOTP). |
| 12 | A05 Alertas e A06 Vigilância (F0 em 10 §6)? | Não são deste cartão: entram na T-012 [ADOTADO NA v2.0], e a A06 sai junto com o corte 3 de [02 §2.4](../docs/spec/02-escopo-e-fases.md). O cliente SSE deste cartão já decodifica o evento `alert` (`alert_event.dart`) para a T-012 consumir. |
| 13 | Estilo de mapa escuro? | Usa `liberty` (stack canônica, DEC-11); o tema escuro vale para a interface do app. |
| 14 | Pedir permissão de notificação aqui? | Não; é da T-012 (A09). Este cartão não pede nenhuma permissão. |
