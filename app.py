from datetime import date
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Suivi de Production - Atelier Textile", page_icon="🧵", layout="wide"
)

# --- تصميم عصري مستوحى من النسيج ودرجات الأزرق ---
st.markdown(
    """
    <style>
    .login-bg {
        background-image: linear-gradient(rgba(10, 25, 47, 0.75), rgba(15, 32, 67, 0.85)), 
                    url('https://images.unsplash.com/photo-1584917865442-de89df76afd3?q=80&w=1600&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        padding: 40px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 20px;
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
    }
    .stButton>button:hover {
        background-color: #122647;
        color: white;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- BASE DE DONNÉES SQLITE ---
DB_NAME = "atelier_production.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
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
                    pieces INTEGER, objectif INTEGER
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


def get_connection():
    return sqlite3.connect(DB_NAME)


def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown(
            """
            <div class="login-bg">
                <h1>🧵 Atelier de Production Textile</h1>
                <p>Veuillez entrer le code d'accès pour continuer</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pwd = st.text_input(
                "🔑 Mot de passe :", type="password", key="pwd_input"
            )
            if st.button("🚀 Valider et Entrer"):
                if pwd == "1234":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Mot de passe incorrect !")
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
                st.rerun()
            conn.close()

st.sidebar.markdown("---")
st.sidebar.header("🗑️ Supprimer des éléments")

st.sidebar.subheader("👷 Supprimer une ouvrière")
conn = get_connection()
ouvrieres_db = conn.execute(
    "SELECT nom, prenom, categorie FROM workers ORDER BY nom"
).fetchall()
conn.close()

if ouvrieres_db:
    ouvriere_options = [
        f"{w[0]} {w[1]} - {w[2]}" for w in ouvrieres_db
    ]
    ouvriere_choisie = st.sidebar.selectbox(
        "Choisir l'ouvrière",
        ouvriere_options,
        key="del_worker",
    )

    if st.sidebar.button("🗑️ SUPPRIMER OUVRIÈRE", key="btn_del_worker"):
        idx = ouvriere_options.index(ouvriere_choisie)
        w = ouvrieres_db[idx]
        conn = get_connection()
        conn.execute(
            "DELETE FROM workers WHERE nom=? AND prenom=?",
            (w[0], w[1]),
        )
        conn.commit()
        conn.close()
        st.sidebar.success("Ouvrière supprimée.")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🧵 Supprimer un poste")
conn = get_connection()
postes_db = conn.execute(
    "SELECT nom FROM postes ORDER BY nom"
).fetchall()
conn.close()

if postes_db:
    poste_choisi = st.sidebar.selectbox(
        "Choisir le poste",
        [p[0] for p in postes_db],
        key="del_poste",
    )
    if st.sidebar.button("🗑️ SUPPRIMER POSTE", key="btn_del_poste"):
        conn = get_connection()
        conn.execute("DELETE FROM postes WHERE nom=?", (poste_choisi,))
        conn.commit()
        conn.close()
        st.sidebar.success("Poste supprimé.")
        st.rerun()
else:
    st.sidebar.info("Aucun poste disponible.")

st.sidebar.subheader("📦 Supprimer un modèle")
conn = get_connection()
modeles_db = conn.execute(
    "SELECT nom FROM modeles ORDER BY nom"
).fetchall()
conn.close()

if modeles_db:
    modele_choisi = st.sidebar.selectbox(
        "Choisir le modèle",
        [m[0] for m in modeles_db],
        key="del_modele",
    )

    if st.sidebar.button("🗑️ SUPPRIMER MODÈLE", key="btn_del_modele"):
        conn = get_connection()
        conn.execute("DELETE FROM paquets WHERE modele=?", (modele_choisi,))
        conn.execute("DELETE FROM modeles WHERE nom=?", (modele_choisi,))
        conn.commit()
        conn.close()
        st.success("Modèle supprimé.")
        st.rerun()
else:
    st.info("Aucun modèle disponible. Ajoute d'abord un modèle.")

st.sidebar.subheader("⚠️ Supprimer un manque / panne")
conn = get_connection()
manques_db = conn.execute(
    """SELECT id, date, nom, prenom, type_manque, duree
        FROM manques ORDER BY id DESC"""
).fetchall()
conn.close()

if manques_db:
    manque_options = [
        f"#{m[0]} | {m[1]} | {m[2]} {m[3]} | {m[4]} | {m[5]}"
        for m in manques_db
    ]

    manque_choisi = st.sidebar.selectbox(
        "Choisir le manque / panne",
        manque_options,
        key="del_manque",
    )

    if st.sidebar.button(
        "🗑️ SUPPRIMER MANQUE / PANNE",
        key="btn_del_manque",
    ):
        idx = manque_options.index(manque_choisi)
        manque_id = manques_db[idx][0]

        conn = get_connection()
        conn.execute("DELETE FROM manques WHERE id=?", (manque_id,))
        conn.commit()
        conn.close()

        st.sidebar.success("Manque / panne supprimé.")
        st.rerun()
