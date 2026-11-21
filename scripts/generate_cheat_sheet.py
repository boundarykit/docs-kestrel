import json
import re
from generate_api_pages import ROOT, leaves

config = json.loads((ROOT / "docs.json").read_text())
groups = next(t["groups"] for t in config["navigation"]["tabs"] if t["tab"] == "API")
source = (ROOT / "snippets/api-operations.jsx").read_text()
operations = {op["page"]: op for op in json.loads(source.removeprefix("export const operations = ").rstrip(";\n"))}
path = ROOT / "api-reference/cheat-sheet.mdx"
intro = re.split(r"^## ", path.read_text(), maxsplit=1, flags=re.M)[0].rstrip()
sections = [intro]
for group in groups:
    rows = []
    for child in group["pages"]:
        if isinstance(child, dict):
            for page in leaves(child["pages"]):
                if page in operations:
                    op = operations[page]
                    rows.append(f"| {op['method']} | `{op['path']}` | [{op['title']}](/{page}) |")
    if rows:
        sections.append(f"## {group['group']}\n\n| Method | Route or event | Reference |\n| --- | --- | --- |\n" + "\n".join(rows))
path.write_text("\n\n".join(sections) + "\n")
