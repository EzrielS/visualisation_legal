import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import streamlit.components.v1 as components
import numpy as np 

from data_utils import compute_statistics, gini, process_data, prepare_chart_data
from viz import show_specialisation_chart, show_activites_chart, langues_pie, experience_pie, gender_pie

# ------------------------------
# Fonctions utilitaires
# ------------------------------



# ------------------------------
# Application Streamlit
# ------------------------------

def main():
    st.set_page_config(layout="wide", page_title="Annuaire des Avocats")
    st.title("Annuaire des Avocats")
    st.markdown("Analyse avancée des données du barreau français")

    # Sidebar
    uploaded = st.sidebar.file_uploader(
        "📁 Choisir un fichier Excel / CSV", type=['xlsx', 'xls', 'csv']
    )
    if not uploaded:
        st.sidebar.info("Importez vos données pour démarrer.")
        return

    # Lecture
    try:
        if uploaded.name.lower().endswith('.csv'):
            raw = pd.read_csv(uploaded)
        else:
            raw = pd.read_excel(uploaded)
    except Exception as e:
        st.sidebar.error(f"Erreur lecture fichier : {e}")
        return

    df = process_data(raw)


    # Filtre barreau
    barreaux = ['Tous'] + sorted(df['barreau'].dropna().unique().tolist())
    sel = st.sidebar.selectbox("Filtrer par Barreau", barreaux)
    if sel != 'Tous':
        df = df[df['barreau'] == sel]

    # Statistiques
    stats = compute_statistics(df)

    # KPI principaux
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Avocats", stats['total'])
    k2.metric(
     label="Diversité Linguistique (%)",
     value=stats['diversite_linguistique'],
     help="Pourcentage d’avocats qui maîtrisent au moins une langue étrangère."
    )
    k3.metric(
     label="Taux Expertise (%)",
     value=stats['taux_expertise'],
     help="Pourcentage d’avocats avec plus de 15 ans d’expérience – reflet du niveau d’expertise global."
    )
    k4.metric("Multi-spécialistes (%)", stats['diversite_specialisation'])

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Expérience Moyenne (ans)", stats['avg_exp'])
    k6.metric(
         label="Concentration Géo (%)",
         value=stats['concentration_geo'],
         help="Indice de Herfindahl régional : plus il est élevé, plus la répartition est concentrée dans quelques villes."
     )
    k7.metric("Taux Renouvellement (%)", stats['taux_renouvellement'])
    k8.metric("Villes Actives", stats['unique_cities'])

    k9, k10, k11, k12 = st.columns(4)
    k9.metric("Sans spécialisation (%)", stats['pct_no_specialisation'])
    k10.metric("Monolingues (%)", stats['pct_monolingues'])
    k11.metric("Quasi-retraités (%)", stats['pct_pre_retraite'])
    k12.metric("Gini Barreaux", stats['gini_barreaux'])

    # un peu plus bas, dans les Insights ou en tableau :
    st.write(f"- Shannon spés.: {stats['shannon_specialisations']}")
    st.write(f"- % Top 3 Barreaux: {stats['pct_top3_barreaux']}%")
    st.write(f"- % Anciens (>30 ans exp): {stats['pct_anciens']}%")


    st.markdown("---")
    st.subheader("Indicateurs de Performance")
    p1, p2, p3, p4 = st.columns(4)
    p1.write(f"**Avocats Multilingues**\n{stats['multilingues']}")
    p2.write(f"**Multi-spécialistes**\n{stats['multispecialistes']}")
    p3.write(f"**Experts Confirmés (15+ ans)**\n{stats['experts_confirmes']}")
    p4.write(f"**Jeunes Diplômés (≤5 ans)**\n{stats['jeunes_diplomes']}")


    # Préparer données chart
    charts = prepare_chart_data(df)

    # Charts interactifs
    st.subheader("Visualisations")
    # Row 1: Barreaux & Langues
    c1, c2 = st.columns(2)
    with c1:
        dfb = charts['barreau']
        bar = (
            alt.Chart(dfb)
               .transform_calculate(Note="'Top 8 barreaux'")
               .mark_bar()
               .encode(
                   x=alt.X('name:N', sort='-y', title='Barreau'),
                   y=alt.Y('value:Q', title='Nombre'),
                   tooltip=[
                       alt.Tooltip('name:N', title='Barreau'),
                       alt.Tooltip('value:Q', title='Effectif'),
                       alt.Tooltip('Note:N', title='Note')
                   ]
               )
               .properties(height=250)
        )
        st.altair_chart(bar, use_container_width=True)

    with c2:
        dfl = charts['langues']
        st.altair_chart(langues_pie(dfl), use_container_width=True)

    # Row 2: Spécialisations & Expérience
    c3, c4 = st.columns(2)
    with c3:
        dfs = charts['specialisations']
        show_specialisation_chart(dfs)

    with c4:
        dfe = charts['experience']
        st.altair_chart(experience_pie(dfe),  use_container_width=True)
    c5, c6 = st.columns(2)
    with c5:
        dfs = charts['activites_dominantes']
        show_activites_chart(dfs)
    with c6:
        st.altair_chart(gender_pie(charts['gender']), use_container_width=True)
    # Analyse géographique
    st.markdown("---")
    st.subheader("Analyse Géographique Détaillée")
    gv, gr = st.columns([1, 1])
    with gv:
        top_villes = df['ville'].value_counts().head(5)
        st.table(
            top_villes.reset_index()
                      .rename(columns={'index': 'Ville', 'ville': 'Ville'})
        )
    with gr:
        regions = df['code_postal'].dropna().astype(str).str[:5].value_counts().head(10)
        st.table(
            regions.reset_index()
                   .rename(columns={'index': 'Région', 'code_postal': 'Code Postal'})
        )

    # Insights & Tendances
    st.markdown("---")
    st.subheader("Insights & Tendances")
    st.markdown(f"""
    - **Diversification** : {stats['diversite_specialisation']} % ont plusieurs spécialisations.  
    - **Internationalisation** : {stats['diversite_linguistique']} % maîtrisent au moins une langue étrangère.  
    - **Renouvellement** : {stats['taux_renouvellement']} % sont de jeunes diplômés (≤ 5 ans).
    """)
    with st.expander("🗒️ Aperçu des données brutes", expanded=True):
        st.dataframe(raw, height=300)


if __name__ == "__main__":
    main()
