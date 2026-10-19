import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Gestion d'Atelier de Couture", page_icon="🧵", layout="wide")

# CSS pour créer le cadre/contour élégant
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .custom-card {
        background-color: #ffffff;
        border: 2px solid #2563eb;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05);
    }
    .stButton>button {
        border-radius: 8px;
        height: 3.2em;
        font-weight: bold;
        font-size: 16px;
    }
    h1, h2, h3 { color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# Connexion à la base de données SQLite
conn = sqlite3.connect('atelier_production.db', check_same_thread=False)
c = conn.cursor()

# Tables de la base de données
c.execute('''
    CREATE TABLE IF NOT EXISTS ouvrieres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT UNIQUE
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS modeles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT UNIQUE
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS postes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT UNIQUE
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS production (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        ouvriere TEXT,
        modele TEXT,
        poste TEXT,
        couleur_ticket TEXT,
        paquet_num INTEGER,
        quantite INTEGER,
        manque INTEGER DEFAULT 0,
        remarque TEXT
    )
''')
conn.commit()

# Titre Principal
st.title("🧵 Système de Gestion d'Atelier de Couture")

# Menu de Navigation
menu = st.sidebar.radio("Navigation", [
    "Saisie des Paquets (Saisie Rapide)", 
    "Gestion Paramètres (Ouvrière/Modèle/Poste)", 
    "Tableau de Production", 
    "Statistiques & Calculs"
])

# ---------------------------------------------------------
# 1. GESTION DES PARAMÈTRES (Ajouter Ouvrière, Modèle, Poste)
# ---------------------------------------------------------
if menu == "Gestion Paramètres (Ouvrière/Modèle/Poste)":
    st.subheader("⚙️ Configuration : Ajouter / Gérer les paramètres")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 👩‍خ Ouvrières")
        nouv_ouvriere = st.text_input("Nouvelle Ouvrière")
        if st.button("➕ Ajouter Ouvrière"):
            if nouv_ouvriere:
                try:
                    c.execute("INSERT INTO ouvrieres (nom) VALUES (?)", (nouv_ouvriere.strip(),))
                    conn.commit()
                    st.success(f"Ouvrière '{nouv_ouvriere}' ajoutée avec succès!")
                except:
                    st.warning("Cette ouvrière existe déjà.")
            else:
                st.error("Veuillez saisir un nom.")
        
        df_ouv = pd.read_sql_query("SELECT nom FROM ouvrieres", conn)
        st.dataframe(df_ouv, use_container_width=True)

    with col2:
        st.markdown("### 👗 Modèles")
        nouv_modele = st.text_input("Nouveau Modèle")
        if st.button("➕ Ajouter Modèle"):
            if nouv_modele:
                try:
                    c.execute("INSERT INTO modeles (nom) VALUES (?)", (nouv_modele.strip(),))
                    conn.commit()
                    st.success(f"Modèle '{nouv_modele}' ajouté avec succès!")
                except:
                    st.warning("Ce modèle existe déjà.")
            else:
                st.error("Veuillez saisir un nom.")
        
        df_mod = pd.read_sql_query("SELECT nom FROM modeles", conn)
        st.dataframe(df_mod, use_container_width=True)

    with col3:
        st.markdown("### 📍 Postes de travail")
        nouv_poste = st.text_input("Nouveau Poste")
        if st.button("➕ Ajouter Poste"):
            if nouv_poste:
                try:
                    c.execute("INSERT INTO postes (nom) VALUES (?)", (nouv_poste.strip(),))
                    conn.commit()
                    st.success(f"Poste '{nouv_poste}' ajouté avec succès!")
                except:
                    st.warning("Ce poste existe déjà.")
            else:
                st.error("Veuillez saisir un nom.")
        
        df_pst = pd.read_sql_query("SELECT nom FROM postes", conn)
        st.dataframe(df_pst, use_container_width=True)

# ---------------------------------------------------------
# 2. SAISIE DES PAQUETS (SAISIE RAPIDE AVEC CONTOUR)
# ---------------------------------------------------------
elif menu == "Saisie des Paquets (Saisie Rapide)":
    
    # Récupération des données enregistrées
    ouvrieres_list = [row[0] for row in c.execute("SELECT nom FROM ouvrieres").fetchall()]
    modeles_list = [row[0] for row in c.execute("SELECT nom FROM modeles").fetchall()]
    postes_list = [row[0] for row in c.execute("SELECT nom FROM postes").fetchall()]

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("📦 Formulaire d'entrée groupee des paquets")
    st.write("Saisissez toutes les informations ainsi que les paquets en une seule fois.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👤 Informations du travail")
        ouvriere = st.selectbox("Sélectionner l'ouvrière", ouvrieres_list if ouvrieres_list else ["Aucune ouvrière"])
        modele = st.selectbox("Sélectionner le modèle", modeles_list if modeles_list else ["Robe"])
        poste = st.selectbox("Sélectionner le poste", postes_list if postes_list else ["Standard"])
        couleur_ticket = st.selectbox("Couleur de Ticket", ["Blanche", "Rouge", "Jaune", "Bleue", "Verte", "Rose", "Autre"])

    with col2:
        st.markdown("#### 🔢 Paquets & Quantités & Manques")
        method = st.radio("Méthode de saisie des numéros de paquets:", [
            "Liste personnalisée (séparés par des virgules : 1, 2, 3, 5, 8)",
            "Intervalle (De paquet X à paquet Y)"
        ])
        
        if "Liste" in method:
            custom_paquets = st.text_input("Saisissez les paquets (ex: 1, 2, 3, 5, 8):", value="1, 2, 3, 5, 8")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                start_p = st.number_input("Du paquet N°:", min_value=1, value=1, step=1)
            with col_b:
                end_p = st.number_input("Au paquet N°:", min_value=1, value=5, step=1)

        quantite_par_paquet = st.number_input("Nombre de pièces par paquet:", min_value=1, value=12, step=1)
        manque = st.number_input("Nombre de manques / pièces défectueuses (Manque):", min_value=0, value=0, step=1)
        remarque = st.text_input("Remarques (Optionnel):", value="")

    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("💾 Enregistrer tous les paquets", type="primary", use_container_width=True):
        if not ouvrieres_list or not modeles_list:
            st.error("⚠️ Veuillez d'abord ajouter au moins une ouvrière et un modèle dans le menu 'Gestion Paramètres' !")
        else:
            paquets_list = []
            if "Liste" in method:
                try:
                    paquets_list = [int(x.strip()) for x in custom_paquets.split(",") if x.strip().isdigit()]
                except Exception:
                    st.error("⚠️ Format de liste incorrect. Exemple: 1, 2, 3, 5, 8")
            else:
                if start_p > end_p:
                    st.error("⚠️ Le paquet de départ doit être inférieur ou égal au paquet de fin!")
                else:
                    paquets_list = list(range(int(start_p), int(end_p) + 1))

            if paquets_list:
                today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                for p_num in paquets_list:
                    c.execute('''
                        INSERT INTO production (date, ouvriere, modele, poste, couleur_ticket, paquet_num, quantite, manque, remarque)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (today_str, ouvriere, modele, poste, couleur_ticket, p_num, quantite_par_paquet, manque, remarque))
                
                conn.commit()
                total_pcs = len(paquets_list) * quantite_par_paquet
                st.success(f"✅ Enregistrement réussi de {len(paquets_list)} paquets ({paquets_list}) pour l'ouvrière [{ouvriere}] - Modèle [{modele}] - Poste [{poste}]. Total: {total_pcs} pièces (Manque: {manque}).")

# ---------------------------------------------------------
# 3. TABLEAU DE PRODUCTION
# ---------------------------------------------------------
elif menu == "Tableau de Production":
    st.subheader("📋 Historique de la Production")
    
    df = pd.read_sql_query("""
        SELECT 
            id AS 'ID', 
            date AS 'Date', 
            ouvriere AS 'Ouvrière', 
            modele AS 'Modèle', 
            poste AS 'Poste', 
            couleur_ticket AS 'Ticket', 
            paquet_num AS 'N° Paquet', 
            quantite AS 'Quantité',
            manque AS 'Manque',
            remarque AS 'Remarque'
        FROM production ORDER BY id DESC
    """, conn)
    
    if not df.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            workers = ["Toutes"] + list(df['Ouvrière'].unique())
            selected_worker = st.selectbox("Filtrer par Ouvrière:", workers)
        with col_f2:
            models = ["Tous"] + list(df['Modèle'].unique())
            selected_model = st.selectbox("Filtrer par Modèle:", models)
            
        df_filtered = df.copy()
        if selected_worker != "Toutes":
            df_filtered = df_filtered[df_filtered['Ouvrière'] == selected_worker]
        if selected_model != "Tous":
            df_filtered = df_filtered[df_filtered['Modèle'] == selected_model]
            
        st.dataframe(df_filtered, use_container_width=True)
    else:
        st.info("Aucun paquet enregistré pour le moment.")

# ---------------------------------------------------------
# 4. STATISTIQUES ET CALCULS
# ---------------------------------------------------------
else:
    st.subheader("📊 Statistiques et Calculs de Production")
    df = pd.read_sql_query("SELECT ouvriere, quantite, manque, paquet_num FROM production", conn)
    
    if not df.empty:
        total_paquets = len(df)
        total_pieces = df['quantite'].sum()
        total_manques = df['manque'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Paquets Réalisés", total_paquets)
        c2.metric("Total Pièces Produites", total_pieces)
        c3.metric("Total Manques / Déchets", total_manques)
        
        st.markdown("---")
        st.markdown("### Récapitulatif par Ouvrière :")
        
        summary = df.groupby("ouvriere").agg(
            Nombre_Paquets=('paquet_num', 'count'),
            Total_Pieces=('quantite', 'sum'),
            Total_Manque=('manque', 'sum')
        ).reset_index()
        
        summary.columns = ["Ouvrière", "Nombre de Paquets", "Total Pièces", "Total Manque"]
        st.table(summary)
        
        st.bar_chart(summary.set_index("Ouvrière")["Total Pièces"])
    else:
        st.info("Aucune donnée disponible pour le moment.")
