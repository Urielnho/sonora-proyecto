from pathlib import Path
import json
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, adjusted_rand_score
from threadpoolctl import threadpool_limits

BASE = Path(__file__).resolve().parents[1]
VARIABLES = ['danceability', 'energy', 'acousticness', 'valence', 'tempo']
FUENTE = 'https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset'


def preparar():
    original = pd.read_csv(BASE / 'datos/canciones_original.csv')
    df = original.drop(columns=[c for c in original if c.startswith('Unnamed:')]).copy()
    nulos = df.isnull().sum().to_dict()
    duplicados = int(df.duplicated().sum())
    df = df.drop_duplicates()
    for c in VARIABLES + ['popularity', 'duration_ms']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.replace([np.inf, -np.inf], np.nan)
    antes = len(df)
    df = df.dropna(subset=VARIABLES + ['track_id', 'track_name', 'artists', 'track_genre', 'popularity', 'duration_ms'])
    eliminados_nulos = antes - len(df)
    validos = df['tempo'].gt(0) & df['duration_ms'].gt(0) & df['popularity'].between(0, 100)
    for c in VARIABLES[:4]:
        validos &= df[c].between(0, 1)
    invalidos = int((~validos).sum())
    df = df[validos].copy()
    # conservar los generos originales sin contar varias veces la misma cancion
    generos = df.groupby('track_id')['track_genre'].agg(lambda s: ' | '.join(sorted(set(s))))
    repetidas = int(df['track_id'].duplicated().sum())
    df = df.drop_duplicates('track_id').copy()
    df['generos'] = df['track_id'].map(generos)
    df['duracion_min'] = df['duration_ms'] / 60000
    atipicos = {}
    for c in VARIABLES:
        q1, q3 = df[c].quantile([.25, .75])
        atipicos[c] = int(((df[c] < q1 - 1.5 * (q3-q1)) | (df[c] > q3 + 1.5 * (q3-q1))).sum())
    resumen = dict(registros_originales=len(original), columnas_originales=len(original.columns),
                   nulos=nulos, duplicados_completos=duplicados, filas_sin_datos=eliminados_nulos,
                   filas_invalidas=invalidos, ids_repetidos=repetidas, registros_limpios=len(df),
                   atipicos_iqr=atipicos, fuente=FUENTE)
    return original, df.reset_index(drop=True), resumen


def entrenar(df, k, semilla=42):
    escalador = StandardScaler()
    X = escalador.fit_transform(df[VARIABLES])
    with threadpool_limits(limits=2):
        modelo = KMeans(n_clusters=k, random_state=semilla, n_init=10)
        etiquetas = modelo.fit_predict(X)
    centros = pd.DataFrame(escalador.inverse_transform(modelo.cluster_centers_), columns=VARIABLES)
    return etiquetas, centros, modelo, X


def generar():
    original, df, resumen = preparar()
    salida = BASE / 'resultados'
    salida.mkdir(exist_ok=True)
    original.head(10).to_csv(salida/'primeros_10.csv', index=False)
    original.dtypes.astype(str).to_csv(salida/'tipos_datos.csv')
    original.describe().to_csv(salida/'estadisticas_originales.csv')
    metricas = []
    modelos = {}
    for k in range(2, 7):
        etiquetas, centros, modelo, X = entrenar(df, k)
        with threadpool_limits(limits=2):
            silueta = silhouette_score(X, etiquetas, sample_size=min(2500, len(df)), random_state=42)
        metricas.append(dict(K=k, inercia=modelo.inertia_, silhouette=silueta, iteraciones=modelo.n_iter_))
        modelos[k] = (etiquetas, centros, modelo)
        print(f'K={k}: silhouette={silueta:.4f}', flush=True)
    metricas = pd.DataFrame(metricas)
    mejor = int(metricas.loc[metricas.silhouette.idxmax(), 'K'])
    etiquetas, centros, modelo = modelos[mejor]
    # ordenar por energia para tener identificadores reproducibles y legibles
    orden = centros.energy.sort_values().index.tolist()
    mapa = {viejo: nuevo for nuevo, viejo in enumerate(orden)}
    df['Grupo'] = [mapa[g] for g in etiquetas]
    centros = centros.loc[orden].reset_index(drop=True)
    nombres = []
    for i, c in centros.iterrows():
        energia = 'energía alta' if c.energy >= .65 else 'energía media' if c.energy >= .4 else 'energía baja'
        textura = 'acústicas' if c.acousticness >= .5 else 'bailables' if c.danceability >= .6 else 'mixtas'
        nombres.append(f'{i+1}. {textura.capitalize()}, {energia}')
    centros['Perfil'] = nombres
    df['Perfil'] = df.Grupo.map(dict(enumerate(nombres)))
    otra_k = 3 if mejor != 3 else 2
    a, b, m = modelos[otra_k]
    resumen.update(k_elegido=mejor, criterio='Mayor silhouette entre K=2 y K=6, muestra fija de 2500 canciones',
                   silhouette=float(metricas.loc[metricas.K.eq(mejor), 'silhouette'].iloc[0]),
                   comparacion_k=otra_k, ari_entre_configuraciones=float(adjusted_rand_score(etiquetas, a)),
                   iteraciones=int(modelo.n_iter_))
    df.to_csv(salida/'canciones_agrupadas.csv', index=False)
    centros.to_csv(salida/'centroides.csv', index=False)
    metricas.to_csv(salida/'evaluacion_k.csv', index=False)
    df.groupby('Perfil')[VARIABLES + ['popularity', 'duracion_min']].describe().to_csv(salida/'estadisticas_grupos.csv')
    (salida/'resumen.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding='utf-8')
    # graficas exploratorias y agrupamiento para la documentacion
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    for columna in ['energy', 'tempo', 'danceability']:
        fig, ax = plt.subplots(figsize=(8,4))
        sns.histplot(df[columna], bins=35, ax=ax, color='#8b5cf6')
        ax.set_title('Distribución de ' + columna)
        fig.tight_layout()
        fig.savefig(salida/f'exploracion_{columna}.png', dpi=150)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(8,5))
    sns.scatterplot(data=df.sample(min(3000,len(df)), random_state=42), x='danceability', y='energy', hue='Perfil', s=12, ax=ax)
    fig.tight_layout()
    fig.savefig(salida/'agrupamientos.png', dpi=150)
    plt.close(fig)
    print(f'Listo: {len(df)} canciones únicas; K elegido: {mejor}', flush=True)


if __name__ == '__main__':
    generar()
