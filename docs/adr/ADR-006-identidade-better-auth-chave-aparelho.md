# ADR-006 — Identidade embutida (Better Auth) + autorização própria; step-up de comando por chave do aparelho

**Status:** Aceito em 07/10/2026

## Contexto

- Usuários: equipe da operadora (console), cliente final e familiares (app), instalador, equipe de busca e a própria Versix. No mês 12: ~3.000 veículos, poucos milhares de usuários.
- A v1.1 (p. 8 e 18, REQ-008 e REQ-009) recomendava provedor OIDC externo com Authorization Code + PKCE e step-up pelo provedor ou WebAuthn.
- Restrições: o orçamento de RAM ([03 §11](../spec/03-arquitetura.md)) não tem espaço para um serviço de 0,5–1 GB; cada serviço a mais é um runbook para o fundador; 24 dias até o Piloto Zero; telas de login com a marca da operadora.
- Bloqueio é ação física. Um booleano "biometria ok" enviado pelo app não prova nada ao servidor (v1.1 p. 18).

## Decisão

1. **Autenticação embutida com Better Auth** no processo `api`, montada sob `/api/v1/auth/*` (integração com o adaptador Fastify validada na primeira tarefa de autenticação [VALIDAR]). Tabelas no schema `auth` do banco `tracksys`, geradas pelo CLI do Better Auth e versionadas como migration dbmate; nada migra em runtime.
   - Plugins: `bearer` (app Flutter, token em `flutter_secure_storage`) e `twoFactor` (TOTP para a equipe da operadora).
   - Console: cookie de sessão `HttpOnly`, `Secure`, `SameSite=Lax`, com checagem de origem confiável.
   - F0: e-mail + senha para `operator_admin`, `operator_agent` e `tenant_owner`.
2. **Autorização própria:** `membership` (papel, operadora, tenant), `platform_support_grant` e RLS ([ADR-004](ADR-004-isolamento-tres-niveis.md)). Plugins de organização do Better Auth não são usados: ele responde só "quem é".
3. **Step-up de comando no app por chave do aparelho:**
   - No primeiro login o app gera um par P-256 não exportável no Secure Enclave (iOS) ou no Android Keystore (StrongBox quando houver), com uso condicionado a biometria a cada assinatura; novo cadastro de biometria no aparelho invalida a chave.
   - A chave pública (SPKI) é gravada em `device_key` por rota autenticada. Registrar chave exige senha confirmada nos últimos 5 min e gera aviso por e-mail ao usuário ([08](../spec/08-identidade-e-seguranca.md)).
   - Para cada comando: o servidor emite desafio válido por 60 s, de uso único, vinculado a usuário, veículo e tipo; o app assina `tracksys-cmd-v1|{challenge_id}|{nonce}|{vehicle_id}|{type}|{reason_code}` com ECDSA P-256/SHA-256 (assinatura DER em base64url); o servidor verifica com a chave pública, consome o desafio de forma atômica e só então cria o comando ([06](../spec/06-comandos-e-bloqueio.md)).
   - Logout, remoção do aparelho e troca de senha revogam a chave (`revoked_at`).
4. **Step-up no console:** segundo fator (TOTP) nos últimos 5 min + motivo obrigatório.

## Alternativas consideradas

- **Logto (open source, OIDC).** Por que não: serviço e banco a mais, RAM, fluxo OIDC com redirecionamento no Flutter, marca por operadora configurada por tenant, upgrades e runbook próprios.
- **Keycloak.** Por que não: JVM pesada para a VM [VALIDAR consumo típico], administração complexa, temas para white label; recursos de sobra para 6 papéis.
- **Supabase Auth.** Por que não: hospedado, coloca a identidade fora da nossa infra e o free tier pausa por inatividade; auto-hospedado, são vários contêineres; o modelo de RLS por claims JWT difere do contexto por transação de 3 níveis.
- **Autenticação escrita do zero.** Por que não: hash de senha, sessão, reset e 2FA são fonte clássica de falha; Better Auth entrega isso testado.
- **Passkeys/WebAuthn no step-up.** Por que não agora: no Flutter dependem de plugins de terceiros e a verificação de attestation é mais complexa; a chave do aparelho prova posse + biometria com uma assinatura ECDSA. Revisitar no gatilho.
- **Booleano de biometria, PIN ou OTP por SMS.** Por que não: booleano não é prova; PIN isolado não é segundo fator; SMS custa, depende de cobertura e sofre SIM swap.

## Consequências

**Positivas**
- Nenhum serviço novo; identidade no mesmo backup e no mesmo failover.
- Telas de login próprias com a marca da operadora.
- Step-up com prova criptográfica vinculada à intenção do comando.

**Negativas**
- A autenticação depende de uma biblioteca jovem: versão fixada, avisos de segurança acompanhados, correção crítica aplicada em ≤ 7 dias.
- Sem SSO corporativo (SAML ou OIDC de terceiros) pronto.
- Tabelas `auth.*` ficam fora do RLS: acesso só pelo módulo `identity`, garantido por lint e revisão N0.
- A chave do aparelho exige código nativo pequeno (Swift e Kotlin via platform channel) ou plugin auditado [VALIDAR]; trocar de aparelho exige novo registro.
- Usuário sem biometria cadastrada não bloqueia pelo app; usa a central ([06](../spec/06-comandos-e-bloqueio.md)).

## Gatilho de revisão

- Operadora exigir SSO corporativo em contrato.
- Mais de 50.000 usuários ativos ou necessidade de federação com outros produtos.
- Vulnerabilidade crítica no Better Auth sem correção em 7 dias.
- Passkeys estáveis no Flutter (iOS e Android) com verificação suportada pelo Better Auth → avaliar trocar a chave do aparelho por passkey.

## Relacionados

- INV-07, INV-08, INV-11.
- [06](../spec/06-comandos-e-bloqueio.md) (step-up na política de comando); [08](../spec/08-identidade-e-seguranca.md) (sessões, papéis, grants, `device_key`); [09](../spec/09-api-e-contratos.md) (rotas); [10](../spec/10-apps-e-ux.md) (fluxo no app).
- [ADR-004](ADR-004-isolamento-tres-niveis.md), [ADR-007](ADR-007-app-unico-flutter-marca-dinamica.md).
