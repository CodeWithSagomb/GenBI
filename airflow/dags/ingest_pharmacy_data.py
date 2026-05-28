import os
import random
import logging
from datetime import datetime, date, timedelta
from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator

# Configuration du logger
logger = logging.getLogger("airflow.task")

def create_pharmacy_schema():
    """
    Crée les 10 tables physiques cibles dans le schéma raw avec les contraintes appropriées.
    Cette opération est idempotente grâce aux clauses IF NOT EXISTS.
    """
    pg_hook = PostgresHook(postgres_conn_id="genbi_postgres_conn")
    
    with pg_hook.get_conn() as conn:
        with conn.cursor() as cursor:
            # 1. Table Pharmacies
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.pharmacies (
                pharmacy_id INT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                country VARCHAR(100) NOT NULL,
                city VARCHAR(100) NOT NULL,
                district VARCHAR(100) NOT NULL
            );
            """)

            # 2. Table Products (Médicaments & Parapharmacie)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.products (
                product_id INT PRIMARY KEY,
                cip_code VARCHAR(50) UNIQUE NOT NULL,
                commercial_name VARCHAR(150) NOT NULL,
                dci VARCHAR(150) NOT NULL,
                therapeutic_class VARCHAR(100) NOT NULL,
                form VARCHAR(100) NOT NULL,
                dosage VARCHAR(50) NOT NULL,
                laboratory VARCHAR(100) NOT NULL,
                origin VARCHAR(50) NOT NULL,
                is_generic BOOLEAN DEFAULT FALSE,
                is_regulated BOOLEAN DEFAULT TRUE,
                vat_rate NUMERIC(3, 2) DEFAULT 0.00,
                public_price_fcfa INT NOT NULL
            );
            """)

            # 3. Table Clients (Patients)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.clients (
                client_id INT PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                phone_number VARCHAR(50),
                client_type VARCHAR(50) DEFAULT 'Passant',
                is_chronic BOOLEAN DEFAULT FALSE,
                loyalty_points INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 4. Table Insurers (Assurances & IPMs)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.insurers (
                insurer_id INT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                default_coverage_rate NUMERIC(3, 2) NOT NULL
            );
            """)

            # 5. Table Stocks (Suivi Lot par Lot)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.stocks (
                stock_id INT PRIMARY KEY,
                product_id INT REFERENCES raw.products(product_id),
                batch_number VARCHAR(50) NOT NULL,
                expiration_date DATE NOT NULL,
                quantity_in_stock INT NOT NULL CHECK (quantity_in_stock >= 0),
                safety_stock_threshold INT DEFAULT 10,
                shelf_location VARCHAR(50) NOT NULL,
                last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 6. Table Purchases (Approvisionnements grossistes)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.purchases (
                purchase_id INT PRIMARY KEY,
                pharmacy_id INT REFERENCES raw.pharmacies(pharmacy_id),
                wholesaler_name VARCHAR(100) NOT NULL,
                order_date DATE NOT NULL,
                delivery_date DATE,
                product_id INT REFERENCES raw.products(product_id),
                quantity_ordered INT NOT NULL,
                quantity_received INT DEFAULT 0,
                purchase_price_fcfa INT NOT NULL,
                batch_number VARCHAR(50),
                expiration_date DATE
            );
            """)

            # 7. Table Sales (Ventes - En-tête)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.sales (
                sale_id INT PRIMARY KEY,
                pharmacy_id INT REFERENCES raw.pharmacies(pharmacy_id),
                client_id INT REFERENCES raw.clients(client_id),
                sale_date TIMESTAMP NOT NULL,
                payment_method VARCHAR(50) NOT NULL,
                client_type VARCHAR(50) NOT NULL,
                insurer_id INT REFERENCES raw.insurers(insurer_id),
                total_amount_fcfa INT NOT NULL CHECK (total_amount_fcfa >= 0),
                patient_share_fcfa INT NOT NULL CHECK (patient_share_fcfa >= 0),
                insurer_share_fcfa INT NOT NULL CHECK (insurer_share_fcfa >= 0),
                vat_amount_fcfa INT DEFAULT 0 CHECK (vat_amount_fcfa >= 0)
            );
            """)

            # 8. Table Sale Details (Lignes de Vente)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.sale_details (
                detail_id INT PRIMARY KEY,
                sale_id INT REFERENCES raw.sales(sale_id),
                product_id INT REFERENCES raw.products(product_id),
                quantity INT NOT NULL CHECK (quantity > 0),
                unit_price_fcfa INT NOT NULL CHECK (unit_price_fcfa >= 0),
                total_line_amount_fcfa INT NOT NULL CHECK (total_line_amount_fcfa >= 0)
            );
            """)

            # 9. Table Missed Sales (Ventes manquées / Ruptures)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.missed_sales (
                missed_sale_id INT PRIMARY KEY,
                pharmacy_id INT REFERENCES raw.pharmacies(pharmacy_id),
                product_id INT REFERENCES raw.products(product_id),
                missed_date TIMESTAMP NOT NULL,
                requested_quantity INT NOT NULL CHECK (requested_quantity > 0),
                client_type VARCHAR(50) NOT NULL
            );
            """)

            # 10. Table Wholesaler Returns (Retours pour Avoir DDP)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.wholesaler_returns (
                return_id INT PRIMARY KEY,
                pharmacy_id INT REFERENCES raw.pharmacies(pharmacy_id),
                wholesaler_name VARCHAR(100) NOT NULL,
                return_date DATE NOT NULL,
                product_id INT REFERENCES raw.products(product_id),
                batch_number VARCHAR(50) NOT NULL,
                quantity_returned INT NOT NULL CHECK (quantity_returned > 0),
                credit_note_amount_fcfa INT,
                status VARCHAR(50) DEFAULT 'En attente'
            );
            """)
            
    logger.info("Schéma physique complet des 10 tables créé dans 'raw'.")

