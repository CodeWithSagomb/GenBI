# 🌍 Exploration Business & Modèle de Données : Officines Pharmaceutiques en Afrique de l'Ouest

Ce document pose les bases conceptuelles et analytiques pour notre plateforme **GenBI** appliquée au secteur des **officines pharmaceutiques en Afrique de l'Ouest** (Sénégal, Côte d'Ivoire, Bénin, Togo, Mali, etc.).

---

## 1. Contexte Sectoriel & Spécificités d'Afrique de l'Ouest

Le marché pharmaceutique d'Afrique de l'Ouest francophone possède des règles commerciales et financières uniques :

1. **La Monnaie (Franc CFA - XOF) :**
   - Les prix des médicaments sont des **entiers stricts** (pas de centimes dans la pratique courante).
   - Exemple : *Un Doliprane 1g boîte de 8 comprimés coûte 1 150 XOF*.

2. **La Régulation des Prix :**
   - Les prix des médicaments essentiels sont réglementés par l'État (Tarif National).
   - Les pharmacies achètent aux **Grossistes Répartiteurs** (Laborex, Ubipharm, Copharm, Tedis, etc.) à un Prix d'Achat Grossiste (PAG) et revendent au Prix Public Réglementé (PPR/PPV). La marge est fixée par un coefficient légal.

3. **Le Tiers-Payant (Assurances & IPM) :**
   - Une part majeure du chiffre d'affaires d'une grande officine urbaine (Abidjan, Dakar, Cotonou) provient du **Tiers-Payant**.
   - Le patient présente sa carte d'assurance (IPM, NSIA, Saham/Sanlam, AXA, Ascoma, Mutuelle ministérielle) ; l'assurance prend en charge un pourcentage (ex: 70% ou 80%) et le patient paie le reste (**Ticket Modérateur** : 20% ou 30%).
   - L'officine doit gérer le recouvrement des factures auprès des assureurs (souvent source de tensions de trésorerie).

4. **Le Mobile Money (Paiements Numériques) :**
   - En dehors des espèces et des cartes bancaires, les paiements mobiles (**Wave, Orange Money, MTN MoMo, Moov Money**) sont très fréquents pour le règlement du ticket modérateur.

5. **La Supply Chain & Péremptions :**
   - En raison du climat chaud et des délais d'importation, le suivi des dates de péremption (**DDP**) et des ruptures de stock est crucial.

---

## 2. Dictionnaire des Acteurs Clés (Grossistes, Assureurs)

### Grossistes Répartiteurs (Fournisseurs)
- **LABOREX** (Présent au Sénégal, Côte d'Ivoire, Cameroun...)
- **UBIPHARM** (Présent dans plus de 15 pays d'Afrique de l'Ouest et Centrale)
- **COPHARMA** (Sénégal)
- **TEDIS PHARMA** (Afrique de l'Ouest)

### Assureurs & Organismes de Prévoyance
- **SAHAM / SANLAM** (Leader panafricain de l'assurance)
- **NSIA Assurances**
- **AXA / ASCOMA**
- **IPM (Institutions de Prévoyance Maladie)** : Mutuelles d'entreprises très courantes au Sénégal (ex : IPM Senelec, IPM Port Autonome).

---

## 3. Schéma Relationnel Proposé (Modèle Physique RAW)

Pour alimenter notre GenBI, nous allons simuler ou charger 6 tables principales dans le schéma `raw`.

```mermaid
erDiagram
    PHARMACIES ||--o{ SALES : "realise"
    PRODUCTS ||--o{ SALE_DETAILS : "contient"
    SALES ||--o{ SALE_DETAILS : "comporte"
    INSURERS ||--o{ SALES : "couvre"
    PRODUCTS ||--o{ PURCHASES : "achete"
    PHARMACIES ||--o{ PURCHASES : "recoit"

    PHARMACIES {
        int pharmacy_id PK
        string name "Nom de la pharmacie"
        string country "Pays (Sénégal, Côte d'Ivoire, etc.)"
        string city "Ville (Dakar, Abidjan, etc.)"
        string district "Quartier (Cocody, Plateau, Almadies...)"
    }

    PRODUCTS {
        int product_id PK
        string cip_code "Code CIP unique du médicament"
        string commercial_name "Nom commercial (ex: Augmentin)"
        string dci "Dénomination Commune Internationale (ex: Amoxicilline)"
        string therapeutic_class "Classe (Antibiotique, Antalgique...)"
        string form "Forme (Comprimé, Sirop...)"
        string dosage "Dosage (500mg, 1g...)"
        string laboratory "Laboratoire (Sanofi, Biogaran, local)"
        string origin "Origine (Importé / Local)"
        int public_price_fcfa "Prix Public Réglementé"
    }

    INSURERS {
        int insurer_id PK
        string name "Saham, Senelec, NSIA..."
        decimal default_coverage_rate "Taux de prise en charge (0.70 = 70%)"
    }

    SALES {
        int sale_id PK
        int pharmacy_id FK
        timestamp sale_date "Date et heure"
        string payment_method "Espèces, Wave, Orange Money, Tiers-Payant"
        string client_type "Passant, Assuré"
        int insurer_id FK "NULL si client Passant"
        int total_amount_fcfa "Montant total"
        int patient_share_fcfa "Ticket modérateur payé par le client"
        int insurer_share_fcfa "Montant à facturer à l'assurance"
    }

    SALE_DETAILS {
        int detail_id PK
        int sale_id FK
        int product_id FK
        int quantity "Quantité vendue"
        int unit_price_fcfa "Prix unitaire appliqué"
        int total_line_amount_fcfa "Total ligne"
    }

    PURCHASES {
        int purchase_id PK
        int pharmacy_id FK
        string wholesaler_name "Grossiste (Laborex, Ubipharm...)"
        date purchase_date
        int product_id FK
        int quantity_received
        int purchase_price_fcfa "Prix d'Achat Grossiste (PAG)"
        date expiration_date "DDP (Date de Péremption)"
    }
```

---

## 4. Questions Métiers Typiques (Le Terrain d'Expression du GenBI)

Une fois ce modèle opérationnel, l'utilisateur final (le pharmacien titulaire, le gérant, ou l'auditeur) pourra poser des questions complexes en langage naturel :

### Questions Financières & Chiffre d'Affaires
- *"Quel est le chiffre d'affaires total de la pharmacie par mode de paiement ce mois-ci ?"*
- *"Quelle est la part du chiffre d'affaires générée par le Tiers-Payant (les assurances) ?"*
- *"Combien nous doit l'assureur Saham pour les ventes du trimestre dernier ?"*

### Questions de Gestion des Stocks & Péremptions
- *"Quels sont les produits qui vont périmer dans les 3 prochains mois et quel est leur coût d'achat ?"*
- *"Donne-moi le top 10 des médicaments les plus vendus en volume (pour éviter les ruptures)."*
- *"Quels produits n'ont enregistré aucune vente au cours des 60 derniers jours ?"*

### Questions Thérapeutiques & Laboratoires
- *"Quelle est la classe thérapeutique la plus vendue à Abidjan vs Dakar ?"*
- *"Quelle proportion de nos ventes d'antibiotiques provient de fabricants locaux (Afrique de l'Ouest) ?"*
- *"Fais-moi un récapitulatif des ventes de DCI 'Paracétamol' toutes marques confondues."*
