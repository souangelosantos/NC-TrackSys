# T-002 — Spike J16 em bancada: capturas, `capability_profile` draft

| Campo | Valor |
|---|---|
| Fase | F0 (semana S1: 07–13/10/2026; resultado registrado até 13/10/2026) |
| Requisitos | REQ-ING-019 |
| Contribui para | REQ-API-015 (capturas validam o envelope na T-005), REQ-ONB-015 e REQ-ONB-016 (textos de SMS e domínio usados na T-014), REQ-DAD-017 (chave de retenção do Traccar confirmada para a T-003) |
| Invariantes | INV-03 (capacidade não confirmada = `unknown`), INV-12 (nós → km/h só na normalização) |
| Risco de revisão | N1 |
| Depende de | Hardware na bancada (2 J16 do lote da Lider + 2 chips emnify ativos + fonte 12 V) |
| Pré-requisito de fato | Traccar acessível na porta 5023 da VM (T-003, passos do fundador 1–6). Se a T-003 atrasar, use o plano B da seção "Especificação detalhada" (5) |
| Estimativa | 2 sessões de agente (sessão 1: ferramentas, dia 1; sessão 2: importação das capturas, perfil e documentação, dia 6) + ~10 h do fundador na bancada |
| Bloqueado por decisão | DEC-02 é o produto desta tarefa (padrão seguro enquanto aberta: toda capacidade `unknown`, nenhum veículo real migra) |
| Tipo | **Mista:** fundador opera o hardware; agente escreve ferramentas, importa e documenta. Uma branch e um PR, mergeado ao fim do spike |

## Objetivo

Transformar o J16 de hipótese em fato medido. Ao final existem: um servidor de captura e um anonimizador em `packages/testkit`; as capturas reais dos cenários S01–S14, anonimizadas, em `packages/testkit/fixtures/j16/` com manifesto; o rascunho do perfil `capability_profile` do J16 (`'draft'`, valores `yes`/`no`/`unknown` com evidência por capacidade); os textos de SMS testados; a versão e o digest do Traccar fixados; e a DEC-02 marcada como resolvida em [15](../docs/spec/15-decisoes-riscos-premissas.md). A T-005 consome esses arquivos sem perguntar nada.

## Contexto obrigatório

- [05 §2, §3, §4, §13, §15](../docs/spec/05-ingestao-e-telemetria.md): chaves do forward, envelope, normalização, perfil de normalização e o roteiro S01–S14.
- [04 §3.3](../docs/spec/04-dominio-e-dados.md): `capability_profile` e as 11 chaves obrigatórias.
- [06 §13.1 item 4, §13.4](../docs/spec/06-comandos-e-bloqueio.md): o S07 preenche a seção `commands` (sem homologar).
- [11 §5, §6](../docs/spec/11-onboarding-e-migracao.md): modelos de SMS e medição de domínio/DNS.
- [15 DEC-02](../docs/spec/15-decisoes-riscos-premissas.md): o que a decisão cobre.
- [ADR-003](../docs/adr/ADR-003-traccar-borda-de-protocolos.md): Traccar como borda.

## Escopo — fazer

**Agente (sessão 1, até 08/10/2026 18:00 BRT):**
1. Criar o pacote `@tracksys/testkit` (se a T-004 ainda não o criou; se criou, só acrescentar scripts e arquivos) com o servidor de captura, o importador/anonimizador e o schema do manifesto (seção 1–3).
2. Criar o override de Compose que coloca o servidor de captura no lugar do `api` na rede do Traccar (seção 4).
3. Escrever o roteiro do fundador `docs/runbooks/spike-j16.md` (seção 6).
4. Escrever os testes de aceite da seção "Testes de aceite" (arquivos de teste de ferramenta passam já na sessão 1; o de fixtures passa só depois das capturas).

**Fundador (09–13/10/2026):**
5. Montar a bancada ([06 §13.1](../docs/spec/06-comandos-e-bloqueio.md) itens 1–3), apontar os 2 J16 para a VM por SMS e executar S01–S14 seguindo `docs/runbooks/spike-j16.md`, guardando as capturas brutas fora do repositório.
6. Obter com a Lider a senha SMS dos J16 e rodar `query_server` em 1 J16 da Lider (alvo de rollback), anotando o resultado em `docs/runbooks/onboarding/lider.md` (sem a senha).
7. Preencher as observações de cada cenário (planilha do roteiro) e entregar ao agente.

