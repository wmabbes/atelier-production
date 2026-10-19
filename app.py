from datetime import date
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Suivi de Production - Atelier", page_icon="🧵", layout="wide"
)

# --- BASE DE DONNÉES SQLITE (CONSERVATION DES DONNÉES) ---
DB_NAME = "atelier_production.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Table Postes
    c.execute(
        "CREATE TABLE IF NOT EXISTS postes (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE)"
    )
    # Table Manques Types
    c.execute(
        "CREATE TABLE IF NOT EXISTS manques_types (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE)"
    )
    # Table Workers
    c.execute(
        "CREATE TABLE IF NOT EXISTS workers (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, prenom TEXT, categorie TEXT, objectif INTEGER, UNIQUE(nom, prenom))"
    )
    # Table Commandes / Modèles
    c.execute(
        "CREATE TABLE IF NOT EXISTS modeles (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE)"
    )
    # Table Billets / Tickets & Paquets
    c.execute(
        "CREATE TABLE IF NOT EXISTS paquets (id INTEGER PRIMARY KEY AUTOINCREMENT, modele TEXT, ticket TEXT, paquet_num INTEGER, quantite INTEGER)"
    )
    # Table Production
    c.execute(
        """CREATE TABLE IF NOT EXISTS production (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, nom TEXT, prenom TEXT, categorie TEXT,
                    sous_categorie TEXT, poste TEXT, heure TEXT,
                    modele TEXT, ticket TEXT, paquet_num INTEGER,
                    pieces INTEGER, objectif INTEGER
                )"""
    )
    # Table Manques / Pannes
    c.execute(
        """CREATE TABLE IF NOT EXISTS manques (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, nom TEXT, prenom TEXT, categorie TEXT,
                    heure TEXT, type_manque TEXT, duree TEXT, remarque TEXT
                )"""
    )

    # Données par défaut si les tables sont vides
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
            ("Pièces avec défauts (Pièces rejetées)",),
            ("Manque garniture / Matière première",),
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


st.markdown(
    "<h1 style='color: #1f77b4; margin-bottom: 0px;'>Suivi de Production</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True
)

# Charger les paramètres
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
            st.sidebar.warning(f"⚠️ Le poste '{clean_poste}' existe déjà !")

st.sidebar.markdown("---")

st.sidebar.subheader("➕ Ajouter un type de Manque")
new_m_type = st.sidebar.text_input("Intitulé du Manque", key="input_new_manque")
if st.sidebar.button("➕ Ajouter Type Manque"):
    clean_manque = new_m_type.strip()
    if clean_manque:
        try:
            conn = get_connection()
            conn.execute(
                "INSERT INTO manques_types (nom) VALUES (?)", (clean_manque,)
            )
            conn.commit()
            conn.close()
            st.sidebar.success("✅ Type ajouté !")
            st.rerun()
        except sqlite3.IntegrityError:
            st.sidebar.warning("⚠️ Ce type de manque existe déjà !")

st.sidebar.markdown("---")

