# BuildKit GHA cache credential-leak lab

This bundle validates the mechanism without contacting Mozilla or redeeming a cloud credential.

## Local scanner control

```bash
python make_fake_buildkit_wif_layer.py --out fake.tar.gz
python scan_buildkit_wif_blob.py fake.tar.gz --json
```

The scanner reports the generated credential metadata but redacts the bearer value.

## Owned GitHub repository lab

Copy the bundle contents into a repository you control:

1. Install `lab/producer.yml` as `.github/workflows/producer.yml` and run it on the default branch. It creates a fake `gha-creds-lab.json`, uses `COPY . .`, and exports `mode=max` BuildKit cache.
2. Install `lab/consumer-pr.yml` as `.github/workflows/consumer-pr.yml`.
3. Open a pull request from a fork of the owned repository.
4. The PR workflow lists the base branch's BuildKit blob keys, downloads bounded-size blobs using the same `go-actions-cache` client BuildKit uses, and finds the fake credential in an intermediate layer.

The lab intentionally does not request an OIDC token, call Google STS, impersonate a service account, or push an image.

## Why this maps to syncstorage-rs

The affected publish job authenticates before a root path-context build. Google Auth writes `gha-creds-*.json` into the workspace. The repository's `.dockerignore` does not exclude that pattern, the Dockerfile executes `COPY . .`/`COPY . /app`, and the workflow exports `type=gha,mode=max`. GitHub documents that fork pull-request workflows can read base-branch caches.
