import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from importlib.util import find_spec


TOOL_ID = "tool-dev-notes-summarizer"
VERSION = "1.0.0"
TOOL_SOURCE = Path("executas/notes-summarizer/tool.py")
BUILD_DIR = Path("dist/executa-binary")
RELEASE_DIR = Path("release")

SUPPORTED_PLATFORMS = {
    ("darwin", "arm64"): "darwin-arm64",
    ("darwin", "aarch64"): "darwin-arm64",
    ("darwin", "x86_64"): "darwin-x86_64",
    ("darwin", "amd64"): "darwin-x86_64",
    ("windows", "x86_64"): "windows-x86_64",
    ("windows", "amd64"): "windows-x86_64",
}


def detect_platform():
    system = platform.system().lower()
    machine = platform.machine().lower()
    key = SUPPORTED_PLATFORMS.get((system, machine))
    if not key:
        supported = ", ".join(sorted(set(SUPPORTED_PLATFORMS.values())))
        raise RuntimeError(
            f"unsupported platform: system={system!r}, arch={machine!r}; "
            f"supported platform keys: {supported}"
        )
    return key


def executable_name(platform_key):
    return f"{TOOL_ID}.exe" if platform_key.startswith("windows") else TOOL_ID


def require_pyinstaller():
    if find_spec("PyInstaller") is None:
        raise RuntimeError(
            "PyInstaller is required to build a standalone Executa binary. "
            "Install it in the build environment, for example: "
            "python -m pip install pyinstaller"
        )


def clean_path(path):
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def run_pyinstaller(platform_key):
    require_pyinstaller()
    if not TOOL_SOURCE.exists():
        raise FileNotFoundError(f"missing Executa source: {TOOL_SOURCE}")

    exe_name = executable_name(platform_key)
    work_dir = BUILD_DIR / "pyinstaller-work" / platform_key
    spec_dir = BUILD_DIR / "pyinstaller-spec" / platform_key
    pyinstaller_dist = BUILD_DIR / "pyinstaller-dist" / platform_key

    clean_path(work_dir)
    clean_path(spec_dir)
    clean_path(pyinstaller_dist)
    work_dir.mkdir(parents=True, exist_ok=True)
    spec_dir.mkdir(parents=True, exist_ok=True)
    pyinstaller_dist.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--name",
        TOOL_ID,
        "--distpath",
        str(pyinstaller_dist),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(spec_dir),
        str(TOOL_SOURCE),
    ]
    subprocess.run(cmd, check=True)

    built = pyinstaller_dist / exe_name
    if not built.exists():
        raise FileNotFoundError(f"PyInstaller did not create expected binary: {built}")

    archive_root = BUILD_DIR / "archive-root" / platform_key
    clean_path(archive_root)
    bin_dir = archive_root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / exe_name
    shutil.copy2(built, target)
    if not platform_key.startswith("windows"):
        target.chmod(0o755)

    return archive_root, f"bin/{exe_name}"


def write_binary_manifest(archive_root, platform_key, entrypoint):
    manifest = {
        "name": TOOL_ID,
        "tool_id": TOOL_ID,
        "version": VERSION,
        "platform": platform_key,
        "runtime": {
            "binary": {
                "entrypoint": {
                    "default": entrypoint,
                    platform_key: entrypoint,
                },
                "permissions": {
                    entrypoint: "0o755",
                },
            },
        },
    }
    manifest_path = archive_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def iter_archive_files(root):
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path, path.relative_to(root).as_posix()


def make_tar_gz(root, out_path, executable_rel):
    with tarfile.open(out_path, "w:gz") as archive:
        for path, rel in iter_archive_files(root):
            info = archive.gettarinfo(str(path), arcname=rel)
            info.mode = 0o755 if rel == executable_rel else 0o644
            with path.open("rb") as fh:
                archive.addfile(info, fh)


def make_zip(root, out_path, executable_rel):
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, rel in iter_archive_files(root):
            info = zipfile.ZipInfo(rel)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if rel == executable_rel else 0o644
            info.external_attr = (mode & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pack_archive(archive_root, platform_key, entrypoint):
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    base = f"{TOOL_ID}-{VERSION}-{platform_key}"

    if platform_key.startswith("windows"):
        out_path = RELEASE_DIR / f"{base}.zip"
        make_zip(archive_root, out_path, entrypoint)
        archive_format = "zip"
    else:
        out_path = RELEASE_DIR / f"{base}.tar.gz"
        make_tar_gz(archive_root, out_path, entrypoint)
        archive_format = "tar.gz"

    return {
        "platform": platform_key,
        "format": archive_format,
        "archive": str(out_path),
        "entrypoint": entrypoint,
        "sha256": sha256_file(out_path),
        "size": out_path.stat().st_size,
    }


def build():
    platform_key = detect_platform()
    archive_root, entrypoint = run_pyinstaller(platform_key)
    write_binary_manifest(archive_root, platform_key, entrypoint)
    return pack_archive(archive_root, platform_key, entrypoint)


def main():
    parser = argparse.ArgumentParser(
        description="Build the current-platform Anna Executa binary archive."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    args = parser.parse_args()

    result = build()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"build success: {result['archive']}")
        print(f"platform: {result['platform']}")
        print(f"format: {result['format']}")
        print(f"entrypoint: {result['entrypoint']}")
        print(f"sha256: {result['sha256']}")
        print(f"size: {result['size']}")


if __name__ == "__main__":
    main()
