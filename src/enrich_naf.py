#!/usr/bin/env python3
"""Joint le code NAF des entreprises via l'API recherche-entreprises.api.gouv.fr.

Le BODACC ne publie pas de code NAF : on le récupère par SIREN et on met en
cache dans `data/sirene_naf.json` (relançable, seules les SIREN manquantes sont
interrogées). Écrit `out/naf.parquet`.

Usage : python src/enrich_naf.py
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor

import duckdb
import pandas as pd
import requests

from common import DATA, OUT, naf_section

API = "https://recherche-entreprises.api.gouv.fr/search"
CACHE = DATA / "sirene_naf.json"
WORKERS = 5
HEADERS = {"User-Agent": "bodacc-pipeline/1.0 (projet etudiant ECE)"}


def lookup(siren: str) -> dict:
    for attempt in range(4):
        try:
            r = requests.get(
                API, params={"q": siren, "minimal": "true"}, headers=HEADERS, timeout=20
            )
            if r.status_code == 429:
                time.sleep(10)
                continue
            r.raise_for_status()
            break
        except (requests.ConnectionError, requests.Timeout):
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))
    for hit in r.json().get("results", []):
        if hit.get("siren") == siren:
            naf = hit.get("activite_principale")
            section, label = naf_section(naf)
            return {"naf": naf, "section": section, "section_libelle": label}
    return {"naf": None, "section": None, "section_libelle": None}


def main() -> None:
    sirens = sorted(
        {
            r[0]
            for r in duckdb.sql(f"SELECT DISTINCT siren FROM '{OUT / 'clean.parquet'}' WHERE siren IS NOT NULL").fetchall()
        }
    )
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    todo = [s for s in sirens if s not in cache]
    print(f"{len(sirens)} SIREN, {len(todo)} à interroger")

    for i, (s, result) in enumerate(
        zip(todo, ThreadPoolExecutor(max_workers=WORKERS).map(lookup, todo)), 1
    ):
        cache[s] = result
        if i % 200 == 0:
            CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            print(f"  {i}/{len(todo)}", flush=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")

    OUT.mkdir(exist_ok=True)
    con = duckdb.connect()
    con.register("rows", pd.DataFrame([{"siren": s, **v} for s, v in cache.items()]))
    con.execute(f"COPY (SELECT * FROM rows) TO '{OUT / 'naf.parquet'}' (FORMAT PARQUET)")

    found = sum(1 for v in cache.values() if v.get("naf"))
    print(f"NAF trouvé : {found}/{len(cache)} SIREN")
    print(f"-> {OUT / 'naf.parquet'}")


if __name__ == "__main__":
    main()
