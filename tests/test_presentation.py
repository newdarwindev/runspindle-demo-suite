import json,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from presentation import assemble,safe_file,validate_links,stamp
import evaluate
class PresentationTests(unittest.TestCase):
 def test_blocked_package_is_truthful_and_zip_verified(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);run=root/'artifacts/run-1';run.mkdir(parents=True);(root/'docs').mkdir();(root/'docs/SOURCES.md').write_text('# References\n');(root/'workflows/bakery-prep').mkdir(parents=True);(root/'workflows/bakery-prep/cues.json').write_text(json.dumps({'headline':'Bakery','speakerNotes':'Verify result.'}));(run/'worker.json').write_text(json.dumps({'status':'blocked'}));(run/'manifest.json').write_text(json.dumps({'runId':'run-1','case':'bakery-prep','outcome':'blocked','media':{'clips':[],'screenshots':[]},'evidence':['worker.json'],'checks':{'expected':False}}));(run/'cookies.json').write_text('DO NOT EXPORT')
   result=assemble(root,False);self.assertEqual(result['runs'],1);self.assertTrue(result['missingMedia']);self.assertFalse(result['brokenLinks']);gallery=Path(result['gallery']).read_text();self.assertIn('blocked',gallery);self.assertIn('No actual browser clip',gallery)
   with zipfile.ZipFile(result['archive']) as z:self.assertNotIn('run-1/cookies.json',z.namelist());self.assertIn('checksums.json',z.namelist());self.assertIsNone(z.testzip())
 def test_path_escape_and_private_state_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'cookies.json').write_text('{}')
   with self.assertRaises(ValueError):safe_file(p,'../outside.json')
   with self.assertRaises(ValueError):safe_file(p,'cookies.json')
 def test_timestamps(self):self.assertEqual(stamp(65.25),'00:01:05.250')
 def test_feedback_bound_to_exact_output(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(evaluate,'STATE',Path(tmp)/'state.json'):
   with self.assertRaises(ValueError):evaluate.approve_feedback('wrong','v2','fixture operator')
   revision=evaluate.output_revision(evaluate.compare());result=evaluate.approve_feedback(revision,'v2','fixture operator');self.assertEqual(result['feedback']['outputRevision'],revision);self.assertEqual(result['active'],'v1')
if __name__=='__main__':unittest.main()
