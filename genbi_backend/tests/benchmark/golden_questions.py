"""
30 paires (question, golden_sql) pour le benchmark qualité LLM.

Colonnes clés disponibles :
  fct_sales        : sale_id, pharmacy_id, client_id, sale_month, sale_year,
                     sale_date, total_amount_fcfa, client_type, payment_method,
                     is_anonymous, nb_products_in_cart, total_units_sold
  stg_raw__sale_details : sale_id, product_id, quantity, unit_price_fcfa, total_line_amount_fcfa
  dim_products     : product_id, commercial_name, therapeutic_class, product_category
  dim_clients      : client_id, client_type, full_name, is_chronic, loyalty_points
  fct_missed_sales : missed_sale_id, product_id, missed_date, missed_month, missed_year,
                     requested_quantity, client_type

expected_rows  : nombre de lignes attendu (None = non vérifié)
expected_scalar: valeur exacte attendue si 1 ligne / 1 colonne (None = non vérifié)
tolerance      : tolérance relative pour les scalaires (défaut 0.02 = 2%)
"""

GOLDEN_QUESTIONS = [

    # ── CA Simple ─────────────────────────────────────────────────────────────

    {
        "id": "Q01", "category": "ca_simple",
        "question": "Combien de ventes avons-nous eu au total ?",
        "golden_sql": (
            "SELECT COUNT(*) AS total_ventes FROM marts.fct_sales"
        ),
        "expected_rows": 1,
        "expected_scalar": 1617,
    },
    {
        "id": "Q02", "category": "ca_simple",
        "question": "Quel est mon chiffre d affaires par mois ?",
        "golden_sql": (
            "SELECT sale_month, sale_year, SUM(total_amount_fcfa) AS ca_fcfa "
            "FROM marts.fct_sales "
            "WHERE sale_year = 2026 "
            "GROUP BY sale_month, sale_year "
            "ORDER BY sale_year, sale_month"
        ),
        "expected_rows": 4,
        "expected_scalar": None,
    },
    {
        "id": "Q03", "category": "ca_simple",
        "question": "Quel est le CA total de ma pharmacie en 2026 ?",
        "golden_sql": (
            "SELECT SUM(total_amount_fcfa) AS ca_total_2026 "
            "FROM marts.fct_sales "
            "WHERE sale_year = 2026"
        ),
        "expected_rows": 1,
        "expected_scalar": 15074800,
    },
    {
        "id": "Q04", "category": "ca_simple",
        "question": "Quel est notre meilleur mois en chiffre d affaires ?",
        "golden_sql": (
            "SELECT sale_month AS mois, SUM(total_amount_fcfa) AS ca_fcfa "
            "FROM marts.fct_sales "
            "WHERE sale_year = 2026 "
            "GROUP BY sale_month "
            "ORDER BY ca_fcfa DESC "
            "LIMIT 1"
        ),
        "expected_rows": 1,
        "expected_scalar": None,
    },
    {
        "id": "Q05", "category": "ca_simple",
        "question": "Quel est mon CA total pour mars 2026 ?",
        "golden_sql": (
            "SELECT SUM(total_amount_fcfa) AS ca_mars_2026 "
            "FROM marts.fct_sales "
            "WHERE sale_month = 3 AND sale_year = 2026"
        ),
        "expected_rows": 1,
        "expected_scalar": 3602350,
    },
    {
        "id": "Q06", "category": "ca_simple",
        "question": "Quel est le CA de fevrier 2026 ?",
        "golden_sql": (
            "SELECT SUM(total_amount_fcfa) AS ca_fevrier_2026 "
            "FROM marts.fct_sales "
            "WHERE sale_month = 2 AND sale_year = 2026"
        ),
        "expected_rows": 1,
        "expected_scalar": 3440000,
    },

    # ── Produits ──────────────────────────────────────────────────────────────

    {
        "id": "Q07", "category": "produits",
        "question": "Quels sont mes 5 produits les plus vendus en quantite ?",
        "golden_sql": (
            "SELECT pd.commercial_name, SUM(sd.quantity) AS total_quantite "
            "FROM marts.fct_sales s "
            "JOIN staging.stg_raw__sale_details sd ON s.sale_id = sd.sale_id "
            "JOIN marts.dim_products pd ON sd.product_id = pd.product_id "
            "GROUP BY pd.commercial_name "
            "ORDER BY total_quantite DESC "
            "LIMIT 5"
        ),
        "expected_rows": 5,
        "expected_scalar": None,
    },
    {
        "id": "Q08", "category": "produits",
        "question": "Quels sont mes 10 produits les plus rentables en chiffre d affaires ?",
        "golden_sql": (
            "SELECT pd.commercial_name, SUM(sd.total_line_amount_fcfa) AS ca_total "
            "FROM marts.fct_sales s "
            "JOIN staging.stg_raw__sale_details sd ON s.sale_id = sd.sale_id "
            "JOIN marts.dim_products pd ON sd.product_id = pd.product_id "
            "GROUP BY pd.commercial_name "
            "ORDER BY ca_total DESC "
            "LIMIT 10"
        ),
        "expected_rows": 10,
        "expected_scalar": None,
    },
    {
        "id": "Q09", "category": "produits",
        "question": "Quel est le produit le plus vendu en quantite ?",
        "golden_sql": (
            "SELECT pd.commercial_name, SUM(sd.quantity) AS total_quantite "
            "FROM marts.fct_sales s "
            "JOIN staging.stg_raw__sale_details sd ON s.sale_id = sd.sale_id "
            "JOIN marts.dim_products pd ON sd.product_id = pd.product_id "
            "GROUP BY pd.commercial_name "
            "ORDER BY total_quantite DESC "
            "LIMIT 1"
        ),
        "expected_rows": 1,
        "expected_scalar": None,
    },
    {
        "id": "Q10", "category": "produits",
        "question": "Quelle est la quantite totale de medicaments vendus en 2026 ?",
        "golden_sql": (
            "SELECT SUM(sd.quantity) AS total_medicaments_vendus "
            "FROM marts.fct_sales s "
            "JOIN staging.stg_raw__sale_details sd ON s.sale_id = sd.sale_id "
            "WHERE s.sale_year = 2026"
        ),
        "expected_rows": 1,
        "expected_scalar": 4901,
    },
    {
        "id": "Q11", "category": "produits",
        "question": "Quel est mon CA par categorie de produit ?",
        "golden_sql": (
            "SELECT pd.product_category, SUM(sd.total_line_amount_fcfa) AS ca_total "
            "FROM marts.fct_sales s "
            "JOIN staging.stg_raw__sale_details sd ON s.sale_id = sd.sale_id "
            "JOIN marts.dim_products pd ON sd.product_id = pd.product_id "
            "GROUP BY pd.product_category "
            "ORDER BY ca_total DESC"
        ),
        "expected_rows": 2,
        "expected_scalar": None,
    },
    {
        "id": "Q12", "category": "produits",
        "question": "Quels sont les 3 produits les plus vendus ?",
        "golden_sql": (
            "SELECT pd.commercial_name, SUM(sd.quantity) AS total_quantite "
            "FROM marts.fct_sales s "
            "JOIN staging.stg_raw__sale_details sd ON s.sale_id = sd.sale_id "
            "JOIN marts.dim_products pd ON sd.product_id = pd.product_id "
            "GROUP BY pd.commercial_name "
            "ORDER BY total_quantite DESC "
            "LIMIT 3"
        ),
        "expected_rows": 3,
        "expected_scalar": None,
    },

    # ── Clients ───────────────────────────────────────────────────────────────

    {
        "id": "Q13", "category": "clients",
        "question": "Quel est le CA par type de client ?",
        "golden_sql": (
            "SELECT client_type, SUM(total_amount_fcfa) AS ca_total "
            "FROM marts.fct_sales "
            "WHERE sale_year = 2026 "
            "GROUP BY client_type "
            "ORDER BY ca_total DESC"
        ),
        "expected_rows": 2,
        "expected_scalar": None,
    },
    {
        "id": "Q14", "category": "clients",
        "question": "Combien de clients distincts avons-nous servis en 2026 ?",
        "golden_sql": (
            "SELECT COUNT(DISTINCT client_id) AS nb_clients_distincts "
            "FROM marts.fct_sales "
            "WHERE sale_year = 2026 AND is_anonymous = false"
        ),
        "expected_rows": 1,
        "expected_scalar": 100,
    },
    {
        "id": "Q15", "category": "clients",
        "question": "Quelle est la repartition des ventes par mode de paiement ?",
        "golden_sql": (
            "SELECT payment_method, COUNT(*) AS nb_ventes "
            "FROM marts.fct_sales "
            "WHERE sale_year = 2026 "
            "GROUP BY payment_method "
            "ORDER BY nb_ventes DESC"
        ),
        "expected_rows": None,
        "expected_scalar": None,
    },
    {
        "id": "Q16", "category": "clients",
        "question": "Combien de ventes aux assures avons-nous eu en 2026 ?",
        "golden_sql": (
            "SELECT COUNT(*) AS nb_ventes_assures "
            "FROM marts.fct_sales "
            "WHERE client_type = 'Assuré' AND sale_year = 2026"
        ),
        "expected_rows": 1,
        "expected_scalar": None,
    },

    # ── Ruptures de stock ─────────────────────────────────────────────────────

    {
        "id": "Q17", "category": "ruptures",
        "question": "Quels produits sont en rupture de stock ?",
        "golden_sql": (
            "SELECT DISTINCT pd.commercial_name "
            "FROM marts.fct_missed_sales ms "
            "JOIN marts.dim_products pd ON ms.product_id = pd.product_id"
        ),
        "expected_rows": 26,
        "expected_scalar": None,
    },
    {
        "id": "Q18", "category": "ruptures",
        "question": "Combien de ruptures de stock ai-je eu par mois ?",
        "golden_sql": (
            "SELECT missed_month AS mois, COUNT(*) AS nb_ruptures "
            "FROM marts.fct_missed_sales "
            "GROUP BY missed_month "
            "ORDER BY missed_month"
        ),
        "expected_rows": 4,
        "expected_scalar": None,
    },
    {
        "id": "Q19", "category": "ruptures",
        "question": "Quels sont les 5 medicaments avec le plus de ruptures de stock ?",
        "golden_sql": (
            "SELECT pd.commercial_name, COUNT(*) AS nb_ruptures "
            "FROM marts.fct_missed_sales ms "
            "JOIN marts.dim_products pd ON ms.product_id = pd.product_id "
            "GROUP BY pd.commercial_name "
            "ORDER BY nb_ruptures DESC "
            "LIMIT 5"
        ),
        "expected_rows": 5,
        "expected_scalar": None,
    },
    {
        "id": "Q20", "category": "ruptures",
        "question": "Quel est le nombre total de ruptures de stock ?",
        "golden_sql": (
            "SELECT COUNT(*) AS total_ruptures FROM marts.fct_missed_sales"
        ),
        "expected_rows": 1,
        "expected_scalar": 64,
    },
    {
        "id": "Q21", "category": "ruptures",
        "question": "Combien de produits differents ont eu des ruptures de stock ?",
        "golden_sql": (
            "SELECT COUNT(DISTINCT product_id) AS nb_produits_en_rupture "
            "FROM marts.fct_missed_sales"
        ),
        "expected_rows": 1,
        "expected_scalar": 26,
    },

    # ── Stats globales ────────────────────────────────────────────────────────

    {
        "id": "Q22", "category": "stats",
        "question": "Quel est le montant moyen d une vente en 2026 ?",
        "golden_sql": (
            "SELECT AVG(total_amount_fcfa) AS montant_moyen_fcfa "
            "FROM marts.fct_sales "
            "WHERE sale_year = 2026"
        ),
        "expected_rows": 1,
        "expected_scalar": None,
    },
    {
        "id": "Q23", "category": "stats",
        "question": "Combien de ventes avons-nous eu en mars 2026 ?",
        "golden_sql": (
            "SELECT COUNT(*) AS nb_ventes "
            "FROM marts.fct_sales "
            "WHERE sale_month = 3 AND sale_year = 2026"
        ),
        "expected_rows": 1,
        "expected_scalar": 411,
    },
    {
        "id": "Q24", "category": "stats",
        "question": "Quelle est l evolution du nombre de ventes par mois ?",
        "golden_sql": (
            "SELECT sale_month AS mois, COUNT(*) AS nb_ventes "
            "FROM marts.fct_sales "
            "WHERE sale_year = 2026 "
            "GROUP BY sale_month "
            "ORDER BY sale_month"
        ),
        "expected_rows": 4,
        "expected_scalar": None,
    },
    {
        "id": "Q25", "category": "stats",
        "question": "Combien de ventes avons-nous eu en mai 2026 ?",
        "golden_sql": (
            "SELECT COUNT(*) AS nb_ventes "
            "FROM marts.fct_sales "
            "WHERE sale_month = 5 AND sale_year = 2026"
        ),
        "expected_rows": 1,
        "expected_scalar": 416,
    },
    {
        "id": "Q26", "category": "stats",
        "question": "Quel est le CA d avril 2026 ?",
        "golden_sql": (
            "SELECT SUM(total_amount_fcfa) AS ca_avril_2026 "
            "FROM marts.fct_sales "
            "WHERE sale_month = 4 AND sale_year = 2026"
        ),
        "expected_rows": 1,
        "expected_scalar": 4080700,
    },

    # ── Jointures complexes ───────────────────────────────────────────────────

    {
        "id": "Q27", "category": "complexe",
        "question": "Quels sont les 5 produits les plus vendus par les assures ?",
        "golden_sql": (
            "SELECT pd.commercial_name, SUM(sd.quantity) AS total_quantite "
            "FROM marts.fct_sales s "
            "JOIN staging.stg_raw__sale_details sd ON s.sale_id = sd.sale_id "
            "JOIN marts.dim_products pd ON sd.product_id = pd.product_id "
            "WHERE s.client_type = 'Assuré' "
            "GROUP BY pd.commercial_name "
            "ORDER BY total_quantite DESC "
            "LIMIT 5"
        ),
        "expected_rows": 5,
        "expected_scalar": None,
    },
    {
        "id": "Q28", "category": "complexe",
        "question": "Combien de ruptures avons-nous eu en mars 2026 ?",
        "golden_sql": (
            "SELECT COUNT(*) AS nb_ruptures_mars "
            "FROM marts.fct_missed_sales "
            "WHERE missed_month = 3"
        ),
        "expected_rows": 1,
        "expected_scalar": 17,
    },
    {
        "id": "Q29", "category": "complexe",
        "question": "Quel est le CA total des medicaments hors parapharmacie ?",
        "golden_sql": (
            "SELECT SUM(sd.total_line_amount_fcfa) AS ca_medicaments "
            "FROM marts.fct_sales s "
            "JOIN staging.stg_raw__sale_details sd ON s.sale_id = sd.sale_id "
            "JOIN marts.dim_products pd ON sd.product_id = pd.product_id "
            "WHERE pd.product_category = 'Médicament' "
            "AND s.sale_year = 2026"
        ),
        "expected_rows": 1,
        "expected_scalar": None,
    },
    {
        "id": "Q30", "category": "complexe",
        "question": "Quels sont les medicaments antipaludeens que nous vendons ?",
        "golden_sql": (
            "SELECT DISTINCT pd.commercial_name "
            "FROM staging.stg_raw__sale_details sd "
            "JOIN marts.dim_products pd ON sd.product_id = pd.product_id "
            "WHERE pd.therapeutic_class = 'Antipaludéen'"
        ),
        "expected_rows": 2,
        "expected_scalar": None,
    },

    # ── Prédiction de rupture ─────────────────────────────────────────────────

    {
        "id": "Q31", "category": "prediction",
        "question": "Dans combien de jours mes stocks vont-ils s epuiser ?",
        "golden_sql": (
            "SELECT sk.commercial_name, "
            "sk.quantity_in_stock, "
            "ROUND(AVG(sd.quantity), 2) AS ventes_moy_par_jour, "
            "ROUND(sk.quantity_in_stock / NULLIF(AVG(sd.quantity), 0)) AS jours_restants "
            "FROM marts.dim_stocks sk "
            "JOIN staging.stg_raw__sale_details sd ON sk.product_id = sd.product_id "
            "JOIN marts.fct_sales s ON sd.sale_id = s.sale_id "
            "WHERE s.sale_date >= CURRENT_DATE - INTERVAL '30 days' "
            "GROUP BY sk.commercial_name, sk.quantity_in_stock "
            "ORDER BY jours_restants ASC"
        ),
        "expected_rows": None,
        "expected_scalar": None,
    },
    {
        "id": "Q32", "category": "prediction",
        "question": "Quels produits vont etre en rupture dans moins de 7 jours ?",
        "golden_sql": (
            "SELECT sk.commercial_name, "
            "sk.quantity_in_stock, "
            "ROUND(sk.quantity_in_stock / NULLIF(AVG(sd.quantity), 0)) AS jours_restants "
            "FROM marts.dim_stocks sk "
            "JOIN staging.stg_raw__sale_details sd ON sk.product_id = sd.product_id "
            "JOIN marts.fct_sales s ON sd.sale_id = s.sale_id "
            "WHERE s.sale_date >= CURRENT_DATE - INTERVAL '30 days' "
            "GROUP BY sk.commercial_name, sk.quantity_in_stock "
            "HAVING ROUND(sk.quantity_in_stock / NULLIF(AVG(sd.quantity), 0)) <= 7 "
            "ORDER BY jours_restants ASC"
        ),
        "expected_rows": None,
        "expected_scalar": None,
    },

    # ── Tiers-payant & paiements ──────────────────────────────────────────────

    {
        "id": "Q33", "category": "paiements",
        "question": "Quel est mon chiffre d affaires tiers-payant ?",
        "golden_sql": (
            "SELECT SUM(total_amount_fcfa) AS ca_tiers_payant "
            "FROM marts.fct_sales "
            "WHERE payment_method = 'Tiers-Payant'"
        ),
        "expected_rows": 1,
        "expected_scalar": None,
    },
    {
        "id": "Q34", "category": "paiements",
        "question": "Quelle est la repartition de mon CA par mode de paiement ?",
        "golden_sql": (
            "SELECT payment_method, "
            "SUM(total_amount_fcfa) AS ca_total, "
            "COUNT(*) AS nb_ventes "
            "FROM marts.fct_sales "
            "GROUP BY payment_method "
            "ORDER BY ca_total DESC"
        ),
        "expected_rows": None,
        "expected_scalar": None,
    },
    {
        "id": "Q35", "category": "paiements",
        "question": "Combien de ventes ont ete payees par Wave ou Orange Money ?",
        "golden_sql": (
            "SELECT payment_method, COUNT(*) AS nb_ventes "
            "FROM marts.fct_sales "
            "WHERE payment_method IN ('Wave', 'Orange Money') "
            "GROUP BY payment_method "
            "ORDER BY nb_ventes DESC"
        ),
        "expected_rows": None,
        "expected_scalar": None,
    },

    # ── Clients chroniques & fidélité ─────────────────────────────────────────

    {
        "id": "Q36", "category": "clients_fidelite",
        "question": "Combien de clients chroniques avons-nous ?",
        "golden_sql": (
            "SELECT COUNT(*) AS nb_clients_chroniques "
            "FROM marts.dim_clients "
            "WHERE is_chronic = TRUE"
        ),
        "expected_rows": 1,
        "expected_scalar": None,
    },
    {
        "id": "Q37", "category": "clients_fidelite",
        "question": "Quels sont mes clients avec le plus de points de fidelite ?",
        "golden_sql": (
            "SELECT full_name, loyalty_points "
            "FROM marts.dim_clients "
            "WHERE is_anonymous = FALSE "
            "ORDER BY loyalty_points DESC "
            "LIMIT 10"
        ),
        "expected_rows": None,
        "expected_scalar": None,
    },
    {
        "id": "Q38", "category": "clients_fidelite",
        "question": "Quel est le CA genere par les clients assures ?",
        "golden_sql": (
            "SELECT SUM(total_amount_fcfa) AS ca_assures "
            "FROM marts.fct_sales "
            "WHERE client_type = 'Assuré'"
        ),
        "expected_rows": 1,
        "expected_scalar": None,
    },

    # ── Marge & rentabilité ───────────────────────────────────────────────────

    {
        "id": "Q39", "category": "marge",
        "question": "Quelle est la valeur totale de mes achats par fournisseur ?",
        "golden_sql": (
            "SELECT fp.wholesaler_name, "
            "SUM(fp.purchase_price_fcfa * fp.quantity_received) AS valeur_achat_fcfa "
            "FROM marts.fct_purchases fp "
            "GROUP BY fp.wholesaler_name "
            "ORDER BY valeur_achat_fcfa DESC"
        ),
        "expected_rows": None,
        "expected_scalar": None,
    },
    {
        "id": "Q40", "category": "marge",
        "question": "Quel est le taux de service de mes fournisseurs ?",
        "golden_sql": (
            "SELECT fp.wholesaler_name, "
            "ROUND(100.0 * SUM(fp.quantity_received) / NULLIF(SUM(fp.quantity_ordered), 0), 1) AS taux_service_pct "
            "FROM marts.fct_purchases fp "
            "GROUP BY fp.wholesaler_name "
            "ORDER BY taux_service_pct DESC"
        ),
        "expected_rows": None,
        "expected_scalar": None,
    },

    # ── Retours fournisseurs ──────────────────────────────────────────────────

    {
        "id": "Q41", "category": "retours",
        "question": "Combien de retours fournisseurs avons-nous effectue ?",
        "golden_sql": (
            "SELECT COUNT(*) AS nb_retours "
            "FROM marts.fct_wholesaler_returns"
        ),
        "expected_rows": 1,
        "expected_scalar": None,
    },
    {
        "id": "Q42", "category": "retours",
        "question": "Quel est le montant total de mes avoirs fournisseurs ?",
        "golden_sql": (
            "SELECT SUM(credit_note_amount_fcfa) AS total_avoirs_fcfa "
            "FROM marts.fct_wholesaler_returns"
        ),
        "expected_rows": 1,
        "expected_scalar": None,
    },
    {
        "id": "Q43", "category": "retours",
        "question": "Quels produits avons-nous le plus retournes aux fournisseurs ?",
        "golden_sql": (
            "SELECT pd.commercial_name, "
            "SUM(wr.quantity_returned) AS total_retourne "
            "FROM marts.fct_wholesaler_returns wr "
            "JOIN marts.dim_products pd ON wr.product_id = pd.product_id "
            "GROUP BY pd.commercial_name "
            "ORDER BY total_retourne DESC "
            "LIMIT 10"
        ),
        "expected_rows": None,
        "expected_scalar": None,
    },

    # ── Clients chroniques ────────────────────────────────────────────────────

    {
        "id": "Q44", "category": "clients",
        "question": "combien de clients chroniques avons-nous ?",
        "golden_sql": (
            "SELECT COUNT(*) AS nb_clients_chroniques "
            "FROM marts.dim_clients "
            "WHERE is_chronic = TRUE"
        ),
        "expected_rows": 1,
        "expected_scalar": None,
    },
]
