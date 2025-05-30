"""viz_utils.py – fonctions de visualisation Altair + helpers Streamlit."""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from functools import partial

# palette sobre - bleu / saumon / gris (complétez ou changez à volonté)
_PIE_DOMAIN = ['male', 'female', '?']          # ex. pour le pie Genre
_PIE_RANGE  = ['#4F6EEB', '#F9A875', '#BBBBBB']


def show_scrollable_bar_chart(
    df: pd.DataFrame,
    note: str,
    y_title: str,
    tooltip_label: str,
    height_px: int = 320,
    bar_size: int = 18
) -> None:
    '''Affiche un bar chart vertical scrollable dans Streamlit.'''
    count = df.shape[0]
    chart = (
        alt.Chart(df)
           .transform_calculate(Note=f"'{note}'")
           .mark_bar(size=bar_size)
           .encode(
               x=alt.X('value:Q', title='Nombre d\u2019avocats'),
               y=alt.Y(
                   'name:N',
                   sort='-x',
                   title=y_title,
                   axis=alt.Axis(labelFontSize=12)
               ),
               tooltip=[
                   alt.Tooltip('name:N', title=tooltip_label),
                   alt.Tooltip('value:Q', title='Effectif'),
                   alt.Tooltip('Note:N', title='Note')
               ]
           )
           .properties(height=count * 22, width=400)
    )
    components.html(
        wrap_with_scroll(chart.to_html(), height=height_px - 20),
        height=height_px,
        scrolling=True
    )


def donut_chart(
    df,
    label_col='name',
    value_col='value',
    note='',
    legend_title='',
    height=250,
    inner_radius=50,
    color_domain=None,
    color_range=None,
):
    """
    Crée un diagramme donut (Altair) prêt à pousser dans Streamlit.

    Parameters
    ----------
    df : pd.DataFrame
    label_col : str   # colonne catégorielle
    value_col : str   # colonne numérique
    note : str        # texte commun dans le tooltip
    legend_title : str
    height : int
    inner_radius : int
    color_domain, color_range : list | None  # pour forcer une palette
    """
    scale = (
        alt.Scale(domain=color_domain, range=color_range)
        if color_domain and color_range else alt.Undefined
    )

    return (
        alt.Chart(df)
           .transform_calculate(Note=f"'{note}'")
           .mark_arc(innerRadius=inner_radius, stroke='white', strokeWidth=1)
           .encode(
               theta=alt.Theta(f'{value_col}:Q', title=''),
               color=alt.Color(f'{label_col}:N',
                               legend=alt.Legend(title=legend_title),
                               scale=scale),
               tooltip=[
                   alt.Tooltip(f'{label_col}:N', title=legend_title or label_col.capitalize()),
                   alt.Tooltip(f'{value_col}:Q', title='Effectif'),
                   alt.Tooltip('Note:N', title='Note'),
               ],
           )
           .properties(height=height)
    )


langues_pie     = partial(
    donut_chart,
    note="Répartition des langues étrangères",
    legend_title="Langue",
)

experience_pie  = partial(
    donut_chart,
    note="Répartition par expérience",
    legend_title="Groupe",
)

gender_pie      = partial(
    donut_chart,
    note="Répartition par genre",
    label_col='sex',
    legend_title="Genre",
    color_domain=_PIE_DOMAIN,
    color_range=_PIE_RANGE,
)




def show_specialisation_chart(dfs: pd.DataFrame):
    show_scrollable_bar_chart(dfs,note='Répartition de toutes les spécialisations',y_title='Spécialisation',tooltip_label='Spécialisation')
def show_activites_chart(dfs: pd.DataFrame):
    show_scrollable_bar_chart(dfs,note='Répartition de toutes les Activités',y_title='Activité Dominante',tooltip_label='Activité Dominante')


def wrap_with_scroll(html: str, height: int = 300) -> str:
    """Enrobe le HTML dans une DIV avec scroll."""
    return f"""
    <div style="
        border:1px solid #ddd;
        border-radius:4px;
        padding:8px;
        height:{height}px;
        overflow:auto;
    ">
      {html}
    </div>
    """


def show_flux_entree_chart(
    df: pd.DataFrame,
    note: str = "",
    tooltip_label: str = "Année",
    height_px: int = 350,
    width_px: int = 800,
) -> None:

    base = (
        alt.Chart(df)
           .transform_calculate(Note=f"'{note}'")
           .encode(
               x=alt.X("name:O",
                       title="Année de prestation de serment",
                       axis=alt.Axis(labelAngle=-45)),
               y=alt.Y(
                   "value:Q",
                   title="Nouveaux avocats",
                   scale=alt.Scale(domainMin=0, nice=True)   # <-- min forcé à 0
               ),
               tooltip=[
                   alt.Tooltip("name:O",  title=tooltip_label),
                   alt.Tooltip("value:Q", title="Admissions"),
                   alt.Tooltip("Note:N",  title="Note"),
               ],
           )
    )

    area = base.mark_area(color="#4C78A8", opacity=0.25)
    line = base.mark_line(color="#4C78A8", strokeWidth=2)
    pts  = base.mark_point(color="#4C78A8", size=50)

    chart = (area + line + pts).properties(width=width_px,
                                           height=height_px,
                                           title="Flux d’entrée au barreau").interactive()

    # plus de composant HTML scrollable
    st.altair_chart(chart, use_container_width=False)
