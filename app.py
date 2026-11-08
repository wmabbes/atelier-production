# -------------------- QUALITE --------------------

elif page == "Contrôle qualité":
    st.title("🔎 Contrôle qualité")

    workers, worker_names = options(
        "SELECT id, nom || ' ' || prenom AS label "
        "FROM workers WHERE actif=1 ORDER BY nom",
        "label"
    )

    modeles, modele_names = options(
        "SELECT id, nom AS label FROM modeles ORDER BY nom",
        "label"
    )

    with st.form("qualite_form"):
        c1, c2, c3 = st.columns(3)

        jour = c1.date_input("Date", date.today())

        modele_name = (
            c2.selectbox("Modèle", modele_names)
            if modele_names else None
        )

        worker_name = c3.selectbox(
            "Ouvrière",
            ["—", *worker_names]
        )

        c1, c2, c3 = st.columns(3)

        categorie = c1.selectbox(
            "Catégorie contrôlée", CATEGORIES
        )

        controlees = c2.number_input(
            "Quantité contrôlée",
            min_value=1,
            value=1
        )

        defectueuses = c3.number_input(
            "Quantité défectueuse",
            min_value=0,
            value=0
        )

        type_defaut = st.text_input("Type de défaut")
        commentaire = st.text_input("Commentaire")

        save = st.form_submit_button("Enregistrer contrôle")

    if save:
        if not modele_names:
            st.error("Ajoutez d'abord un modèle.")

        elif defectueuses > controlees:
            st.error(
                "La quantité défectueuse ne peut pas dépasser "
                "la quantité contrôlée."
            )

        else:
            execute(
                """INSERT INTO qualite
                (jour,modele_id,worker_id,categorie,
                 quantite_controlee,quantite_defectueuse,
                 type_defaut,commentaire)
                VALUES(?,?,?,?,?,?,?,?)""",
                (
                    jour.isoformat(),
                    modeles[modele_name],
                    workers.get(worker_name),
                    categorie,
                    int(controlees),
                    int(defectueuses),
                    type_defaut,
                    commentaire
                )
            )

            st.success("Contrôle qualité enregistré.")
            st.rerun()

    df = query_df("""
        SELECT q.id,q.jour,m.nom AS modele,
        w.nom || ' ' || w.prenom AS ouvriere,
        q.categorie,q.quantite_controlee,
        q.quantite_defectueuse,q.type_defaut,q.commentaire
        FROM qualite q
        LEFT JOIN modeles m ON q.modele_id=m.id
        LEFT JOIN workers w ON q.worker_id=w.id
        ORDER BY q.jour DESC,q.id DESC
    """)

    if not df.empty:
        df["taux_defauts_%"] = (
            df["quantite_defectueuse"]
            / df["quantite_controlee"] * 100
        ).round(1)

        st.dataframe(df, use_container_width=True, hide_index=True)

    else:
        st.info("Aucun contrôle enregistré.")

# -------------------- RAPPORTS --------------------

elif page == "Rapports":
    st.title("📈 Rapports et exportation")

    c1, c2 = st.columns(2)

    debut = c1.date_input(
        "Date début",
        date.today() - timedelta(days=7)
    )

    fin = c2.date_input(
        "Date fin",
        date.today()
    )

    df = query_df("""
        SELECT p.id,p.jour,p.heure_debut,p.heure_fin,
        w.nom || ' ' || w.prenom AS ouvriere,
        ps.nom AS poste,
        m.nom AS modele,
        o.nom AS operation,
        p.categorie,p.quantite,
        p.temps_standard,p.temps_disponible,
        p.ticket,p.paquet,p.notes
        FROM production p
        LEFT JOIN workers w ON p.worker_id=w.id
        LEFT JOIN postes ps ON p.poste_id=ps.id
        LEFT JOIN modeles m ON p.modele_id=m.id
        LEFT JOIN operations o ON p.operation_id=o.id
        WHERE p.jour BETWEEN ? AND ?
        ORDER BY p.jour, p.heure_debut
    """, (debut.isoformat(), fin.isoformat()))

    if not df.empty:

        df["rendement_%"] = df.apply(
            lambda r: round(
                rendement_pct(
                    r["quantite"],
                    r["temps_standard"],
                    r["temps_disponible"]
                ),
                1
            ),
            axis=1
        )

        st.metric(
            "Quantité totale",
            f"{int(df['quantite'].sum()):,}".replace(",", " ")
        )

        st.metric(
            "Rendement moyen",
            f"{df['rendement_%'].mean():.1f}%"
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:
            df.to_excel(
                writer,
                index=False,
                sheet_name="Rapport"
            )

        output.seek(0)

        st.download_button(
            "⬇️ Télécharger Excel",
            data=output.getvalue(),
            file_name="rapport_production.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            "⬇️ Télécharger CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="rapport_production.csv",
            mime="text/csv"
        )

    else:
        st.info("Aucune production pour cette période.")

# -------------------- PARAMETRES --------------------

elif page == "Paramètres":
    st.title("⚙️ Paramètres et formules")

    st.subheader("Formule de rendement")

    st.latex(
        r"Rendement(\%) = "
        r"\frac{Quantité\ réelle \times Temps\ standard\ (sec)}"
        r"{Temps\ disponible\ (min) \times 60}\times 100"
    )

    st.write(
        "Le temps disponible est calculé à partir de l'heure "
        "début et de l'heure fin, en retirant la pause 12:00–13:00."
    )

    st.info(
        "Le temps standard doit être en secondes par pièce. "
        "Pour le chronométrage, mesurez plusieurs pièces puis "
        "divisez le temps total par le nombre de pièces."
    )

    st.subheader("Sauvegarde")

    st.warning(
        "La base de données est le fichier "
        "atelier_production.db dans le même dossier que app.py. "
        "Faites-en une copie régulièrement."
    )

    st.subheader("Tables de données")

    for table in [
        "workers",
        "postes",
        "modeles",
        "operations",
        "production",
        "chronometrage",
        "paquets",
        "manques",
        "qualite"
    ]:
        count = query_df(
            f"SELECT COUNT(*) AS n FROM {table}"
        ).iloc[0]["n"]

        st.write(
            f"- **{table}** : {int(count)} enregistrement(s)"
        )

st.sidebar.divider()
st.sidebar.caption("Version 1.0 • Atelier Textile")