else:
    st.sidebar.button(
        "🗑️ SUPPRIMER MANQUE / PANNE",
        key="btn_del_manque_vide",
        disabled=True,
    )
    st.sidebar.info("Aucun manque / panne enregistré.")

st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Ajouter une panne")
conn = get_connection()
ouvrieres = conn.execute(
    "SELECT nom, prenom, categorie FROM workers ORDER BY nom"
).fetchall()
conn.close()

if ouvrieres:
    ouvriere_options = [
        f"{w[0]} {w[1]} - {w[2]}" for w in ouvrieres
    ]

    ouvriere = st.sidebar.selectbox(
        "Choisir l'ouvrière",
        ouvriere_options,
        key="ajout_panne_ouvriere",
    )

    date_panne = st.sidebar.date_input(
        "Date de la panne",
        key="date_panne",
    )

    heure_panne = st.sidebar.time_input(
        "Heure de la panne",
        key="heure_panne",
    )

    type_panne = st.sidebar.text_input(
        "Type de panne",
        placeholder="Exemple : machine en panne",
        key="type_panne",
    )

    duree_panne = st.sidebar.number_input(
        "Durée (minutes)",
        min_value=0,
        step=5,
        key="duree_panne",
    )

    remarque_panne = st.sidebar.text_input(
        "Remarque",
        key="remarque_panne",
    )

    if st.sidebar.button("➕ AJOUTER PANNE", key="btn_ajouter_panne"):
        if not type_panne.strip():
            st.sidebar.warning("Saisis le type de panne.")
        else:
            idx = ouvriere_options.index(ouvriere)
            w = ouvrieres[idx]

            conn = get_connection()
            conn.execute(
                """INSERT INTO manques
                (date, nom, prenom, categorie, heure,
                 type_manque, duree, remarque)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    date_panne.isoformat(),
                    w[0],
                    w[1],
                    w[2],
                    heure_panne.strftime("%H:%M"),
                    type_panne.strip(),
                    duree_panne,
                    remarque_panne.strip(),
                ),
            )
            conn.commit()
            conn.close()

            st.sidebar.success("Panne ajoutée avec succès.")
            st.rerun()
else:
    st.sidebar.warning(
        "Ajoute d'abord une ouvrière dans la liste des ouvrières."
    )

# --- MAIN PAGE ---
selected_date = st.date_input("📅 Date du jour", date.today(), format="DD/MM/YYYY")
st.markdown("---")

tab_prod, tab_manque, tab_suivi = st.tabs(
    [
        "⏱️ Saisie de la Production",
        "⚠️ Enregistrer les manques",
        "📊 Suivi & Sortie Modèle",
    ]
)

tranches_horaires = [
    "07:30 - 08:30",
    "08:30 - 09:30",
    "09:30 - 10:30",
    "10:30 - 12:00",
    "13:00 - 14:00",
    "14:00 - 15:00",
    "15:00 - 16:00",
    "16:00 - 17:00",
]

sections_def = [
    ("DOS", "dos"),
    ("DEVANT", "devant"),
    ("FINITION", "finition"),
    ("CONTRÔLE", "controle"),
]

with tab_prod:
    if not workers:
        st.error("⚠️ Veuillez ajouter des ouvrières !")
    elif not modeles_list:
        st.warning("⚠️ Veuillez ajouter des modèles !")
    else:
        sec_tabs = st.tabs(["📋 DOS", "📋 DEVANT", "📋 FINITION", "📋 CONTRÔLE"])

        for idx, (title, cat_key) in enumerate(sections_def):
            with sec_tabs[idx]:
                st.markdown(f"### 📍 Section : {title}")
                cat_workers = [w for w in workers if w["Catégorie"] == cat_key]

                if not cat_workers:
                    st.warning(f"Aucune ouvrière dans {title}.")
                else:
                    worker_opts = [
                        f"{w['Prénom']} {w['Nom']} (Obj: {w['Objectif']} pcs/h)"
                        for w in cat_workers
                    ]

                    col_a, col_b = st.columns(2)
                    with col_a:
                        sel_worker_str = st.selectbox(
                            "Ouvrière", worker_opts, key=f"prod_w_{cat_key}"
                        )
                        w_selected_obj = cat_workers[
                            worker_opts.index(sel_worker_str)
                        ]

                        sous_cat = "-"
                        if cat_key == "controle":
                            sous_cat = st.radio(
                                "Type de Contrôle :",
                                ["Contrôle DOS", "Contrôle DEVANT"],
                                key="ctrl_sub_type",
                            )
                            sel_poste = "Contrôle"
                        else:
                            sel_poste = st.selectbox(
                                "Poste Actuel",
                                postes_list,
                                key=f"prod_poste_{cat_key}",
                            )

                        heure = st.selectbox(
                            "Tranche Horaire",
                            tranches_horaires,
                            key=f"prod_h_{cat_key}",
                        )

                    with col_b:
                        sel_cmd = st.selectbox(
                            "Modèle", modeles_list, key=f"prod_cmd_{cat_key}"
                        )

                        conn = get_connection()
                        tickets_db = conn.execute(
                            "SELECT DISTINCT ticket FROM paquets WHERE modele=?",
                            (sel_cmd,),
                        ).fetchall()
                        conn.close()
                        tickets_opts = [t[0] for t in tickets_db]

                        sel_ticket = (
                            st.selectbox(
                                "Billet / Ticket",
                                tickets_opts,
                                key=f"prod_ticket_{cat_key}",
                            )
                            if tickets_opts
                            else None
                        )

                        # --- التعديل هنا: إدخال أرقام الباكوات بحرية عبر خانة نصية ---
                        paquet_input_str = st.text_input(
                            "Numéro(s) de Paquet (ex: 1 ou 1,2,3 ou 1-5)",
                            value="1",
                            key=f"prod_paquet_input_{cat_key}",
                            help="أدخل رقم الباكو مباشرة (مثال: 5) أو عدة أرقام مفصولة بفواصل (مثال: 1, 2, 3)"
                        )
                        
                        qty_per_paquet = st.number_input(
                            "Nombre de pièces par paquet",
                            min_value=1,
                            value=20,
                            key=f"prod_qty_paquet_{cat_key}"
                        )

                    if st.button(
                        f"💾 Enregistrer ({title})", key=f"btn_save_{cat_key}"
                    ):
                        # تحليل الأرقام المدخلة في خانة النص
                        paquets_to_save = []
                        try:
                            # دعم الأرقام المفردة أو المفصولة بفواصل
                            parts = paquet_input_str.split(",")
                            for p in parts:
                                p = p.strip()
                                if "-" in p:
                                    start, end = map(int, p.split("-"))
                                    paquets_to_save.extend(list(range(start, end + 1)))
                                elif p.isdigit():
                                    paquets_to_save.append(int(p))
                        except Exception:
                            pass

                        if not paquets_to_save:
                            st.error("⚠️ Veuillez entrer un numéro de paquet valide !")
                        else:
                            formatted_date_str = selected_date.strftime("%d/%m/%Y")
                            conn = get_connection()
                            
                            saved_count = 0
                            for p_num in paquets_to_save:
                                dup = conn.execute(
                                    """SELECT id FROM production
                                    WHERE date=? AND nom=? AND prenom=?
                                    AND modele=? AND ticket=? AND paquet_num=?
                                    AND sous_categorie=?""",
                                    (
                                        formatted_date_str,
                                        w_selected_obj["Nom"],
                                        w_selected_obj["Prénom"],
                                        sel_cmd,
                                        sel_ticket,
                                        p_num,
                                        sous_cat,
                                    ),
                                ).fetchone()

                                if not dup:
                                    conn.execute(
                                        """INSERT INTO production (date, nom, prenom, categorie, sous_categorie, poste, heure, modele, ticket, paquet_num, pieces, objectif)
                                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                        (
                                            formatted_date_str,
                                            w_selected_obj["Nom"],
                                            w_selected_obj["Prénom"],
                                            cat_key,
                                            sous_cat,
                                            sel_poste,
                                            heure,
                                            sel_cmd,
                                            sel_ticket,
                                            p_num,
                                            qty_per_paquet,
                                            w_selected_obj["Objectif"],
                                        ),
                                    )
                                    saved_count += 1

                            conn.commit()
                            conn.close()
                            
                            if saved_count > 0:
                                st.success(f"✅ Enregistré avec succès ({saved_count} paquet(s)) !")
                                st.rerun()
                            else:
                                st.error("❌ Erreur : Ces paquets ont déjà été enregistrés pour cette ouvrière !")

