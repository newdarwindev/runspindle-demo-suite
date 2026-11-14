"""Locked fixture comparison and explicit operator-approved activation / rollback."""
import argparse,hashlib,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'.state/evaluation.json'
VERSIONS={'v1':"case['packs']",'v2':"'blocked' if case.get('note') else case['packs'] * case['size']"}
DATA=[{'family':'packs','partition':'held-out','packs':2,'size':6,'expected':12},{'family':'packs','partition':'held-out','packs':3,'size':4,'expected':12},{'family':'ambiguous','partition':'held-out','packs':1,'size':6,'note':'Saturday instead?','expected':'blocked'}]
def revision(version):return hashlib.sha256(VERSIONS[version].encode()).hexdigest()
def compare():
 result={'dataPartition':'held-out','relatedExamplesGrouped':True,'fixtureMeasurements':True,'competitiveSavings':'untested hypothesis','datasetRevision':hashlib.sha256(json.dumps(DATA,sort_keys=True).encode()).hexdigest(),'versions':{}}
 for version in VERSIONS:
  rows=[]
  for case in DATA:
   actual=eval(compile(VERSIONS[version],'<locked-fixture-'+version+'>','eval'),{'__builtins__':{}},{'case':case});rows.append({'family':case['family'],'expected':case['expected'],'actual':actual,'passed':actual==case['expected']})
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
def output_revision(comparison):
 return hashlib.sha256(json.dumps(comparison,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def approve_feedback(output,version,operator):
 expected=output_revision(compare())
 if output!=expected or not operator:raise ValueError('Feedback approval must bind exact comparison output')
 s=state();s['feedback']={'outputRevision':output,'candidateRevision':revision(version),'operator':operator,'approvedAt':time.time(),'text':'Handle pack sizes explicitly and ask owner about ambiguous pickup notes.'};STATE.parent.mkdir(exist_ok=True);STATE.write_text(json.dumps(s,indent=2));return s

def serve(port=4320):
 from http.server import BaseHTTPRequestHandler,HTTPServer
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def send(self,obj,status=200,content_type='application/json'):
   b=(json.dumps(obj) if content_type=='application/json' else obj).encode();self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  def do_GET(self):
   if self.path=='/health':return self.send({'fixture':'bakery-evaluation'})
   data=compare();output=output_revision(data)
   page=EVALUATION_HTML.replace('__COMPARISON__',json.dumps(data)).replace('__OUTPUT_REVISION__',output)
   return self.send(page,content_type='text/html')
  def do_POST(self):
   try:
    body=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))));action=body['action']
    if action=='compare':result={'comparison':compare(),'outputRevision':output_revision(compare()),'state':state()}
    elif action=='feedback':result=approve_feedback(body['outputRevision'],'v2',body['operator'])
    elif action=='activate':
     s=state()
     if s.get('feedback',{}).get('outputRevision')!=output_revision(compare()):raise ValueError('Approve feedback for this output first')
     result=activate('v2',body['approvedRevision'],body['operator'])
    elif action=='rollback':result=rollback()
    else:raise ValueError('Unsupported action')
    return self.send(result)
   except (KeyError,ValueError) as e:return self.send({'error':str(e)},400)
 HTTPServer(('127.0.0.1',port),Handler).serve_forever()

EVALUATION_HTML=r"""<!doctype html><html lang="en"><meta charset="utf-8"><title>Bakery evaluation fixture</title><style>body{font:20px system-ui;background:#102234;color:#eef7ff;padding:35px;max-width:1150px;margin:auto}button,input{font:inherit;padding:12px;margin:8px}input{width:90%;font:15px monospace}section{background:#203c50;padding:20px;border-radius:16px;margin:20px 0}pre{white-space:pre-wrap;font-size:15px}.badge{color:#a1f0d5}</style><p class="badge">FICTIONAL DEMO · CONCEPTUAL INTERFACE · SCRIPTED FIXTURE OPERATOR</p><h1>Measure the change before approving it.</h1><p>Same held-out examples. Related pack examples remain in one partition. No customer data or production workflow is changed.</p><button id="compare">Compare locked v1 and v2</button><section><h2>Independent fixture comparison</h2><pre id="comparison"></pre></section><section><h2>Approve feedback for this exact output</h2><label>Comparison output revision<input id="output" value="__OUTPUT_REVISION__"></label><button id="feedback">Fixture operator approves feedback</button><h2>Explicit candidate approval</h2><label>Approved candidate revision<input id="revision" placeholder="Paste the exact v2 revision from the comparison"></label><button id="activate">Fixture operator approves activation</button><button id="rollback">Roll back to prior version</button></section><section><h2>Active version and evidence</h2><pre id="state">Active: v1. No candidate approved.</pre></section><p>Fixture counts and timings only. Savings versus supported ChatGPT Work, Claude Cowork, connectors, imports or manual processes are an untested hypothesis. Future cost includes setup, maintenance, review and recovery per verified completion.</p><script>const $=x=>document.getElementById(x);const comparison=__COMPARISON__;async function action(kind,data={}){const r=await fetch('/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:kind,...data})});const v=await r.json();$('state').textContent=JSON.stringify(v,null,2);if(kind==='compare')$('comparison').textContent=JSON.stringify(v.comparison,null,2);return v}$('compare').onclick=()=>action('compare');$('feedback').onclick=()=>action('feedback',{outputRevision:$('output').value,operator:'scripted fixture operator'});$('activate').onclick=()=>action('activate',{approvedRevision:$('revision').value,operator:'scripted fixture operator'});$('rollback').onclick=()=>action('rollback');</script></html>"""

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['compare','activate','rollback','status','serve']);p.add_argument('--version',choices=VERSIONS);p.add_argument('--approved-revision');p.add_argument('--operator');p.add_argument('--state-file',type=Path);p.add_argument('--port',type=int,default=4320);a=p.parse_args()
 if a.state_file:STATE=a.state_file
 if a.action=='serve':serve(a.port)
 else:
  result=compare() if a.action=='compare' else activate(a.version,a.approved_revision,a.operator) if a.action=='activate' else rollback() if a.action=='rollback' else state();print(json.dumps(result,indent=2))
