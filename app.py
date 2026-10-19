from datetime import date
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Suivi de Production - Atelier", page_icon="🧵", layout="wide"
)

st.markdown(
    "<h1 style='color: #1f77b4; margin-bottom: 0px;'>Suivi de Production</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True
)

if "postes_list" not in st.session_state:
    st.session_state.postes_list = [
        "Surfilage",
        "Piqueuse",
        "Assemblage",
        "Repassage",
        "Finition",
        "Contrôle",
    ]

if "manques_types" not in st.session_state:
    st.session_state.manques_types = [
        "Panne machine (Réparation)",
        "Pièces avec défauts (Pièces rejetées)",
        "Manque garniture / Matière première",
        "Attente Lancement / Modèle",
        "Autre problème technique",
    ]

if "workers" not in st.session_state:
    st.session_state.workers = [
        {"Nom": "Ben Salah", "Prénom": "Mariem", "Catégorie": "dos", "Objectif": 50},
        {"Nom": "TRABELSI", "Prénom": "Sarra", "Catégorie": "devant", "Objectif": 60},
        {"Nom": "GHARBI", "Prénom": "Fatma", "Catégorie": "finition", "Objectif": 80},
        {"Nom": "KHELIFA", "Prénom": "Amani", "Catégorie": "controle", "Objectif": 100},
    ]

if "commandes" not in st.session_state:
    st.session_state.commandes = {
        "Chemise": {
            "Billet Bleu": [
                {"paquet_num": 1, "quantite": 12},
                {"paquet_num": 2, "quantite": 12},
            ],
            "Ticket Noir": [
                {"paquet_num": 1, "quantite": 15},
            ],
        }
    }

if "production_data" not in st.session_state:
    st.session_state.production_data = pd.DataFrame(
        columns=[
            "Date",
            "Nom",
            "Prénom",
            "Catégorie",
            "Poste",
            "Heure",
            "Modèle",
            "Billet / Ticket",
            "N° Paquet",
            "Pièces",
            "Objectif/Heure",
        ]
    )

if "manques_data" not in st.session_state:
    st.session_state.manques_data = pd.DataFrame(
        columns=[
            "Date",
            "Nom",
            "Prénom",
            "Catégorie",
            "Heure",
            "Type de Manque / Panne",
            "Durée",
            "Remarque",
        ]
    )

# --- SIDEBAR ---
st.sidebar.header("👷‍♀️ Paramètres & Ouvrières")

st.sidebar.subheader("➕ Ajouter un Poste")
new_poste_name = st.sidebar.text_input("Nom du Poste", key="input_new_poste")
if st.sidebar.button("➕ Ajouter Poste"):
    clean_poste = new_poste_name.strip()
    if clean_poste:
        exists = any(
            p.lower() == clean_poste.lower()
            for p in st.session_state.postes_list
        )
        if exists:
            st.sidebar.warning(f"⚠️ Le poste '{clean_poste}' existe déjà !")
        else:
            st.session_state.postes_list.append(clean_poste)
            st.sidebar.success(f"✅ Poste '{clean_poste}' ajouté !")
            st.rerun()

st.sidebar.markdown("---")

st.sidebar.subheader("➕ Ajouter un type de Manque")
new_m_type = st.sidebar.text_input("Intitulé du Manque", key="input_new_manque")
if st.sidebar.button("➕ Ajouter Type Manque"):
    clean_manque = new_m_type.strip()
    if clean_manque:
        exists = any(
            m.lower() == clean_manque.lower()
            for m in st.session_state.manques_types
        )
        if exists:
            st.sidebar.warning("⚠️ Ce type de manque existe déjà !")
        else:
            st.session_state.manques_types.append(clean_manque)
            st.sidebar.success("✅ Type ajouté !")
            st.rerun()

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
        exists = any(
            w["Nom"].lower() == clean_nom.lower()
            and w["Prénom"].lower() == clean_prenom.lower()
            for w in st.session_state.workers
        )
        if exists:
            st.sidebar.error(
                f"❌ L'ouvrière '{clean_prenom} {clean_nom}' existe déjà !"
            )
        else:
            st.session_state.workers.append(
                {
                    "Nom": clean_nom,
                    "Prénom": clean_prenom,
                    "Catégorie": w_cat,
                    "Objectif": w_obj,
                }
            )
            st.sidebar.success(
                f"✅ {clean_prenom} {clean_nom} ajoutée dans [{w_cat.upper()}] !"
            )
            st.rerun()

