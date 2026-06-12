#!/usr/bin/env python3
"""
ollama_codegen.py — Multi-model code generation pipeline via Ollama (v3).

Architecture:
    MANAGER     — plans a code outline (sections), assigns sections to coders,
                  assembles the final script, and routes after failures.
    CODERS      — small/specialised models that each generate ONE section of
                  the outline, so the work fits inside their context window.
    EVALUATORS  — a 5-model panel. Each judge reads the task REQUIREMENTS plus
                  the captured stdout/stderr of the assembled program and votes
                  pass/fail. The run only succeeds when at least 4 of 5 judges
                  vote pass. This replaces exact-output matching, so
                  non-deterministic programs can be graded.

VRAM tiers:
    By default the pipeline uses models sized for 12 GB of VRAM.
    Pass --vram 24 to use the larger 24 GB model set instead.

Usage:
    python ollama_codegen.py <task_file> [options]
    python ollama_codegen.py task.txt --vram 24

Options:
    --vram               VRAM tier: 12 (default) or 24
    --output-dir, -o     Directory for attempts/ and success.py  (default: .)
    --max-iterations,-n  Maximum assemble→run→evaluate cycles    (default: 10)
    --models, -m         Coder model names (overrides tier defaults)
    --manager            Manager model name (overrides tier default)
    --evaluators         Evaluator model names (overrides tier defaults)
    --timeout            Seconds before killing the program run  (default: 15)
    --no-sandbox         Skip dangerous-pattern check (use with care)

Task file sections:
    TASK:          Natural-language description of what the script must do
    REQUIREMENTS:  Natural-language acceptance criteria the evaluator panel
                   grades against
    INPUT_DATA:    (optional) stdin piped into the generated script
    TEST_ARGS:     (optional) CLI args passed to the generated script
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import requests

# ── Configuration ─────────────────────────────────────────────────────────────

OLLAMA_BASE_URL    = "http://localhost:11434"
DEFAULT_MAX_ITER   = 10
DEFAULT_OUTPUT_DIR = "."
SCRIPT_TIMEOUT     = 15
VOTES_REQUIRED     = 4          # of 5 evaluators must vote "pass"
HISTORY_TRUNC      = 2000       # chars of stdout/stderr kept per history record

MODEL_TIERS: dict[int, dict] = {
    12: {
        "coders": [
            "qwen2.5-coder:14b",
            "qwen2.5-coder:7b",
            "deepseek-coder-v2:16b",
            "codegemma:7b",
            "starcoder2:7b",
        ],
        "manager": "llama3.1:8b",
        "evaluators": [
            "phi4:14b",
            "qwen3:8b",
            "qwen2.5:14b",
            "gemma3:12b",
            "mistral-nemo:12b",
        ],
    },
    24: {
        "coders": [
            "qwen3-coder:30b",
            "qwen2.5-coder:32b",
            "devstral:24b",
            "codestral:22b",
            "deepseek-coder-v2:16b",
        ],
        "manager": "qwen3:30b",
        "evaluators": [
            "gemma3:27b",
            "qwen3:30b",
            "qwen2.5:32b",
            "mistral-small:24b",
            "phi4:14b",
        ],
    },
}

# Set in main() from --vram / overrides
MANAGER_MODEL: str = MODEL_TIERS[12]["manager"]
EVALUATOR_MODELS: list[str] = MODEL_TIERS[12]["evaluators"]

# Crude sandbox heuristics — patterns we refuse to execute locally.
DANGEROUS_PATTERNS = [
    r"\bos\.system\s*\(",
    r"\bsubprocess\b",
    r"\bshutil\.rmtree\s*\(",
    r"\bsocket\b",
    r"\bctypes\b",
    r"\bos\.remove\s*\(",
    r"\bos\.unlink\s*\(",
    r"\beval\s*\(\s*input",
]

# Single session = connection pooling across the many Ollama calls
SESSION = requests.Session()


# ── Ollama API helpers ─────────────────────────────────────────────────────────

def ollama_chat(
    model: str,
    messages: list[dict],
    temperature: float = 0.2,
    json_schema: dict | None = None,
) -> str:
    """
    POST to Ollama /api/chat.
    Pass json_schema to enforce structured JSON output at the API layer,
    bypassing model tendency to wrap responses in prose or markdown.
    """
    payload: dict = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if json_schema:
        payload["format"] = json_schema

    url = f"{OLLAMA_BASE_URL}/api/chat"
    try:
        resp = SESSION.post(url, json=payload, timeout=300)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        sys.exit(f"[FATAL] Cannot reach Ollama at {OLLAMA_BASE_URL}. Is it running?")
    except requests.exceptions.HTTPError as exc:
        sys.exit(f"[FATAL] Ollama HTTP error for '{model}': {exc}")

    return resp.json()["message"]["content"]


def list_ollama_models() -> list[str]:
    """Return full names (tag included) of locally pulled models."""
    try:
        resp = SESSION.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        return []


def resolve_models(requested: list[str], available: list[str], label: str) -> list[str]:
    """
    Match requested model names against what's pulled locally.
    Accepts exact names ('qwen2.5-coder:14b') or base names
    ('qwen2.5-coder' matches any local tag of that model).
    Warns about anything that didn't resolve.
    """
    if not available:
        print(f"[WARN] Could not enumerate local models; using {label} list as-is.")
        return requested

    avail_bases = {a.split(":")[0]: a for a in available}
    avail_set = set(available)

    resolved, missing = [], []
    for r in requested:
        if r in avail_set:
            resolved.append(r)
        elif r.split(":")[0] in avail_bases:
            resolved.append(avail_bases[r.split(":")[0]])
        else:
            missing.append(r)

    if missing:
        print(f"[WARN] {label} model(s) not pulled locally: {missing}")
    if not resolved:
        print(f"[WARN] No {label} models resolved; using requested names as-is.")
        return requested
    return resolved


# ── Task file parser ───────────────────────────────────────────────────────────

def parse_task_file(path: str) -> dict:
    """
    Parse a structured task file. Supports multi-line sections.

    Returns a dict with keys:
        task, requirements, input_data, test_args
    """
    text = Path(path).read_text()
    KEYS = {"TASK", "REQUIREMENTS", "INPUT_DATA", "TEST_ARGS"}

    sections: dict[str, list[str]] = {k: [] for k in KEYS}
    current_key: str | None = None
    current_lines: list[str] = []

    def _flush():
        nonlocal current_key, current_lines
        if current_key:
            sections[current_key] = ["\n".join(current_lines).strip()]
        current_key = None
        current_lines = []

    for line in text.splitlines():
        # Comment lines (# ...) are never section content — skip them entirely
        if re.match(r"^\s*#", line):
            continue
        m = re.match(rf"^({'|'.join(KEYS)})\s*:", line)
        if m:
            _flush()
            current_key = m.group(1)
            rest = line[m.end():].strip()
            current_lines = [rest] if rest else []
        elif current_key:
            current_lines.append(line)
    _flush()

    def _get(key: str, default: str = "") -> str:
        return sections[key][0] if sections[key] else default

    task_text    = _get("TASK")
    requirements = _get("REQUIREMENTS")

    if not task_text:
        sys.exit("[FATAL] Task file must contain a TASK: section.")
    if not requirements:
        sys.exit("[FATAL] Task file must contain a REQUIREMENTS: section "
                 "(natural-language acceptance criteria for the evaluator panel).")

    raw_args = _get("TEST_ARGS")
    return {
        "task":         task_text,
        "requirements": requirements,
        "input_data":   _get("INPUT_DATA"),
        "test_args":    raw_args.split() if raw_args else [],
    }


# ── Code extraction ────────────────────────────────────────────────────────────

CODE_LINE = re.compile(
    r"^\s*(import |from |def |class |if |elif |else:|for |while |try:|"
    r"except|finally:|return |print\(|#|@|with |raise |assert |pass\b|"
    r"break\b|continue\b|[a-zA-Z_]\w*\s*[\(\[=])"
)


def _extract_code(response: str) -> str:
    """
    Pull pure Python out of a model response regardless of formatting.

    Priority order:
      1. Content inside the LAST ```python ... ``` (or plain ```) fence
      2. Line-scored heuristic fallback for unfenced responses
    """
    text = response.strip()

    fenced = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if fenced:
        return fenced[-1].strip()

    lines = text.splitlines()
    code_start = 0
    for i, line in enumerate(lines):
        if line.strip() and CODE_LINE.match(line):
            code_start = i
            break

    candidate = lines[code_start:]
    non_blank = [l for l in candidate if l.strip()]
    if not non_blank:
        return ""

    score = sum(1 for l in non_blank if CODE_LINE.match(l)) / len(non_blank)
    return "\n".join(candidate).strip() if score >= 0.5 else ""


# ── Manager: code outline ──────────────────────────────────────────────────────

OUTLINE_SCHEMA = {
    "type": "object",
    "properties": {
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name":        {"type": "string"},
                    "description": {"type": "string"},
                    "interface":   {"type": "string"},
                    "model":       {"type": "string"},
                },
                "required": ["name", "description", "interface", "model"],
            },
        },
        "notes": {"type": "string"},
    },
    "required": ["sections", "notes"],
}


def manager_outline(task: dict, coder_models: list[str], feedback: str = "") -> dict:
    """
    Ask the manager to break the program into small, independently
    generatable sections, each assigned to a coder model. Each section's
    'interface' describes exactly what it must define (function signatures,
    globals) so sections compose cleanly.
    """
    model_list = "\n".join(f"  - {m}" for m in coder_models)
    feedback_block = f"\nPREVIOUS-FAILURE FEEDBACK (address this in the new outline):\n{feedback}\n" if feedback else ""

    prompt = textwrap.dedent(f"""
        You are the architect for a Python code-generation pipeline.
        Break the program below into 2-5 small, self-contained sections that
        small coder models can each generate independently. Sections will be
        concatenated IN ORDER into one script, so:

        - Section 1 should contain all imports and constants.
        - Each section's "interface" must state EXACTLY what it defines
          (e.g. "defines function parse_input(text: str) -> list[int]")
          and what it may call from earlier sections.
        - The FINAL section must contain the main entry point
          (if __name__ == "__main__": ...).
        - Assign each section a "model" from the available coder models,
          giving the hardest section to the strongest model.

        AVAILABLE CODER MODELS:
        {model_list}

        TASK:
        {task['task']}

        REQUIREMENTS (graded by an evaluator panel after the program runs):
        {task['requirements']}
        {feedback_block}
        Return JSON: {{"sections": [{{"name", "description", "interface", "model"}}], "notes": "..."}}
    """).strip()

    raw = ollama_chat(
        MANAGER_MODEL,
        [{"role": "user", "content": prompt}],
        temperature=0.2,
        json_schema=OUTLINE_SCHEMA,
    )

    try:
        outline = json.loads(raw)
        sections = outline.get("sections", [])
        if not sections:
            raise ValueError("empty outline")
        # Sanitise model assignments
        for s in sections:
            if s.get("model") not in coder_models:
                s["model"] = coder_models[0]
        return outline
    except (json.JSONDecodeError, ValueError, AttributeError):
        # Degenerate fallback: single section, strongest model
        print("[MANAGER] Could not parse outline; falling back to single-section plan.")
        return {
            "sections": [{
                "name": "whole_program",
                "description": task["task"],
                "interface": "Complete runnable script including main entry point.",
                "model": coder_models[0],
            }],
            "notes": "Fallback single-section outline.",
        }


# ── Coders: per-section generation ────────────────────────────────────────────

def generate_section(
    section: dict,
    outline: dict,
    task: dict,
    feedback: str = "",
) -> str:
    """
    Ask the assigned coder model to generate ONE section of the program.
    The full outline is summarised so the coder knows what surrounds its
    section, but it only writes its own part — keeping prompts small enough
    for 7B-class context windows.
    """
    outline_summary = "\n".join(
        f"  {i+1}. {s['name']}: {s['interface']}"
        for i, s in enumerate(outline["sections"])
    )

    system = (
        "You are an expert Python programmer working on ONE section of a larger "
        "script. Write ONLY your assigned section. Do not re-write other sections, "
        "do not add imports unless your section is the imports section, and do not "
        "wrap your code in a class unless told to. "
        "Return the code in a ```python ... ``` block."
    )

    feedback_block = f"\n\nFIX FEEDBACK FOR THIS SECTION:\n{feedback}" if feedback else ""

    user = textwrap.dedent(f"""
        OVERALL TASK:
        {task['task']}

        PROGRAM OUTLINE (sections are concatenated in order):
        {outline_summary}

        YOUR SECTION: {section['name']}
        DESCRIPTION: {section['description']}
        INTERFACE CONTRACT (you must define exactly this): {section['interface']}{feedback_block}

        Write only this section now.
    """).strip()

    response = ollama_chat(
        section["model"],
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.3,
    )
    return _extract_code(response)


# ── Manager: assembly ──────────────────────────────────────────────────────────

def manager_assemble(task: dict, outline: dict, section_code: dict[str, str]) -> str:
    """
    Piece the generated sections together into one runnable script.

    Strategy: deterministic concatenation first (always available as a
    fallback), then a manager review pass that may fix seams — duplicate
    imports, missing glue, ordering issues. If the manager's output can't be
    extracted as code, the concatenation is used as-is.

    Single-section outlines skip the repair pass entirely: there are no
    seams to fix, so the extra LLM call would be pure overhead.
    """
    ordered = [section_code.get(s["name"], "") for s in outline["sections"]]
    concatenated = "\n\n\n".join(c for c in ordered if c).strip()

    if len(outline["sections"]) == 1:
        return concatenated

    prompt = textwrap.dedent(f"""
        You are assembling a Python script from independently generated
        sections. Fix any seams: remove duplicate imports, resolve name
        mismatches between sections, and ensure there is exactly one
        `if __name__ == "__main__":` entry point. Do NOT redesign the
        program — only stitch and repair.

        TASK:
        {task['task']}

        ASSEMBLED DRAFT:
        ```python
        {concatenated}
        ```

        Return the complete, corrected script in a single ```python block.
    """).strip()

    response = ollama_chat(MANAGER_MODEL, [{"role": "user", "content": prompt}], temperature=0.1)
    repaired = _extract_code(response)

    if repaired and len(repaired) >= 0.5 * len(concatenated):
        return repaired
    print("[MANAGER] Assembly review produced no usable code; using raw concatenation.")
    return concatenated


# ── Program execution ──────────────────────────────────────────────────────────

def sandbox_check(code: str) -> str | None:
    """Return a description of the first dangerous pattern found, else None."""
    for pat in DANGEROUS_PATTERNS:
        if re.search(pat, code):
            return pat
    return None


def run_program(code: str, task: dict, timeout: int, sandbox: bool) -> tuple[str, str, int]:
    """
    Write the assembled code to a temp file and run it with the task's
    stdin/args, capturing stdout, stderr, and the exit code.
    """
    if sandbox:
        hit = sandbox_check(code)
        if hit:
            return "", f"[SANDBOX] Refused to run: code matches dangerous pattern {hit}", -1

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
        script_path = f.name

    try:
        proc = subprocess.run(
            [sys.executable, script_path, *task["test_args"]],
            input=task["input_data"] or None,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return "", f"[TIMEOUT] Exceeded {timeout}s", -1
    finally:
        Path(script_path).unlink(missing_ok=True)


# ── Evaluator panel ────────────────────────────────────────────────────────────

EVAL_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict":  {"type": "string", "enum": ["pass", "fail"]},
        "feedback": {"type": "string"},
    },
    "required": ["verdict", "feedback"],
}


def _judge_once(model: str, task: dict, code: str, stdout: str, stderr: str, returncode: int) -> dict:
    """One evaluator's verdict on a single run."""
    prompt = textwrap.dedent(f"""
        You are a strict but fair code evaluator. A program was generated for
        the task below and executed once. Decide whether its OUTPUT satisfies
        EVERY requirement. The output may be non-deterministic — judge whether
        this particular run is CONSISTENT with the requirements, not whether
        it matches a fixed string.

        Verdict rules:
        - "fail" if the program crashed (non-zero exit, traceback in stderr)
          unless the requirements explicitly allow it.
        - "fail" if ANY requirement is violated or unverifiable from the output.
        - "pass" only if every requirement is satisfied by this run.
        - In "feedback", list each violated requirement and what concretely
          must change. Be specific; this feedback drives the next iteration.

        TASK:
        {task['task']}

        REQUIREMENTS:
        {task['requirements']}

        PROGRAM (first 80 lines):
        {chr(10).join(code.splitlines()[:80])}

        EXIT CODE: {returncode}

        STDOUT:
        {stdout or '(none)'}

        STDERR:
        {stderr or '(none)'}

        Return JSON: {{"verdict": "pass" | "fail", "feedback": "..."}}
    """).strip()

    raw = ollama_chat(
        model,
        [{"role": "user", "content": prompt}],
        temperature=0.1,
        json_schema=EVAL_SCHEMA,
    )

    try:
        result = json.loads(raw)
        if result.get("verdict") not in ("pass", "fail"):
            raise ValueError("bad verdict")
        return result
    except (json.JSONDecodeError, ValueError, AttributeError):
        return {"verdict": "fail", "feedback": "Evaluator response unparseable; counted as fail vote."}


def evaluator_panel(task: dict, code: str, stdout: str, stderr: str, returncode: int) -> dict:
    """
    Poll the evaluator panel and apply majority voting.

    With a full 5-model panel, at least VOTES_REQUIRED (4) pass votes are
    needed for success. If fewer than 5 evaluators resolved locally, the
    threshold degrades to n-1 (minimum 1) with a warning at startup.

    Early exit: judging stops as soon as the outcome is mathematically
    decided — on 12 GB cards every extra judge call costs a model swap,
    so skipping moot votes is a significant runtime saving.
    """
    n = len(EVALUATOR_MODELS)
    needed = VOTES_REQUIRED if n >= 5 else max(1, n - 1)
    max_fails_allowed = n - needed

    passes, fails = 0, 0
    votes: dict[str, str] = {}
    fail_feedback: list[str] = []

    for i, model in enumerate(EVALUATOR_MODELS):
        result = _judge_once(model, task, code, stdout, stderr, returncode)
        votes[model] = result["verdict"]

        if result["verdict"] == "pass":
            passes += 1
            print(f"[EVAL]   {model}: PASS  ({passes} pass / {fails} fail)")
        else:
            fails += 1
            fail_feedback.append(f"[{model}] {result['feedback']}")
            print(f"[EVAL]   {model}: FAIL  ({passes} pass / {fails} fail)")

        remaining = n - (i + 1)
        if fails > max_fails_allowed:
            # Verdict can no longer reach the pass threshold
            if remaining:
                print(f"[EVAL]   outcome decided — skipping {remaining} remaining judge(s)")
            break
        if passes >= needed and remaining:
            print(f"[EVAL]   pass threshold reached — skipping {remaining} remaining judge(s)")
            break

    verdict = "pass" if passes >= needed else "fail"
    feedback = "\n".join(fail_feedback) if fail_feedback else "All evaluators passed."
    return {
        "verdict": verdict,
        "feedback": feedback,
        "votes": votes,
        "passes": passes,
        "needed": needed,
    }


# ── Manager: failure routing ───────────────────────────────────────────────────

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "strategy": {"type": "string", "enum": ["patch", "reoutline"]},
        "reason":   {"type": "string"},
        "section_feedback": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
    },
    "required": ["strategy", "reason", "section_feedback"],
}


