#!/usr/bin/env python3
"""Aplatit le JSON brut et écrit `out/clean.parquet`.

- dédoublonne sur (SIREN, date de parution, type de procédure)
- normalise les types de procédure et les dates
- n'invente rien : les champs absents restent NULL

Usage : python src/build.py
"""
from __future__ import annotations

import datetime as dt

import duckdb
import pandas as pd

from common import OUVERTURES, OUT, etablissement, jugement, load_raw, personne, procedure_type, siren


def flatten(record: dict) -> dict:
    p = personne(record)
    j = jugement(record)
    e = etablissement(record)
    siege = personne(record).get("adresseSiegeSocial") or {}
    if isinstance(siege, list):
        siege = siege[0] if siege else {}
    nature = j.get("nature")
    return {
        "annonce_id": record.get("id"),
        "date_parution": record.get("dateparution"),
        "famille": record.get("familleavis"),
        "type_avis": record.get("typeavis_lib"),
        "tribunal": record.get("tribunal"),
        "departement": str(record.get("numerodepartement") or "").zfill(2) or None,
        "departement_nom": record.get("departement_nom_officiel"),
        "region": record.get("region_nom_officiel"),
        "ville": record.get("ville"),
        "siren": siren(record),
        "denomination": p.get("denomination") or p.get("nom") or p.get("prenom"),
        "activite": p.get("activite"),
        "forme_juridique": p.get("formeJuridique"),
        "code_postal_siege": siege.get("codePostal") if isinstance(siege, dict) else None,
        "nature_jugement": nature,
        "procedure": procedure_type(nature),
        "date_jugement": j.get("date"),
        "etablissement_commune": (e.get("adresse") or {}).get("ville") if isinstance(e.get("adresse"), dict) else None,
    }


def main() -> None:
    rows = [flatten(r) for r in load_raw()]
    df = pd.DataFrame(rows)
    df["annee"] = pd.to_datetime(df["date_parution"], errors="coerce").dt.year
    df["mois"] = pd.to_datetime(df["date_parution"], errors="coerce").dt.month
    df["date_jugement"] = pd.to_datetime(df["date_jugement"], errors="coerce")
    df["est_ouverture"] = df["procedure"].isin(OUVERTURES)

    before = len(df)
    df = df.sort_values(["date_parution", "annonce_id"])
    df = df.drop_duplicates(subset=["siren", "date_parution", "procedure"], keep="first")

    OUT.mkdir(exist_ok=True)
    con = duckdb.connect()
    con.register("flat", df)
    con.execute(
        f"COPY (SELECT * FROM flat ORDER BY date_parution, annonce_id) "
        f"TO '{OUT / 'clean.parquet'}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )

    print(f"Annonces aplaties      : {before}")
    print(f"Après dédoublonnage    : {len(df)}  ({before - len(df)} doublons retirés)")
    print(f"Ouvertures de procédure: {int(df['est_ouverture'].sum())}")
    print(f"SIREN renseigné        : {int(df['siren'].notna().sum())} / {len(df)}")
    print(f"Période                : {df['date_parution'].min()} -> {df['date_parution'].max()}")
    print(f"-> {OUT / 'clean.parquet'}")


if __name__ == "__main__":
    main()
