import argparse
from pathlib import Path
import time

# Constants and default values
OLLAMA_BASE_URL    = "http://localhost:11434"
DEFAULT_MAX_ITER   = 20
DEFAULT_OUTPUT_DIR = "."
MANAGER_MODEL      = "llama3"
DEFAULT_MODELS     = ["deepseek-coder", "codellama", "mistral","qwen2.5-coder","starcoder2","deepseek-coder-v2"]
SCRIPT_TIMEOUT     = 15

# Helper functions
def list_ollama_models():
    """Simulate listing available Ollama models."""
    return DEFAULT_MODELS  # Replace with actual model enumeration

def ollama_chat(model, messages):
    """Simulate a chat with an Ollama model."""
    # Replace this with actual interaction with the model
    if model == MANAGER_MODEL:
        return "Initial route from manager"
    elif model in DEFAULT_MODELS:
        return "Generated code snippet"

def run_tests(code, task, timeout, sandbox):
    """Simulate running tests on generated code using codestral:22b."""
    # Replace this with actual test execution using codestral:22b
    if task['expected_output'] == code.strip():
        return True, task['expected_output'], ""
    else:
        return False, code.strip(), "Test failed"

# Parsing the task file
def parse_task_file(file_path):
    """Parse a task definition file."""
    with open(file_path, 'r') as file:
        content = file.read()
    # Simulate parsing (replace with actual logic)
    return {
        'task': content,
        'expected_output': "Expected output",
        'inline_tests': ["assert code == expected_output"],
        'test_script': "path_to_test_script.py"
    }

# Saving attempt results
def save_attempt(output_dir, fail_count, code, stdout, stderr, feedback, model):
    """Save artefacts for one failed attempt into attempts/NNN/."""
    # Replace this with actual saving logic
    print(f"Saved attempt {fail_count}")

# Running the pipeline
def run_pipeline(args):
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sandbox = not args.no_sandbox
    timeout = args.timeout

    print(f"\n{'═'*62}")
    print(f"  Ollama Code-Gen Pipeline  (sandbox={'ON' if sandbox else 'OFF'})")
    print(f"{'═'*62}")

    # Parsing task file
    print(f"[TASK]  {args.task_file}")
    task = parse_task_file(args.task_file)
    print(f"[TASK]  {task['task'][:80]}{'…' if len(task['task']) > 80 else ''}")
    if task["expected_output"]:
        print(f"[EXPECTED] {repr(task['expected_output'][:60])}")
    if task["inline_tests"]:
        print(f"[TESTS] {len(task['inline_tests'])} inline assert test(s)")
    if task["test_script"]:
        print(f"[TEST_SCRIPT] {task['test_script']}")

    # Resolving coder models
    available = list_ollama_models()
    requested = args.models or DEFAULT_MODELS
    if available:
        coder_models = [m for m in requested if m in available]
        if not coder_models:
            print(f"[WARN] None of {requested} found locally (available: {available}). Using as-is.")
            coder_models = requested
    else:
        print("[WARN] Could not enumerate Ollama models; using provided names.")
        coder_models = requested

    # Manager picks initial order
    print(f"\n[MANAGER] '{MANAGER_MODEL}' planning initial route…")
    next_model = manager_plan(task, coder_models)[0]

    # Iterative generation loop
    iteration  = 0   # total loop counter (includes skipped empty responses)
    fail_count = 0   # files actually written
    history: list[dict] = []   # rich history passed to models and manager

    print(f"\n[PIPELINE] Max {args.max_iterations} iterations  |  Models: {coder_models}\n")

    while iteration < args.max_iterations:
        iteration += 1
        model = next_model
        print(f"[ITER {iteration:02d}]  model={model}")

        # Generate code
        feedback = history[-1]["manager_feedback"] if history else ""
        code = generate_code(model, task, history, feedback)

        if not code:
            print(f"[ITER {iteration:02d}]  Empty response — skipping (iteration counter does not advance file count)")
            continue

        # Test
        success, stdout, stderr = run_tests(code, task, timeout, sandbox)

        # Record in history regardless of outcome
        record = {
            "attempt": fail_count + 1,
            "model":   model,
            "code":    code,
            "stdout":  stdout,
            "stderr":  stderr,
            "manager_feedback": "",
        }

        if success:
            success_path = output_dir / "success.py"
            success_path.write_text(code)
            print(f"\n{'═'*62}")
            print(f"  ✓  SUCCESS — iteration {iteration}, model '{model}'")
            print(f"     {success_path}")
            print(f"{'═'*62}\n")
            return

        # Failure path
        fail_count += 1
        route = manager_route(task, coder_models, history + [record])
        record["manager_feedback"] = route["feedback"]
        history.append(record)

        save_attempt(output_dir, fail_count, code, stdout, stderr, route["feedback"], model)

        print(f"[ITER {iteration:02d}]  FAILED")
        print(f"  expected : {repr(task['expected_output'][:60])}")
        print(f"  got      : {repr(stdout[:60])}")
        if stderr:
            print(f"  stderr   : {stderr[:120]}")
        print(f"[MANAGER] → next: '{route['next_model']}'  reason: {route['reason'][:80]}")
        print(f"[MANAGER] feedback: {route['feedback'][:200].replace(chr(10), ' ')}")
        print()

        next_model = route["next_model"]

    print(f"\n[PIPELINE] Reached max iterations ({args.max_iterations}) — no success.")
    print(f"[PIPELINE] Artefacts in: {output_dir}/attempts/")

# Main function
def main():
    parser = argparse.ArgumentParser(
        description="Multi-model Ollama code-generation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("task_file", help="Path to task definition file")
    parser.add_argument("--output-dir", "-o", default=DEFAULT_OUTPUT_DIR,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--max-iterations", "-n", type=int, default=DEFAULT_MAX_ITER,
                        help=f"Max attempts (default: {DEFAULT_MAX_ITER})")
    parser.add_argument("--models", "-m", nargs="+",
                        help="Coder models (overrides defaults)")
    parser.add_argument("--manager", default=MANAGER_MODEL,
                        help=f"Manager model (default: {MANAGER_MODEL})")
    parser.add_argument("--timeout", type=int, default=SCRIPT_TIMEOUT,
                        help=f"Script execution timeout in seconds (default: {SCRIPT_TIMEOUT})")
    parser.add_argument("--no-sandbox", action="store_true",
                        help="Disable dangerous-import check (use only with trusted tasks)")

    args = parser.parse_args()

    run_pipeline(args)

if __name__ == "__main__":
    main()