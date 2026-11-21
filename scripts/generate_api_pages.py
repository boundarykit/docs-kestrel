import argparse
import json
import re
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
START = "{/* GENERATED:START */}"
END = "{/* GENERATED:END */}"
BASE = "https://api.boundarykit.com"
METHODS = {"get", "post", "put", "patch", "delete"}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def page_path(page):
    return ROOT / (page + ".mdx")


def leaves(items):
    for item in items:
        if isinstance(item, str):
            yield item
        else:
            yield from leaves(item["pages"])


def group(items, name):
    for item in items:
        if isinstance(item, dict) and item["group"] == name:
            return item["pages"]
    pages = []
    items.append({"group": name, "pages": pages})
    return pages


def write_page(page, header, body):
    path = page_path(page)
    path.parent.mkdir(parents=True, exist_ok=True)
    original = path.read_text() if path.exists() else header + "\n\n" + START + "\n" + END + "\n"
    if original.count(START) != 1 or original.count(END) != 1:
        raise ValueError(f"Expected one generated region in {path}")
    prefix, rest = original.split(START)
    _, suffix = rest.split(END)
    path.write_text(prefix + START + "\n\n" + body + "\n\n" + END + suffix)


def fields(schema, spec, seen=()):
    ref = schema.get("$ref")
    if ref and ref not in seen:
        return fields(spec["components"]["schemas"][ref.split("/")[-1]], spec, (*seen, ref))
    if "oneOf" in schema:
        key = schema.get("discriminator", {}).get("propertyName", "type")
        return f"Select the payload by `{key}`.\n\n" + "\n\n".join(fields(s, spec, seen) for s in schema["oneOf"])
    return "\n".join(f"- `{k}` — `{v.get('const', v.get('type', v.get('$ref', 'object').split('/')[-1]))}`" for k, v in schema.get("properties", {}).items())


def generate(spec):
    config = json.loads((ROOT / "docs.json").read_text())
    groups = next(t["groups"] for t in config["navigation"]["tabs"] if t["tab"] == "API")
    resources = group(groups, "REST API")
    known = {item["group"].lower() for item in resources if isinstance(item, dict)}
    existing = {}
    for file in (ROOT / "api-reference/endpoint").rglob("*.mdx"):
        match = re.search(r"^(?:openapi|api):\s*[\"']?(GET|POST|PUT|PATCH|DELETE)\s+(?:https?://[^/]+)?(/[^\s\"']+)", file.read_text(), re.M)
        if match:
            existing[match.groups()] = file.relative_to(ROOT).with_suffix("").as_posix()
    ignored = set((ROOT / "scripts/api-ignore.txt").read_text().splitlines())
    used = set(existing.values())
    ops = {}
    for route, methods in spec["paths"].items():
        for method, op in methods.items():
            verb = method.upper()
            if method not in METHODS:
                continue
            params = methods.get("parameters", []) + op.get("parameters", [])
            if f"{verb} {route}" in ignored or re.search(r"/(?:internal|admin|health|\.well-known|ping|bbb(?:-[^/]*)?)(?:/|$)", route) or any("internal" in p.get("name", "").lower() for p in params):
                continue
            title = op.get("summary") or f"{verb} {route}"
            tag = next(iter(op.get("tags", [])), "Other").lower()
            pages = group(resources, tag.title()) if tag in known else group(groups, "Other")
            version = re.match(r"/(v\d+)/", route)
            stem = f"api-reference/endpoint/{version[1] if version else 'common'}/{slug(title)}"
            page = existing.get((verb, route))
            if not page:
                page = stem
                if page in used:
                    page += "-" + slug(f"{verb}-{route}")
                while page in used:
                    page += "-alt"
            used.add(page)
            if page not in pages:
                pages.append(page)
            header = f"---\ntitle: {json.dumps(title)}\napi: {verb} {BASE}{route}\n---"
            body = [f"`{verb} {route}`", op.get("description", ""), "## Parameters", *[f"- `{p.get('name', p.get('$ref'))}` ({p.get('in', 'reference')}) {p.get('description', '')}".rstrip() for p in params], "## Responses", *[f"- `{code}` {r.get('description','')}" for code, r in op.get("responses", {}).items()]]
            write_page(page, header, "\n\n".join(filter(None, body)))
            ops[page] = dict(page=page, title=title, method=verb, path=route)
    for event, hook in spec.get("webhooks", {}).items():
        page = "api-reference/webhook/" + slug(event)
        pages = group(group(groups, "Events"), "Webhooks")
        if page not in pages:
            pages.append(page)
        schema = hook["post"]["requestBody"]["content"]["application/json"]["schema"]
        write_page(page, f"---\ntitle: {json.dumps(event)}\n---", "## Payload\n\n" + fields(schema, spec))
        ops[page] = dict(page=page, title=event, method="Webhook", path=event)
    (ROOT / "docs.json").write_text(json.dumps(config, indent=2) + "\n")
    ordered = [ops[p] for g in groups for p in leaves(g["pages"]) if p in ops]
    (ROOT / "snippets/api-operations.jsx").write_text("export const operations = " + json.dumps(ordered, indent=2) + ";\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    source = parser.parse_args().source
    if source.startswith(("https://", "http://")):
        with urlopen(source, timeout=30) as response:
            generate(json.load(response))
    else:
        generate(json.loads(Path(source).read_text()))
