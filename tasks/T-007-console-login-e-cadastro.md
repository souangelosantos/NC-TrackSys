# T-007 — Console: login e cadastro de cliente, veículo, rastreador e vínculo

| Campo | Valor |
|---|---|
| Fase | F0 (semana S2: 14–20/10/2026) |
| Requisitos | REQ-UX-025, REQ-UX-001 (tokens no console), REQ-API-004 (rota real), REQ-API-006, REQ-API-008 (rotas de frota), REQ-API-010, REQ-API-018 (fixtures das rotas novas), REQ-DAD-007 (mapeamento HTTP), REQ-DAD-011 (reset ao abrir/encerrar vínculo), REQ-DAD-018 (transferência sem mover histórico, no módulo de vínculo; a quarentena `closed_assignment_late` está no aplicador da T-005), REQ-DAD-022, REQ-SEG-009 (parte), REQ-SEG-026 (auditoria de frota), REQ-ONB-019 (parte de UI: aviso em C05 pela sonda da T-005) |
| Invariantes | INV-03, INV-06, INV-07, INV-10 (`cut_point` explícito), INV-12 |
| Risco de revisão | **N2** na UI (02 §2.3). O módulo `fleet` da API e o vínculo com `cut_point` seguem o rito **N1** (REQ-UX-025 é N1): revisão cruzada obrigatória |
| Depende de | T-006 (02 §2.3); T-004; **T-005** para as tabelas `capability_profile`, `sim_card`, `device`, `device_assignment`, `device_state` e o helper de outbox (dependência de dados, ver Decisões) |
| Estimativa | 3 sessões (1: API de frota; 2: base do console, login, 2FA, convite; 3: telas de cadastro e vínculo + testes) |
| Bloqueado por decisão | nenhuma (formato de IMEI e protocolo do J16: [VALIDAR — DEC-02], padrão abaixo) |

## Objetivo

Permitir que a equipe da operadora entre no console e cadastre, sem SQL, os clientes, veículos, rastreadores e vínculos do piloto, com a pergunta obrigatória "Relé de bloqueio instalado?" e o `cut_point` gravado de forma explícita (INV-10). A tarefa entrega as rotas de frota do F0 no `api` (módulo `fleet`) e as telas C01 e C03–C06 de 10 §9 em `apps/console`. É o caminho que substitui o corte 5 de 02 §2.4 (cadastro por SQL).

## Contexto obrigatório

- [10](../docs/spec/10-apps-e-ux.md) §1 a §3 (onde fica o código, princípios, tokens), §9 (C01, C03 a C06, menu por papel), REQ-UX-001 e REQ-UX-025.
- [09](../docs/spec/09-api-e-contratos.md) §2 (convenções, coleção), §3 (códigos), §5 (ETag), §6 (rotas de frota), REQ-API-004, 006, 008 e 010.
- [04](../docs/spec/04-dominio-e-dados.md) §3.3 (DDL de frota, regras de `device_assignment`), §9.1 (transferência, ordem de lock e reset de `device_state`), REQ-DAD-007, 011, 018 e 022.
- [11 §10](../docs/spec/11-onboarding-e-migracao.md) (sonda `app.device_ingest_probe`, criada pela T-005) e REQ-ONB-019; [13 §11](../docs/spec/13-infra-e-operacao.md) (Sentry).
- [08](../docs/spec/08-identidade-e-seguranca.md) §3 (matriz), §11 (minimização e `audit_log`).
- Cartões [T-006](T-006-autenticacao-e-contexto-rls.md) (pipeline, idempotência, `db-errors`, `appendAudit`, rotas de auth) e T-005 (DDL de frota e outbox).

## Escopo — fazer

1. Schemas Zod em `packages/contracts/src/fleet/`, entradas no registro, OpenAPI e clientes regenerados (seção 1).
2. Módulo `apps/api/src/fleet/` com as 19 rotas da seção 1, keyset, ETag/`If-Match` e regras da seção 2; `registerConstraintProblem` para IMEI, ICCID e sobreposição.
3. Abertura e encerramento de vínculo em transação única com reset de `device_state`, outbox e NOTIFY, e transferência de veículo de [04 §9.1](../docs/spec/04-dominio-e-dados.md) (REQ-DAD-018) (seção 3).
4. Funções puras em `packages/domain/src/fleet/`: `isValidCpf`, `isValidCnpj`, `normalizePlate`.
5. `apps/console`: base (Vite, React 19, TanStack Router/Query, Tailwind 4, shadcn/ui, tokens), cliente `openapi-fetch`, SDK do Sentry com inicialização mínima (DSN opcional em `VITE_SENTRY_DSN`), login com TOTP, ativação de 2FA, convite, redefinição de senha e telas C03 a C06 (seção 4).
6. Fixtures de isolamento (`apps/api/test/scope-fixtures.ts`) e linhas da matriz para as rotas novas.
7. Testes de aceite em `tests/acceptance/T-007/` (API e UI) e roteiro manual com capturas no PR.

## Fora do escopo