def manager_review(task: dict, outline: dict, eval_feedback: str, history: list[dict]) -> dict:
    """
    Given the evaluator panel's failure feedback, the manager decides whether
    to PATCH (regenerate only the broken sections, with targeted feedback) or
    REOUTLINE (the architecture itself is wrong; start a fresh outline).
    """
    section_names = [s["name"] for s in outline["sections"]]
    history_text = ""
    for h in history[-2:]:
        history_text += (
            f"\n--- Iteration {h['iteration']} ---\n"
            f"verdict : fail\n"
            f"stderr  : {(h['stderr'] or '(none)')[:300]}\n"
            f"feedback: {h['eval_feedback'][:400]}\n"
        )

    prompt = textwrap.dedent(f"""
        You manage a sectioned code-generation pipeline. The assembled program
        failed evaluation by a multi-model judge panel. Decide how to recover.

        TASK:
        {task['task']}

        REQUIREMENTS:
        {task['requirements']}

        OUTLINE SECTIONS: {", ".join(section_names)}

        EVALUATOR PANEL FEEDBACK (current failure):
        {eval_feedback}

        RECENT HISTORY:{history_text or " (none)"}

        Choose:
        - "patch": the outline is sound; map the failure to the specific
          section(s) responsible and give each one concrete fix instructions
          in "section_feedback" (keys MUST be section names from the list).
        - "reoutline": the structure itself is wrong or patching has failed
          repeatedly; the pipeline will build a new outline from scratch.
          Put guidance for the new outline in section_feedback under the
          key "outline".

        Return JSON: {{"strategy": "patch"|"reoutline", "reason": "...",
                       "section_feedback": {{"<section or 'outline'>": "<fix instructions>"}}}}
    """).strip()

    raw = ollama_chat(
        MANAGER_MODEL,
        [{"role": "user", "content": prompt}],
        temperature=0.2,
        json_schema=REVIEW_SCHEMA,
    )

    try:
        result = json.loads(raw)
        if result.get("strategy") not in ("patch", "reoutline"):
            raise ValueError("bad strategy")
        if result["strategy"] == "patch":
            valid = {k: v for k, v in result.get("section_feedback", {}).items() if k in section_names}
            if not valid:
                # Manager named no valid section — escalate to reoutline
                return {"strategy": "reoutline", "reason": "Patch targeted no valid sections.",
                        "section_feedback": {"outline": eval_feedback}}
            result["section_feedback"] = valid
        return result
    except (json.JSONDecodeError, ValueError, AttributeError):
        return {"strategy": "reoutline",
                "reason": "Manager review unparseable; rebuilding outline.",
                "section_feedback": {"outline": eval_feedback}}