if st.session_state.workers:
    st.sidebar.markdown("---")
    st.sidebar.subheader("❌ Supprimer une ouvrière")
    worker_del_options = [
        f"[{w['Catégorie'].upper()}] {w['Prénom']} {w['Nom']}"
        for w in st.session_state.workers
    ]
    selected_w_to_del = st.sidebar.selectbox(
        "Ouvrière à supprimer", worker_del_options
    )
    if st.sidebar.button("🗑️ Supprimer l'ouvrière"):
        del_idx = worker_del_options.index(selected_w_to_del)
        removed = st.session_state.workers.pop(del_idx)
        st.sidebar.success(f"❌ {removed['Prénom']} supprimée !")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📦 Modèles & Billets/Tickets")

st.sidebar.subheader("➕ Créer un Modèle")
new_model_input = st.sidebar.text_input("Nom du Modèle", key="input_new_model")
if st.sidebar.button("➕ Créer Modèle"):
    clean_model = new_model_input.strip()
    if clean_model:
        if clean_model not in st.session_state.commandes:
            st.session_state.commandes[clean_model] = {}
            st.sidebar.success(f"✅ Modèle '{clean_model}' créé !")
            st.rerun()
        else:
            st.sidebar.warning("⚠️ Ce modèle existe déjà !")

