# BoundaryKit Kestrel documentation

Run the generators from the repository root with Python 3.9 or later.

```sh
python3 scripts/generate_api_pages.py openapi.json
python3 scripts/generate_cheat_sheet.py
python3 -m unittest discover -s tests
```

Keep operator notes outside the generated region on each endpoint page. The API navigation controls the operation index and cheat sheet order. The cheat sheet skips operations listed directly under Other.
