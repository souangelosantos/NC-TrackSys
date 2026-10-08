"""Gera docs/spec/16-rastreabilidade.md a partir dos capítulos e cartões de tarefa.

Uso: python3 -I trace.py <repo>
Lê os cabeçalhos de requisito no formato canônico:
  ### REQ-XXX-NNN — Título
  **Fase:** F0 · **Prioridade:** P0 · **Risco:** N0 · **Invariantes:** INV-01, INV-02
e as linhas "**Aceite.** CT-..." seguintes, além da linha "Requisitos" da tabela de cada cartão.
"""
import pathlib
import re
import sys
from collections import defaultdict

repo = pathlib.Path(sys.argv[1])
spec = repo / 'docs' / 'spec'
tasks_dir = repo / 'tasks'

REQ_HDR = re.compile(r'^#{2,4}\s+(REQ-[A-Z]+-\d{3})\s+[—-]\s+(.+?)\s*$')
META = re.compile(r'\*\*Fase:\*\*\s*([^·]+?)\s*·\s*\*\*Prioridade:\*\*\s*([^·]+?)\s*·\s*\*\*Risco:\*\*\s*([^·]+?)\s*·\s*\*\*Invariantes:\*\*\s*(.+)$')
CT = re.compile(r'\bCT-[A-Z]+-\d{3}\b')
INV = re.compile(r'\bINV-\d{2}\b')
REQ_ANY = re.compile(r'\bREQ-[A-Z]+-\d{3}\b')
RANGE = re.compile(r'\b(REQ-[A-Z]+)-(\d{3})\s+(?:a|até)\s+(REQ-[A-Z]+)-(\d{3})\b')


def reqs_in(text):
    """IDs citados, expandindo faixas como 'REQ-ING-002 a REQ-ING-015'."""
    found = list(REQ_ANY.findall(text))
    for m in RANGE.finditer(text):
        if m.group(1) == m.group(3):
            a, b = int(m.group(2)), int(m.group(4))
            found += [f'{m.group(1)}-{n:03d}' for n in range(min(a, b), max(a, b) + 1)]
    return list(dict.fromkeys(found))


reqs = {}
order = []
problems = []
for f in sorted(spec.glob('[0-1][0-9]-*.md')):
    if f.name.startswith('16-'):
        continue
    lines = f.read_text(encoding='utf-8').splitlines()
    i = 0
    while i < len(lines):
        m = REQ_HDR.match(lines[i])
        if not m:
            i += 1
            continue
        rid, title = m.group(1), m.group(2)
        meta = None
        cts = []
        j = i + 1
        while j < len(lines) and not REQ_HDR.match(lines[j]) and not lines[j].startswith('## '):
            if meta is None:
                mm = META.search(lines[j])
                if mm:
                    meta = mm
            if '**Aceite' in lines[j] or lines[j].lstrip().startswith(('- CT-', '* CT-', 'CT-')):
                cts += CT.findall(lines[j])
            j += 1
        if rid in reqs:
            problems.append(f'{rid} definido mais de uma vez ({reqs[rid]["file"]} e {f.name})')
        if meta is None:
            problems.append(f'{rid} ({f.name}) sem linha de metadados no formato canônico')
            phase = prio = risk = '?'
            invs = []
        else:
            phase, prio, risk = (meta.group(1).strip(), meta.group(2).strip(), meta.group(3).strip())
            invs = INV.findall(meta.group(4))
        if not cts:
            problems.append(f'{rid} ({f.name}) sem CT no aceite')
        reqs[rid] = dict(file=f.name, title=title, phase=phase, prio=prio, risk=risk,
                         invs=sorted(set(invs)), cts=list(dict.fromkeys(cts)))
        order.append(rid)
        i = j

req_tasks = defaultdict(list)
task_rows = []
for t in sorted(tasks_dir.glob('T-[0-9][0-9][0-9]-*.md')):
    text = t.read_text(encoding='utf-8')
    tid = t.name[:5]
    title_m = re.search(r'^#\s+T-\d{3}\s+[—-]\s+(.+)$', text, re.M)
    title = title_m.group(1).strip() if title_m else t.stem
    row = re.search(r'^\|\s*Requisitos\s*\|\s*(.+?)\s*\|\s*$', text, re.M)
    rlist = reqs_in(row.group(1)) if row else []
    phase_m = re.search(r'^\|\s*Fase\s*\|\s*(F\d)', text, re.M)
    risk_m = re.search(r'^\|\s*Risco de revisão\s*\|\s*\**(N\d)', text, re.M)
    task_rows.append((tid, t.name, title, phase_m.group(1) if phase_m else '?', risk_m.group(1) if risk_m else '?', rlist))
    for r in rlist:
        req_tasks[r].append(tid)
        if r not in reqs:
            problems.append(f'{tid} cita {r}, que não está definido nos capítulos')