- Mapa ao vivo (C02), histórico (C07), SSE e os campos `state`, `stateAge`, `availableActions` e o filtro `presence` do veículo (T-008).
- Provisionamento do rastreador no Traccar: subcomando `pilot provision` da T-014 (job automático no F1, T-024). Aqui `provisioning` só muda para `done` quando `traccar_device_id` estiver preenchido.
- Migrations: nenhuma tabela, coluna ou política nova. Encerramento de cliente e arquivamento avulso de veículo. Na transferência, o passo 7 de 04 §9.1 (alertas abertos e vigilância de V1) entra com a T-011, dona dessas tabelas.
- Host de ingestão do Sentry no `connect-src` do CSP de `app.` (T-013).
- Telas F1 (`/usuarios`, `/chips`, `/marca`, `/auditoria`), importação CSV, campos de contato do cliente citados em C03 (ver Decisões).
- Publicação do build no Caddy (T-003/T-013).

## Arquivos a criar/alterar

```
criar    packages/contracts/src/fleet/{tenants,vehicles,devices,sim-cards,assignments,capability-profiles}.ts  (+ registry, openapi, clientes)
criar    packages/contracts/design/tokens.json  packages/contracts/src/design/tokens.ts   (se ainda não existirem; conteúdo de 10 §3)
criar    packages/domain/src/fleet/{br-document.ts,plate.ts}
criar    apps/api/src/fleet/{fleet.module.ts,tenants.controller.ts,vehicles.controller.ts,devices.controller.ts,sim-cards.controller.ts,
         assignments.controller.ts,capability-profiles.controller.ts,cursor.ts,etag.ts,device-state-reset.ts,vehicle-transfer.ts}
alterar  apps/api/test/{scope-fixtures.ts,permissions.matrix.test.ts}
criar    apps/console/{package.json,tsconfig.json,vite.config.ts,index.html,components.json}
criar    apps/console/src/{main.tsx,styles.css,router.tsx,routeTree.gen.ts}  apps/console/src/api/{client.ts,problem-messages.ts}
criar    apps/console/src/auth/{use-me.ts,guards.ts}  apps/console/src/lib/{format.ts,idempotency.ts,sentry.ts}  apps/console/src/testing/harness.tsx
criar    apps/console/src/routes/{__root,login,login.totp,conta.2fa,convite,redefinir-senha,use-o-app,clientes.index,clientes.$tenantId,
         veiculos.$vehicleId,veiculos.$vehicleId.vinculo,rastreadores.index,rastreadores.$deviceId}.tsx
criar    apps/console/src/features/fleet/{tenant-form,vehicle-form,device-form,assignment-form,assignment-history,invite-owner-dialog}.tsx
criar    apps/console/src/components/ui/*   (shadcn: button, input, label, radio-group, select, checkbox, table, dialog, alert)
alterar  tests/vitest.config.ts (include `tests/acceptance/**/*.test.tsx`)  tests/tsconfig.json (jsx react-jsx, lib DOM, include *.tsx)
alterar  package.json raiz (devDependency `jsdom`)
criar    tests/acceptance/T-007/{world.ts,fleet-api.test.ts,assignments.test.ts,transfer.test.ts,pagination-etag.test.ts,ui-vinculo.test.tsx,ui-cadastro.test.tsx,ui-login.test.tsx}
```

## Especificação detalhada

### (1) Rotas e schemas

