import os
import shutil
import platform
import json
import tarfile
import zipfile

TOOL_ID = "tool-dev-notes-summarizer"
VERSION = "1.0.0"

SRC = "executas/notes-summarizer"
DIST = "dist"

def detect_platform():
    sys = platform.system().lower()
    arch = platform.machine().lower()

    if sys == "darwin":
        if "arm" in arch:
            return "darwin-arm64"
        return "darwin-x86_64"

    if sys == "windows":
        return "windows-x86_64"

    raise Exception("unsupported platform")

def build_tree():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)

    root = os.path.join(DIST, TOOL_ID)
    os.makedirs(os.path.join(root, "bin"), exist_ok=True)

    # copy tool.py → bin/
    shutil.copy(
        os.path.join(SRC, "tool.py"),
        os.path.join(root, "bin", "tool.py")
    )

    manifest = {
        "name": TOOL_ID,
        "version": VERSION,
        "runtime": {
            "binary": {
                "entrypoint": {
                    "default": "bin/tool.py",
                    "windows-x86_64": "bin/tool.py"
                },
                "permissions": {
                    "bin/tool.py": "0o755"
                }
            }
        }
    }

    with open(os.path.join(root, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    return root

def pack(root):
    platform_key = detect_platform()
    base = f"{TOOL_ID}-{VERSION}-{platform_key}"
    out_dir = "release"

    os.makedirs(out_dir, exist_ok=True)

    if platform_key.startswith("windows"):
        out_path = shutil.make_archive(
            os.path.join(out_dir, base),
            "zip",
            root
        )
    else:
        out_path = shutil.make_archive(
            os.path.join(out_dir, base),
            "gztar",
            root
        )

    return out_path

if __name__ == "__main__":
    root = build_tree()
    out = pack(root)

    print("build success:", out)