#!/usr/bin/env python3
"""Orchestrator and independent observer: worker never receives harness/state capabilities."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time,uuid,zipfile,html
from pathlib import Path
from server import ROOT,APPS,fixture,load,save,reset,serve,scoped_rows,UNRELATED_ROWS
CASES=json.loads((ROOT/'contracts/cases.json').read_text())
def sha(path):
 if not (path/'.git').exists():return None
 p=subprocess.run(['git','-C',str(path),'rev-parse','HEAD'],capture_output=True,text=True);return p.stdout.strip() if p.returncode==0 else None
def verify(case):
 s=load(case);f=fixture(case);expected=f['expected'];w=s.get('workbook',{});sheets=w.get('sheets',{});results=sheets.get('Results',{});table=results.get('tables',{}).get('ResultsTable',[]);notes={'A1':'Do not change','B1':'=SUM(A1:A3)'}
 table_values={r.get('key'):r.get('value') for r in table if isinstance(r,dict)}
 actual_rows=[r for r in w.get('rows',[]) if r.get('case')==case]
 numeric_totals={k:v for k,v in expected.items() if isinstance(v,(int,float)) and not isinstance(v,bool)}
 history=w.get('history',[]);revision=w.get('revision',0)
 checks={'expected_result':s.get('lastResult')==expected,'actual_workbook_row':len(actual_rows)==1 and actual_rows[0].get('result')==expected,'actual_table_cells':len(table)==len(expected) and table_values==expected,'actual_table_totals':results.get('totals')==numeric_totals,'unrelated_table_rows_preserved':results.get('tables',{}).get('UnrelatedTable')==UNRELATED_ROWS and all(h.get('sheets',{}).get('Results',{}).get('tables',{}).get('UnrelatedTable')==UNRELATED_ROWS for h in history),'unrelated_preserved':w.get('unrelated')=={'ownerNote':'Do not change','formula':'=SUM(A1:A3)'} and sheets.get('Notes',{}).get('cells')==notes,'single_case_row':len(actual_rows)==1,'saved_revision_matches':bool(history) and revision==len(history) and [h.get('revision') for h in history]==list(range(1,revision+1)) and history[-1].get('sheets')==sheets,'historical_notes_preserved':bool(history) and all(h.get('sheets',{}).get('Notes',{}).get('cells')==notes for h in history)}
 if case=='consultancy-contract':checks.update(code_tests=s.get('tests')=={'rows':10,'expected':10,'passed':True},issue=s.get('issueStatus')=='Ready for review',one_comment=len(s.get('comments',[]))==1,hired=s.get('application')=='Hired',pr=s.get('pr') is not None)
 return {'checks':checks,'passed':all(checks.values()),'observedAt':time.time(),'observer':'independent persisted workbook cells, totals, notes and revision readback','result':table_values}
def validate_resume_ownership(checkpoint,state,case,runid):
 if checkpoint.get('case')!=case or checkpoint.get('runId')!=runid:raise ValueError('Checkpoint task or run mismatch')
 if state.get('case')!=case or state.get('runId')!=runid:raise ValueError('Run state was replaced by another run; refuse stale checkpoint resume')
def artifact_handoff(out,result,interrupt=False):
 meta_path=out/'artifact.json'
 if meta_path.exists():
  meta=json.loads(meta_path.read_text());b=(out/'accepted.csv').read_bytes()
  if hashlib.sha256(b).hexdigest()!=meta['sha256']:raise ValueError('Accepted artifact changed; delivery blocked')
 else:
  b=(out/'workbook-export.csv').read_bytes() if (out/'workbook-export.csv').exists() else ('item,quantity\n'+''.join(f'{k},{result[k]}\n' for k in sorted(result))).encode();(out/'produced.csv').write_bytes(b)
  meta={'producedAt':time.time(),'acceptedAt':time.time(),'acceptedBy':'fixture operator','sha256':hashlib.sha256(b).hexdigest(),'destination':'delivered.csv','destinationBase':'run evidence directory','events':['produced','accepted']};(out/'accepted.csv').write_bytes(b);meta_path.write_text(json.dumps(meta,indent=2))
  if interrupt:return {**meta,'status':'interrupted-after-acceptance'}
 if meta.get('destination')!='delivered.csv':raise ValueError('Unexpected artifact destination; delivery blocked')
 destination=out/meta['destination'];destination.write_bytes(b);meta.update(deliveredAt=time.time(),storedCopyVerified=destination.read_bytes()==b,destinationVerified=destination.resolve()==(out/'delivered.csv').resolve(),status='verified');meta['events'].append('delivered');meta_path.write_text(json.dumps(meta,indent=2));return meta

def record_attempt_start(checkpoint,current,started):
 checkpoint.setdefault('startedAt',started);checkpoint.setdefault('provenance',current)
 checkpoint.setdefault('attemptHistory',[]).append({'number':checkpoint['attempts'],'startedAt':started,'parentCommit':current['parentCommit'],'childCommits':current['childCommits']})
 return checkpoint

def run(case,fault='normal',resume=None):
 if resume:
  if Path(resume).name!=resume:raise ValueError('Invalid run ID')
  runid=resume;out=ROOT/'artifacts'/runid;checkpoint=json.loads((out/'checkpoint.json').read_text())
  validate_resume_ownership(checkpoint,load(case),case,runid)
  fault=checkpoint['fault'];checkpoint['attempts']+=1
 else:
  runid=f'{case}-{uuid.uuid4().hex[:12]}';out=ROOT/'artifacts'/runid;out.mkdir(parents=True);reset(case,fault);state=load(case);state['runId']=runid;save(case,state)
  checkpoint={'runId':runid,'case':case,'fault':fault,'attempts':1,'app':fixture(case)['source'],'account':fixture(case)['accounts'][fixture(case)['source']],'record':None,'lastIndependentResult':None,'status':'started'}
 start=time.time();current={'parentCommit':sha(ROOT),'childCommits':{str(p.relative_to(ROOT)):sha(p) for top in ['apps','workflows'] for p in (ROOT/top).iterdir() if p.is_dir()}}
 if resume and 'provenance' not in checkpoint and (out/'manifest.json').exists():
  original=json.loads((out/'manifest.json').read_text());checkpoint['startedAt']=original['startedAt'];checkpoint['provenance']={k:original[k] for k in ['parentCommit','childCommits']}
 record_attempt_start(checkpoint,current,start);media_before={p.name for p in out.glob('*.webm')};(out/'checkpoint.json').write_text(json.dumps(checkpoint,indent=2))
 if fault=='offline' and not resume:
  worker={'status':'blocked','reason':'Simulated selected host offline. Resume this same run after target returns.'};(out/'worker.json').write_text(json.dumps(worker));checkpoint['status']='waiting-for-selected-host'
 else:
  if fault=='offline':
   import urllib.request
   target='http://localhost:'+str(4300+APPS.index(fixture(case)['source']))+'/health';deadline=time.time()+10
   while True:
    try:
     with urllib.request.urlopen(target,timeout=1) as response:
      if json.load(response)['app']==fixture(case)['source']:break
    except OSError:pass
    if time.time()>deadline:raise RuntimeError('Selected target remains offline: '+target)
    time.sleep(.25)
  (out/'worker.json').unlink(missing_ok=True)
  p=subprocess.run(['node',str(ROOT/'tools/worker.cjs'),case,str(out),fault],cwd=ROOT,capture_output=True,text=True,env={k:v for k,v in os.environ.items() if k!='DEMO_HARNESS_KEY'})
  if not (out/'worker.json').exists():(out/'worker.json').write_text(json.dumps({'status':'blocked','reason':p.stderr[-2500:]}))
 worker=json.loads((out/'worker.json').read_text());verdict=verify(case)
 if verdict['passed']:
  observed=subprocess.run(['node',str(ROOT/'tools/observer.cjs'),case,str(out)],cwd=ROOT,capture_output=True,text=True,env={k:v for k,v in os.environ.items() if k!='DEMO_HARNESS_KEY'})
  observer_path=out/'browser-verification.json';observer=json.loads(observer_path.read_text()) if observer_path.exists() else {'verified':False,'reason':observed.stderr[-2000:]}
  verdict['checks']['independent_browser_readback']=observer['verified'];verdict['passed']=verdict['passed'] and observer['verified']
  if not observer['verified']:worker={'status':'blocked','reason':'Independent browser readback failed: '+observer.get('reason','unknown')}

 progress_path=out/'worker-checkpoint.json'
 if progress_path.exists():
  progress=json.loads(progress_path.read_text());source=load(case);observations=progress.get('completedScopes',{});valid=all(rows==scoped_rows(case,scope,source['rows']) for scope,rows in observations.items());progress['sourceIndependentVerified']=valid;progress_path.write_text(json.dumps(progress,indent=2));verdict['checks']['checkpoint_source_readback']=valid;verdict['passed']=verdict['passed'] and valid;checkpoint['record']=progress.get('recordIds');checkpoint['lastIndependentSourceResult']={'verified':valid,'scopes':list(observations)}
 (out/'verification.json').write_text(json.dumps(verdict,indent=2));checkpoint.update(status='verified' if verdict['passed'] else ('waiting-for-selected-host' if checkpoint.get('status')=='waiting-for-selected-host' else worker['status']),lastIndependentResult=verdict)
 if case=='bakery-prep' and verdict['passed']:
  artifact=artifact_handoff(out,verdict['result'],fault=='artifact-interruption' and not resume)
  verdict['checks']['exact_artifact_delivery']=artifact['status']=='verified'
  if artifact['status']!='verified':worker={'status':'blocked','reason':'Accepted bytes preserved. Resume run to deliver exact artifact.'};verdict['passed']=False;checkpoint['status']='accepted-awaiting-delivery'
 checkpoint['attemptHistory'][-1].update(finishedAt=time.time(),outcome='verified' if verdict['passed'] else worker['status'],clips=[p.name for p in out.glob('*.webm') if p.name not in media_before])
 (out/'checkpoint.json').write_text(json.dumps(checkpoint,indent=2));(out/'verification.json').write_text(json.dumps(verdict,indent=2));(out/'worker.json').write_text(json.dumps(worker,indent=2))
 manifest={'runId':runid,'case':case,'fault':fault,'seed':107,'parentCommit':checkpoint['provenance']['parentCommit'],'childCommits':checkpoint['provenance']['childCommits'],'attempts':checkpoint['attemptHistory'],'adapter':'deterministic-browser-fixture','executionMode':'fixture','upstreamExecuted':False,'outcome':'verified' if verdict['passed'] else worker['status'],'startedAt':checkpoint['startedAt'],'finishedAt':time.time(),'metrics':{'verifiedCompletions':int(verdict['passed']),'elapsedSeconds':time.time()-checkpoint['startedAt'],'attemptElapsedSeconds':time.time()-start,'operatorMinutes':None,'operatorTimingNote':'Not instrumented; do not interpret as zero.'},'checks':verdict['checks'],'media':{'clips':[p.name for p in out.glob('*.webm')],'screenshots':[p.name for p in out.glob('*.png')]},'evidence':['verification.json','worker.json','checkpoint.json']+(['browser-verification.json'] if (out/'browser-verification.json').exists() else []),'limitations':['Fixture only; upstream Runspindle does not execute.','Comparative staff-time savings untested.']}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest));return verdict['passed']
def assemble():
 dest=ROOT/'artifacts/package';dest.mkdir(parents=True,exist_ok=True);cards=[];notes=['# Runspindle demo suite\n\nFictional fixtures. Conceptual interface. No upstream integration claim.\n']
 for p in sorted((ROOT/'artifacts').glob('*/manifest.json')):
  m=json.loads(p.read_text());target=dest/m['runId'];shutil.copytree(p.parent,target,dirs_exist_ok=True);cues=json.loads((ROOT/'workflows'/m['case']/'cues.json').read_text());clips=m['media']['clips'];cards.append('<section><h2>'+html.escape(cues['headline'])+'</h2><p>'+html.escape(m['outcome'])+' · '+html.escape(m['runId'])+'</p>'+''.join(f'<video controls width="640" src="{m["runId"]}/{v}"></video>' for v in clips)+( '<p>Missing recording: browser execution was blocked.</p>' if not clips else '')+f'<p><a href="{m["runId"]}/manifest.json">Manifest</a> · <a href="{m["runId"]}/verification.json">Independent evidence</a></p></section>');notes.append('## '+cues['headline']+'\n'+cues['speakerNotes']+'\n\nShots: '+', '.join(cues['shots'])+'\nRun: '+m['runId']+'; outcome: '+m['outcome']+'. Timecodes unavailable unless media exists.\n')
 (dest/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Runspindle demo suite</title><style>body{font:18px system-ui;max-width:1000px;margin:auto;background:#102234;color:white}section{padding:25px;margin:20px;background:#203c50}a{color:#a1f0d5}</style><h1>Teach it a real job. Run it again. Measure the difference.</h1><p>FICTIONAL DEMO · CONCEPTUAL INTERFACE · Fixture measurements only</p>'+''.join(cards));(dest/'cue-sheet.md').write_text('\n'.join(notes));shutil.copytree(ROOT/'docs',dest/'docs',dirs_exist_ok=True)
 with zipfile.ZipFile(ROOT/'artifacts/presentation.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in dest.rglob('*'):
   if p.is_file():z.write(p,p.relative_to(dest))
 print(dest/'index.html')
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['bootstrap','doctor','up','reset','run','record','record-all','assemble','test','verify','resume','fault-matrix']);p.add_argument('case',nargs='?',choices=CASES);p.add_argument('--fault',default='normal');p.add_argument('--run-id');a=p.parse_args()
 if a.command=='bootstrap':subprocess.run(['npm','ci'],cwd=ROOT,check=True);subprocess.run(['npx','playwright','install','chromium'],cwd=ROOT,check=True)
 elif a.command=='doctor':print(json.dumps({'python':sys.version,'node':shutil.which('node'),'git':shutil.which('git'),'submodules':subprocess.run(['git','submodule','status'],cwd=ROOT,capture_output=True,text=True).stdout,'browser':'Run a case to verify actual browser availability'},indent=2))
 elif a.command=='up':serve()
 elif a.command=='reset':reset(a.case,a.fault)
 elif a.command=='resume':sys.exit(0 if run(a.case,resume=a.run_id) else 1)
 elif a.command in ['run','record']:sys.exit(0 if run(a.case,a.fault) else 1)
 elif a.command=='record-all':sys.exit(0 if all([run(c) for c in CASES]) else 1)
 elif a.command=='fault-matrix':
  matrix=[]
  scenarios=[('bookkeeper-deposit','expired'),('vintage-returns','wrong-account'),('bookkeeper-deposit','denied'),('bookkeeper-deposit','missing'),('bakery-prep','crash'),('consultancy-contract','lost-ack'),('consultancy-contract','unresolved'),('consultancy-contract','forbidden'),('bakery-prep','artifact-interruption'),('bakery-prep','ambiguous'),('produce-packing','tenant-expired'),('subcontractor-invoices','tenant-expired'),('bakery-prep','offline'),('bakery-prep','stale')]
  for case,fault in scenarios:
   passed=run(case,fault);manifest_path=max((ROOT/'artifacts').glob('*/manifest.json'),key=lambda p:p.stat().st_mtime);m=json.loads(manifest_path.read_text());worker=json.loads((manifest_path.parent/'worker.json').read_text());first=m['outcome'];resumed=False
   if fault in ['crash','artifact-interruption','offline'] and not passed:
    passed=run(case,resume=m['runId']);resumed=True
   expected_block={'denied':'Access denied','missing':'Missing or ambiguous','forbidden':'Agent assistance forbidden'}
   matched=(not passed and expected_block[fault] in worker.get('reason','') and bool(m['media']['clips'])) if fault in expected_block else passed
   if fault=='unresolved':matched=not passed and m['outcome']=='unknown' and len(load(case)['operations'])==1 and bool(m['media']['clips'])
   matrix.append({'case':case,'fault':fault,'runId':m['runId'],'initialOutcome':first,'resumed':resumed,'verifiedCompletion':passed,'expectedBehaviorVerified':matched})
  (ROOT/'artifacts/fault-matrix.json').write_text(json.dumps(matrix,indent=2));print(json.dumps(matrix,indent=2));sys.exit(0 if all(x['expectedBehaviorVerified'] for x in matrix) else 1)
 elif a.command=='assemble':
  from presentation import assemble as build_presentation
  print(json.dumps(build_presentation(ROOT),indent=2))
 elif a.command=='verify':print(json.dumps(verify(a.case),indent=2))
 elif a.command=='test':subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,check=True)
if __name__=='__main__':main()
