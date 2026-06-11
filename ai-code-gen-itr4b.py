#!/usr/bin/env python3
"""
ollama_codegen.py — Multi-model code generation pipeline via Ollama.

Pipeline stages (in order):
    1. Parse task file
    2. Resolve available coder models
    3. Manager picks initial model order
    4. Generation loop:
         a. Coder model generates a Python script
         b. Deterministic tests run (test_runner.py)
         c. Evaluator LLM judges semantic correctness
         d. On failure: manager routes to next model with structured feedback
         e. Artefacts saved to attempts/NNN/

Usage:
    python ollama_codegen.py <task_file> [options]

Options:
    --output-dir, -o    Directory for attempts/ and success.py  (default: .)
    --max-iterations,-n Maximum generation attempts              (default: 20)
    --models, -m        Coder model names (space-separated)
    --manager           Manager model name                       (default: llama3)
    --evaluator         Evaluator model name                     (default: llama3)
    --timeout           Seconds before killing a test run        (default: 15)
    --no-sandbox        Skip dangerous-import check (use with care)
    --no-evaluator      Skip LLM evaluation gate; use only deterministic tests

Task file sections:
    TASK:             Natural-language description of what the script must do
    EXPECTED_OUTPUT:  Exact stdout the script must produce
    REQUIREMENTS:     (optional) Natural-language rubric for the evaluator model.
                      When present without EXPECTED_OUTPUT/TEST/TEST_SCRIPT,
                      the evaluator is the sole pass/fail gate (no exact matching).
    INPUT_DATA:       (optional) stdin piped into the generated script
    TEST_ARGS:        (optional) CLI args passed to the generated script
    TEST:             (optional, repeatable) assert-style test lines
    TEST_SCRIPT:      (optional) path to an external test file to run

See task_example.txt for a complete example.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import requests

from test_runner import run_tests


# ── Configuration ──────────────────────────────────────────────────────────────

OLLAMA_BASE_URL    = "http://localhost:11434"
DEFAULT_MAX_ITER   = 20
DEFAULT_OUTPUT_DIR = "."
MANAGER_MODEL      = "llama3"
EVALUATOR_MODEL    = "llama3"
DEFAULT_MODELS     = [
    "deepseek-coder", "codellama", "mistral",
    "qwen2.5-coder", "starcoder2", "deepseek-coder-v2",
]
SCRIPT_TIMEOUT     = 15

# Pre-compiled regexes used by _extract_code helpers.
# Defined at module level to avoid recompilation on every call.
_CODE_LINE = re.compile(
    r"^\s*(import |from |def |class |if |elif |else:|for |while |try:|"
    r"except|finally:|return |print\(|#|@|with |raise |assert |pass\b|"
    r"break\b|continue\b|[a-zA-Z_]\w*\s*[\(\[=])"
)
_PROSE_LINE = re.compile(
    r"^[A-Z][a-z].*\.$"
    r"|^(Here|This|The|Note|To|In|For|You|We|It|If|Then|Now)\b"
    r"|^(Expected|Output|Result|Usage|Example|Below|Above)\b",
    re.IGNORECASE,
)


# ── Ollama API helpers ─────────────────────────────────────────────────────────

def ollama_chat(
    model: str,
    messages: list[dict],
    temperature: float = 0.2,
    json_schema: dict | None = None,
) -> str:
    """
    POST a chat completion request to Ollama's /api/chat endpoint.

    Args:
        model:       Name of the locally pulled Ollama model.
        messages:    List of {"role": ..., "content": ...} dicts.
        temperature: Sampling temperature (lower = more deterministic).
        json_schema: Optional JSON schema passed as `format` to enforce
                     structured output at the API layer, bypassing the model's
                     tendency to wrap responses in prose or markdown fences.

    Returns:
        The model's raw reply string.

    Raises:
        SystemExit on connection error or HTTP error (unrecoverable).
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
        resp = requests.post(url, json=payload, timeout=180)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        sys.exit(f"[FATAL] Cannot reach Ollama at {OLLAMA_BASE_URL}. Is it running?")
    except requests.exceptions.HTTPError as exc:
        sys.exit(f"[FATAL] Ollama HTTP error for '{model}': {exc}")

    return resp.json()["message"]["content"]