# Referências a REQ não definidos em qualquer documento
for f in list(spec.glob('*.md')) + list((repo / 'docs' / 'adr').glob('*.md')) + list((repo / 'docs' / 'anexos').glob('*.md')):
    if f.name.startswith('16-'):
        continue
    for r in set(REQ_ANY.findall(f.read_text(encoding='utf-8'))):
        if r not in reqs:
            problems.append(f'{f.relative_to(repo)} cita {r}, que não está definido')

phases = ['F0', 'F1', 'F2', 'F3']
by_phase = defaultdict(int)
for r in reqs.values():
    by_phase[r['phase'].split(',')[0].strip()] += 1

out = []
out.append('# 16 — Rastreabilidade')
out.append('')
out.append('> **Resumo:** matriz gerada automaticamente a partir dos capítulos 01–15 e dos cartões em `tasks/`. Liga cada requisito à fase, prioridade, risco, invariantes, testes de aceite (CT) e tarefas que o implementam. Não edite à mão: rode o gerador.')
out.append('> **Fases:** F0–F3  ·  **Status:** Aprovado para execução')
out.append('> **Muda em relação à v1.1:** matriz por requisito (não por faixa), com tarefa responsável e verificação automática de IDs.')
out.append('')
out.append('## Como usar na revisão de PR')
out.append('')
out.append('1. Ache o REQ que o PR implementa e confira se o CT correspondente está nos testes do PR.')
out.append('2. Confira as invariantes listadas: o revisor tenta quebrar cada uma.')
out.append('3. Requisito sem tarefa no F0/F1 é lacuna: abra um cartão antes de implementar.')
out.append('')
out.append('## Totais')
out.append('')
out.append('| Fase | Requisitos |')
out.append('|---|---|')
for p in phases:
    out.append(f'| {p} | {by_phase.get(p, 0)} |')
out.append(f'| **Total** | **{len(reqs)}** |')
out.append('')
out.append('## Matriz requisito → teste → tarefa')
out.append('')
out.append('| REQ | Título | Capítulo | Fase | Prior. | Risco | Invariantes | CT | Tarefas |')
out.append('|---|---|---|---|---|---|---|---|---|')
for rid in order:
    r = reqs[rid]
    out.append(f"| {rid} | {r['title']} | [{r['file'][:2]}]({r['file']}) | {r['phase']} | {r['prio']} | {r['risk']} | {', '.join(r['invs']) or '—'} | {', '.join(r['cts']) or '—'} | {', '.join(req_tasks.get(rid, [])) or '—'} |")
out.append('')
out.append('## Invariante → requisitos')
out.append('')
inv_map = defaultdict(list)
for rid in order:
    for inv in reqs[rid]['invs']:
        inv_map[inv].append(rid)
out.append('| Invariante | Requisitos que a protegem |')
out.append('|---|---|')
for inv in sorted(inv_map):
    out.append(f"| {inv} | {', '.join(inv_map[inv])} |")
out.append('')
out.append('## Tarefa → requisitos')
out.append('')
out.append('| Tarefa | Fase | Risco | Requisitos |')
out.append('|---|---|---|---|')
for tid, fname, title, ph, rk, rlist in task_rows:
    out.append(f"| [{tid} — {title}](../../tasks/{fname}) | {ph} | {rk} | {', '.join(rlist) or '—'} |")
out.append('')
gaps = [rid for rid in order if reqs[rid]['phase'].startswith(('F0', 'F1')) and not req_tasks.get(rid)]
out.append('## Lacunas (F0/F1 sem tarefa)')
out.append('')
if gaps:
    for g in gaps:
        out.append(f'- {g} — {reqs[g]["title"]} ({reqs[g]["phase"]})')
else:
    out.append('Nenhuma: todo requisito do F0 e do F1 tem tarefa responsável.')
out.append('')
out.append('## Como regenerar')
out.append('')
out.append('```bash')
out.append('python3 scripts/trace.py .   # a partir da raiz do repositório')
out.append('```')
out.append('')
(spec / '16-rastreabilidade.md').write_text('\n'.join(out), encoding='utf-8')
print(f'reqs={len(reqs)} tasks={len(task_rows)} gaps={len(gaps)} problems={len(problems)}')
for p in problems:
    print('PROBLEMA:', p)
