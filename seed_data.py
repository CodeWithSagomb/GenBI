"""Script de seed des données pharmacie — remplace le DAG Airflow pour un lancement direct."""
import random
import psycopg2
from datetime import datetime, date, timedelta

CONN = dict(host="localhost", port=5432, dbname="genbi", user="postgres", password="postgres_admin_123")

def get_conn():
    return psycopg2.connect(**CONN)

def create_pharmacy_schema():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.pharmacies (
                pharmacy_id INT PRIMARY KEY, name VARCHAR(150) NOT NULL,
                country VARCHAR(100) NOT NULL, city VARCHAR(100) NOT NULL, district VARCHAR(100) NOT NULL
            );""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.products (
                product_id INT PRIMARY KEY, cip_code VARCHAR(50) UNIQUE NOT NULL,
                commercial_name VARCHAR(150) NOT NULL, dci VARCHAR(150) NOT NULL,
                therapeutic_class VARCHAR(100) NOT NULL, form VARCHAR(100) NOT NULL,
                dosage VARCHAR(50) NOT NULL, laboratory VARCHAR(100) NOT NULL,
                origin VARCHAR(50) NOT NULL, is_generic BOOLEAN DEFAULT FALSE,
                is_regulated BOOLEAN DEFAULT TRUE, vat_rate NUMERIC(3,2) DEFAULT 0.00,
                public_price_fcfa INT NOT NULL
            );""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.clients (
                client_id INT PRIMARY KEY, first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL, phone_number VARCHAR(50),
                client_type VARCHAR(50) DEFAULT 'Passant', is_chronic BOOLEAN DEFAULT FALSE,
                loyalty_points INT DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.insurers (
                insurer_id INT PRIMARY KEY, name VARCHAR(150) NOT NULL,
                default_coverage_rate NUMERIC(3,2) NOT NULL
            );""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.stocks (
                stock_id INT PRIMARY KEY, product_id INT REFERENCES raw.products(product_id),
                batch_number VARCHAR(50) NOT NULL, expiration_date DATE NOT NULL,
                quantity_in_stock INT NOT NULL CHECK (quantity_in_stock >= 0),
                safety_stock_threshold INT DEFAULT 10, shelf_location VARCHAR(50) NOT NULL,
                last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.purchases (
                purchase_id INT PRIMARY KEY, pharmacy_id INT REFERENCES raw.pharmacies(pharmacy_id),
                wholesaler_name VARCHAR(100) NOT NULL, order_date DATE NOT NULL,
                delivery_date DATE, product_id INT REFERENCES raw.products(product_id),
                quantity_ordered INT NOT NULL, quantity_received INT DEFAULT 0,
                purchase_price_fcfa INT NOT NULL, batch_number VARCHAR(50), expiration_date DATE
            );""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.sales (
                sale_id INT PRIMARY KEY, pharmacy_id INT REFERENCES raw.pharmacies(pharmacy_id),
                client_id INT REFERENCES raw.clients(client_id),
                sale_date TIMESTAMP NOT NULL, payment_method VARCHAR(50) NOT NULL,
                client_type VARCHAR(50) NOT NULL, insurer_id INT REFERENCES raw.insurers(insurer_id),
                total_amount_fcfa INT NOT NULL CHECK (total_amount_fcfa >= 0),
                patient_share_fcfa INT NOT NULL CHECK (patient_share_fcfa >= 0),
                insurer_share_fcfa INT NOT NULL CHECK (insurer_share_fcfa >= 0),
                vat_amount_fcfa INT DEFAULT 0 CHECK (vat_amount_fcfa >= 0)
            );""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.sale_details (
                detail_id INT PRIMARY KEY, sale_id INT REFERENCES raw.sales(sale_id),
                product_id INT REFERENCES raw.products(product_id),
                quantity INT NOT NULL CHECK (quantity > 0),
                unit_price_fcfa INT NOT NULL CHECK (unit_price_fcfa >= 0),
                total_line_amount_fcfa INT NOT NULL CHECK (total_line_amount_fcfa >= 0)
            );""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.missed_sales (
                missed_sale_id INT PRIMARY KEY, pharmacy_id INT REFERENCES raw.pharmacies(pharmacy_id),
                product_id INT REFERENCES raw.products(product_id),
                missed_date TIMESTAMP NOT NULL, requested_quantity INT NOT NULL CHECK (requested_quantity > 0),
                client_type VARCHAR(50) NOT NULL
            );""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.wholesaler_returns (
                return_id INT PRIMARY KEY, pharmacy_id INT REFERENCES raw.pharmacies(pharmacy_id),
                wholesaler_name VARCHAR(100) NOT NULL, return_date DATE NOT NULL,
                product_id INT REFERENCES raw.products(product_id), batch_number VARCHAR(50) NOT NULL,
                quantity_returned INT NOT NULL CHECK (quantity_returned > 0),
                credit_note_amount_fcfa INT, status VARCHAR(50) DEFAULT 'En attente'
            );""")
        conn.commit()
    print("✅ Tables raw créées.")

def populate_pharmacy_data():
    random.seed(42)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""TRUNCATE raw.sale_details, raw.sales, raw.purchases, raw.stocks,
                raw.missed_sales, raw.wholesaler_returns,
                raw.clients, raw.products, raw.insurers, raw.pharmacies CASCADE;""")
        conn.commit()

    pharmacies = [
        (1,'Pharmacie Bourguiba','Sénégal','Dakar','Amitié/Fann'),
        (2,'Pharmacie des Almadies','Sénégal','Dakar','Almadies'),
        (3,'Pharmacie de la Nation','Sénégal','Dakar','Plateau'),
    ]
    insurers = [
        (1,'IPM Senelec',0.80),(2,'IPM Port Autonome de Dakar',0.70),
        (3,'IPM Sonatel',0.80),(4,'Saham Assurances (Sanlam)',0.80),(5,'NSIA Assurances',0.70),
    ]
    products = [
        (101,'3400936272545','Doliprane','Paracétamol','Antalgique','Comprimé','1g','Sanofi','Importé',False,True,0.00,1150),
        (102,'3400936272514','Doliprane Pédiatrique','Paracétamol','Antalgique','Sirop','2.4%','Sanofi','Importé',False,True,0.00,1450),
        (103,'3400935627195','Augmentin Adultes','Amoxicilline / Acide Clavulanique','Antibiotique','Poudre suspension','1g/125mg','GlaxoSmithKline','Importé',False,True,0.00,4800),
        (104,'3400930008544','Amoxicilline Biogaran','Amoxicilline','Antibiotique','Gélule','500mg','Biogaran','Importé',True,True,0.00,1850),
        (105,'3400932943256','Glucophage','Metformine','Antidiabétique','Comprimé','850mg','Merck','Importé',False,True,0.00,2450),
        (106,'3400933221940','Metformine IPD','Metformine','Antidiabétique','Comprimé','1000mg','Institut Pasteur Dakar','Local',True,True,0.00,1500),
        (107,'3400934983056','Coversyl','Périndopril','Antihypertenseur','Comprimé','5mg','Servier','Importé',False,True,0.00,8900),
        (108,'3400938562719','Lovenox','Énoxaparine','Anticoagulant','Seringue préremplie','4000 UI','Sanofi','Importé',False,True,0.00,19500),
        (109,'3400931293051','Spasfon','Phloroglucinol','Antispasmodique','Comprimé lyoc','80mg','Teva','Importé',False,True,0.00,2200),
        (110,'3400934391059','Gaviscon','Alginate de sodium / Bicarbonate','Anti-acide','Suspension buvable','Sachet','Reckitt Benckiser','Importé',False,True,0.00,2900),
        (111,'3282779007421','Mustela Crème Change','Hygiène bébé','Parapharmacie','Crème','100ml','Laboratoires Expanscience','Importé',False,False,0.18,6200),
        (112,'3518665983021','Dexeryl Crème','Dermatologie','Parapharmacie','Crème','250g','Pierre Fabre','Importé',False,False,0.18,4800),
        (113,'6131294830129','Eau de Ciel Bébé','Cosmétique','Parapharmacie','Eau de Cologne','200ml','Pharmivoire','Local',False,False,0.18,3500),
        (114,'6131294830555','Savon Antiseptique Valda','Hygiène','Parapharmacie','Savon','100g','Pharmivoire','Local',False,False,0.18,1200),
        (115,'3400936272999','Paracétamol Valdafrique','Paracétamol','Antalgique','Comprimé','500mg','Valdafrique Ségnal','Local',True,True,0.00,750),
        (116,'8699540010016','Coartem','Artémether / Luméfantrine','Antipaludéen','Comprimé','80mg/480mg','Novartis','Importé',False,True,0.00,3500),
        (117,'6131294831001','ASAQ Winthrop','Artésunate / Amodiaquine','Antipaludéen','Comprimé','100mg/270mg','Sanofi','Importé',True,True,0.00,2200),
        (118,'3400936100011','Ibuprofène Biogaran','Ibuprofène','Anti-inflammatoire','Comprimé','400mg','Biogaran','Importé',True,True,0.00,900),
        (119,'3400936100028','Diclofénac Mylan','Diclofénac sodique','Anti-inflammatoire','Comprimé gastrorésistant','50mg','Mylan','Importé',True,True,0.00,1100),
        (120,'3400936100035','Oméprazole Biogaran','Oméprazole','Antiulcéreux','Gélule','20mg','Biogaran','Importé',True,True,0.00,1200),
        (121,'3400936100042','Azithromycine Biogaran','Azithromycine','Antibiotique','Comprimé','500mg','Biogaran','Importé',True,True,0.00,2800),
        (122,'3400936100059','Métronidazole Biogaran','Métronidazole','Antibiotique','Comprimé','500mg','Biogaran','Importé',True,True,0.00,1000),
        (123,'3400936100066','Loratadine Biogaran','Loratadine','Antihistaminique','Comprimé','10mg','Biogaran','Importé',True,True,0.00,800),
        (124,'6131294831018','Amlodipine IPD','Amlodipine','Antihypertenseur','Comprimé','5mg','Institut Pasteur Dakar','Local',True,True,0.00,1100),
        (125,'3400936100073','Fluconazole Mylan','Fluconazole','Antifongique','Gélule','150mg','Mylan','Importé',True,True,0.00,1500),
        (126,'3400936100080','Albendazole GSK','Albendazole','Antiparasitaire','Comprimé','400mg','GlaxoSmithKline','Importé',False,True,0.00,950),
        (127,'3400936100097','Tardyferon B9','Fer / Acide Folique','Supplément','Comprimé pelliculé','80mg/0.35mg','Pierre Fabre','Importé',False,True,0.00,2200),
        (128,'3400936100103','Vitamine C UPSA','Acide Ascorbique','Supplément','Comprimé effervescent','500mg','UPSA','Importé',False,False,0.18,750),
        (129,'3400936100110','Microval','Lévonorgestrel','Contraceptif','Comprimé','30mcg','Pfizer','Importé',False,True,0.00,1500),
        (130,'3701129501017','Photoderm SPF50+','Filtre solaire','Parapharmacie','Crème','40ml','Bioderma','Importé',False,False,0.18,8500),
    ]

    first_names = ['Mamadou','Aminata','Fatou','Cheikh','Mariama','Abdoulaye','Ousmane','Khady','Babacar','Astou',
                   'Moussa','Awa','Ibrahima','Rokhy','Demba','Penda','Samba','Seynabou','Modou','Anta',
                   'Alassane','Ndèye','Amadou','Khadidiatou','Alioune','Coumba','Papa','Binetou','Moustapha','Ramatoulaye']
    last_names = ['Diop','Ndiaye','Sow','Diallo','Ba','Kane','Sy','Gueye','Cisse','Fall','Diagne','Sarr',
                  'Faye','Badji','Mbodj','Seck','Thiam','Ly','Sané','Deme','Kouyaté','Camara','Touré','Dramé']

    clients = []
    for i in range(1, 101):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        phone = f"+221 77 {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}"
        c_type = random.choice(['Passant','Assuré','Assuré'])
        is_chronic = random.choice([True,False,False]) if c_type == 'Assuré' else False
        points = random.randint(0,450) if is_chronic or c_type == 'Assuré' else 0
        signup = datetime(2026, random.choices([1,2,3,4,5], weights=[10,25,30,25,10])[0], random.randint(1,28))
        clients.append((i, fn, ln, phone, c_type, is_chronic, points, signup))

    stocks = []
    stock_idx = 1
    for prod in products:
        pid = prod[0]
        stocks.append((stock_idx, pid, f"LOT-{pid}-A", date(2027,6,30), random.randint(50,200), 15,
                       'Tiroir '+random.choice(['A1','A2','B1','B2']) if prod[4]!='Parapharmacie' else 'Rayon Parapharmacie',
                       datetime.now()))
        stock_idx += 1
        stocks.append((stock_idx, pid, f"LOT-{pid}-B", date(2026,6,20), random.randint(5,30), 10,
                       'Tiroir '+random.choice(['A3','B3']) if prod[4]!='Parapharmacie' else 'Tête de gondole',
                       datetime.now()))
        stock_idx += 1
        if pid == 108:
            stocks.append((stock_idx, pid, f"LOT-{pid}-C", date(2026,12,31), random.randint(20,60), 5,
                           'Frigo Thermostaté 1', datetime.now()))
            stock_idx += 1

    wholesalers = ['UBIPHARM Sénégal','LABOREX Sénégal','COPHARMA','TEDIS PHARMA']
    purchases = []
    for i in range(1, 101):
        pharm_id = random.choice([1,2,3])
        w = random.choice(wholesalers)
        order_dt = date(2026, random.randint(2,5), random.randint(1,28))
        prod = random.choice(products)
        qty_ord = random.randint(20,150)
        rate = random.choice([1.0,1.0,1.0,0.9,0.8,0.0])
        qty_rec = int(qty_ord * rate)
        pag = int(prod[12] * 0.71)
        batch = f"LOT-{prod[0]}-A" if qty_rec > 0 else None
        exp_dt = date(2027,6,30) if qty_rec > 0 else None
        deliv_dt = order_dt + timedelta(days=1) if qty_rec > 0 else None
        purchases.append((i, pharm_id, w, order_dt, deliv_dt, prod[0], qty_ord, qty_rec, pag, batch, exp_dt))

    sales = []
    sale_details = []
    sale_idx = 1
    detail_idx = 1
    start_date = datetime(2026,2,1,8,30,0)
    current_time = datetime(2026,5,28,12,0,0)
    insured_clients = [c for c in clients if c[4]=='Assuré']
    chronic_clients = [c for c in clients if c[5] is True]

    for c in chronic_clients:
        c_id = c[0]
        c_insurer_id = random.choice([1,2,3,4,5])
        coverage_rate = [ins[2] for ins in insurers if ins[0]==c_insurer_id][0]
        purchase_dates = [
            datetime(2026,2,5,random.randint(9,19),random.randint(0,59)),
            datetime(2026,3,5,random.randint(9,19),random.randint(0,59)),
            datetime(2026,4,4,random.randint(9,19),random.randint(0,59)),
            datetime(2026,5,4,random.randint(9,19),random.randint(0,59)),
        ]
        chronic_products = [products[4], products[6]]
        for p_date in purchase_dates:
            total = sum(p[12] for p in chronic_products)
            vat = int(sum(p[12]*float(p[11]) for p in chronic_products))
            ins_share = int(total * float(coverage_rate))
            pat_share = total - ins_share
            sales.append((sale_idx, random.choice([1,2,3]), c_id, p_date, 'Tiers-Payant','Assuré',c_insurer_id,total,pat_share,ins_share,vat))
            for p in chronic_products:
                sale_details.append((detail_idx, sale_idx, p[0], 1, p[12], p[12]))
                detail_idx += 1
            sale_idx += 1

    delta_days = (current_time - start_date).days
    for day in range(delta_days + 1):
        sale_day = start_date + timedelta(days=day)
        num_sales = random.randint(15,30) if sale_day.weekday()==6 else random.randint(30,55)
        for s in range(num_sales):
            h = random.choice([8,9,10,11,12,13,16,17,18,19,20])
            m = random.randint(0,59)
            s_date = datetime(sale_day.year, sale_day.month, sale_day.day, h, m, random.randint(0,59))
            is_anonymous = random.choice([True,True,False])
            client_id = None
            client_type = 'Passant'
            insurer_id = None
            pay_method = random.choice(['Espèces','Wave','Wave','Orange Money'])
            coverage_rate = 0.00
            if not is_anonymous:
                c = random.choice(clients)
                client_id = c[0]
                client_type = c[4]
                if client_type == 'Assuré':
                    insurer_id = random.choice([1,2,3,4,5])
                    coverage_rate = [ins[2] for ins in insurers if ins[0]==insurer_id][0]
                    pay_method = 'Tiers-Payant'
            cart = random.sample(products, random.randint(1,4))
            total = 0
            vat = 0
            cart_details = []
            for p in cart:
                qty = random.choice([1,1,1,2])
                line = p[12]*qty
                total += line
                vat += int(line*float(p[11]))
                cart_details.append((p[0], qty, p[12], line))
            ins_share = int(total*float(coverage_rate)) if client_type=='Assuré' else 0
            pat_share = total - ins_share
            sales.append((sale_idx, random.choice([1,2,3]), client_id, s_date, pay_method, client_type, insurer_id, total, pat_share, ins_share, vat))
            for det in cart_details:
                sale_details.append((detail_idx, sale_idx, det[0], det[1], det[2], det[3]))
                detail_idx += 1
            sale_idx += 1

    missed_sales = []
    for i in range(1, 201):
        prod = random.choice(products)
        m_date = start_date + timedelta(days=random.randint(1,delta_days-1), hours=random.randint(8,20), minutes=random.randint(0,59))
        missed_sales.append((i, random.choice([1,2,3]), prod[0], m_date, random.randint(1,3), random.choice(['Passant','Assuré'])))

    returns = []
    for idx, prod in enumerate(products, 1):
        ret_date = date(2026, random.randint(3,5), random.randint(1,20))
        qty = random.randint(5,15)
        pag = int(prod[12]*0.71)
        returns.append((idx, random.choice([1,2,3]), random.choice(['UBIPHARM Sénégal','LABOREX Sénégal']),
                        ret_date, prod[0], f"LOT-{prod[0]}-B", qty, qty*pag, random.choice(['Validé','En attente'])))

    print(f"  Données préparées : {len(sales)} ventes · {len(sale_details)} lignes · {len(stocks)} stocks")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO raw.pharmacies VALUES (%s,%s,%s,%s,%s)", pharmacies)
            cur.executemany("INSERT INTO raw.insurers VALUES (%s,%s,%s)", insurers)
            cur.executemany("INSERT INTO raw.products VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", products)
            cur.executemany("INSERT INTO raw.clients VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", clients)
            cur.executemany("INSERT INTO raw.stocks VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", stocks)
            cur.executemany("INSERT INTO raw.purchases VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", purchases)
            for k in range(0, len(sales), 1000):
                cur.executemany("INSERT INTO raw.sales VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", sales[k:k+1000])
            for k in range(0, len(sale_details), 1000):
                cur.executemany("INSERT INTO raw.sale_details VALUES (%s,%s,%s,%s,%s,%s)", sale_details[k:k+1000])
            cur.executemany("INSERT INTO raw.missed_sales VALUES (%s,%s,%s,%s,%s,%s)", missed_sales)
            cur.executemany("INSERT INTO raw.wholesaler_returns VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", returns)
        conn.commit()
    print(f"✅ Données insérées : {len(sales)} ventes · {len(sale_details)} lignes de détail.")

if __name__ == "__main__":
    print("--- Étape 1 : Création des tables raw ---")
    create_pharmacy_schema()
    print("--- Étape 2 : Insertion des données ---")
    populate_pharmacy_data()
    print("--- Seed terminé ---")
