#!/usr/bin/env python3
from pathlib import Path
import csv,json,re,shutil,sys
R=Path(__file__).resolve().parents[1]; T=R/'tickets'; K=R/'knowledge'; D=R/'dist'
CASE=re.compile(r'^IMC-([A-Z0-9]+)-(\d{3,})(?:-(\d{2}))?$'); GW=re.compile(r'^GW\d{3}$'); TAG=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
REQ=re.compile(r'^REQUEST(?:_V(\d+))?\.txt$'); VER=re.compile(r'^V(\d{3,})$')
DOM={'DATA_ROOM','GATEWAY','DATABASE','RESULTS','SCHEDULE','MATCH_REPORT','TRANSFERS','PLAYER_CODEX','PLAYER_STATS','IMPORTER','SITE','MINISITE','DEPLOYMENT','COMPETITION','AUTHORITY','GENERAL'}
DT={'REQUEST','RESPONSE','DECISION','REPORT','AUDIT','POLICY'}; KT={'POLICY','PLAYBOOK','REFERENCE'}; KP={'POLICY':300,'PLAYBOOK':200,'REFERENCE':100}

def labels(p,names):
 l=p.read_text(encoding='utf-8').splitlines(); m={}
 for i,n in enumerate(names):
  x=n+': '
  if i>=len(l) or not l[i].startswith(x) or not l[i][len(x):].strip(): raise ValueError(f'{p}: {n} non valido')
  m[n]=l[i][len(x):].strip()
 j=len(names)+(1 if len(l)>len(names) and l[len(names)]=='' else 0); return m,'\n'.join(l[j:]).strip()

def doc(p):
 m,b=labels(p,['CASE_ID','DOC_TYPE','AREA','DATE','TOPIC'])
 if not CASE.match(m['CASE_ID']) or m['DOC_TYPE'] not in DT: raise ValueError(f'{p}: documento ticket non valido')
 return m,b

def meta(p):
 m,b=labels(p,['CASE_ID','AREA','DOMAIN','GW','TOPIC','TAGS','CASE_KIND','ROOT_CASE_ID']); a=CASE.match(m['CASE_ID']); r=CASE.match(m['ROOT_CASE_ID'])
 if not a or not r or r.group(3) or m['AREA']!=a.group(1) or m['AREA']!=r.group(1) or m['DOMAIN'] not in DOM: raise ValueError(f'{p}: gerarchia non valida')
 g=[x.strip() for x in m['GW'].split(',') if x.strip()]; t=[x.strip() for x in m['TAGS'].split(',') if x.strip()]
 if not g or any(x!='GLOBAL' and not GW.match(x) for x in g) or ('GLOBAL' in g and len(g)>1): raise ValueError(f'{p}: GW non valido')
 if not t or len(t)!=len(set(t)) or any(not TAG.match(x) for x in t): raise ValueError(f'{p}: TAGS non validi')
 it=int(a.group(3)) if a.group(3) else None
 if (m['CASE_KIND']=='ROOT' and (it is not None or m['CASE_ID']!=m['ROOT_CASE_ID'])) or (m['CASE_KIND']=='ITERATION' and it is None) or m['CASE_KIND'] not in {'ROOT','ITERATION'}: raise ValueError(f'{p}: CASE_KIND non valido')
 return m|{'gw':g,'tags':t,'iteration':it},b

def status(ds):
 q=[d for d in ds if d['doc_type']=='DECISION']
 if q:
  x=re.search(r'(?mi)^STATUS:\s*([A-Z_]+)',q[-1]['body']); return x.group(1) if x else 'CLOSED'
 return 'WAITING_REVIEW' if any(d['doc_type']=='RESPONSE' for d in ds) else 'OPEN'

def tickets(err):
 out=[]
 for d in sorted(p for p in T.glob('*/*/*') if p.is_dir()):
  area,year,old=d.relative_to(T).parts; mp=d/'CASE_META.txt'
  if not mp.exists(): err.append(f'{old}: CASE_META.txt mancante'); continue
  try: cm,_=meta(mp)
  except Exception as e: err.append(str(e)); continue
  ds=[]
  for p in sorted(d.glob('*.txt')):
   if p.name=='CASE_META.txt': continue
   try: m,b=doc(p)
   except Exception as e: err.append(str(e)); continue
   if m['AREA']!=area or m['DATE'][:4]!=year: err.append(f'{p}: path incoerente')
   rv=0; z=REQ.match(p.name)
   if z: rv=int(z.group(1) or 1)
   ds.append({'name':p.name,'path':str(p.relative_to(R)),'doc_type':m['DOC_TYPE'],'date':m['DATE'],'topic':m['TOPIC'],'request_version':rv,'body':b})
  rs=sorted([x for x in ds if x['doc_type']=='REQUEST' and x['request_version']],key=lambda x:(x['request_version'],x['name']))
  if not rs: err.append(f'{old}: REQUEST mancante'); continue
  active=rs[-1]
  if active['topic']!=cm['TOPIC']: err.append(f'{old}: TOPIC CASE_META/REQUEST incoerente')
  alias=[] if old==cm['CASE_ID'] else [old]
  search=' '.join([cm['CASE_ID'],old,cm['ROOT_CASE_ID'],cm['AREA'],cm['DOMAIN'],cm['GW'],cm['TOPIC'],cm['TAGS']]+[x['body'] for x in ds]).lower()
  out.append({'case_id':cm['CASE_ID'],'canonical_case_id':cm['CASE_ID'],'original_case_id':old,'aliases':alias,'case_kind':cm['CASE_KIND'],'root_case_id':cm['ROOT_CASE_ID'],'iteration':cm['iteration'],'area':cm['AREA'],'date':active['date'],'domain':cm['DOMAIN'],'gw':cm['gw'],'topic':cm['TOPIC'],'tags':cm['tags'],'status':status(ds),'active_request':active['path'],'case_meta':str(mp.relative_to(R)),'searchable_text':search,'documents':[{k:x[k] for k in ('name','path','doc_type','date','topic','request_version')} for x in ds]})
 ids={x['canonical_case_id'] for x in out}
 for x in out:
  if x['root_case_id'] not in ids: err.append(f"{x['canonical_case_id']}: root mancante")
 aliases={a:x['canonical_case_id'] for x in out for a in x['aliases']}
 def key(x):
  m=CASE.match(x['canonical_case_id']); return x['area'],int(m.group(2)),x['iteration'] or 0
 return sorted(out,key=key),aliases

