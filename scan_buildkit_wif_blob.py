#!/usr/bin/env python3
"""Scan one BuildKit layer blob for generated Google GitHub Actions credentials.

The scanner is intentionally redacted: it never prints the bearer value. It supports
gzip, zstd, and uncompressed tar layers.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path
from typing import BinaryIO


def _open_stream(path: Path) -> tuple[BinaryIO, str]:
    raw = path.open("rb")
    magic = raw.read(4)
    raw.seek(0)
    if magic[:2] == b"\x1f\x8b":
        return gzip.GzipFile(fileobj=raw), "gzip"
    if magic == b"\x28\xb5\x2f\xfd":
        try:
            import zstandard  # type: ignore
        except ImportError as exc:
            raw.close()
            raise RuntimeError("zstd layer detected; install zstandard") from exc
        return zstandard.ZstdDecompressor().stream_reader(raw), "zstd"
    return raw, "plain"


def _redact(path: str, obj: dict) -> dict:
    source = obj.get("credential_source") or {}
    headers = source.get("headers") or {}
    authorization = str(headers.get("Authorization", ""))
    token = authorization.removeprefix("Bearer ").removeprefix("bearer ")
    return {
        "member": path,
        "type": obj.get("type"),
        "audience": obj.get("audience"),
        "token_url": obj.get("token_url"),
        "credential_source_url": str(source.get("url", "")),
        "has_bearer_header": authorization.lower().startswith("bearer "),
        "bearer_length": len(token),
        "bearer_sha256_prefix": hashlib.sha256(token.encode()).hexdigest()[:16] if token else "",
        "service_account_impersonation_url": obj.get("service_account_impersonation_url"),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("blob", type=Path)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    stream, encoding = _open_stream(args.blob)
    findings: list[dict] = []
    try:
        with tarfile.open(fileobj=stream, mode="r|*") as tf:
            for member in tf:
                if not member.isfile() or "gha-creds-" not in Path(member.name).name:
                    continue
                f = tf.extractfile(member)
                if f is None:
                    continue
                try:
                    obj = json.loads(f.read().decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if isinstance(obj, dict):
                    findings.append(_redact(member.name, obj))
    finally:
        stream.close()

    result = {"blob": str(args.blob), "encoding": encoding, "findings": findings}
    print(json.dumps(result, indent=2) if args.json else result)
    return 0 if findings else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
