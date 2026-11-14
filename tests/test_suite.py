import io,json,sys,unittest,types,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from server import Handler,reset,load,fixture,APPS
from demo import verify

def request(case,app,action,data=None,token='',path='/ui',headers=None):
 body=json.dumps({'case':case,'action':action,'data':data or {},'token':token}).encode();h=object.__new__(Handler);h.rfile=io.BytesIO(body);h.headers={'Content-Length':str(len(body)),**(headers or {})};h.path=path;h.server=types.SimpleNamespace(app=app);result=[];h.send=lambda obj,status=200,kind=None:result.append((status,obj));h.do_POST();return result[0]
def signin(case,app,account=None,challenge=False):return request(case,app,'signin',{'account':account or fixture(case)['accounts'][app],'role':'operator','challengeComplete':challenge})[1]
class ContractTests(unittest.TestCase):
 def setUp(self):reset('bookkeeper-deposit');reset('consultancy-contract');reset('bakery-prep')
 def test_all_seven_fixtures_and_fourteen_apps(self):
  self.assertEqual(len(APPS),14)
  for path in (Path(__file__).resolve().parents[1]/'workflows').glob('*/fixtures.json'):
   f=json.loads(path.read_text());self.assertTrue(f['expected']);self.assertTrue(f['accounts']);self.assertTrue((path.parent/'cues.json').exists())
 def test_wrong_account_blocks_read_write(self):
  token=signin('bookkeeper-deposit','mock-bank','other')['token'];self.assertEqual(request('bookkeeper-deposit','mock-bank','read',token=token)[0],403)
 def test_token_not_valid_other_origin(self):
  token=signin('bookkeeper-deposit','mock-bank')['token'];self.assertEqual(request('bookkeeper-deposit','mock-excel','read',token=token)[0],401)
 def test_expired_challenge_handback(self):
  reset('bookkeeper-deposit','expired');v=signin('bookkeeper-deposit','mock-bank');self.assertEqual(v['status'],'challenge');v=signin('bookkeeper-deposit','mock-bank',challenge=True);status,identity=request('bookkeeper-deposit','mock-bank','identity',token=v['token']);self.assertEqual(status,200);self.assertEqual(identity['account'],'ledger-business')
 def test_denied_stays_denied(self):
  reset('bookkeeper-deposit','denied');self.assertEqual(signin('bookkeeper-deposit','mock-bank',challenge=True)['status'],'denied')
 def test_harness_not_unlocked_without_secret(self):
  os.environ.pop('DEMO_HARNESS_KEY',None);self.assertEqual(request('bookkeeper-deposit','mock-bank','observe',path='/harness')[0],403)
 def test_readonly_bank_cannot_submit(self):
  token=signin('bookkeeper-deposit','mock-bank')['token'];self.assertEqual(request('bookkeeper-deposit','mock-bank','submit',{'operationId':'x'},token)[0],403)
 def test_idempotent_deposit_preserves_unrelated(self):
  token=signin('bookkeeper-deposit','mock-excel')['token'];data={'operationId':'deposit-107','result':fixture('bookkeeper-deposit')['expected']}
  for _ in range(2):self.assertEqual(request('bookkeeper-deposit','mock-excel','save-workbook',data,token)[0],200)
  self.assertTrue(verify('bookkeeper-deposit')['passed']);self.assertEqual(load('bookkeeper-deposit')['workbook']['revision'],1)
 def test_missing_reference_not_empty_valid_match(self):
  reset('bookkeeper-deposit','missing');self.assertFalse(any(r['reference']=='invoice-107' for r in load('bookkeeper-deposit')['rows']))
 def test_lost_ack_reconciles_single_submission(self):
  reset('consultancy-contract','lost-ack');board=signin('consultancy-contract','mock-job-board')['token'];request('consultancy-contract','mock-job-board','choose-job',{'role':'operator','listing':'job-5'},board);app=signin('consultancy-contract','mock-applicant-portal')['token'];request('consultancy-contract','mock-applicant-portal','register',{'name':'Fixture','listing':'job-5'},app);token=signin('consultancy-contract','mock-applicant-portal')['token'];data={'operationId':'application-47'}
  status,v=request('consultancy-contract','mock-applicant-portal','submit',data,token);self.assertEqual(status,503);self.assertEqual(v['status'],'unknown');self.assertEqual(request('consultancy-contract','mock-applicant-portal','reconcile',data,token)[1]['status'],'verified');request('consultancy-contract','mock-applicant-portal','submit',data,token);self.assertEqual(len(load('consultancy-contract')['operations']),1)
 def test_unresolved_ack_remains_unknown(self):
  reset('consultancy-contract','unresolved');token=signin('consultancy-contract','mock-applicant-portal')['token'];self.assertEqual(request('consultancy-contract','mock-applicant-portal','reconcile',{'operationId':'x'},token)[1]['status'],'unknown')
 def test_real_fixture_code_change_and_tests(self):
  token=signin('consultancy-contract','mock-code-workspace')['token'];self.assertEqual(request('consultancy-contract','mock-code-workspace','test-code',token=token)[1]['rows'],6);request('consultancy-contract','mock-code-workspace','edit-code',{'code':'def export(jobs):\n    return list(jobs)\n'},token);self.assertTrue(request('consultancy-contract','mock-code-workspace','test-code',token=token)[1]['passed'])
 def test_forbidden_assessment_blocks_agent(self):
  reset('consultancy-contract','forbidden');token=signin('consultancy-contract','mock-coderpad')['token'];self.assertEqual(request('consultancy-contract','mock-coderpad','coderpad',{'code':'sum(status == "open" for status in jobs)'},token)[0],403)
 def test_bakery_pack_fixture(self):
  rows=[r for r in fixture('bakery-prep')['rows'] if r['paid'] and r['date']=='2026-11-15'];self.assertEqual(sum(r['loaves'] for r in rows),3);self.assertEqual(sum(r['rolls'] for r in rows),16)
