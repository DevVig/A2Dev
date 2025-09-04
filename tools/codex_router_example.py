"""
Codex Web/IDE preprocessor example.

Usage: integrate this script as a message preprocessor in your Codex harness.
If a message starts with @analyst/@pm/@dev/@spm or *command, route it to
`python3 a2dev_cli.py route "<message>"` and surface the CLI output.
Otherwise, pass the message through unchanged.
"""

import os
import subprocess
import sys


def main():
    msg = sys.stdin.read().strip()
    if not msg:
        print("")
        return
    triggers = ("@analyst", "@pm", "@dev", "@spm", "*")
    if msg.lower().startswith(triggers):
        # Prefer Node wrapper (a2dev); fallback to Python shim if unavailable
        try:
            cmd = ["a2dev", "route", msg]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError("a2dev returned non-zero")
        except Exception:
            cmd = [sys.executable or "python3", "a2dev_cli.py", "route", msg]
            proc = subprocess.run(cmd, capture_output=True, text=True)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        return
    # default: echo the original message (no routing)
    print(msg)


if __name__ == "__main__":
    main()
