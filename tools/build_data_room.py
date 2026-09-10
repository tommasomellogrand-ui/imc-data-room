#!/usr/bin/env python3
from __future__ import annotations
import csv, json, re, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TICKETS=ROOT/'tickets'; DIST=ROOT/'dist'
LABELS=['CASE_ID','DOC_TYPE','AREA','DATE','TOPIC']
DOC_TYPES={'REQUEST','RESPONSE','DECISION','REPORT','AUDIT','POLICY'}
STATUSES={'OPEN','IN_PROGRESS','WAITING_REVIEW','APPROVED','APPROVED_WITH_CHANGES','REJECTED','CLOSED'}
CASE_RE=re.compile(r'^IMC-([A-Z0-9]+)-(\d{3,})$')
DATE_RE=re.compile(r'^\d{4}-\d{2}-\d{2}$')
REQ_RE=re.compile(r'^REQUEST(?:_V(\d+))?\.txt$')

def parse(path:Path):
    lines=path.read_text(encoding='utf-8').splitlines()
    if len(lines)<6: raise ValueError(f'{path}: documento troppo corto')
    meta={}
    for i,label in enumerate(LABELS):
        prefix=label+': '
        if not lines[i].startswith(prefix): raise ValueError(f'{path}: riga {i+1} deve iniziare con {prefix!r}')
        value=lines[i][len(prefix):].strip()
        if not value: raise ValueError(f'{path}: {label} vuoto')
        meta[label]=value
    if lines[5] != '': raise ValueError(f'{path}: la riga 6 deve essere vuota')
    if meta['DOC_TYPE'] not in DOC_TYPES: raise ValueError(f'{path}: DOC_TYPE non ammesso')
    if not CASE_RE.match(meta['CASE_ID']): raise ValueError(f'{path}: CASE_ID non valido')
    if not DATE_RE.match(meta['DATE']): raise ValueError(f'{path}: DATE non valida')
    body='\n'.join(lines[6:]).strip()
    return meta,body

def request_version(path:Path):
    m=REQ_RE.match(path.name)
    if not m: return 0
    return int(m.group(1) or 1)

def derive_status(docs):
    decisions=[d for d in docs if d['doc_type']=='DECISION']
    if decisions:
        body=decisions[-1]['body']
        m=re.search(r'(?mi)^STATUS:\s*([A-Z_]+)\s*$',body)
        if m and m.group(1) in STATUSES: return m.group(1)
        return 'CLOSED'
    if any(d['doc_type']=='RESPONSE' for d in docs): return 'WAITING_REVIEW'
    return 'OPEN'

def build():
    errors=[]; cases={}
    for path in sorted(TICKETS.rglob('*.txt')):
        try: meta,body=parse(path)
        except Exception as e: errors.append(str(e)); continue
        parts=path.relative_to(TICKETS).parts
        if len(parts)<4: errors.append(f'{path}: path atteso tickets/AREA/YYYY/CASE_ID/file'); continue
        area,year,case_id=parts[0],parts[1],parts[2]
        if case_id!=meta['CASE_ID']: errors.append(f'{path}: CASE_ID non coincide con directory')
        if area!=meta['AREA']: errors.append(f'{path}: AREA non coincide con directory')
        if year!=meta['DATE'][:4]: errors.append(f'{path}: anno path non coincide con DATE')
        cases.setdefault(case_id,[]).append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'name':path.name,'case_id':case_id,'doc_type':meta['DOC_TYPE'],'area':meta['AREA'],'date':meta['DATE'],'topic':meta['TOPIC'],'body':body,'request_version':request_version(path)})
    registry=[]
    for case_id,docs in sorted(cases.items()):
        reqs=sorted([d for d in docs if d['doc_type']=='REQUEST' and d['request_version']],key=lambda d:(d['request_version'],d['name']))
        if not reqs: errors.append(f'{case_id}: REQUEST mancante'); continue
        active=reqs[-1]
        for d in docs:
            if d['doc_type'] in {'RESPONSE','DECISION'} and (d['area']!=active['area'] or d['topic']!=active['topic']):
                errors.append(f"{d['path']}: AREA/TOPIC non coerenti con REQUEST attivo {active['name']}")
        registry.append({'case_id':case_id,'area':active['area'],'date':active['date'],'topic':active['topic'],'status':derive_status(docs),'active_request':active['path'],'documents':[{k:d[k] for k in ('name','path','doc_type','date','topic','request_version')} for d in docs]})
    if errors:
        print('\n'.join('ERROR: '+e for e in errors),file=sys.stderr); return 1
    if DIST.exists(): shutil.rmtree(DIST)
    shutil.copytree(ROOT/'site',DIST)
    (DIST/'data').mkdir(parents=True,exist_ok=True)
    (DIST/'data'/'registry.json').write_text(json.dumps({'version':1,'tickets':registry},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (DIST/'data'/'registry.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['case_id','area','date','topic','status','active_request']); w.writeheader(); w.writerows([{k:c[k] for k in w.fieldnames} for c in registry])
    for c in registry:
        case_dir=DIST/'cases'/c['case_id']; case_dir.mkdir(parents=True,exist_ok=True)
        active=ROOT/c['active_request']; shutil.copy2(active,case_dir/'request.txt')
        docs=[]
        for d in c['documents']:
            src=ROOT/d['path']; dst=case_dir/d['name']; shutil.copy2(src,dst); docs.append({**d,'url':f"cases/{c['case_id']}/{d['name']}"})
        (case_dir/'case.json').write_text(json.dumps({**c,'documents':docs,'request_url':f"cases/{c['case_id']}/request.txt"},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Validated and built {len(registry)} ticket(s)')
    return 0

if __name__=='__main__': raise SystemExit(build())
