import hashlib,os,json,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from presentation import assemble,safe_file,validate_links,stamp,export_fault_matrix,make_reel,ffmpeg_binary
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
 def test_fault_matrix_export_and_identity_validation(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);art=root/'artifacts';dest=root/'package';art.mkdir();(dest/'run-1').mkdir(parents=True)
   entry={'runId':'run-1','case':'bookkeeper-deposit','outcome':'blocked'}
   (dest/'run-1/manifest.json').write_text(json.dumps({'fault':'denied'}))
   row={'runId':'run-1','case':'bookkeeper-deposit','fault':'denied','initialOutcome':'blocked','resumed':False,'verifiedCompletion':False,'expectedBehaviorVerified':True,'privateExtra':'must not export'}
   (art/'fault-matrix.json').write_text(json.dumps([row]));r=export_fault_matrix(art,dest,[entry]);self.assertEqual(r['status'],'verified');self.assertNotIn('privateExtra',(dest/'fault-matrix.json').read_text());self.assertIn('run-1/manifest.json',(dest/'fault-matrix.md').read_text())
   for changes in [{'runId':'absent'},{'case':'wrong'},{'fault':'missing'},{'verifiedCompletion':True},{'resumed':'false'}]:
    (art/'fault-matrix.json').write_text(json.dumps([{**row,**changes}]))
    with self.assertRaises(ValueError):export_fault_matrix(art,dest,[entry])
 def test_fault_matrix_absence_is_explicit(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);self.assertEqual(export_fault_matrix(root,root,[])['status'],'unavailable')
 def test_portable_reel_failure_is_not_rendered(self):
  from types import SimpleNamespace
  entries=[{'case':'bakery-prep','outcome':'verified','runId':'run-1','media':[{'clip':'page.webm'}]}]
  with tempfile.TemporaryDirectory() as tmp,patch('presentation.shutil.which',return_value='/tool/ffmpeg'),patch('presentation.subprocess.run') as run:
   run.side_effect=[SimpleNamespace(returncode=0)]*3+[SimpleNamespace(returncode=1)]
   result=make_reel(Path(tmp),entries)
   self.assertEqual(result['status'],'failed')
   self.assertIn('WebM',result['reason'])
   self.assertIn('libvpx',run.call_args.args[0])
 def test_portable_reel_records_both_formats(self):
  from types import SimpleNamespace
  entries=[{'case':'bakery-prep','outcome':'verified','runId':'run-1','media':[{'clip':'page.webm'}]}]
  with tempfile.TemporaryDirectory() as tmp,patch('presentation.shutil.which',return_value='/tool/ffmpeg'),patch('presentation.subprocess.run',return_value=SimpleNamespace(returncode=0)),patch('presentation.duration',return_value=3):
   result=make_reel(Path(tmp),entries)
   self.assertEqual(result['status'],'rendered')
   self.assertEqual(result['portablePath'],'combined-reel.webm')
   self.assertEqual(result['path'],'combined-reel.mp4')
 def test_timestamps(self):self.assertEqual(stamp(65.25),'00:01:05.250')
 def test_feedback_bound_to_exact_output(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(evaluate,'STATE',Path(tmp)/'state.json'):
   with self.assertRaises(ValueError):evaluate.approve_feedback('wrong','v2','fixture operator')
   revision=evaluate.output_revision(evaluate.compare());result=evaluate.approve_feedback(revision,'v2','fixture operator');self.assertEqual(result['feedback']['outputRevision'],revision);self.assertEqual(result['active'],'v1')
 def test_portfolio_directory_links_and_source_templates(self):
  from presentation import validate_links
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'docs/portfolio/tools').mkdir(parents=True)
   (root/'docs/SOURCES.md').write_text('# Sources')
   (root/'docs/index.html').write_text('<a href="portfolio/">Portfolio</a>')
   (root/'docs/portfolio/index.html').write_text('<p>Real static page</p>')
   (root/'docs/portfolio/tools/template.html').write_text('<script src="not-rendered.js"></script>')
   (root/'artifacts').mkdir()
   result=assemble(root,False)
   with zipfile.ZipFile(result['archive']) as z:
    self.assertIn('docs/portfolio/index.html',z.namelist())
    self.assertNotIn('docs/portfolio/tools/template.html',z.namelist())
   self.assertFalse(result['brokenLinks'])
   (root/'docs/portfolio/index.html').unlink()
   self.assertIn('index.html: portfolio/',validate_links(root/'docs'))
 def test_task_local_ffmpeg_pin_and_permissions(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'ffmpeg';path.write_bytes(b'encoder');path.chmod(0o700)
   digest=hashlib.sha256(path.read_bytes()).hexdigest()
   with patch.dict(os.environ,{'DEMO_FFMPEG_PATH':str(path),'DEMO_FFMPEG_SHA256':digest}):
    self.assertEqual(ffmpeg_binary(),str(path))
    path.chmod(0o600)
    with self.assertRaisesRegex(ValueError,'not executable'):ffmpeg_binary()
    path.chmod(0o700);path.write_bytes(b'changed')
    with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):ffmpeg_binary()
   for value,pin in [(str(path),''),('relative/path',digest)]:
    with patch.dict(os.environ,{'DEMO_FFMPEG_PATH':value,'DEMO_FFMPEG_SHA256':pin}):
     with self.assertRaises(ValueError):ffmpeg_binary()
   link=Path(tmp)/'link';link.symlink_to(path)
   with patch.dict(os.environ,{'DEMO_FFMPEG_PATH':str(link),'DEMO_FFMPEG_SHA256':digest}):
    with self.assertRaises(ValueError):ffmpeg_binary()
 def test_directory_index_symlink_containment(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);package=root/'package';child=package/'child';child.mkdir(parents=True)
   outside=root/'outside.html';outside.write_text('outside')
   (package/'index.html').write_text('<a href="child/">Child</a>')
   (child/'index.html').symlink_to(outside)
   self.assertIn('index.html: child/',validate_links(package))
   (child/'index.html').unlink();(child/'real.html').write_text('inside')
   (child/'index.html').symlink_to(child/'real.html')
   self.assertEqual(validate_links(package),[])
if __name__=='__main__':unittest.main()