| `operationId` | Método e caminho | Permissão | Request → Response |
|---|---|---|---|
| `tenants.list` · `tenants.create` | `GET` · `POST /api/v1/tenants` | `tenant.read` · `tenant.write` | `?q&status&cursor&limit` → coleção de `Tenant` · `{kind, displayName, document?}` → 201 `Tenant` + `ETag` + `Location` |
| `tenants.get` · `tenants.update` | `GET` · `PATCH /api/v1/tenants/{tenantId}` | `tenant.read` · `tenant.write` | → 200 + `ETag` · merge patch `{displayName?, document?}` + `If-Match` → 200 |
| `vehicles.list` · `vehicles.create` | `GET` · `POST /api/v1/vehicles` | `vehicle.read` · `vehicle.write` | `?tenantId&q&cursor&limit` → coleção · `{tenantId, kind, plate?, make?, model?, color?, year?, nickname?}` → 201 `Vehicle` |
| `vehicles.get` · `vehicles.update` | `GET` · `PATCH /api/v1/vehicles/{vehicleId}` | `vehicle.read` · `vehicle.write` | → 200 + `ETag` · merge patch + `If-Match` (titular: só `nickname` e `color`) |
| `vehicles.assignments` | `GET /api/v1/vehicles/{vehicleId}/assignments` | `vehicle.read` + `device.read` | → coleção de `Assignment` (mais recente primeiro, sem paginação: ≤ 200) |
| `vehicles.transfer` | `POST /api/v1/vehicles/{vehicleId}/transfer` | `vehicle.write` + `assignment.write` (só equipe) | `{toTenantId, reason}` → 201 `{vehicle: Vehicle, transferredAt}` (o `vehicle` é o V1' do novo titular) + `Location: /api/v1/vehicles/{id de V1'}` |
| `devices.list` · `devices.create` | `GET` · `POST /api/v1/devices` | `device.read` · `device.write` | `?status&q&cursor&limit` → coleção · `{imei, model, protocol, capabilityProfileId, firmware?, simIccid?}` → 201 com `provisioning: "pending"` |
| `devices.get` · `devices.update` | `GET` · `PATCH /api/v1/devices/{deviceId}` | `device.read` · `device.write` | → 200 com `imei` completo + `ETag` · `{status?, firmware?, simIccid?}` + `If-Match` |
| `sim-cards.list` · `sim-cards.create` | `GET` · `POST /api/v1/sim-cards` | `device.read` · `device.write` | `?q&cursor&limit` → coleção · `{iccid, msisdn?, apn?}` → 201 `SimCard` |
| `device-assignments.create` | `POST /api/v1/device-assignments` | `assignment.write` | `{vehicleId, deviceId, cutPoint, isPrimary, notes?}` → 201 `Assignment` |
| `device-assignments.close` | `POST /api/v1/device-assignments/{assignmentId}/close` | `assignment.write` | `{reason, deviceStatus?}` → 200 `{validTo}` |
| `capability-profiles.list` | `GET /api/v1/capability-profiles` | `device.read` | → coleção de `CapabilityProfile` |

Todos os `POST` de criação aceitam `Idempotency-Key` opcional (T-006). Respostas:

- `Tenant` = `{id, kind: 'person'|'company', displayName, document: string|null, status: 'active'|'suspended_commercial'|'closed', createdAt, updatedAt}`.
- `Vehicle` = `{id, tenantId, plate, kind: 'car'|'motorcycle'|'truck'|'other', make, model, color, year, nickname, archivedAt, primaryDevice: {id, model, imeiLast4, profileStatus}|null, createdAt, updatedAt}` (opcionais como `null` explícito).
- `Device` = `{id, imeiLast4, imei (só em devices.get), model, protocol, firmware, capabilityProfileId, profileStatus, simIccid, status: 'stock'|'installed'|'maintenance'|'retired', provisioning: 'pending'|'done', lastContactAt, currentAssignment: {id, vehicleId, cutPoint, validFrom}|null, ingestProbe: {lastQuarantinedAt, lastError, quarantined24h}, createdAt, updatedAt}` (`ingestProbe` = `LEFT JOIN LATERAL app.device_ingest_probe(d.id)`, T-005; nunca traz IMEI nem payload).
- `SimCard` = `{id, iccid, msisdn, apn, provider: 'emnify', status, createdAt}`. `Assignment` = `{id, vehicleId, deviceId, cutPoint: 'fuel_pump'|'ignition'|'starter'|null, isPrimary, validFrom, validTo, notes}`. `CapabilityProfile` = `{id, model, firmwareRange, protocol, version, status: 'draft'|'homologated'|'suspended', capabilities: Record<string, 'yes'|'no'|'unknown'>}`.

Validação de entrada (objetos estritos): `plate` `^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$` (mensagem "Placa deve seguir o padrão AAA1A11."); `year` 1950–2100; `make`, `model`, `color`, `nickname` ≤ 60; `displayName` 1–200; `document` `^\d{11}$|^\d{14}$` mais dígito verificador (`rule: "document_check_digit"`); `imei` `^\d{15}$` [VALIDAR — DEC-02: igual ao `uniqueId` do Traccar no gt06]; `iccid` `^\d{18,20}$`; `msisdn` E.164; `apn` ≤ 100; `notes` ≤ 2.000; `reason` 1–500; `deviceStatus` `stock`|`maintenance` (padrão `stock`); `toTenantId` uuid. **`cutPoint` é chave obrigatória** com valor do enum ou `null` (`z.enum([...]).nullable()` sem `.optional()`): ausente → 422 `errors[0] = {path: "cutPoint", rule: "required"}`.

Exemplo (`agente.alfa`, console, `Origin: https://app.tracksys.com.br`, `Idempotency-Key: 0192a1b2-9a00-7000-8000-000000000201`):

```http
POST /api/v1/device-assignments
{"vehicleId":"0192a1b2-0000-7000-8000-0000000000f1","deviceId":"0192a1b2-0000-7000-8000-0000000000d1",
 "cutPoint":"fuel_pump","isPrimary":true,"notes":"Relé na bomba, sob o banco do motorista"}
```

```json
{
  "id": "0192a1b2-0e00-7000-8000-00000000e001", "vehicleId": "0192a1b2-0000-7000-8000-0000000000f1",
  "deviceId": "0192a1b2-0000-7000-8000-0000000000d1", "cutPoint": "fuel_pump", "isPrimary": true,
  "validFrom": "2026-10-16T13:05:12.481Z", "validTo": null, "notes": "Relé na bomba, sob o banco do motorista"
}
```

Sem a chave `cutPoint` (422, `application/problem+json`):

```json
{
  "type": "https://api.tracksys.com.br/problems/validation-failed", "title": "Dados inválidos", "status": 422,
  "code": "VALIDATION_FAILED", "detail": "1 campo inválido.", "instance": "/api/v1/device-assignments",
  "correlationId": "0192a1b2-7f00-7000-8000-00000000aa07",
  "errors": [{ "path": "cutPoint", "rule": "required", "message": "Informe o ponto de corte ou null (sem bloqueio instalado)." }]
}
```

### (2) Regras dos handlers