**Agente (sessão 2, 12–13/10/2026):**
8. Importar as capturas com o anonimizador para `packages/testkit/fixtures/j16/<cenário>/` e gerar `manifest.json` (seção 3).
9. Escrever `capability-profile.draft.json` e `sms/templates.json` com base nas observações (seções 7–8).
10. Atualizar `infra/traccar/traccar.xml.tpl` e o digest do Traccar se o spike provar chave ou versão diferente (seção 9), e marcar como resolvidos os `[VALIDAR — DEC-02]` confirmados nos capítulos 05, 07 e 11 (só o texto do marcador e o valor; nenhuma regra nova).
11. Atualizar a linha da DEC-02 em [15 §2](../docs/spec/15-decisoes-riscos-premissas.md) para `Resolvida — <data> — <resumo>` (REQ-QLD-020).

## Fora do escopo

- Ingestão na TrackSys (`/internal/v1`, inbox, projeção): T-005.
- Tabela `capability_profile` e o INSERT do perfil: T-005 (migration) copia o JSON desta tarefa.
- Homologação de bloqueio (20 ciclos, `status = 'homologated'`): F1, [06 §13](../docs/spec/06-comandos-e-bloqueio.md). O S07 aqui só observa respostas.
- Código de modelos de SMS em `packages/domain`: T-014. Aqui só os textos e a evidência.
- Qualquer captura com IMEI real, coordenada real, senha SMS ou MSISDN dentro do repositório.

## Arquivos a criar/alterar

```
packages/testkit/package.json                       (criar se não existir; senão acrescentar scripts)
packages/testkit/tsconfig.json                      (criar se não existir)
packages/testkit/src/capture-server.ts
packages/testkit/src/capture-import.ts
packages/testkit/src/anonymize.ts
packages/testkit/src/manifest.ts
packages/testkit/fixtures/j16/manifest.json
packages/testkit/fixtures/j16/capability-profile.draft.json
packages/testkit/fixtures/j16/sms/templates.json
packages/testkit/fixtures/j16/sms/evidence/*.png    (prints das respostas do S11 com número e senha borrados)
packages/testkit/fixtures/j16/S01-parado-desligado/…  até S14-eventos/…  (NNN-position.json, NNN-event.json)
infra/traccar/docker-compose.capture.yml
infra/traccar/traccar.xml.tpl                       (alterar só se o spike provar chave diferente; criado na T-003)
infra/docker-compose.yml                            (alterar só o digest do Traccar, se mudar; criado na T-003)
docs/runbooks/spike-j16.md
docs/runbooks/onboarding/lider.md                   (alvo de rollback; sem senha)
docs/spec/15-decisoes-riscos-premissas.md           (linha DEC-02)
docs/spec/05-ingestao-e-telemetria.md, 07-alertas-e-tempo-real.md, 11-onboarding-e-migracao.md  (só marcadores [VALIDAR — DEC-02] resolvidos)
tests/acceptance/T-002/capture-server.test.ts
tests/acceptance/T-002/anonymize.test.ts
tests/acceptance/T-002/fixtures.test.ts
tests/acceptance/T-002/profile-draft.test.ts
```

## Especificação detalhada

### (1) Pacote `@tracksys/testkit`

`packages/testkit/package.json` (se a T-004 já criou, acrescente só os scripts e as dependências que faltarem):

```json
{
  "name": "@tracksys/testkit",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "exports": { ".": "./src/index.ts", "./*": "./src/*.ts" },
  "scripts": {
    "typecheck": "tsc -p tsconfig.json",
    "capture": "node src/capture-server.ts",
    "capture:import": "node src/capture-import.ts"
  },
  "dependencies": { "zod": "^4.6.5" },
  "devDependencies": { "@types/node": "^24.19.1", "typescript": "^7.0.2" }
}
```

Os scripts rodam com o Node 24 direto sobre TypeScript (remoção de tipos nativa): use só sintaxe apagável (sem `enum`, `namespace` ou propriedades de parâmetro) e imports com extensão `.ts`. `tsconfig.json` estende `../../tsconfig.base.json` e inclui `src/**/*.ts` e `test/**/*.ts`.

### (2) Servidor de captura — `src/capture-server.ts`

