import pytest
from core.viz_classifier import detect_viz_hint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _hint(question, sql, columns, rows):
    return detect_viz_hint(question, sql, columns, rows)


# ---------------------------------------------------------------------------
# Cas None — pas de graphique pertinent
# ---------------------------------------------------------------------------
class TestNullCases:
    def test_empty_rows(self):
        assert _hint("question", "SELECT col1, col2", ["col1", "col2"], []) is None

    def test_single_row(self):
        assert _hint("question", "SELECT col1, col2", ["col1", "col2"], [["A", 100]]) is None

    def test_single_column(self):
        assert _hint("question", "SELECT col1", ["col1"], [["A"], ["B"]]) is None

    def test_no_columns(self):
        assert _hint("question", "SELECT", [], []) is None


# ---------------------------------------------------------------------------
# LINE — signal temporel dans la question
# ---------------------------------------------------------------------------
class TestLineDetection:
    def test_par_mois(self):
        assert _hint("CA par mois", "SELECT mois, ca FROM t", ["mois", "ca"],
                     [[1, 100], [2, 200], [3, 300]]) == "line"

    def test_trend_en(self):
        assert _hint("monthly revenue trend", "SELECT mois, ca FROM t", ["mois", "ca"],
                     [[1, 100], [2, 200]]) == "line"

    def test_evolution(self):
        assert _hint("évolution du chiffre d'affaires", "SELECT m, ca FROM t", ["m", "ca"],
                     [[1, 100], [2, 150]]) == "line"

    def test_tendance(self):
        assert _hint("quelle est la tendance des ventes ?", "SELECT m, v FROM t", ["m", "v"],
                     [[1, 10], [2, 20], [3, 15]]) == "line"


# ---------------------------------------------------------------------------
# BAR — LIMIT dans le SQL (top-N, données partielles)
# ---------------------------------------------------------------------------
class TestBarFromLimit:
    def test_limit_5(self):
        assert _hint("top 5 produits", "SELECT produit, quantite FROM t ORDER BY quantite DESC LIMIT 5",
                     ["produit", "quantite"],
                     [["A", 100], ["B", 80], ["C", 60], ["D", 40], ["E", 20]]) == "bar"

    def test_limit_lowercase(self):
        assert _hint("best sellers", "SELECT produit, ca FROM t limit 3",
                     ["produit", "ca"],
                     [["A", 500], ["B", 400], ["C", 300]]) == "bar"

    def test_limit_3_categories(self):
        # Même si 3 lignes (candidat pie), LIMIT dans le SQL → bar
        assert _hint("top 3 assureurs", "SELECT assureur, nb FROM t LIMIT 3",
                     ["assureur", "nb"],
                     [["CNAM", 80], ["IPM", 50], ["Autre", 20]]) == "bar"


# ---------------------------------------------------------------------------
# PIE — composition structurelle pure
# ---------------------------------------------------------------------------
class TestPieDetection:
    def test_payment_modes_2_rows(self):
        assert _hint("répartition par mode de paiement",
                     "SELECT mode_paiement, COUNT(*) AS nb FROM t GROUP BY mode_paiement",
                     ["mode_paiement", "nb"],
                     [["Cash", 100], ["Assurance", 50]]) == "pie"

    def test_generics_vs_branded(self):
        assert _hint("part des génériques vs princeps",
                     "SELECT type_med, COUNT(*) FROM t GROUP BY type_med",
                     ["type_med", "count"],
                     [["Générique", 150], ["Princeps", 80]]) == "pie"

    def test_origin_3_rows(self):
        assert _hint("origine des produits",
                     "SELECT origin, COUNT(*) FROM t GROUP BY origin",
                     ["origin", "count"],
                     [["Local", 80], ["Importé", 120], ["Autre", 10]]) == "pie"

    def test_exactly_4_rows_still_pie(self):
        assert _hint("distribution par catégorie",
                     "SELECT cat, nb FROM t GROUP BY cat",
                     ["categorie", "nb"],
                     [["A", 10], ["B", 20], ["C", 30], ["D", 40]]) == "pie"

    def test_no_temporal_keyword_needed(self):
        # Pas de mot-clé "répartition" — la structure seule suffit
        assert _hint("assureurs",
                     "SELECT assureur, COUNT(*) FROM t GROUP BY assureur",
                     ["assureur", "nb"],
                     [["CNAM", 80], ["IPM", 50]]) == "pie"

    def test_composition_5_rows_is_pie(self):
        # 5 lignes + mot de composition → pie autorisé (5 types d'assurance lisibles)
        assert _hint("distribution par type d'assurance",
                     "SELECT type_assurance, COUNT(*) FROM t GROUP BY type_assurance",
                     ["type_assurance", "nb"],
                     [["CNAM", 80], ["IPM", 50], ["Privée", 30], ["Mutuelle", 20], ["Autre", 10]]) == "pie"

    def test_boolean_is_generic_is_pie(self):
        # is_generic retourne bool (True/False) depuis PostgreSQL — bool est
        # sous-classe de int en Python, il ne faut pas le traiter comme numérique
        assert _hint("part des génériques vs princeps",
                     "SELECT is_generic, SUM(ca) FROM t GROUP BY is_generic",
                     ["is_generic", "ca_total"],
                     [[False, 13660250], [True, 2870650]]) == "pie"


