import os
import platform
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

NAME = "SerialPortIdentifier"
DIST = Path("dist")
RELEASE = Path("release")

# "binary" is the PyInstaller output in dist/, "archive" the format of the
# file published in release/ (None: the binary is published as is).
PLATFORMS = {
    "linux": {"os": "linux", "mode": "--onefile",
              "binary": NAME, "archive": "tar.gz"},
    "win32": {"os": "windows", "mode": "--onefile",
              "binary": f"{NAME}.exe", "archive": None},
    # "darwin": {"os": "macos", "mode": "--onedir",
    #            "binary": f"{NAME}.app", "archive": "zip"},
}

ARCHS = {"x86_64": "x64", "amd64": "x64", "aarch64": "arm64", "arm64": "arm64"}


def version():
    """Tag name (e.g. v1.0.0) on a tag build, 'dev' otherwise."""
    if os.environ.get("GITHUB_REF_TYPE") == "tag":
        return os.environ["GITHUB_REF_NAME"]
    return "dev"


def arch():
    machine = platform.machine().lower()
    return ARCHS.get(machine, machine)


def build(cfg):
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        cfg["mode"],
        f"--add-data=serial.png{os.pathsep}.",
        "--icon=serial.png",
        f"{NAME}.py",
    ]
    print(f"Command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def package(cfg):
    binary = DIST / cfg["binary"]
    base = f"{NAME}-{version()}-{cfg['os']}-{arch()}"

    shutil.rmtree(RELEASE, ignore_errors=True)
    RELEASE.mkdir()

    if cfg["archive"] == "tar.gz":
        dest = RELEASE / f"{base}.tar.gz"
        with tarfile.open(dest, "w:gz") as tar:
            tar.add(binary, arcname=binary.name)
    elif cfg["archive"] == "zip":
        # ditto keeps the metadata of the macOS .app bundle.
        dest = RELEASE / f"{base}.zip"
        subprocess.run(["ditto", "-c", "-k", "--keepParent",
                        str(binary), str(dest)], check=True)
    else:
        dest = RELEASE / f"{base}{binary.suffix}"
        shutil.copy2(binary, dest)

    print(f"Package: {dest}")


def main():
    cfg = PLATFORMS.get(sys.platform)
    if cfg is None:
        sys.exit(f"Unsupported platform: {sys.platform} "
                 f"(supported: {', '.join(PLATFORMS)})")
    print(f"Platform: {sys.platform} ({arch()}), version: {version()}")
    build(cfg)
    package(cfg)


if __name__ == "__main__":
    main()