def list_ollama_models() -> list[str]:
    """
    Return all locally pulled model names from Ollama, preserving tags.

    Both the full tagged name (e.g. 'qwen2.5-coder:14b') and the untagged
    base name ('qwen2.5-coder') are returned so that callers can match
    against either format. Duplicates are removed with dict.fromkeys to
    preserve order.

    Returns:
        Deduplicated list of model name strings, or [] on failure.
    """
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        resp.raise_for_status()
        names = []
        for m in resp.json().get("models", []):
            full = m["name"]           # e.g. "qwen2.5-coder:14b"
            base = full.split(":")[0]  # e.g. "qwen2.5-coder"
            names.append(full)
            names.append(base)
        return list(dict.fromkeys(names))  # deduplicate, preserve order
    except Exception:
        return []


# ── Task file parser ───────────────────────────────────────────────────────────

def parse_task_file(path: str) -> dict:
    """
    Parse a structured task file into a usable task dict.

    Internally delegates to:
        _read_sections()   — state-machine line parser
        _build_task_dict() — validation and normalization

    Returns a dict with keys:
        task, expected_output, input_data, test_args,
        inline_tests (list[str]), test_script (str|None)
    """
    text = Path(path).read_text()
    sections, inline_tests = _read_sections(text)
    return _build_task_dict(sections, inline_tests)


def _read_sections(text: str) -> tuple[dict, list[str]]:
    """
    State-machine parser that splits raw task file text into named sections.

    How it works:
        - Lines beginning with # are ignored (comments).
        - A line matching 'SECTION_NAME:' starts a new section.
        - All subsequent lines until the next section header are accumulated
          as that section's content.
        - _flush() commits the in-progress section before starting a new one;
          it must be called both on each new header and at end-of-file.

    Args:
        text: Raw content of the task file.

    Returns:
        (sections dict, inline_tests list)
        sections maps section name -> [single string value]
        inline_tests is a flat list because TEST: is repeatable.
    """
    KEYS = {"TASK", "EXPECTED_OUTPUT", "REQUIREMENTS", "INPUT_DATA", "TEST_ARGS", "TEST", "TEST_SCRIPT"}
    sections: dict[str, list[str]] = {k: [] for k in KEYS}
    inline_tests: list[str] = []

    current_key: str | None = None
    current_lines: list[str] = []

    # _flush commits whatever section is currently in progress. It is a nested
    # function because it needs to mutate current_key and current_lines via
    # nonlocal — these are the parser's state variables and don't belong at
    # module scope.
    def _flush():
        nonlocal current_key, current_lines
        if current_key:
            value = "\n".join(current_lines).strip()
            if current_key == "TEST":
                inline_tests.append(value)
            else:
                sections[current_key] = [value]
        current_key = None
        current_lines = []

    for line in text.splitlines():
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

    return sections, inline_tests


def _build_task_dict(sections: dict, inline_tests: list[str]) -> dict:
    """
    Validate parsed sections and build the canonical task dict.

    Args:
        sections:     Output of _read_sections (section name -> [value]).
        inline_tests: List of TEST: block strings from _read_sections.

    Returns:
        Validated task dict ready for use by the rest of the pipeline.

    Raises:
        SystemExit if required sections are missing.
    """
    def _get(key: str, default: str = "") -> str:
        return sections[key][0] if sections[key] else default

    task_text    = _get("TASK")
    expected     = _get("EXPECTED_OUTPUT")
    requirements = _get("REQUIREMENTS")

    if not task_text:
        sys.exit("[FATAL] Task file must contain a TASK: section.")

    # A task is valid if it has at least one way to judge correctness:
    # deterministic (EXPECTED_OUTPUT, TEST, TEST_SCRIPT) or semantic (REQUIREMENTS).
    # REQUIREMENTS enables purely natural-language grading via the evaluator model,
    # with no exact-match testing at all.
    has_deterministic = expected or inline_tests or _get("TEST_SCRIPT")
    has_semantic      = bool(requirements)
    if not has_deterministic and not has_semantic:
        sys.exit(
            "[FATAL] Task file must contain at least one of: "
            "EXPECTED_OUTPUT:, TEST:, TEST_SCRIPT:, or REQUIREMENTS:"
        )

    raw_args = _get("TEST_ARGS")
    return {
        "task":            task_text,
        "expected_output": expected,
        "requirements":    requirements,   # natural-language rubric for the evaluator
        "input_data":      _get("INPUT_DATA"),
        "test_args":       raw_args.split() if raw_args else [],
        "inline_tests":    inline_tests,
        "test_script":     _get("TEST_SCRIPT") or None,
    }


# ── Manager: initial plan ──────────────────────────────────────────────────────

