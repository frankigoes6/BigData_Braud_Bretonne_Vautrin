#!/usr/bin/env python3
"""Contrôle de qualité du fichier brut BODACC, sans aucune correction.

Compte les anomalies de `data/bodacc_idf_2022_2025.json` et écrit le résultat
dans `data/quality_report.json`.
Usage : python src/quality.py
"""
from __future__ import annotations

import json
import re
from collections import Counter

from common import (DATA, OUVERTURES, jugement, load_raw, parse_json_field,
                    procedure_type, siren)

DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CHAMPS_IMBRIQUES = (
    "listepersonnes", "listeetablissements", "jugement", "acte", "divers",
    "depot", "radiationaurcs", "modificationsgenerales", "parutionavisprecedent",
    "listeprecedentexploitant", "listeprecedentproprietaire",
)


def json_invalide(record: dict, champ: str) -> bool:
    """Vrai si le champ est un texte qui ne se décode pas en JSON."""
    valeur = record.get(champ)
    return isinstance(valeur, str) and parse_json_field(valeur) is None


def main() -> None:
    rows = load_raw()

    imbriques_invalides = sum(
        1 for r in rows for f in CHAMPS_IMBRIQUES if json_invalide(r, f)
    )
    dates_invalides = sum(
        1 for r in rows if not DATE_ISO.match(str(r.get("dateparution", "")))
    )
    siren_absent = sum(1 for r in rows if siren(r) is None)
    # Pas de champ NAF dans le BODACC : on teste les clés, pas le texte libre.
    naf_present = sum(1 for r in rows if any("naf" in str(k).lower() for k in r))
    types = Counter(procedure_type(jugement(r).get("nature")) for r in rows)

    # Doublon métier : même SIREN, même date, même type de procédure.
    cles = Counter(
        (siren(r), r.get("dateparution"), procedure_type(jugement(r).get("nature")))
        for r in rows
    )
    doublons = sum(n - 1 for n in cles.values() if n > 1)

    report = {
        "lignes": len(rows),
        "colonnes": len(rows[0]),
        "identifiants_uniques": len({r.get("id") for r in rows}),
        "champs_imbriques_en_texte": sum(
            1 for f in CHAMPS_IMBRIQUES
            if isinstance(rows[0].get(f), (str, type(None)))
        ),
        "champs_imbriques_json_invalides": imbriques_invalides,
        "dates_parution_invalides": dates_invalides,
        "siren_absent_ou_mal_forme": siren_absent,
        "codes_naf_presents": naf_present,
        "doublons_metier": doublons,
        "familles": Counter(r.get("familleavis") for r in rows),
        "types_procedure": types,
    }
    report = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in report.items()}
    (DATA / "quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Lignes                  : {report['lignes']}")
    print(f"Colonnes                : {report['colonnes']}")
    print(f"Identifiants uniques    : {report['identifiants_uniques']}")
    print(f"JSON imbriqué invalide  : {imbriques_invalides}")
    print(f"Dates invalides         : {dates_invalides}")
    print(f"SIREN absent/malformé   : {siren_absent}")
    print(f"Codes NAF présents      : {naf_present}")
    print(f"Doublons métier         : {doublons}")
    print(f"Familles                : {report['familles']}")
    print("\nTypes de procédure (après normalisation) :")
    for nom, nombre in types.most_common():
        marque = "  <- ouverture" if nom in OUVERTURES else ""
        print(f"  {nom:<24} {nombre:>5}{marque}")
    print("\n-> data/quality_report.json")


if __name__ == "__main__":
    main()
