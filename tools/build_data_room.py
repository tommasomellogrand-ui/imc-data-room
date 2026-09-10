#!/usr/bin/env python3
from __future__ import annotations
import csv, json, re, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TICKETS=ROOT/'tickets'; KNOWLEDGE=ROOT/'knowledge'; DIST=ROOT/'dist'
TICKET_LABELS=['CASE_ID','DOC_TYPE','AREA','DATE','TOPIC']
KNOWLEDGE_LABELS=['DOC_ID','DOC_TYPE','AREA','DATE','TOPIC','VERSION','STATUS','ACTIVITY']
TICKET_DOC_TYPES={'REQUEST','RESPONSE','DECISION','REPORT','AUDIT','POLICY'}
KNOWLEDGE_TYPES={'POLICY','PLAYBOOK','REFERENCE'}
KNOWLEDGE_STATUSES={'ACTIVE','DEPRECATED'}
STATUSES={'OPEN','IN_PROGRESS','WAITING_REVIEW','APPROVED','APPROVED_WITH_CHANGES','REJECTED','CLOSED'}
CASE_RE=re.compile(r'^IMC-([A-Z0-9]+)-(\d{3,})$')
DOC_ID_RE=re.compile(r'^IMC-[A-Z0-9-]+$')
DATE_RE=re.compile(r'^\d{4}-\d{2}-\d{2}$')
REQ_RE=re.compile(r'^REQUEST(?:_V(\d+))?\.txt$')
VER_RE=re.compile(r'^V(\d{3,})$')
PRECEDENCE={'POLICY':300,'PLAYBOOK':200,'REFERENCE':100}

def parse_labels(path:Path,labels:list[str]):
    lines=path.read_text(encoding='utf-8').splitlines()
    if len(lines)<len(labels)+1: raise ValueError(f'{path}: documento troppo corto')
    meta={}
    for i,label in enumerate(labels):
        prefix=label+': '
        if not lines[i].startswith(prefix): raise ValueError(f'{path}: riga {i+1} deve iniziare con {prefix!r}')
        value=lines[i][len(prefix):].strip()
        if not value: raise ValueError(f'{path}: {label} vuoto')
        meta[label]=value
    if lines[len(labels)]!='': raise ValueError(f'{path}: riga {len(labels)+1} deve essere vuota')
    body='\n'.join(lines[len(labels)+1:]).strip()
    return meta,body

def parse_ticket(path:Path):
    meta,body=parse_labels(path,TICKET_LABELS)
    if meta['DOC_TYPE'] not in TICKET_DOC_TYPES: raise ValueError(f'{path}: DOC_TYPE non ammesso')
    if not CASE_RE.match(meta['CASE_ID']): raise ValueError(f'{path}: CASE_ID non valido')
    if not DATE_RE.match(meta['DATE']): raise ValueError(f'{path}: DATE non valida')
    return meta,body

def parse_knowledge(path:Path):
    meta,body=parse_labels(path,KNOWLEDGE_LABELS)
    if meta['DOC_TYPE'] not in KNOWLEDGE_TYPES: raise ValueError(f'{path}: DOC_TYPE knowledge non ammesso')
    if not DOC_ID_RE.match(meta['DOC_ID']): raise ValueError(f'{path}: DOC_ID non valido')
    if not DATE_RE.match(meta['DATE']): raise ValueError(f'{path}: DATE non valida')
    if not VER_RE.match(meta['VERSION']): raise ValueError(f'{path}: VERSION non valida')
    if meta['STATUS'] not in KNOWLEDGE_STATUSES: raise ValueError(f'{path}: STATUS knowledge non ammesso')
    return meta,body

def request_version(path:Path):
    m=REQ_RE.match(path.name)
    return int(m.group(1) or 1) if m else 0

def derive_status(docs):
    decisions=[d for d in docs if d['doc_type']=='DECISION']
    if decisions:
        body=decisions[-1]['body']; m=re.search(r'(?mi)^STATUS:\s*([A-Z_]+)\s*$',body)
        return m.group(1) if m and m.group(1) in STATUSES else 'CLOSED'
    return 'WAITING_REVIEW' if any(d['doc_type']=='RESPONSE' for d in docs) else 'OPEN'