def manager_plan(task: dict, available: list[str]) -> list[str]:
    """
    Ask the manager model to choose and order coder models for this task.

    Uses Ollama structured output (format=JSON schema) so the response is
    guaranteed to be valid JSON — no regex fragility. If parsing fails,
    falls back to the provided available list unchanged.

    Args:
        task:      Parsed task dict (uses task['task'] for context).
        available: List of model names confirmed present on this machine.

    Returns:
        Ordered list of model names the manager recommends trying.
    """
    schema = {
        "type": "object",
        "properties": {
            "models": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ordered list of model names to use",
            }
        },
        "required": ["models"],
    }

    model_list = "\n".join(f"  - {m}" for m in available)
    prompt = textwrap.dedent(f"""
        You are the orchestration manager for a Python code-generation pipeline.
        Choose which models should attempt the task and the order they should run.

        Available models:
        {model_list}

        Task:
        {task['task']}

        Rules:
        - Prefer coding-specialised models (deepseek-coder, codellama) for code tasks.
        - Put the strongest / most specialised model first.
        - Include 2-4 models.
        - Return a JSON object with a "models" array, e.g. {{"models": ["deepseek-coder", "mistral"]}}
    """).strip()

    raw = ollama_chat(
        MANAGER_MODEL,
        [{"role": "user", "content": prompt}],
        temperature=0.1,
        json_schema=schema,
    )

    try:
        order = json.loads(raw).get("models", [])
        valid = [m for m in order if m in available]
        if valid:
            print(f"[MANAGER] Initial model order: {valid}")
            return valid
    except (json.JSONDecodeError, AttributeError):
        pass

    print("[MANAGER] Could not parse plan; using default model order.")
    return available


# ── Manager: per-iteration routing ────────────────────────────────────────────

def manager_route(
    task: dict,
    available: list[str],
    history: list[dict],
) -> dict:
    """
    After a failure, ask the manager which model to try next and why.

    Sends the last 3 attempts (code, stdout, stderr, evaluator reasoning)
    to the manager so it can make an informed routing decision.

    Args:
        task:      Parsed task dict.
        available: List of available model name strings.
        history:   Full attempt history list; only the last 3 are sent.

    Returns:
        Dict with keys: next_model (str), reason (str), feedback (str).
    """
    schema = {
        "type": "object",
        "properties": {
            "next_model": {"type": "string"},
            "reason":     {"type": "string"},
            "feedback":   {"type": "string"},
        },
        "required": ["next_model", "reason", "feedback"],
    }

    recent = history[-3:]

    # Build history summary using list + join (avoids repeated string copies).
    # Include evaluator reasoning when present — it's higher-quality signal
    # than raw stdout for the manager to diagnose what went wrong.
    history_parts = []
    for h in recent:
        evaluator_note = (
            f"EVALUATOR: {h['evaluator_reason']}"
            if h.get("evaluator_reason")
            else "EVALUATOR: (not run)"
        )
        history_parts.append(textwrap.dedent(f"""
            --- Attempt {h['attempt']} | model: {h['model']} ---
            STDOUT : {h['stdout'] or '(none)'}
            STDERR : {h['stderr'] or '(none)'}
            {evaluator_note}
            CODE (first 40 lines):
            {chr(10).join(h['code'].splitlines()[:40])}
        """))
    history_text = "".join(history_parts)

    model_list = ", ".join(available)
    prompt = textwrap.dedent(f"""
        You are managing a code-generation pipeline. The last attempt failed.
        Choose which model should attempt next and write precise fixing feedback.

        TASK:
        {task['task']}

        EXPECTED OUTPUT:
        {task['expected_output']}

        AVAILABLE MODELS: {model_list}

        RECENT ATTEMPTS:
        {history_text.strip()}

        Return JSON:
        {{
          "next_model": "<one of the available model names>",
          "reason": "<why you chose this model>",
          "feedback": "<concrete bullet-point fixes for the next coder>"
        }}
    """).strip()

    raw = ollama_chat(
        MANAGER_MODEL,
        [{"role": "user", "content": prompt}],
        temperature=0.2,
        json_schema=schema,
    )

    try:
        result = json.loads(raw)
        if result.get("next_model") not in available:
            result["next_model"] = available[0]
        return result
    except (json.JSONDecodeError, AttributeError):
        return {
            "next_model": available[0],
            "reason":     "Could not parse manager response; defaulting.",
            "feedback":   "",
        }


