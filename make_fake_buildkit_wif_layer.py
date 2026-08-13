#!/usr/bin/env python3
"""Create a harmless OCI-style compressed layer containing a fake gha-creds file."""
from __future__ import annotations

import argparse
import gzip
import io
import json
import tarfile
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="fake_buildkit_wif_layer.tar.gz")
    args = p.parse_args()

    fake = {
        "type": "external_account",
        "audience": "//iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/lab/providers/github",
        "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        "token_url": "https://sts.googleapis.com/v1/token",
        "credential_source": {
            "url": "https://pipelines.actions.githubusercontent.com/lab/idtoken?audience=lab",
            "headers": {"Authorization": "Bearer LAB_FAKE_REQUEST_TOKEN_DO_NOT_USE"},
            "format": {"type": "json", "subject_token_field_name": "value"},
        },
        "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/lab@example.invalid:generateAccessToken",
    }
    data = json.dumps(fake, separators=(",", ":")).encode()

    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w") as tf:
        info = tarfile.TarInfo("app/gha-creds-deadbeef.json")
        info.mode = 0o600
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))

    out = Path(args.out)
    with out.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            gz.write(tar_buf.getvalue())
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
