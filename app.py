from datetime import date
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Suivi de Production - Atelier Textile", page_icon="🧵", layout="wide"
)

# --- تصميم عصري متكامل لصفحة الدخول (خلفية خياطة وأزياء تملأ الصفحة بالكامل) ---
st.markdown(
    """
    <style>
    /* إخفاء القائمة الجانبية وعلامات التبويب أثناء وجود المستخدم في صفحة الدخول */
    .login-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-image: linear-gradient(rgba(10, 25, 47, 0.82), rgba(15, 32, 67, 0.90)), 
                          url('https://images.unsplash.com/photo-1558769132-cb1aea458c5e?q=80&w=1920&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 999999;
        color: white;
        padding: 20px;
    }
    .login-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
        text-align: center;
        max-width: 450px;
        width: 100%;
    }
    .atelier-badge {
        display: inline-block;
        background: #ffb703;
        color: #000;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin-bottom: 15px;
        text-transform: uppercase;
    }
    .stApp {
        background-color: #f4f7f6;
    }
    h1, h2, h3 {
        color: #1b3b6f;
    }
    .stButton>button {
        background-color: #1b3b6f;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        width: 100%;
        padding: 10px;
    }
    .stButton>button:hover {
        background-color: #122647;
        color: white;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- BASE DE DONNÉES SQLITE (Multi-user safe) ---
DB_NAME = "atelier_production.db"


def get_connection():
    return sqlite3.connect(DB_NAME, timeout=30.0, check_same_thread=False)


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS postes (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS manques_types (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS workers (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, prenom TEXT, categorie TEXT, objectif INTEGER, UNIQUE(nom, prenom))"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS modeles (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS paquets (id INTEGER PRIMARY KEY AUTOINCREMENT, modele TEXT, ticket TEXT, paquet_num INTEGER, quantite INTEGER)"
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS production (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, nom TEXT, prenom TEXT, categorie TEXT,
                    sous_categorie TEXT, poste TEXT, heure TEXT,
                    modele TEXT, ticket TEXT, paquet_num INTEGER,
                    pieces INTEGER, objectif INTEGER,
                    UNIQUE(nom, prenom, modele, ticket, paquet_num)
                )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS manques (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, nom TEXT, prenom TEXT, categorie TEXT,
                    heure TEXT, type_manque TEXT, duree TEXT, remarque TEXT
                )"""
    )

    c.execute("SELECT COUNT(*) FROM postes")
    if c.fetchone()[0] == 0:
        default_postes = [
            ("Surfilage",),
            ("Piqueuse",),
            ("Assemblage",),
            ("Repassage",),
            ("Finition",),
        ]
        c.executemany("INSERT INTO postes (nom) VALUES (?)", default_postes)

    c.execute("SELECT COUNT(*) FROM manques_types")
    if c.fetchone()[0] == 0:
        default_m = [
            ("Panne machine (Réparation)",),
            ("Pièces avec défauts",),
            ("Manque garniture / Matière",),
            ("Attente Lancement / Modèle",),
            ("Autre problème technique",),
        ]
        c.executemany("INSERT INTO manques_types (nom) VALUES (?)", default_m)

    c.execute("SELECT COUNT(*) FROM workers")
    if c.fetchone()[0] == 0:
        default_w = [
            ("Ben Salah", "Mariem", "dos", 50),
            ("TRABELSI", "Sarra", "devant", 60),
            ("GHARBI", "Fatma", "finition", 80),
            ("KHELIFA", "Amani", "controle", 100),
        ]
        c.executemany(
            "INSERT INTO workers (nom, prenom, categorie, objectif) VALUES (?, ?, ?, ?)",
            default_w,
        )

    conn.commit()
    conn.close()


init_db()


def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        # واجهة تسجيل الدخول بتصميم كامل الشاشة (Full-Screen Login)
        st.markdown(
            """
            <div class="login-container">
                <div class="login-card">
                    <div class="atelier-badge">🧵 Atelier de Confection & Textile</div>
                    <h1 style="color: white; margin-bottom: 10px; font-size: 26px;">Suivi de Production</h1>
                    <p style="color: #cbd5e1; font-size: 14px; margin-bottom: 25px;">
                        Gestion des ateliers (Pantalon, Chemise, Jupe, Jean)
                    </p>
                </div>
            </div>
        """,
            unsafe_allow_html=True,
        )

        # عناصر الإدخال الخاصة بكلمة المرور لتكون متناسقة فوق الخلفية
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("<div style='height: 38vh;'></div>", unsafe_allow_html=True)
            pwd = st.text_input(
                "🔑 Code d'accès :", type="password", key="pwd_input"
            )
            if st.button("🚀 Valider et Entrer"):
                if pwd == "1234":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Code incorrect !")
        return False
    return True


if not check_password():
    st.stop()