def populate_pharmacy_data():
    """
    Génère et insère des données d'officine dakaroise à haute fidélité (10 000+ lignes au total).
    Utilise le chargement en lot (bulk insert) pour garantir une vitesse d'exécution maximale.
    """
    pg_hook = PostgresHook(postgres_conn_id="genbi_postgres_conn")
    
    # 0. Nettoyage préalable pour garantir la reproductibilité (Idempotence)
    logger.info("Nettoyage des anciennes données pour réinitialisation...")
    pg_hook.run("""
        TRUNCATE raw.sale_details, raw.sales, raw.purchases, raw.stocks, 
                 raw.missed_sales, raw.wholesaler_returns, 
                 raw.clients, raw.products, raw.insurers, raw.pharmacies 
        CASCADE;
    """)

    # 1. Données statiques : Pharmacies
    pharmacies = [
        (1, 'Pharmacie Bourguiba', 'Sénégal', 'Dakar', 'Amitié/Fann'),
        (2, 'Pharmacie des Almadies', 'Sénégal', 'Dakar', 'Almadies'),
        (3, 'Pharmacie de la Nation', 'Sénégal', 'Dakar', 'Plateau')
    ]
    
    # 2. Données statiques : Assureurs & IPMs
    insurers = [
        (1, 'IPM Senelec', 0.80),
        (2, 'IPM Port Autonome de Dakar', 0.70),
        (3, 'IPM Sonatel', 0.80),
        (4, 'Saham Assurances (Sanlam)', 0.80),
        (5, 'NSIA Assurances', 0.70)
    ]

    # 3. Données statiques : Produits réels d'officine
    # (CIP, Nom Commercial, DCI, Classe Thérapeutique, Forme, Dosage, Laboratoire, Origine, is_generic, is_regulated, vat_rate, public_price)
    products = [
        (101, '3400936272545', 'Doliprane', 'Paracétamol', 'Antalgique', 'Comprimé', '1g', 'Sanofi', 'Importé', False, True, 0.00, 1150),
        (102, '3400936272514', 'Doliprane Pédiatrique', 'Paracétamol', 'Antalgique', 'Sirop', '2.4%', 'Sanofi', 'Importé', False, True, 0.00, 1450),
        (103, '3400935627195', 'Augmentin Adultes', 'Amoxicilline / Acide Clavulanique', 'Antibiotique', 'Poudre suspension', '1g/125mg', 'GlaxoSmithKline', 'Importé', False, True, 0.00, 4800),
        (104, '3400930008544', 'Amoxicilline Biogaran', 'Amoxicilline', 'Antibiotique', 'Gélule', '500mg', 'Biogaran', 'Importé', True, True, 0.00, 1850),
        (105, '3400932943256', 'Glucophage', 'Metformine', 'Antidiabétique', 'Comprimé', '850mg', 'Merck', 'Importé', False, True, 0.00, 2450),
        (106, '3400933221940', 'Metformine IPD', 'Metformine', 'Antidiabétique', 'Comprimé', '1000mg', 'Institut Pasteur Dakar', 'Local', True, True, 0.00, 1500),
        (107, '3400934983056', 'Coversyl', 'Périndopril', 'Antihypertenseur', 'Comprimé', '5mg', 'Servier', 'Importé', False, True, 0.00, 8900),
        (108, '3400938562719', 'Lovenox', 'Énoxaparine', 'Anticoagulant', 'Seringue préremplie', '4000 UI', 'Sanofi', 'Importé', False, True, 0.00, 19500),
        (109, '3400931293051', 'Spasfon', 'Phloroglucinol', 'Antispasmodique', 'Comprimé lyoc', '80mg', 'Teva', 'Importé', False, True, 0.00, 2200),
        (110, '3400934391059', 'Gaviscon', 'Alginate de sodium / Bicarbonate', 'Anti-acide', 'Suspension buvable', 'Sachet', 'Reckitt Benckiser', 'Importé', False, True, 0.00, 2900),
        (111, '3282779007421', 'Mustela Crème Change', 'Hygiène bébé', 'Parapharmacie', 'Crème', '100ml', 'Laboratoires Expanscience', 'Importé', False, False, 0.18, 6200),
        (112, '3518665983021', 'Dexeryl Crème', 'Dermatologie', 'Parapharmacie', 'Crème', '250g', 'Pierre Fabre', 'Importé', False, False, 0.18, 4800),
        (113, '6131294830129', 'Eau de Ciel Bébé', 'Cosmétique', 'Parapharmacie', 'Eau de Cologne', '200ml', 'Pharmivoire', 'Local', False, False, 0.18, 3500),
        (114, '6131294830555', 'Savon Antiseptique Valda', 'Hygiène', 'Parapharmacie', 'Savon', '100g', 'Pharmivoire', 'Local', False, False, 0.18, 1200),
        (115, '3400936272999', 'Paracétamol Valdafrique', 'Paracétamol', 'Antalgique', 'Comprimé', '500mg', 'Valdafrique Ségnal', 'Local', True, True, 0.00, 750)
    ]

    # 4. Données dynamiques : Clients sénégalais (100 clients)
    first_names = ['Mamadou', 'Aminata', 'Fatou', 'Cheikh', 'Mariama', 'Abdoulaye', 'Ousmane', 'Khady', 'Babacar', 'Astou', 
                   'Moussa', 'Awa', 'Ibrahima', 'Rokhy', 'Demba', 'Penda', 'Samba', 'Seynabou', 'Modou', 'Anta',
                   'Alassane', 'Ndèye', 'Amadou', 'Khadidiatou', 'Alioune', 'Coumba', 'Papa', 'Binetou', 'Moustapha', 'Ramatoulaye']
    last_names = ['Diop', 'Ndiaye', 'Sow', 'Diallo', 'Ba', 'Kane', 'Sy', 'Gueye', 'Cisse', 'Fall', 'Diagne', 'Sarr', 
                  'Faye', 'Badji', 'Mbodj', 'Seck', 'Thiam', 'Ly', 'Sané', 'Deme', 'Kouyaté', 'Camara', 'Touré', 'Dramé']
    
    clients = []
    # Assurer que certains clients chroniques réguliers soient présents
    for i in range(1, 101):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        phone = f"+221 77 {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}"
        c_type = random.choice(['Passant', 'Assuré', 'Assuré'])
        is_chronic = random.choice([True, False, False]) if c_type == 'Assuré' else False
        points = random.randint(0, 450) if is_chronic or c_type == 'Assuré' else 0
        signup_date = datetime(2025, random.randint(1, 12), random.randint(1, 28))
        clients.append((i, fn, ln, phone, c_type, is_chronic, points, signup_date))

    # 5. Stocks par lots et emplacements physiques
    stocks = []
    stock_idx = 1
    # Pour chaque produit, on crée 2 ou 3 lots distincts avec des dates de péremption variables
    for prod in products:
        prod_id = prod[0]
        # Lot 1 : Standard, expire loin
        stocks.append((
            stock_idx, prod_id, f"LOT-{prod_id}-A", 
            date(2027, 6, 30), random.randint(50, 200), 15, 
            'Tiroir ' + random.choice(['A1', 'A2', 'B1', 'B2']) if prod[4] != 'Parapharmacie' else 'Rayon Parapharmacie',
            datetime.now()
        ))
        stock_idx += 1
        
        # Lot 2 : Expire bientôt (pour tester les alertes de péremption)
        # Certains vont expirer le mois prochain (juin 2026)
        stocks.append((
            stock_idx, prod_id, f"LOT-{prod_id}-B", 
            date(2026, 6, 20), random.randint(5, 30), 10, 
            'Tiroir ' + random.choice(['A3', 'B3']) if prod[4] != 'Parapharmacie' else 'Tête de gondole',
            datetime.now()
        ))
        stock_idx += 1

        # Lot 3 : Réfrigéré spécifique pour Lovenox / Insuline
        if prod_id == 108: # Lovenox
            stocks.append((
                stock_idx, prod_id, f"LOT-{prod_id}-C", 
                date(2026, 12, 31), random.randint(20, 60), 5, 
                'Frigo Thermostaté 1', datetime.now()
            ))
            stock_idx += 1

    # 6. Approvisionnements purchases (Bons de commande/Livraison)
    # Historique d'achats sur les 90 derniers jours
    purchases = []
    purchase_idx = 1
    wholesalers = ['UBIPHARM Sénégal', 'LABOREX Sénégal', 'COPHARMA', 'TEDIS PHARMA']
    
    # 20 commandes passées ces 90 derniers jours
    for i in range(1, 101):
        pharm_id = random.choice([1, 2, 3])
        wholesaler = random.choice(wholesalers)
        order_dt = date(2026, random.randint(2, 5), random.randint(1, 28))
        prod = random.choice(products)
        qty_ord = random.randint(20, 150)
        # Taux de service réaliste (grossiste livre parfois moins que commandé - Rupture)
        rate = random.choice([1.0, 1.0, 1.0, 0.9, 0.8, 0.0]) # 0.0 correspond à une rupture totale de commande
        qty_rec = int(qty_ord * rate)
        
        # Calcul du PAG (généralement ~70% du prix public PPR)
        pag = int(prod[12] * 0.71)
        batch = f"LOT-{prod[0]}-A" if qty_rec > 0 else None
        exp_dt = date(2027, 6, 30) if qty_rec > 0 else None
        deliv_dt = order_dt + timedelta(days=1) if qty_rec > 0 else None
        
        purchases.append((
            purchase_idx, pharm_id, wholesaler, order_dt, deliv_dt, 
            prod[0], qty_ord, qty_rec, pag, batch, exp_dt
        ))
        purchase_idx += 1

    # 7 & 8. Ventes et détails (Génération massive de 4000+ ventes détaillées)
    # On génère un flux de ventes réaliste s'étalant sur les 90 derniers jours
    sales = []
    sale_details = []
    sale_idx = 1
    detail_idx = 1
    
    # Démarrage au 1er Mars 2026
    start_date = datetime(2026, 3, 1, 8, 30, 0)
    current_time = datetime(2026, 5, 28, 12, 0, 0)
    
    # Liste des assurés pour le Tiers-Payant
    insured_clients = [c for c in clients if c[4] == 'Assuré']
    chronic_clients = [c for c in clients if c[5] is True]
    passant_clients = [c for c in clients if c[4] == 'Passant']

    # Simulation des ventes régulières des patients chroniques (tous les 30 jours pile pour l'observance)
    for c in chronic_clients:
        c_id = c[0]
        # L'assuré a une mutuelle/IPM fixe
        c_insurer_id = random.choice([1, 2, 3, 4, 5])
        coverage_rate = [ins[2] for ins in insurers if ins[0] == c_insurer_id][0]
        
        # 3 passages programmés à 30 jours d'intervalle
        purchase_dates = [
            datetime(2026, 3, 5, random.randint(9, 19), random.randint(0, 59)),
            datetime(2026, 4, 4, random.randint(9, 19), random.randint(0, 59)),
            datetime(2026, 5, 4, random.randint(9, 19), random.randint(0, 59))
        ]
        
        # Le patient diabétique/hypertendu prend toujours les mêmes spécialités
        # ex: Metformine + Coversyl
        chronic_products = [products[4], products[6]] # Glucophage + Coversyl
        
        for p_date in purchase_dates:
            total_sale_amount = sum(p[12] for p in chronic_products)
            vat_amount = int(sum(p[12] * float(p[11]) for p in chronic_products))
            
            ins_share = int(total_sale_amount * float(coverage_rate))
            pat_share = total_sale_amount - ins_share
            
            # Vente d'en-tête
            sales.append((
                sale_idx, random.choice([1, 2, 3]), c_id, p_date, 
                'Tiers-Payant', 'Assuré', c_insurer_id, 
                total_sale_amount, pat_share, ins_share, vat_amount
            ))
            
            # Lignes de vente associées
            for p in chronic_products:
                sale_details.append((
                    detail_idx, sale_idx, p[0], 1, p[12], p[12]
                ))
                detail_idx += 1
                
            sale_idx += 1

    # Simulation des ventes quotidiennes aléatoires au comptoir (20 à 45 ventes par jour sur 88 jours)
    delta_days = (current_time - start_date).days
    
    for day in range(delta_days + 1):
        sale_day = start_date + timedelta(days=day)
        # Éviter les dimanches avec moins d'activité
        num_sales_today = random.randint(15, 30) if sale_day.weekday() == 6 else random.randint(30, 55)
        
        for s in range(num_sales_today):
            # Heures réalistes de pharmacie (garde, midi, rush fin de journée)
            h = random.choice([8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20])
            m = random.randint(0, 59)
            s_date = datetime(sale_day.year, sale_day.month, sale_day.day, h, m, random.randint(0, 59))
            
            # Type de client : 60% passant anonyme (client_id NULL), 40% Assuré ou Passant enregistré
            is_anonymous = random.choice([True, True, False])
            
            client_id = None
            client_type = 'Passant'
            insurer_id = None
            pay_method = random.choice(['Espèces', 'Wave', 'Wave', 'Orange Money'])
            coverage_rate = 0.00
            
            if not is_anonymous:
                c = random.choice(clients)
                client_id = c[0]
                client_type = c[4]
                if client_type == 'Assuré':
                    insurer_id = random.choice([1, 2, 3, 4, 5])
                    coverage_rate = [ins[2] for ins in insurers if ins[0] == insurer_id][0]
                    pay_method = 'Tiers-Payant'

            # Contenu du panier : 1 à 4 produits aléatoires
            cart_products = random.sample(products, random.randint(1, 4))
            total_sale_amount = 0
            vat_amount = 0
            
            cart_details = []
            for p in cart_products:
                qty = random.choice([1, 1, 1, 2])
                price_line = p[12] * qty
                total_sale_amount += price_line
                vat_amount += int(price_line * float(p[11]))
                cart_details.append((p[0], qty, p[12], price_line))
            
            ins_share = int(total_sale_amount * float(coverage_rate)) if client_type == 'Assuré' else 0
            pat_share = total_sale_amount - ins_share
            
            # En-tête de vente
            sales.append((
                sale_idx, random.choice([1, 2, 3]), client_id, s_date, 
                pay_method, client_type, insurer_id, 
                total_sale_amount, pat_share, ins_share, vat_amount
            ))
            
            # Détails associés
            for det in cart_details:
                sale_details.append((
                    detail_idx, sale_idx, det[0], det[1], det[2], det[3]
                ))
                detail_idx += 1
                
            sale_idx += 1

    # 9. Ventes manquées (Ruptures de stock constatées)
    missed_sales = []
    missed_idx = 1
    # 150 ventes manquées sur le trimestre
    for i in range(150):
        prod = random.choice(products)
        m_date = start_date + timedelta(days=random.randint(1, 87), hours=random.randint(8, 20), minutes=random.randint(0, 59))
        missed_sales.append((
            missed_idx, random.choice([1, 2, 3]), prod[0], m_date, random.randint(1, 3), random.choice(['Passant', 'Assuré'])
        ))
        missed_idx += 1

    # 10. Retours Grossistes (produits renvoyés car péremption à 3-6 mois)
    returns = []
    return_idx = 1
    # 10 retours grossistes initiés en Mai 2026 pour nos lots B expirant le 20 Juin 2026
    for prod in products:
        prod_id = prod[0]
        # On renvoie le lot B expirant en Juin
        ret_date = date(2026, 5, random.randint(1, 20))
        qty_ret = random.randint(5, 15)
        pag = int(prod[12] * 0.71) # PAG estimé
        credit_note = qty_ret * pag # Valeur totale de l'avoir attendu
        
        returns.append((
            return_idx, random.choice([1, 2, 3]), random.choice(['UBIPHARM Sénégal', 'LABOREX Sénégal']),
            ret_date, prod_id, f"LOT-{prod_id}-B", qty_ret, credit_note, random.choice(['Validé', 'En attente'])
        ))
        return_idx += 1

    # EXECUTION DES BULK INSERTS DANS POSTGRESQL (Très performant, une seule transaction par table)
    logger.info("Début des insertions en lots (Bulk Inserts)...")
    
    with pg_hook.get_conn() as conn:
        with conn.cursor() as cursor:
            # Pharmacies
            cursor.executemany("INSERT INTO raw.pharmacies VALUES (%s, %s, %s, %s, %s)", pharmacies)
            # Assureurs
            cursor.executemany("INSERT INTO raw.insurers VALUES (%s, %s, %s)", insurers)
            # Produits
            cursor.executemany("INSERT INTO raw.products VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", products)
            # Clients
            cursor.executemany("INSERT INTO raw.clients VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", clients)
            # Stocks
            cursor.executemany("INSERT INTO raw.stocks VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", stocks)
            # Commandes
            cursor.executemany("INSERT INTO raw.purchases VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", purchases)
            # Ventes (en-tête) - Utilise des lots de 1000 pour la stabilité mémoire
            for k in range(0, len(sales), 1000):
                cursor.executemany("INSERT INTO raw.sales VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", sales[k:k+1000])
            # Lignes de ventes - En lots de 1000
            for k in range(0, len(sale_details), 1000):
                cursor.executemany("INSERT INTO raw.sale_details VALUES (%s, %s, %s, %s, %s, %s)", sale_details[k:k+1000])
            # Ventes manquées
            cursor.executemany("INSERT INTO raw.missed_sales VALUES (%s, %s, %s, %s, %s, %s)", missed_sales)
            # Retours grossistes
            cursor.executemany("INSERT INTO raw.wholesaler_returns VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", returns)

    logger.info(f"Données pharmaceutiques insérées avec succès ! {len(sales)} ventes et {len(sale_details)} lignes créées.")

# Définition du DAG Airflow
with DAG(
    dag_id='ingest_pharmacy_data',
    start_date=datetime(2026, 1, 1),
    schedule=None,  # Déclenchement manuel uniquement
    catchup=False,
    tags=['genbi', 'raw', 'pharmacy', 'dakar'],
) as dag:

    create_tables = PythonOperator(
        task_id='create_pharmacy_schema',
        python_callable=create_pharmacy_schema
    )

    populate_data = PythonOperator(
        task_id='populate_pharmacy_data',
        python_callable=populate_pharmacy_data
    )

    # L'initialisation du schéma doit obligatoirement précéder l'ingestion
    create_tables >> populate_data
