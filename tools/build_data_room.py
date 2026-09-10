#!/usr/bin/env python3
from __future__ import annotations
import csv, json, re, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TICKETS=ROOT/'tickets'; KNOWLEDGE=ROOT/'knowledge'; DIST=ROOT/'dist'
TICKET_LABELS=['CASE_ID','DOC_TYPE','AREA','DATE','TOPIC']
CASE_META_LABELS=['CASE_ID','AREA','DOMAIN','GW','TOPIC','TAGS','CASE_KIND','ROOT_CASE_ID']
KNOWLEDGE_LABELS=['DOC_ID','DOC_TYPE','AREA','DATE','TOPIC','VERSION','STATUS','ACTIVITY']
TICKET_DOC_TYPES={'REQUEST','RESPONSE','DECISION','REPORT','AUDIT','POLICY'}
KNOWLEDGE_TYPES={'POLICY','PLAYBOOK','REFERENCE'}
KNOWLEDGE_STATUSES={'ACTIVE','DEPRECATED'}
STATUSES={'OPEN','IN_PROGRESS','WAITING_REVIEW','APPROVED','APPROVED_WITH_CHANGES','REJECTED','CLOSED'}
DOMAINS={'DATA_ROOM','GATEWAY','DATABASE','RESULTS','SCHEDULE','MATCH_REPORT','TRANSFERS','PLAYER_CODEX','PLAYER_STATS','IMPORTER','SITE','MINISITE','DEPLOYMENT','COMPETITION','AUTHORITY','GENERAL'}
CASE_RE=re.compile(r'^IMC-([A-Z0-9]+)-(\d{3,})(?:-(\d{2}))?$')
DOC_ID_RE=re.compile(r'^IMC-[A-Z0-9-]+$'); DATE_RE=re.compile(r'^\d{4}-\d{2}-\d{2}$')
REQ_RE=re.compile(r'^REQUEST(?:_V(\d+))?\.txt$'); VER_RE=re.compile(r'^V(\d{3,})$')
TAG_RE=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$'); GW_RE=re.compile(r'^GW\d{3}$')
PRECEDENCE={'POLICY':300,'PLAYBOOK':200,'REFERENCE':100}

def parse_labels(path:Path,labels:list[str]):
    lines=path.read_text(encoding='utf-8').splitlines(); meta={}
    if len(lines)<len(labels): raise ValueError(f'{path}: documento troppo corto')
    for i,label in enumerate(labels):
        prefix=label+': '
        if not lines[i].startswith(prefix): raise ValueError(f'{path}: riga {i+1} deve iniziare con {prefix!r}')
        value=lines[i][len(prefix):].strip()
        if not value: raise ValueError(f'{path}: {label} vuoto')
        meta[label]=value
    body_start=len(labels)
    if body_start<len(lines) and lines[body_start]=='': body_start+=1
    return meta,'\n'.join(lines[body_start:]).strip()

def parse_ticket(path:Path):
    meta,body=parse_labels(path,TICKET_LABELS)
    if meta['DOC_TYPE'] not in TICKET_DOC_TYPES: raise ValueError(f'{path}: DOC_TYPE non ammesso')
    if not CASE_RE.match(meta['CASE_ID']): raise ValueError(f'{path}: CASE_ID non valido')
    if not DATE_RE.match(meta['DATE']): raise ValueError(f'{path}: DATE non valida')
    return meta,body

def parse_case_meta(path:Path):
    meta,body=parse_labels(path,CASE_META_LABELS)
    m=CASE_RE.match(meta['CASE_ID']); r=CASE_RE.match(meta['ROOT_CASE_ID'])
    if not m or not r or r.group(3): raise ValueError(f'{path}: CASE_ID/ROOT_CASE_ID non valido')
    if meta['AREA']!=m.group(1) or meta['AREA']!=r.group(1): raise ValueError(f'{path}: AREA incoerente con CASE_ID')
    if meta['DOMAIN'] not in DOMAINS: raise ValueError(f'{path}: DOMAIN non controllato')
    gw=[x.strip() for x in meta['GW'].split(',') if x.strip()]
    if not gw or any(x!='GLOBAL' and not GW_RE.match(x) for x in gw) or ('GLOBAL' in gw and len(gw)>1): raise ValueError(f'{path}: GW non valido')
    tags=[x.strip() for x in meta['TAGS'].split(',') if x.strip()]
    if not tags or len(tags)!=len(set(tags)) or any(not TAG_RE.match(x) for x in tags): raise ValueError(f'{path}: TAGS non validi')
    kind=meta['CASE_KIND']
    if kind not in {'ROOT','ITERATION'}: raise ValueError(f'{path}: CASE_KIND non valido')
    iteration=None
    if kind=='ROOT':
        if meta['CASE_ID']!=meta['ROOT_CASE_ID'] or m.group(3): raise ValueError(f'{path}: ROOT incoerente')
    else:
        if not m.group(3) or meta['CASE_ID']==meta['ROOT_CASE_ID']: raise ValueError(f'{path}: ITERATION incoerente')
        iteration=int(m.group(3))
        extra=dict(line.split(': ',1) for line in body.splitlines() if ': ' in line)
        if extra.get('ITERATION') and int(extra['ITERATION'])!=iteration: raise ValueError(f'{path}: ITERATION metadata incoerente')
    return {**meta,'gw':gw,'tags':tags,'iteration':iteration},body