if st.session_state.commandes:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎟️ Ajouter Billet/Ticket & Paquet")
    target_model = st.sidebar.selectbox(
        "Modèle concerné",
        list(st.session_state.commandes.keys()),
        key="sel_target_m",
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
            if clean_ticket not in st.session_state.commandes[target_model]:
                st.session_state.commandes[target_model][clean_ticket] = []

            existing_paquets = [
                p["paquet_num"]
                for p in st.session_state.commandes[target_model][clean_ticket]
            ]
            if p_num_in in existing_paquets:
                st.sidebar.error(
                    f"❌ Le paquet N°{p_num_in} existe déjà dans ce billet !"
                )
            else:
                st.session_state.commandes[target_model][clean_ticket].append(
                    {"paquet_num": p_num_in, "quantite": p_qte_in}
                )
                st.sidebar.success(
                    f"✅ Paquet N°{p_num_in} ({p_qte_in} pcs) ajouté !"
                )
                st.rerun()

    st.sidebar.markdown("---")
    del_m_target = st.sidebar.selectbox(
        "Modèle à supprimer",
        list(st.session_state.commandes.keys()),
        key="del_m_sel",
    )
    if st.sidebar.button("❌ Supprimer CE MODÈLE"):
        del st.session_state.commandes[del_m_target]
        st.sidebar.success("Modèle supprimé !")
        st.rerun()

# --- MAIN PAGE ---
selected_date = st.date_input("📅 Date du jour", date.today(), format="DD/MM/YYYY")
st.markdown("---")

tab_prod, tab_manque, tab_suivi = st.tabs(
    [
        "⏱️ Saisie de la Production",
        "⚠️ Enregistrer les manques / pannes",
        "📊 Suivi, Bilan & Quantités Finies",
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

with tab_prod:
    st.subheader("⏱️ Saisie de la Production")

    if not st.session_state.workers:
        st.error("⚠️ Veuillez ajouter des ouvrières !")
    elif not st.session_state.commandes:
        st.warning("⚠️ Veuillez ajouter des modèles !")
    else:
        worker_opts = [
            f"[{w['Catégorie'].upper()}] {w['Prénom']} {w['Nom']} (Obj: {w['Objectif']} pcs/h)"
            for w in st.session_state.workers
        ]
        cmd_opts = list(st.session_state.commandes.keys())

        col_a, col_b = st.columns(2)
        with col_a:
            sel_worker = st.selectbox(
                "Sélectionner l'Ouvrière", worker_opts, key="prod_w"
            )
            w_selected_obj = st.session_state.workers[worker_opts.index(sel_worker)]
            sel_cat = w_selected_obj["Catégorie"]
            st.info(f"📁 Section attribuée : **{sel_cat.upper()}**")

            sel_poste = st.selectbox(
                "Poste Actuel", st.session_state.postes_list, key="prod_poste"
            )
            heure = st.selectbox(
                "Tranche Horaire", tranches_horaires, key="prod_h"
            )

        with col_b:
            sel_cmd = st.selectbox(
                "Sélectionner le Modèle", cmd_opts, key="prod_cmd"
            )
            tickets_opts = list(st.session_state.commandes[sel_cmd].keys())
            sel_ticket = (
                st.selectbox(
                    "Sélectionner le Billet / Ticket",
                    tickets_opts,
                    key="prod_ticket",
                )
                if tickets_opts
                else None
            )

            if sel_ticket and st.session_state.commandes[sel_cmd][sel_ticket]:
                paquet_list = st.session_state.commandes[sel_cmd][sel_ticket]
                paquet_opts = [
                    f"Paquet N°{p['paquet_num']} ({p['quantite']} pcs)"
                    for p in paquet_list
                ]
                sel_paquet_str = st.selectbox(
                    "Sélectionner le Paquet", paquet_opts, key="prod_paquet"
                )
                chosen_paquet = paquet_list[paquet_opts.index(sel_paquet_str)]
            else:
                chosen_paquet = {"paquet_num": 1, "quantite": 0}
                st.info("Aucun paquet défini pour ce billet.")

        # Vérification si le modèle est entièrement sorti du Contrôle
        df_p_check = st.session_state.production_data
        model_is_finished = False
        if not df_p_check.empty:
            ctrl_qty = df_p_check[
                (df_p_check["Modèle"] == sel_cmd) & (df_p_check["Catégorie"] == "controle")
            ]["Pièces"].sum()
            
            target_qty = sum(
                p["quantite"]
                for t in st.session_state.commandes.get(sel_cmd, {}).values()
                for p in t
            )
            if target_qty > 0 and ctrl_qty >= target_qty and sel_cat == "controle":
                model_is_finished = True

        if model_is_finished:
            st.error(f"🔒 Le modèle '{sel_cmd}' est déjà totalement validé et sorti du CONTRÔLE ! Impossible de le réenregistrer.")

        if st.button("💾 Enregistrer ce Paquet", disabled=model_is_finished):
            if chosen_paquet["quantite"] > 0:
                p_num = chosen_paquet["paquet_num"]
                df_history = st.session_state.production_data

                formatted_date_str = selected_date.strftime("%d/%m/%Y")

                is_duplicate = False
                if not df_history.empty:
                    is_duplicate = (
                        (df_history["Date"] == formatted_date_str)
                        & (df_history["Nom"] == w_selected_obj["Nom"])
                        & (df_history["Prénom"] == w_selected_obj["Prénom"])
                        & (df_history["Modèle"] == sel_cmd)
                        & (df_history["Billet / Ticket"] == sel_ticket)
                        & (df_history["N° Paquet"] == p_num)
                    ).any()

                if is_duplicate:
                    st.error(
                        f"❌ ERREUR : L'ouvrière {w_selected_obj['Prénom']} {w_selected_obj['Nom']} a déjà enregistré le Paquet N°{p_num} de '{sel_cmd}' !"
                    )
                else:
                    pcs = chosen_paquet["quantite"]
                    new_record = {
                        "Date": formatted_date_str,
                        "Nom": w_selected_obj["Nom"],
                        "Prénom": w_selected_obj["Prénom"],
                        "Catégorie": sel_cat,
                        "Poste": sel_poste,
                        "Heure": heure,
                        "Modèle": sel_cmd,
                        "Billet / Ticket": sel_ticket,
                        "N° Paquet": p_num,
                        "Pièces": pcs,
                        "Objectif/Heure": w_selected_obj["Objectif"],
                    }
                    st.session_state.production_data = pd.concat(
                        [
                            st.session_state.production_data,
                            pd.DataFrame([new_record]),
                        ],
                        ignore_index=True,
                    )
                    st.success(
                        f"✅ Enregistré : {w_selected_obj['Prénom']} en [{sel_cat.upper()} - {sel_poste}] ({pcs} pcs) !"
                    )
            else:
                st.warning("⚠️ Impossible d'enregistrer un paquet vide !")

with tab_manque:
    st.subheader("⚠️ Enregistrer les manques / pannes")
    if not st.session_state.workers:
        st.error("⚠️ Veuillez ajouter des ouvrières !")
    else:
        worker_opts_m = [
            f"[{w['Catégorie'].upper()}] {w['Prénom']} {w['Nom']}" for w in st.session_state.workers
        ]
        with st.form("form_manque"):
            sel_worker_m = st.selectbox(
                "Ouvrière concernée", worker_opts_m, key="manque_w"
            )
            w_obj_m = st.session_state.workers[worker_opts_m.index(sel_worker_m)]
            sel_cat_m = w_obj_m["Catégorie"]
            st.info(f"📁 Section : **{sel_cat_m.upper()}**")

            heure_m = st.selectbox(
                "Tranche Horaire", tranches_horaires, key="manque_h"
            )
            type_manque = st.selectbox(
                "Type de Manque", st.session_state.manques_types, key="manque_type"
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
                new_m_record = {
                    "Date": formatted_date_str,
                    "Nom": w_obj_m["Nom"],
                    "Prénom": w_obj_m["Prénom"],
                    "Catégorie": sel_cat_m,
                    "Heure": heure_m,
                    "Type de Manque / Panne": type_manque,
                    "Durée": duree_panne,
                    "Remarque": remarque_m,
                }
                st.session_state.manques_data = pd.concat(
                    [
                        st.session_state.manques_data,
                        pd.DataFrame([new_m_record]),
                    ],
                    ignore_index=True,
                )
                st.success("⚠️ Arrêt enregistré avec succès !")

with tab_suivi:
    st.subheader(
        "📊 Bilan Global & Suivi Indépendant par Section (Dos, Devant, Finition, Contrôle)"
    )

    total_model_target = {}
    for mod_name, tickets_dict in st.session_state.commandes.items():
        m_total = 0
        for t_name, paquets_list in tickets_dict.items():
            for p in paquets_list:
                m_total += p["quantite"]
        total_model_target[mod_name] = m_total

    df_p = st.session_state.production_data.copy()

    # --- TAB SORTIE MODÈLE (DEPUIS CONTRÔLE UNIQUEMENT) ---
    st.markdown("### 📦 Sortie Modèle (Validé uniquement depuis le CONTRÔLE)")
    df_controle = df_p[df_p["Catégorie"] == "controle"] if not df_p.empty else pd.DataFrame()

    summary_rows = []
    formatted_date_str = selected_date.strftime("%d/%m/%Y")
    for m_name, target_qty in total_model_target.items():
        validated_pcs = (
            df_controle[df_controle["Modèle"] == m_name]["Pièces"].sum()
            if not df_controle.empty
            else 0
        )
        
        is_finished = validated_pcs >= target_qty and target_qty > 0
        status = "✅ Sorti du Contrôle (Terminé)" if is_finished else "⏳ En cours..."
        
        progress_pct = (
            round((validated_pcs / target_qty) * 100, 2)
            if target_qty > 0
            else 0
        )

        summary_rows.append(
            {
                "Date": formatted_date_str,
                "Modèle": m_name,
                "Quantité Total Prévue": target_qty,
                "Quantité Sortie (Contrôle)": validated_pcs,
                "Progression (%)": progress_pct,
                "Statut Final": status,
            }
        )
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)
    st.markdown("---")

    # --- SECTIONS INDÉPENDANTES (DOS, DEVANT, FINITION, CONTRÔLE) ---
    sections = [
        ("DOS", "dos"),
        ("DEVANT", "devant"),
        ("FINITION", "finition"),
        ("CONTRÔLE", "controle"),
    ]

    for title, cat_key in sections:
        with st.expander(f"📌 Section : {title}", expanded=True):
            col_sec1, col_sec2 = st.columns([1, 2])

            # Liste des ouvrières du قسم
            with col_sec1:
                st.markdown(f"**👷‍♀️ Worker List - {title}**")
                cat_workers = [
                    w for w in st.session_state.workers if w["Catégorie"] == cat_key
                ]
                if cat_workers:
                    st.dataframe(
                        pd.DataFrame(cat_workers)[["Prénom", "Nom", "Objectif"]],
                        use_container_width=True,
                    )
                else:
                    st.info(f"Aucune ouvrière dans {title}")

            # Production du قسم
            with col_sec2:
                st.markdown(f"**⚙️ Tableau de Production - {title}**")
                if not df_p.empty:
                    df_cat = df_p[df_p["Catégorie"] == cat_key]
                    if not df_cat.empty:
                        df_grouped = (
                            df_cat.groupby(
                                [
                                    "Date",
                                    "Modèle",
                                    "Nom",
                                    "Prénom",
                                    "Poste",
                                    "Heure",
                                    "Objectif/Heure",
                                ],
                                as_index=False,
                            )
                            .agg({"Pièces": "sum"})
                            .rename(columns={"Pièces": "Total Pièces"})
                        )
                        df_grouped["Rendement (%)"] = (
                            (df_grouped["Total Pièces"] / df_grouped["Objectif/Heure"]) * 100
                        ).round(2)

                        cols_order = [
                            "Date",
                            "Modèle",
                            "Nom",
                            "Prénom",
                            "Poste",
                            "Heure",
                            "Total Pièces",
                            "Objectif/Heure",
                            "Rendement (%)",
                        ]
                        st.dataframe(df_grouped[cols_order], use_container_width=True)
                    else:
                        st.info(f"Aucune production enregistrée pour {title}")
                else:
                    st.info(f"Aucune production enregistrée pour {title}")

    if not st.session_state.manques_data.empty:
        st.markdown("---")
        st.markdown("### ⚠️ Liste des manques / pannes")
        st.dataframe(st.session_state.manques_data, use_container_width=True)

    if not df_p.empty or not st.session_state.manques_data.empty:
        st.markdown("---")
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("🗑️ Supprimer dernier paquet"):
                if not st.session_state.production_data.empty:
                    st.session_state.production_data = (
                        st.session_state.production_data.iloc[:-1]
                    )
                    st.rerun()
        with col_del2:
            if st.button("🗑️ Supprimer dernier manque"):
                if not st.session_state.manques_data.empty:
                    st.session_state.manques_data = (
                        st.session_state.manques_data.iloc[:-1]
                    )
                    st.rerun()
