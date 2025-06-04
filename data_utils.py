import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st  # uniquement pour le cache
from unidecode import unidecode
import gender_guesser.detector as gender

det = gender.Detector()
bads = ['andy', 'unknown']
def genderize(name):
    gender = det.get_gender(name)
    if gender in bads:
        gender = det.get_gender(unidecode(name))
    if gender in bads:
        gender = det.get_gender(name.split('-')[0])
    if gender in bads:
        gender = det.get_gender(unidecode(name.split('-')[0]))
    if gender in bads:
        return '?'
    return gender.replace('mostly_male', 'male').replace('mostly_female', 'female')


def add_gender(df):
    "Ajoute une colonne ‘gender’ (male / female / ?)"
    print('DEBUG')
    df = df.copy()
    df['gender'] = df.nom_complet.apply(lambda x: x.split()[0]).apply(genderize)
    return df



def compute_statistics(df: pd.DataFrame) -> dict:
    total = len(df)
    stats = {}
    avg_exp = df['annees_experience'].mean() if total else 0
    unique_barreaux = df['barreau'].nunique()
    unique_cities = df['ville'].nunique()

    multilingues = df[df['langues'].map(len) > 0].shape[0]
    multispecialistes = df[df['specialisations'].map(len) > 1].shape[0]
    experts_confirmes = df[df['annees_experience'] > 15].shape[0]
    jeunes_diplomes = df[df['annees_experience'] <= 5].shape[0]

    diversite_linguistique = (multilingues / total * 100) if total else 0
    diversite_specialisation = (multispecialistes / total * 100) if total else 0
    taux_expertise = (experts_confirmes / total * 100) if total else 0
    taux_renouvellement = (jeunes_diplomes / total * 100) if total else 0

    # Indice Herfindahl (concentration géographique)
    counts = df['ville'].value_counts()
    herf = (counts.div(total) ** 2).sum() * 100 if total else 0

    # --- nouvelles métriques ---
    # % sans spécialisation
    no_spec = df[df['specialisations'].map(len) == 0].shape[0]
    stats['pct_no_specialisation'] = round(no_spec / total * 100, 1)

    # % monolingues
    mono = df[df['langues'].map(len) == 0].shape[0]
    stats['pct_monolingues'] = round(mono / total * 100, 1)

    # % quasi-retraités (exp >= 35 ans)
    near_ret = df[df['annees_experience'] >= 35].shape[0]
    stats['pct_pre_retraite'] = round(near_ret / total * 100, 1)

    # Indice Shannon sur les spécialisations
    spec_counts = df.explode('specialisations')['specialisations'].value_counts()
    p = spec_counts / spec_counts.sum() if spec_counts.sum() else pd.Series()
    stats['shannon_specialisations'] = round(-(p * np.log2(p)).sum(), 2)

    # Indice Gini sur la taille des barreaux
    bar_counts = df['barreau'].value_counts().values
    stats['gini_barreaux'] = round(gini(bar_counts), 3)

    # % dans les Top 3 barreaux
    top3 = df['barreau'].value_counts().head(3).sum()
    stats['pct_top3_barreaux'] = round(top3 / total * 100, 1)

    # % « anciens » (> 30 ans d’expérience)
    anciens = df[df['annees_experience'] > 30].shape[0]
    stats['pct_anciens'] = round(anciens / total * 100, 1)


    stats.update({
            'total': total,
            'avg_exp': round(avg_exp, 1),
            'unique_barreaux': unique_barreaux,
            'unique_cities': unique_cities,
            'diversite_linguistique': round(diversite_linguistique, 1),
            'diversite_specialisation': round(diversite_specialisation, 1),
            'taux_expertise': round(taux_expertise, 1),
            'taux_renouvellement': round(taux_renouvellement, 1),
            'concentration_geo': round(herf, 1),
            'multilingues': multilingues,
            'multispecialistes': multispecialistes,
            'experts_confirmes': experts_confirmes,
            'jeunes_diplomes': jeunes_diplomes,
        })
    return stats



def gini(array: np.ndarray) -> float:
    """Indice de Gini pour un vecteur d’effectifs."""
    x = np.sort(array)
    n = len(x)
    if n == 0 or x.mean() == 0:
        return 0.0
    # formule : ∑|xi - xj| / (2 n² μ)
    diffs = np.abs(x.reshape(-1,1) - x.reshape(1,-1)).sum()
    return diffs / (2 * n**2 * x.mean())


@st.cache_data
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Langues (exclure 'Français')
    def parse_langues(val):
        if isinstance(val, list):
            langs = val
        elif isinstance(val, str):
            langs = [l.strip()
                     for l in val.replace("[", "")
                                  .replace("]", "")
                                  .replace("'", "")
                                  .split(',')
                     ] if val else []
        else:
            langs = []
        return [l for l in langs if l and l.lower() != 'français']
    df['langues'] = df['langues'].apply(parse_langues)

    # Spécialisations
    specs_cols = ['specialisations_1', 'specialisations_2', 'specialisations_3']
    df['specialisations'] = df[specs_cols] \
        .apply(lambda row: [s for s in row if isinstance(s, str) and s.strip()],
               axis=1)

    # Activités dominantes
    acts_cols = ['activite_dominante_1', 'activite_dominante_2', 'activite_dominante_3']
    df['activites_dominantes'] = df[acts_cols] \
        .apply(lambda row: [a for a in row if isinstance(a, str) and a.strip()],
               axis=1)

    # Années d'expérience
    current_year = datetime.now().year
    def compute_experience(date_str):
        try:
            return current_year - pd.to_datetime(date_str).year
        except:
            return 0
    df['annees_experience'] = df['date_prestation_serment'] \
        .apply(compute_experience)

    df = add_gender(df)
    df = add_age_columns(df)
    return df



