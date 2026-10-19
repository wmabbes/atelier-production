import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# Configuration de la page
st.set_page_config(page_title="Atelier Couture - Gestion de Production", page_icon="🧵", layout="wide")

# Style CSS pour l'encadrement
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

# Connexion SQLite
conn = sqlite3.connect('atelier_production_v2.db', check_same_thread=False)
c = conn.cursor()

# Tables SQL propres et unifiées
c.execute('CREATE TABLE IF NOT EXISTS ouvrieres (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE)')
c.execute('CREATE TABLE IF NOT EXISTS modeles (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE)')
c.execute('CREATE TABLE IF NOT EXISTS postes (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE)')

c.execute('''
    CREATE TABLE IF NOT EXISTS production (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_travail TEXT,
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

# Postes par défaut
postes_defaut = ["DOS", "DEVANT", "CONTROL", "FINITION", "MONTAGE", "ASSEMBLAGE"]
for p in postes_defaut:
    try:
        c.execute("INSERT INTO postes (nom) VALUES (?)", (p,))
    except:
        pass
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
# 1. SAISIE DES PAQUETS
# ---------------------------------------------------------
if menu == "Saisie des Paquets (Saisie Rapide)":
    
    ouvrieres_list = [row[0] for row in c.execute("SELECT nom FROM ouvrieres").fetchall()]
    modeles_list = [row[0] for row in c.execute("SELECT nom FROM modeles").fetchall()]
    postes_list = [row[0] for row in c.execute("SELECT nom FROM postes").fetchall()]

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("📦 Formulaire d'entrée groupée des paquets")
    
    col_date, col_ticket = st.columns(2)
    with col_date:
        date_saisie = st.date_input("Date du travail", date.today())
    with col_ticket:
        couleur_ticket = st.selectbox("Couleur de Ticket", ["Blanche", "Rouge", "Jaune", "Bleue", "Verte", "Rose", "Autre"])

    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👤 Informations du travail")
        ouvriere = st.selectbox("Ouvrière (الخدامة)", ouvrieres_list if ouvrieres_list else ["Ajoutez une ouvrière d'abord"])
        modele = st.selectbox("Modèle (الموديل)", modeles_list if modeles_list else ["Ajoutez un modèle d'abord"])
        poste = st.selectbox("Poste de travail (Dos, Devant, Control...)", postes_list if postes_list else ["Standard"])

    with col2:
        st.markdown("#### 🔢 Paquets, Quantités & Manques")
        method = st.radio("Méthode de saisie des paquets:", [
            "Liste personnalisée (séparés par des virgules : 1, 2, 3, 5, 8)",
            "Intervalle (De paquet X à paquet Y)"
        ])
        
        if "Liste" in method:
            custom_paquets = st.text_input("Numéros des paquets (ex: 1, 2, 3, 5, 8):", value="1, 2, 3, 5, 8")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                start_p = st.number_input("Du paquet N°:", min_value=1, value=1, step=1)
            with col_b:
                end_p = st.number_input("Au paquet N°:", min_value=1, value=5, step=1)

        quantite_par_paquet = st.number_input("Nombre de pièces par paquet (Quantité):", min_value=1, value=12, step=1)
        manque = st.number_input("Nombre de pièces manquantes (Manque / الناقص):", min_value=0, value=0, step=1)
        remarque = st.text_input("Remarques (Optionnel):", value="")

    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("💾 Enregistrer tous les paquets", type="primary", use_container_width=True):
        if not ouvrieres_list or not modeles_list:
            st.error("⚠️ Veuillez ajouter au moins une ouvrière et un modèle dans le menu 'Gestion Paramètres' !")
        else:
            paquets_list = []
            if "Liste" in method:
                try:
                    paquets_list = [int(x.strip()) for x in custom_paquets.split(",") if x.strip().isdigit()]
                except Exception:
                    st.error("⚠️ Format incorrect. Exemple: 1, 2, 3, 5, 8")
            else:
                if start_p > end_p:
                    st.error("⚠️ Le paquet de départ doit être inférieur ou égal au paquet de fin!")
                else:
                    paquets_list = list(range(int(start_p), int(end_p) + 1))

            if paquets_list:
                str_date = date_saisie.strftime("%Y-%m-%d")
                
                for p_num in paquets_list:
                    c.execute('''
                        INSERT INTO production (date_travail, ouvriere, modele, poste, couleur_ticket, paquet_num, quantite, manque, remarque)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (str_date, ouvriere, modele, poste, couleur_ticket, p_num, quantite_par_paquet, manque, remarque))
                
                conn.commit()
                total_pcs = len(paquets_list) * quantite_par_paquet
                st.success(f"✅ Enregistré avec succès ! Paquets: {paquets_list} | Total Pièces: {total_pcs} (Manque: {manque})")

