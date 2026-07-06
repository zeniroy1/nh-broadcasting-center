# Musinsa Product Search Plugin Submission

This submission contains a Codex plugin and a working public-signal based Musinsa product search/comparison prototype.

The project includes implemented modules for natural-language intent parsing, public product collection, query generation, proxy scoring, recommendation output, a buyer-facing HTML UI, and validation tests.

## Structure

```text
submission/
├── src/
│   ├── .codex-plugin/plugin.json
│   ├── skills/musinsa-product-roadmap/SKILL.md
│   ├── config/
│   │   ├── musinsa_category_keywords.json
│   │   ├── scoring_weights.json
│   │   ├── collection_scope.json
│   │   ├── keyword_learning_queue.json
│   │   ├── review_signal_keywords.json
│   │   └── search_keyword_aliases.json
│   ├── scripts/
│   │   ├── musinsa_intent_parser.py
│   │   ├── musinsa_query_generator.py
│   │   ├── musinsa_live_buyer_app.py
│   │   ├── musinsa_buyer_server.py
│   │   ├── musinsa_scoring_model.py
│   │   ├── musinsa_recommendation_output.py
│   │   ├── musinsa_runtime_paths.py
│   │   └── supporting schema, metric, audit, and keyword-learning modules
│   ├── packaging/
│   │   ├── musinsa_buyer_app.spec
│   │   └── build_exe.bat
│   ├── dist/
│   │   └── MusinsaBuyerApp.exe
│   ├── tests/
│   │   └── test_*.py
│   ├── app/
│   │   └── musinsa_buyer_app.html
│   ├── docs/
│   │   ├── musinsa_search_parsing_roadmap.md
│   │   ├── specific_term_search_fix_plan.md
│   │   ├── live_buyer_program.md
│   │   ├── step_01_...step_10_*.md
│   │   └── design, decision, alignment, and self-review documents
│   └── reports/
│       ├── step_01_...step_10_*_status.html/svg
│       └── live_buyer_app_status.html/svg
├── README.md
└── logs/
    └── full conversation logs or log instructions
```

## Plugin Purpose

The plugin and prototype help a buyer move from a natural-language shopping request to comparable Musinsa product candidates using only public or proxy-safe signals.

The implemented flow:

- Parses natural-language requests into structured conditions such as gender, age band, product group, specific item terms, color, style, and price range.
- Generates Musinsa-oriented search queries while preserving specific item terms such as `래시가드`, `메신저백`, or `벨트`.
- Collects public product signals from exposed HTML/JSON where available.
- Normalizes public product data such as product name, brand, price, review count, review score, ranking position, image URL, and product URL.
- Applies public/proxy metrics for purpose fit, review evidence, price fit, target fit, popularity signals, delivery/stock status, and review-risk estimation.
- Ranks five comparison candidates, supports shortlist-style three-candidate detail review, and exposes a buyer-facing HTML UI.
- Keeps public-data boundaries explicit: actual sales counts, internal Musinsa ranking algorithms, private conversion rates, and exact age/gender purchaser counts are not claimed.

## Implemented Components

- `src/scripts/musinsa_intent_parser.py`: natural-language intent parser.
- `src/scripts/musinsa_query_generator.py`: search query candidate generator with specific-term preservation and slash category splitting.
- `src/scripts/musinsa_live_buyer_app.py`: public product collection, intent gates, fallback handling, and app model builder.
- `src/scripts/musinsa_buyer_server.py`: local HTTP server for the buyer-facing app; also handles the double-click EXE launch flow (auto-opens the browser, single-instance reuse, console-less logging).
- `src/scripts/musinsa_scoring_model.py`: proxy scoring model.
- `src/scripts/musinsa_recommendation_output.py`: ranked comparison and shortlist report builder.
- `src/scripts/musinsa_keyword_learning.py`: keyword pool update planning/support logic.
- `src/scripts/musinsa_project_audit.py`: submission consistency audit.
- `src/scripts/musinsa_runtime_paths.py`: resolves config/app asset paths for both normal source runs and a frozen (PyInstaller) executable, and keeps the writable keyword-learning queue next to the .exe instead of inside its temporary bundle folder.
- `src/app/musinsa_buyer_app.html`: interactive browser UI.
- `src/packaging/musinsa_buyer_app.spec` + `src/packaging/build_exe.bat`: PyInstaller build spec and Windows build script that produce a standalone `MusinsaBuyerApp.exe`.
- `src/tests/test_*.py`: regression tests for parsing, query generation, collection, scoring, recommendation output, server behavior, runtime path resolution, and audit checks.

## Current Status

This submission includes a working prototype and supporting tests.

The implementation currently supports:

- public Musinsa search/ranking data collection where available;
- natural-language condition extraction;
- product-group and specific-term matching;
- alias and umbrella keyword handling;
- public/proxy metric scoring;
- comparison table and visual report output;
- local buyer app serving via `musinsa_buyer_server.py`, including a one-click standalone EXE build;
- project audit and validation scripts.

Known boundaries:

- The prototype does not claim access to Musinsa private data.
- Review count is treated as public purchase-response evidence, not exact purchase count.
- Age/gender fit remains a proxy or inferred signal unless directly exposed in public data.
- Live fetch behavior can vary depending on Musinsa page/API availability, rate limits, and response shape.

## Validation

From `submission/src`, the expected validation commands are:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m compileall -q scripts
python scripts/musinsa_live_buyer_app.py --validate
python scripts/musinsa_project_audit.py
```

At the latest local check, the implementation passed the full test suite (130 tests) and project audit.

## Running The Buyer App (from source)

From `submission/src`:

```powershell
python scripts/musinsa_buyer_server.py --port 8765
```

This starts the server and automatically opens `http://127.0.0.1:8765/` in your default browser. Pass `--no-browser` to skip that and just print the URL.

## Standalone Windows EXE (double-click launch)

The server script doubles as the entry point for a single-file Windows executable, so the whole "start a server, then open it in a browser" flow becomes one double-click.

Build it (on Windows, with Python 3.10+ on PATH):

```powershell
cd submission\src
packaging\build_exe.bat
```

This installs PyInstaller if needed, runs the test suite as a safety check, and produces `submission/src/dist/MusinsaBuyerApp.exe`.

What double-clicking `MusinsaBuyerApp.exe` does:

- Starts the local server on `127.0.0.1:8765` (no terminal window is shown).
- Opens the app automatically in the default browser a moment later.
- If it's already running (e.g. double-clicked twice), the second launch just opens the browser to the existing server instead of erroring out.
- Any runtime errors are written to `musinsa_buyer_app.log` next to the .exe, since there is no console to print to.
- The keyword-learning queue (`config/keyword_learning_queue.json`) is copied next to the .exe on first run and updated there, so learned keywords persist across restarts instead of living inside the temporary bundle folder PyInstaller extracts to.

To quit the app, close it from Task Manager (there is no window/tray icon to click "Quit" from in this version).

Manual build (equivalent to what the .bat file does):

```powershell
pip install pyinstaller
python -m unittest discover -s tests -p "test_*.py"
pyinstaller packaging\musinsa_buyer_app.spec --noconfirm
```

## Logs

The `logs/` folder must contain the full, unedited AI conversation log before final submission.

If a helper note such as `logs/README_LOGS.md` is included, it is not a substitute for the required full conversation log.

## Packaging (submission zip)

To submit, zip the contents so the archive has this top-level structure:

```text
submission.zip
├── src/
├── README.md
└── logs/
```

Do not zip the parent `submission` folder itself if the evaluator expects `src` at the zip root.