with tab_manque:
    st.subheader("⚠️ Enregistrer les manques / pannes")
    if workers:
        worker_opts_m = [
            f"[{w['Catégorie'].upper()}] {w['Prénom']} {w['Nom']}"
            for w in workers
        ]
        with st.form("form_manque"):
            sel_worker_m = st.selectbox(
                "Ouvrière concernée", worker_opts_m, key="manque_w"
            )
            w_obj_m = workers[worker_opts_m.index(sel_worker_m)]
            sel_cat_m = w_obj_m["Catégorie"]

            heure_m = st.selectbox(
                "Tranche Horaire", tranches_horaires, key="manque_h"
            )
            types_manques_avec_panne = list(manques_types)

            if "Panne" not in types_manques_avec_panne:
                types_manques_avec_panne.append("Panne")

            type_manque = st.selectbox(
                "Type de Manque",
                list(manques_types) + (
                    ["Panne"] if "Panne" not in manques_types else []
                ),
                key="manque_type"
            )
            duree_panne = st.selectbox(
                "Durée",
                [
                    "30 minutes",
                    "1 heure",
                    "1 heure et demi",
                    "2 heures",
                    "Plus de 2 heures",
                ],
                key="manque_duree",
            )
            remarque_m = st.text_input("Remarque", key="manque_rem")
            if st.form_submit_button("⚠️ Enregistrer l'Arrêt"):
                formatted_date_str = selected_date.strftime("%d/%m/%Y")
                conn = get_connection()
                conn.execute(
                    """INSERT INTO manques (date, nom, prenom, categorie, heure, type_manque, duree, remarque)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        formatted_date_str,
                        w_obj_m["Nom"],
                        w_obj_m["Prénom"],
                        sel_cat_m,
                        heure_m,
                        type_manque,
                        duree_panne,
                        remarque_m,
                    ),
                )
                conn.commit()
                conn.close()
                st.success("⚠️ Arrêt enregistré !")
                st.rerun()

with tab_suivi:
    st.subheader("📊 Bilan Global & Tableaux par Section")

    conn = get_connection()
    df_p = pd.read_sql_query("SELECT * FROM production", conn)
    df_m = pd.read_sql_query("SELECT * FROM manques", conn)
    conn.close()

    st.markdown("### 📦 Sortie Modèle - Validation Contrôle Final")
    summary_rows = []

    conn = get_connection()
    for m_name in modeles_list:
        target_qty = (
            conn.execute(
                "SELECT SUM(quantite) FROM paquets WHERE modele=?", (m_name,)
            ).fetchone()[0]
            or 0
        )
        validated_dos = (
            conn.execute(
                "SELECT SUM(pieces) FROM production WHERE modele=? AND categorie='controle' AND sous_categorie='Contrôle DOS'",
                (m_name,),
            ).fetchone()[0]
            or 0
        )
        validated_devant = (
            conn.execute(
                "SELECT SUM(pieces) FROM production WHERE modele=? AND categorie='controle' AND sous_categorie='Contrôle DEVANT'",
                (m_name,),
            ).fetchone()[0]
            or 0
        )

        dates_recorded = conn.execute(
            "SELECT DISTINCT date FROM production WHERE modele=?", (m_name,)
        ).fetchall()
        dates_str = (
            ", ".join([d[0] for d in dates_recorded])
            if dates_recorded
            else "-"
        )

        is_finished = (
            validated_dos >= target_qty
            and validated_devant >= target_qty
            and target_qty > 0
        )
        status = "✅ Sorti (Terminé)" if is_finished else "⏳ En cours..."

        summary_rows.append(
            {
                "Date": dates_str,
                "Modèle": m_name,
                "Quantité Prévue": target_qty,
                "Contrôle DOS": validated_dos,
                "Contrôle DEVANT": validated_devant,
                "Statut": status,
            }
        )
    conn.close()

    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)
    st.markdown("---")

    for title, cat_key in sections_def:
        st.markdown(f"## 📋 Section : {title}")
        col_w, col_prod = st.columns([1, 2])

        with col_w:
            cat_workers = [w for w in workers if w["Catégorie"] == cat_key]
            if cat_workers:
                st.dataframe(
                    pd.DataFrame(cat_workers)[["Prénom", "Nom", "Objectif"]],
                    use_container_width=True,
                )

        with col_prod:
            if not df_p.empty:
                df_cat = df_p[df_p["categorie"] == cat_key]
                if not df_cat.empty:
                    df_grouped = (
                        df_cat.groupby(
                            [
                                "date",
                                "modele",
                                "nom",
                                "prenom",
                                "sous_categorie",
                                "poste",
                                "heure",
                                "objectif",
                            ],
                            as_index=False,
                        )
                        .agg({"pieces": "sum"})
                        .rename(
                            columns={
                                "pieces": "Total Pièces",
                                "date": "Date Record",
                                "modele": "Modèle",
                                "nom": "Nom",
                                "prenom": "Prénom",
                                "sous_categorie": "Sous_Catégorie",
                                "poste": "Poste",
                                "heure": "Heure",
                                "objectif": "Objectif/Heure",
                            }
                        )
                    )
                    df_grouped["Rendement (%)"] = (
                        (df_grouped["Total Pièces"] / df_grouped["Objectif/Heure"])
                        * 100
                    ).round(2)
                    st.dataframe(df_grouped, use_container_width=True)
        st.markdown("---")

