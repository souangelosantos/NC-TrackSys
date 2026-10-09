# T-032 — App: push, telas de alertas (A05), modo vigilância (A06) e notificações (A09)

| Campo | Valor |
|---|---|
| Fase | F0 (semana S3: 21–27/10/2026; marco 27/10: alerta provocado chega ao celular com a tela bloqueada) |
| Requisitos | REQ-UX-009, REQ-UX-010, REQ-UX-012 |
| Invariantes | INV-03, INV-07, INV-08 (A06 nunca dispara comando físico) |
| Risco de revisão | N0 pelo caminho: `.github/workflows/mobile-release.yml` (`--dart-define=FIREBASE_*`); demais arquivos N2 (app Flutter). Revisor de outro fornecedor e leitura linha a linha só no workflow; o resto segue o checklist N2 |
| Depende de | T-009 (app com login, mapa ao vivo, A03 e cliente SSE), T-012 (rotas de tokens e preferências, leituras `alerts.get` e `watch-mode.get`, entrega FCM). Usa artefatos já entregues: T-011 (`GET /api/v1/alerts`, `POST`/`DELETE` da vigilância), T-008 (evento SSE `alert`, `availableActions.watchMode`), T-010 (ações A07 e A08; até ela entrar, o detalhe mostra só "Ver no mapa" e registra no PR) |
| Estimativa | 2 sessões de agente (1: Firebase, token, canais, toque no push e A09; 2: A05, A06 e ensaio ponta a ponta) |
| Bloqueado por decisão | DEC-03 (conta Apple: sem ela, iOS sai do G0 pelo corte 6 de [02 §2.4](../docs/spec/02-escopo-e-fases.md#24-plano-de-corte)); projeto Firebase com chave APNs (ação do fundador no S2) |

## Objetivo

Fazer o alerta chegar à tela bloqueada do cliente final e levá-lo ao detalhe em 1 toque: `firebase_messaging`, canais do Android, Time Sensitive no iOS, token sincronizado com a T-012, banner em primeiro plano, A05 (lista e detalhe), A06 (interruptor da vigilância) e A09 (permissão e preferências).

A06 sai com o corte 3 de [02 §2.4](../docs/spec/02-escopo-e-fases.md#24-plano-de-corte); A05 e A09 não têm corte.

## Contexto obrigatório

- [10 §6](../docs/spec/10-apps-e-ux.md#6-app--telas): telas A05, A06 e A09, rotas internas do app (`/alertas`, `/alertas/:id`), REQ-UX-009, REQ-UX-010 e REQ-UX-012.
- [07 §2](../docs/spec/07-alertas-e-tempo-real.md#2-catálogo) (textos), §5 (vigilância), §7 (mensagem FCM e `data.link`), §8 (preferências).
- [T-012](T-012-push-fcm-tokens-e-entregas.md): rotas `/api/v1/me/push-tokens`, `/api/v1/me/alert-preferences`, `GET /api/v1/alerts/{alertId}` e `GET /api/v1/vehicles/{vehicleId}/watch-mode`.
- [T-009](T-009-app-login-lista-mapa-ao-vivo-marca.md): `go_router`, sessão, cliente SSE, A03, chips de estado e regra de offline; [T-011](T-011-motor-de-alertas-f0.md): `GET /api/v1/alerts` e rotas de vigilância.
- [02 §2.4](../docs/spec/02-escopo-e-fases.md#24-plano-de-corte): corte 3 (modo vigilância) e corte 6 (iOS).

## Escopo — fazer

1. Dependências `firebase_core` e `firebase_messaging`; `FirebaseOptions` montado de `--dart-define` (seção 1).
2. Android: `POST_NOTIFICATIONS`, pedido em tempo de execução e canais `alerts_high` e `alerts_info` (seção 1). iOS: Push Notifications, Time Sensitive e `remote-notification`.
3. `push_token_sync.dart` e `alert_link.dart` (seção 2): token sincronizado com a T-012 e toque no push que abre o alerta.
4. A05 Alertas: lista de 30 dias e detalhe (seção 3).
5. A06 Modo vigilância: interruptor no A03 (seção 4).
6. A09 Notificações: permissão explicada, faixa de recusa e preferências (seção 5).
7. `--dart-define=FIREBASE_*` no build de release de `.github/workflows/mobile-release.yml` (criado pela T-010), com os valores em variáveis do ambiente `mobile-release`.
8. Testes de aceite em `tests/acceptance/T-032/mobile`, testes unitários em `apps/mobile/test/` e ensaio ponta a ponta em `docs/runbooks/gates/G0.md`.

## Fora do escopo

- Servidor do push (migration, `claim_push_token`, rotas, `alerts.deliver`, adaptador FCM): [T-012](T-012-push-fcm-tokens-e-entregas.md).
- Histórico de alertas além de 30 dias, filtros na A05 e central de notificações: F1.
- Reconhecer alerta pelo app (cliente não tem `alert.ack`, [08 §3](../docs/spec/08-identidade-e-seguranca.md#3-papéis-e-permissões)) e mudar o raio da vigilância (o app sempre envia `{}`, raio 150 m).
- Push para a equipe da operadora (F0–F1 usa a fila do console) e qualquer comando físico a partir do app (T-021, F1).
- Modo vigilância com raio ou agenda configurável; SMS, WhatsApp ou e-mail como canal de alerta.

## Arquivos a criar/alterar

```
.github/workflows/mobile-release.yml (alterar: --dart-define=FIREBASE_*)
apps/mobile/pubspec.yaml (firebase_core, firebase_messaging)
apps/mobile/lib/push/{push_service,push_token_sync,alert_link,firebase_options}.dart, apps/mobile/lib/main.dart
apps/mobile/android/app/src/main/AndroidManifest.xml, apps/mobile/android/app/src/main/kotlin/**/MainActivity.kt
apps/mobile/ios/Runner/{Runner.entitlements,Info.plist}
apps/mobile/lib/features/{alerts/alerts_screen,alerts/alert_detail_screen,alerts/alerts_repository}.dart
apps/mobile/lib/features/{vehicle/watch_mode_switch,vehicle/watch_mode_repository}.dart
apps/mobile/lib/features/{notifications/notifications_screen,notifications/permission_explainer,notifications/notifications_banner}.dart
apps/mobile/lib/router.dart, apps/mobile/lib/features/home/home_screen.dart, apps/mobile/lib/features/vehicle/vehicle_detail_screen.dart, apps/mobile/lib/features/account/account_screen.dart
  (alterar: rotas /alertas e /alertas/:id, acesso pelo Início, interruptor no A03, link para A09 na Conta)
apps/mobile/test/push/{alert_link_test,push_token_sync_test}.dart
tests/acceptance/T-032/mobile/{pubspec.yaml,alerts/alert_detail_test.dart,watch_mode/watch_mode_switch_test.dart,notifications/notifications_test.dart}
```

## Especificação detalhada

### (1) Firebase, canais e permissões

- `FirebaseOptions` montado de `--dart-define` (`FIREBASE_API_KEY`, `FIREBASE_PROJECT_ID`, `FIREBASE_MESSAGING_SENDER_ID`, `FIREBASE_APP_ID_ANDROID`, `FIREBASE_APP_ID_IOS`). Nenhum `google-services.json` ou `GoogleService-Info.plist` entra no repositório.
- Android: `POST_NOTIFICATIONS` no manifesto e pedido em tempo de execução (Android 13+). `MainActivity.kt` cria `alerts_high` ("Alertas", `IMPORTANCE_HIGH`) e `alerts_info` ("Avisos", `IMPORTANCE_DEFAULT`) no 1º início.
- iOS: capacidades Push Notifications e Time Sensitive (`com.apple.developer.usernotifications.time-sensitive`), `UIBackgroundModes = remote-notification`. A permissão é pedida após o login, com texto PT-BR que explica os alertas de segurança.

### (2) Token e toque no push

- `push_token_sync.dart` chama `PUT /api/v1/me/push-tokens` no login, a cada retorno ao primeiro plano e em `onTokenRefresh`. No logout chama `DELETE` antes de apagar a sessão. Falha de rede: nova tentativa em 30 s, sem bloquear a UI.
- Primeiro plano: `onMessage` mostra `MaterialBanner` com título, corpo e ação "Ver" (abre o detalhe).
- Toque (`onMessageOpenedApp` e `getInitialMessage`): `alert_link.dart` valida `tracksys://alerts/<uuid>` e abre `/alertas/<alertId>` (A05, 1 toque), com o app encerrado, em segundo plano ou aberto.
- Sem sessão, o toque passa pelo login e volta ao alerta (destino guardado pelo `go_router` da T-009). Link inválido abre `/inicio`.

### (3) A05 Alertas (`/alertas` e `/alertas/:id`)

- Acesso por ícone de alertas no topo do Início.
- Lista de 30 dias, abertos primeiro, montada com `GET /api/v1/alerts?status=open`, `?status=acknowledged` e `?status=closed&from=<agora − 30 d>` (T-011), nessa ordem, seguindo `nextCursor`.
- Atualiza com o evento SSE `alert` do cliente SSE da T-009: deduplicado por `alertId`, precedência `closed` > `acknowledged` > `open`, como no console da T-008.
- Detalhe por `GET /api/v1/alerts/{alertId}`: título, corpo, hora BRT, veículo, mini-mapa com `lastLocation` e estado atual do veículo (chip e idade da T-009).
- `lastLocation = null`: sem marcador e texto "Local do alerta indisponível" (INV-03).
- Ações: "Ver no mapa" (`/inicio?veiculo=<vehicleId>`: centraliza e abre o card; 2º toque), "Falar com a central" (A07, T-010) e "Navegar até o veículo" (A08, T-010).
- 404 mostra "Alerta não encontrado", sem nenhum dado do alerta. Não há botão de reconhecer.

### (4) A06 Modo vigilância (interruptor no A03)

- Visível com `availableActions.watchMode.available` ou `active`. O estado vem de `GET /api/v1/vehicles/{vehicleId}/watch-mode`.
- Ligar: confirmação "Avisaremos se o veículo sair 150 m deste local ou se a ignição ligar", depois `POST /api/v1/vehicles/{vehicleId}/watch-mode` com `{}`. Em 201/200, círculo de `radiusM` metros em volta de `anchor` e "Vigilância ativa desde {HH:mm BRT de activatedAt}".
- Desligar: `DELETE` (204).

| Resposta | Texto |
|---|---|
| 409 `WATCH_MODE_VEHICLE_ON` | "Desligue o veículo para ativar a vigilância" |
| 409 `WATCH_MODE_NO_FIX` | "Sem posição válida nas últimas 24 h. Não é possível ativar." |
| outro erro | "Não foi possível ativar. Tente de novo." (o interruptor volta) |

Sem conexão, o interruptor fica desabilitado (nenhuma ação que escreve offline, T-009). Nenhum comando físico parte desta tela (INV-08).

### (5) A09 Notificações (pela Conta, A10)

- Explicação PT-BR antes do pedido de permissão (Android 13+ `POST_NOTIFICATIONS`; iOS com Time Sensitive).
- Permissão negada: faixa "Alertas desligados neste celular" com "Ativar" no Início, que abre as configurações do sistema.
- Preferências por veículo × tipo de `GET /api/v1/me/alert-preferences`: `locked` mostra o interruptor travado "Sempre ativo"; `available = false` mostra "Indisponível neste rastreador".
- Mudança chama `PUT`; resposta 422 reverte o interruptor.
- Cartão no 1º acesso: "Quer ser avisado quando a ignição ligar?" (só se `ignition_on` estiver `available`).

## Testes de aceite (congelados)

Pacote Flutter `tests/acceptance/T-032/mobile` (dependência por caminho do app, como na T-009). Cliente HTTP falso, relógio fixo e `LiveMapController` falso da T-009. Datas deslocadas para o dia UTC corrente, mantendo a hora. V1 = "Gol prata".

| Arquivo | Dado / Quando / Então |
|---|---|
| `alerts/alert_detail_test.dart` — CT-UX-009 | Dado `getInitialMessage` com `tracksys://alerts/<id>` de um `sos` de V1 e sessão válida, Quando o app abre, Então o 1º quadro é o detalhe com "Pânico acionado" (1 toque). |
| idem | Dado o detalhe aberto, Quando toca "Ver no mapa", Então navega para `/inicio?veiculo=<V1>` com V1 centralizado (2 toques). |
| idem | Dado a API respondendo 404 ao alerta, Quando o detalhe abre, Então mostra "Alerta não encontrado" e nenhum título, corpo ou mapa. |
| idem | Dado sessão expirada, Quando toca o link, Então abre `/entrar` e, depois do login, o detalhe do mesmo alerta. |
| idem | Dado lista com 1 `closed`, 1 `acknowledged` e 1 `open`, Quando A05 carrega, Então a ordem é `open`, `acknowledged`, `closed`; um evento SSE `alert` com `status = "closed"` move o item para o fim. |
| idem | Dado `lastLocation = null`, Quando o detalhe abre, Então não há marcador e aparece "Local do alerta indisponível". |
| `watch_mode/watch_mode_switch_test.dart` — CT-UX-010 | Dado V1 estacionado com `available = true`, Quando ativa e o `POST` responde 201 com `activatedAt = <hoje>T00:14:00Z`, Então a confirmação traz o texto exato, o mapa mostra círculo de 150 m e "Vigilância ativa desde 21:14". |
| idem | Dado `POST` com 409 `WATCH_MODE_VEHICLE_ON`, Então "Desligue o veículo para ativar a vigilância" e o interruptor fica desligado. |
| idem | Dado `POST` com 409 `WATCH_MODE_NO_FIX`, Então o texto da A06 para esse erro. |
| idem | Dado sem conexão, Então o interruptor está desabilitado e há 0 requisições. |
| `notifications/notifications_test.dart` — CT-UX-012 | Dado 1º login no Android 14 (plataforma falsa), Quando entra, Então a explicação aparece antes da chamada de permissão e os canais `alerts_high` (alta) e `alerts_info` são pedidos ao `MainActivity` pelo canal de plataforma. |
| idem | Dado permissão negada, Então o Início mostra a faixa "Alertas desligados neste celular". |
| idem | Dado preferência de `sos`, Então o interruptor está travado em "Sempre ativo". |
| idem | Dado perfil sem `power_cut_alarm` (`available = false`), Então `power_cut` aparece "Indisponível neste rastreador". |
| idem | Dado `PUT` respondendo 422, Então o interruptor volta ao estado anterior. |

Testes unitários não congelados em `apps/mobile/test/push/`:

| Arquivo | Dado / Quando / Então |
|---|---|
| `alert_link_test.dart` | Dado `tracksys://alerts/<uuid>` válido, Então rota `/alertas/<alertId>`; esquema, host ou UUID inválidos, Então `/inicio`. |
| `push_token_sync_test.dart` | Dado cliente falso, Quando ocorrem login, retorno ao primeiro plano e renovação do token, Então cada um chama `PUT`; no logout chama `DELETE` antes de limpar a sessão. |

## Comandos de verificação

```bash
pnpm install
(cd apps/mobile && flutter pub get && flutter analyze && flutter test)
(cd tests/acceptance/T-032/mobile && flutter pub get && flutter test)
pnpm verify
```

## Definição de pronto

- [ ] Comandos verdes local e no CI; testes congelados anteriores intactos; `T-032/**` congelado no 1º commit do PR (escrito por agente de outro fornecedor).
- [ ] Ensaio ponta a ponta (marco 27/10): com o J16 de bancada, 3 `ignition_on` e 1 `offline` provocados chegam a 1 Android (teste fechado) com o app fechado e a tela bloqueada, e a 1 iPhone (TestFlight) se DEC-03 permitir. Padrão sem ignição confirmada no perfil [VALIDAR — DEC-02]: 3 `watch_mode_breach` por deslocamento no lugar dos `ignition_on`.
- [ ] `sent_at − originAt` de cada entrega ≤ 60 s; o toque abre o detalhe e "Ver no mapa" centraliza o veículo; registrado em `docs/runbooks/gates/G0.md`.
- [ ] `--dart-define=FIREBASE_*` no `mobile-release.yml` com os valores no ambiente `mobile-release`; nenhum arquivo de configuração do Firebase no repositório.
- [ ] PR `feat(app): push, alertas, vigilância e notificações (T-032)` com REQ, INV, `Risco declarado: N0` (pelo workflow), revisão de outro fornecedor no workflow e, se aplicado, o corte 3.

## Decisões já tomadas

| Dúvida provável | Resposta |
|---|---|
| 1. O toque na notificação abre o quê? | O detalhe do alerta `/alertas/:id` (A05), como manda REQ-UX-009. O mapa com o veículo centralizado fica a 1 toque ("Ver no mapa" → `/inicio?veiculo=<vehicleId>`). |
| 2. A06 entra se o prazo apertar? | A06 sai com o corte 3 de [02 §2.4](../docs/spec/02-escopo-e-fases.md#24-plano-de-corte): o fundador registra `- Corte 3 aplicado em DD/MM/AAAA HH:mm BRT: <motivo>.` na seção `## Cortes` do `G0.md` (formato da seção 5 da T-015), REQ-UX-010 passa para o F1 e o resto desta tarefa segue. A05 e A09 não têm corte (REQ-UX-009 e REQ-UX-012 são P0). |
| 3. Configuração do Firebase no repositório? | Nenhuma. `--dart-define` em build local e CI; os valores ficam nos segredos do CI e no gerenciador do fundador. |
| 4. O que fazer se a T-010 ainda não entregou A07 e A08? | O detalhe mostra só "Ver no mapa"; registrar no PR e acrescentar as duas ações quando a T-010 entrar. |
| 5. O cliente pode reconhecer um alerta ou mudar o raio da vigilância? | Não. Cliente não tem `alert.ack`; a A06 sempre envia `{}` e o raio é 150 m. |
| 6. O que mostra a A05 quando o alerta está fora do escopo ou foi apagado? | "Alerta não encontrado", sem título, corpo, mapa nem qualquer dado; a rota devolve 404 idêntico nos dois casos. |
| 7. A vigilância pode ser ligada sem internet? | Não. O interruptor fica desabilitado offline: nenhuma ação que escreve é aceita sem conexão (T-009). |
| 8. Quem recebe push no F0? | Só `tenant_owner` do cliente do veículo; a regra e a entrega estão na T-012. O app não filtra nada: mostra o que o servidor entregou. |
| 9. Existe teste congelado de Dart? | Sim, em `tests/acceptance/T-032/mobile` (pacote Flutter com dependência por caminho do app, como na T-009). Testes unitários não congelados ficam em `apps/mobile/test/`. |