# ---------------------------------------------------------------------------
# PIE — cas exclus (doit retourner bar ou None)
# ---------------------------------------------------------------------------
class TestPieExclusions:
    def test_6_rows_not_pie_even_with_composition(self):
        # ≥6 lignes → pas pie même avec mot de composition
        result = _hint("distribution par catégorie", "SELECT cat, nb FROM t GROUP BY cat",
                       ["categorie", "nb"],
                       [["A", 10], ["B", 20], ["C", 30], ["D", 40], ["E", 50], ["F", 60]])
        assert result == "bar"

    def test_5_rows_neutral_question_not_pie(self):
        # 5 lignes sans mot de composition → pas pie (limite stricte = 4)
        result = _hint("résultats par segment", "SELECT cat, nb FROM t GROUP BY cat",
                       ["categorie", "nb"],
                       [["A", 10], ["B", 20], ["C", 30], ["D", 40], ["E", 50]])
        assert result == "bar"

    def test_temporal_col_not_pie(self):
        # col[0] contient "mois" → pas pie
        result = _hint("comparaison deux mois",
                       "SELECT mois, ca FROM t",
                       ["mois", "ca"],
                       [[1, 100], [2, 200]])
        assert result != "pie"

    def test_id_col_not_pie(self):
        # col[0] finit par _id → pas pie
        result = _hint("répartition",
                       "SELECT insurer_id, COUNT(*) FROM t GROUP BY insurer_id",
                       ["insurer_id", "count"],
                       [[1, 100], [2, 50]])
        assert result != "pie"

    def test_fcfa_col_not_pie(self):
        # col[0] finit par _fcfa → pas pie
        result = _hint("répartition",
                       "SELECT amount_fcfa, COUNT(*) FROM t GROUP BY amount_fcfa",
                       ["amount_fcfa", "count"],
                       [[1000, 5], [2000, 3]])
        assert result != "pie"

    def test_negative_values_not_pie(self):
        result = _hint("répartition",
                       "SELECT cat, val FROM t GROUP BY cat",
                       ["categorie", "valeur"],
                       [["A", -10], ["B", 20]])
        assert result != "pie"

    def test_numeric_first_col_not_pie(self):
        # col[0] numérique (mois entier) → pas pie
        result = _hint("répartition",
                       "SELECT mois, ca FROM t",
                       ["mois", "ca"],
                       [[1, 100], [2, 200]])
        assert result != "pie"

    def test_3_columns_neutral_question_not_pie(self):
        # 3 colonnes, aucun mot de composition dans la question → pas pie
        result = _hint("résultats par segment",
                       "SELECT cat, nb, ca FROM t GROUP BY cat",
                       ["categorie", "nb", "ca"],
                       [["A", 10, 500], ["B", 20, 1000]])
        assert result != "pie"


# ---------------------------------------------------------------------------
# BAR — signal de ranking (most/best/highest/…)
# ---------------------------------------------------------------------------
class TestBarFromRanking:
    def test_most_orders_is_bar(self):
        # "most" = ranking → bar même si 4 lignes et 2 colonnes (candidat pie)
        assert _hint("Which suppliers have the most orders?",
                     "SELECT wholesaler_name, COUNT(*) AS nb_orders FROM marts.fct_purchases GROUP BY wholesaler_name ORDER BY nb_orders DESC",
                     ["wholesaler_name", "nb_orders"],
                     [["UBIPHARM", 10], ["LABOREX", 7], ["TEDIS", 6], ["COPHARMA", 4]]) == "bar"

    def test_highest_revenue_is_bar(self):
        assert _hint("Which product has the highest revenue?",
                     "SELECT commercial_name, SUM(total_line_amount_fcfa) AS ca FROM t GROUP BY commercial_name ORDER BY ca DESC",
                     ["commercial_name", "ca"],
                     [["Paracetamol", 500000], ["Ibuprofen", 300000]]) == "bar"

    def test_best_selling_no_limit_is_bar(self):
        assert _hint("best selling products",
                     "SELECT commercial_name, SUM(total_units_sold) AS units FROM t GROUP BY commercial_name",
                     ["commercial_name", "units"],
                     [["ProdA", 200], ["ProdB", 150], ["ProdC", 100]]) == "bar"


# ---------------------------------------------------------------------------
# BAR — fallback comparaison
# ---------------------------------------------------------------------------
class TestBarFallback:
    def test_multiple_rows_returns_bar(self):
        assert _hint("ruptures par produit",
                     "SELECT produit, COUNT(*) FROM t GROUP BY produit",
                     ["produit", "nb_ruptures"],
                     [["ProdA", 5], ["ProdB", 3], ["ProdC", 8],
                      ["ProdD", 2], ["ProdE", 1], ["ProdF", 4]]) == "bar"

    def test_stocks_sous_seuil(self):
        assert _hint("quels produits sont sous le seuil ?",
                     "SELECT produit, stock FROM t WHERE stock < seuil",
                     ["produit", "stock"],
                     [["ParacetamolA", 5], ["IbuprofeneB", 2],
                      ["AmoxicillineC", 1], ["MetformineD", 0],
                      ["AmlodipineE", 3]]) == "bar"
