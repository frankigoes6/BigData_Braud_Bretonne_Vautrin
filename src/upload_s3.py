#!/usr/bin/env python3
"""Dépose les données sur S3 Onyxia (bucket = `user-<namespace>`).

Lit les identifiants injectés par Onyxia : AWS_ACCESS_KEY_ID,
AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, AWS_S3_ENDPOINT, AWS_DEFAULT_REGION.

Usage : python src/upload_s3.py [--processed]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]
# Dans un service Onyxia, KUBERNETES_NAMESPACE vaut déjà `user-<id>`.
_NS = os.environ["KUBERNETES_NAMESPACE"]
BUCKET = _NS if _NS.startswith("user-") else "user-" + _NS


def client():
    return boto3.client(
        "s3",
        endpoint_url="https://" + os.environ["AWS_S3_ENDPOINT"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        aws_session_token=os.environ["AWS_SESSION_TOKEN"],
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )


def upload(s3, path: Path, prefix: str) -> None:
    if not path.exists():
        print(f"(absent, ignoré) {path.name}")
        return
    s3.upload_file(str(path), BUCKET, f"{prefix}/{path.name}")
    print(f"s3://{BUCKET}/{prefix}/{path.name}")


def main() -> None:
    s3 = client()
    for name in ("bodacc_idf_2022_2025.json", "bodacc_idf_2022_2025.manifest.json", "README.md"):
        upload(s3, ROOT / "data" / name, "raw/bodacc")

    if "--processed" in sys.argv:
        for name in ("clean.parquet",):
            upload(s3, ROOT / "out" / name, "processed/bodacc/clean")
        for name in ("agg_mois_dept.parquet", "agg_secteur.parquet", "agg_saisonnalite.parquet"):
            upload(s3, ROOT / "out" / name, "processed/bodacc/agg")
        upload(s3, ROOT / "data" / "sirene_naf.json", "processed/bodacc/naf")
    else:
        print("(sorties non déposées : relancer avec --processed)")


if __name__ == "__main__":
    main()