- Coleções (REQ-API-006): keyset sem OFFSET, escopo aplicado pela RLS antes da paginação. Ordem: `vehicles` por `(coalesce(plate, ''), id)` crescente (09 §9.1); `tenants`, `devices` e `sim-cards` por `(created_at, id)` decrescente. Cursor = base64url de `{"k":[…]}` validado por Zod; inválido → 422 `{path: "cursor", rule: "cursor_invalid"}`. Filtro `q`: `tenants` por `display_name ILIKE` ou documento exato; `vehicles` por placa ou apelido `ILIKE`; `devices` pelos últimos dígitos do IMEI (≥ 4 dígitos). IMEI completo nunca vai em cursor, URL ou log.
- ETag (09 §5): `"u" || (extract(epoch FROM updated_at) * 1000000)::bigint`. PATCH sem `If-Match` → 428 `PRECONDITION_REQUIRED`; `UPDATE … SET …, updated_at = greatest(clock_timestamp(), updated_at + interval '1 microsecond') WHERE id = $1 AND updated_at = $2 RETURNING updated_at`; 0 linhas → relê: ausente → 404, presente → 412 `PRECONDITION_FAILED` com o `ETag` atual. Merge patch (RFC 7396): `null` limpa campo opcional.
- Recurso é carregado sob RLS antes da regra fina: invisível → 404; visível sem direito → 403. Titular (`tenant_owner`) em `vehicles.update` com campo diferente de `nickname`/`color` → 403 `FORBIDDEN`. No escopo `tenant`, `Tenant.document` sai `null` (08 §11, minimização).
- `devices.create`: perfil inexistente → 422 `{path: "capabilityProfileId", rule: "not_found"}`; `model`/`protocol` diferentes do perfil → 422 `rule: "profile_mismatch"` (perfil J16: protocolo `gt06` [VALIDAR — DEC-02]); `INSERT app.device` (`status = 'stock'`) e `INSERT app.device_state (device_id, operator_id) … ON CONFLICT (device_id) DO NOTHING` na mesma transação. `provisioning` = `pending` se `traccar_device_id` é NULL, senão `done`. Conflito em `device_imei_active_key` → 409 `DEVICE_ALREADY_REGISTERED` sem operadora, id ou nome no corpo, e `audit_log` `device.create` com `result = 'denied'` gravado em transação própria após o ROLLBACK (CT-DAD-022). `sim_card_iccid_key` e `device_sim_active_key` → 409 `SIM_ALREADY_REGISTERED`; ICCID de outra operadora (23503) → 404.
- `devices.update`: `status` só `stock`, `maintenance` ou `retired`, e só sem vínculo aberto (senão 409 `CONFLICT`); `installed` só pelo vínculo.
- `lastContactAt` vem de `device_state.last_contact_at`; `currentAssignment` e `primaryDevice` do vínculo aberto (`valid_to IS NULL`, primário).
- `audit_log` (`appendAudit`, mesma transação, `correlation_id`): `tenant.create|update`, `vehicle.create|update`, `device.create|update`, `assignment.create|close` (com `reason` no encerramento).

### (3) Vínculo: abrir e encerrar (escopo `operator`, uma transação)

Ordem de lock igual à da projeção (04 §9.1): `device_state` primeiro.

**Abrir** (`device-assignments.create`): (1) `SELECT … FROM app.device_state WHERE device_id = $d FOR UPDATE` (linha ausente → `INSERT` padrão e relê); (2) `SELECT status FROM app.device WHERE id = $d FOR UPDATE`: invisível → 404, `status <> 'stock'` → 409 `CONFLICT`; (3) veículo invisível → 404, arquivado → 409 `CONFLICT`; (4) `INSERT app.device_assignment (operator_id, tenant_id, vehicle_id, device_id, cut_point, is_primary, notes, installed_by)` com `valid_from` padrão `now()`; 23P01 em `device_assignment_device_excl` ou `device_assignment_primary_excl` → 409 `ASSIGNMENT_OVERLAP`; (5) `UPDATE app.device SET status = 'installed'`; (6) reset abaixo com o vínculo novo; (7) outbox `device.state.updated.v1` pelo helper de `packages/db` (T-005) e `pg_notify('device_state', '{"d":"<deviceId>","r":<revision>,"o":"<operatorId>","t":"<tenantId>"}')` (03 §7); (8) `audit_log` `assignment.create`. Resposta 201 com `Location: /api/v1/vehicles/{vehicleId}/assignments`.

**Encerrar** (`device-assignments.close`): (1) vínculo invisível → 404; `valid_to` preenchido → 409 `CONFLICT`; (2) lock de `device_state` do rastreador; (3) `T = greatest(now(), coalesce(last_fix_at + interval '1 second', now()))` (corte não retroativo; o gatilho `device_assignment_close` recusa `T` anterior a posição gravada → 409); (4) `UPDATE … SET valid_to = T`; (5) `device.status = deviceStatus`; (6) reset com vínculo NULL; (7) outbox e NOTIFY (`"t"` nulo); (8) `audit_log` `assignment.close` com `reason`. Resposta `{validTo: T}`.

Reset (`device-state-reset.ts`, REQ-DAD-011; `revision` sobe pelo gatilho `device_state_revision` da T-005):

