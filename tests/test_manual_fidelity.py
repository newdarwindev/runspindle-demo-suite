import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from server import reset,load,render_ui
from test_suite import request,signin
class ManualFidelityTests(unittest.TestCase):
 def call(self,app,action,data=None):
  return request('consultancy-contract',app,action,data,signin('consultancy-contract',app)['token'])
 def test_application_requires_draft_and_written_screening(self):
  reset('consultancy-contract')
  self.call('mock-job-board','choose-job',{'role':'operator','listing':'job-5'})
  self.call('mock-applicant-portal','register',{'name':'Demo','listing':'job-5'})
  self.assertEqual(self.call('mock-applicant-portal','submit',{'operationId':'app'})[0],409)
  self.call('mock-applicant-portal','application-draft',{'answer':'Five hours weekly'})
  self.assertEqual(self.call('mock-applicant-portal','submit',{'operationId':'app'})[0],200)
  self.assertEqual(self.call('mock-applicant-portal','advance',{'role':'operator'})[0],409)
  self.call('mock-applicant-portal','written-screening')
  self.assertEqual(self.call('mock-applicant-portal','advance',{'role':'operator'})[1]['round'],1)
  self.assertEqual(self.call('mock-applicant-portal','advance',{'role':'operator'})[0],409)
  self.assertEqual(self.call('mock-interview-room','advance',{'role':'operator'})[1]['round'],2)
 def test_owner_can_choose_each_pickup_day(self):
  for day in ['2026-11-15','2026-11-21']:
   reset('bakery-prep','ambiguous');token=signin('bakery-prep','mock-counterorders')['token']
   status,_=request('bakery-prep','mock-counterorders','decide-pickup',{'role':'operator','date':day},token)
   self.assertEqual(status,200);self.assertEqual(load('bakery-prep')['rows'][-1]['date'],day)
  page=render_ui('mock-counterorders');self.assertIn('id="pickup-date"',page);self.assertIn("date:$('pickup-date').value",page)
 def test_record_links_scope_read(self):
  reset('subcontractor-invoices');data={'account':'electric-company','role':'operator','scope':'GC-North/school'}
  token=request('subcontractor-invoices','mock-vendor-portal','signin',data)[1]['token']
  r=request('subcontractor-invoices','mock-vendor-portal','read',{'scope':'GC-North/school','record':'C-104'},token)[1]
  self.assertEqual([x['id'] for x in r['rows']],['C-104'])
  r=request('subcontractor-invoices','mock-vendor-portal','read',{'scope':'GC-North/school','record':'C-112'},token)[1]
  self.assertEqual(r['rows'],[])
 def test_manual_and_scripted_actor_labels_are_distinct(self):
  reset('consultancy-contract')
  for fixture_operator,expected in [(True,'fixture operator'),(False,'human operator')]:
   request('consultancy-contract','mock-mail','signin',{'account':'consultant','role':'operator','fixtureOperator':fixture_operator})
   self.assertEqual(load('consultancy-contract')['events'][-1]['actor'],expected)
  self.assertIn("get('operator')!=='manual'",render_ui('mock-mail'))
 def test_operator_adapter_waits_without_clicking_in_manual_mode(self):
  import subprocess
  script=r"""
const assert=require('assert');const {createOperator}=require('./tools/fixture-operator.cjs');
(async()=>{for(const mode of ['manual','scripted']){let clicks=0,events=[];const page={url:()=> 'http://localhost:4300',waitForResponse:async()=>({json:async()=>({status:'signed-in'})}),locator:()=>({click:async()=>{clicks++}})};const op=createOperator(mode,(kind,v)=>events.push({kind,...v}));await op.perform(page,'signin');assert.equal(clicks,mode==='manual'?0:1);assert.equal(events.at(-1).actor,mode==='manual'?'human operator':'fixture operator');assert(events.at(-1).durationMilliseconds>=0);await assert.rejects(()=>op.perform(page,'save'));}})().catch(e=>{console.error(e);process.exitCode=1});
"""
  subprocess.run(['node','-e',script],cwd=Path(__file__).resolve().parents[1],check=True,capture_output=True,text=True)
