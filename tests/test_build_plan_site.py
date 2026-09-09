from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "publish" / "build_plan_site.py"
SPEC = importlib.util.spec_from_file_location("build_plan_site", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BuildPlanSiteTests(unittest.TestCase):
    def test_generates_one_search_page_per_grade_and_subject(self) -> None:
        payload = {
            "egitim_yili": "2026-2027",
            "dosyalar": [
                {"id": 1, "sinif": "9", "ders": "Türk Dili ve Edebiyatı", "kayit_sayisi": 40, "grup": "Kültür", "brans": "Türk Dili", "yayinevi": "MEB", "sistem": "Örgün"},
                {"id": 2, "sinif": "9", "ders": "Türk Dili ve Edebiyatı", "kayit_sayisi": 39, "grup": "Kültür", "brans": "Türk Dili", "yayinevi": "Özel", "sistem": "Örgün"},
                {"id": 3, "sinif": "Hazırlık", "ders": "İngilizce", "kayit_sayisi": 41, "grup": "Kültür", "brans": "İngilizce", "yayinevi": "MEB", "sistem": "Örgün"},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = root / "index.json"
            index.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            entries = MODULE.build_site(index, root, "https://example.test/data")

            self.assertEqual(len(entries), 2)
            page = root / "plan" / "9-sinif-turk-dili-ve-edebiyati-yillik-plani" / "index.html"
            self.assertTrue(page.is_file())
            content = page.read_text(encoding="utf-8")
            self.assertIn("9. Sınıf Türk Dili ve Edebiyatı Yıllık Planı", content)
            self.assertIn("App Store", content)
            self.assertIn("Google Play", content)
            self.assertIn("Haftalık ayrıntılar uygulamada açılır", content)
            self.assertIn("2 plan seçeneği", content)
            self.assertEqual((root / "sitemap.xml").read_text(encoding="utf-8").count("<url>"), 3)
            self.assertIn("İngilizce Yıllık Planı", (root / "llms-full.txt").read_text(encoding="utf-8"))
            self.assertTrue((root / "site.webmanifest").is_file())

    def test_slugify_preserves_turkish_meaning(self) -> None:
        self.assertEqual(MODULE.slugify("12. Sınıf Çağdaş Türk"), "12-sinif-cagdas-turk")


if __name__ == "__main__":
    unittest.main()
