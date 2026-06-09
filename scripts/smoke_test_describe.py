#!/usr/bin/env python3
"""
smoke_test_describe.py — verify that a compiled Executa binary responds to `describe` RPC.

Usage:
  python scripts/smoke_test_describe.py <binary_path>

Example:
  python scripts/smoke_test_describe.py dist/executa-binary/archive-root/windows-x86_64/bin/tool-dev-notes-summarizer.exe
"""

import json
import subprocess
import sys


def smoke_test(binary_path):
    """Run the binary, send describe JSON-RPC, and verify the response."""
    try:
        proc = subprocess.Popen(
            [binary_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Send describe request
        req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "describe"})
        print(f"[smoke_test] sending: {req}", file=sys.stderr)

        proc.stdin.write(req + "\n")
        proc.stdin.flush()

        # Read response
        response_line = proc.stdout.readline()
        if not response_line:
            print("[smoke_test] ERROR: no response from binary", file=sys.stderr)
            proc.terminate()
            return False

        print(f"[smoke_test] received: {response_line}", file=sys.stderr)

        try:
            response = json.loads(response_line)
        except json.JSONDecodeError as e:
            print(f"[smoke_test] ERROR: invalid JSON response: {e}", file=sys.stderr)
            proc.terminate()
            return False

        # Verify structure
        if not isinstance(response, dict):
            print("[smoke_test] ERROR: response is not a dict", file=sys.stderr)
            proc.terminate()
            return False

        if response.get("id") != 1:
            print(f"[smoke_test] ERROR: expected id=1, got id={response.get('id')}", file=sys.stderr)
            proc.terminate()
            return False

        if "result" not in response:
            print(f"[smoke_test] ERROR: no 'result' in response", file=sys.stderr)
            proc.terminate()
            return False

        manifest = response.get("result", {})
        if not isinstance(manifest, dict):
            print("[smoke_test] ERROR: result is not a dict", file=sys.stderr)
            proc.terminate()
            return False

        # Check required manifest fields
        required_fields = ["name", "display_name", "version", "host_capabilities", "tools"]
        for field in required_fields:
            if field not in manifest:
                print(f"[smoke_test] ERROR: manifest missing '{field}'", file=sys.stderr)
                proc.terminate()
                return False

        # Verify host_capabilities includes "llm.sample"
        host_caps = manifest.get("host_capabilities", [])
        if "llm.sample" not in host_caps:
            print(f"[smoke_test] ERROR: 'llm.sample' not in host_capabilities: {host_caps}", file=sys.stderr)
            proc.terminate()
            return False

        print("[smoke_test] ✓ describe RPC successful", file=sys.stderr)
        print(f"[smoke_test] manifest name: {manifest.get('name')}", file=sys.stderr)
        print(f"[smoke_test] manifest version: {manifest.get('version')}", file=sys.stderr)

        proc.terminate()
        return True

    except Exception as e:
        print(f"[smoke_test] ERROR: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <binary_path>", file=sys.stderr)
        sys.exit(1)

    binary_path = sys.argv[1]
    success = smoke_test(binary_path)
    sys.exit(0 if success else 1)
