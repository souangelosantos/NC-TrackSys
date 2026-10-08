# ADR-005 — Infra Oracle Always Free: 2 VMs ARM (primária + standby), Docker Compose, rastreadores apontados por domínio

**Status:** Aceito em 07/10/2026

## Contexto

- Recursos próprios; meta de infra ≤ 10% da receita (≈ R$ 1.170/mês no mês 12). A conta Oracle Cloud tem cota Always Free de Ampere A1 de 4 OCPU e 24 GB de RAM no total e 200 GB de block storage [VALIDAR — DEC-12 limites vigentes].
- SLO de 99,5%/mês = ≤ 3 h 36 min de minutos ruins. Uma reconstrução de VM (~2 h) consome mais da metade do orçamento.
- Os rastreadores da Lider apontam hoje para o IP da SmartGPS e são reconfigurados por SMS. Cada troca de servidor custa SMS, tempo e risco; não pode se repetir a cada mudança de infra.
- A Oracle pode recuperar instâncias Always Free ociosas em contas gratuitas [VALIDAR — DEC-12].

## Decisão

1. **Duas VMs Ampere A1**, cada uma com 2 OCPU, 12 GB de RAM e 100 GB (redistribuição em DEC-12), Ubuntu 24.04 ARM, na mesma região (São Paulo ou Vinhedo, DEC-12) e em fault domains diferentes.
   - **Primária:** `caddy`, `traccar`, `api`, `worker`, `db` em Docker Compose (`infra/docker-compose.yml`).
   - **Standby (F1):** réplica Postgres por streaming assíncrono via Tailscale, com `restore_command` lendo o WAL do object storage se ficar para trás; Uptime Kuma (sondas de 60 s); `caddy` servindo `status.`; agente SRE ([ADR-010](ADR-010-operacao-assistida-por-ia.md)); imagens de `traccar`, `api` e `worker` baixadas e paradas.
2. **Docker Compose, sem Kubernetes.** `infra/scripts/provision.sh` é idempotente e reconstrói o host do zero em Ubuntu ARM ou x86 de qualquer provedor (imagens multi-arch).
3. **Rastreador por domínio.** Todo rastreador recebe `gps.<TRACKSYS_DOMAIN>`, nunca IP. DNS na Cloudflare, registro A **sem proxy** (o proxy gratuito não encaminha TCP arbitrário e trocaria o IP e a porta de origem exigidos no registro de acesso do Marco Civil), TTL de 60 s. `api.`, `app.` e `status.` seguem o mesmo regime.
4. **Failover dos rastreadores:** [ADOTADO NA v2.0: o registro `gps.` aponta para um IP público reservado da OCI, reatribuído à standby no failover; sem IP reservado, o failover troca o registro A]. Se o J16 não aceitar domínio ou resolver DNS só no boot [VALIDAR — DEC-02], só o IP reservado preserva o RTO de 30 min para os rastreadores; sem ele, voltar a transmitir exige SMS ou reinício do aparelho.
5. **Pay As You Go** (DEC-12): converter a conta. Recursos Always Free seguem sem cobrança; a conta sai da política de recuperação de instância ociosa e ganha mais chance de capacidade A1 [VALIDAR — DEC-12]. Proteções: orçamento OCI com alerta em US$ 1/mês e quotas de compartimento zerando shapes pagos [VALIDAR].
6. **Failover (F1):** manual pelo fundador com `infra/scripts/failover`; no F2 o agente SRE pode disparar (ADR-010). Ordem: cercar a primária (parar contêineres ou a instância), promover a réplica, subir `traccar`, `api` e `worker` com despacho de comandos desligado até a reconciliação (REQ-ARQ-016), mover IP ou DNS, conferir as sondas. RTO ≤ 30 min com standby; ≤ 2 h sem standby (F0). RPO ≤ 5 min (WAL contínuo, `archive_timeout` 60 s).
7. **Backups:** WAL-G para o Oracle Object Storage, com cópia na Cloudflare R2 ([13](../spec/13-infra-e-operacao.md)).
8. **Rede:** só 80, 443 e as portas dos protocolos homologados na security list; SSH só pela Tailscale ([03 §10](../spec/03-arquitetura.md)).

## Alternativas consideradas

- **Supabase (São Paulo) + Fly.io (GRU).** Por que não: custo cresce com uso desde cedo; o TCP do Traccar fica fora do pacote; auth e RLS baseados em JWT não batem com o contexto por transação de 3 níveis; free tier com pausa por inatividade [VALIDAR].
- **VPS paga barata (Hetzner, Contabo).** Por que não agora: mensalidade sem receita e datacenters fora do Brasil (latência e transferência internacional, [Anexo B](../anexos/B-juridico.md)) [VALIDAR ofertas]. Fica como destino do `provision.sh` em desastre da Oracle.
- **Free tier da AWS ou da GCP.** Por que não: 12 meses ou instâncias com ~1 GB de RAM, que não comportam Postgres + Traccar.
- **Kubernetes (k3s).** Por que não: camada de operação a mais para 5 contêineres.
- **Uma VM só no F1, com backup.** Por que não: reconstrução de ~2 h consome mais da metade do orçamento mensal de 3 h 36 min.
- **Rastreadores por IP.** Por que não: toda troca de servidor vira campanha de SMS em milhares de aparelhos.

## Consequências

**Positivas**
- Infra R$ 0 no F0–F1; standby quente com RTO de 30 min a partir do F1.
- Troca de servidor sem SMS; reconstrução documentada em script.

**Negativas**
- Mesma região: falha regional da Oracle derruba as duas VMs → restore em outro provedor a partir da R2 (RTO ≤ 2 h, [13](../spec/13-infra-e-operacao.md)).
- Risco de encerramento de conta ou mudança do Always Free → backups fora da Oracle e `provision.sh` agnóstico de provedor.
- ARM64: toda imagem precisa de arm64; por isso o `infra/db/Dockerfile` próprio (a imagem `postgis/postgis` não publica arm64 [VALIDAR]).
- Os limites do Object Storage Always Free (20 GB e 50.000 requisições/mês [VALIDAR — DEC-12]) serão ultrapassados: o WAL com `archive_timeout` de 60 s gera até ~43.200 segmentos/mês, e o Parquet frio cresce todo mês. Com Pay As You Go o excedente é cobrado por uso; medir no F1 e lançar no custo ([01](../spec/01-visao-e-negocio.md)).
- Firewall em duas camadas (security list e iptables do Ubuntu); portas publicadas pelo Docker ignoram o iptables do host, então a security list é a camada que vale.
- Capacidade A1 às vezes indisponível na criação ("out of capacity") → criar as duas VMs já no S1.

## Gatilho de revisão

- RAM da VM > 80% (média de 1 h) em 3 de 7 dias, ou disco do volume > 70%.
- Minutos ruins > 50% do orçamento mensal (≥ 1 h 48 min) em 2 meses seguidos.
- Mais de 3.000 veículos ativos ou ingestão > 100 msg/s sustentada por 1 h.
- Mudança da Oracle nas regras do Always Free ou do Pay As You Go.

## Relacionados

- REQ-ARQ-003, REQ-ARQ-004, REQ-ARQ-012, REQ-ARQ-016.
- [03](../spec/03-arquitetura.md) §2, §10, §11; [13](../spec/13-infra-e-operacao.md); [Anexo C](../anexos/C-operacional.md).
- DEC-02, DEC-04, DEC-12; [ADR-002](ADR-002-postgres-unico-fila-barramento.md), [ADR-010](ADR-010-operacao-assistida-por-ia.md).
