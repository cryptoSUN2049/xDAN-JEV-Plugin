import hashlib
import io
import json
import tarfile

import pytest

from xdan_jev_plugin import bundle


def test_real_overlay(tmp_path):
    manifest = bundle.unpack(tmp_path)
    assert len(manifest["files"]) == 46
    assert manifest["base_repo"] == "Qwen/Qwen3.5-9B"
    with pytest.raises(ValueError, match="missing or corrupt"):
        bundle.verify(tmp_path)
    (tmp_path / "README.md").write_text("tampered")
    with pytest.raises(ValueError, match="overlay hash mismatch"):
        bundle.unpack(tmp_path)


def test_traversal_and_symlink(tmp_path):
    for name in ("../outside", "/tmp/absolute"):
        with pytest.raises(ValueError, match="unsafe"):
            bundle.safe_path(tmp_path, name)
    (tmp_path / "escape").symlink_to("/tmp")
    with pytest.raises(ValueError, match="escapes"):
        bundle.safe_path(tmp_path, "escape/asset")


def test_archive_rejects_links(tmp_path, monkeypatch):
    archive = tmp_path / "bad.tgz"
    with tarfile.open(archive, "w:gz") as tar:
        item = tarfile.TarInfo("link")
        item.type = tarfile.SYMTYPE
        item.linkname = "/tmp"
        tar.addfile(item)
    monkeypatch.setattr(bundle, "ARCHIVE", archive)
    with pytest.raises(ValueError, match="nonregular"):
        bundle.unpack(tmp_path / "out")


def test_prepare_resume_and_verify(tmp_path, monkeypatch):
    base = tmp_path / "base"
    base.mkdir()
    (base / "weights").write_bytes(b"original")
    sha = hashlib.sha256(b"original").hexdigest()
    config = json.dumps({"verified_base_files": {"weights": sha}}).encode()
    manifest = json.dumps(
        {
            "files": {
                "weights": sha,
                "router_release/config.json": hashlib.sha256(config).hexdigest(),
            }
        }
    ).encode()
    monkeypatch.setattr(bundle, "MANIFEST_SHA", hashlib.sha256(manifest).hexdigest())
    archive = tmp_path / "fixture.tgz"
    with tarfile.open(archive, "w:gz") as tar:
        for name, content in {
            "release-manifest.json": manifest,
            "router_release/config.json": config,
        }.items():
            item = tarfile.TarInfo(name)
            item.size = len(content)
            tar.addfile(item, io.BytesIO(content))
    monkeypatch.setattr(bundle, "ARCHIVE", archive)
    output = tmp_path / "model"
    assert bundle.prepare(output, base)["verified"]
    assert bundle.prepare(output, base)["verified"]
    (output / "weights").write_bytes(b"bad")
    with pytest.raises(ValueError, match="corrupt"):
        bundle.verify(output)
