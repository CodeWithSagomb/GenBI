"""
Seed juin 2026 — append uniquement, sans TRUNCATE.

Génère les ventes du 1er au 30 juin 2026 en respectant les patterns de seed_data.py :
  - Clients chroniques : visite le 4 juin (Glucophage + Coversyl, Tiers-Payant)
  - Ventes quotidiennes : 15-30 (dimanche) / 30-55 (autres jours)
  - Même distribution clients / produits / paiements que seed_data.py

Usage :
    python3 seed_june.py
    cd dbt_project && dbt run
"""
import random
import psycopg2
from datetime import datetime, timedelta

CONN = dict(host="localhost", port=5432, dbname="genbi", user="postgres", password="postgres_admin_123")

def get_conn():
    return psycopg2.connect(**CONN)


def seed_june():
    random.seed(142)  # seed distinct de 42 — données juin reproductibles et indépendantes

    with get_conn() as conn:
        with conn.cursor() as cur:
            # ── IDs de continuation ────────────────────────────────────────────
            cur.execute("SELECT COALESCE(MAX(sale_id), 0) FROM raw.sales")
            sale_idx = cur.fetchone()[0] + 1
            cur.execute("SELECT COALESCE(MAX(detail_id), 0) FROM raw.sale_details")
            detail_idx = cur.fetchone()[0] + 1

            # ── Référentiels statiques ─────────────────────────────────────────
            cur.execute("SELECT client_id, client_type, is_chronic FROM raw.clients ORDER BY client_id")
            clients = [(r[0], r[1], r[2]) for r in cur.fetchall()]  # (id, type, is_chronic)

            # Produits triés par product_id → même ordre que seed_data.py
            # index 4 = Glucophage (105) · index 6 = Coversyl (107)
            cur.execute("SELECT product_id, public_price_fcfa, vat_rate FROM raw.products ORDER BY product_id")
            products = [(r[0], int(r[1]), float(r[2])) for r in cur.fetchall()]

            cur.execute("SELECT insurer_id, default_coverage_rate FROM raw.insurers ORDER BY insurer_id")
            insurers = [(r[0], float(r[1])) for r in cur.fetchall()]  # (id, rate)

    chronic_clients = [c for c in clients if c[2]]
    chronic_products = [products[4], products[6]]   # Glucophage · Coversyl

    sales = []
    sale_details = []

    # ── 1. Visites chroniques — 4 juin ────────────────────────────────────────
    for c_id, _, _ in chronic_clients:
        ins = random.choice(insurers)
        insurer_id, coverage_rate = ins
        p_date = datetime(2026, 6, 4, random.randint(9, 19), random.randint(0, 59))
        total = sum(p[1] for p in chronic_products)
        vat   = int(sum(p[1] * p[2] for p in chronic_products))
        ins_share = int(total * coverage_rate)
        pat_share = total - ins_share
        sales.append((sale_idx, random.choice([1, 2, 3]), c_id, p_date,
                      'Tiers-Payant', 'Assuré', insurer_id,
                      total, pat_share, ins_share, vat))
        for p in chronic_products:
            sale_details.append((detail_idx, sale_idx, p[0], 1, p[1], p[1]))
            detail_idx += 1
        sale_idx += 1

    # ── 2. Ventes quotidiennes — 1er au 30 juin ───────────────────────────────
    start_june = datetime(2026, 6, 1, 8, 30, 0)
    for day in range(30):
        sale_day = start_june + timedelta(days=day)
        num_sales = random.randint(15, 30) if sale_day.weekday() == 6 else random.randint(30, 55)
        for _ in range(num_sales):
            h = random.choice([8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20])
            s_date = datetime(sale_day.year, sale_day.month, sale_day.day,
                              h, random.randint(0, 59), random.randint(0, 59))
            is_anonymous = random.choice([True, True, False])
            client_id    = None
            client_type  = 'Passant'
            insurer_id   = None
            pay_method   = random.choice(['Espèces', 'Wave', 'Wave', 'Orange Money'])
            coverage_rate = 0.00

            if not is_anonymous:
                c = random.choice(clients)
                client_id, client_type, _ = c
                if client_type == 'Assuré':
                    ins = random.choice(insurers)
                    insurer_id, coverage_rate = ins
                    pay_method = 'Tiers-Payant'

            cart = random.sample(products, random.randint(1, 4))
            total = 0
            vat   = 0
            cart_details = []
            for p in cart:
                qty  = random.choice([1, 1, 1, 2])
                line = p[1] * qty
                total += line
                vat   += int(line * p[2])
                cart_details.append((p[0], qty, p[1], line))

            ins_share = int(total * coverage_rate) if client_type == 'Assuré' else 0
            pat_share = total - ins_share
            sales.append((sale_idx, random.choice([1, 2, 3]), client_id, s_date,
                          pay_method, client_type, insurer_id,
                          total, pat_share, ins_share, vat))
            for det in cart_details:
                sale_details.append((detail_idx, sale_idx, det[0], det[1], det[2], det[3]))
                detail_idx += 1
            sale_idx += 1

    print(f"  Données juin préparées : {len(sales)} ventes · {len(sale_details)} lignes de détail")

    # ── 3. Insertion ──────────────────────────────────────────────────────────
    with get_conn() as conn:
        with conn.cursor() as cur:
            for k in range(0, len(sales), 1000):
                cur.executemany(
                    "INSERT INTO raw.sales VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    sales[k:k+1000]
                )
            for k in range(0, len(sale_details), 1000):
                cur.executemany(
                    "INSERT INTO raw.sale_details VALUES (%s,%s,%s,%s,%s,%s)",
                    sale_details[k:k+1000]
                )
        conn.commit()
    print(f"✅ Juin inséré : {len(sales)} ventes · {len(sale_details)} lignes de détail")
    print("   → Lancer ensuite : cd dbt_project && dbt run")


if __name__ == "__main__":
    print("--- Seed juin 2026 (append) ---")
    seed_june()
