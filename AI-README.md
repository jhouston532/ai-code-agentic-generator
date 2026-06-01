# Ollama Code-Gen Pipeline

A multi-model, manager-directed code-generation loop that uses local Ollama
models to iteratively produce a Python script that satisfies a task.

---

## Architecture

```
task_file.txt
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  Manager model (llama3 / mistral / …)                       │
│   • Initial plan  — ranks coder models for the task         │
│   • Per-iteration — picks next model + writes feedback      │
└────────────┬────────────────────────────────────────────────┘
             │ next_model + feedback
             ▼
     ┌───────────────┐
     │  Coder model  │  receives: task + prior attempts + feedback
     └───────┬───────┘
             │ generated script
             ▼
     ┌───────────────┐
     │  Sandbox      │  blocks dangerous imports (os, sys, shutil, …)
     └───────┬───────┘
             │
     ┌───────▼───────┐
     │  Test runner  │  exact stdout / inline asserts / external test script
     └───────┬───────┘
          ┌──┴──┐
        FAIL   PASS
          │      └──→  success.py
          ▼
   attempts/NNN/
   ├── code.py
   ├── stdout.txt
   ├── stderr.txt
   ├── manager_feedback.txt
   └── model.txt
   fail-N.py  (flat copy for quick browsing)
```

---

## Requirements

```bash
pip install requests
```

Ollama must be running: https://ollama.com

---

## Task file format

```
TASK:
Describe what the script must do.

EXPECTED_OUTPUT:
Exact stdout the script must produce (compared after strip()).

INPUT_DATA:
Optional stdin piped into the script on each test run.

TEST_ARGS:
Optional CLI args (space-separated) passed to the script.

TEST:
assert add(2, 3) == 5
assert add(-1, 1) == 0

TEST:
assert subtract(10, 4) == 6

TEST_SCRIPT:
my_tests.py
```

**Testing modes** (pick one or combine):

| Section | Behaviour |
|---|---|
| `EXPECTED_OUTPUT` | stdout must match exactly (stripped) |
| `TEST:` (repeatable) | assert lines appended to generated code and executed; all must pass |
| `TEST_SCRIPT:` | external `.py` run via subprocess; pass = exit code 0 |

---

## Usage

```bash
# Minimal
python ollama_codegen.py task_example.txt

# Full options
python ollama_codegen.py task.txt \
  --output-dir ./runs        \
  --models deepseek-coder codellama mistral \
  --manager llama3           \
  --max-iterations 20        \
  --timeout 15               \
  --no-sandbox               # only for fully trusted tasks
```

---

## Output layout

```
<output-dir>/
├── attempts/
│   ├── 001/
│   │   ├── code.py               generated script
│   │   ├── stdout.txt            what it printed
│   │   ├── stderr.txt            any errors
│   │   ├── manager_feedback.txt  manager's diagnosis
│   │   └── model.txt             which model generated it
│   └── 002/ …
├── fail-1.py                     flat copy (quick browsing)
├── fail-2.py
└── success.py                    written on first passing attempt
```

---

## Configuration defaults (top of script)

| Variable | Default | Description |
|---|---|---|
| `MANAGER_MODEL` | `llama3` | Model used for routing and review |
| `DEFAULT_MODELS` | `[deepseek-coder, codellama, mistral]` | Coder pool |
| `SCRIPT_TIMEOUT` | `15` | Seconds per test run |
| `DEFAULT_MAX_ITER` | `20` | Max attempts before giving up |
| `DANGEROUS_IMPORTS` | see source | Imports blocked by sandbox |

---

## What changed from v1

| Issue | Fix |
|---|---|
| Regex JSON parsing fragility | Ollama `format` schema enforces valid JSON output |
| `/tmp/` hardcoded (Windows crash) | `tempfile.NamedTemporaryFile` — cross-platform |
| File number gaps on empty response | Separate `fail_count` only increments on write |
| "No markdown fences" prompt fights fine-tuning | Embrace fences; strip them after |
| Dangerous code executed directly | Import scanner blocks `os`, `sys`, `shutil`, etc. |
| Manager only routes once | Manager picks `next_model` after every failed attempt |
| Only exact stdout testing | `TEST:` assert blocks and `TEST_SCRIPT:` now supported |
| Models start from scratch each time | Full prior attempt history passed to every model |
| Only `fail-N.py` saved | `attempts/NNN/` folder with stdout, stderr, feedback, model |