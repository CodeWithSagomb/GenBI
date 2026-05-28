from datetime import datetime
from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator

def create_raw_tables():
    # Connexion à PostgreSQL via la connexion pré-configurée
    pg_hook = PostgresHook(postgres_conn_id="genbi_postgres_conn")
    
    # Création de la table des clients dans le schéma RAW
    pg_hook.run("""
    CREATE TABLE IF NOT EXISTS raw.customers (
        customer_id INT PRIMARY KEY,
        customer_name VARCHAR(100),
        email VARCHAR(100),
        country VARCHAR(50),
        created_at TIMESTAMP
    );
    """)
    
    # Création de la table des produits dans le schéma RAW
    pg_hook.run("""
    CREATE TABLE IF NOT EXISTS raw.products (
        product_id INT PRIMARY KEY,
        product_name VARCHAR(100),
        category VARCHAR(50),
        price NUMERIC(10, 2)
    );
    """)
    
    # Création de la table des commandes dans le schéma RAW
    pg_hook.run("""
    CREATE TABLE IF NOT EXISTS raw.orders (
        order_id INT PRIMARY KEY,
        customer_id INT,
        product_id INT,
        quantity INT,
        amount NUMERIC(10, 2),
        order_date TIMESTAMP
    );
    """)
    print("Tables dans le schéma RAW créées avec succès.")

def insert_mock_data():
    pg_hook = PostgresHook(postgres_conn_id="genbi_postgres_conn")
    
    # Validation pour éviter les doublons si le DAG est exécuté plusieurs fois
    count_cust = pg_hook.get_first("SELECT COUNT(*) FROM raw.customers;")[0]
    if count_cust > 0:
        print("Les données de test existent déjà dans raw.customers. Ingestion ignorée.")
        return
        
    # Liste de clients réalistes (France, Belgique, Allemagne, UK)
    customers = [
        (1, 'Jean Dupont', 'jean.dupont@email.com', 'France', '2026-01-15 10:00:00'),
        (2, 'Marie Laurent', 'marie.laurent@email.com', 'France', '2026-02-20 11:30:00'),
        (3, 'Hans Müller', 'hans.mueller@email.com', 'Allemagne', '2026-03-01 09:15:00'),
        (4, 'John Smith', 'john.smith@email.com', 'Royaume-Uni', '2026-03-10 14:00:00'),
        (5, 'Chloe Dubois', 'chloe.dubois@email.com', 'Belgique', '2026-03-18 16:45:00')
    ]
    
    # Liste de produits high-tech et mode
    products = [
        (101, 'Ordinateur Portable Pro', 'Électronique', 1200.00),
        (102, 'Casque Audio Bluetooth', 'Électronique', 150.00),
        (103, 'Chaussures de Sport Runner', 'Mode', 90.00),
        (104, 'Montre Connectée Sport', 'Électronique', 250.00),
        (105, 'Sac à Dos Imperméable', 'Mode', 60.00)
    ]
    
    # Commandes reliant clients et produits
    orders = [
        (1001, 1, 101, 1, 1200.00, '2026-05-01 14:30:00'),
        (1002, 1, 103, 2, 180.00, '2026-05-02 09:15:00'),
        (1003, 2, 102, 1, 150.00, '2026-05-03 18:20:00'),
        (1004, 3, 104, 1, 250.00, '2026-05-04 10:00:00'),
        (1005, 4, 101, 1, 1200.00, '2026-05-05 11:45:00'),
        (1006, 5, 105, 3, 180.00, '2026-05-06 15:30:00'),
        (1007, 2, 103, 1, 90.00, '2026-05-07 16:15:00'),
        (1008, 4, 102, 2, 300.00, '2026-05-08 13:00:00'),
        (1009, 3, 105, 1, 60.00, '2026-05-09 17:00:00'),
        (1010, 1, 104, 1, 250.00, '2026-05-10 11:00:00')
    ]
    
    # Ingestion des Clients
    for cust in customers:
        pg_hook.run("INSERT INTO raw.customers VALUES (%s, %s, %s, %s, %s)", parameters=cust)
        
    # Ingestion des Produits
    for prod in products:
        pg_hook.run("INSERT INTO raw.products VALUES (%s, %s, %s, %s)", parameters=prod)
        
    # Ingestion des Commandes
    for ord in orders:
        pg_hook.run("INSERT INTO raw.orders VALUES (%s, %s, %s, %s, %s, %s)", parameters=ord)
        
    print("Données fictives insérées avec succès dans raw.")

# Définition du DAG
with DAG(
    dag_id='ingest_ecommerce_data',
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,  # Déclenchement manuel uniquement
    catchup=False,
    tags=['genbi', 'raw', 'ecommerce'],
) as dag:

    create_tables = PythonOperator(
        task_id='create_raw_tables',
        python_callable=create_raw_tables
    )

    populate_data = PythonOperator(
        task_id='insert_mock_data',
        python_callable=insert_mock_data
    )

    # Définition des dépendances des tâches
    create_tables >> populate_data
