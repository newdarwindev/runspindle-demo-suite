"""Regression tests against a cached-result false positive and cross-run resume."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import demo

class IndependentEvidenceTests(unittest.TestCase):
 def state(self):
  result={'loaves':3,'rolls':16}
  sheets={'Results':{'tables':{'ResultsTable':[{'key':k,'value':v,'source':''} for k,v in result.items()],'UnrelatedTable':copy.deepcopy(demo.UNRELATED_ROWS)},'totals':dict(result)},'Notes':{'cells':{'A1':'Do not change','B1':'=SUM(A1:A3)'},'tables':{}}}
  return {'case':'bakery-prep','runId':'run-A','lastResult':result,'workbook':{'rows':[{'case':'bakery-prep','result':dict(result)}],'unrelated':{'ownerNote':'Do not change','formula':'=SUM(A1:A3)'},'sheets':sheets,'revision':1,'history':[{'revision':1,'sheets':copy.deepcopy(sheets)}]}}
 def verdict(self,state):
  with patch.object(demo,'load',return_value=state):return demo.verify('bakery-prep')
 def test_actual_cells_are_verified_not_cached_result(self):
  s=self.state();self.assertTrue(self.verdict(s)['passed']);s['workbook']['sheets']['Results']['tables']['ResultsTable'][0]['value']=999
  self.assertFalse(self.verdict(s)['passed']);self.assertFalse(self.verdict(s)['checks']['actual_table_cells'])
 def test_actual_saved_row_corruption_fails(self):
  s=self.state();s['workbook']['rows'][0]['result']['rolls']=999;self.assertFalse(self.verdict(s)['checks']['actual_workbook_row'])
 def test_actual_totals_corruption_fails(self):
  s=self.state();s['workbook']['sheets']['Results']['totals']['rolls']=999;self.assertFalse(self.verdict(s)['checks']['actual_table_totals'])
 def test_notes_formula_corruption_fails_even_with_untouched_sentinel(self):
  s=self.state();s['workbook']['sheets']['Notes']['cells']['B1']='removed';self.assertFalse(self.verdict(s)['checks']['unrelated_preserved'])
 def test_history_corruption_or_revision_drift_fails(self):
  s=self.state();s['workbook']['history'][0]['sheets']['Notes']['cells']['A1']='corrupted';self.assertFalse(self.verdict(s)['checks']['historical_notes_preserved']);self.assertFalse(self.verdict(s)['checks']['saved_revision_matches'])
 def test_duplicate_table_keys_fail(self):
  s=self.state();s['workbook']['sheets']['Results']['tables']['ResultsTable'].append({'key':'loaves','value':3});self.assertFalse(self.verdict(s)['checks']['actual_table_cells'])
 def test_interleaved_same_case_run_rejects_old_resume(self):
  checkpoint={'case':'bakery-prep','runId':'run-A'};state=self.state();demo.validate_resume_ownership(checkpoint,state,'bakery-prep','run-A');state['runId']='run-B'
  with self.assertRaisesRegex(ValueError,'replaced by another run'):demo.validate_resume_ownership(checkpoint,state,'bakery-prep','run-A')
 def test_resume_requires_task_and_run_match(self):
  with self.assertRaises(ValueError):demo.validate_resume_ownership({'case':'bakery-prep','runId':'other'},self.state(),'bakery-prep','run-A')
class AuditRegressionTests(unittest.TestCase):
 def test_original_provenance_and_start_survive_new_attempt(self):
  cp={'attempts':1};one={'parentCommit':'aaa','childCommits':{'app':'111'}};two={'parentCommit':'bbb','childCommits':{'app':'222'}}
  demo.record_attempt_start(cp,one,100);cp['attempts']=2;demo.record_attempt_start(cp,two,200)
  self.assertEqual(cp['startedAt'],100);self.assertEqual(cp['provenance'],one);self.assertEqual(cp['attemptHistory'][1]['parentCommit'],'bbb')
 def test_artifact_destination_is_real_readback_file(self):
  import tempfile
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp);(out/'workbook-export.csv').write_bytes(b'key,value\nloaves,3\nrolls,16\n');meta=demo.artifact_handoff(out,{'loaves':3,'rolls':16})
   self.assertEqual(meta['destination'],'delivered.csv');self.assertTrue(meta['destinationVerified']);self.assertEqual((out/meta['destination']).read_bytes(),(out/'accepted.csv').read_bytes())
 def test_bank_reference_scope_never_returns_other_deposit(self):
  from test_suite import request,signin
  from server import reset
  reset('bookkeeper-deposit');token=signin('bookkeeper-deposit','mock-bank')['token']
  status,response=request('bookkeeper-deposit','mock-bank','read',token=token);self.assertEqual(status,200);self.assertEqual([r['id'] for r in response['rows']],['deposit-107'])
  self.assertEqual(request('bookkeeper-deposit','mock-bank','read',{'scope':'invoice-108'},token)[0],403)
  reset('bookkeeper-deposit','missing');token=signin('bookkeeper-deposit','mock-bank')['token'];self.assertEqual(request('bookkeeper-deposit','mock-bank','read',token=token)[1]['rows'],[])
 def test_actual_fixture_repository_changes_and_runs_tests(self):
  from test_suite import request,signin
  from server import reset,load,code_repository,git_fixture
  reset('consultancy-contract');token=signin('consultancy-contract','mock-code-workspace')['token'];repo=code_repository(load('consultancy-contract'));self.assertTrue((repo/'.git').is_dir());self.assertIn('test_selected_month_includes_completed',(repo/'test_exporter.py').read_text())
  original=request('consultancy-contract','mock-code-workspace','test-code',token=token)[1];self.assertEqual(original['rows'],6);self.assertFalse(original['passed'])
  request('consultancy-contract','mock-code-workspace','edit-code',{'code':'def export(jobs):\n    return list(jobs)\n'},token)
  self.assertEqual((repo/'exporter.py').read_text(),'def export(jobs):\n    return list(jobs)\n');self.assertTrue(request('consultancy-contract','mock-code-workspace','test-code',token=token)[1]['passed'])
  self.assertEqual(load('consultancy-contract')['testEvidence']['testCount'],2)
  request('consultancy-contract','mock-code-workspace','open-pr',{'operationId':'pr-audit'},token);pr=load('consultancy-contract')['pr'];self.assertNotEqual(pr['baseCommit'],pr['headCommit']);self.assertEqual(pr['headCommit'],git_fixture(repo,'rev-parse','HEAD'))
  request('consultancy-contract','mock-code-workspace','edit-code',{'code':'def export(jobs):\n    return [j for j in jobs if j["status"] == "open"]\n'},token)
  self.assertEqual(request('consultancy-contract','mock-code-workspace','open-pr',{'operationId':'stale-test-pr'},token)[0],409)
 def test_stale_observation_is_explicit_then_refreshed(self):
  from test_suite import request,signin
  from server import reset,freshness
  self.assertEqual(freshness(100,401)['status'],'stale');self.assertEqual(freshness(100,101)['status'],'verified')
  reset('bakery-prep','stale');token=signin('bakery-prep','mock-counterorders')['token'];self.assertEqual(request('bakery-prep','mock-counterorders','read',token=token)[1]['status'],'stale');self.assertEqual(request('bakery-prep','mock-counterorders','observation-status',token=token)[1]['status'],'stale');self.assertEqual(request('bakery-prep','mock-counterorders','read',token=token)[1]['status'],'verified')
 def test_unrelated_table_corruption_is_detected(self):
  s=IndependentEvidenceTests().state();s['workbook']['sheets']['Results']['tables']['UnrelatedTable'][0]['amount']=999
  with patch.object(demo,'load',return_value=s):self.assertFalse(demo.verify('bakery-prep')['checks']['unrelated_table_rows_preserved'])
if __name__=='__main__':unittest.main()