```sql
UPDATE app.device_state
   SET tenant_id = $2, vehicle_id = $3, assignment_id = $4,       -- os três NULL no encerramento
       last_fix_at = NULL, lat_e7 = NULL, lon_e7 = NULL, speed_kmh_x10 = NULL, course_deg = NULL, ignition = NULL,
       motion = 'unknown', relay_state = 'unknown', relay_observed_at = NULL, power_state = 'unknown', aux = '{}'
 WHERE device_id = $1
RETURNING revision;                                               -- last_contact_at é mantido (contato é do rastreador)
```

**Transferir veículo** (`vehicles.transfer`, REQ-DAD-018, [04 §9.1](../docs/spec/04-dominio-e-dados.md); mesma transação no escopo `operator`, `vehicle-transfer.ts`): (1) V1 invisível → 404, arquivado → 409 `CONFLICT`; `toTenantId` invisível → 404, igual ao cliente de V1 → 422 `{path: "toTenantId", rule: "same_tenant"}`, cliente `closed` → 409 `CONFLICT`; (2) `SELECT … FROM app.device_state WHERE device_id = ANY($rastreadores dos vínculos abertos de V1) ORDER BY device_id FOR UPDATE`; (3) `T = greatest(now(), max(last_fix_at) + interval '1 second')` (sem posição: `now()`; corte retroativo proibido); (4) `valid_to = T` em todos os vínculos abertos de V1; (5) `UPDATE app.vehicle SET archived_at = T` em V1 e depois `INSERT` de V1' no cliente destino copiando `plate`, `kind`, `make`, `model`, `color` e `year`, nessa ordem (unicidade de placa); (6) `INSERT` dos vínculos de V1' com `valid_from = T`, mesmo `cut_point` e `is_primary`; (7) reset de `device_state` de cada rastreador para o vínculo novo (mesmo `device-state-reset.ts`); (8) `audit_log` `vehicle.transfer` com `reason`, outbox `device.state.updated.v1` e NOTIFY por rastreador. Resposta 201 `{vehicle: <V1'>, transferredAt: T}`. Posições de V1 nunca são atualizadas: continuam com o cliente e o veículo de origem (INV-06); o titular antigo vê V1 arquivado e o novo só fatos com `fix_time ≥ T`. Fix tardio do vínculo encerrado recebido mais de 24 h depois de `T` vai para quarentena `closed_assignment_late` pelo aplicador da T-005.

### (4) Console (`apps/console`)

- Dependências de workspace só `@tracksys/contracts` e `@tracksys/domain` (03 §12). Pacotes: `react`/`react-dom` 19, `vite`, `@tanstack/react-router` + `@tanstack/router-plugin` (rotas por arquivo; `routeTree.gen.ts` versionado), `@tanstack/react-query`, `tailwindcss` 4 + `@tailwindcss/vite`, componentes shadcn/ui copiados em `src/components/ui`, `openapi-fetch`, `qrcode` (QR do TOTP; sem alternativa sem dependência), `@testing-library/react` e `@testing-library/user-event` (dev).
- `api/client.ts`: `createClient<paths>({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '', credentials: 'include' })` com o tipo gerado em `packages/contracts/generated/ts/schema.d.ts`; envia `X-Operator-Id` quando o usuário escolheu operadora (guardada em `sessionStorage`, com `try/catch`). Dev: proxy do Vite de `/api` para `http://127.0.0.1:3000` (origem `http://localhost:5173`, aceita pelo `api` em `development`). `problem-messages.ts` traduz pelo `code`, nunca pelo `title`.
- Sentry (`lib/sentry.ts`, pacote `@sentry/react` na última versão estável com ≥ 2 semanas, citada no PR): `initSentry(import.meta.env)` roda em `main.tsx` antes do render; `VITE_SENTRY_DSN` ausente ou vazio → não chama `Sentry.init` (desligado, padrão em desenvolvimento e nos testes); com DSN → `Sentry.init({ dsn, sendDefaultPii: false, tracesSampleRate: 0 })`, sem replay, com `beforeSend` que remove cookies, headers e query string do `request`. Nenhum IMEI, token ou coordenada vai em breadcrumb ou mensagem.
- Tokens (REQ-UX-001): `tokens.json` de 10 §3; `main.tsx` grava `--tk-<nome>` no `:root` a partir de `tokens.ts`; `styles.css` usa `@theme` com `var(--tk-…)`. Nenhum hex em `apps/console/src`. Tema escuro único. Estado nunca só por cor (texto + ícone). Horários em `America/Sao_Paulo`.
- Rotas e regras:

