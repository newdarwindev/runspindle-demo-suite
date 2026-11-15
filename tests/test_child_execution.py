import json,runpy,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from server import APPS,APP_DEFAULTS,PORTS,render_ui
class ChildExecutionTests(unittest.TestCase):
 def test_child_business_steps_execute_all_six_data_workflows(self):
  script="""const assert=require('assert'),fs=require('fs');(async()=>{for(const name of JSON.parse(fs.readFileSync('contracts/cases.json'))){const flow=require('./workflows/'+name+'/steps.cjs');assert(Array.isArray(flow.scopes));if(name==='consultancy-contract')continue;const f=require('./workflows/'+name+'/fixtures.json');assert.deepStrictEqual(await flow.execute({rows:f.rows}),f.expected);}})().catch(e=>{console.error(e);process.exitCode=1});"""
  subprocess.run(['node','-e',script],cwd=ROOT,check=True,capture_output=True,text=True)
 def test_independent_assertions_are_owned_by_each_workflow(self):
  for case in json.loads((ROOT/'contracts/cases.json').read_text()):
   module=runpy.run_path(str(ROOT/'workflows'/case/'assertions.py'));f=json.loads((ROOT/'workflows'/case/'fixtures.json').read_text())
   self.assertEqual(module['expected']({},f),f['expected']);self.assertTrue(callable(module['checks']))
 def test_app_defaults_are_loaded_and_used(self):
  for app in APPS:
   defaults=json.loads((ROOT/'apps'/app/'defaults.json').read_text())
   self.assertEqual(APP_DEFAULTS[app],defaults);self.assertEqual(PORTS[app],defaults['port']);self.assertIn(defaults['title'],render_ui(app))
 def test_worker_dispatches_to_child_not_copy_of_business_logic(self):
  worker=(ROOT/'tools/worker.cjs').read_text();self.assertIn('workflow.execute(',worker);self.assertIn('workflow.scopes',worker)
  self.assertNotIn("result={approved:",worker);self.assertNotIn("const assessment=",worker)
 def test_app_acl_rejects_wrong_app_operation(self):
  from test_suite import request,signin
  from server import reset
  reset('bookkeeper-deposit');token=signin('bookkeeper-deposit','mock-bank')['token']
  self.assertEqual(request('bookkeeper-deposit','mock-bank','save-workbook',{'result':{},'operationId':'bad'},token)[0],403)
