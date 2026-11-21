import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RegenerationTest(unittest.TestCase):
    def test_mutated_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("scripts", "snippets", "api-reference"):
                shutil.copytree(ROOT / name, root / name)
            shutil.copy(ROOT / "docs.json", root)
            spec = json.loads((ROOT / "openapi.json").read_text())
            operation = spec["paths"]["/v1/boundaries"]["get"]
            operation["parameters"][0]["description"] = "Select the kestrel organization."
            new = {"get": {"summary": "Read kestrel queue", "responses": {"200": {"description": "Ready"}}}}
            spec["paths"]["/v1/kestrel-queue"] = new
            spec["paths"]["/v1/kestrel-hidden"] = new
            with (root / "scripts/api-ignore.txt").open("a") as file:
                file.write("\nGET /v1/kestrel-hidden\n")
            (root / "mutation.json").write_text(json.dumps(spec))
            page = root / "api-reference/endpoint/v1/list-boundaries.mdx"
            before = page.read_text()
            subprocess.run([sys.executable, "scripts/generate_api_pages.py", "mutation.json"], cwd=root, check=True)
            subprocess.run([sys.executable, "scripts/generate_cheat_sheet.py"], cwd=root, check=True)
            after = page.read_text()
            self.assertEqual(before.split("{/* GENERATED:START */}")[0], after.split("{/* GENERATED:START */}")[0])
            self.assertEqual(before.split("{/* GENERATED:END */}")[1], after.split("{/* GENERATED:END */}")[1])
            self.assertIn("Select the kestrel organization.", after)
            index = (root / "snippets/api-operations.jsx").read_text()
            self.assertIn("/v1/kestrel-queue", index)
            self.assertNotIn("kestrel-hidden", index)
            pages = list((root / "api-reference/endpoint").rglob("*.mdx"))
            self.assertEqual(len(pages), 200)
            self.assertIn("GET /v1/kestrel-queue", next(p for p in pages if p.stem == "read-kestrel-queue").read_text())
            self.assertNotIn("kestrel-queue", (root / "api-reference/cheat-sheet.mdx").read_text())
