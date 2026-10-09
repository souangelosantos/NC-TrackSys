# ADR-003 — Traccar como borda de protocolos (decodifica e envia comandos), integrado por forwarding HTTP e API REST; TrackSys não escreve no banco do Traccar

**Status:** Aceito em 07/10/2026

## Contexto

- A maioria da base da Lider usa J16, que costuma falar protocolo binário compatível com GT06 [VALIDAR — DEC-02]. Cada modelo novo traz decodificação e codificação de comando próprias.
- Traccar é servidor open source (Apache 2.0) com suporte à família GT06 e a centenas de outros protocolos, forward HTTP de posições e eventos e API REST de comandos. A v1.1 já o adotava (referência 6.16.0, p. 7–10) e já proibia escrita da TrackSys nas tabelas dele.
- `Position.speed` do Traccar vem em nós (v1.1 p. 10).
- Homologar hardware rápido é parte da meta de onboarding de operadora em ≤ 14 dias (F2).

## Decisão

1. Traccar 6.x como contêiner `traccar`, com tag e digest fixados no spike S1 (DEC-02) e configuração versionada em `infra/traccar/`.
2. Papel do Traccar: sessão TCP, decodificação, gravação no próprio banco e envio de comandos. Ele não conhece operadora, cliente nem política de comando.
3. Banco do Traccar: database `traccar` no mesmo cluster Postgres, com papel próprio sem acesso ao banco `tracksys`. Entra no mesmo backup e na mesma réplica.
4. Entrada na TrackSys: forward HTTP JSON de posições e de eventos para `http://api:3001/internal/v1/traccar/positions` e `/internal/v1/traccar/events`, com header secreto. Chaves de configuração do forward e de retentativa confirmadas no spike [VALIDAR — DEC-02]. Contrato e normalização em [05](../spec/05-ingestao-e-telemetria.md).
5. Saída para o Traccar: só o `worker` chama a API REST (8082, rede interna) com o usuário de serviço dedicado `TRACCAR_API_USER` (senha no SOPS), o único com permissão de comando — `POST /api/devices` no provisionamento (`uniqueId` = IMEI) e `POST /api/commands/send` no despacho, com `noQueue` quando o perfil suportar ([06](../spec/06-comandos-e-bloqueio.md)).
6. A TrackSys nunca lê nem escreve o banco `traccar` por SQL. Backfill usa a API REST do Traccar (`GET /api/positions`) em modo sem efeito externo (INV-05).
7. O Traccar guarda 7 dias de posições (janela de backfill), pela opção nativa de limpeza [VALIDAR].
8. Registro automático de dispositivo desconhecido desligado: só IMEIs provisionados pelo `worker` geram sessão útil [VALIDAR]. Registro de usuário desligado (`server.registration = false`): o primeiro acesso não vira admin de quem chegar antes.
9. Velocidade em nós vira km/h uma única vez, na normalização em `packages/domain` (10 nós = 18,52 km/h; INV-12).
10. Porta pública só a do protocolo homologado (F0: 5023 [VALIDAR — DEC-02]). A 8082 nunca é publicada; acesso humano ao painel do Traccar por túnel SSH via Tailscale, com usuário `readonly = true` e `limitCommands = true` [VALIDAR nomes das opções na versão fixada]; a senha de admin fica só no cofre ([15 §3.1](../spec/15-decisoes-riscos-premissas.md#31-fator-ônibus--1-cofre-e-contingência)).
11. `INGEST_SOURCE_INSTANCE` identifica o par instância + banco `traccar` e muda se o banco for recriado vazio (REQ-ARQ-013).
12. Comando enviado por fora da plataforma é detectado: `commandResult` ao vivo sem comando de relé ativo ou UNKNOWN no rastreador abre o alerta `command_outside_platform` (`critical`) e uma page ao fundador ([06 §8.3](../spec/06-comandos-e-bloqueio.md#83-evidência-tardia), REQ-CMD-023).

## Alternativas consideradas

- **Decodificador GT06 próprio em Node.** Por que não: variantes por fabricante e firmware, login, heartbeat, CRC e codificação de comando; semanas de trabalho e risco de bug no caminho N0 de comando.
- **Plataforma de borda paga (ex.: Flespi).** Por que não: custo por dispositivo [VALIDAR], dependência externa no caminho crítico e dados fora da nossa infra.
- **Forward do Traccar direto para broker (AMQP, Kafka, Redis).** Por que não: exige broker ([ADR-002](ADR-002-postgres-unico-fila-barramento.md)); HTTP para a inbox devolve 202 só após commit.
- **Ler o banco do Traccar (polling SQL ou CDC).** Por que não: acopla ao schema interno, que muda entre versões.
- **Traccar com H2 embutido.** Por que não: fica fora do backup e da réplica; o failover perderia o cadastro de dispositivos do Traccar.

## Consequências

**Positivas**
- Modelos novos sem código de protocolo: homologação vira configuração + `capability_profile` ([04](../spec/04-dominio-e-dados.md)).
- Projeto maduro, com comunidade grande e documentação de protocolos.
- A TrackSys fica livre para evoluir domínio e API sem tocar em bytes de protocolo.

**Negativas**
- JVM ocupa 1,5 GB do orçamento de RAM.
- Dependência de upstream: toda atualização do Traccar reexecuta a suíte de capturas do `packages/testkit` e a suíte CT-CMD antes de produção.
- A retentativa do forward é limitada: queda longa do `api` vira lacuna, recuperada por backfill dentro de 7 dias.
- Resposta do Traccar ao envio não prova atuação física ([06](../spec/06-comandos-e-bloqueio.md)).
- O Traccar envia `engineStop` a qualquer rastreador para quem tiver permissão na API ou no painel; sem os usuários do item 5 e do item 10, esse caminho não teria política, step-up, `cut_point` nem auditoria.
- Sessões TCP vivem em um processo: escalar horizontalmente exige afinidade por porta ou operadora.

## Gatilho de revisão

- Mais de ~20.000 dispositivos conectados ou CPU do Traccar > 70% sustentado → múltiplas instâncias particionadas por porta ou operadora.
- Hardware a homologar sem suporte no Traccar, com ≥ 500 veículos em uma operadora [PREMISSA] → avaliar decodificador próprio só para esse protocolo.
- Vulnerabilidade crítica no Traccar sem correção upstream em 14 dias → avaliar fork mínimo.

## Relacionados

- INV-01, INV-05, INV-12.
- REQ-ARQ-002, REQ-ARQ-013, REQ-CMD-023.
- [03 §5](../spec/03-arquitetura.md#5-ingestão-síncrona-com-fallback) e §8; [05](../spec/05-ingestao-e-telemetria.md); [06](../spec/06-comandos-e-bloqueio.md); [11](../spec/11-onboarding-e-migracao.md).
- [ADR-002](ADR-002-postgres-unico-fila-barramento.md), [ADR-005](ADR-005-infra-oracle-always-free.md).