# ── Evaluator ─────────────────────────────────────────────────────────────────

def evaluator_judge(
    task: dict,
    code: str,
    stdout: str,
    stderr: str,
    model: str,
) -> tuple[bool, str]:
    """
    Use an LLM to semantically evaluate whether the script output satisfies
    the task requirements. Replaces (or supplements) exact string matching.

    The evaluator receives the full execution context — task description,
    expected output, generated code, stdout, and stderr — because:
        - stdout alone can look correct while the code is brittle
        - stderr tracebacks are an automatic failure signal
        - expected_output may be a reference, not a required exact match

    Args:
        task:   Parsed task dict.
        code:   The generated Python source code.
        stdout: Captured stdout from running the code.
        stderr: Captured stderr from running the code.
        model:  Ollama model name to use as the judge.

    Returns:
        (passed: bool, reasoning: str)
        passed=False if JSON parsing fails (fail-safe default).
    """
    schema = {
        "type": "object",
        "properties": {
            "passed": {
                "type": "boolean",
                "description": (
                    "True if the output meets all core semantic requirements "
                    "of the task. False otherwise."
                ),
            },
            "reasoning": {
                "type": "string",
                "description": (
                    "Concise explanation of why the output passed or failed, "
                    "noting any specific discrepancies."
                ),
            },
        },
        "required": ["passed", "reasoning"],
    }

    system_prompt = (
        "You are an objective QA automation judge. Evaluate whether the actual "
        "output of a generated Python script satisfies the stated task requirements.\n\n"
        "Guidelines:\n"
        "- Prioritise semantic correctness over exact formatting.\n"
        "- Ignore trivial differences like trailing whitespace or newline counts "
        "unless the task explicitly requires them.\n"
        "- If STDERR contains a Python traceback or crash, the evaluation MUST fail.\n"
        "- You must output only valid JSON matching the requested schema."
    )

    # Build the grading rubric section.
    # REQUIREMENTS (natural-language) takes priority as the primary rubric when
    # present. EXPECTED_OUTPUT is included as a reference in either case, but
    # when only EXPECTED_OUTPUT exists it becomes the definitive pass criterion.
    rubric_parts = []
    if task.get("requirements"):
        rubric_parts.append(f"REQUIREMENTS (grade strictly against these):\n{task['requirements']}")
    if task.get("expected_output"):
        label = "EXPECTED OUTPUT (reference only)" if task.get("requirements") else "EXPECTED OUTPUT (pass criterion)"
        rubric_parts.append(f"{label}:\n{task['expected_output']}")
    rubric = "\n\n".join(rubric_parts) if rubric_parts else "(no rubric provided — use your best judgement)"

    user_content = (
        f"TASK DESCRIPTION:\n{task['task']}\n\n"
        f"{rubric}\n\n"
        f"GENERATED CODE:\n{code}\n\n"
        f"ACTUAL STDOUT:\n{stdout or '(no stdout)'}\n\n"
        f"ACTUAL STDERR:\n{stderr or '(no stderr)'}\n"
    )

    raw = ollama_chat(
        model,
        [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ],
        temperature=0.1,  # low temperature for deterministic grading
        json_schema=schema,
    )

    try:
        result = json.loads(raw)
        return bool(result.get("passed", False)), result.get("reasoning", "No reasoning provided.")
    except (json.JSONDecodeError, TypeError, AttributeError) as exc:
        return False, f"Evaluator failed to produce valid JSON. Error: {exc}. Raw: {raw}"


# ── Code extraction ────────────────────────────────────────────────────────────

def _extract_code(response: str) -> str:
    """
    Pull pure Python out of a model response regardless of formatting.

    Dispatcher that tries three strategies in priority order:
        1. Last ```python ... ``` or ``` ... ``` fenced block
        2. Prose-stripped line-scoring heuristic (handles conversational models)
        3. Highest-scoring paragraph in the full response (last resort)

    Returns an empty string if nothing plausible is found.
    """
    text = response.strip()

    # Strategy 1: fenced code blocks — most reliable, try first.
    result = _extract_fenced(text)
    if result:
        return result

    # Strategy 2: prose-stripped heuristic — handles models (e.g. Qwen, Mistral)
    # that include a line like "Here is the code:\n\nimport sys\n..." before code.
    result = _extract_prose_heuristic(text)
    if result:
        return result

    # Strategy 3: paragraph scoring — last resort when the response has no
    # clear code start, but one paragraph scores highly on the code-line ratio.
    return _extract_best_paragraph(text)