def parse_knowledge(path:Path):
    meta,body=parse_labels(path,KNOWLEDGE_LABELS)
    if meta['DOC_TYPE'] not in KNOWLEDGE_TYPES or not DOC_ID_RE.match(meta['DOC_ID']) or not DATE_RE.match(meta['DATE']) or not VER_RE.match(meta['VERSION']) or meta['STATUS'] not in KNOWLEDGE_STATUSES: raise ValueError(f'{path}: metadata knowledge non validi')
    return meta,body

def request_version(path:Path):
    m=REQ_RE.match(path.name); return int(m.group(1) or 1) if m else 0

def derive_status(docs):
    decisions=[d for d in docs if d['doc_type']=='DECISION']
    if decisions:
        body=decisions[-1]['body']; m=re.search(r'(?mi)^STATUS:\s*([A-Z_]+)\s*$',body)
        return m.group(1) if m and m.group(1) in STATUSES else 'CLOSED'
    return 'WAITING_REVIEW' if any(d['doc_type']=='RESPONSE' for d in docs) else 'OPEN'

def case_sort(c):
    m=CASE_RE.match(c['canonical_case_id']); return (c['area'],int(m.group(2)),c['iteration'] or 0)

def build_tickets(errors):
    physical={}
    for case_dir in sorted(p for p in TICKETS.glob('*/*/*') if p.is_dir()):
        parts=case_dir.relative_to(TICKETS).parts
        if len(parts)!=3: continue
        area,year,original_id=parts
        meta_path=case_dir/'CASE_META.txt'
        if not meta_path.exists(): errors.append(f'{original_id}: CASE_META.txt mancante'); continue
        try: cm,_=parse_case_meta(meta_path)
        except Exception as e: errors.append(str(e)); continue
        docs=[]
        for path in sorted(case_dir.glob('*.txt')):
            if path.name=='CASE_META.txt': continue
            try: meta,body=parse_ticket(path)
            except Exception as e: errors.append(str(e)); continue
            if meta['AREA']!=area or year!=meta['DATE'][:4]: errors.append(f'{path}: AREA/anno incoerente con directory')
            docs.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'name':path.name,'case_id':meta['CASE_ID'],'doc_type':meta['DOC_TYPE'],'area':meta['AREA'],'date':meta['DATE'],'topic':meta['TOPIC'],'body':body,'request_version':request_version(path)})
        reqs=sorted([d for d in docs if d['doc_type']=='REQUEST' and d['request_version']],key=lambda d:(d['request_version'],d['name']))
        if not reqs: errors.append(f'{original_id}: REQUEST mancante'); continue
        active=reqs[-1]
        if cm['TOPIC']!=active['topic']: errors.append(f'{original_id}: CASE_META TOPIC diverso dal REQUEST attivo')
        aliases=[] if original_id==cm['CASE_ID'] else [original_id]
        searchable=' '.join([cm['CASE_ID'],original_id,cm['ROOT_CASE_ID'],cm['AREA'],cm['DOMAIN'],cm['GW'],cm['TOPIC'],cm['TAGS']] + [d['body'] for d in docs]).lower()
        item={'case_id':cm['CASE_ID'],'canonical_case_id':cm['CASE_ID'],'original_case_id':original_id,'aliases':aliases,'case_kind':cm['CASE_KIND'],'root_case_id':cm['ROOT_CASE_ID'],'iteration':cm['iteration'],'area':cm['AREA'],'date':active['date'],'domain':cm['DOMAIN'],'gw':cm['gw'],'topic':cm['TOPIC'],'tags':cm['tags'],'status':derive_status(docs),'active_request':active['path'],'case_meta':str(meta_path.relative_to(ROOT)).replace('\\','/'),'searchable_text':searchable,'documents':[{k:d[k] for k in ('name','path','doc_type','date','topic','request_version')} for d in docs]}
        if item['canonical_case_id'] in physical: errors.append(f"canonical duplicato: {item['canonical_case_id']}")
        physical[item['canonical_case_id']]=item
    for c in physical.values():
        if c['root_case_id'] not in physical: errors.append(f"{c['canonical_case_id']}: root mancante {c['root_case_id']}")
    aliases={}
    for c in physical.values():
        for a in c['aliases']:
            if a in physical or a in aliases: errors.append(f'alias collision: {a}')
            aliases[a]=c['canonical_case_id']
    return sorted(physical.values(),key=case_sort),aliases