# ---------------------------------------------------------
# 2. GESTION DES PARAMÈTRES
# ---------------------------------------------------------
elif menu == "Gestion Paramètres (Ouvrière/Modèle/Poste)":
    st.subheader("⚙️ Configuration : Ajouter العاملات والموديلات والأقسام")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 👩‍خ Ouvrière (الخدامة)")
        nouv_ouvriere = st.text_input("Nom de l'ouvrière")
        if st.button("➕ Ajouter Ouvrière"):
            if nouv_ouvriere:
                try:
                    c.execute("INSERT INTO ouvrieres (nom) VALUES (?)", (nouv_ouvriere.strip(),))
                    conn.commit()
                    st.success(f"Ouvrière '{nouv_ouvriere}' ajoutée !")
                    st.rerun()
                except:
                    st.warning("Existe déjà.")
            else:
                st.error("Saisissez un nom.")
        
        df_ouv = pd.read_sql_query("SELECT nom AS 'Ouvrière' FROM ouvrieres", conn)
        st.dataframe(df_ouv, use_container_width=True)

    with col2:
        st.markdown("### 👗 Modèle (الموديل)")
        nouv_modele = st.text_input("Nom du modèle")
        if st.button("➕ Ajouter Modèle"):
            if nouv_modele:
                try:
                    c.execute("INSERT INTO modeles (nom) VALUES (?)", (nouv_modele.strip(),))
                    conn.commit()
                    st.success(f"Modèle '{nouv_modele}' ajouté !")
                    st.rerun()
                except:
                    st.warning("Existe déjà.")
            else:
                st.error("Saisissez un modèle.")
        
        df_mod = pd.read_sql_query("SELECT nom AS 'Modèle' FROM modeles", conn)
        st.dataframe(df_mod, use_container_width=True)

    with col3:
        st.markdown("### 📍 Poste (Dos, Devant...)")
        nouv_poste = st.text_input("Nom du poste")
        if st.button("➕ Ajouter Poste"):
            if nouv_poste:
                try:
                    c.execute("INSERT INTO postes (nom) VALUES (?)", (nouv_poste.strip(),))
                    conn.commit()
                    st.success(f"Poste '{nouv_poste}' ajouté !")
                    st.rerun()
                except:
                    st.warning("Existe déjà.")
            else:
                st.error("Saisissez un poste.")
        
        df_pst = pd.read_sql_query("SELECT nom AS 'Poste' FROM postes", conn)
        st.dataframe(df_pst, use_container_width=True)

# ---------------------------------------------------------
# 3. TABLEAU DE PRODUCTION
# ---------------------------------------------------------
elif menu == "Tableau de Production":
    st.subheader("📋 Historique de la Production")
    
    df = pd.read_sql_query("""
        SELECT 
            id AS 'ID', 
            date_travail AS 'Date', 
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
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            workers = ["Toutes"] + list(df['Ouvrière'].unique())
            selected_worker = st.selectbox("Filtrer par Ouvrière:", workers)
        with col_f2:
            models = ["Tous"] + list(df['Modèle'].unique())
            selected_model = st.selectbox("Filtrer par Modèle:", models)
        with col_f3:
            postes = ["Tous"] + list(df['Poste'].unique())
            selected_poste = st.selectbox("Filtrer par Poste:", postes)
            
        df_filtered = df.copy()
        if selected_worker != "Toutes":
            df_filtered = df_filtered[df_filtered['Ouvrière'] == selected_worker]
        if selected_model != "Tous":
            df_filtered = df_filtered[df_filtered['Modèle'] == selected_model]
        if selected_poste != "Tous":
            df_filtered = df_filtered[df_filtered['Poste'] == selected_poste]
            
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
        c3.metric("Total Manques (الناقص)", total_manques)
        
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
