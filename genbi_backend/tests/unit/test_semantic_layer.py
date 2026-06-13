"""Tests unitaires — core/semantic_layer.py

Couverture :
  - load_catalog : structure YAML, IDs uniques, synonymes présents
  - _normalize   : minuscules, accents supprimés
  - resolve_semantics : matching normal, cas limites, format de sortie
"""
import pytest

from core.semantic_layer import load_catalog, resolve_semantics, _normalize


# ── Catalog de test isolé (indépendant du fichier YAML réel) ──────────────────

CATALOG_TEST = {
    "metrics": [
        {
            "id": "chiffre_affaires",
            "label": "Chiffre d'affaires",
            "synonymes": ["mon CA", "le CA", "CA total", "revenu", "recettes", "chiffre d affaires"],
            "sql": "SUM(total_amount_fcfa)",
            "table": "marts.fct_sales",
            "unite": "FCFA",
        },
        {
            "id": "nb_ruptures",
            "label": "Ruptures de stock",
            "synonymes": ["ruptures", "ventes manquees", "stockout"],
            "sql": "COUNT(*)",
            "table": "marts.fct_missed_sales",
            "unite": "ruptures",
        },
    ],
    "dimensions": [
        {
            "id": "par_mois",
            "label": "Par mois",
            "synonymes": ["par mois", "mensuel", "evolution mensuelle"],
            "colonnes": {
                "marts.fct_sales": "sale_month",
                "marts.fct_missed_sales": "missed_month",
            },
        },
        {
            "id": "par_produit",
            "label": "Par produit",
            "synonymes": ["par produit", "par medicament", "top produits"],
            "colonne": "marts.dim_products.commercial_name",
            "jointure": "staging.stg_raw__sale_details",
        },
    ],
    "filtres": [
        {
            "id": "clients_chroniques",
            "label": "Clients chroniques",
            "synonymes": ["chroniques", "malades chroniques", "clients chroniques"],
            "sql": "is_chronic = TRUE",
            "table": "marts.dim_clients",
        },
    ],
}


# ── load_catalog — structure du fichier réel ──────────────────────────────────

def test_load_catalog_retourne_trois_sections():
    cat = load_catalog()
    assert "metrics" in cat
    assert "dimensions" in cat
    assert "filtres" in cat


def test_load_catalog_sections_non_vides():
    cat = load_catalog()
    assert len(cat["metrics"]) > 0
    assert len(cat["dimensions"]) > 0
    assert len(cat["filtres"]) > 0


def test_load_catalog_ids_tous_uniques():
    cat = load_catalog()
    all_ids = [
        e["id"]
        for section in ("metrics", "dimensions", "filtres")
        for e in cat[section]
    ]
    assert len(all_ids) == len(set(all_ids)), "IDs dupliqués détectés dans le catalogue"


def test_load_catalog_chaque_entree_a_synonymes_non_vides():
    cat = load_catalog()
    for section in ("metrics", "dimensions", "filtres"):
        for entry in cat[section]:
            assert entry.get("synonymes"), (
                f"Entrée '{entry.get('id')}' sans synonymes dans '{section}'"
            )


def test_load_catalog_fichier_absent_leve_erreur():
    with pytest.raises(FileNotFoundError):
        load_catalog("/chemin/inexistant/catalog.yaml")


# ── _normalize ────────────────────────────────────────────────────────────────

def test_normalize_met_en_minuscules():
    assert _normalize("CA") == "ca"
    assert _normalize("REVENU") == "revenu"


def test_normalize_supprime_accents():
    assert _normalize("révenu") == "revenu"
    assert _normalize("péremptions") == "peremptions"
    assert _normalize("tiers-payant") == "tiers-payant"
    assert _normalize("assurés") == "assures"


def test_normalize_combine_minuscules_et_accents():
    assert _normalize("Chiffre d'Affaires") == "chiffre d'affaires"
    assert _normalize("Rupturés") == "ruptures"


# ── resolve_semantics — cas normaux ──────────────────────────────────────────

def test_resolve_ca_par_synonyme_revenu():
    ctx = resolve_semantics("quel est mon revenu ce mois ?", CATALOG_TEST)
    assert "Chiffre d'affaires" in ctx
    assert "SUM(total_amount_fcfa)" in ctx


def test_resolve_ruptures_par_synonyme_ventes_manquees():
    ctx = resolve_semantics("combien de ventes manquees ce trimestre ?", CATALOG_TEST)
    assert "Ruptures de stock" in ctx
    assert "fct_missed_sales" in ctx


def test_resolve_dimension_par_mois():
    ctx = resolve_semantics("quel est mon CA par mois ?", CATALOG_TEST)
    assert "Par mois" in ctx
    assert "sale_month" in ctx


def test_resolve_filtre_clients_chroniques():
    ctx = resolve_semantics("combien de clients chroniques avons-nous ?", CATALOG_TEST)
    assert "Clients chroniques" in ctx
    assert "is_chronic = TRUE" in ctx


def test_resolve_plusieurs_matches_meme_question():
    ctx = resolve_semantics("quel est mon CA par mois ?", CATALOG_TEST)
    assert "Chiffre d'affaires" in ctx
    assert "Par mois" in ctx


# ── resolve_semantics — cas limites ──────────────────────────────────────────

def test_resolve_aucun_match_retourne_chaine_vide():
    ctx = resolve_semantics("quelle heure est-il ?", CATALOG_TEST)
    assert ctx == ""


def test_resolve_catalog_none_retourne_chaine_vide():
    ctx = resolve_semantics("quel est mon CA ?", None)
    assert ctx == ""


def test_resolve_catalog_vide_retourne_chaine_vide():
    ctx = resolve_semantics("quel est mon CA ?", {})
    assert ctx == ""


def test_resolve_insensible_a_la_casse():
    ctx = resolve_semantics("quel est mon CA total ce mois ?", CATALOG_TEST)
    assert "Chiffre d'affaires" in ctx


def test_resolve_insensible_aux_accents():
    ctx = resolve_semantics("combien de rupturés avons-nous ?", CATALOG_TEST)
    assert "Ruptures de stock" in ctx


def test_resolve_pas_de_doublon_si_synonyme_repete():
    ctx = resolve_semantics("CA revenu recettes chiffre", CATALOG_TEST)
    assert ctx.count("Chiffre d'affaires") == 1


# ── Format de sortie ─────────────────────────────────────────────────────────

def test_resolve_contient_balise_semantic_context():
    ctx = resolve_semantics("quel est mon CA ?", CATALOG_TEST)
    assert ctx.startswith("<semantic_context>")
    assert "</semantic_context>" in ctx


def test_resolve_contient_termes_detectes():
    ctx = resolve_semantics("quel est mon CA ?", CATALOG_TEST)
    assert "Termes détectés" in ctx


def test_resolve_pas_de_faux_positif_ca_prenom():
    """'ca' pronom français ne doit pas déclencher Chiffre d'affaires."""
    ctx = resolve_semantics("bonjour comment ca va ?", CATALOG_TEST)
    assert "Chiffre d'affaires" not in ctx


def test_resolve_pas_de_faux_positif_ventes_manquees():
    """'ventes manquées' doit déclencher Ruptures, pas Nombre de ventes."""
    ctx = resolve_semantics("combien de ventes manquees avons-nous ?", CATALOG_TEST)
    assert "Ruptures de stock" in ctx
    assert "Nombre de ventes" not in ctx