def _extract_fenced(text: str) -> str:
    """
    Extract code from the last ```python ... ``` or ``` ... ``` fence.

    Returns the stripped block content, or empty string if none found.
    """
    fenced = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if fenced:
        return fenced[-1].strip()
    return ""


def _extract_prose_heuristic(text: str) -> str:
    """
    Strip leading prose and return the code-looking remainder.

    Scans lines top-to-bottom, discarding clearly prose lines until a
    code-looking line is found. Then scores the remaining block: if at
    least 50% of non-blank lines look like Python, returns it.

    The 50% threshold is intentionally lenient because we've already
    removed leading prose — the remaining block is expected to be mostly code.
    """
    lines = text.splitlines()

    code_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if _CODE_LINE.match(line):
            code_start = i
            break
        if _PROSE_LINE.match(stripped):
            continue
        # Ambiguous non-empty, non-prose line — stop discarding here
        code_start = i
        break

    candidate_lines = lines[code_start:]
    if not candidate_lines:
        return ""

    non_blank = [l for l in candidate_lines if l.strip()]
    if not non_blank:
        return ""

    code_lines = sum(1 for l in non_blank if _CODE_LINE.match(l))
    score = code_lines / len(non_blank)

    if score >= 0.5:
        return "\n".join(candidate_lines).strip()

    return ""


def _extract_best_paragraph(text: str) -> str:
    """
    Score every double-newline-separated paragraph and return the best.

    Uses a stricter 60% threshold than _extract_prose_heuristic because
    no prose stripping has been done — the whole response is fair game,
    so we need higher confidence to avoid returning prose as code.

    Returns the best paragraph, or empty string if none reaches threshold.
    """
    paragraphs = re.split(r"\n{2,}", text)
    best_para, best_score = "", 0.0

    for para in paragraphs:
        para_lines = [l for l in para.splitlines() if l.strip()]
        if not para_lines:
            continue
        s = sum(1 for l in para_lines if _CODE_LINE.match(l)) / len(para_lines)
        # Prefer higher score; break ties by length (longer = more complete code)
        if s > best_score or (s == best_score and len(para) > len(best_para)):
            best_score, best_para = s, para

    if best_score >= 0.6:
        return best_para.strip()

    return ""


# ── Code generation ────────────────────────────────────────────────────────────

def generate_code(model: str, task: dict, history: list[dict], feedback: str = "") -> str:
    """
    Ask a coder model to generate (or repair) a Python script.

    Sends the last 3 failed attempts (code, stdout, stderr) so the model
    can learn from prior mistakes. Also forwards any structured feedback
    from the manager.

    Args:
        model:    Coder model name.
        task:     Parsed task dict.
        history:  Full attempt history; last 3 are included in the prompt.
        feedback: Manager-provided bullet-point feedback from the previous round.

    Returns:
        Extracted Python source code string, or "" if the model response
        contained nothing recognisable as code.
    """
    recent = history[-3:]

    # Build prior-attempt block using list + join (avoids O(n^2) string concat)
    prior_parts = []
    for h in recent:
        prior_parts.append(textwrap.dedent(f"""
            ### Attempt {h['attempt']} (by {h['model']})
            ```python
            {h['code']}
            ```
            stdout : {h['stdout'] or '(none)'}
            stderr : {h['stderr'] or '(none)'}
        """))
    prior_attempts = "".join(prior_parts)

    system = (
        "You are an expert Python programmer. "
        "Produce a single, complete, immediately runnable Python script. "
        "You may wrap it in a ```python ... ``` code block if you wish."
    )

    user_parts = [f"TASK:\n{task['task']}"]

    # Give the coder the most relevant success criteria available.
    # If REQUIREMENTS are defined, those take priority — the coder should
    # understand what it means to satisfy them, not just match a string.
    if task.get("requirements"):
        user_parts.append(f"REQUIREMENTS (your output must satisfy all of these):\n{task['requirements']}")
    if task.get("expected_output"):
        label = "EXAMPLE OUTPUT (for reference)" if task.get("requirements") else "EXPECTED OUTPUT (match exactly after strip)"
        user_parts.append(f"{label}:\n{task['expected_output']}")
    if task["input_data"]:
        user_parts.append(f"INPUT (provided via stdin):\n{task['input_data']}")
    if task["inline_tests"]:
        tests = "\n".join(task["inline_tests"])
        user_parts.append(f"INLINE TESTS (must all pass):\n{tests}")
    if prior_attempts:
        user_parts.append(
            f"PRIOR FAILED ATTEMPTS (do not repeat these mistakes):\n{prior_attempts.strip()}"
        )
    if feedback:
        user_parts.append(f"REVIEWER FEEDBACK (fix these issues):\n{feedback}")

    user = "\n\n".join(user_parts)

    response = ollama_chat(
        model,
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.3,
    )

    return _extract_code(response)


