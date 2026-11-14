#!/usr/bin/env python3
"""Orchestrator and independent observer: worker never receives harness/state capabilities."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time,uuid,zipfile,html
from pathlib import Path
from server import ROOT,APPS,fixture,load,reset,serve,scoped_rows
CASES=json.loads((ROOT/'contracts/cases.json').read_text())
def sha(path):
 if not (path/'.git').exists():return None
 p=subprocess.run(['git','-C',str(path),'rev-parse','HEAD'],capture_output=True,text=True);return p.stdout.strip() if p.returncode==0 else None
def verify(case):
 s=load(case);f=fixture(case);checks={'expected_result':s['lastResult']==f['expected'],'unrelated_preserved':s['workbook']['unrelated']=={'ownerNote':'Do not change','formula':'=SUM(A1:A3)'},'single_case_row':len([r for r in s['workbook']['rows'] if r['case']==case])==1}
 if case=='consultancy-contract':checks.update(code_tests=s['tests']=={'rows':10,'expected':10,'passed':True},issue=s['issueStatus']=='Ready for review',one_comment=len(s['comments'])==1,hired=s['application']=='Hired',pr=s['pr'] is not None)
 return {'checks':checks,'passed':all(checks.values()),'observedAt':time.time(),'observer':'independent server persisted-state readback','result':s['lastResult']}
def artifact_handoff(out,result,interrupt=False):
 meta_path=out/'artifact.json'
 if meta_path.exists():
  meta=json.loads(meta_path.read_text());b=(out/'accepted.csv').read_bytes()
  if hashlib.sha256(b).hexdigest()!=meta['sha256']:raise ValueError('Accepted artifact changed; delivery blocked')
 else:
  b=('item,quantity\n'+''.join(f'{k},{result[k]}\n' for k in sorted(result))).encode();(out/'produced.csv').write_bytes(b)
  meta={'producedAt':time.time(),'acceptedAt':time.time(),'acceptedBy':'fixture operator','sha256':hashlib.sha256(b).hexdigest(),'destination':'presentation/accepted.csv','events':['produced','accepted']};(out/'accepted.csv').write_bytes(b);meta_path.write_text(json.dumps(meta,indent=2))
  if interrupt:return {**meta,'status':'interrupted-after-acceptance'}
 (out/'delivered.csv').write_bytes(b);meta.update(deliveredAt=time.time(),storedCopyVerified=(out/'delivered.csv').read_bytes()==b,status='verified');meta['events'].append('delivered');meta_path.write_text(json.dumps(meta,indent=2));return meta

def run(case,fault='normal',resume=None):
 if resume:
  if Path(resume).name!=resume:raise ValueError('Invalid run ID')
  runid=resume;out=ROOT/'artifacts'/runid;checkpoint=json.loads((out/'checkpoint.json').read_text())
  if checkpoint['case']!=case:raise ValueError('Checkpoint case mismatch')
  fault=checkpoint['fault'];checkpoint['attempts']+=1
 else:
  runid=f'{case}-{uuid.uuid4().hex[:12]}';out=ROOT/'artifacts'/runid;out.mkdir(parents=True);reset(case,fault)
  checkpoint={'runId':runid,'case':case,'fault':fault,'attempts':1,'app':fixture(case)['source'],'account':fixture(case)['accounts'][fixture(case)['source']],'record':None,'lastIndependentResult':None,'status':'started'}
 start=time.time();(out/'checkpoint.json').write_text(json.dumps(checkpoint,indent=2))
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
  p=subprocess.run(['node',str(ROOT/'tools/worker.cjs'),case,str(out),fault],cwd=ROOT,capture_output=True,text=True)
  if not (out/'worker.json').exists():(out/'worker.json').write_text(json.dumps({'status':'blocked','reason':p.stderr[-2500:]}))
 worker=json.loads((out/'worker.json').read_text());verdict=verify(case)
 progress_path=out/'worker-checkpoint.json'
 if progress_path.exists():
  progress=json.loads(progress_path.read_text());source=load(case);observations=progress.get('completedScopes',{});valid=all(rows==scoped_rows(case,scope,source['rows']) for scope,rows in observations.items());progress['sourceIndependentVerified']=valid;progress_path.write_text(json.dumps(progress,indent=2));verdict['checks']['checkpoint_source_readback']=valid;verdict['passed']=verdict['passed'] and valid;checkpoint['record']=progress.get('recordIds');checkpoint['lastIndependentSourceResult']={'verified':valid,'scopes':list(observations)}
 (out/'verification.json').write_text(json.dumps(verdict,indent=2));checkpoint.update(status='verified' if verdict['passed'] else checkpoint.get('status','blocked'),lastIndependentResult=verdict)
 if case=='bakery-prep' and verdict['passed']:
  artifact=artifact_handoff(out,verdict['result'],fault=='artifact-interruption' and not resume)
  if artifact['status']!='verified':worker={'status':'blocked','reason':'Accepted bytes preserved. Resume run to deliver exact artifact.'};verdict['passed']=False;checkpoint['status']='accepted-awaiting-delivery'
 (out/'checkpoint.json').write_text(json.dumps(checkpoint,indent=2))
 manifest={'runId':runid,'case':case,'fault':fault,'seed':107,'parentCommit':sha(ROOT),'childCommits':{str(p.relative_to(ROOT)):sha(p) for top in ['apps','workflows'] for p in (ROOT/top).iterdir() if p.is_dir()},'adapter':'deterministic-browser-fixture','executionMode':'fixture','upstreamExecuted':False,'outcome':'verified' if verdict['passed'] else worker['status'],'startedAt':start,'finishedAt':time.time(),'metrics':{'verifiedCompletions':int(verdict['passed']),'elapsedSeconds':time.time()-start,'operatorMinutes':None,'operatorTimingNote':'Not instrumented; do not interpret as zero.'},'checks':verdict['checks'],'media':{'clips':[p.name for p in out.glob('*.webm')],'screenshots':[p.name for p in out.glob('*.png')]},'evidence':['verification.json','worker.json','checkpoint.json'],'limitations':['Fixture only; upstream Runspindle does not execute.','Comparative staff-time savings untested.']}
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
  for case,fault in [('bookkeeper-deposit','expired'),('vintage-returns','wrong-account'),('bookkeeper-deposit','denied'),('bookkeeper-deposit','missing'),('bakery-prep','crash'),('consultancy-contract','lost-ack'),('consultancy-contract','forbidden'),('bakery-prep','artifact-interruption'),('bakery-prep','ambiguous'),('produce-packing','tenant-expired'),('subcontractor-invoices','tenant-expired'),('bakery-prep','offline')]:
   passed=run(case,fault);matrix.append({'case':case,'fault':fault,'verifiedCompletion':passed})
  (ROOT/'artifacts/fault-matrix.json').write_text(json.dumps(matrix,indent=2));print(json.dumps(matrix,indent=2))
 elif a.command=='assemble':assemble()
 elif a.command=='verify':print(json.dumps(verify(a.case),indent=2))
 elif a.command=='test':subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,check=True)
if __name__=='__main__':main()
