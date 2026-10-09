# ADR-008 — Contrato primeiro: Zod → OpenAPI → clientes TS e Dart gerados; SSE para tempo real

**Status:** Aceito em 07/10/2026

## Contexto

- Três consumidores da API (console em TypeScript, app em Dart, testes de aceite) e dois tipos de evento produzidos pelo servidor (outbox e SSE). Deriva de tipo entre eles vira bug em produção.
- A v1.1 (p. 20–23) usava REST + WebSocket com OpenAPI e AsyncAPI, Problem Details (RFC 9457), `Idempotency-Key` e ETag/`If-Match`.
- Agentes de IA escrevem os dois lados do contrato. Um contrato gerado transforma deriva em erro de compilação, que o próprio agente corrige.

## Decisão

1. **Fonte única:** schemas Zod 4 em `packages/contracts` para corpo de requisição e resposta, parâmetros, erros (Problem Details), payloads de eventos de domínio (outbox) e eventos SSE. JSON em camelCase.
2. **Build:** `pnpm --filter @tracksys/contracts build` gera `packages/contracts/openapi/openapi.json` (OpenAPI 3.1). A biblioteca de conversão compatível com Zod 4 é escolhida na primeira tarefa de contratos [VALIDAR].
3. **Clientes gerados e versionados no repositório:** TypeScript com `openapi-typescript` em `packages/contracts/generated/ts/`; Dart com openapi-generator `dart-dio` em `packages/contracts/generated/dart/`, consumido por `apps/mobile` como dependência de caminho.
4. **CI:** regenera OpenAPI e clientes e falha com `git diff --exit-code`; compara o OpenAPI com o de `main` e falha em mudança incompatível dentro de `/api/v1` (ferramenta de diff de OpenAPI [VALIDAR]).
5. **Validação em runtime:** o `api` valida entrada e saída com os mesmos schemas (pipe Zod próprio, sem class-validator); o `worker` valida payload de job e de outbox ao consumir.
6. **Evolução:** em `/api/v1` só mudança aditiva, com campo novo opcional. Remoção ou troca de tipo exige `/api/v2`, ou evento `.v2` publicado em paralelo durante a migração (regras em [09](../spec/09-api-e-contratos.md)).
7. **Tempo real por SSE:** `GET /api/v1/stream` envia `vehicle.state` com `id: <revision>`; reconexão com `Last-Event-ID` recebe o snapshot do escopo ([03 §7](../spec/03-arquitetura.md#7-tempo-real-sse--listennotify)). Escritas e comandos sempre por POST. O app usa SSE só em primeiro plano; em segundo plano, push.

## Alternativas consideradas

- **Código primeiro (decorators NestJS → OpenAPI).** Por que não: o tipo nasce no servidor e só existe depois que ele compila; não cobre eventos nem payload de job.
- **tRPC.** Por que não: só TypeScript; o app Dart ficaria de fora.
- **GraphQL.** Por que não: servidor, cache e autorização por campo mais complexos; REST + RLS resolvem o caso.
- **gRPC/protobuf.** Por que não: o navegador precisa de proxy; webhooks e ferramentas web pioram.
- **WebSocket (v1.1).** Por que não: canal bidirecional não é necessário. SSE é HTTP comum (Caddy, HTTP/2, reconexão nativa com `Last-Event-ID`), mais simples de autenticar e testar.
- **TypeBox.** Equivalente. Zod 4 fica pela familiaridade dos agentes e pela conversão nativa para JSON Schema.

## Consequências

**Positivas**
- Deriva entre servidor, console e app vira erro de compilação.
- Um schema valida API, eventos e jobs.
- Toda mudança de contrato aparece num diff revisável.

**Negativas**
- Código gerado no repositório aumenta os diffs (aceito: diff de contrato é revisão útil).
- O gerador Dart produz código verboso e exige Java no CI [VALIDAR].
- Flutter não tem cliente SSE oficial: o app usa um parser mínimo sobre a resposta em stream do `dio` ([10](../spec/10-apps-e-ux.md)).
- SSE é unidirecional: não há canal do cliente para o servidor além do HTTP comum.

## Gatilho de revisão

- Necessidade de canal bidirecional de baixa latência (ex.: chat em tempo real no app) → WebSocket só para esse caso.
- Mais de 5.000 conexões SSE simultâneas por processo `api`, ou memória do `api` > 80% do limite por causa delas → gateway de tempo real dedicado [PREMISSA].
- O gerador Dart bloquear uma entrega por mais de 1 dia → trocar a forma de geração.

## Relacionados

- INV-04, INV-12.
- REQ-ARQ-007, REQ-ARQ-011.
- [09](../spec/09-api-e-contratos.md) (rotas, erros, idempotência, evolução); [07](../spec/07-alertas-e-tempo-real.md) (eventos SSE); [10](../spec/10-apps-e-ux.md).
- [ADR-001](ADR-001-monolito-modular-nestjs.md), [ADR-007](ADR-007-app-unico-flutter-marca-dinamica.md).