- Uso: `pnpm --filter @tracksys/testkit capture -- --port 3001 --out <dir> --scenario S03`.
- `node:http`, sem dependências. Aceita `POST` em qualquer caminho terminado em `/positions` ou `/events`; outro método ou caminho → 404.
- Cada corpo (até 262.144 bytes; acima → 413) é gravado byte a byte em `<out>/<scenario>/<NNN>-<position|event>.json`, `NNN` com 3 dígitos crescentes por cenário (`001`, `002`…), e a resposta é `202` com corpo vazio.
- `--scenario` pode ser trocado sem reiniciar: `POST /_scenario` com corpo `S04` muda o cenário corrente (o fundador usa `curl` entre cenários).
- `--fail-for <segundos>` faz o servidor responder `503` por N segundos a partir do próximo corpo (cenário S13); as requisições recusadas não são gravadas.
- Não loga corpo, IMEI nem coordenada; loga uma linha por requisição: `{"ts","scenario","n","kind","bytes"}`.
- `--out` padrão: `~/tracksys-captures/raw` (fora do repositório). Recusa (`exit 2`) um `--out` dentro do diretório do repositório.

### (3) Importador e anonimizador — `src/capture-import.ts`, `src/anonymize.ts`, `src/manifest.ts`

`pnpm --filter @tracksys/testkit capture:import -- --raw ~/tracksys-captures/raw/S03 --scenario S03-movimento --origin-imei <IMEI real>` grava `packages/testkit/fixtures/j16/S03-movimento/NNN-*.json`.

Regras de `anonymize(envelope, ctx)` (pura, testada):
1. Toda ocorrência do IMEI real (em `device.uniqueId` e em qualquer string do corpo) vira `860000000000001`; o 2º J16 vira `860000000000002`. `device.name` vira `J16-bancada-1` ou `-2`.
2. Coordenadas: o primeiro fix válido do cenário é a âncora real `(lat0, lon0)`. Cada ponto é convertido para metros locais (`dx = (lon − lon0) × cos(lat0) × R`, `dy = (lat − lat0) × R`, `R = 6.371.008,8 m`) e reprojetado na origem fictícia `(−5,089211; −42,801892)`: `lat' = −5,089211 + dy/R`, `lon' = −42,801892 + dx/(R × cos(−5,089211°))`, arredondado a 6 casas. Distâncias entre pontos ficam preservadas com erro < 0,5% até 50 km.
3. Tempos (`fixTime`, `deviceTime`, `serverTime`), velocidade, curso, altitude e atributos numéricos ficam intactos. Ids do Traccar (`position.id`, `event.id`, `deviceId`) ficam intactos.
4. Atributos com dados de rede (`cid`, `lac`, `mcc`, `mnc`, `operator`, `iccid`, `phone`) são removidos.

`manifest.json` (schema Zod `J16Manifest` em `src/manifest.ts`):

```json
{
  "schemaVersion": 1,
  "device": { "model": "J16", "firmware": "<versão lida no PARAM#>", "imeiMasked": "***0001" },
  "traccar": { "image": "traccar/traccar:6.x.y", "digest": "sha256:<índice multi-arquitetura>", "protocol": "gt06", "port": 5023 },
  "capturedAt": "2026-10-10",
  "rawArchive": { "location": "bucket privado tracksys-backup/spike-j16/", "sha256": "<SHA-256 do .tar.zst das capturas brutas e do hex>" },
  "scenarios": [
    { "id": "S03", "dir": "S03-movimento", "files": ["001-position.json"], "result": "ok",
      "observations": "30 km/h estável: média 29,4 km/h normalizada; intervalo medido 30 s", "decides": ["moving_interval_s=30"] },
    { "id": "S06", "dir": null, "files": [], "result": "not_applicable", "observations": "botão SOS não instalado no lote" }
  ]
}
```

`result` ∈ `ok`, `partial`, `not_applicable`; `not_applicable` exige `files: []` e `observations` não vazio.

### (4) Override de Compose — `infra/traccar/docker-compose.capture.yml`

Coloca o servidor de captura na rede `tracksys` com o alias `api`, de modo que `forward.url = http://api:3001/...` da T-003 chegue nele sem mudar o Traccar:

```yaml
services:
  capture:
    image: node:24-bookworm-slim
    working_dir: /repo
    command: ["node", "packages/testkit/src/capture-server.ts", "--port", "3001", "--out", "/captures", "--scenario", "S01"]
    volumes:
      - /opt/tracksys:/repo:ro
      - /var/lib/tracksys/captures:/captures
    networks:
      tracksys:
        aliases: [api]
    mem_limit: 256m
```

Uso na VM: `docker compose -f infra/docker-compose.yml -f infra/traccar/docker-compose.capture.yml up -d capture`. O `/captures` da VM é copiado para o notebook do fundador por `scp` via Tailscale e apagado da VM ao fim do spike. Para esta exceção, `--out /captures` é aceito porque o caminho não está dentro do repositório montado.

