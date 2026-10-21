
import streamlit as st
import pandas as pd
from datetime import date, time, datetime, timedelta

st.set_page_config(
    page_title="Rendement Atelier",
    page_icon="🧵",
    layout="wide"
)

SECTIONS = ["DOS", "DEVANT", "FINITION", "CONTRÔLE"]
COULEURS = ["Blanc", "Jaune"]

if "ouvriers" not in st.session_state:
    st.session_state.ouvriers = []
if "modeles" not in st.session_state:
    st.session_state.modeles = []
if "tickets" not in st.session_state:
    st.session_state.tickets = []
if "productions" not in st.session_state:
    st.session_state.productions = []
if "pannes" not in st.session_state:
    st.session_state.pannes = []
if "types_pannes" not in st.session_state:
    st.session_state.types_pannes = [
        "Panne machine",
        "Manque matière",
        "Manque pièce",
        "Manque gabarit",
        "Attente alimentation",
        "Changement modèle",
        "Problème qualité",
        "Absence ouvrière",
        "Autre"
    ]


def heures_effectives(debut, fin):
    """Durée en heures en déduisant la pause 12:00-13:00."""
    d1 = datetime.combine(date.today(), debut)
    d2 = datetime.combine(date.today(), fin)

    if d2 <= d1:
        return 0.0

    duree = (d2 - d1).total_seconds() / 3600

    pause_debut = datetime.combine(date.today(), time(12, 0))
    pause_fin = datetime.combine(date.today(), time(13, 0))

    chevauchement = max(
        0,
        (min(d2, pause_fin) - max(d1, pause_debut)).total_seconds()
    ) / 3600

    return max(0.0, duree - chevauchement)


def quantite_ouvrier(nom, section, modele, jour):
    return sum(
        int(p["Quantité"])
        for p in st.session_state.productions
        if p["Ouvrier"] == nom
        and p["Section"] == section
        and p["Modèle"] == modele
        and p["Date"] == str(jour)
    )


st.title("🧵 Application de rendement — Atelier")
st.caption("Gestion des ouvriers, modèles, tickets et production")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👷 Ouvriers",
    "📋 Modèles & tickets",
    "📦 Production",
    "🔧 Pannes",
    "📊 Rendement"
])

# ---------------------------------------------------------
# 1. OUVRIERS
# ---------------------------------------------------------
with tab1:
    st.header("Ajouter ou supprimer un ouvrier")

    with st.form("form_ouvrier", clear_on_submit=True):
        nom = st.text_input("Nom et prénom")
        section = st.selectbox("Section", SECTIONS)
        poste = st.text_input("Poste / opération")
        rendement_standard = st.number_input(
            "Rendement prévu par heure (pièces)",
            min_value=0.0,
            value=0.0,
            step=1.0
        )
        ajouter = st.form_submit_button("➕ Ajouter ouvrier")

        if ajouter:
            nom = nom.strip()
            if not nom:
                st.error("Saisir le nom de l'ouvrier.")
            elif any(
                o["Nom"].casefold() == nom.casefold()
                and o["Section"] == section
                for o in st.session_state.ouvriers
            ):
                st.error("Cet ouvrier existe déjà dans cette section.")
            else:
                st.session_state.ouvriers.append({
                    "Nom": nom,
                    "Section": section,
                    "Poste": poste.strip() or "Non précisé",
                    "Rendement prévu/h": float(rendement_standard)
                })
                st.success("Ouvrier ajouté.")
                st.rerun()

    if st.session_state.ouvriers:
        st.subheader("Liste des ouvriers")
        st.dataframe(
            pd.DataFrame(st.session_state.ouvriers),
            use_container_width=True,
            hide_index=True
        )

        index_suppr = st.selectbox(
            "Choisir l'ouvrier à supprimer",
            range(len(st.session_state.ouvriers)),
            format_func=lambda i: (
                f'{st.session_state.ouvriers[i]["Nom"]} — '
                f'{st.session_state.ouvriers[i]["Section"]}'
            )
        )

        if st.button("🗑️ Supprimer ouvrier"):
            st.session_state.ouvriers.pop(index_suppr)
            st.rerun()
    else:
        st.info("Aucun ouvrier. Ajoute le premier ouvrier ci-dessus.")

