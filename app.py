from pathlib import Path

code = r'''import streamlit as st
import pandas as pd
from datetime import datetime, time
from io import BytesIO

st.set_page_config(page_title="Rendement Atelier", page_icon="🧵", layout="wide")

SECTIONS = ["DOS", "DEVANT", "FINITION", "CONTRÔLE"]
PANNES_DEFAUT = [
    "Panne machine", "Manque de pièces", "Manque de matière",
    "Manque de gabarit", "Absence ouvrière", "Arrêt de production", "Autre panne"
]

def init_state():
    defaults = {
        "ouvriers": {s: [] for s in SECTIONS},
        "productions": [],
        "pannes": [],
        "modeles": [],
        "ticket_keys": set(),
        "worker_counter": 1,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def minutes_travail(debut, fin, pause_debut, pause_fin):
    debut_dt = datetime.combine(datetime.today(), debut)
    fin_dt = datetime.combine(datetime.today(), fin)
    pause_debut_dt = datetime.combine(datetime.today(), pause_debut)
    pause_fin_dt = datetime.combine(datetime.today(), pause_fin)
    total = max(0, (fin_dt - debut_dt).total_seconds() / 60)
    pause = max(0, (min(fin_dt, pause_fin_dt) - max(debut_dt, pause_debut_dt)).total_seconds() / 60)
    return max(0, total - pause)

init_state()
st.title("🧵 Calcul du rendement des ouvriers")
st.caption("Atelier de confection • DOS • DEVANT • FINITION • CONTRÔLE")

with st.sidebar:
    st.header("⏱️ Horaires de travail")
    heure_debut = st.time_input("Début", value=time(7, 30), key="heure_debut")
    heure_fin = st.time_input("Fin", value=time(17, 0), key="heure_fin")
    pause_debut = st.time_input("Début de pause", value=time(12, 0), key="pause_debut")
    pause_fin = st.time_input("Fin de pause", value=time(13, 0), key="pause_fin")
    minutes = minutes_travail(heure_debut, heure_fin, pause_debut, pause_fin)
    st.metric("Temps de travail effectif", f"{int(minutes // 60)} h {int(minutes % 60):02d} min")
    st.caption("Avec les horaires par défaut : 8 h 30 (510 minutes).")

tabs = st.tabs(["👷 Ouvriers & rendement", "🎫 Modèles et tickets", "🛠️ Pannes", "📊 Résumé & export"])

with tabs[0]:
    st.subheader("Listes indépendantes par poste")
    st.info("Ajoute les ouvriers dans le tableau du poste correspondant. Un même nom ne peut pas être ajouté deux fois dans la même liste.")
    for section in SECTIONS:
        with st.expander(f"Tableau {section}", expanded=(section == "DOS")):
            with st.form(f"form_ouvrier_{section}", clear_on_submit=True):
                c1, c2 = st.columns([2, 2])
                nom = c1.text_input("Nom de l'ouvrier/ouvrière", key=f"nom_{section}")
                poste = c2.text_input("Poste / opération", key=f"poste_{section}", placeholder="Ex. Surfilage, plaquage…")
                ajoute = st.form_submit_button(f"➕ Ajouter à {section}")
            if ajoute:
                nom_net = nom.strip()
                if not nom_net:
                    st.error("ERREUR : Saisis le nom de l'ouvrier.")
                elif any(o["nom"].casefold() == nom_net.casefold() for o in st.session_state.ouvriers[section]):
                    st.error(f"ERREUR : {nom_net} existe déjà dans le tableau {section}.")
                else:
                    st.session_state.ouvriers[section].append({"nom": nom_net, "poste": poste.strip() or "Non précisé"})
                    st.success(f"{nom_net} ajouté(e) à {section}.")
                    st.rerun()

            ouvriers = st.session_state.ouvriers[section]
            if ouvriers:
                lignes = []
                for o in ouvriers:
                    prod = sum(int(p["quantite"]) for p in st.session_state.productions
                               if p["section"] == section and p["ouvrier"].casefold() == o["nom"].casefold())
                    rendement_h = prod / (minutes / 60) if minutes > 0 else 0
                    lignes.append({"Nom": o["nom"], "Poste": o["poste"], "Quantité totale": prod,
                                   "Rendement moyen / heure": round(rendement_h, 2)})
                st.dataframe(pd.DataFrame(lignes), use_container_width=True, hide_index=True)
                choix = st.selectbox("Choisir un ouvrier à retirer", ["—"] + [o["nom"] for o in ouvriers],
                                     key=f"retirer_{section}")
                if st.button(f"🗑️ Retirer de {section}", key=f"btn_retirer_{section}"):
                    if choix == "—":
                        st.warning("Choisis un ouvrier.")
                    else:
                        st.session_state.ouvriers[section] = [o for o in ouvriers if o["nom"] != choix]
                        st.success(f"{choix} retiré(e) de la liste. Les productions déjà enregistrées sont conservées.")
                        st.rerun()
            else:
                st.caption("Aucun ouvrier ajouté pour le moment.")

    st.divider()
    st.subheader("Enregistrer une production (paquet)")
    noms_modeles = [m["code"] for m in st.session_state.modeles]
    if not noms_modeles:
        st.warning("Crée d'abord un modèle dans l'onglet « Modèles et tickets ».")
    else:
        with st.form("production_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            modele_prod = c1.selectbox("Modèle", noms_modeles)
            section_prod = c2.selectbox("Tableau / section", SECTIONS)
            ouv_dispo = [o["nom"] for o in st.session_state.ouvriers[section_prod]]
            ouvrier_prod = c3.selectbox("Ouvrier", ["—"] + ouv_dispo)
            c4, c5, c6 = st.columns(3)
            couleur_prod = c4.selectbox("Couleur du ticket", ["Blanc", "Jaune"])
            ticket_prod = c5.text_input("Numéro du ticket / paquet")
            quantite_prod = c6.number_input("Quantité produite (pièces)", min_value=1, value=1, step=1)
            enregistrer_prod = st.form_submit_button("✅ Enregistrer la production")
        if enregistrer_prod:
            ticket = ticket_prod.strip()
            if ouvrier_prod == "—":
                st.error("ERREUR : Choisis un ouvrier inscrit dans cette section.")
            elif not ticket:
                st.error("ERREUR : Saisis le numéro du ticket/paquet.")
            else:
                key = (modele_prod.casefold(), couleur_prod.casefold(), ticket.casefold())
                if key in st.session_state.ticket_keys:
                    st.error(f"ERREUR : Le paquet/ticket « {ticket} » du modèle {modele_prod} ({couleur_prod}) est déjà enregistré. Production non ajoutée.")
                else:
                    st.session_state.ticket_keys.add(key)
                    st.session_state.productions.append({
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "modele": modele_prod, "section": section_prod,
                        "ouvrier": ouvrier_prod, "couleur": couleur_prod,
                        "ticket": ticket, "quantite": int(quantite_prod),
                        "heure": datetime.now().strftime("%H:%M:%S")
                    })
                    st.success(f"Production enregistrée : paquet {ticket}, {ouvrier_prod}, {section_prod}.")
                    st.rerun()

    if st.session_state.productions:
        st.subheader("Historique des productions")
        dfp = pd.DataFrame(st.session_state.productions)
        dfp = dfp.rename(columns={"date":"Date", "modele":"Modèle", "section":"Section", "ouvrier":"Ouvrier",
                                  "couleur":"Ticket", "ticket":"N° paquet", "quantite":"Quantité", "heure":"Heure"})
        st.dataframe(dfp, use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Créer un modèle")
    with st.form("modele_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        code_modele = c1.text_input("Code / nom du modèle", placeholder="Ex. CHEMISE-001")
        quantite_prevue = c2.number_input("Quantité totale prévue (pièces)", min_value=1, value=100, step=1)
        paquets_blancs = c3.number_input("Nombre de paquets tickets blancs", min_value=0, value=0, step=1)
        paquets_jaunes = st.number_input("Nombre de paquets tickets jaunes", min_value=0, value=0, step=1)
        creer_modele = st.form_submit_button("➕ Créer le modèle")
    if creer_modele:
        code = code_modele.strip()
        if not code:
            st.error("Saisis le code du modèle.")
        elif any(m["code"].casefold() == code.casefold() for m in st.session_state.modeles):
            st.error("ERREUR : Ce modèle existe déjà.")
        else:
            st.session_state.modeles.append({"code": code, "quantite_prevue": int(quantite_prevue),
                                             "blancs": int(paquets_blancs), "jaunes": int(paquets_jaunes)})
            st.success(f"Modèle {code} créé.")
            st.rerun()

    if st.session_state.modeles:
        st.subheader("Modèles enregistrés")
        for m in st.session_state.modeles:
            with st.container(border=True):
                deja = sum(p["quantite"] for p in st.session_state.productions if p["modele"] == m["code"])
                tickets_blancs = sum(1 for p in st.session_state.productions if p["modele"] == m["code"] and p["couleur"] == "Blanc")
                tickets_jaunes = sum(1 for p in st.session_state.productions if p["modele"] == m["code"] and p["couleur"] == "Jaune")
                st.write(f"**{m['code']}** — prévu : {m['quantite_prevue']} pièces — produit : {deja} pièces")
                st.progress(min(1.0, deja / m["quantite_prevue"]))
                st.caption(f"Tickets enregistrés : Blanc {tickets_blancs}/{m['blancs']} • Jaune {tickets_jaunes}/{m['jaunes']}")
                if deja >= m["quantite_prevue"]:
                    st.success("MODÈLE TERMINÉ — quantité prévue atteinte.")
                else:
                    st.info(f"Reste {m['quantite_prevue'] - deja} pièce(s) pour atteindre la quantité prévue.")
        st.caption("Le statut « modèle terminé » se base sur la quantité totale prévue. Les quantités de tickets blancs/jaunes servent au suivi des paquets.")

with tabs[2]:
    st.subheader("Enregistrer une panne / un arrêt")
    with st.form("panne_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        type_panne = c1.selectbox("Type de panne", PANNES_DEFAUT + ["Autre"])
        section_panne = c2.selectbox("Section concernée", SECTIONS + ["Atelier entier"])
        c3, c4, c5 = st.columns(3)
        debut_panne = c3.time_input("Heure début", value=time(10, 0))
        fin_panne = c4.time_input("Heure fin", value=time(10, 15))
        detail_panne = c5.text_input("Détail (facultatif)")
        ajouter_panne = st.form_submit_button("➕ Ajouter la panne")
    if ajouter_panne:
        debut_dt = datetime.combine(datetime.today(), debut_panne)
        fin_dt = datetime.combine(datetime.today(), fin_panne)
        if fin_dt <= debut_dt:
            st.error("ERREUR : L'heure de fin doit être après l'heure de début.")
        else:
            duree = int((fin_dt - debut_dt).total_seconds() / 60)
            st.session_state.pannes.append({"Date": datetime.now().strftime("%Y-%m-%d"), "Type de panne": type_panne,
                                             "Section": section_panne, "Début": debut_panne.strftime("%H:%M"),
                                             "Fin": fin_panne.strftime("%H:%M"), "Durée (min)": duree,
                                             "Détail": detail_panne.strip()})
            st.success(f"Panne enregistrée : {duree} minute(s).")
            st.rerun()
    if st.session_state.pannes:
        st.dataframe(pd.DataFrame(st.session_state.pannes), use_container_width=True, hide_index=True)
        if st.button("Effacer l'historique des pannes"):
            st.session_state.pannes = []
            st.rerun()

with tabs[3]:
    st.subheader("Résumé de la journée")
    total_pieces = sum(p["quantite"] for p in st.session_state.productions)
    st.metric("Total pièces enregistrées", total_pieces)
    st.metric("Paquets/tickets uniques", len(st.session_state.productions))
    st.metric("Nombre de pannes", len(st.session_state.pannes))
    if st.session_state.productions:
        df = pd.DataFrame(st.session_state.productions)
        resume = df.groupby(["section", "ouvrier"], as_index=False).agg(
            **{"Quantité totale": ("quantite", "sum"), "Nombre de paquets": ("ticket", "count")}
        )
        resume["Rendement / heure"] = (resume["Quantité totale"] / (minutes / 60)).round(2) if minutes > 0 else 0
        st.dataframe(resume.rename(columns={"section":"Section", "ouvrier":"Ouvrier"}),
                     use_container_width=True, hide_index=True)
        st.download_button("⬇️ Télécharger les productions (CSV)",
                           data=df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="productions_atelier.csv", mime="text/csv")
    else:
        st.info("Aucune production enregistrée. Ajoute des modèles, des ouvriers et des tickets pour commencer.")
    if st.session_state.modeles:
        st.download_button("⬇️ Télécharger les modèles (CSV)",
                           data=pd.DataFrame(st.session_state.modeles).to_csv(index=False).encode("utf-8-sig"),
                           file_name="modeles_atelier.csv", mime="text/csv")

st.divider()
st.caption("Note : le rendement affiché ici correspond aux pièces produites par heure de travail effectif. Pour calculer le rendement en pourcentage, il faut ajouter le temps standard de chaque opération.")
'''
path = Path("/mnt/data/app.py")
print(f"Fichier créé : {path} ({path.stat().st_size} octets)")
