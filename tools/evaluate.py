"""Locked fixture comparison and explicit operator-approved activation / rollback."""
import argparse,hashlib,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'.state/evaluation.json'
VERSIONS={'v1':'packs-are-items; ambiguous-counts-tomorrow','v2':'packs-times-size; ambiguous-requires-owner'}
DATA=[{'family':'packs','partition':'held-out','packs':2,'size':6,'expected':12},{'family':'packs','partition':'held-out','packs':3,'size':4,'expected':12},{'family':'ambiguous','partition':'held-out','packs':1,'size':6,'note':'Saturday instead?','expected':'blocked'}]
def revision(version):return hashlib.sha256(VERSIONS[version].encode()).hexdigest()
def compare():
 result={'dataPartition':'held-out','relatedExamplesGrouped':True,'fixtureMeasurements':True,'competitiveSavings':'untested hypothesis','versions':{}}
 for version in VERSIONS:
  rows=[]
  for case in DATA:
   actual=('blocked' if case.get('note') else case['packs']*case['size']) if version=='v2' else case['packs'];rows.append({'family':case['family'],'expected':case['expected'],'actual':actual,'passed':actual==case['expected']})
  result['versions'][version]={'revision':revision(version),'cases':rows,'verifiedCompletions':sum(r['passed'] and r['actual']!='blocked' for r in rows),'blocked':sum(r['actual']=='blocked' for r in rows),'failed':sum(not r['passed'] for r in rows),'elapsedSeconds':None,'operatorMinutes':None}
 return result
def state():return json.loads(STATE.read_text()) if STATE.exists() else {'active':'v1','previous':None,'approvals':[]}
def activate(version,approved_revision,operator):
 if not operator or approved_revision!=revision(version):raise ValueError('Explicit operator approval bound to exact revision required')
 s=state();s['previous']=s['active'];s['active']=version;s['approvals'].append({'version':version,'revision':approved_revision,'operator':operator,'approvedAt':time.time()});STATE.parent.mkdir(exist_ok=True);STATE.write_text(json.dumps(s,indent=2));return s
def rollback():
 s=state()
 if not s['previous']:raise ValueError('No prior active version')
 s['active'],s['previous']=s['previous'],s['active'];STATE.write_text(json.dumps(s,indent=2));return s
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['compare','activate','rollback','status']);p.add_argument('--version',choices=VERSIONS);p.add_argument('--approved-revision');p.add_argument('--operator');a=p.parse_args();result=compare() if a.action=='compare' else activate(a.version,a.approved_revision,a.operator) if a.action=='activate' else rollback() if a.action=='rollback' else state();print(json.dumps(result,indent=2))
