# BigData_Braud_Bretonne_Vautrin

Projet **Écosystème Big Data II** — pipeline de traitement des annonces BODACC
(défaillances d'entreprises) en Île-de-France, de 2022 à 2025.

## Auteurs

- BRAUD Frank
- BRETONNE Mathis
- VAUTRIN Denis

## Prérequis

- Python 3.9+
- Un accès au stockage objet **S3 Onyxia** (bucket et identifiants)
- `git`
- Outil de traitement au choix : Spark ou DuckDB (voir `src/`)

## Dataset

| | |
|---|---|
| **Nom** | BODACC — Annonces commerciales (DILA) |
| **Source** | https://www.data.gouv.fr/datasets/bodacc |
| **API** | `https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/exports/json` |
| **Licence** | Licence Ouverte / Open Licence Etalab 2.0 |
| **Date de téléchargement** | 2026-11-19 |
| **Taille livrée** | 4,49 Mo — 1 992 annonces (`data/bodacc_idf_2022_2025.json`) |
| **Périmètre** | Île-de-France (75, 77, 78, 91, 92, 93, 94, 95), 2022–2025 |
| **Filtres** | `publicationavis = A`, `familleavis ∈ {collective, vente, conciliation}` |

Le filtre complet représente 171 755 annonces (~360 Mo) ; le fichier livré en est
un échantillon systématique (détail dans `data/README.md`).

## Problématique

Quels départements d'Île-de-France et quels secteurs d'activité concentrent le
plus de procédures collectives entre 2022 et 2025 ? Observe-t-on une saisonnalité
mensuelle des défaillances ? La part de liquidations judiciaires varie-t-elle
selon le secteur ?

## Chemins S3

| Donnée | Chemin |
|---|---|
| Brut | `s3://<bucket>/raw/bodacc/` |
| Traité | `s3://<bucket>/processed/bodacc/` |

## Reproduction

```bash
# 1. Cloner le dépôt
git clone git@github.com:frankigoes6/BigData_Braud_Bretonne_Vautrin.git
cd BigData_Braud_Bretonne_Vautrin

# 2. (Re)générer les données brutes — optionnel, le fichier est déjà versionné
python3 src/fetch_bodacc.py

# 3. Déposer le brut sur S3 (adapter le bucket et le profil)
aws s3 cp data/bodacc_idf_2022_2025.json s3://<bucket>/raw/bodacc/

# 4. Exécuter le pipeline de nettoyage et d'agrégation
#    TODO : commande à compléter (Spark ou DuckDB)
```

**Redémarrage** : relancer les étapes 3 et 4. Le pipeline doit être idempotent
(réécriture complète des préfixes `raw/bodacc/` et `processed/bodacc/`).

## Structure du dépôt

```text
.
├── README.md
├── data/       # données brutes (échantillon BODACC)
├── evidence/   # captures numérotées 01_..., 02_...
├── src/        # code (Python, SQL, ...)
└── k8s/        # manifestes Kubernetes
```
