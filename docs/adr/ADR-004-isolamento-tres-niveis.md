# ADR-004 — Isolamento em 3 níveis (plataforma → operadora → cliente): RLS FORCE, FK composta, contexto por transação, teste de catálogo no CI

**Status:** Aceito em 07/10/2026

## Contexto

- Três níveis de autoridade: plataforma (Versix) → operadora → cliente (`tenant`). Uma operadora nunca vê outra; um cliente nunca vê outro; a equipe da operadora vê todos os clientes dela.
- Agentes de IA escrevem a maior parte do código. Um filtro esquecido numa consulta é provável. Vazar localização é o pior incidente de dados possível (segurança física e LGPD).
- A v1.1 (p. 17) trazia FK composta `(tenant_id, id)`, RLS FORCE, papel de aplicação não dono, `set_config` local por transação e o CT-01, mas modelava dois níveis e resolvia a central com subconsulta por tenant.

## Decisão

1. Toda linha de cliente tem `operator_id` e `tenant_id` NOT NULL e imutáveis; toda linha de operadora tem `operator_id`.
2. RLS ENABLE + FORCE em toda tabela do schema `app` (inclusive partição), fora da allowlist `rlsExempt` (CAT-01), e ao menos uma política em cada uma (CAT-02), com USING e WITH CHECK para SELECT, INSERT, UPDATE e DELETE:
   - tabela de cliente: `operator_id = app.current_operator_id() AND (app.current_scope() = 'operator' OR tenant_id = ANY (app.current_tenant_ids()))`;
   - tabela de operadora: `operator_id = app.current_operator_id()`, escrita só com escopo `operator`;
   - `operator`: `id = app.current_operator_id()`.
3. Contexto por transação, nunca por sessão: `SELECT set_config('app.operator_id', $1, true), set_config('app.scope', $2, true), set_config('app.tenant_ids', $3, true)`. As funções `app.current_operator_id()`, `app.current_scope()` e `app.current_tenant_ids()` são STABLE e falham fechado: contexto vazio vira NULL e nenhuma linha passa. O contexto aceita `app.user_id` opcional (`app.current_user_id()`, mesma regra), usado pelas políticas de tabela de usuário, como `device_key_self`.
4. Escopos: `operator` para a equipe da operadora (o papel refina a permissão na aplicação, [08](../spec/08-identidade-e-seguranca.md)); `tenant` com a lista de tenants da membership para `tenant_owner` e `tenant_member`.
5. FK composta: toda FK para tabela com `tenant_id` inclui `tenant_id` (e `operator_id` quando aplicável); toda FK para tabela de operadora inclui `operator_id`. Uma referência cruzada falha na FK mesmo que a política tenha erro.
6. Papéis de banco: `tracksys_owner` (dono, só migrations), `tracksys_app` (NOBYPASSRLS, não dono), `tracksys_ingest` (inbox e `app.resolve_device_for_ingest` SECURITY DEFINER), `tracksys_ops_ro` (métricas agregadas, sem telemetria).
7. `platform_admin` não tem membership. Acesso a dados de uma operadora só com `platform_support_grant` ativo (motivo e expiração), registrado em `audit_log` com `actor_type = 'support'`.
8. Agentes de IA operam com o contexto de quem os aciona (INV-07, INV-11; [ADR-010](ADR-010-operacao-assistida-por-ia.md)).
9. O verificador de catálogo de `packages/db` roda no CI contra o banco migrado e falha se: tabela do schema `app` (inclusive partição) sem RLS ENABLE + FORCE fora da allowlist (`rlsExempt`); tabela com RLS e nenhuma política; tabela de `app` sem `operator_id` NOT NULL fora da allowlist (`withoutOperatorId`, com justificativa) ou com `tenant_id` anulável fora de `nullableTenantId`; FK para tabela com `operator_id`/`tenant_id` que não liga essas colunas na mesma posição (FK com colunas trocadas também falha); `tracksys_app` superusuário, dono de objeto, com BYPASSRLS ou membro (direto ou herdado) de papel com esses poderes; `tracksys_app` com UPDATE (mesmo de uma coluna), DELETE ou TRUNCATE em tabela append-only; função SECURITY DEFINER fora da chave `securityDefiner`, sem `SET search_path` ou executável por PUBLIC ([04 §5.1](../spec/04-dominio-e-dados.md#51-regras-cat-pnpm-dbcheck-ci-em-todo-pr), regras CAT-01 a CAT-07; a T-004 entrega a CAT-07).
10. O teste de isolamento (dados de 2 operadoras × 2 clientes; cada rota, job e stream tenta ler e escrever fora do escopo) roda em todo PR; especificação em [04](../spec/04-dominio-e-dados.md) e [08](../spec/08-identidade-e-seguranca.md).

## Alternativas consideradas

- **Filtro só na aplicação.** Por que não: um `WHERE` esquecido vaza; o banco não garante nada (achado da v1.1).
- **Schema por operadora.** Por que não: migrations multiplicadas, catálogo crescendo, pools por schema; 12 operadoras no mês 12 e dezenas depois.
- **Banco ou VM por operadora.** Por que não: RAM, conexões e backups multiplicados; incompatível com o Always Free. Pode virar oferta paga.
- **RLS sem FK composta.** Por que não: a política protege a leitura, mas uma escrita com id de outro cliente poderia referenciar linha alheia.
- **Contexto por sessão (`SET` sem `LOCAL`).** Por que não: o pool reutiliza conexões e o contexto vaza entre requisições.
- **Central por subconsulta por tenant (v1.1).** Por que não: custo por linha e erro fácil; o escopo `operator` resolve.

## Consequências

**Positivas**
- Isolamento mantido mesmo com bug de aplicação.
- Tabela nova sem política quebra o CI no mesmo PR.
- Um mecanismo para API, jobs, SSE, exportação e agentes de IA.

**Negativas**
- Toda consulta paga o predicado: índices começam por `operator_id`/`tenant_id` ([04](../spec/04-dominio-e-dados.md)).
- Jobs e SSE precisam abrir transação com contexto (REQ-ARQ-010); esquecer devolve 0 linhas, falha fechada e visível em teste.
- DuckDB lendo Parquet frio não aplica RLS: o caminho frio fixa o prefixo `operator_id=` e filtra `tenant_id`/`vehicle_id` a partir de pedido autorizado ([ADR-009](ADR-009-retencao-quente-frio.md)).
- Tabelas `auth.*` do Better Auth ficam fora do RLS; acesso só pelo módulo `identity` ([ADR-006](ADR-006-identidade-better-auth-chave-aparelho.md)).
- Funções SECURITY DEFINER são exceções controladas, com revisão N0.

## Gatilho de revisão

- Overhead de RLS > 20% no p95 da consulta de histórico (1 veículo, 1 dia) em benchmark → otimizar índices e políticas; remover RLS não é opção.
- Operadora exigir isolamento físico em contrato → banco dedicado como oferta paga (ADR nova).
- Sub-revenda (quarto nível) entrar no escopo → ADR nova.

## Relacionados

- INV-06, INV-07, INV-11.
- REQ-ARQ-004, REQ-ARQ-010, REQ-ARQ-011.
- [04](../spec/04-dominio-e-dados.md) (modelo, políticas, allowlist); [08](../spec/08-identidade-e-seguranca.md) (papéis, grants); [T-001](../../tasks/T-001-fundacao-monorepo-e-isolamento.md).