def build_tickets(errors):
    cases={}
    for path in sorted(TICKETS.rglob('*.txt')):
        try: meta,body=parse_ticket(path)
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
            if d['doc_type'] in {'RESPONSE','DECISION'} and (d['area']!=active['area'] or d['topic']!=active['topic']): errors.append(f"{d['path']}: AREA/TOPIC non coerenti con REQUEST attivo {active['name']}")
        registry.append({'case_id':case_id,'area':active['area'],'date':active['date'],'topic':active['topic'],'status':derive_status(docs),'active_request':active['path'],'documents':[{k:d[k] for k in ('name','path','doc_type','date','topic','request_version')} for d in docs]})
    return registry

def build_knowledge(errors):
    groups={}
    if not KNOWLEDGE.exists(): return []
    for path in sorted(KNOWLEDGE.rglob('*.txt')):
        try: meta,body=parse_knowledge(path)
        except Exception as e: errors.append(str(e)); continue
        parts=path.relative_to(KNOWLEDGE).parts
        if len(parts)!=4: errors.append(f'{path}: path atteso knowledge/TYPE/AREA/DOC_ID/VNNN.txt'); continue
        dtype,area,doc_id,name=parts
        if dtype!=meta['DOC_TYPE'] or area!=meta['AREA'] or doc_id!=meta['DOC_ID']: errors.append(f'{path}: metadata non coerenti con directory')
        if name!=meta['VERSION']+'.txt': errors.append(f'{path}: filename non coincide con VERSION')
        version=int(VER_RE.match(meta['VERSION']).group(1))
        item={'doc_id':meta['DOC_ID'],'doc_type':meta['DOC_TYPE'],'area':meta['AREA'],'date':meta['DATE'],'topic':meta['TOPIC'],'version':meta['VERSION'],'version_number':version,'status':meta['STATUS'],'activity':[x.strip() for x in meta['ACTIVITY'].split(',') if x.strip()],'path':str(path.relative_to(ROOT)).replace('\\','/'),'body':body,'precedence':PRECEDENCE[meta['DOC_TYPE']]}
        groups.setdefault(item['doc_id'],[]).append(item)
    registry=[]
    for doc_id,versions in sorted(groups.items()):
        versions=sorted(versions,key=lambda x:x['version_number'])
        active_candidates=[v for v in versions if v['status']=='ACTIVE']
        active=(active_candidates or versions)[-1]
        registry.append({k:active[k] for k in ('doc_id','doc_type','area','date','topic','version','status','activity','path','precedence')}|{'versions':[{k:v[k] for k in ('version','status','date','path')} for v in versions]})
    return sorted(registry,key=lambda x:(-x['precedence'],x['area'],x['topic'],x['doc_id']))

def build():
    errors=[]; tickets=build_tickets(errors); knowledge=build_knowledge(errors)
    if errors:
        print('\n'.join('ERROR: '+e for e in errors),file=sys.stderr); return 1
    if DIST.exists(): shutil.rmtree(DIST)
    shutil.copytree(ROOT/'site',DIST); (DIST/'data').mkdir(parents=True,exist_ok=True)
    (DIST/'data'/'registry.json').write_text(json.dumps({'version':1,'tickets':tickets},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (DIST/'data'/'registry.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['case_id','area','date','topic','status','active_request']); w.writeheader(); w.writerows([{k:c[k] for k in w.fieldnames} for c in tickets])
    for c in tickets:
        case_dir=DIST/'cases'/c['case_id']; case_dir.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/c['active_request'],case_dir/'request.txt')
        docs=[]
        for d in c['documents']:
            src=ROOT/d['path']; dst=case_dir/d['name']; shutil.copy2(src,dst); docs.append({**d,'url':f"cases/{c['case_id']}/{d['name']}"})
        (case_dir/'case.json').write_text(json.dumps({**c,'documents':docs,'request_url':f"cases/{c['case_id']}/request.txt"},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (DIST/'data'/'knowledge.json').write_text(json.dumps({'version':1,'precedence':['POLICY','PLAYBOOK','REFERENCE'],'resolution':'highest ACTIVE version per DOC_ID; POLICY > PLAYBOOK > REFERENCE; exact AREA preferred over GLOBAL by consumer','documents':knowledge},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (DIST/'data'/'knowledge.csv').open('w',encoding='utf-8',newline='') as f:
        fields=['doc_id','doc_type','area','date','topic','version','status','path']; w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows([{k:d[k] for k in fields} for d in knowledge])
    for d in knowledge:
        out=DIST/'knowledge'/d['doc_type']/d['doc_id']; out.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/d['path'],out/'current.txt')
        (out/'current.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Validated and built {len(tickets)} ticket(s), {len(knowledge)} knowledge document(s)')
    return 0

if __name__=='__main__': raise SystemExit(build())