st.markdown(
    "<h1 style='color: #1b3b6f; margin-bottom: 0px;'>🧵 Suivi de Production - Atelier</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<hr style='margin-top: 5px; margin-bottom: 20px; border-top: 2px solid #1b3b6f;'>",
    unsafe_allow_html=True,
)

conn = get_connection()
postes_list = [row[0] for row in conn.execute("SELECT nom FROM postes").fetchall()]
manques_types = [
    row[0] for row in conn.execute("SELECT nom FROM manques_types").fetchall()
]
workers_db = conn.execute(
    "SELECT nom, prenom, categorie, objectif FROM workers"
).fetchall()
workers = [
    {"Nom": w[0], "Prénom": w[1], "Catégorie": w[2], "Objectif": w[3]}
    for w in workers_db
]
modeles_list = [
    row[0] for row in conn.execute("SELECT nom FROM modeles").fetchall()
]
conn.close()

# --- SIDEBAR ---
st.sidebar.header("👷‍♀️ Paramètres & Ouvrières")

st.sidebar.subheader("➕ Ajouter un Poste")
new_poste_name = st.sidebar.text_input("Nom du Poste", key="input_new_poste")
if st.sidebar.button("➕ Ajouter Poste"):
    clean_poste = new_poste_name.strip()
    if clean_poste:
        try:
            conn = get_connection()
            conn.execute("INSERT INTO postes (nom) VALUES (?)", (clean_poste,))
            conn.commit()
            conn.close()
            st.sidebar.success(f"✅ Poste '{clean_poste}' ajouté !")
            st.rerun()
        except sqlite3.IntegrityError:
            st.sidebar.warning(f"⚠️ Le poste existe déjà !")

st.sidebar.markdown("---")
st.sidebar.subheader("➕ Ajouter une Ouvrière")
w_nom = st.sidebar.text_input("Nom", key="w_nom_in")
w_prenom = st.sidebar.text_input("Prénom", key="w_prenom_in")
w_cat = st.sidebar.selectbox(
    "Section", ["dos", "devant", "finition", "controle"], key="w_cat_in"
)
w_obj = st.sidebar.number_input(
    "Objectif fixe/heure", min_value=1, value=50, key="w_obj_in"
)
if st.sidebar.button("➕ Ajouter l'ouvrière"):
    clean_nom = w_nom.strip()
    clean_prenom = w_prenom.strip()
    if clean_nom and clean_prenom:
        try:
            conn = get_connection()
            conn.execute(
                "INSERT INTO workers (nom, prenom, categorie, objectif) VALUES (?, ?, ?, ?)",
                (clean_nom, clean_prenom, w_cat, w_obj),
            )
            conn.commit()
            conn.close()
            st.sidebar.success(f"✅ Ouvrière ajoutée avec succès !")
            st.rerun()
        except sqlite3.IntegrityError:
            st.sidebar.error(f"❌ L'ouvrière existe déjà !")

st.sidebar.markdown("---")
st.sidebar.header("📦 Modèles & Tickets")
new_model_input = st.sidebar.text_input("Nom du Modèle", key="input_new_model")
if st.sidebar.button("➕ Créer Modèle"):
    clean_model = new_model_input.strip()
    if clean_model:
        try:
            conn = get_connection()
            conn.execute(
                "INSERT INTO modeles (nom) VALUES (?)", (clean_model,)
            )
            conn.commit()
            conn.close()
            st.sidebar.success(f"✅ Modèle créé !")
            st.rerun()
        except sqlite3.IntegrityError:
            st.sidebar.warning("⚠️ Ce modèle existe déjà !")

if modeles_list:
    target_model = st.sidebar.selectbox(
        "Modèle concerné", modeles_list, key="sel_target_m"
    )
    t_name_in = st.sidebar.text_input(
        "Nom du Ticket", value="Billet Bleu", key="t_name_input"
    )
    p_num_in = st.sidebar.number_input(
        "N° du Paquet", min_value=1, value=1, key="p_num_input"
    )
    p_qte_in = st.sidebar.number_input(
        "Quantité de pièces", min_value=1, value=20, key="p_qte_input"
    )

    if st.sidebar.button("💾 Ajouter au Modèle"):
        clean_ticket = t_name_in.strip()
        if clean_ticket:
            conn = get_connection()
            check_p = conn.execute(
                "SELECT id FROM paquets WHERE modele=? AND ticket=? AND paquet_num=?",
                (target_model, clean_ticket, p_num_in),
            ).fetchone()
            if check_p:
                st.sidebar.error(f"❌ Le paquet existe déjà !")
            else:
                conn.execute(
                    "INSERT INTO paquets (modele, ticket, paquet_num, quantite) VALUES (?, ?, ?, ?)",
                    (target_model, clean_ticket, p_num_in, p_qte_in),
                )
                conn.commit()
                st.sidebar.success(f"✅ Paquet ajouté !")