st.sidebar.subheader("➕ Ajouter une Ouvrière")
w_nom = st.sidebar.text_input("Nom", key="w_nom_in")
w_prenom = st.sidebar.text_input("Prénom", key="w_prenom_in")
w_cat = st.sidebar.selectbox(
    "Section / Département",
    ["dos", "devant", "finition", "controle"],
    key="w_cat_in",
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
            st.sidebar.success(
                f"✅ {clean_prenom} {clean_nom} ajoutée dans [{w_cat.upper()}] !"
            )
            st.rerun()
        except sqlite3.IntegrityError:
            st.sidebar.error(
                f"❌ L'ouvrière '{clean_prenom} {clean_nom}' existe déjà !"
            )

if workers:
    st.sidebar.markdown("---")
    st.sidebar.subheader("❌ Supprimer une ouvrière")
    worker_del_options = [
        f"[{w['Catégorie'].upper()}] {w['Prénom']} {w['Nom']}" for w in workers
    ]
    selected_w_to_del = st.sidebar.selectbox(
        "Ouvrière à supprimer", worker_del_options
    )
    if st.sidebar.button("🗑️ Supprimer l'ouvrière"):
        del_w = workers[worker_del_options.index(selected_w_to_del)]
        conn = get_connection()
        conn.execute(
            "DELETE FROM workers WHERE nom=? AND prenom=?",
            (del_w["Nom"], del_w["Prénom"]),
        )
        conn.commit()
        conn.close()
        st.sidebar.success(f"❌ {del_w['Prénom']} supprimée !")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📦 Modèles & Billets/Tickets")

st.sidebar.subheader("➕ Créer un Modèle")
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
            st.sidebar.success(f"✅ Modèle '{clean_model}' créé !")
            st.rerun()
        except sqlite3.IntegrityError:
            st.sidebar.warning("⚠️ Ce modèle existe déjà !")

if modeles_list:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎟️ Ajouter Billet/Ticket & Paquet")
    target_model = st.sidebar.selectbox(
        "Modèle concerné", modeles_list, key="sel_target_m"
    )
    t_name_in = st.sidebar.text_input(
        "Nom du Billet / Ticket", value="Billet Bleu", key="t_name_input"
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
                st.sidebar.error(
                    f"❌ Le paquet N°{p_num_in} existe déjà dans ce billet !"
                )
            else:
                conn.execute(
                    "INSERT INTO paquets (modele, ticket, paquet_num, quantite) VALUES (?, ?, ?, ?)",
                    (target_model, clean_ticket, p_num_in, p_qte_in),
                )
                conn.commit()
                st.sidebar.success(
                    f"✅ Paquet N°{p_num_in} ({p_qte_in} pcs) ajouté !"
                )
                st.rerun()
            conn.close()

    st.sidebar.markdown("---")
    del_m_target = st.sidebar.selectbox(
        "Modèle à supprimer", modeles_list, key="del_m_sel"
    )
    if st.sidebar.button("❌ Supprimer CE MODÈLE"):
        conn = get_connection()
        conn.execute("DELETE FROM modeles WHERE nom=?", (del_m_target,))
        conn.execute("DELETE FROM paquets WHERE modele=?", (del_m_target,))
        conn.commit()
        conn.close()
        st.sidebar.success("Modèle supprimé !")
        st.rerun()

# --- MAIN PAGE ---
selected_date = st.date_input("📅 Date du jour", date.today(), format="DD/MM/YYYY")
st.markdown("---")

tab_prod, tab_manque, tab_suivi = st.tabs(
    [
        "⏱️ Saisie de la Production Par Section",
        "⚠️ Enregistrer les manques / pannes",
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
    st.subheader("⏱️ Saisie de la Production par Section Indépendante")

    if not workers:
        st.error("⚠️ Veuillez ajouter des ouvrières dans la barre latérale !")
    elif not modeles_list:
        st.warning("⚠️ Veuillez ajouter des modèles dans la barre latérale !")
    else:
        sec_tabs = st.tabs(["📋 DOS", "📋 DEVANT", "📋 FINITION", "📋 CONTRÔLE"])

        for idx, (title, cat_key) in enumerate(sections_def):
            with sec_tabs[idx]:
                st.markdown(f"### 📍 Section : {title}")

                cat_workers = [w for w in workers if w["Catégorie"] == cat_key]

                if not cat_workers:
                    st.warning(
                        f"⚠️ Aucune ouvrière enregistrée dans la section {title}."
                    )
                else:
                    worker_opts = [
                        f"{w['Prénom']} {w['Nom']} (Obj: {w['Objectif']} pcs/h)"
                        for w in cat_workers
                    ]

                    col_a, col_b = st.columns(2)
                    with col_a:
                        sel_worker_str = st.selectbox(
                            f"Sélectionner l'Ouvrière ({title})",
                            worker_opts,
                            key=f"prod_w_{cat_key}",
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
                            "Sélectionner le Modèle",
                            modeles_list,
                            key=f"prod_cmd_{cat_key}",
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
                                "Sélectionner le Billet / Ticket",
                                tickets_opts,
                                key=f"prod_ticket_{cat_key}",
                            )
                            if tickets_opts
                            else None
                        )

                        if sel_ticket:
                            conn = get_connection()
                            paquets_db = conn.execute(
                                "SELECT paquet_num, quantite FROM paquets WHERE modele=? AND ticket=?",
                                (sel_cmd, sel_ticket),
                            ).fetchall()
                            conn.close()
                            paquet_opts = [
                                f"Paquet N°{p[0]} ({p[1]} pcs)"
                                for p in paquets_db
                            ]
                            if paquet_opts:
                                sel_paquet_str = st.selectbox(
                                    "Sélectionner le Paquet",
                                    paquet_opts,
                                    key=f"prod_paquet_{cat_key}",
                                )
                                chosen_p_idx = paquet_opts.index(
                                    sel_paquet_str
                                )
                                chosen_paquet = {
                                    "paquet_num": paquets_db[chosen_p_idx][0],
                                    "quantite": paquets_db[chosen_p_idx][1],
                                }
                            else:
                                chosen_paquet = {"paquet_num": 1, "quantite": 0}
                        else:
                            chosen_paquet = {"paquet_num": 1, "quantite": 0}
                            st.info("Aucun paquet défini pour ce billet.")

                    conn = get_connection()
                    target_qty = (
                        conn.execute(
                            "SELECT SUM(quantite) FROM paquets WHERE modele=?",
                            (sel_cmd,),
                        ).fetchone()[0]
                        or 0
                    )

                    ctrl_dos_qty = (
                        conn.execute(
                            "SELECT SUM(pieces) FROM production WHERE modele=? AND categorie='controle' AND sous_categorie='Contrôle DOS'",
                            (sel_cmd,),
                        ).fetchone()[0]
                        or 0
                    )
                    ctrl_devant_qty = (
                        conn.execute(
                            "SELECT SUM(pieces) FROM production WHERE modele=? AND categorie='controle' AND sous_categorie='Contrôle DEVANT'",
                            (sel_cmd,),
                        ).fetchone()[0]
                        or 0
                    )
                    conn.close()

                    model_is_finished = (
                        target_qty > 0
                        and ctrl_dos_qty >= target_qty
                        and ctrl_devant_qty >= target_qty
                        and cat_key == "controle"
                    )

                    if model_is_finished:
                        st.error(
                            f"🔒 Le modèle '{sel_cmd}' est déjà totalement validé et sorti (Contrôle DOS + DEVANT 100%) !"
                        )

                    if st.button(
                        f"💾 Enregistrer ce Paquet ({title})",
                        key=f"btn_save_{cat_key}",
                        disabled=model_is_finished,
                    ):
                        if chosen_paquet["quantite"] > 0:
                            p_num = chosen_paquet["paquet_num"]
                            formatted_date_str = selected_date.strftime(
                                "%d/%m/%Y"
                            )

                            conn = get_connection()
                            dup = conn.execute(
                                """SELECT id FROM production WHERE date=? AND nom=? AND prenom=? 
                                            AND modele=? AND ticket=? AND paquet_num=? AND sous_categorie=?""",
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

                            if dup:
                                st.error(
                                    f"❌ ERREUR : L'ouvrière {w_selected_obj['Prénom']} {w_selected_obj['Nom']} a déjà enregistré le Paquet N°{p_num} !"
                                )
                                conn.close()
                            else:
                                pcs = chosen_paquet["quantite"]
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
                                        pcs,
                                        w_selected_obj["Objectif"],
                                    ),
                                )
                                conn.commit()
                                conn.close()
                                st.success(
                                    f"✅ Enregistré le {formatted_date_str} : {w_selected_obj['Prénom']} ({pcs} pcs) !"
                                )
                                st.rerun()
                        else:
                            st.warning("⚠️ Impossible d'enregistrer !")

with tab_manque:
    st.subheader("⚠️ Enregistrer les manques / pannes")
    if not workers:
        st.error("⚠️ Veuillez ajouter des ouvrières !")
    else:
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
            st.info(f"📁 Section : **{sel_cat_m.upper()}**")

            heure_m = st.selectbox(
                "Tranche Horaire", tranches_horaires, key="manque_h"
            )
            type_manque = st.selectbox(
                "Type de Manque", manques_types, key="manque_type"
            )
            duree_panne = st.selectbox(
                "Durée",
                [
                    "30 minutes (0.5h)",
                    "1 heure (1.0h)",
                    "1 heure et demi (1.5h)",
                    "2 heures (2.0h)",
                    "Plus de 2 heures",
                ],
                key="manque_duree",
            )
            remarque_m = st.text_input("Remarque / Détails", key="manque_rem")
            if st.form_submit_button("⚠️ Enregistrer cet Arrêt"):
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
                st.success(
                    f"⚠️ Arrêt enregistré avec succès le {formatted_date_str} !"
                )
                st.rerun()

with tab_suivi:
    st.subheader("📊 Bilan Global & Tableaux Indépendants par Section")

    conn = get_connection()
    df_p = pd.read_sql_query("SELECT * FROM production", conn)
    df_m = pd.read_sql_query("SELECT * FROM manques", conn)
    conn.close()

    # --- TABLEAU SORTIE MODÈLE (VALIDATION CONTRÔLE DOS + DEVANT) ---
    st.markdown("### 📦 Sortie Modèle - Validation Contrôle Final (DOS & DEVANT)")

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

        # استخراج تواريخ التسجيل الفعلية لهذا الموديل
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
                "Date Enregistrement": dates_str,
                "Modèle": m_name,
                "Quantité Prévue": target_qty,
                "Contrôle DOS (pcs)": validated_dos,
                "Contrôle DEVANT (pcs)": validated_devant,
                "Statut Final": status,
            }
        )
    conn.close()

    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)
    st.markdown("---")

    # --- TABLEAUX INDÉPENDANTS POUR CHAQUE SECTION ---
    for title, cat_key in sections_def:
        st.markdown(f"## 📋 Section : {title}")

        col_w, col_prod = st.columns([1, 2])

        with col_w:
            st.markdown(f"**👷‍♀️ Ouvrières ({title})**")
            cat_workers = [w for w in workers if w["Catégorie"] == cat_key]
            if cat_workers:
                st.dataframe(
                    pd.DataFrame(cat_workers)[["Prénom", "Nom", "Objectif"]],
                    use_container_width=True,
                )
            else:
                st.info(f"Aucune ouvrière dans {title}.")

        with col_prod:
            st.markdown(f"**⚙️ Production ({title})**")
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

                    cols_order = [
                        "Date Record",
                        "Modèle",
                        "Nom",
                        "Prénom",
                        "Sous_Catégorie",
                        "Poste",
                        "Heure",
                        "Total Pièces",
                        "Objectif/Heure",
                        "Rendement (%)",
                    ]
                    st.dataframe(
                        df_grouped[cols_order], use_container_width=True
                    )
                else:
                    st.info(f"Aucune production enregistrée pour {title}.")
            else:
                st.info(f"Aucune production enregistrée pour {title}.")

        st.markdown("---")

    if not df_m.empty:
        st.markdown("### ⚠️ Liste des manques / pannes")
        st.dataframe(df_m, use_container_width=True)

    if not df_p.empty or not df_m.empty:
        st.markdown("---")
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("🗑️ Supprimer dernier paquet"):
                conn = get_connection()
                last_id = conn.execute(
                    "SELECT MAX(id) FROM production"
                ).fetchone()[0]
                if last_id:
                    conn.execute(
                        "DELETE FROM production WHERE id=?", (last_id,)
                    )
                    conn.commit()
                conn.close()
                st.rerun()
        with col_del2:
            if st.button("🗑️ Supprimer dernier manque"):
                conn = get_connection()
                last_id = conn.execute(
                    "SELECT MAX(id) FROM manques"
                ).fetchone()[0]
                if last_id:
                    conn.execute("DELETE FROM manques WHERE id=?", (last_id,))
                    conn.commit()
                conn.close()
                st.rerun()