| Rota | Regra |
|---|---|
| `/login` (C01) | E-mail + senha → `auth.sign-in-email`. `INVALID_CREDENTIALS` → "E-mail ou senha inválidos."; `RATE_LIMITED` → "Muitas tentativas. Tente de novo em N min." (`retryAfterS`); `twoFactorRedirect` → `/login/totp` (6 dígitos ou "Usar código de recuperação"). Depois, `GET /api/v1/me`: 403 `TWO_FACTOR_ENROLLMENT_REQUIRED` → `/conta/2fa`; 400 `OPERATOR_SELECTION_REQUIRED` → seletor de operadora; só memberships de cliente → `/use-o-app` ("Acesse pelo aplicativo"); equipe → `/clientes` |
| `/conta/2fa` | Senha → `auth.two-factor-enable` → QR do `totpURI`, segredo em texto e 10 códigos (baixar `.txt`) → código → `auth.verify-totp` → `/clientes` |
| `/convite`, `/redefinir-senha` | Token lido de `location.hash` e apagado da URL (`history.replaceState`); senha + confirmação; erros pelo `rule` (`password_min_length` → "Use pelo menos 10 caracteres."; `password_common` → "Senha muito comum. Escolha outra."); `INVITATION_INVALID` → "Convite inválido ou vencido." |
| `/clientes`, `/clientes/:tenantId` (C03) | Lista com busca e "Carregar mais"; novo cliente (pessoa/empresa, nome, CPF/CNPJ com máscara e validação de dígito pela função do domínio: "CPF inválido"/"CNPJ inválido"); detalhe com edição (`If-Match`; 412 → "Os dados mudaram. Recarregue."), veículos do cliente, "Novo veículo" e "Convidar titular" (`invitations.create` com `role: 'tenant_owner'` e `Idempotency-Key` = UUID gerado ao abrir o diálogo) |
| `/veiculos/:vehicleId` (C04) | Placa normalizada por `normalizePlate` (maiúsculas, sem hífen nem espaço) antes do envio; tipo, marca, modelo, cor, ano, apelido; vínculo atual e anteriores (`vehicles.assignments`), com "Vincular rastreador" (sem vínculo aberto) e "Encerrar vínculo" (motivo obrigatório; destino "Estoque" ou "Manutenção") |
| `/rastreadores`, `/rastreadores/:deviceId` (C05) | Lista com IMEI mascarado (`***0001`), modelo, perfil e status do perfil ("Rascunho", "Homologado", "Suspenso"), status, "Último contato: nunca" ou "há X", vínculo atual e aviso "Comunicando sem vínculo" quando `ingestProbe.quarantined24h > 0` e `ingestProbe.lastError` ∈ {`no_assignment`, `unknown_device`, `device_identity_mismatch`} ([11 §10](../docs/spec/11-onboarding-e-migracao.md), REQ-ONB-019). Novo rastreador: IMEI ("IMEI deve ter 15 dígitos"), perfil (de `capability-profiles.list`), firmware, ICCID e MSISDN opcionais (cria o chip antes; 409 `SIM_ALREADY_REGISTERED` segue com o ICCID existente; 404 no rastreador → "Chip não encontrado nesta operadora"). IMEI completo só no detalhe |
| `/veiculos/:vehicleId/vinculo` (C06) | Rastreador em estoque (`devices.list?status=stock`); "Relé de bloqueio instalado?" Sim/Não **sem padrão** e "Salvar" desativado até a resposta; Sim → ponto de corte obrigatório ("Bomba de combustível", "Ignição pós-chave", "Motor de arranque") com a mensagem "Escolha o ponto de corte" e "Salvar" desativado até a escolha; Não → envia `"cutPoint": null` e o detalhe mostra "Sem bloqueio instalado"; "Rastreador principal" marcado por padrão. O texto de efeito de cada ponto de corte vem de `packages/domain/src/commands/texts.ts` (06 §15); se o arquivo não existir em `main`, mostre só o nome e registre no PR — não escreva texto de segurança novo |

Menu do F0 (equipe: `operator_admin` e `operator_agent`): Clientes e Rastreadores. A autorização vale no `api`; o menu só esconde.

## Testes de aceite (congelados)

`tests/acceptance/T-007/`. `world.ts` usa `seedIdentityWorld` (T-006) com operadoras novas por arquivo, cria um perfil `J16-T007-<aleatório>` `draft` (conexão `tracksys_owner`, política `capability_profile_owner_all` da T-005) e rastreadores com IMEI `3593390` + 8 dígitos aleatórios (testes repetíveis no mesmo banco). Os testes de UI usam `// @vitest-environment jsdom`, `src/testing/harness.tsx` e um `fetch` falso que grava as requisições.

