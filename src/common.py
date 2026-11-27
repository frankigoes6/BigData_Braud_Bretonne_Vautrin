"""Fonctions partagées : chemins, parsing du JSON imbriqué, normalisation.

Les champs `listepersonnes`, `jugement`, `acte`, ... sont des chaînes JSON
(stockées en texte par l'export BODACC) : tout usage doit passer par
`parse_json_field` avant lecture.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "out"
RAW = DATA / "bodacc_idf_2022_2025.json"


def load_raw() -> list[dict]:
    return json.loads(RAW.read_text(encoding="utf-8"))


def parse_json_field(value):
    """Champ BODACC en texte JSON -> objet Python (None si invalide)."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value


def first(value):
    """Certains champs sont un objet ou une liste d'objets."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def personne(record: dict) -> dict:
    lp = parse_json_field(record.get("listepersonnes"))
    p = first(lp.get("personne")) if isinstance(lp, dict) else None
    return p if isinstance(p, dict) else {}


def siren(record: dict) -> str | None:
    imm = first(personne(record).get("numeroImmatriculation")) or {}
    digits = "".join(c for c in str(imm.get("numeroIdentification", "")) if c.isdigit())
    return digits if len(digits) == 9 else None


def jugement(record: dict) -> dict:
    j = parse_json_field(record.get("jugement"))
    return j if isinstance(j, dict) else {}


def etablissement(record: dict) -> dict:
    le = parse_json_field(record.get("listeetablissements"))
    e = first(le.get("etablissement")) if isinstance(le, dict) else None
    return e if isinstance(e, dict) else {}


def procedure_type(nature: str | None) -> str:
    """Nature du jugement -> type de procédure normalisé."""
    n = (nature or "").lower()
    if not n:
        return "sans_jugement"
    if "conversion" in n and "liquidation" in n:
        return "conversion_liquidation"
    if "ouverture" in n and "liquidation" in n:
        return "liquidation"
    if "ouverture" in n and "redressement" in n:
        return "redressement"
    if "ouverture" in n and "sauvegarde" in n:
        return "sauvegarde"
    if "clôture" in n or "cloture" in n:
        return "cloture"
    if "plan" in n:
        return "plan"
    if "faillite" in n or "interdiction de gérer" in n:
        return "sanction"
    if "créances" in n or "creances" in n:
        return "creances"
    return "autre"


OUVERTURES = ("liquidation", "redressement", "sauvegarde", "conversion_liquidation")

# NAF rév. 2 : division (2 premiers chiffres) -> section
_SECTIONS = [
    ("A", 1, 3, "Agriculture, sylviculture et pêche"),
    ("B", 5, 9, "Industries extractives"),
    ("C", 10, 33, "Industrie manufacturière"),
    ("D", 35, 35, "Production et distribution d'électricité, de gaz"),
    ("E", 36, 39, "Eau, assainissement, déchets"),
    ("F", 41, 43, "Construction"),
    ("G", 45, 47, "Commerce, réparation d'automobiles"),
    ("H", 49, 53, "Transports et entreposage"),
    ("I", 55, 56, "Hébergement et restauration"),
    ("J", 58, 63, "Information et communication"),
    ("K", 64, 66, "Activités financières et d'assurance"),
    ("L", 68, 68, "Activités immobilières"),
    ("M", 69, 75, "Activités spécialisées, scientifiques et techniques"),
    ("N", 77, 82, "Activités de services administratifs et de soutien"),
    ("O", 84, 84, "Administration publique"),
    ("P", 85, 85, "Enseignement"),
    ("Q", 86, 88, "Santé humaine et action sociale"),
    ("R", 90, 93, "Arts, spectacles et activités récréatives"),
    ("S", 94, 96, "Autres activités de services"),
    ("T", 97, 98, "Activités des ménages en tant qu'employeurs"),
    ("U", 99, 99, "Activités extra-territoriales"),
]


def naf_section(code: str | None) -> tuple[str, str] | tuple[None, None]:
    """Code NAF ("43.21A") -> (section, libellé)."""
    if not code:
        return None, None
    digits = "".join(c for c in code[:2] if c.isdigit())
    if not digits:
        return None, None
    division = int(digits)
    for section, lo, hi, label in _SECTIONS:
        if lo <= division <= hi:
            return section, label
    return None, None
