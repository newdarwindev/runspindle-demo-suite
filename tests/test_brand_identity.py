"""Milestone 6: child-owned identities, not a shared recolored placeholder."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPS = json.loads((ROOT / 'contracts/apps.json').read_text())

def luminance(value):
    channels = [int(value[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
    return sum(a*b for a, b in zip(linear, (.2126, .7152, .0722)))

def contrast(a, b):
    a, b = sorted((luminance(a), luminance(b)))
    return (b + .05) / (a + .05)

class BrandIdentityTests(unittest.TestCase):
    def test_every_app_owns_a_complete_distinct_identity(self):
        identities = []
        for app in APPS:
            brand = json.loads((ROOT / 'apps' / app / 'brand.json').read_text())
            self.assertEqual(brand['id'], app)
            for field in ('name', 'mark', 'tagline', 'style', 'typography', 'colors'):
                self.assertTrue(brand[field])
            identities.append(brand)
        for field in ('name', 'mark', 'tagline', 'style', 'colors', 'typography'):
            self.assertEqual(len({json.dumps(b[field], sort_keys=True) for b in identities}), len(APPS), field)

    def test_identity_is_consumed_by_actual_child_markup(self):
        for app in APPS:
            with self.subTest(app=app):
                folder = ROOT / 'apps' / app
                brand = json.loads((folder / 'brand.json').read_text())
                html = (folder / 'ui.html').read_text()
                self.assertIn(f'<title>{brand["name"]} · Fictional demo</title>', html)
                self.assertIn(f'data-visual-style="{brand["style"]}"', html)
                self.assertIn(f'data-brand="{app}"', html)
                self.assertIn(brand['tagline'], html)
                self.assertIn("$('title').textContent=" + json.dumps(brand['name']), html)
                for color in brand['colors'].values(): self.assertIn(color, html)
                for family in ('display', 'body'): self.assertIn(brand['typography'][family], html)
                self.assertIn(':focus-visible', html)
                self.assertIn('@media(max-width:640px)', html)
                self.assertNotRegex(html, r'(?:src|href)=["\']https?://|@import|url\(https?://')
                self.assertIn('FICTIONAL DEMO', html)
                for selector in ('signin', 'challenge', 'identity', 'read', 'payload', 'case', 'account'):
                    self.assertIn(f'id="{selector}"', html)

    def test_readable_palette_contrast(self):
        for app in APPS:
            brand = json.loads((ROOT / 'apps' / app / 'brand.json').read_text())
            c = brand['colors']
            with self.subTest(app=app):
                self.assertGreaterEqual(contrast(c['text'], c['background']), 4.5)
                self.assertGreaterEqual(contrast(c['text'], c['surface']), 4.5)
                button_text = '#17212c' if app in ('mock-coderpad', 'mock-code-workspace') else '#ffffff'
                self.assertGreaterEqual(contrast(c['accent'], button_text), 4.5)

if __name__ == '__main__': unittest.main()
