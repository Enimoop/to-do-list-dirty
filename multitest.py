import re
import subprocess
import sys
from pathlib import Path

PYTHON_TARGETS = ["3.13", "3.9", "2.7"]
DJANGO_VERSIONS = ["5.0", "4.2", "3.2"]

ROOT = Path(__file__).resolve().parent
PIPFILE = ROOT / "Pipfile"


def run(cmd, env=None):
    print("$ " + " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT, env=env)


def get_actual_python(env=None):
    try:
        out = subprocess.check_output(
            ["python", "-c", "import sys; print(sys.version.split()[0])"],
            cwd=ROOT,
            env=env,
            text=True,
        )
        return out.strip()
    except Exception:
        return "unknown"


def patch_pipfile_python_version(target_version: str):
    """Replace python_version in Pipfile while keeping a backup."""
    content = PIPFILE.read_text(encoding="utf-8")
    backup = content

    # replace line: python_version = "X.Y"
    new_content, n = re.subn(
        r'python_version\s*=\s*"[0-9]+\.[0-9]+"',
        f'python_version = "{target_version}"',
        content,
    )

    if n == 0:
        # if missing, add under [requires]
        if "[requires]" not in content:
            new_content += f'\n[requires]\npython_version = "{target_version}"\n'
        else:
            new_content = re.sub(
                r"(\[requires\]\s*)",
                r"\1\npython_version = \"" + target_version + "\"\n",
                content,
                count=1,
            )

    PIPFILE.write_text(new_content, encoding="utf-8")
    return backup


def restore_pipfile(backup: str):
    PIPFILE.write_text(backup, encoding="utf-8")


def main():
    if not PIPFILE.exists():
        print("❌ Pipfile not found at project root.")
        sys.exit(1)

    print("=== SIMULATED MATRIX TEST START ===")

    original = PIPFILE.read_text(encoding="utf-8")

    try:
        for py_target in PYTHON_TARGETS:
            print(f"\n=== Target Python {py_target} (simulated via Pipfile) ===")

            # patch Pipfile python_version
            backup = patch_pipfile_python_version(py_target)

            for dj in DJANGO_VERSIONS:
                venv_name = f"todolist-py{py_target}-dj{dj}".replace(".", "_")

                env = dict(**os.environ)
                env["PIPENV_CUSTOM_VENV_NAME"] = venv_name
                env["PIPENV_IGNORE_VIRTUALENVS"] = "1"

                print(f"\n  → Django {dj} on target Python {py_target}")
                print(f"    (pipenv venv name: {venv_name})")

                # clean previous env for this combo if exists
                run(["python", "-m", "pipenv", "--rm"], env=env)

                # install targeted Django
                rc = run(
                    ["python", "-m", "pipenv", "install", f"django=={dj}", "--skip-lock"],
                    env=env,
                )
                if rc != 0:
                    print("    ❌ install failed, skipping tests")
                    continue

                print(f"    ✅ Target Python: {py_target}")

                # run tests
                rc = run(
                    ["python", "-m", "pipenv", "run", "python", "manage.py", "test"],
                    env=env,
                )
                if rc == 0:
                    print("    ✅ tests OK")
                else:
                    print("    ❌ tests FAILED")

            restore_pipfile(backup)

    finally:
        restore_pipfile(original)

    print("\n=== SIMULATED MATRIX TEST END ===")


if __name__ == "__main__":
    import os
    main()
