
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Gestion Rendement Atelier",
    page_icon="🧵",
    layout="wide"
)

SECTIONS = ["DOS", "DEVANT", "FINITION", "CONTRÔLE"]
COULEURS = ["Blanc", "Jaune"]

# Initialisation des données
DEFAULTS = {
    "ouvriers": {s: [] for s in SECTIONS},
    "productions": [],
    "pannes": [],
    "types_pannes": [
        "Panne machine",
        "Manque matière",
        "Manque pièce",
        "Manque gabarit",
        "Attente alimentation",
        "Changement modèle",
        "Problème qualité",
        "Absence ouvrière",
        "Autre"
    ],
    "modeles": [],
    "tickets_utilises": []
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if key == "types_pannes" else (
            {k: v.copy() for k, v in value.items()}
            if isinstance(value, dict)
            else list(value) if isinstance(value, list)
            else value
        )


def heures_travail():
    # 07:30 - 17:00 moins pause 12:00 - 13:00
    return 8.5


def nombre_produit(nom_modele, section, ouvrier):
    return sum(
        int(p["Quantité"])
        for p in st.session_state.productions
        if p["Modèle"] == nom_modele
        and p["Section"] == section
        and p["Ouvrier"] == ouvrier
    )


def temps_pannes(nom_modele, section, ouvrier):
    total = 0
    for p in st.session_state.pannes:
        if (
            p["Modèle"] == nom_modele
            and p["Section"] == section
            and (p["Ouvrier"] == ouvrier or p["Ouvrier"] == "Toute la section")
        ):
            total += int(p["Durée (min)"])
    return total


def rendement(nom_modele, section, ouvrier):
    quantite = nombre_produit(nom_modele, section, ouvrier)
    temps_disponible = heures_travail() - temps_pannes(
        nom_modele, section, ouvrier
    ) / 60
    if temps_disponible <= 0:
        return 0
    return round(quantite / temps_disponible, 2)


st.title("🧵 Gestion de production et rendement")
st.caption(
    "Horaire : 07:30–17:00 | Pause déduite : 12:00–13:00 | "
    "Temps normal : 8 h 30"
)

tab_ouvriers, tab_modeles, tab_production, tab_pannes, tab_resume = st.tabs(
    [
        "👥 Ouvriers",
        "📋 Modèles",
        "📦 Production",
        "🔧 Pannes",
        "📊 Résumé"
    ]
)

# =========================================================
# 1. GESTION DES OUVRIERS
# =========================================================
with tab_ouvriers:
    st.header("Gestion des ouvriers")

    section_ouvrier = st.selectbox(
        "Choisir une section",
        SECTIONS,
        key="section_ouvrier"
    )

    with st.form("ajouter_ouvrier", clear_on_submit=True):
        nom = st.text_input("Nom et prénom de l'ouvrier")
        poste = st.text_input("Poste / opération")
        ajouter = st.form_submit_button("➕ Ajouter l'ouvrier")

        if ajouter:
            nom = nom.strip()
            poste = poste.strip()

            if not nom:
                st.error("Saisir le nom de l'ouvrier.")
            elif any(
                o["Nom"].casefold() == nom.casefold()
                for o in st.session_state.ouvriers[section_ouvrier]
            ):
                st.error("Cet ouvrier existe déjà dans cette section.")
            else:
                st.session_state.ouvriers[section_ouvrier].append({
                    "Nom": nom,
                    "Poste": poste if poste else "Non précisé"
                })
                st.success("Ouvrier ajouté avec succès.")
                st.rerun()

    liste = st.session_state.ouvriers[section_ouvrier]

    if liste:
        st.subheader(f"Liste des ouvriers — {section_ouvrier}")
        st.dataframe(
            pd.DataFrame(liste),
            use_container_width=True,
            hide_index=True
        )

        nom_a_supprimer = st.selectbox(
            "Choisir un ouvrier à supprimer",
            [o["Nom"] for o in liste],
            key="ouvrier_a_supprimer"
        )

        if st.button("🗑️ Supprimer l'ouvrier"):
            st.session_state.ouvriers[section_ouvrier] = [
                o for o in liste if o["Nom"] != nom_a_supprimer
            ]
            st.warning(
                "Ouvrier supprimé de la liste. "
                "Les anciens enregistrements de production sont conservés."
            )
            st.rerun()
    else:
        st.info("Aucun ouvrier enregistré dans cette section.")

    st.divider()
    st.subheader("Effectif par section")

    effectifs = [
        {"Section": s, "Nombre d'ouvriers": len(st.session_state.ouvriers[s])}
        for s in SECTIONS
    ]
    st.dataframe(
        pd.DataFrame(effectifs),
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# 2. GESTION DES MODÈLES
# =========================================================
with tab_modeles:
    st.header("Modèles de fabrication")

    with st.form("ajouter_modele", clear_on_submit=True):
        nom_modele = st.text_input("Nom ou référence du modèle")
        quantite_prevue = st.number_input(
            "Quantité totale prévue (pièces)",
            min_value=1,
            value=100,
            step=1
        )
        nb_blanc = st.number_input(
            "Nombre de paquets Blanc prévus",
            min_value=0,
            value=0,
            step=1
        )
        nb_jaune = st.number_input(
            "Nombre de paquets Jaune prévus",
            min_value=0,
            value=0,
            step=1
        )
        ajouter_modele = st.form_submit_button("➕ Créer le modèle")

        if ajouter_modele:
            nom_modele = nom_modele.strip()
            if not nom_modele:
                st.error("Saisir le nom du modèle.")
            elif any(
                m["Modèle"].casefold() == nom_modele.casefold()
                for m in st.session_state.modeles
            ):
                st.error("Ce modèle existe déjà.")
            else:
                st.session_state.modeles.append({
                    "Modèle": nom_modele,
                    "Quantité prévue": int(quantite_prevue),
                    "Paquets Blanc prévus": int(nb_blanc),
                    "Paquets Jaune prévus": int(nb_jaune),
                    "Date création": datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                st.success("Modèle créé.")
                st.rerun()

    if st.session_state.modeles:
        st.subheader("Modèles enregistrés")
        st.dataframe(
            pd.DataFrame(st.session_state.modeles),
            use_container_width=True,
            hide_index=True
        )

        modele_supprimer = st.selectbox(
            "Modèle à supprimer",
            [m["Modèle"] for m in st.session_state.modeles],
            key="modele_supprimer"
        )

        if st.button("🗑️ Supprimer le modèle"):
            st.session_state.modeles = [
                m for m in st.session_state.modeles
                if m["Modèle"] != modele_supprimer
            ]
            st.warning(
                "Le modèle a été retiré de la liste. "
                "Les productions déjà enregistrées ne sont pas supprimées."
            )
            st.rerun()
    else:
        st.info("Crée d'abord un modèle avant d'enregistrer la production.")


# =========================================================
# 3. ENREGISTREMENT DE LA PRODUCTION
# =========================================================
with tab_production:
    st.header("Enregistrer la production")

    if not st.session_state.modeles:
        st.warning("Ajoute d'abord un modèle dans l'onglet Modèles.")
    else:
        noms_modeles = [m["Modèle"] for m in st.session_state.modeles]

        modele = st.selectbox(
            "Modèle",
            noms_modeles,
            key="prod_modele"
        )

        section = st.selectbox(
            "Section",
            SECTIONS,
            key="prod_section"
        )

        ouvriers_section = st.session_state.ouvriers[section]
        noms_ouvriers = [o["Nom"] for o in ouvriers_section]

        if not noms_ouvriers:
            st.warning(
                f"Aucun ouvrier dans {section}. "
                "Ajoute d'abord les ouvriers dans l'onglet Ouvriers."
            )
        else:
            with st.form("form_production", clear_on_submit=True):
                ouvrier = st.selectbox("Ouvrier", noms_ouvriers)
                poste_ouvrier = next(
                    (
                        o["Poste"] for o in ouvriers_section
                        if o["Nom"] == ouvrier
                    ),
                    "Non précisé"
                )

                couleur = st.selectbox("Couleur du ticket", COULEURS)
                numero_paquet = st.text_input(
                    "Numéro du paquet",
                    placeholder="Exemple : 001"
                )
                quantite = st.number_input(
                    "Quantité réalisée (pièces)",
                    min_value=1,
                    value=1,
                    step=1
                )
                enregistrer = st.form_submit_button(
                    "✅ Enregistrer la production"
                )

                if enregistrer:
                    numero_paquet = numero_paquet.strip()

                    if not numero_paquet:
                        st.error("Saisir le numéro du paquet.")
                    else:
                        cle_ticket = (
                            modele.casefold(),
                            section,
                            couleur,
                            numero_paquet.casefold()
                        )

                        if cle_ticket in st.session_state.tickets_utilises:
                            st.error(
                                "Erreur : ce paquet a déjà été enregistré "
                                "pour ce modèle, cette section et cette couleur."
                            )
                        else:
                            st.session_state.tickets_utilises.append(cle_ticket)
                            st.session_state.productions.append({
                                "Date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "Modèle": modele,
                                "Section": section,
                                "Ouvrier": ouvrier,
                                "Poste": poste_ouvrier,
                                "Couleur ticket": couleur,
                                "Numéro paquet": numero_paquet,
                                "Quantité": int(quantite)
                            })
                            st.success("Production enregistrée.")
                            st.rerun()

    st.divider()
    st.subheader("Historique de production")

    if st.session_state.productions:
        df_prod = pd.DataFrame(st.session_state.productions)
        st.dataframe(
            df_prod.sort_index(ascending=False),
            use_container_width=True,
            hide_index=True
        )

        if st.button("🗑️ Effacer tout l'historique de production"):
            st.session_state.productions = []
            st.session_state.tickets_utilises = []
            st.warning("Historique effacé.")
            st.rerun()
    else:
        st.info("Aucune production enregistrée pour le moment.")


# =========================================================
# 4. GESTION DES PANNES
# =========================================================
with tab_pannes:
    st.header("Arrêts et pannes")

    with st.expander("➕ Ajouter un type de panne"):
        with st.form("ajouter_type_panne", clear_on_submit=True):
            nouveau_type = st.text_input("Nouveau type de panne")
            valider_type = st.form_submit_button("Ajouter le type")

            if valider_type:
                nouveau_type = nouveau_type.strip()
                if not nouveau_type:
                    st.error("Saisir le nom du type de panne.")
                elif any(
                    x.casefold() == nouveau_type.casefold()
                    for x in st.session_state.types_pannes
                ):
                    st.error("Ce type de panne existe déjà.")
                else:
                    st.session_state.types_pannes.append(nouveau_type)
                    st.success("Type de panne ajouté.")
                    st.rerun()

    if not st.session_state.modeles:
        st.warning("Crée d'abord un modèle dans l'onglet Modèles.")
    else:
        noms_modeles_panne = [
            m["Modèle"] for m in st.session_state.modeles
        ]

        with st.form("form_panne", clear_on_submit=True):
            modele_panne = st.selectbox(
                "Modèle concerné",
                noms_modeles_panne
            )
            section_panne = st.selectbox(
                "Section concernée",
                SECTIONS,
                key="section_panne"
            )

            choix_ouvriers = [
                "Toute la section"
            ] + [
                o["Nom"]
                for o in st.session_state.ouvriers[section_panne]
            ]

            ouvrier_panne = st.selectbox(
                "Ouvrier concerné",
                choix_ouvriers
            )

            type_panne = st.selectbox(
                "Type de panne",
                st.session_state.types_pannes
            )

            duree_panne = st.number_input(
                "Durée de la panne (minutes)",
                min_value=1,
                value=10,
                step=1
            )

            details_panne = st.text_input("Détails (facultatif)")
            enregistrer_panne = st.form_submit_button("Enregistrer la panne")

            if enregistrer_panne:
                st.session_state.pannes.append({
                    "Date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Modèle": modele_panne,
                    "Section": section_panne,
                    "Ouvrier": ouvrier_panne,
                    "Type de panne": type_panne,
                    "Durée (min)": int(duree_panne),
                    "Détails": details_panne.strip()
                })
                st.success("Panne enregistrée.")
                st.rerun()

    st.divider()
    st.subheader("Historique des pannes")

    if st.session_state.pannes:
        st.dataframe(
            pd.DataFrame(st.session_state.pannes),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Aucune panne enregistrée.")


# =========================================================
# 5. RÉSUMÉ ET RENDEMENT
# =========================================================
with tab_resume:
    st.header("Résumé et rendement")

    if not st.session_state.modeles:
        st.info("Crée un modèle pour consulter son rendement.")
    else:
        modele_resume = st.selectbox(
            "Choisir le modèle à analyser",
            [m["Modèle"] for m in st.session_state.modeles],
            key="resume_modele"
        )

        infos_modele = next(
            m for m in st.session_state.modeles
            if m["Modèle"] == modele_resume
        )

        st.subheader("Rendement par ouvrier")

        lignes = []

        for sec in SECTIONS:
            for o in st.session_state.ouvriers[sec]:
                nom_ouvrier = o["Nom"]
                qte = nombre_produit(modele_resume, sec, nom_ouvrier)
                panne_min = temps_pannes(
                    modele_resume, sec, nom_ouvrier
                )
                temps_net = heures_travail() - panne_min / 60
                rend = round(qte / temps_net, 2) if temps_net > 0 else 0

                lignes.append({
                    "Section": sec,
                    "Ouvrier": nom_ouvrier,
                    "Poste": o["Poste"],
                    "Quantité totale": qte,
                    "Pannes (min)": panne_min,
                    "Heures disponibles": round(max(temps_net, 0), 2),
                    "Rendement (pièces/heure)": rend
                })

        if lignes:
            df_rendement = pd.DataFrame(lignes)
            st.dataframe(
                df_rendement,
                use_container_width=True,
                hide_index=True
            )

            csv_rendement = df_rendement.to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                "⬇️ Télécharger le rendement (CSV)",
                data=csv_rendement,
                file_name=f"rendement_{modele_resume}.csv",
                mime="text/csv"
            )
        else:
            st.warning("Ajoute des ouvriers pour calculer le rendement.")

        st.divider()
        st.subheader("Avancement du modèle")

        quantite_prevue = infos_modele["Quantité prévue"]
        avancement_sections = []

        for sec in SECTIONS:
            total_section = sum(
                int(p["Quantité"])
                for p in st.session_state.productions
                if p["Modèle"] == modele_resume
                and p["Section"] == sec
            )

            pourcentage = min(
                100,
                round(total_section / quantite_prevue * 100, 1)
            )

            avancement_sections.append({
                "Section": sec,
                "Quantité réalisée": total_section,
                "Quantité prévue": quantite_prevue,
                "Avancement (%)": pourcentage
            })

            st.write(
                f"**{sec}** — {total_section} / {quantite_prevue} pièces"
            )
            st.progress(int(pourcentage))

        if all(
            ligne["Quantité réalisée"] >= quantite_prevue
            for ligne in avancement_sections
        ):
            st.success(
                "✅ Modèle terminé dans toutes les sections !"
            )
        else:
            st.info(
                "Le modèle n'est pas encore terminé dans toutes les sections."
            )

        st.divider()
        st.subheader("Alertes")

        alertes = []

        for sec in SECTIONS:
            for o in st.session_state.ouvriers[sec]:
                qte = nombre_produit(
                    modele_resume, sec, o["Nom"]
                )
                if qte == 0:
                    alertes.append(
                        f"{o['Nom']} — {sec} : aucun rendement enregistré."
                    )

        if alertes:
            for alerte in alertes:
                st.warning("⚠️ " + alerte)
        else:
            st.success("Tous les ouvriers ont une production enregistrée.")

        st.divider()
        st.subheader("Télécharger les données")

        if st.session_state.productions:
            df_export = pd.DataFrame(st.session_state.productions)
            st.download_button(
                "⬇️ Télécharger toutes les productions (CSV)",
                data=df_export.to_csv(index=False).encode("utf-8-sig"),
                file_name="productions_atelier.csv",
                mime="text/csv"
            )

        if st.session_state.pannes:
            df_pannes = pd.DataFrame(st.session_state.pannes)
            st.download_button(
                "⬇️ Télécharger les pannes (CSV)",
                data=df_pannes.to_csv(index=False).encode("utf-8-sig"),
                file_name="pannes_atelier.csv",
                mime="text/csv"
            )

st.divider()
st.caption(
    "Application de suivi d'atelier — "
    "Le rendement affiché correspond aux pièces produites par heure disponible."
)
