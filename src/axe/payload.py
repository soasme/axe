"""Compose the payload zip embedded into a built binary (see trailer.py)."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path


def compose(
    config_doc: dict,
    app_wheel_name: str,
    app_wheel: bytes,
    dep_wheels: list[Path],
    uv_archive: Path,
    python_archive: Path,
) -> bytes:
    """Build the payload zip. Entries are stored uncompressed: the wheels and
    the uv/python archives are already compressed."""
    entries: list[tuple[str, bytes]] = [(f"wheels/{app_wheel_name}", app_wheel)]
    entries += [(f"wheels/{p.name}", p.read_bytes()) for p in dep_wheels]
    entries.append((f"uv/{uv_archive.name}", uv_archive.read_bytes()))
    entries.append((f"python/{python_archive.name}", python_archive.read_bytes()))

    doc = dict(config_doc)
    doc["wheel_name"] = app_wheel_name
    doc["uv_archive"] = f"uv/{uv_archive.name}"
    doc["python_archive"] = f"python/{python_archive.name}"

    # Fingerprint everything that defines the installation; it keys the
    # per-app install directory on the user's machine.
    digest = hashlib.sha256(json.dumps(doc, sort_keys=True).encode())
    for name, data in entries:
        digest.update(name.encode())
        digest.update(hashlib.sha256(data).digest())
    doc["fingerprint"] = digest.hexdigest()[:16]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("config.json", json.dumps(doc, sort_keys=True))
        for name, data in entries:
            zf.writestr(name, data)
    return buf.getvalue()
