# ADR-007 — App único Flutter com marca dinâmica por operadora (opção C); console React

**Status:** Aceito em 07/10/2026

## Contexto

- O app do cliente final é o produto principal: "app modesto" é uma das duas dores da Lider com o tracker-net. Paridade mínima no app: mapa ao vivo, histórico, bloqueio e alertas.
- O fundador escolheu a opção C: app único "TrackSys" com marca dinâmica da operadora agora; app dedicado por operadora depois, como opcional pago; portal web do cliente depois.
- Lojas: conta Apple Developer pendente (DEC-03); conta pessoal nova no Google Play exige teste fechado com 12 testadores por 14 dias antes de produção [VALIDAR regra vigente]. A diretriz 4.2.6 da App Store exige que apps de template sejam publicados pelo dono do conteúdo, o que impede a Versix de publicar um app por operadora na própria conta.
- O console é ferramenta de trabalho da central e da operadora: tabelas densas, formulários, mapa.
- Stack dominada inclui Flutter e React.

## Decisão

1. **App único Flutter** (`apps/mobile`), publicado pela conta da Versix. A marca da operadora (`operator_brand`: nome, logo, cor primária e secundária, WhatsApp e telefone da central) é carregada em runtime e guardada em cache no aparelho.
   - Tela pré-login neutra TrackSys; após o login, aplica a marca da operadora da membership (fluxo exato em [10](../spec/10-apps-e-ux.md)).
   - O console só aceita cores com contraste ≥ 4,5:1 (WCAG AA) contra o texto sobre elas.
   - Bibliotecas: `maplibre_gl` + OpenFreeMap, `firebase_messaging`, `flutter_secure_storage`, `local_auth`, chave assimétrica nativa ([ADR-006](ADR-006-identidade-better-auth-chave-aparelho.md)).
   - Cliente HTTP Dart gerado de `packages/contracts` ([ADR-008](ADR-008-contrato-primeiro-zod-openapi-sse.md)).
2. **Console React 19** (`apps/console`): Vite, TanStack Router e Query, MapLibre GL JS, Tailwind 4, shadcn/ui; build estático servido pelo Caddy em `app.`; cliente TS gerado.
3. **Opção B (F2, opcional paga):** o mesmo código Flutter com flavors por operadora e pipeline de build próprio, publicado na conta de desenvolvedor da operadora com a Versix como membro.
4. **Portal web do cliente (F2):** build Flutter Web do mesmo app.

## Alternativas consideradas

- **Opção A, um app por operadora desde já.** Por que não: uma conta de loja e uma revisão por operadora; impossível até 31/10/2026.
- **Somente PWA/web.** Por que não: push no iOS só com PWA instalada; sem chave em Secure Enclave para o step-up; sem biometria nativa; a experiência inferior é justamente a dor a resolver.
- **React Native.** Por que não: viável, mas o fundador já domina Flutter; MapLibre e chave nativa exigem pontes equivalentes; trocar não traz ganho.
- **Console em Flutter Web.** Por que não: o ecossistema React é mais maduro para tabelas, formulários e MapLibre GL JS, e os agentes produzem shadcn/ui com boa qualidade.
- **Marca embutida no build.** Por que não: exige um build por operadora, o que equivale à opção A.

## Consequências

**Positivas**
- Uma publicação nas lojas atende todas as operadoras; operadora nova entra sem build novo (meta de onboarding ≤ 14 dias no F2).
- Um código para o app e para o futuro portal web.
- A opção B vira receita adicional sem reescrita.

**Negativas**
- O nome e o ícone "TrackSys" aparecem na loja; operadora que quer marca própria na loja paga a opção B.
- Marca dinâmica exige cuidado com cache (logo novo aparece na próxima abertura) e com as telas anteriores ao login.
- Dois frameworks de UI com tokens de design mantidos em dois lugares ([10](../spec/10-apps-e-ux.md)).
- Cada versão relevante depende da conta Apple (DEC-03) e do ciclo de teste do Google Play.

## Gatilho de revisão

- 3 ou mais operadoras pedindo app dedicado com pagamento aceito → industrializar a opção B (flavors + pipeline).
- Crash-free do app < 99,5% por 2 semanas seguidas, atribuído ao framework → revisão técnica.
- Apple ou Google mudarem a regra para apps multimarca.

## Relacionados

- [02 — Escopo e fases](../spec/02-escopo-e-fases.md); [09](../spec/09-api-e-contratos.md); [10](../spec/10-apps-e-ux.md) (UX, estados honestos, tokens, marca).
- DEC-03, DEC-04, DEC-11.
- [ADR-006](ADR-006-identidade-better-auth-chave-aparelho.md), [ADR-008](ADR-008-contrato-primeiro-zod-openapi-sse.md).