class EvaluationTests(unittest.TestCase):
 def test_locked_comparison_and_approval(self):
  from evaluate import compare,activate,revision,rollback,STATE
  previous=STATE.read_bytes() if STATE.exists() else None
  try:
   if STATE.exists():STATE.unlink()
   c=compare();self.assertEqual(c['versions']['v2']['failed'],0);self.assertGreater(c['versions']['v1']['failed'],0)
   with self.assertRaises(ValueError):activate('v2','wrong','fixture operator')
   self.assertEqual(activate('v2',revision('v2'),'fixture operator')['active'],'v2')
   self.assertEqual(rollback()['active'],'v1')
  finally:
   if previous is None:STATE.unlink(missing_ok=True)
   else:STATE.write_bytes(previous)

class RecoveryTests(unittest.TestCase):
 def test_tenant_sessions_cannot_cross_scope_or_project(self):
  reset('subcontractor-invoices');data={'account':'electric-company','role':'operator','scope':'GC-North/school'}
  token=request('subcontractor-invoices','mock-vendor-portal','signin',data)[1]['token']
  status,result=request('subcontractor-invoices','mock-vendor-portal','read',{'scope':'GC-North/school'},token)
  self.assertEqual(status,200);self.assertEqual([r['project'] for r in result['rows']],['school'])
  self.assertEqual(request('subcontractor-invoices','mock-vendor-portal','read',{'scope':'GC-South/library'},token)[0],403)
 def test_same_name_worker_is_excluded_at_source(self):
  reset('staffing-billing');scope='A/worker-17/2026-W46';token=request('staffing-billing','mock-timesheet-portal','signin',{'account':'coordinator','role':'operator','scope':scope})[1]['token'];rows=request('staffing-billing','mock-timesheet-portal','read',{'scope':scope},token)[1]['rows'];self.assertEqual(len(rows),1);self.assertEqual(rows[0]['hours'],36)
 def test_bakery_ambiguous_requires_owner_decision(self):
  reset('bakery-prep','ambiguous');token=signin('bakery-prep','mock-counterorders')['token'];self.assertIsNone(load('bakery-prep')['rows'][-1]['date'])
  self.assertEqual(request('bakery-prep','mock-counterorders','decide-pickup',{'date':'2026-11-21'},token)[0],403)
  self.assertEqual(request('bakery-prep','mock-counterorders','decide-pickup',{'date':'2026-11-21','role':'operator'},token)[0],200);self.assertEqual(load('bakery-prep')['rows'][-1]['date'],'2026-11-21')
 def test_exact_artifact_resume_and_tampering(self):
  import tempfile
  from demo import artifact_handoff
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);first=artifact_handoff(p,{'loaves':3,'rolls':16},True);self.assertEqual(first['status'],'interrupted-after-acceptance');self.assertFalse((p/'delivered.csv').exists());accepted=(p/'accepted.csv').read_bytes();second=artifact_handoff(p,{'loaves':999});self.assertTrue(second['storedCopyVerified']);self.assertEqual((p/'delivered.csv').read_bytes(),accepted);self.assertEqual(second['events'],['produced','accepted','delivered']);(p/'accepted.csv').write_text('tampered')
   with self.assertRaises(ValueError):artifact_handoff(p,{'loaves':3})
 def test_scope_controls_render_in_every_app(self):
  from server import render_ui
  ui=render_ui('mock-vendor-portal');self.assertIn('id="scope"',ui);self.assertIn('GC-North/school',ui);self.assertIn('data:{...data,scope:',ui)
 def test_checkpoint_scope_readback(self):
  from server import scoped_rows
  reset('subcontractor-invoices');s=load('subcontractor-invoices');self.assertEqual(len(scoped_rows('subcontractor-invoices','GC-North/school',s['rows'])),1)
  with self.assertRaises(ValueError):scoped_rows('subcontractor-invoices','GC-North/other',s['rows'])