### (5) Plano B sem a T-003 pronta

Se em 09/10/2026 a VM não tiver o Compose da T-003: na VM (ou em qualquer host com IP público e porta 5023 liberada), `docker network create tracksys` e `docker run -d --name traccar --network tracksys -p 5023:5023 -v $PWD/traccar.xml:/opt/traccar/conf/traccar.xml:ro traccar/traccar:<tag fixada>` com um `traccar.xml` mínimo (H2 embutido, forward para `http://api:3001/...`), mais o `capture` com `docker run --network tracksys --network-alias api`. Só para o spike; nada disso vai para produção.

### (6) Roteiro do fundador — `docs/runbooks/spike-j16.md`

Contém, nesta ordem: lista de material ([06 §13.1](../docs/spec/06-comandos-e-bloqueio.md)); comando SMS para apontar o J16 para a VM (modelo `set_server_ip` com o IP da VM, porque o domínio definitivo ainda não existe); como subir o `capture` e trocar de cenário (`curl -X POST http://127.0.0.1:3001/_scenario -d S04` a partir do contêiner); a tabela S01–S14 de [05 §15](../docs/spec/05-ingestao-e-telemetria.md) com duração, procedimento, o que anotar e a pergunta que o cenário decide; a planilha de observações (colunas `cenário, início UTC, fim UTC, mensagens, intervalo médio s, observação, resultado`); e o encerramento (copiar `/captures`, compactar com `tar --zstd`, calcular SHA-256, subir ao bucket privado, apagar da VM).

Pontos que o roteiro manda medir, com o padrão seguro se não for possível medir:

| Pergunta (DEC-02) | Cenário | Padrão seguro se não medir |
|---|---|---|
| Protocolo e porta | todos | gt06 na 5023 |
| `position.id` presente no forward | S13 | quarentena `missing_source_id` (sem fingerprint) |
| Forward de eventos tem retentativa | S13, S14 | tratar como sem retentativa |
| Heartbeat chega com `outdated = true` | S01 | heartbeat sem fix não vira posição |
| Ignição confiável | S02, S04 | `ignition = "unknown"` |
| Corte de alimentação (`powerCut`, `charge`) | S05 | `power_cut_alarm = "unknown"`, `power_source = null` |
| SOS | S06 | `sos = "unknown"` |
| Relé e estado reportado (`blocked`) | S07 | `relay = "unknown"`, `relay_state_reported = "unknown"` |
| Buffer offline e atributo de arquivo | S08 | `offline_buffer = "unknown"`, `archive_attribute = null` |
| Fix inválido e `fixTime` sem GPS | S09 | fix inválido não vira posição |
| Intervalos em movimento e parado | S01, S03 | 30 s e 300 s ([P-01](../docs/spec/15-decisoes-riscos-premissas.md)) |
| Domínio, tempo de re-resolução de DNS, servidor secundário, posição por SMS | S11 | `domain_support = "unknown"` (plano B por IP, [11 §6](../docs/spec/11-onboarding-e-migracao.md)) |
| WNRO e deriva de relógio | S12 | `wnro_correction = false` |

### (7) Rascunho do perfil — `fixtures/j16/capability-profile.draft.json`

Objeto que vai literalmente para a coluna `capabilities` (T-005). As 11 chaves de [04 §3.3](../docs/spec/04-dominio-e-dados.md) com `"yes"`, `"no"` ou `"unknown"`; seção `normalization` de [05 §13](../docs/spec/05-ingestao-e-telemetria.md) com os tipos de lá; seção `commands` parcial do S07 sem `homologation_ref`; e `evidence` com o arquivo de captura que prova cada `yes`/`no`:

```json
{
  "relay": "yes", "relay_state_reported": "unknown", "ignition": "yes", "power_cut_alarm": "unknown", "sos": "unknown",
  "accelerometer": "unknown", "device_speed_gate": "unknown", "secondary_server": "unknown", "domain_support": "unknown",
  "sms_position": "unknown", "offline_buffer": "unknown",
  "normalization": { "version": 1, "source_id_strategy": "traccar_id", "power_source": null, "power_main_min_v": null,
    "wnro_correction": false, "store_invalid_fix": false, "trust_motion_attribute": false, "archive_attribute": null,
    "moving_interval_s": 30, "stopped_interval_s": 300 },
  "commands": { "version": 1, "block_type": "engineStop", "unblock_type": "engineResume", "no_queue": "unknown",
    "offline_error_pattern": null, "ack_patterns": null },
  "evidence": { "ignition": "S04-ignicao/003-position.json", "relay": "S07-rele/002-event.json" }
}
```