@st.cache_data
def prepare_chart_data(df: pd.DataFrame) -> dict:
    # Barreau (top 8)
    bc = df['barreau'].value_counts().head(8)
    barreau = pd.DataFrame({'name': bc.index, 'value': bc.values})

    # Langues (top 8)
    le = df.explode('langues')
    lc = le['langues'].value_counts().head(8)
    langues = pd.DataFrame({'name': lc.index, 'value': lc.values})

    # Spécialisations (top 8)
    se = df.explode('specialisations')
    sc = se['specialisations'].value_counts()#.head(8)
    specialisations = pd.DataFrame({'name': sc.index, 'value': sc.values})

    # Activites Dominantes (top 8)
    ad = df.explode('activites_dominantes')
    adv = ad['activites_dominantes'].value_counts()#.head(8)
    activites_dominantes = pd.DataFrame({'name': adv.index, 'value': adv.values})

    # Expérience
    max_exp = df['annees_experience'].max() or 0
    bins = [0, 5, 15, 25, max_exp + 1]
    labels = ['Débutants (0–5)', 'Confirmés (6–15)',
              'Experts (16–25)', 'Séniors (25+)']
    tmp = df.copy()
    tmp['exp_range'] = pd.cut(tmp['annees_experience'],
                              bins=bins,
                              labels=labels,
                              right=False)
    ec = tmp['exp_range'].value_counts().reindex(labels, fill_value=0)
    experience = pd.DataFrame({'name': ec.index, 'value': ec.values})

    gender = df['gender'].value_counts().rename_axis('sex').reset_index(name='value')

    flux_entree = prepare_flux_entree_data(df)
    return {
        'barreau': barreau,
        'langues': langues,
        'specialisations': specialisations,
        'activites_dominantes': activites_dominantes,
        'experience': experience,
        'gender': gender,
        'flux_entree': flux_entree
    }



############################################
# data_utils.py  (à la suite de process_data)

def add_age_columns(df, today=None):
    """Ajoute seniority, age estimé et tranche d'âge."""
    if today is None:
        today = pd.Timestamp.today().normalize()
    df = df.copy()
    df['date_prestation_serment'] = pd.to_datetime(
        df['date_prestation_serment'], errors='coerce')
    df['seniority_years'] = (
        (today - df['date_prestation_serment']).dt.days / 365.25
    )
    df['age_est'] = df['seniority_years'] + 27        # 27 ans ≈ âge moyen du serment
    bins = [0, 30, 40, 50, 60, np.inf]
    labels = ['<30', '30-39', '40-49', '50-59', '60+']
    df['age_bracket'] = pd.cut(df['age_est'], bins=bins, labels=labels)
    df['in_structure'] = (df['structure_reference'].notna() & df['structure_reference'].str.strip().ne('')) | (df.structure_reference.apply(lambda x: x.split()[0] == 'Individuel' if type(x) == str else False))
    df['is_specialised'] = df[['specialisations_1','specialisations_2','specialisations_3']].notna().any(axis=1)
    return df


def compute_age_insights(df):
    """Retourne deux tables prêtes à afficher (structure & spé)."""
    # on ignore les 'NaN' pour éviter de biaiser les %.
    base = df.dropna(subset=['age_bracket'])
    # Structure
    struct = (base.groupby(['age_bracket','in_structure'])
                   .size().unstack(fill_value=0)
                   .rename(columns={False: 'Solo', True: 'Structure'}))
    struct = struct.reindex(columns=['Solo', 'Structure'], fill_value=0)
    struct['% Structure'] = (struct['Structure']/struct.sum(axis=1)*100).round(1)
    # Spécialisation
    spec = (base.groupby(['age_bracket','is_specialised'])
                  .size().unstack(fill_value=0)
                  .rename(columns={False: 'Non spé', True: 'Spécialisés'}))
    spec = spec.reindex(columns=['Non spé', 'Spécialisés'], fill_value=0)
    spec['% Spécialisés'] = (spec['Spécialisés']/spec.sum(axis=1)*100).round(1)
    return struct, spec



##########################################
def prepare_flux_entree_data(df: pd.DataFrame,
                             col_date="date_prestation_serment",
                             year_min: int = 1990,
                             year_max: int = 2024) -> pd.DataFrame:
    """
    Agrège le nombre d'avocats admis par année de prestation de serment.

    Retourne un DataFrame avec colonnes `name` (année, str) et `value` (effectif).
    """
    years = (
        pd.to_datetime(df[col_date], errors="coerce")
          .dt.year
          .value_counts()
          .sort_index()
          .loc[year_min:year_max]
    )
    flux_df = pd.DataFrame({
        "name": years.index.astype(str),
        "value": years.values,
    })
    return flux_df