class RichWorkflowTests(unittest.TestCase):
 def test_workbook_cells_csv_totals_revisions_preserve_notes(self):
  reset('bakery-prep');token=signin('bakery-prep','mock-excel')['token'];request('bakery-prep','mock-excel','save-workbook',{'result':{'loaves':3,'rolls':16},'operationId':'one'},token)
  request('bakery-prep','mock-excel','edit-cell',{'sheet':'Results','table':'ResultsTable','key':'loaves','value':'4'},token)
  w=load('bakery-prep')['workbook'];self.assertEqual(w['sheets']['Results']['totals']['loaves'],4);self.assertEqual(len(w['history']),2);self.assertEqual(w['history'][0]['sheets']['Results']['totals']['loaves'],3)
  exported=request('bakery-prep','mock-excel','export-csv',token=token)[1]['csv'];self.assertIn('loaves,4',exported);request('bakery-prep','mock-excel','import-csv',{'csv':exported.replace('loaves,4','loaves,3')},token);self.assertTrue(verify('bakery-prep')['passed']);self.assertEqual(load('bakery-prep')['workbook']['sheets']['Notes']['cells']['B1'],'=SUM(A1:A3)')
  self.assertEqual(request('bakery-prep','mock-excel','edit-cell',{'sheet':'Notes','table':'ResultsTable','key':'loaves','value':'0'},token)[0],403)
 def test_registration_needs_owner_listing(self):
  reset('consultancy-contract');app=signin('consultancy-contract','mock-applicant-portal')['token'];self.assertEqual(request('consultancy-contract','mock-applicant-portal','register',{'name':'Fixture','listing':'job-5'},app)[0],409)
  board=signin('consultancy-contract','mock-job-board')['token'];request('consultancy-contract','mock-job-board','choose-job',{'role':'operator','listing':'job-5'},board);self.assertEqual(request('consultancy-contract','mock-applicant-portal','register',{'name':'Fixture','listing':'job-5'},app)[0],200)
 def test_assessment_requires_exact_revision_review(self):
  reset('consultancy-contract');token=signin('consultancy-contract','mock-coderpad')['token'];code='sum(status == "open" for status in jobs)';request('consultancy-contract','mock-coderpad','coderpad',{'code':code},token)
  self.assertEqual(request('consultancy-contract','mock-coderpad','submit-assessment',{'code':code},token)[0],409);request('consultancy-contract','mock-coderpad','review-assessment',{'code':code,'role':'operator'},token);self.assertEqual(request('consultancy-contract','mock-coderpad','submit-assessment',{'code':code+' '},token)[0],409);self.assertTrue(request('consultancy-contract','mock-coderpad','submit-assessment',{'code':code},token)[1]['submitted'])
 def test_source_links_saved_with_invoice_status(self):
  reset('subcontractor-invoices');token=signin('subcontractor-invoices','mock-excel')['token'];links={'C-104':'http://localhost:4310/?record=C-104','C-112':'http://localhost:4310/?record=C-112'};request('subcontractor-invoices','mock-excel','save-workbook',{'result':fixture('subcontractor-invoices')['expected'],'sourceLinks':links,'operationId':'invoices'},token);self.assertEqual(load('subcontractor-invoices')['workbook']['rows'][0]['sourceLinks'],links)

if __name__=='__main__':unittest.main()