# ---------------------------------------------------------
# 2. MODÈLES ET TICKETS
# ---------------------------------------------------------
with tab2:
    st.header("Gestion des modèles")

    with st.form("form_modele", clear_on_submit=True):
        nom_modele = st.text_input("Nom / référence du modèle")
        quantite_prevue = st.number_input(
            "Quantité prévue du modèle",
            min_value=1,
            value=100,
            step=1
        )
        ajouter_modele = st.form_submit_button("➕ Ajouter modèle")

        if ajouter_modele:
            nom_modele = nom_modele.strip()
            if not nom_modele:
                st.error("Saisir le nom du modèle.")
            elif any(
                m["Nom"].casefold() == nom_modele.casefold()
                for m in st.session_state.modeles
            ):
                st.error("Ce modèle existe déjà.")
            else:
                st.session_state.modeles.append({
                    "Nom": nom_modele,
                    "Quantité prévue": int(quantite_prevue)
                })
                st.success("Modèle ajouté.")
                st.rerun()

    if st.session_state.modeles:
        st.dataframe(
            pd.DataFrame(st.session_state.modeles),
            use_container_width=True,
            hide_index=True
        )

        choix_modele_suppr = st.selectbox(
            "Modèle à supprimer",
            [m["Nom"] for m in st.session_state.modeles],
            key="choix_modele_suppr"
        )

        if st.button("🗑️ Supprimer modèle"):
            st.session_state.modeles = [
                m for m in st.session_state.modeles
                if m["Nom"] != choix_modele_suppr
            ]
            st.rerun()

    st.divider()
    st.subheader("Ajouter les tickets de chaque modèle")

    if st.session_state.modeles:
        noms_modeles = [m["Nom"] for m in st.session_state.modeles]

        with st.form("form_ticket", clear_on_submit=True):
            modele_ticket = st.selectbox("Modèle du ticket", noms_modeles)
            couleur_ticket = st.selectbox("Couleur", COULEURS)
            numero_ticket = st.text_input(
                "Numéro du paquet / ticket",
                placeholder="Exemple : 001"
            )
            quantite_ticket = st.number_input(
                "Quantité de pièces dans ce paquet",
                min_value=1,
                value=10,
                step=1
            )
            ajouter_ticket = st.form_submit_button("➕ Ajouter ticket")

            if ajouter_ticket:
                numero_ticket = numero_ticket.strip()
                deja_present = any(
                    t["Modèle"] == modele_ticket
                    and t["Couleur"] == couleur_ticket
                    and t["Numéro"] == numero_ticket
                    for t in st.session_state.tickets
                )

                if not numero_ticket:
                    st.error("Saisir le numéro du ticket.")
                elif deja_present:
                    st.error("Ce ticket existe déjà pour ce modèle et cette couleur.")
                else:
                    st.session_state.tickets.append({
                        "Modèle": modele_ticket,
                        "Couleur": couleur_ticket,
                        "Numéro": numero_ticket,
                        "Quantité prévue": int(quantite_ticket)
                    })
                    st.success("Ticket ajouté.")
                    st.rerun()

    if st.session_state.tickets:
        st.subheader("Liste des tickets")
        st.dataframe(
            pd.DataFrame(st.session_state.tickets),
            use_container_width=True,
            hide_index=True
        )

        choix_ticket_suppr = st.selectbox(
            "Ticket à supprimer",
            range(len(st.session_state.tickets)),
            format_func=lambda i: (
                f'{st.session_state.tickets[i]["Modèle"]} — '
                f'{st.session_state.tickets[i]["Couleur"]} — '
                f'{st.session_state.tickets[i]["Numéro"]}'
            )
        )

        if st.button("🗑️ Supprimer ticket"):
            st.session_state.tickets.pop(choix_ticket_suppr)
            st.rerun()