# ── Artefact persistence ───────────────────────────────────────────────────────

def save_attempt(
    output_dir: Path,
    fail_count: int,
    code: str,
    stdout: str,
    stderr: str,
    feedback: str,
    model: str,
    evaluator_result: dict | None = None,
) -> None:
    """
    Save all artefacts for one failed attempt into attempts/NNN/.

    Creates:
        attempts/NNN/code.py
        attempts/NNN/stdout.txt
        attempts/NNN/stderr.txt
        attempts/NNN/manager_feedback.txt
        attempts/NNN/model.txt
        attempts/NNN/evaluator.json   (if evaluator_result is provided)

    The evaluator JSON is stored separately so pipeline behavior can be
    diagnosed by replaying what the evaluator saw and decided.

    Args:
        output_dir:        Root output directory (Path object).
        fail_count:        Attempt number, used to name the subdirectory.
        code:              Generated Python source.
        stdout:            Captured stdout.
        stderr:            Captured stderr.
        feedback:          Manager feedback string for this attempt.
        model:             Name of the model that generated the code.
        evaluator_result:  Optional dict from evaluator_judge for logging.
    """
    attempt_dir = output_dir / "attempts" / f"{fail_count:03d}"
    attempt_dir.mkdir(parents=True, exist_ok=True)

    (attempt_dir / "code.py").write_text(code)
    (attempt_dir / "stdout.txt").write_text(stdout)
    (attempt_dir / "stderr.txt").write_text(stderr)
    (attempt_dir / "manager_feedback.txt").write_text(feedback)
    (attempt_dir / "model.txt").write_text(model)

    if evaluator_result:
        (attempt_dir / "evaluator.json").write_text(
            json.dumps(evaluator_result, indent=2)
        )

    print(f"[SAVED]  attempts/{fail_count:03d}/")


def save_success(code: str, output_dir: Path, iteration: int, model: str) -> None:
    """
    Write the successful script and print the success banner.

    Args:
        code:       Python source that passed all checks.
        output_dir: Root output directory.
        iteration:  Loop iteration number (for display).
        model:      Model that generated the winning code.
    """
    success_path = output_dir / "success.py"
    success_path.write_text(code)
    print(f"\n{'='*62}")
    print(f"  SUCCESS -- iteration {iteration}, model '{model}'")
    print(f"     {success_path}")
    print(f"{'='*62}\n")


# ── Pipeline helpers ───────────────────────────────────────────────────────────

def _resolve_coder_models(requested: list[str], available: list[str]) -> list[str]:
    """
    Filter the requested model list to those confirmed present on this machine.

    Handles both tagged ('qwen2.5-coder:14b') and untagged ('qwen2.5-coder')
    names because list_ollama_models() returns both forms. A requested name
    matches if it appears in available under either form.

    Args:
        requested: Model names from CLI or DEFAULT_MODELS.
        available: All names returned by list_ollama_models().

    Returns:
        Filtered list, or the original requested list if available is empty
        (Ollama unreachable) or no matches found (with a warning).
    """
    if not available:
        print("[WARN] Could not enumerate Ollama models; using provided names as-is.")
        return requested

    matched = [m for m in requested if m in available]
    if not matched:
        print(f"[WARN] None of {requested} found locally (available: {available}). Using as-is.")
        return requested

    return matched


def _print_task_summary(task: dict) -> None:
    """Print a human-readable summary of the parsed task to stdout."""
    print(f"[TASK]  {task['task'][:80]}{'...' if len(task['task']) > 80 else ''}")
    if task["expected_output"]:
        print(f"[EXPECTED] {repr(task['expected_output'][:60])}")
    if task.get("requirements"):
        preview = task["requirements"][:80].replace("\n", " ")
        ellipsis = "..." if len(task["requirements"]) > 80 else ""
        print(f"[REQUIREMENTS] {preview}{ellipsis}")
    if task["inline_tests"]:
        print(f"[TESTS] {len(task['inline_tests'])} inline assert test(s)")
    if task["test_script"]:
        print(f"[TEST_SCRIPT] {task['test_script']}")