def build_knowledge(errors):
    groups={}
    if not KNOWLEDGE.exists(): return []
    for path in sorted(KNOWLEDGE.rglob('*.txt')):
        try: meta,body=parse_knowledge(path)
        except Exception as e: errors.append(str(e)); continue
        parts=path.relative_to(KNOWLEDGE).parts
        if len(parts)!=4: errors.append(f'{path}: path knowledge non valido'); continue
        dtype,area,doc_id,name=parts
        if dtype!=meta['DOC_TYPE'] or area!=meta['AREA'] or doc_id!=meta['DOC_ID'] or name!=meta['VERSION']+'.txt': errors.append(f'{path}: metadata/path knowledge incoerenti')
        version=int(VER_RE.match(meta['VERSION']).group(1)); item={'doc_id':meta['DOC_ID'],'doc_type':meta['DOC_TYPE'],'area':meta['AREA'],'date':meta['DATE'],'topic':meta['TOPIC'],'version':meta['VERSION'],'version_number':version,'status':meta['STATUS'],'activity':[x.strip() for x in meta['ACTIVITY'].split(',') if x.strip()],'path':str(path.relative_to(ROOT)).replace('\\','/'),'body':body,'precedence':PRECEDENCE[meta['DOC_TYPE']]}; groups.setdefault(item['doc_id'],[]).append(item)
    registry=[]
    for doc_id,versions in sorted(groups.items()):
        versions=sorted(versions,key=lambda x:x['version_number']); active=([v for v in versions if v['status']=='ACTIVE'] or versions)[-1]
        registry.append({k:active[k] for k in ('doc_id','doc_type','area','date','topic','version','status','activity','path','precedence')}|{'versions':[{k:v[k] for k in ('version','status','date','path')} for v in versions]})
    return sorted(registry,key=lambda x:(-x['precedence'],x['area'],x['topic'],x['doc_id']))

def copy_case_resolver(c,out_id,alias_of=None):
    case_dir=DIST/'cases'/out_id; case_dir.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/c['active_request'],case_dir/'request.txt'); shutil.copy2(ROOT/c['case_meta'],case_dir/'CASE_META.txt')
    docs=[]
    for d in c['documents']:
        src=ROOT/d['path']; dst=case_dir/d['name']; shutil.copy2(src,dst); docs.append({**d,'url':f"cases/{out_id}/{d['name']}"})
    payload={**c,'documents':docs,'request_url':f"cases/{out_id}/request.txt",'resolver_case_id':out_id,'alias_of':alias_of}
    (case_dir/'case.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def build():
    errors=[]; tickets,aliases=build_tickets(errors); knowledge=build_knowledge(errors)
    if errors: print('\n'.join('ERROR: '+e for e in errors),file=sys.stderr); return 1
    if DIST.exists(): shutil.rmtree(DIST)
    shutil.copytree(ROOT/'site',DIST); (DIST/'data').mkdir(parents=True,exist_ok=True)
    roots=[]
    for root in [c for c in tickets if c['case_kind']=='ROOT']:
        children=[c for c in tickets if c['root_case_id']==root['canonical_case_id'] and c['case_kind']=='ITERATION']
        roots.append({'root_case_id':root['canonical_case_id'],'domain':root['domain'],'area':root['area'],'topic':root['topic'],'status':root['status'],'iteration_count':len(children),'iterations':[c['canonical_case_id'] for c in sorted(children,key=lambda x:x['iteration'] or 0)]})
    registry={'version':2,'tickets':tickets,'macro_cases':roots}
    (DIST/'data'/'registry.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (DIST/'data'/'case-aliases.json').write_text(json.dumps({'version':1,'aliases':aliases},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (DIST/'data'/'registry.csv').open('w',encoding='utf-8',newline='') as f:
        fields=['canonical_case_id','original_case_id','area','domain','gw','topic','tags','case_kind','root_case_id','iteration','date','status']; w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for c in tickets: w.writerow({**{k:c[k] for k in fields if k not in {'gw','tags'}},'gw':','.join(c['gw']),'tags':','.join(c['tags'])})
    for c in tickets:
        copy_case_resolver(c,c['canonical_case_id'])
        for alias in c['aliases']: copy_case_resolver(c,alias,c['canonical_case_id'])
    (DIST/'data'/'knowledge.json').write_text(json.dumps({'version':1,'precedence':['POLICY','PLAYBOOK','REFERENCE'],'resolution':'highest ACTIVE version per DOC_ID; POLICY > PLAYBOOK > REFERENCE; exact AREA preferred over GLOBAL by consumer','documents':knowledge},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (DIST/'data'/'knowledge.csv').open('w',encoding='utf-8',newline='') as f:
        fields=['doc_id','doc_type','area','date','topic','version','status','path']; w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows([{k:d[k] for k in fields} for d in knowledge])
    for d in knowledge:
        out=DIST/'knowledge'/d['doc_type']/d['doc_id']; out.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/d['path'],out/'current.txt'); (out/'current.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Validated and built {len(tickets)} ticket(s