# T-010 — App: histórico do dia e deep links (WhatsApp da central e navegação)

| Campo | Valor |
|---|---|
| Fase | F0 (semana S3: 21–27/10/2026; teste fechado do Google Play iniciado até 27/10) |
| Requisitos | REQ-UX-008 (tela A04), REQ-UX-011, REQ-UX-030 (parte F0: teste fechado Android e TestFlight) |
| Invariantes | INV-03, INV-06, INV-07, INV-12 |
| Risco de revisão | **N0 pelo caminho:** `.github/workflows/mobile-release.yml` (assinatura e segredos do AAB). Demais arquivos N2 (app Flutter, scripts, runbook). Leitura linha a linha e revisor de outro fornecedor só no workflow; o resto segue o checklist N2 |
| Depende de | T-009 (app, sessão, marca, `brt.dart`, `formatAge`, A03); usa `GET /api/v1/vehicles/{vehicleId}/history` (com `availableFrom`) e `history-vectors.json` da T-008 |
| Estimativa | 2 sessões de agente (1: histórico; 2: deep links e distribuição) |
| Bloqueado por decisão | DEC-03 só para a parte iOS (TestFlight); sem a conta Apple, entrega o Android e o fundador avalia o corte 6 de [02 §2.4](../docs/spec/02-escopo-e-fases.md#24-plano-de-corte). DEC-04 não bloqueia o código, mas o build entregue aos testadores do G0 usa o domínio definitivo em `TRACKSYS_DOMAIN` |

## Objetivo

Completar o app do F0 com o que o cliente usa depois de ver o mapa: o trajeto de um dia (hoje, ontem ou até 90 dias), com lacunas honestas e distância qualificada; "Falar com a central" por WhatsApp (ou telefone) com placa e link da última posição; e "Navegar até o veículo" pelo Google Maps ou Waze, avisando quando a posição é antiga. Também entrega o caminho de distribuição do F0: AAB assinado enviado ao teste fechado do Google Play por tag, verificação de segredos no binário e roteiro do TestFlight, para que o teste fechado comece até 27/10/2026 e o G0-3/G0-4 rodem em aparelho real.

## Contexto obrigatório

- [10 §5 (idade), §6 (A03, A04, A07, A08), §12 (distribuição)](../docs/spec/10-apps-e-ux.md#5-estados-honestos); REQ-UX-008, REQ-UX-011, REQ-UX-030.
- [09 §9.4](../docs/spec/09-api-e-contratos.md#94-get-apiv1vehiclesvehicleidhistory): histórico, lacunas e paginação; campo aditivo `availableFrom` (T-008).
- [02 §2.2 e §2.5](../docs/spec/02-escopo-e-fases.md#22-cronograma-semanal): prazo do teste fechado (27/10) e roteiros G0-3/G0-4.
- [ADR-007](../docs/adr/ADR-007-app-unico-flutter-marca-dinamica.md): app publicado pela conta da Versix; regras das lojas.
- Cartões T-008 (`buildHistorySegments`, `summarizeHistory`, vetores) e T-009 (estrutura do app, `OfflineGate`, área de ações deixada no A03).

## Escopo — fazer

1. Tela A04 `/veiculos/:id/historico?dia=AAAA-MM-DD` (seção 1).
2. Dart puro: `history_summary.dart`, `brtDayRange`/`brtToday` e paginação do dia (seção 2).
3. Construtores puros dos links A07 e A08 e o abridor de URL (seção 3).
4. Ações no A03: "Histórico do dia", "Falar com a central", "Navegar até o veículo" (seção 4).
5. Distribuição F0: workflow `mobile-release.yml`, assinatura Android, verificação de segredos no AAB e runbook (seção 5).
6. Testes de aceite em `tests/acceptance/T-010/`.

## Fora do escopo

- A05 Alertas, A06 Vigilância e A09 Notificações (T-012; a A05 reutiliza as ações A07 e A08 deste cartão).
- "Solicitar relatório" acima de 90 dias e exportação (F1, [ADR-009](../docs/adr/ADR-009-retencao-quente-frio.md)).
- Publicação em produção nas lojas (F1, G1-5); pipeline iOS automatizado (F0 é manual); flavors (F2).
- Cache offline de histórico; tela C07 do console (T-008); WhatsApp Cloud API (F2).

## Arquivos a criar/alterar

```
criar    apps/mobile/lib/ux/history_summary.dart ; alterar apps/mobile/lib/ux/brt.dart (brtDayRange, brtToday)
criar    apps/mobile/lib/features/history/{history_screen,history_map,day_selector,history_summary_card,history_pager}.dart
criar    apps/mobile/lib/links/{support_link,navigation_links,url_opener}.dart
criar    apps/mobile/lib/features/vehicle/{vehicle_actions,navigate_sheet}.dart
alterar  apps/mobile/lib/features/vehicle/vehicle_detail_screen.dart  apps/mobile/lib/router.dart  apps/mobile/pubspec.yaml (url_launcher)
alterar  apps/mobile/android/app/src/main/AndroidManifest.xml (<queries>)  apps/mobile/android/app/build.gradle.kts (assinatura)
alterar  .gitignore (apps/mobile/android/key.properties, *.jks, *.keystore)
criar    .github/workflows/mobile-release.yml  apps/mobile/tool/{check_aab_secrets,write_key_properties}.sh  docs/runbooks/mobile-release.md
criar    apps/mobile/test/** (unitários, não congelados)
criar    tests/acceptance/T-010/release.test.ts
criar    tests/acceptance/T-010/mobile/pubspec.yaml  tests/acceptance/T-010/mobile/test/*_test.dart
```

## Especificação detalhada

### (1) A04 Histórico do dia

- **Dia**: padrão hoje BRT (`brtToday(agora)`); botões "Hoje", "Ontem" e "Escolher dia" (`showDatePicker`, `pt_BR`, `firstDate` = hoje − 89 dias, `lastDate` = hoje: 90 dias, sempre dentro da janela quente da API). O dia escolhido vai para `?dia=AAAA-MM-DD`.
- **Busca**: `GET /api/v1/vehicles/{id}/history?from={brtDayRange.from}&to={brtDayRange.to}&limit=5000`, seguindo `nextCursor` até `null` **antes** de desenhar trajeto e resumo ("Carregando trajeto…"); `gaps` somados de todas as páginas (a API já liga páginas pelo cursor). Teto de 20 páginas → "Trajeto grande demais para o app. Use o console." Sair da tela cancela as requisições (`CancelToken`).
- **Mapa** (`history_map.dart`, MapLibre atrás da interface `HistoryMapController`; falso nos testes): segmentos de `buildHistorySegments`; sólido = linha de 4 dp em `TsColors.moving`; lacuna = linha tracejada (`[2, 2]`) em `TsColors.textSecondary` com rótulo no ponto médio "Sem dados {HH:mm}–{HH:mm}"; marcador de início (`trip_origin`, "Início {HH:mm}") e de fim (`flag`, "Fim {HH:mm}"); câmera enquadra os pontos válidos com margem de 64 dp (1 ponto → zoom 16). O app não calcula lacuna nem interpola (10 §6, A04).
- **Toque**: ponto válido mais próximo a até 48 dp → balão "{HH:mm} · {v} km/h" (`v` arredondado, meio para cima) ou "{HH:mm} · velocidade desconhecida"; nenhum perto → nada.
- **Resumo** (`history_summary_card.dart`): "Primeiro ponto {HH:mm} · Último ponto {HH:mm}" e a distância de `summarizeHistory` ("0,2 km" ou "≥ 0,3 km (há lacunas)"); `Semantics` lê "km" como "quilômetros".
- **Estados**: dia inteiro antes de `availableFrom` (`availableFrom ≥ to`) → "Histórico disponível a partir de {dd/MM/aaaa}" sem mapa; sem pontos válidos → "Sem posições neste dia"; 404 → "Veículo não encontrado"; 422 `HISTORY_REQUIRES_EXPORT` → "Período fora dos 90 dias disponíveis no app"; 429 → "Muitas consultas. Tente de novo em {n} s" (`Retry-After`); sem resposta de rede → "Sem internet. O histórico precisa de conexão."

### (2) Dart puro

- `history_summary.dart`: `buildHistorySegments(items, gaps)` e `summarizeHistory(items, gaps)` com saída idêntica às funções TS da T-008 sobre `packages/testkit/fixtures/ux/history-vectors.json` (lido por caminho relativo); só pontos `valid`; distância = soma de haversine (raio 6.371.008,8 m) só nos trechos sólidos; uma casa decimal com vírgula.
- `brt.dart` (acréscimos): `brtDayRange('2026-10-20')` → `from = 2026-10-20T03:00:00Z`, `to = 2026-10-21T03:00:00Z`; `brtToday(DateTime.utc(2026, 10, 21, 2, 30))` → `'2026-10-20'`. Deslocamento fixo UTC−03:00, como na T-008.
- `history_pager.dart`: `loadHistoryDay(api, vehicleId, day)` → `HistoryDay { items, gaps, availableFrom }`.

### (3) Links (A07, A08) e abridor

`support_link.dart` — `buildSupportLink({ brand, userName, vehicle, state, now })` → `SupportLink.whatsapp(Uri)`, `SupportLink.phone(Uri)` ou `null`:

- Com `supportWhatsapp`: `https://wa.me/{supportWhatsapp sem "+"}?text={Uri.encodeComponent(texto)}`.
- `texto` = `Olá, {brand.displayName}. Sou {user.name}. Veículo {nickname}, placa {plate}. Última posição ({relógio}): https://maps.google.com/?q={lat},{lon}`, com `lat`/`lon` em `toStringAsFixed(6)` (ponto decimal) e `relógio` = `formatBrtClock(lastFixAt, now)` ("HH:mm"; outro dia: "dd/MM HH:mm").
- Variações: sem apelido → `Veículo placa {plate}.`; sem placa → `Veículo {nickname}.`; sem os dois → `Veículo sem identificação.`; sem posição válida → a última frase vira `Última posição: indisponível.`
- Só `supportPhone` → `tel:{supportPhone}` (E.164 com "+", ex.: `tel:+558632220000`). Nenhum dos dois → `null`: o botão some e o A03 mostra "Contato da central não cadastrado" (10 §4 item 6).

`navigation_links.dart` — com posição válida: Google Maps `https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving`; Waze `https://waze.com/ul?ll={lat},{lon}&navigate=yes` (6 casas, ponto). `navigationWarning(lastFixAt, now)`: idade > 600 s → `Posição de {formatAge}. O veículo pode ter se movido.` (ex.: "Posição de há 25 min. …"); idade ≥ 24 h → `Posição de {dd/MM} às {HH:mm}. O veículo pode ter se movido.`; ≤ 600 s → `null`.

`url_opener.dart` — interface `UrlOpener.open(Uri) → Future<bool>` com implementação `launchUrl(uri, mode: LaunchMode.externalApplication)`; não chama `canLaunchUrl`; `false` ou exceção → SnackBar "Não foi possível abrir o WhatsApp" / "o Google Maps" / "o Waze" / "Não foi possível iniciar a ligação". iOS: nada em `LSApplicationQueriesSchemes` (só `https` e `tel`). Android (`AndroidManifest.xml`, dentro de `<manifest>`):

```xml
<queries>
  <intent>
    <action android:name="android.intent.action.VIEW" />
    <data android:scheme="https" />
  </intent>
  <intent>
    <action android:name="android.intent.action.DIAL" />
    <data android:scheme="tel" />
  </intent>
</queries>
```

Offline: os links seguem habilitados com o último dado do cache (abrir WhatsApp ou navegação não escreve na TrackSys); a hora no texto e o aviso de idade mantêm a honestidade.

### (4) Ações no A03

Na área deixada pela T-009, em coluna, alvos ≥ 48 dp: "Histórico do dia" → `/veiculos/:id/historico`; "Falar com a central" (ou o texto de contato ausente); "Navegar até o veículo" → com aviso, diálogo com o texto do aviso, "Continuar" e "Cancelar"; depois a folha `navigate_sheet.dart` com "Google Maps" e "Waze". Sem posição válida → botão desativado com "Sem posição válida para navegar". Rótulos de `Semantics` iguais aos textos visíveis.

### (5) Distribuição F0 (REQ-UX-030)

`.github/workflows/mobile-release.yml`, disparo `push` em tags `mobile-v*`, job Android (`ubuntu-latest`), nesta ordem:

1. `actions/checkout`, pnpm, `subosito/flutter-action` (`flutter-version-file: apps/mobile/pubspec.yaml`), `bash apps/mobile/tool/prepare_api.sh`.
2. `flutter test` em `apps/mobile`, `tests/acceptance/T-009/mobile` e `tests/acceptance/T-010/mobile`.
3. `X.Y.Z` = tag sem `mobile-v`, validada por `^[0-9]+\.[0-9]+\.[0-9]+$` (senão falha).
4. Assinatura: `ANDROID_KEYSTORE_B64` → `$RUNNER_TEMP/upload.jks`; `apps/mobile/android/key.properties` com `storeFile`, `storePassword` (`ANDROID_KEYSTORE_PASSWORD`), `keyAlias` (`ANDROID_KEY_ALIAS`), `keyPassword` (`ANDROID_KEY_PASSWORD`). `build.gradle.kts` lê `key.properties`; build `release` sem ele falha com "assinatura de release ausente" (nunca cai na chave de debug).
5. `flutter build appbundle --release --build-name X.Y.Z --build-number ${{ github.run_number }} --dart-define=API_BASE_URL=https://api.${{ vars.TRACKSYS_DOMAIN }} --dart-define=WEB_BASE_URL=https://app.${{ vars.TRACKSYS_DOMAIN }} --dart-define=APP_VERSION=X.Y.Z --dart-define=SENTRY_DSN=${{ vars.SENTRY_DSN_MOBILE }}` (a T-012 acrescenta os `FIREBASE_*` quando entrar).
6. `bash apps/mobile/tool/check_aab_secrets.sh build/app/outputs/bundle/release/app-release.aab`: `unzip -p "$1" | strings | grep -E 'FCM_SERVICE_ACCOUNT|BEGIN (RSA |EC )?PRIVATE KEY|ANDROID_KEYSTORE'`; achou → sai com 1 citando o padrão (nunca o trecho).
7. Envio ao teste fechado: `r0adkll/upload-google-play@<SHA de 40 caracteres>` com `serviceAccountJsonPlainText: ${{ secrets.PLAY_SERVICE_ACCOUNT_JSON }}`, `packageName: br.com.versix.tracksys`, `releaseFiles` do AAB, `track: alpha` [VALIDAR — nome da faixa de teste fechado criada no Play Console], `status: completed`.
8. Release no Sentry `tracksys-mobile@X.Y.Z` por `getsentry/action-release@<SHA>` só quando `SENTRY_AUTH_TOKEN` existir (checado por variável de ambiente no passo).
9. AAB como artefato do workflow (30 dias).

Esqueleto obrigatório (ações de terceiros com SHA real no lugar de `<sha>`; versões de ação oficiais `actions/*` também por SHA):

```yaml
name: mobile-release
on:
  push:
    tags: ['mobile-v*']
permissions:
  contents: read
jobs:
  android:
    runs-on: ubuntu-latest
    environment: mobile-release            # segredos só neste ambiente
    steps:
      - uses: actions/checkout@<sha>
      - uses: pnpm/action-setup@<sha>
      - uses: subosito/flutter-action@<sha>
        with: { flutter-version-file: apps/mobile/pubspec.yaml, cache: true }
      - run: pnpm install --frozen-lockfile && bash apps/mobile/tool/prepare_api.sh
      - run: |
          (cd apps/mobile && flutter test)
          (cd tests/acceptance/T-009/mobile && flutter test)
          (cd tests/acceptance/T-010/mobile && flutter test)
      - id: ver
        run: |
          v="${GITHUB_REF_NAME#mobile-v}"
          [[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "tag inválida: $GITHUB_REF_NAME"; exit 1; }
          echo "version=$v" >> "$GITHUB_OUTPUT"
      - run: bash apps/mobile/tool/write_key_properties.sh
        env:
          ANDROID_KEYSTORE_B64: ${{ secrets.ANDROID_KEYSTORE_B64 }}
          ANDROID_KEYSTORE_PASSWORD: ${{ secrets.ANDROID_KEYSTORE_PASSWORD }}
          ANDROID_KEY_ALIAS: ${{ secrets.ANDROID_KEY_ALIAS }}
          ANDROID_KEY_PASSWORD: ${{ secrets.ANDROID_KEY_PASSWORD }}
      - run: >-
          cd apps/mobile && flutter build appbundle --release
          --build-name ${{ steps.ver.outputs.version }} --build-number ${{ github.run_number }}
          --dart-define=API_BASE_URL=https://api.${{ vars.TRACKSYS_DOMAIN }}
          --dart-define=WEB_BASE_URL=https://app.${{ vars.TRACKSYS_DOMAIN }}
          --dart-define=APP_VERSION=${{ steps.ver.outputs.version }}
          --dart-define=SENTRY_DSN=${{ vars.SENTRY_DSN_MOBILE }}
      - run: bash apps/mobile/tool/check_aab_secrets.sh apps/mobile/build/app/outputs/bundle/release/app-release.aab
      - uses: r0adkll/upload-google-play@<sha>
        with: { serviceAccountJsonPlainText: '${{ secrets.PLAY_SERVICE_ACCOUNT_JSON }}', packageName: br.com.versix.tracksys, releaseFiles: apps/mobile/build/app/outputs/bundle/release/app-release.aab, track: alpha, status: completed }
      # passos 8 (Sentry, condicional) e 9 (artefato) a seguir
```

`check_aab_secrets.sh` (completo):

```bash
#!/usr/bin/env bash
# Falha se o AAB contiver segredo conhecido. Nunca imprime o trecho encontrado.
set -euo pipefail
aab="${1:?uso: check_aab_secrets.sh <arquivo.aab>}"
for pattern in 'FCM_SERVICE_ACCOUNT' 'BEGIN (RSA |EC )?PRIVATE KEY' 'ANDROID_KEYSTORE'; do
  if unzip -p "$aab" | strings | grep -Eq "$pattern"; then
    echo "segredo encontrado no AAB: padrão '$pattern'" >&2
    exit 1
  fi
done
echo "AAB sem segredos conhecidos."
```

`write_key_properties.sh` (criar em `apps/mobile/tool/`) decodifica `ANDROID_KEYSTORE_B64` para `$RUNNER_TEMP/upload.jks` e grava `apps/mobile/android/key.properties`; falta de qualquer variável → sai com 1 nomeando a variável, nunca o valor.

`docs/runbooks/mobile-release.md`: nomes dos segredos e variáveis (sem valores); geração da chave de upload e guarda fora do repositório; 1º envio do AAB manual pelo Play Console (exigência para app novo [VALIDAR — regra vigente]); criação da faixa de teste fechado com ≥ 12 testadores por 14 dias seguidos [VALIDAR — regra do Google Play para conta pessoal], política de privacidade e Segurança dos dados ([Anexo B](../docs/anexos/B-juridico.md)); como cortar versão (`git tag mobile-v0.1.0` + push da tag); como interromper uma versão; iOS no F0: arquivar no Xcode (ou Codemagic [VALIDAR — custo]) com os mesmos `--dart-define`, enviar ao App Store Connect, testadores internos e externos no TestFlight (revisão beta da Apple [VALIDAR prazo]; depende de DEC-03); gravação dos vídeos do G0-3/G0-4.

## Testes de aceite (congelados)

**Dart** (pacote `tests/acceptance/T-010/mobile`, `pubspec.yaml` com `tracksys_mobile: { path: ../../../../apps/mobile }` e `flutter_test`; API, mapa e `UrlOpener` falsos):

- `history_summary_test.dart` — vetores de `history-vectors.json`: `gap` → segmentos sólido/lacuna/sólido, rótulo "Sem dados 08:03–08:09", `distanceM` 315 ± 1, "≥ 0,3 km (há lacunas)"; `continuous` → 1 segmento, 160 ± 1 m, "0,2 km".
- `day_range_test.dart` — **CT-UX-008** (dia BRT): `brtDayRange('2026-10-20')` → `2026-10-20T03:00:00Z` e `2026-10-21T03:00:00Z`; `brtToday(2026-10-21T02:30:00Z)` → `2026-10-20`; `brtToday(2026-10-21T03:00:00Z)` → `2026-10-21`; com agora 2026-10-20T15:00:00Z, o calendário vai de 23/07/2026 a 20/10/2026.
- `history_screen_test.dart` — **CT-UX-008** (A04): ao escolher 20/10, a API falsa recebe `from=2026-10-20T03:00:00Z&to=2026-10-21T03:00:00Z&limit=5000`; resposta de 09 §9.4 → `HistoryMapController` recebe trecho tracejado de (−5,086842; −42,800331) a (−5,079100; −42,795020) com "Sem dados 08:03–08:09" e o resumo começa com "≥"; `gaps` vazio com pontos às 10:58:12Z e 11:02:30Z → 1 trecho contínuo e "0,2 km"; 1ª página com `nextCursor` → 2ª requisição com `cursor=` e nenhum resumo exibido antes dela; `availableFrom` 2026-10-22T13:00:00Z e dia 21/10 → "Histórico disponível a partir de 22/10/2026" sem linha; toque sobre o 2º ponto → "08:02 · 19 km/h"; 404 → "Veículo não encontrado"; sem rede → "Sem internet. O histórico precisa de conexão."
- `links_test.dart` — **CT-UX-011**: `supportWhatsapp` +5586999990000, operadora "Alfa", usuário "Dono A1", V1 "Gol prata" TST1A23, fix (−5,089211; −42,801892) em 2026-10-20T21:14:00Z e agora 21:20:00Z → `https://wa.me/5586999990000?text=…` cujo texto decodificado é exatamente "Olá, Alfa. Sou Dono A1. Veículo Gol prata, placa TST1A23. Última posição (18:14): https://maps.google.com/?q=-5.089211,-42.801892"; Waze → `https://waze.com/ul?ll=-5.089211,-42.801892&navigate=yes`; Google Maps → `https://www.google.com/maps/dir/?api=1&destination=-5.089211,-42.801892&travelmode=driving`; fix de há 25 min → "Posição de há 25 min. O veículo pode ter se movido."; fix de há exatamente 10 min → sem aviso; sem apelido → "Veículo placa TST1A23."; sem posição → "Última posição: indisponível." e navegação `null`; só `supportPhone` +558632220000 → `tel:+558632220000`; nenhum contato → `null`.
- `vehicle_actions_test.dart` — A03: com WhatsApp, tocar "Falar com a central" chama o `UrlOpener` 1 vez com a URI do `wa.me`; sem contatos → sem botão e com "Contato da central não cadastrado"; "Navegar até o veículo" com fix de há 25 min → diálogo de aviso antes da folha; "Waze" → `UrlOpener` com a URI do Waze; `UrlOpener` devolve `false` → "Não foi possível abrir o Waze"; posição `null` → botão desativado com "Sem posição válida para navegar"; "Histórico do dia" → rota `/veiculos/<id>/historico`; A03 e A04 passam em `androidTapTargetGuideline` e `labeledTapTargetGuideline`.

**TS** (`pnpm test:acceptance`):

- `release.test.ts` — **CT-UX-030** (parte verificável sem loja): o workflow tem `--build-number ${{ github.run_number }}`, `--build-name` vindo da tag, `track: alpha`, todo `uses:` fixado por SHA de 40 caracteres hexadecimais e o passo `check_aab_secrets.sh` antes do envio; `check_aab_secrets.sh` sobre um zip (criado com `python3 -m zipfile -c`) contendo `-----BEGIN PRIVATE KEY-----` → código 1; com `FCM_SERVICE_ACCOUNT` → 1; zip limpo → 0. A parte da loja (tag `mobile-v0.3.0` → AAB `versionName 0.3.0`, `versionCode` = número da execução, faixa de teste fechado, release no Sentry) é evidência manual no PR.

## Comandos de verificação

```bash
pnpm install
pnpm test:acceptance -- tests/acceptance/T-010
bash apps/mobile/tool/prepare_api.sh
(cd apps/mobile && flutter pub get && flutter analyze && flutter test)
(cd tests/acceptance/T-010/mobile && flutter pub get && flutter test)
(cd tests/acceptance/T-009/mobile && flutter pub get && flutter test)          # regressão da T-009
(cd apps/mobile && flutter build apk --debug --dart-define=API_BASE_URL=https://api.example.invalid)
pnpm check:tokens-only && pnpm verify
```

Primeira versão (evidência no PR): tag `mobile-v0.1.0` → workflow verde; `bundletool dump manifest --bundle app-release.aab --xpath /manifest/@android:versionCode` igual ao `run_number` e `versionName` 0.1.0; versão visível na faixa de teste fechado; roteiro G0-4 ensaiado em Android: trajeto de ontem de V1 com horário do 1º e do último ponto válido igual ao da API de histórico.

## Definição de pronto

- [ ] Comandos de verificação verdes local e no CI; testes congelados de T-009 e T-010 intactos.
- [ ] Teste fechado do Google Play com a versão do workflow até 27/10/2026 (ou bloqueio registrado no G0 com causa); TestFlight enviado ou bloqueio por DEC-03 registrado.
- [ ] Nenhum segredo, `key.properties`, `.jks` ou `google-services.json` no repositório; `check_aab_secrets.sh` verde no AAB publicado.
- [ ] PR `feat(mobile): histórico do dia, deep links e distribuição do F0 (T-010)` com REQ, INV, CT, `Risco declarado: N0` (pelo caminho: `mobile-release.yml`; demais N2) e as evidências acima.

## Decisões já tomadas (não pergunte, siga)

| # | Dúvida provável | Resposta |
|---|---|---|
| 1 | Distância soma o trecho da lacuna? | Não. Lacuna fica fora da soma; por isso "≥ {x} km (há lacunas)". Uma casa decimal, igual à T-008. |
| 2 | Resumo usa o 1º item da API ou o 1º ponto válido? | O 1º e o último ponto **válidos** (os que aparecem no mapa). O roteiro do G0-4 compara com o 1º e o último item `valid: true` da API. |
| 3 | Guardar histórico para ver offline? | Não no F0: o histórico exige rede e a tela diz isso. O cache offline da T-009 cobre só lista, estado e marca. |
| 4 | Links funcionam offline? | Sim, com o último dado do cache: não escrevem na TrackSys. O texto leva a hora do fix e a navegação avisa a idade. |
| 5 | `wa.me` com `+`, espaço ou traço? | Só dígitos (o banco já guarda E.164 validado). Texto com `Uri.encodeComponent` (espaço vira `%20`, nunca `+`). |
| 6 | Apelido, placa ou posição ausentes no texto do WhatsApp? | Variações da seção 3; nunca "null" nem coordenada inventada (INV-03). |
| 7 | Conferir com `canLaunchUrl` antes de abrir? | Não; abre direto e trata `false`/exceção com mensagem. Evita declarar esquemas e falsos negativos no Android 11+. |
| 8 | Ação de terceiros para enviar ao Play? | `r0adkll/upload-google-play` fixada por SHA, justificada no PR (sem Ruby/fastlane). O 1º envio de app novo é manual no Play Console. |
| 9 | `versionCode`? | `github.run_number`, sempre crescente; `versionName` = X.Y.Z da tag (10 §12). |
| 10 | Pipeline iOS no F0? | Manual pelo runbook (Xcode ou Codemagic [VALIDAR — custo]); automação é F1. Sem DEC-03, o G0 pode seguir só com Android (corte 6). |
| 11 | DSN do Sentry é segredo? | Não (é público por desenho); vai em `vars`. Chave de upload, senha do keystore e JSON da conta de serviço vão em `secrets`. |
| 12 | Calendário de 90 dias inclui o dia de hoje − 90? | Não: hoje e os 89 anteriores. Assim `from` nunca cai antes de agora − 90 dias e a API nunca responde 422 por idade. |
| 13 | Variáveis do Firebase no build de release? | Entram com a T-012, no mesmo workflow; este cartão não cria `FIREBASE_*`. |