O exemplo acima mostra o formato; os valores finais vêm das observações. Regra: só vira `"yes"` ou `"no"` a capacidade com arquivo em `evidence`; o resto fica `"unknown"` (INV-03). Pelo menos uma capacidade com `relay = "yes"` não habilita nada: o perfil continua `'draft'` (INV-10).

### (8) Textos de SMS — `fixtures/j16/sms/templates.json`

Chaves de [11 §5](../docs/spec/11-onboarding-e-migracao.md) (`query_server`, `query_params`, `set_server_domain`, `set_server_ip`, `rollback`, `position`, `reset`), cada uma com `text` (com `{host}`, `{port}`, `{password}` onde o S11 provar), `status` (`validated` só com resposta observada; senão `draft`), `expectedReply` e `evidenceRef` (print em `sms/evidence/`, com número e senha borrados). Nenhuma senha real no arquivo.

### (9) Traccar

- Fixar a imagem por digest do índice multi-arquitetura (`docker buildx imagetools inspect traccar/traccar:<tag>`), registrar em `manifest.json` e, se diferente do que a T-003 colocou, trocar em `infra/docker-compose.yml`.
- Confirmar cada chave de [05 §2](../docs/spec/05-ingestao-e-telemetria.md) e de [13 §5](../docs/spec/13-infra-e-operacao.md) na versão fixada (inclusive a de retenção de 7 dias, REQ-DAD-017). Chave com nome diferente é corrigida em `infra/traccar/traccar.xml.tpl` e no capítulo.

## Testes de aceite (congelados)

`tests/acceptance/T-002/capture-server.test.ts` — sobe o servidor numa porta livre com `--out` num diretório temporário fora do repositório.
- Dado o cenário `S03`, Quando chegam 2 `POST /internal/v1/traccar/positions` de 900 bytes, Então ambos recebem 202 e existem `S03/001-position.json` e `S03/002-position.json` idênticos aos corpos.
- Dado `POST /_scenario` com `S13` e `--fail-for 60`, Quando chega 1 POST, Então a resposta é 503 e nenhum arquivo é gravado.
- Dado um corpo de 262.145 bytes, Então 413. Dado `--out` dentro do repositório, Então o processo sai com código 2.
- Dado 10 requisições, Então nenhuma linha de log contém `uniqueId` nem `latitude`.

`tests/acceptance/T-002/anonymize.test.ts`
- Dado um envelope com `device.uniqueId = "359339000000001"`, `latitude = -23.550520`, `longitude = -46.633308` como âncora e um 2º ponto 500 m ao norte, Quando anonimizado, Então `uniqueId = "860000000000001"`, a âncora vira `(-5.089211, -42.801892)` e a distância haversine entre os 2 pontos anonimizados fica entre 497,5 m e 502,5 m.
- Dado `speed = 16.2`, `fixTime = "2026-10-10T13:00:00.000+00:00"` e `attributes.cid = 1234`, Então velocidade e tempo continuam iguais e `cid` não existe.
- Dado o IMEI real repetido dentro de uma string de atributo, Então nenhuma string do resultado contém `359339000000001`.

`tests/acceptance/T-002/fixtures.test.ts` (CT-ING-019; passa depois da sessão 2)
- Dado `packages/testkit/fixtures/j16/manifest.json`, Então ele passa no schema `J16Manifest` e cada cenário S01–S14 aparece uma vez, com ≥ 1 arquivo ou `result = "not_applicable"`.
- Dado todos os `*.json` sob `fixtures/j16/`, Então toda sequência isolada de exatamente 15 dígitos (regex `(?<![0-9])[0-9]{15}(?![0-9])`) é `860000000000001` ou `860000000000002`.
- Dado os arquivos do trecho de 30 km/h do S03 (marcado em `observations`), Quando a velocidade em nós de cada `position.speed` é convertida por `× 1,852`, Então a média fica entre 27 e 33 km/h.
- Dado `manifest.traccar.digest`, Então começa com `sha256:` e tem 71 caracteres.