def _handle_failure(
    task: dict,
    fail_count: int,
    record: dict,
    coder_models: list[str],
    history: list[dict],
    output_dir: Path,
) -> tuple[str, dict]:
    """
    Process a failed iteration: route to next model, save artefacts, log output.

    This extracts the dense failure-handling block that previously lived
    inline in the main loop, making the loop itself much easier to read.

    Args:
        task:         Parsed task dict.
        fail_count:   Current failure count (used for directory naming).
        record:       The attempt record for this iteration. Contains code,
                      stdout, stderr, and evaluator_reason. manager_feedback
                      is set here before the record is appended to history.
        coder_models: Available model list for the manager to route within.
        history:      Attempt history accumulated so far (does not yet include record).
        output_dir:   Root output directory for artefact storage.

    Returns:
        (next_model, updated_record) where updated_record has manager_feedback set.
    """
    route = manager_route(task, coder_models, history + [record])
    record["manager_feedback"] = route["feedback"]
    history.append(record)

    # Package evaluator result for disk storage if we have one
    evaluator_result = None
    if record.get("evaluator_reason"):
        evaluator_result = {
            "passed":    False,
            "reasoning": record["evaluator_reason"],
        }

    save_attempt(
        output_dir, fail_count,
        record["code"], record["stdout"], record["stderr"],
        route["feedback"], record["model"],
        evaluator_result,
    )

    print(f"[ITER {record['attempt']:02d}]  FAILED")
    print(f"  expected : {repr(task['expected_output'][:60])}")
    print(f"  got      : {repr(record['stdout'][:60])}")
    if record["stderr"]:
        print(f"  stderr   : {record['stderr'][:120]}")
    if record.get("evaluator_reason"):
        print(f"  evaluator: {record['evaluator_reason'][:120]}")
    print(f"[MANAGER] -> next: '{route['next_model']}'  reason: {route['reason'][:80]}")
    print(f"[MANAGER] feedback: {route['feedback'][:200].replace(chr(10), ' ')}")
    print()

    return route["next_model"], record


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run_pipeline(args: argparse.Namespace) -> None:
    """
    Orchestrate the full code-generation pipeline.

    Pipeline stages:
        1. Parse task file and print summary
        2. Resolve coder models against what's locally available
        3. Manager picks initial model order
        4. Main loop (up to max_iterations):
             a. Generate code with current coder model
             b. Run deterministic tests (test_runner.py)
             c. Run LLM evaluator gate (unless --no-evaluator)
             d. On success: save success.py and exit
             e. On failure: route to next model, save attempt artefacts

    Args:
        args: Parsed argparse.Namespace from main().
    """
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sandbox  = not args.no_sandbox
    timeout  = args.timeout
    use_eval = not args.no_evaluator

    print(f"\n{'='*62}")
    print(f"  Ollama Code-Gen Pipeline  (sandbox={'ON' if sandbox else 'OFF'})")
    if use_eval:
        print(f"  Evaluator: {args.evaluator}")
    print(f"{'='*62}")

    # Stage 1: parse task
    print(f"[TASK]  {args.task_file}")
    task = parse_task_file(args.task_file)
    _print_task_summary(task)

    # Stage 2: resolve coder models
    available    = list_ollama_models()
    requested    = args.models or DEFAULT_MODELS
    coder_models = _resolve_coder_models(requested, available)

    # Stage 3: manager picks initial order
    print(f"\n[MANAGER] '{MANAGER_MODEL}' planning initial route...")
    next_model = manager_plan(task, coder_models)[0]

    # Stage 4: main generation loop.
    # iteration  = total loop passes (includes empty-response skips)
    # fail_count = attempts that produced code but failed tests/evaluation
    iteration  = 0
    fail_count = 0
    history: list[dict] = []

    print(f"\n[PIPELINE] Max {args.max_iterations} iterations  |  Models: {coder_models}\n")

    while iteration < args.max_iterations:
        iteration += 1
        model = next_model
        print(f"[ITER {iteration:02d}]  model={model}")

        # Step 4a: generate
        feedback = history[-1]["manager_feedback"] if history else ""
        code = generate_code(model, task, history, feedback)

        if not code:
            print(f"[ITER {iteration:02d}]  Empty response -- skipping")
            continue

        # Step 4b: deterministic tests.
        # Skipped entirely when the task uses REQUIREMENTS-only mode — there
        # is no EXPECTED_OUTPUT or TEST blocks to check against, so the
        # evaluator is the sole judge.
        requirements_only = bool(task.get("requirements") and not task.get("expected_output")
                                 and not task.get("inline_tests") and not task.get("test_script"))

        if requirements_only:
            # No deterministic checks — run the script directly to capture
            # stdout/stderr for the evaluator. We use subprocess here rather
            # than test_runner internals to avoid coupling to its private API.
            det_success = True   # gate is the evaluator, not this check
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as tmp:
                tmp.write(code)
                tmp_path = tmp.name
            try:
                proc = subprocess.run(
                    ["python3", tmp_path],
                    input=task.get("input_data") or "",
                    capture_output=True, text=True, timeout=timeout,
                )
                stdout, stderr = proc.stdout, proc.stderr
                if proc.returncode != 0:
                    det_success = False  # crash = automatic evaluator fail
            except subprocess.TimeoutExpired:
                stdout, stderr = "", "[TIMEOUT]"
                det_success = False
            finally:
                os.unlink(tmp_path)
        else:
            det_success, stdout, stderr = run_tests(code, task, timeout, sandbox)

        # Step 4c: LLM evaluator gate.
        # Runs when deterministic tests pass (or there are none).
        # In requirements-only mode the evaluator is the sole pass/fail gate.
        # The evaluator's reasoning is stored in the record so the manager
        # receives it as richer signal than raw stdout on the next failure.
        evaluator_passed = False
        evaluator_reason = ""

        if det_success and use_eval:
            evaluator_passed, evaluator_reason = evaluator_judge(
                task, code, stdout, stderr, args.evaluator
            )
            if evaluator_passed:
                print(f"[EVALUATOR OK] {evaluator_reason[:100]}")
            else:
                print(f"[EVALUATOR FAIL] {evaluator_reason[:100]}")
        elif det_success and not use_eval:
            # No evaluator gate requested — deterministic pass is sufficient
            evaluator_passed = True

        # NOTE: record is constructed here but manager_feedback is intentionally
        # left empty. It is populated inside _handle_failure after the manager
        # has been consulted. This two-phase mutation is necessary because we
        # need to pass the record to the manager before we know the feedback.
        record: dict = {
            "attempt":          fail_count + 1,
            "model":            model,
            "code":             code,
            "stdout":           stdout,
            "stderr":           stderr,
            "manager_feedback": "",
            "evaluator_reason": evaluator_reason,
        }

        # Step 4d: success path
        if evaluator_passed:
            save_success(code, output_dir, iteration, model)
            return

        # Step 4e: failure path
        fail_count += 1
        next_model, _ = _handle_failure(
            task, fail_count, record, coder_models, history, output_dir
        )

    print(f"\n[PIPELINE] Reached max iterations ({args.max_iterations}) -- no success.")
    print(f"[PIPELINE] Artefacts in: {output_dir}/attempts/")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    """Parse CLI arguments and launch the pipeline."""
    global MANAGER_MODEL, EVALUATOR_MODEL

    parser = argparse.ArgumentParser(
        description="Multi-model Ollama code-generation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("task_file",
                        help="Path to task definition file")
    parser.add_argument("--output-dir", "-o", default=DEFAULT_OUTPUT_DIR,
                        help="Output directory (default: .)")
    parser.add_argument("--max-iterations", "-n", type=int, default=DEFAULT_MAX_ITER,
                        help=f"Max attempts (default: {DEFAULT_MAX_ITER})")
    parser.add_argument("--models", "-m", nargs="+",
                        help="Coder models (overrides defaults)")
    parser.add_argument("--manager", default=MANAGER_MODEL,
                        help=f"Manager model (default: {MANAGER_MODEL})")
    parser.add_argument("--evaluator", default=EVALUATOR_MODEL,
                        help=f"Evaluator model (default: {EVALUATOR_MODEL})")
    parser.add_argument("--timeout", type=int, default=SCRIPT_TIMEOUT,
                        help=f"Script execution timeout in seconds (default: {SCRIPT_TIMEOUT})")
    parser.add_argument("--no-sandbox", action="store_true",
                        help="Disable dangerous-import check (use only with trusted tasks)")
    parser.add_argument("--no-evaluator", action="store_true",
                        help="Skip LLM evaluation gate; rely only on deterministic tests")

    args = parser.parse_args()
    MANAGER_MODEL   = args.manager
    EVALUATOR_MODEL = args.evaluator

    run_pipeline(args)


if __name__ == "__main__":
    main()