| Arquivo | Dado / Quando / Então |
|---|---|
| `fleet-api.test.ts` (CT-API-004, CT-SEG-009 parte, CT-API-008 parte, CT-DAD-022, CT-SEG-026 parte, CT-ONB-019 parte) | `agente.alfa`: `POST /api/v1/vehicles` com `{"tenantId":"<A1>","kind":"car","plate":"abc-1234"}` → 422 com `errors[0]` `{path: "plate", rule: "pattern"}`; com `"cor2":"x"` → `rule = "unrecognized_key"`; com `"plate":"TST1A23"` → 201, `ETag` e `audit_log` `vehicle.create` (`actor_type = 'user'`, `result = 'success'`). `dono.a1`: `PATCH /api/v1/vehicles/{V1}` com `{"plate":"ABC1D23"}` e `If-Match` atual → 403; com `{"nickname":"Gol prata"}` → 200; em V2 → 404. `admin.beta` `PATCH /api/v1/vehicles/{V1}` → 404. `dono.a2` `GET /api/v1/vehicles/{V1}` e `GET /api/v1/vehicles/{uuid aleatório}` → 404 com `type`, `title` e `detail` iguais. Rastreador da Alfa `installed` com IMEI I1: Beta `POST /api/v1/devices` com I1 → 409 `DEVICE_ALREADY_REGISTERED`, corpo sem o id nem o nome da Alfa, e `audit_log` da Beta `device.create` `denied`; IMEI I2 `retired` na Alfa → Beta grava (201). Cliente com `document: "52998224724"` → 422 `document_check_digit`; `"52998224725"` → 201; `dono.a1` lê o próprio cliente → `document: null`. `dono.a1` `GET /api/v1/capability-profiles` → 403. CT-ONB-019 (C05): rastreador da Alfa em estoque com 4 linhas de inbox `quarantined`/`no_assignment` na última hora (gravadas como `tracksys_ingest`, `device.uniqueId` = IMEI dele) → `devices.get` com `ingestProbe.quarantined24h = 4` e `lastError = "no_assignment"`; o mesmo rastreador lido por `admin.beta` → 404 |
| `transfer.test.ts` (CT-DAD-018; datas deslocadas para o dia UTC corrente) | V1 de A1 com R1 e 1.000 posições gravadas por `ingestTraccar` (T-005) até `now() − 60 s`. `agente.alfa` transfere V1 para A2 com `reason` → 201 com V1' (`tenantId = A2`, mesma placa), V1 com `archivedAt = transferredAt` (`T`), as 1.000 posições continuam com `tenant_id = A1` e `vehicle_id = V1`, o contexto `tenant` de A2 conta 0 posições com `fix_time < T`, `device_state` de R1 com `tenant_id = A2`, `vehicle_id = V1'` e `revision` maior, e `audit_log` `vehicle.transfer` com o motivo. Fix com `fix_time = T + 60 s` recebido em `T + 65 s` → grava em V1'; fix `T − 120 s` recebido em `T + 5 min` → grava em V1; outro fix `T − 120 s` (outro `source_event_id`) recebido em `T + 48 h` → quarentena `closed_assignment_late`. Repetir a transferência → 409; `toTenantId` = A1 → 422 `same_tenant`; cliente da Beta → 404; `dono.a1` → 403 |
| `assignments.test.ts` (CT-UX-025 API, CT-DAD-007 HTTP, CT-DAD-011) | `POST /api/v1/device-assignments` para V1 e R1 (em estoque) sem a chave `cutPoint` → 422 `errors[0].path = "cutPoint"`; com `"cutPoint":"trunk"` → 422 `rule = "enum"`; com `"cutPoint": null` → 201, `vehicles.assignments` mostra `cutPoint: null`, R1 `installed`, e `device_state` de R1 com `tenant_id = A1`, `vehicle_id = V1`, `ignition` NULL, `motion = 'unknown'` e `revision` maior que antes; 1 linha nova na outbox. R3 como primário em V1 → 409 `ASSIGNMENT_OVERLAP`; R1 (instalado) em V2 de A2 → 409 `CONFLICT`; `agente.alfa` com `vehicleId` = veículo da Beta → 404. Encerrar com `{"reason":"Troca de rastreador","deviceStatus":"maintenance"}` → 200 com `validTo`, R1 `maintenance`, `device_state` de R1 com `tenant_id` NULL e `revision` maior, contexto `tenant` de A1 não vê a linha; encerrar de novo → 409; `audit_log` `assignment.close` com o motivo. `dono.a1` `POST /api/v1/device-assignments` → 403 |
| `pagination-etag.test.ts` (CT-API-006, CT-API-010) | Operadora com 120 veículos (placas `TST0A00` a `TST0A99` e `TST0B00` a `TST0B19`): `agente` lista sem `limit` e segue os cursores → 50, 50 e 20 itens, último `nextCursor = null`, sem repetição nem falta, mesmo com o veículo `AAA0A00` criado entre a 1ª e a 2ª página; `limit=201` → 422; cursor adulterado → 422 `cursor_invalid`. Cliente A1: `GET` devolve `ETag` `"u…"`; `PATCH /api/v1/tenants/{A1}` sem `If-Match` → 428; com `If-Match: "u1760972400000000"` → 412 com o `ETag` atual no header; com o atual → 200 e `ETag` novo diferente |
| `ui-vinculo.test.tsx` (CT-UX-025 UI) | Formulário de vínculo sem resposta ao relé → "Salvar" desativado; "Sim" sem ponto de corte → texto "Escolha o ponto de corte", "Salvar" desativado e 0 `POST`; "Bomba de combustível" → `POST` com `"cutPoint":"fuel_pump"`; "Não" → `POST` com a chave `cutPoint` presente e valor `null`; após o 201, o detalhe mostra "Sem bloqueio instalado" |
| `ui-cadastro.test.tsx` (CT-UX-025 placa, REQ-UX-001 parte) | Placa digitada `tst-1a23` → corpo do `POST` com `"plate":"TST1A23"`; CPF `529.982.247-24` → "CPF inválido" e 0 `POST`; IMEI com 14 dígitos → "IMEI deve ter 15 dígitos"; nenhum arquivo em `apps/console/src` contém `#[0-9A-Fa-f]{6}`. Detalhe do rastreador com `ingestProbe {quarantined24h: 4, lastError: "no_assignment"}` → "Comunicando sem vínculo"; com `quarantined24h: 0` → sem o aviso |
| `ui-login.test.tsx` (C01) | Resposta 401 `INVALID_CREDENTIALS` → "E-mail ou senha inválidos."; `twoFactorRedirect: true` → campo de código TOTP; `/me` só com membership `tenant_owner` → "Acesse pelo aplicativo"; `/me` com 403 `TWO_FACTOR_ENROLLMENT_REQUIRED` → tela de ativação de 2FA. `initSentry({})` não chama `Sentry.init` (módulo simulado); com `VITE_SENTRY_DSN` de teste chama uma vez com `sendDefaultPii: false` |