# ── Iteration metadata ─────────────────────────────────────────────────────────

def save_attempt(
    output_dir: Path,
    iteration: int,
    code: str,
    stdout: str,
    stderr: str,
    panel: dict,
    outline: dict,
    review: dict,
) -> None:
    """Save all artefacts for one failed iteration into attempts/NNN/."""
    attempt_dir = output_dir / "attempts" / f"{iteration:03d}"
    attempt_dir.mkdir(parents=True, exist_ok=True)

    (attempt_dir / "code.py").write_text(code)
    (attempt_dir / "stdout.txt").write_text(stdout)
    (attempt_dir / "stderr.txt").write_text(stderr)
    (attempt_dir / "evaluator_panel.json").write_text(json.dumps(panel, indent=2))
    (attempt_dir / "outline.json").write_text(json.dumps(outline, indent=2))
    (attempt_dir / "manager_review.json").write_text(json.dumps(review, indent=2))

    print(f"[SAVED]  attempts/{iteration:03d}/")


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run_pipeline(args: argparse.Namespace) -> None:
    global EVALUATOR_MODELS

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sandbox = not args.no_sandbox
    timeout = args.timeout
    tier = MODEL_TIERS[args.vram]

    print(f"\n{'═'*62}")
    print(f"  Ollama Code-Gen Pipeline v3  (sandbox={'ON' if sandbox else 'OFF'}, vram={args.vram}GB)")
    print(f"  manager={MANAGER_MODEL}")
    print(f"{'═'*62}")

    # 1. Parse task file
    print(f"[TASK]  {args.task_file}")
    task = parse_task_file(args.task_file)
    print(f"[TASK]  {task['task'][:80]}{'…' if len(task['task']) > 80 else ''}")
    print(f"[REQS]  {task['requirements'][:80]}{'…' if len(task['requirements']) > 80 else ''}")

    # 2. Resolve models against local pulls
    available = list_ollama_models()
    coder_models = resolve_models(args.models or tier["coders"], available, "coder")
    EVALUATOR_MODELS = resolve_models(args.evaluators or tier["evaluators"], available, "evaluator")
    print(f"[CODERS] {coder_models}")
    print(f"[JUDGES] {EVALUATOR_MODELS}")
    if len(EVALUATOR_MODELS) < 5:
        thresh = max(1, len(EVALUATOR_MODELS) - 1)
        print(f"[WARN]  Only {len(EVALUATOR_MODELS)} evaluator(s) resolved — "
              f"pass threshold degraded from {VOTES_REQUIRED}/5 to {thresh}/{len(EVALUATOR_MODELS)}.")

    # 3. Manager builds the initial outline
    print(f"\n[MANAGER] '{MANAGER_MODEL}' drafting code outline…")
    outline = manager_outline(task, coder_models)
    for i, s in enumerate(outline["sections"], 1):
        print(f"  {i}. {s['name']}  →  {s['model']}")
        print(f"     {s['interface'][:90]}")

    # 4. Generate / assemble / run / judge loop
    section_code: dict[str, str] = {}
    section_feedback: dict[str, str] = {s["name"]: "" for s in outline["sections"]}
    sections_to_generate = set(section_feedback)

    history: list[dict] = []
    iteration = 0

    while iteration < args.max_iterations:
        iteration += 1
        print(f"\n[ITER {iteration:02d}] ───────────────────────────────────────")

        # 4a. (Re)generate any pending sections
        for s in outline["sections"]:
            name = s["name"]
            if name not in sections_to_generate:
                continue
            fb = section_feedback.get(name, "")
            print(f"[ITER {iteration:02d}]  generating section '{name}' with {s['model']}…")
            code = generate_section(s, outline, task, fb)
            if not code:
                # One retry with the first coder as fallback
                fallback = dict(s, model=coder_models[0])
                print(f"[ITER {iteration:02d}]  empty response — retrying with {fallback['model']}")
                code = generate_section(fallback, outline, task, fb)
            section_code[name] = code or "# (section generation failed)"
        sections_to_generate.clear()

        # 4b. Manager assembles the full script
        print(f"[ITER {iteration:02d}]  manager assembling {len(outline['sections'])} section(s)…")
        full_code = manager_assemble(task, outline, section_code)
        if not full_code.strip():
            print(f"[ITER {iteration:02d}]  assembly produced nothing — rebuilding outline")
            outline = manager_outline(task, coder_models, "Previous assembly was empty.")
            section_code.clear()
            section_feedback = {s["name"]: "" for s in outline["sections"]}
            sections_to_generate = set(section_feedback)
            continue

        # 4c. Run the program and capture results
        stdout, stderr, returncode = run_program(full_code, task, timeout, sandbox)
        print(f"[ITER {iteration:02d}]  ran program  exit={returncode}  "
              f"stdout={len(stdout)}B  stderr={len(stderr)}B")

        # 4d. Evaluator panel votes
        panel = evaluator_panel(task, full_code, stdout, stderr, returncode)
        print(f"[EVAL]   panel verdict: {panel['verdict'].upper()}  "
              f"({panel['passes']} pass, needed {panel['needed']})")

        if panel["verdict"] == "pass":
            success_path = output_dir / "success.py"
            success_path.write_text(full_code)
            print(f"\n{'═'*62}")
            print(f"  ✓  SUCCESS — iteration {iteration}  "
                  f"({panel['passes']}/{len(EVALUATOR_MODELS)} judges)")
            print(f"     {success_path}")
            print(f"{'═'*62}\n")
            return

        # 4e. Failure → manager decides patch vs reoutline
        print(f"[EVAL]   feedback: {panel['feedback'][:200].replace(chr(10), ' ')}")
        history.append({
            "iteration": iteration,
            "stdout": stdout[:HISTORY_TRUNC],
            "stderr": stderr[:HISTORY_TRUNC],
            "eval_feedback": panel["feedback"],
        })

        review = manager_review(task, outline, panel["feedback"], history)
        save_attempt(output_dir, iteration, full_code, stdout, stderr,
                     panel, outline, review)

        if review["strategy"] == "reoutline":
            print(f"[MANAGER] REOUTLINE — {review['reason'][:100]}")
            guidance = review["section_feedback"].get("outline", panel["feedback"])
            outline = manager_outline(task, coder_models, guidance)
            section_code.clear()
            section_feedback = {s["name"]: "" for s in outline["sections"]}
            sections_to_generate = set(section_feedback)
            for i, s in enumerate(outline["sections"], 1):
                print(f"  {i}. {s['name']}  →  {s['model']}")
        else:
            print(f"[MANAGER] PATCH — {review['reason'][:100]}")
            for name, fb in review["section_feedback"].items():
                print(f"  ↻ {name}: {fb[:90]}")
                section_feedback[name] = fb
                sections_to_generate.add(name)

    print(f"\n[PIPELINE] Reached max iterations ({args.max_iterations}) — no success.")
    print(f"[PIPELINE] Artefacts in: {output_dir}/attempts/")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    global MANAGER_MODEL, EVALUATOR_MODELS
    parser = argparse.ArgumentParser(
        description="Multi-model Ollama code-generation pipeline v3 "
                    "(outline → sectioned generation → assembly → run → 5-judge panel)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("task_file", help="Path to task definition file")
    parser.add_argument("--vram", type=int, choices=[12, 24], default=12,
                        help="VRAM tier: 12 (default) or 24 — selects the model set")
    parser.add_argument("--output-dir", "-o", default=DEFAULT_OUTPUT_DIR,
                        help="Output directory (default: .)")
    parser.add_argument("--max-iterations", "-n", type=int, default=DEFAULT_MAX_ITER,
                        help=f"Max assemble→run→evaluate cycles (default: {DEFAULT_MAX_ITER})")
    parser.add_argument("--models", "-m", nargs="+",
                        help="Coder models (overrides tier defaults)")
    parser.add_argument("--manager",
                        help="Manager model (overrides tier default)")
    parser.add_argument("--evaluators", nargs="+",
                        help="Evaluator models (overrides tier defaults)")
    parser.add_argument("--timeout", type=int, default=SCRIPT_TIMEOUT,
                        help=f"Script execution timeout in seconds (default: {SCRIPT_TIMEOUT})")
    parser.add_argument("--no-sandbox", action="store_true",
                        help="Disable dangerous-pattern check (use only with trusted tasks)")

    args = parser.parse_args()

    tier = MODEL_TIERS[args.vram]
    MANAGER_MODEL    = args.manager or tier["manager"]
    EVALUATOR_MODELS = args.evaluators or tier["evaluators"]

    run_pipeline(args)


if __name__ == "__main__":
    main()