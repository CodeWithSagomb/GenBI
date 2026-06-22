"""
Golden set — 50 questions métier avec critères de validation.

Chaque question définit des checks programmatiques :
  sql_must_contain     : mots-clés obligatoires dans le SQL généré
  sql_must_not_contain : patterns interdits (hallucinations connues)
  row_count            : nombre de lignes attendu exact (None = pas de contrainte)
  row_count_min        : borne inférieure du nombre de lignes
  row_count_max        : borne supérieure du nombre de lignes
  value_range          : {"col": int, "min": float, "max": float} — valeur numérique attendue
  viz_hint             : type de graphique attendu ("line"|"bar"|"pie"|None)
  insight_forbidden    : mots/expressions interdits dans l'insight
"""

GOLDEN_SET = [

    # ── FINANCE (8) ────────────────────────────────────────────────────────────
    {
        "id": "F001", "category": "finance",
        "question": "Quel est mon chiffre d'affaires total ?",
        "checks": {
            "sql_must_contain":     ["SUM", "total_amount_fcfa", "fct_sales"],
            "sql_must_not_contain": ["fct_purchases", "GROUP BY"],
            "row_count": 1,
            "value_range": {"col": 0, "min": 14_000_000, "max": 20_000_000},
            "viz_hint": None,
            "insight_forbidden": ["millions", "Le pharmacien"],
        }
    },
    {
        "id": "F002", "category": "finance",
        "question": "Comment évolue mon chiffre d'affaires par mois ?",
        "checks": {
            "sql_must_contain":     ["SUM", "total_amount_fcfa", "sale_month", "GROUP BY"],
            "sql_must_not_contain": ["LIMIT", "WHERE sale_month"],
            "row_count_min": 3, "row_count_max": 12,
            "viz_hint": "line",
            "insight_forbidden": ["millions", "trimestre", "semestre"],
        }
    },
    {
        "id": "F003", "category": "finance",
        "question": "Quelle est ma marge brute totale ?",
        "checks": {
            "sql_must_contain":     ["public_price_fcfa", "purchase_price_fcfa", "quantity_ordered", "fct_purchases"],
            "sql_must_not_contain": ["fct_sales", "total_amount_fcfa"],
            "row_count": 1,
            "value_range": {"col": 0, "min": 1_500_000, "max": 5_000_000},
            "viz_hint": None,
            "insight_forbidden": ["millions", "23 334"],
        }
    },
    {
        "id": "F004", "category": "finance",
        "question": "Quel est le montant total de mes achats fournisseurs ?",
        "checks": {
            "sql_must_contain":     ["fct_purchases"],
            "sql_must_not_contain": ["fct_sales"],
            "row_count_min": 1,
            "insight_forbidden": ["millions", "Le pharmacien"],
        }
    },
    {
        "id": "F005", "category": "finance",
        "question": "Quels sont mes 3 meilleurs mois en chiffre d'affaires ?",
        "checks": {
            "sql_must_contain":     ["SUM", "total_amount_fcfa", "sale_month", "LIMIT 3"],
            "row_count": 3,
            "viz_hint": "bar",
            "insight_forbidden": ["millions"],
        }
    },
    {
        "id": "F006", "category": "finance",
        "question": "Quel est mon chiffre d'affaires par mode de paiement ?",
        "checks": {
            "sql_must_contain":     ["SUM", "total_amount_fcfa", "payment_method", "GROUP BY"],
            "sql_must_not_contain": ["PIVOT", "CASE WHEN"],
            "row_count_min": 2, "row_count_max": 5,
            "viz_hint": "pie",
            "insight_forbidden": ["millions"],
        }
    },
    {
        "id": "F007", "category": "finance",
        "question": "Quel est le montant total collecté via le tiers-payant ?",
        "checks": {
            "sql_must_contain":     ["fct_sales"],
            "sql_must_not_contain": [],
            "row_count": 1,
            "viz_hint": None,
            "insight_forbidden": ["millions", "Le pharmacien"],
        }
    },
    {
        "id": "F008", "category": "finance",
        "question": "Quelle est ma TVA collectée totale ?",
        "checks": {
            "sql_must_contain":     ["vat_amount_fcfa", "fct_sales"],
            "row_count": 1,
            "viz_hint": None,
            "insight_forbidden": ["millions"],
        }
    },

    # ── PRODUITS (8) ──────────────────────────────────────────────────────────
    {
        "id": "P001", "category": "produits",
        "question": "Quels sont mes 5 produits les plus vendus en quantité ?",
        "checks": {
            "sql_must_contain":     ["LIMIT 5", "stg_raw__sale_details"],
            "sql_must_not_contain": ["fct_purchases"],
            "row_count": 5,
            "viz_hint": "bar",
            "insight_forbidden": ["millions", "FCFA"],
        }
    },
    {
        "id": "P002", "category": "produits",
        "question": "Quels sont mes 5 produits les plus rentables en marge ?",
        "checks": {
            "sql_must_contain":     ["public_price_fcfa", "purchase_price_fcfa", "fct_purchases", "LIMIT 5"],
            "sql_must_not_contain": ["fct_sales"],
            "row_count": 5,
            "viz_hint": "bar",
            "insight_forbidden": ["millions"],
        }
    },
    {
        "id": "P003", "category": "produits",
        "question": "Quelles classes thérapeutiques génèrent le plus de chiffre d'affaires ?",
        "checks": {
            "sql_must_contain":     ["therapeutic_class", "GROUP BY"],
            "sql_must_not_contain": ["product_category"],
            "row_count_min": 5,
            "viz_hint": "bar",
            "insight_forbidden": ["millions"],
        }
    },
    {
        "id": "P004", "category": "produits",
        "question": "Quelle est la part des médicaments génériques versus princeps dans mes ventes ?",
        "checks": {
            "sql_must_contain":     ["is_generic", "GROUP BY"],
            "sql_must_not_contain": ["PIVOT", "CASE WHEN"],
            "row_count": 2,
            "viz_hint": "pie",
            "insight_forbidden": ["millions"],
        }
    },
    {
        "id": "P005", "category": "produits",
        "question": "Quels produits d'origine locale se vendent le mieux ?",
        "checks": {
            "sql_must_contain":     ["origin", "Local"],
            "sql_must_not_contain": ["Sénégal", "France"],
            "row_count_min": 1,
            "viz_hint": "bar",
            "insight_forbidden": ["millions", "Importé"],
        }
    },
    {
        "id": "P006", "category": "produits",
        "question": "Quel est mon produit le plus rentable en marge ?",
        "checks": {
            "sql_must_contain":     ["public_price_fcfa", "purchase_price_fcfa", "fct_purchases"],
            "sql_must_not_contain": ["fct_sales"],
            "row_count": 1,
            "viz_hint": None,
            "insight_forbidden": ["millions", "23 334"],
        }
    },
    {
        "id": "P007", "category": "produits",
        "question": "Quelle est la répartition des ventes par laboratoire fabricant ?",
        "checks": {
            "sql_must_contain":     ["laboratory", "GROUP BY"],
            "row_count_min": 3,
            "viz_hint": "bar",
            "insight_forbidden": ["millions"],
        }
    },
    {
        "id": "P008", "category": "produits",
        "question": "Quelle est la répartition de mes ventes par forme galénique ?",
        "checks": {
            "sql_must_contain":     ["form", "GROUP BY"],
            "sql_must_not_contain": ["PIVOT"],
            "row_count_min": 2,
            "insight_forbidden": ["millions"],
        }
    },

    # ── STOCKS (8) ────────────────────────────────────────────────────────────
    {
        "id": "S001", "category": "stocks",
        "question": "Quels produits sont sous le seuil de sécurité de stock ?",
        "checks": {
            "sql_must_contain":     ["is_below_safety_threshold", "TRUE", "dim_stocks"],
            "sql_must_not_contain": ["quantity_in_stock <= 0", "quantity_in_stock = 0"],
            "row_count_min": 1,
            "viz_hint": "bar",
            "insight_forbidden": ["millions", "FCFA"],
        }
    },
    {
        "id": "S002", "category": "stocks",
        "question": "Combien de produits sont en rupture de stock ?",
        "checks": {
            "sql_must_contain":     ["COUNT", "fct_missed_sales"],
            "sql_must_not_contain": ["SELECT DISTINCT commercial_name"],
            "row_count": 1,
            "value_range": {"col": 0, "min": 20, "max": 30},
            "viz_hint": None,
            "insight_forbidden": ["30 produits", "FCFA"],
        }
    },
    {
        "id": "S003", "category": "stocks",
        "question": "Quels lots expirent dans les 30 prochains jours ?",
        "checks": {
            "sql_must_contain":     ["expiration_date", "dim_stocks"],
            "sql_must_not_contain": [],
            "row_count_min": 1,
            "viz_hint": "bar",
            "insight_forbidden": ["millions", "FCFA", "7 lots"],
        }
    },
    {
        "id": "S004", "category": "stocks",
        "question": "Quels lots expirent dans les 7 prochains jours ?",
        "checks": {
            "sql_must_contain":     ["expiration_date", "dim_stocks"],
            "row_count_min": 0,
            "viz_hint": "bar",
            "insight_forbidden": ["millions"],
        }
    },
    {
        "id": "S005", "category": "stocks",
        "question": "Quel produit a le plus grand stock actuel ?",
        "checks": {
            "sql_must_contain":     ["quantity_in_stock", "dim_stocks"],
            "sql_must_not_contain": ["fct_sales"],
            "row_count_min": 1,
            "viz_hint": None,
            "insight_forbidden": ["millions", "FCFA"],
        }
    },
    {
        "id": "S006", "category": "stocks",
        "question": "Combien de lots sont en stock en ce moment ?",
        "checks": {
            "sql_must_contain":     ["COUNT", "dim_stocks"],
            "row_count": 1,
            "viz_hint": None,
            "insight_forbidden": ["FCFA", "millions"],
        }
    },
    {
        "id": "S007", "category": "stocks",
        "question": "Quels sont les produits avec le moins de stock ?",
        "checks": {
            "sql_must_contain":     ["quantity_in_stock", "dim_stocks", "ORDER BY"],
            "row_count_min": 1,
            "viz_hint": "bar",
            "insight_forbidden": ["millions", "FCFA"],
        }
    },
    {
        "id": "S008", "category": "stocks",
        "question": "Quelle est la valeur totale de mon stock en prix public ?",
        "checks": {
            "sql_must_contain":     ["public_price_fcfa", "quantity_in_stock", "dim_stocks"],
            "row_count": 1,
            "viz_hint": None,
            "insight_forbidden": ["millions"],
        }
    },

    # ── RUPTURES (6) ──────────────────────────────────────────────────────────
    {
        "id": "R001", "category": "ruptures",
        "question": "Quel produit a eu le plus de ventes manquées ?",
        "checks": {
            "sql_must_contain":     ["fct_missed_sales"],
            "sql_must_not_contain": ["fct_sales"],
            "row_count": 1,
            "viz_hint": None,
            "insight_forbidden": ["FCFA", "millions"],
        }
    },
    {
        "id": "R002", "category": "ruptures",
        "question": "Combien de ventes manquées j'ai eu au total ?",
        "checks": {
            "sql_must_contain":     ["COUNT", "fct_missed_sales"],
            "sql_must_not_contain": ["fct_sales"],
            "row_count": 1,
            "value_range": {"col": 0, "min": 1, "max": 500},
            "viz_hint": None,
            "insight_forbidden": ["FCFA", "millions"],
        }
    },
    {
        "id": "R003", "category": "ruptures",
        "question": "Comment évoluent les ventes manquées par mois ?",
        "checks": {
            "sql_must_contain":     ["missed_month", "fct_missed_sales", "GROUP BY"],
            "sql_must_not_contain": ["sale_month", "fct_sales"],
            "row_count_min": 2,
            "viz_hint": "line",
            "insight_forbidden": ["FCFA", "millions"],
        }
    },
    {
        "id": "R004", "category": "ruptures",
        "question": "Quel est le mois avec le plus de ruptures ?",
        "checks": {
            "sql_must_contain":     ["missed_month", "fct_missed_sales"],
            "sql_must_not_contain": ["fct_sales"],
            "row_count": 1,
            "viz_hint": None,
            "insight_forbidden": ["FCFA", "millions"],
        }
    },
    {
        "id": "R005", "category": "ruptures",
        "question": "Quels produits ont eu des ruptures en février ?",
        "checks": {
            "sql_must_contain":     ["fct_missed_sales"],
            "sql_must_not_contain": ["sale_month", "fct_sales"],
            "row_count_min": 1,
            "viz_hint": "bar",
            "insight_forbidden": ["FCFA", "millions"],
        }
    },
    {
        "id": "R006", "category": "ruptures",
        "question": "Combien de produits différents ont eu des ruptures ?",
        "checks": {
            "sql_must_contain":     ["COUNT", "DISTINCT", "fct_missed_sales"],
            "row_count": 1,
            "value_range": {"col": 0, "min": 20, "max": 30},
            "viz_hint": None,
            "insight_forbidden": ["FCFA", "millions", "30 produits"],
        }
    },

    # ── CLIENTS (6) ───────────────────────────────────────────────────────────
    {
        "id": "C001", "category": "clients",
        "question": "Quelle est la répartition de mes ventes par mode de paiement ?",
        "checks": {
            "sql_must_contain":     ["payment_method", "GROUP BY", "fct_sales"],
            "sql_must_not_contain": ["PIVOT", "CASE WHEN", "Assurance", "Cash"],
            "row_count_min": 2, "row_count_max": 5,
            "viz_hint": "pie",
            "insight_forbidden": ["millions", "Assurance", "Cash"],
        }
    },
    {
        "id": "C002", "category": "clients",
        "question": "Quelle est la répartition de mes ventes par type de client ?",
        "checks": {
            "sql_must_contain":     ["client_type", "GROUP BY", "fct_sales"],
            "sql_must_not_contain": ["PIVOT", "sales_rep"],
            "row_count_min": 2, "row_count_max": 3,
            "viz_hint": "pie",
            "insight_forbidden": ["millions", "Le pharmacien"],
        }
    },
    {
        "id": "C003", "category": "clients",
        "question": "Quel jour de la semaine génère le plus de ventes ?",
        "checks": {
            "sql_must_contain":     ["sale_dow", "fct_sales"],
            "sql_must_not_contain": ["sale_date"],
            "row_count_min": 1,
            "viz_hint": None,
            "insight_forbidden": ["millions", "FCFA", "Lundi"],
        }
    },
    {
        "id": "C004", "category": "clients",
        "question": "Quel est le panier moyen par vente ?",
        "checks": {
            "sql_must_contain":     ["nb_products_in_cart", "AVG", "fct_sales"],
            "row_count": 1,
            "viz_hint": None,
            "insight_forbidden": ["millions", "FCFA"],
        }
    },
    {
        "id": "C005", "category": "clients",
        "question": "Combien de ventes ont été faites avec des clients anonymes ?",
        "checks": {
            "sql_must_contain":     ["is_anonymous", "fct_sales"],
            "row_count_min": 1,
            "viz_hint": None,
            "insight_forbidden": ["millions", "FCFA"],
        }
    },
    {
        "id": "C006", "category": "clients",
        "question": "Quelle est la part des ventes assurées versus non assurées ?",
        "checks": {
            "sql_must_contain":     ["client_type", "GROUP BY", "fct_sales"],
            "sql_must_not_contain": ["PIVOT", "sales_rep_id"],
            "row_count_min": 2,
            "viz_hint": "pie",
            "insight_forbidden": ["millions"],
        }
    },

    # ── FOURNISSEURS (6) ──────────────────────────────────────────────────────
    {
        "id": "FO001", "category": "fournisseurs",
        "question": "Quel fournisseur me livre le plus souvent ?",
        "checks": {
            "sql_must_contain":     ["wholesaler_name", "fct_purchases"],
            "sql_must_not_contain": ["fct_sales"],
            "row_count": 1,
            "viz_hint": None,
            "insight_forbidden": ["millions", "ventes", "orders", "transactions"],
        }
    },
    {
        "id": "FO002", "category": "fournisseurs",
        "question": "Quel est le montant total de mes achats par fournisseur ?",
        "checks": {
            "sql_must_contain":     ["wholesaler_name", "fct_purchases", "GROUP BY"],
            "sql_must_not_contain": ["fct_sales"],
            "row_count_min": 2,
            "insight_forbidden": ["millions"],
        }
    },
    {
        "id": "FO003", "category": "fournisseurs",
        "question": "Quel est le délai moyen de livraison par fournisseur ?",
        "checks": {
            "sql_must_contain":     ["fct_purchases", "delivery_date", "order_date"],
            "row_count_min": 1,
            "insight_forbidden": ["millions", "FCFA"],
        }
    },
    {
        "id": "FO004", "category": "fournisseurs",
        "question": "Quel est le taux de service de mes fournisseurs ?",
        "checks": {
            "sql_must_contain":     ["fct_purchases"],
            "sql_must_not_contain": ["fct_sales"],
            "row_count_min": 1,
            "insight_forbidden": ["millions"],
        }
    },
    {
        "id": "FO005", "category": "fournisseurs",
        "question": "Comment évoluent mes achats par mois ?",
        "checks": {
            "sql_must_contain":     ["fct_purchases", "order_date", "GROUP BY"],
            "sql_must_not_contain": ["fct_sales", "sale_month"],
            "row_count_min": 2,
            "viz_hint": "line",
            "insight_forbidden": ["millions"],
        }
    },
    {
        "id": "FO006", "category": "fournisseurs",
        "question": "Quels fournisseurs ont le meilleur taux de service ?",
        "checks": {
            "sql_must_contain":     ["wholesaler_name", "fct_purchases"],
            "row_count_min": 2,
            "insight_forbidden": ["millions"],
        }
    },

    # ── OPÉRATIONNEL (8) ──────────────────────────────────────────────────────
    {
        "id": "O001", "category": "operationnel",
        "question": "Combien de ventes j'ai réalisées au total ?",
        "checks": {
            "sql_must_contain":     ["COUNT", "fct_sales"],
            "sql_must_not_contain": ["fct_missed_sales"],
            "row_count": 1,
            "value_range": {"col": 0, "min": 1_000, "max": 3_000},
            "viz_hint": None,
            "insight_forbidden": ["FCFA", "millions"],
        }
    },
    {
        "id": "O002", "category": "operationnel",
        "question": "Combien de ventes j'ai réalisées par mois ?",
        "checks": {
            "sql_must_contain":     ["COUNT", "fct_sales", "sale_month", "GROUP BY"],
            "row_count_min": 3, "row_count_max": 12,
            "viz_hint": "line",
            "insight_forbidden": ["FCFA", "millions"],
        }
    },
    {
        "id": "O003", "category": "operationnel",
        "question": "Quelle est la répartition de mes ventes par jour de la semaine ?",
        "checks": {
            "sql_must_contain":     ["sale_dow", "fct_sales", "GROUP BY"],
            "row_count_min": 5, "row_count_max": 7,
            "viz_hint": "bar",
            "insight_forbidden": ["millions"],
        }
    },
    {
        "id": "O004", "category": "operationnel",
        "question": "Combien de produits différents ai-je vendus au total ?",
        "checks": {
            "sql_must_contain":     ["COUNT", "DISTINCT", "stg_raw__sale_details"],
            "row_count": 1,
            "viz_hint": None,
            "insight_forbidden": ["FCFA", "millions"],
        }
    },
    {
        "id": "O005", "category": "operationnel",
        "question": "Quel est le nombre total d'unités vendues ?",
        "checks": {
            "sql_must_contain":     ["total_units_sold", "fct_sales"],
            "row_count": 1,
            "viz_hint": None,
            "insight_forbidden": ["FCFA", "millions"],
        }
    },
    {
        "id": "O006", "category": "operationnel",
        "question": "Combien de commandes fournisseurs ai-je passées au total ?",
        "checks": {
            "sql_must_contain":     ["COUNT", "fct_purchases"],
            "sql_must_not_contain": ["fct_sales"],
            "row_count": 1,
            "viz_hint": None,
            "insight_forbidden": ["FCFA", "millions", "ventes", "orders"],
        }
    },
    {
        "id": "O007", "category": "operationnel",
        "question": "Quel assureur prend en charge le plus de ventes ?",
        "checks": {
            "sql_must_contain":     ["dim_insurers", "GROUP BY"],
            "sql_must_not_contain": ["sales_rep"],
            "row_count_min": 1,
            "viz_hint": None,
            "insight_forbidden": ["millions"],
        }
    },
    {
        "id": "O008", "category": "operationnel",
        "question": "Quelle est la répartition de mes ventes par assureur ?",
        "checks": {
            "sql_must_contain":     ["dim_insurers", "GROUP BY"],
            "sql_must_not_contain": ["PIVOT"],
            "row_count_min": 2,
            "viz_hint": "pie",
            "insight_forbidden": ["millions"],
        }
    },
]