Roteiro manual (capturas no PR): `admin.alfa` entra com TOTP; cria cliente, veículo e rastreador; vincula com "Sim → Bomba de combustível"; encerra para "Estoque"; refaz com "Não".

## Comandos de verificação

```bash
pnpm install && cp .env.example .env && pnpm db:up && pnpm db:migrate
pnpm contracts:check && pnpm db:check
pnpm --filter @tracksys/api test          # scope.e2e inclui as 19 rotas novas
pnpm --filter @tracksys/console typecheck && pnpm --filter @tracksys/console test
pnpm --filter @tracksys/console build     # apps/console/dist estático
pnpm verify
```

## Definição de pronto

- Comandos verdes local e no CI; `acceptance-freeze` verde; clientes TS e Dart regenerados no mesmo PR.
- Revisão cruzada registrada (rito N1 do módulo `fleet`); capturas do roteiro manual no PR.
- Nenhum IMEI completo em log, URL ou cursor.

## Decisões já tomadas

| Dúvida provável | Resposta |
|---|---|
| Criar as tabelas de frota aqui? | Não. Vêm da migration da T-005 (04 §3.7). Se a T-005 não estiver em `main`, espere; não crie migration. A dependência de dados não aparece em 02 §2.3 e está registrada no PR. |
| Quem implementa as rotas de frota? | Esta tarefa (módulo `fleet` do `api`), junto com as telas que as usam. |
| Normalizar placa na API? | Não. A UI normaliza (`tst-1a23` → `TST1A23`); a API valida o padrão e recusa `abc-1234` (CT-API-004 e CT-UX-025 juntos). |
| `cutPoint` pode faltar? | Não. A chave é obrigatória; `null` explícito = "Sem bloqueio instalado" (INV-10). A UI não tem resposta padrão para o relé. |
| `state`, `availableActions`, `presence` no veículo? | Na T-008. Acrescentar campo de resposta e parâmetro de query é mudança aditiva (09 §10). |
| `deviceStatus` no encerramento não está em 09 §6? | Campo opcional novo (aditivo), padrão `stock`, para cumprir C06 ("devolve o rastreador a `stock` ou `maintenance`"). |
| `last_contact_at` no reset? | Mantido: é do rastreador, não do veículo. Posição, ignição e estados vão a NULL/`unknown`. O aviso "Comunicando sem vínculo" vem da sonda `app.device_ingest_probe` (T-005), não de `last_contact_at`: mensagem em quarentena não atualiza `device_state`. |
| Transferência de veículo aqui, sem rota em 09 §6? | Sim (REQ-DAD-018, decisão da v2.0). `vehicles.transfer` é rota nova aditiva no registro de contratos; o PR registra o acréscimo para 09 §6. A quarentena de fix tardio é do aplicador da T-005; esta tarefa só a prova no CT-DAD-018. |
| Sentry no console sem DSN? | Desligado. Sem `VITE_SENTRY_DSN` o SDK nem inicializa; o DSN de produção e o host no CSP de `app.` são da T-013. |
| Telefone e e-mail de contato do cliente (C03)? | Fora do F0: as colunas não existem em 04 nem em `POST /api/v1/tenants` (09 §6). Registrado como pendência. |
| `provisioning: "failed"`? | Não é emitido aqui: sem job de provisionamento, só `pending`/`done` derivados de `traccar_device_id`, que o `pilot provision` da T-014 grava. |
| Titular no console? | Não. Usuário só com membership de cliente vê "Acesse pelo aplicativo". |
| Fuso na UI | `America/Sao_Paulo` (BRT, sem horário de verão); API e banco em UTC. |
| Por que criar `device_state` junto com o rastreador? | Para que abrir vínculo trave sempre a mesma linha primeiro (ordem de lock da projeção, 04 §9.1) e o reset nunca dependa de a ingestão já ter visto o rastreador. `ON CONFLICT DO NOTHING` convive com a T-005. |
| Ordem das coleções | Veículos por placa (09 §9.1); clientes, rastreadores e chips do mais novo para o mais antigo, para não pôr nome, documento ou IMEI no cursor. |
| `vehicles.assignments` sem paginação? | Um veículo tem poucos vínculos no histórico; teto de 200 itens. Paginar depois é aditivo. |
| Commit | `feat(api): rotas de frota (T-007)`, `feat(console): login e cadastro (T-007)`, `test(console): aceite (T-007)`. |
