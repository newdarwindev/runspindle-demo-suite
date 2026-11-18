import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from server import APPS,render_ui
from workspace_ui import WORKSPACES
class WorkspaceTests(unittest.TestCase):
 def test_all_apps_have_distinct_editorial_identity(self):
  self.assertEqual(set(APPS),set(WORKSPACES))
  self.assertEqual(len({v[0] for v in WORKSPACES.values()}),len(APPS))
  for app in APPS:
   content=render_ui(app)
   for marker in ['id="workspace"','id="records-panel"','id="record-filter"','id="record-count"','id="record-empty"','Skip to workspace']:
    self.assertIn(marker,content,app)
   self.assertIn('aria-live',content)
   self.assertIn('prefers-reduced-motion',content)
 def test_filter_is_a_view_not_a_backend_operation(self):
  self.assertNotIn('fetch(',__import__('workspace_ui').JS)
  self.assertIn('row.hidden=',__import__('workspace_ui').JS)