# ---------------------------------------------------------
# 3. PRODUCTION
# ---------------------------------------------------------
with tab3:
    st.header("Saisie de la production")

    if not st.session_state.ouvriers:
        st.warning("Ajoute d'abord les ouvriers.")
    elif not st.session_state.modeles:
        st.warning("Ajoute d'abord les modèles.")
    elif not st.session_state.tickets:
        st.warning("Ajoute d'abord les tickets des modèles.")
    else:
        jour = st.date_input("📅 Date de production", value=date.today())

        c1, c2 = st.columns(2)
        with c1:
            debut = st.selectbox(
                "Heure de début",
                [time(h, m) for h in range(7, 18) for m in (0, 30)],
                index=1,
                format_func=lambda x: x.strftime("%H:%M")
            )
        with c2:
            fin = st.selectbox(
                "Heure de fin",
                [time(h, m) for h in range(7, 18) for m in (0, 30)],
                index=19,
                format_func=lambda x: x.strftime("%H:%M")
            )

        heures = heures_effectives(debut, fin)
        st.info(
            f"Temps de travail calculé : {heures:.2f} heures "
            "(pause 12:00–13:00 déduite)"
        )

        with st.form("form_production", clear_on_submit=True):
            modele_prod = st.selectbox(
                "Modèle",
                [m["Nom"] for m in st.session_state.modeles]
            )

            tickets_modele = [
                t for t in st.session_state.tickets
                if t["Modèle"] == modele_prod
            ]

            if tickets_modele:
                ticket_index = st.selectbox(
                    "Ticket / paquet",
                    range(len(tickets_modele)),
                    format_func=lambda i: (
                        f'{tickets_modele[i]["Couleur"]} — '
                        f'{tickets_modele[i]["Numéro"]} '
                        f'({tickets_modele[i]["Quantité prévue"]} pièces)'
                    )
                )
            else:
                ticket_index = None
                st.warning("Ce modèle n'a pas encore de ticket.")

            section_prod = st.selectbox("Section", SECTIONS)

            ouvriers_disponibles = [
                o for o in st.session_state.ouvriers
                if o["Section"] == section_prod
            ]

            if ouvriers_disponibles:
                ouvrier_prod = st.selectbox(
                    "Ouvrier",
                    [o["Nom"] for o in ouvriers_disponibles]
                )
            else:
                ouvrier_prod = None
                st.warning("Aucun ouvrier dans cette section.")

            qte_prod = st.number_input(
                "Quantité réellement réalisée",
                min_value=1,
                value=1,
                step=1
            )

            enregistrer_prod = st.form_submit_button("✅ Enregistrer production")

            if enregistrer_prod:
                if not tickets_modele:
                    st.error("Ajoute d'abord un ticket à ce modèle.")
                elif not ouvriers_disponibles:
                    st.error("Ajoute un ouvrier à cette section.")
                else:
                    ticket_choisi = tickets_modele[ticket_index]
                    cle_ticket = (
                        str(jour),
                        modele_prod,
                        section_prod,
                        ticket_choisi["Couleur"],
                        ticket_choisi["Numéro"]
                    )

                    deja_saisi = any(
                        (
                            p["Date"],
                            p["Modèle"],
                            p["Section"],
                            p["Couleur"],
                            p["Ticket"]
                        ) == cle_ticket
                        for p in st.session_state.productions
                    )

                    if deja_saisi:
                        st.error(
                            "Ce ticket est déjà enregistré pour cette date, "
                            "ce modèle et cette section."
                        )
                    elif qte_prod > ticket_choisi["Quantité prévue"]:
                        st.error(
                            "La quantité saisie dépasse la quantité prévue du ticket."
                        )
                    else:
                        st.session_state.productions.append({
                            "Date": str(jour),
                            "Début": debut.strftime("%H:%M"),
                            "Fin": fin.strftime("%H:%M"),
                            "Heures effectives": heures,
                            "Modèle": modele_prod,
                            "Section": section_prod,
                            "Ouvrier": ouvrier_prod,
                            "Couleur": ticket_choisi["Couleur"],
                            "Ticket": ticket_choisi["Numéro"],
                            "Quantité": int(qte_prod)
                        })
                        st.success("Production enregistrée.")
                        st.rerun()

    st.divider()
    st.subheader("Historique")

    if st.session_state.productions:
        st.dataframe(
            pd.DataFrame(st.session_state.productions),
            use_container_width=True,
            hide_index=True
        )

        if st.button("🗑️ Effacer toutes les productions"):
            st.session_state.productions = []
            st.rerun()

