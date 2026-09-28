"""Reconstruct a fixed, hash-verified model without executing downloaded code."""

import hashlib
import json
import shutil
import tarfile
from pathlib import Path

MANIFEST_SHA = "74248445b83ecd84cbea709914bd71f035bce0fd41be89921f1c1ea0f00d7305"
ARCHIVE = Path(__file__).parent / "assets/research-r1.tgz"


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def safe_path(root, name):
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe asset path: {name}")
    target = root / relative
    if not target.resolve().is_relative_to(root.resolve()) or target.is_symlink():
        raise ValueError(f"asset escapes bundle: {name}")
    return target


def read_manifest(root):
    path = safe_path(root, "release-manifest.json")
    if digest(path) != MANIFEST_SHA:
        raise ValueError("release manifest identity mismatch")
    return json.loads(path.read_text())


def verify(root):
    root = Path(root).resolve()
    manifest = read_manifest(root)
    for name, expected in manifest["files"].items():
        path = safe_path(root, name)
        if not path.is_file() or digest(path) != expected:
            raise ValueError(f"asset missing or corrupt: {name}")
    return {"verified": True, "files": len(manifest["files"]), "manifest": MANIFEST_SHA}


def unpack(root):
    """Copy regular files only; immutable manifest authenticates each member."""
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        members = archive.getmembers()
        if len({m.name for m in members}) != len(members):
            raise ValueError("duplicate archive members")
        for member in members:
            if not member.isfile():
                raise ValueError("archive contains nonregular asset")
            target = safe_path(root, member.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                with archive.extractfile(member) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
    manifest = read_manifest(root)
    for member in members:
        if member.name == "release-manifest.json":
            continue
        if digest(safe_path(root, member.name)) != manifest["files"].get(member.name):
            raise ValueError(f"overlay hash mismatch: {member.name}")
    return manifest


def prepare(output, base_dir=None):
    from huggingface_hub import hf_hub_download

    output = Path(output).absolute()
    if output.is_symlink():
        raise ValueError("output cannot be a symlink")
    if output.exists():
        return verify(output)
    pending = output.with_name(output.name + ".pending")
    if pending.is_symlink():
        raise ValueError("staging cannot be a symlink")
    pending.mkdir(parents=True, exist_ok=True)
    manifest = unpack(pending)
    config = json.loads((pending / "router_release/config.json").read_text())
    for name, expected in config["verified_base_files"].items():
        target = safe_path(pending, name)
        if target.exists():
            if digest(target) != expected:
                raise ValueError(
                    f"staged asset corrupt; remove it before retry: {name}"
                )
            continue
        source = (
            safe_path(Path(base_dir).resolve(), name)
            if base_dir
            else Path(
                hf_hub_download(
                    manifest["base_repo"], name, revision=manifest["base_revision"]
                )
            )
        )
        if digest(source) != expected:
            raise ValueError(f"base asset identity mismatch: {name}")
        temporary = target.with_name(target.name + ".download")
        if temporary.is_symlink():
            raise ValueError("unsafe temporary file")
        shutil.copyfile(source, temporary)
        temporary.replace(target)
    result = verify(pending)
    pending.rename(output)
    return result