`tests/acceptance/T-002/profile-draft.test.ts`
- Dado `capability-profile.draft.json`, Então as 11 chaves de [04 §3.3](../docs/spec/04-dominio-e-dados.md) existem com valor em `yes`/`no`/`unknown`, `normalization.source_id_strategy` ∈ `traccar_id`/`fingerprint_v1` e `moving_interval_s`, `stopped_interval_s` são inteiros > 0.
- Dado cada chave com `yes` ou `no`, Então `evidence[chave]` aponta para um arquivo existente em `fixtures/j16/`.
- Dado `commands`, Então não existe `homologation_ref`.
- Dado `sms/templates.json`, Então nenhuma entrada `validated` está sem `evidenceRef` existente e nenhum texto contém sequência de 4 ou mais dígitos fora de `{…}` (senha real).

## Comandos de verificação

```bash
pnpm install
pnpm --filter @tracksys/testkit typecheck
pnpm lint
pnpm test:acceptance -- tests/acceptance/T-002
pnpm verify                       # tudo da T-001 continua verde
git grep -nP '(?<![0-9])[0-9]{15}(?![0-9])' -- packages/testkit/fixtures | grep -vE '86000000000000[12]'   # saída vazia
```

Esperado: os 4 arquivos de `T-002` verdes; o último comando sem saída.

## Definição de pronto

- [ ] Ferramentas da sessão 1 mergeadas no mesmo PR das capturas, com os testes verdes.
- [ ] S01–S14 com captura ou `not_applicable` justificado; manifesto com digest do Traccar e SHA-256 do arquivo bruto no bucket privado.
- [ ] `capability-profile.draft.json` com evidência para todo `yes`/`no`; `sms/templates.json` sem senha.
- [ ] Alvo de rollback da SmartGPS em `docs/runbooks/onboarding/lider.md`.
- [ ] DEC-02 `Resolvida` em [15 §2](../docs/spec/15-decisoes-riscos-premissas.md) e marcadores `[VALIDAR — DEC-02]` resolvidos nos capítulos tocados.
- [ ] PR `feat(testkit): spike J16 em bancada e perfil draft (T-002)`, risco N1, com revisão cruzada.

## Decisões já tomadas (não pergunte, siga)

| Dúvida provável | Resposta |
|---|---|
| Onde ficam as capturas brutas e o hex do protocolo? | Fora do repositório: notebook do fundador e bucket privado `tracksys-backup/spike-j16/`. O repositório guarda só o SHA-256 no manifesto. |
| `true`/`false`/`null` ou `yes`/`no`/`unknown` nas capacidades? | `yes`/`no`/`unknown` nas 11 chaves ([04 §3.3](../docs/spec/04-dominio-e-dados.md), [06 §2](../docs/spec/06-comandos-e-bloqueio.md)). Onde [05 §13](../docs/spec/05-ingestao-e-telemetria.md) e [07](../docs/spec/07-alertas-e-tempo-real.md) dizem `true`, leia `"yes"`; `null` = `"unknown"`. Os campos de `normalization` mantêm os tipos de [05 §13](../docs/spec/05-ingestao-e-telemetria.md). |
| O rascunho de [05 §13](../docs/spec/05-ingestao-e-telemetria.md) diz `ignition: true, relay: true` antes do spike. Uso isso? | Não. Só vira `yes` o que a captura provar. Sem prova, `unknown`. |
| O J16 não aceitou domínio no S11. | `domain_support = "no"`; registre o tempo medido; o plano B por IP de [11 §6](../docs/spec/11-onboarding-e-migracao.md) passa a valer e a T-014 o usa. Não altere o ADR-005 nesta tarefa. |
| O Traccar não decodificou o J16 em gt06. | Pare as capturas, anote no PR e teste o decodificador alternativo que o manual indicar ([15 DEC-02](../docs/spec/15-decisoes-riscos-premissas.md) plano B). Se nenhum servir até 13/10, o fundador decide outro modelo para o piloto. |
| Posso comandar bloqueio real no S07? | Só na bancada (relé + lâmpada), com chamadas diretas à API do Traccar a partir do túnel SSH. Nunca em veículo. Nada de homologar: o perfil fica `'draft'`. |
| Precisa de `pnpm verify` verde com as fixtures? | Sim. As fixtures entram no PR; o job `acceptance-freeze` passa a cobrir `packages/testkit/fixtures/**` a partir desta tarefa ([14 §7](../docs/spec/14-qualidade-e-processo-ia.md)). |
| A senha SMS da Lider entra em algum arquivo? | Nunca. Nem no runbook, nem em fixture, nem no PR. Só o fundador a guarda (gerenciador de senhas). |
| Quem escreve no capítulo 15? | O agente, no mesmo PR, com o texto que o fundador aprovou na planilha de observações. |
