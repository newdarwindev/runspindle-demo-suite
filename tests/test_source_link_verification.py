import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import demo
from server import workbook_commit
class SourceLinkVerificationTests(unittest.TestCase):
 def test_wrong_project_or_missing_source_link_fails(self):
  from test_independent_evidence import IndependentEvidenceTests
  state=IndependentEvidenceTests().state();case='subcontractor-invoices';state['case']=case
  state['workbook']['rows']=[];state['workbook']['history']=[];state['workbook']['revision']=0
  expected=demo.fixture(case)['expected'];links={k:f'http://localhost:4310/?case={case}&scope={scope}&record={k}' for k,scope in [('C-104','GC-North%2Fschool'),('C-112','GC-South%2Flibrary')]}
  workbook_commit(state,case,expected,links);state['lastResult']=expected
  with patch.object(demo,'load',return_value=state):self.assertTrue(demo.verify(case)['passed'])
  for bad in ['',links['C-104'].replace('school','other')]:
   changed=copy.deepcopy(state);changed['workbook']['rows'][0]['sourceLinks']['C-104']=bad
   with patch.object(demo,'load',return_value=changed):self.assertFalse(demo.verify(case)['checks']['invoice_source_links'])
  state['workbook']['sheets']['Results']['tables']['ResultsTable'][0]['source']=''
  with patch.object(demo,'load',return_value=state):self.assertFalse(demo.verify(case)['checks']['invoice_source_links'])

class BakeryDecisionVerificationTests(unittest.TestCase):
 def test_explicit_tomorrow_choice_changes_expected_count(self):
  from test_independent_evidence import IndependentEvidenceTests
  state=IndependentEvidenceTests().state();state['fault']='ambiguous';state['decisions']=[{'order':'223','date':'2026-11-15'}]
  result={'loaves':4,'rolls':16};workbook_commit(state,'bakery-prep',result);state['lastResult']=result
  with patch.object(demo,'load',return_value=state):self.assertTrue(demo.verify('bakery-prep')['passed'])
  state['decisions']=[]
  with patch.object(demo,'load',return_value=state):self.assertFalse(demo.verify('bakery-prep')['passed'])