def knowledge(err):
 groups={}
 for p in sorted(K.rglob('*.txt')) if K.exists() else []:
  try: m,b=labels(p,['DOC_ID','DOC_TYPE','AREA','DATE','TOPIC','VERSION','STATUS','ACTIVITY'])
  except Exception as e: err.append(str(e)); continue
  if m['DOC_TYPE'] not in KT or not VER.match(m['VERSION']): err.append(f'{p}: knowledge non valido'); continue
  v=int(VER.match(m['VERSION']).group(1)); x={'doc_id':m['DOC_ID'],'doc_type':m['DOC_TYPE'],'area':m['AREA'],'date':m['DATE'],'topic':m['TOPIC'],'version':m['VERSION'],'status':m['STATUS'],'activity':[z.strip() for z in m['ACTIVITY'].split(',') if z.strip()],'path':str(p.relative_to(R)),'precedence':KP[m['DOC_TYPE']],'n':v}; groups.setdefault(x['doc_id'],[]).append(x)
 out=[]
 for _,vs in sorted(groups.items()):
  vs.sort(key=lambda x:x['n']); a=([x for x in vs if x['status']=='ACTIVE'] or vs)[-1]; out.append({k:a[k] for k in ('doc_id','doc_type','area','date','topic','version','status','activity','path','precedence')}|{'versions':[{k:v[k] for k in ('version','status','date','path')} for v in vs]})
 return sorted(out,key=lambda x:(-x['precedence'],x['area'],x['topic']))

def resolver(c,cid,alias=None):
 o=D/'cases'/cid; o.mkdir(parents=True,exist_ok=True); shutil.copy2(R/c['active_request'],o/'request.txt'); shutil.copy2(R/c['case_meta'],o/'CASE_META.txt'); docs=[]
 for d in c['documents']:
  shutil.copy2(R/d['path'],o/d['name']); docs.append(d|{'url':f"cases/{cid}/{d['name']}"})
 (o/'case.json').write_text(json.dumps(c|{'documents':docs,'request_url':f'cases/{cid}/request.txt','resolver_case_id':cid,'alias_of':alias},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def build():
 e=[]; ts,al=tickets(e); ks=knowledge(e)
 if e: print('\n'.join('ERROR: '+x for x in e),file=sys.stderr); return 1
 if D.exists(): shutil.rmtree(D)
 shutil.copytree(R/'site',D); (D/'data').mkdir(parents=True,exist_ok=True)
 roots=[]
 for r in [x for x in ts if x['case_kind']=='ROOT']:
  ch=sorted([x for x in ts if x['root_case_id']==r['canonical_case_id'] and x['case_kind']=='ITERATION'],key=lambda x:x['iteration'] or 0); roots.append({'root_case_id':r['canonical_case_id'],'area':r['area'],'domain':r['domain'],'topic':r['topic'],'status':r['status'],'iteration_count':len(ch),'iterations':[x['canonical_case_id'] for x in ch]})
 (D/'data'/'registry.json').write_text(json.dumps({'version':2,'tickets':ts,'macro_cases':roots},ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); (D/'data'/'case-aliases.json').write_text(json.dumps({'version':1,'aliases':al},indent=2)+'\n')
 with (D/'data'/'registry.csv').open('w',newline='',encoding='utf-8') as f:
  fs=['canonical_case_id','original_case_id','area','domain','gw','topic','tags','case_kind','root_case_id','iteration','date','status']; w=csv.DictWriter(f,fieldnames=fs); w.writeheader()
  for x in ts: w.writerow({**{k:x[k] for k in fs if k not in {'gw','tags'}},'gw':','.join(x['gw']),'tags':','.join(x['tags'])})
 for x in ts:
  resolver(x,x['canonical_case_id']); [resolver(x,a,x['canonical_case_id']) for a in x['aliases']]
 (D/'data'/'knowledge.json').write_text(json.dumps({'version':1,'documents':ks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (D/'data'/'knowledge.csv').open('w',newline='',encoding='utf-8') as f:
  fs=['doc_id','doc_type','area','date','topic','version','status','path']; w=csv.DictWriter(f,fieldnames=fs); w.writeheader(); w.writerows([{k:x[k] for k in fs} for x in ks])
 for x in ks:
  o=D/'knowledge'/x['doc_type']/x['doc_id']; o.mkdir(parents=True,exist_ok=True); shutil.copy2(R/x['path'],o/'current.txt'); (o/'current.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'Validated and built {len(ts)} ticket(s), {len(ks)} knowledge document(s), {len(al)} alias(es)'); return 0
if __name__=='__main__': raise SystemExit(build())