# ---------------------------------------------------------
# 4. PANNES
# ---------------------------------------------------------
with tab4:
    st.header("Gestion des pannes")

    with st.form("form_type_panne", clear_on_submit=True):
        nouveau_type = st.text_input("Ajouter un type de panne")
        ajouter_type = st.form_submit_button("➕ Ajouter type de panne")

        if ajouter_type:
            nouveau_type = nouveau_type.strip()
            if nouveau_type and nouveau_type.casefold() not in [
                x.casefold() for x in st.session_state.types_pannes
            ]:
                st.session_state.types_pannes.append(nouveau_type)
                st.success("Type de panne ajouté.")
                st.rerun()
            else:
                st.error("Saisir un nouveau type de panne.")

    if st.session_state.modeles:
        with st.form("form_panne", clear_on_submit=True):
            modele_panne = st.selectbox(
                "Modèle",
                [m["Nom"] for m in st.session_state.modeles],
                key="modele_panne"
            )
            section_panne = st.selectbox(
                "Section",
                SECTIONS,
                key="section_panne"
            )

            ouvriers_panne = [
                o["Nom"] for o in st.session_state.ouvriers
                if o["Section"] == section_panne
            ]
            choix_panne = ["Toute la section"] + ouvriers_panne

            ouvrier_panne = st.selectbox(
                "Ouvrier concerné",
                choix_panne
            )
            type_panne = st.selectbox(
                "Type de panne",
                st.session_state.types_pannes
            )
            date_panne = st.date_input(
                "Date de panne",
                value=date.today()
            )
            duree_panne = st.number_input(
                "Durée en minutes",
                min_value=1,
                value=10,
                step=1
            )
            details_panne = st.text_input("Détails")
            enregistrer_panne = st.form_submit_button("Enregistrer panne")

            if enregistrer_panne:
                st.session_state.pannes.append({
                    "Date": str(date_panne),
                    "Modèle": modele_panne,
                    "Section": section_panne,
                    "Ouvrier": ouvrier_panne,
                    "Type": type_panne,
                    "Durée (min)": int(duree_panne),
                    "Détails": details_panne
                })
                st.success("Panne enregistrée.")
                st.rerun()

    if st.session_state.pannes:
        st.subheader("Historique des pannes")
        st.dataframe(
            pd.DataFrame(st.session_state.pannes),
            use_container_width=True,
            hide_index=True
        )

# ---------------------------------------------------------
# 5. RENDEMENT
# ---------------------------------------------------------
with tab5:
    st.header("Rendement par ouvrier")

    date_rendement = st.date_input(
        "Choisir la date",
        value=date.today(),
        key="date_rendement"
    )

    if st.session_state.productions:
        modeles_rendement = sorted(set(
            p["Modèle"] for p in st.session_state.productions
        ))
        modele_rendement = st.selectbox(
            "Modèle à analyser",
            modeles_rendement
        )

        lignes = []

        for o in st.session_state.ouvriers:
            qte = sum(
                int(p["Quantité"])
                for p in st.session_state.productions
                if p["Date"] == str(date_rendement)
                and p["Modèle"] == modele_rendement
                and p["Ouvrier"] == o["Nom"]
                and p["Section"] == o["Section"]
            )

            heures_ouvrier = sum(
                float(p["Heures effectives"])
                for p in st.session_state.productions
                if p["Date"] == str(date_rendement)
                and p["Modèle"] == modele_rendement
                and p["Ouvrier"] == o["Nom"]
                and p["Section"] == o["Section"]
            )

            # Ne pas additionner les heures si plusieurs tickets
            # ont été saisis sur le même créneau.
            heures_ouvrier = min(heures_ouvrier, 8.5)

            r_h = round(qte / heures_ouvrier, 2) if heures_ouvrier > 0 else 0
            standard = float(o["Rendement prévu/h"])
            r_pct = round(r_h / standard * 100, 1) if standard > 0 else None

            lignes.append({
                "Section": o["Section"],
                "Ouvrier": o["Nom"],
                "Poste": o["Poste"],
                "Quantité": qte,
                "Rendement réel/h": r_h,
                "Rendement prévu/h": standard,
                "Rendement (%)": r_pct if r_pct is not None else "À définir"
            })

        df = pd.DataFrame(lignes)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇️ Télécharger le rendement CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="rendement_atelier.csv",
            mime="text/csv"
        )

        for _, ligne in df.iterrows():
            if ligne["Quantité"] == 0:
                st.warning(
                    f'⚠️ {ligne["Ouvrier"]} ({ligne["Section"]}) '
                    "n'a pas encore de production enregistrée."
                )
            elif isinstance(ligne["Rendement (%)"], (int, float)) \
                    and ligne["Rendement (%)"] < 100:
                st.warning(
                    f'⚠️ {ligne["Ouvrier"]} : rendement inférieur à 100%.'
                )
    else:
        st.info("Enregistre la production pour calculer les rendements.")

st.divider()
st.caption(
    "Attention : les données sont conservées dans la session Streamlit. "
    "Pour un usage quotidien durable, il faudra ajouter une base de données."
)

