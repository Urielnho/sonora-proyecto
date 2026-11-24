from pathlib import Path
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from string import Template
from identidad import PALETA, COLORES, FUENTE, color_perfil
from filtros import nombre_genero, normalizar

BASE = Path(__file__).resolve().parents[1]
px.defaults.color_discrete_sequence = COLORES
st.set_page_config(page_title='SONORA · Análisis musical', layout='wide', initial_sidebar_state='collapsed')
st.markdown(Template('''<style>
.stApp {background:$fondo;color:$texto;font-family:Inter,"Segoe UI",Arial,sans-serif}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
#MainMenu, footer, [data-testid="stToolbar"] {display:none}
header[data-testid="stHeader"] {background:transparent;height:0}
.block-container {padding:1.5rem 3rem 3rem;max-width:1440px}
h1,h2,h3 {letter-spacing:-.025em;font-weight:600!important}
h1 {font-size:1.65rem!important;padding:.25rem 0!important}
h2 {font-size:1.25rem!important} h3 {font-size:1.05rem!important}
p, label {font-size:14px!important}
[data-testid="stCaptionContainer"] {color:$secundario}
[data-testid="stMetric"] {background:transparent;border:0;border-left:1px solid $linea;border-radius:0;padding:4px 20px 10px}
[data-testid="stMetricLabel"] {color:$secundario;font-size:12px}
[data-testid="stMetricValue"] {font-size:1.85rem;font-weight:500;letter-spacing:-.04em}
[data-testid="stMetricValue"] * {font-size:1.85rem!important;line-height:1.2!important;font-weight:500}
.wordmark {font-size:25px;font-weight:650;letter-spacing:3.5px;line-height:1.4}
.wordmark::first-letter {color:$coral}
.wordmark small {display:block;font-size:10px;font-weight:400;letter-spacing:1px;color:$secundario;margin-top:3px}
[data-testid="stRadio"] [role="radiogroup"] {gap:24px;min-height:43px;align-items:center}
[data-testid="stRadio"] [role="radiogroup"] label {border-bottom:2px solid transparent;padding:8px 0;border-radius:0}
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {border-color:$coral;color:$coral}
[data-testid="stRadio"] [role="radiogroup"] label>div:first-child {display:none}
[data-testid="stRadioOption"]>div>div:first-child {display:none}
[data-testid="stPopover"] button, button[kind="secondary"], [data-testid="stDownloadButton"] button {border:1px solid $linea;border-radius:3px;background:$superficie;color:$texto;box-shadow:none}
[data-testid="stPopoverBody"] {background:$superficie;border:1px solid $linea;border-radius:4px;min-width:min(540px,90vw);max-height:85vh;overflow-y:auto}
[data-baseweb="select"]>div, [data-baseweb="input"], [data-testid="stExpander"] {border-radius:3px!important;border-color:$linea!important}
[data-testid="stDataFrame"] {border-radius:0}
hr {border-color:$linea;margin:12px 0 20px}
@media(max-width:760px) {
 .block-container {padding:1rem 1rem 2rem}
 [data-testid="stMetric"] {padding:4px 8px}
 [data-testid="stMetricValue"] {font-size:1.4rem}
 [data-testid="stMetricValue"] * {font-size:1.4rem!important}
 [data-testid="stRadio"] [role="radiogroup"] {gap:14px}
}

[data-testid="stRadioOption"]:hover {color:$texto}
[data-testid="stRadioOption"]:focus-within {outline:1px solid $coral;outline-offset:4px}
[data-testid="stPopover"] button:hover, [data-testid="stDownloadButton"] button:hover {border-color:$coral;color:$texto;background:$superficie}
[data-testid="stExpander"] summary:hover {color:$coral}
[data-baseweb="select"]>div, [data-baseweb="input"], [data-baseweb="textarea"] {background:$superficie!important;border-radius:3px!important}
[data-baseweb="select"]:focus-within>div, [data-baseweb="input"]:focus-within {border-color:$coral!important;box-shadow:none!important}
[data-baseweb="tag"] {background:$linea!important;color:$texto!important;border-radius:2px!important;border-bottom:2px solid $coral}
[data-baseweb="popover"], [data-baseweb="tooltip"] {border-radius:3px!important}
[data-baseweb="menu"] {background:$superficie;color:$texto}
[data-baseweb="slider"] [role="slider"] {background:$coral;box-shadow:none}
[data-testid="stDataFrame"] {border:1px solid $linea}
[data-testid="stCaptionContainer"] p {color:$secundario!important}
[data-testid="stMetricLabel"] p {color:$secundario!important;font-size:12px!important}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {color:$coral;border-color:$coral}
</style>''').substitute(PALETA), unsafe_allow_html=True)
ETIQUETAS = {'energy':'Energía', 'danceability':'Bailabilidad', 'acousticness':'Acústica',
             'valence':'Tono emocional', 'tempo':'Tempo (BPM)', 'popularity':'Popularidad', 'duracion_min':'Duración (min)'}


@st.cache_data
def cargar():
    df = pd.read_csv(BASE/'resultados/canciones_agrupadas.csv')
    centros = pd.read_csv(BASE/'resultados/centroides.csv')
    evaluacion = pd.read_csv(BASE/'resultados/evaluacion_k.csv')
    resumen = json.loads((BASE/'resultados/resumen.json').read_text(encoding='utf-8'))
    return df, centros, evaluacion, resumen


if not (BASE/'resultados/resumen.json').exists():
    st.info('Primero ejecuta: python codigo/analisis.py')
    st.stop()
df, centros, evaluacion, resumen = cargar()
perfiles = centros.Perfil.tolist()
duracion_maxima = float(int(df.duracion_min.max()) + 1)


def restablecer_filtros():
    for clave in ['busqueda', 'perfil_elegido', 'genero', 'nivel_popularidad',
                  'rango_popularidad', 'tipo_duracion', 'rango_duracion']:
        st.session_state.pop(clave, None)


def quitar_filtro(claves):
    for clave in claves:
        st.session_state.pop(clave, None)


@st.cache_data
def nombres_busqueda(nombres, artistas):
    return (nombres.fillna('') + ' ' + artistas.fillna('')).map(normalizar)


def filtros_activos():
    return sum([st.session_state.get('perfil_elegido', 'Todos los perfiles') != 'Todos los perfiles',
                bool(st.session_state.get('genero', [])),
                st.session_state.get('nivel_popularidad', 'Cualquiera') != 'Cualquiera',
                st.session_state.get('tipo_duracion','Cualquier duración') != 'Cualquier duración',
                bool(st.session_state.get('busqueda','').strip())])

marca, navegacion, filtros = st.columns([1.2, 3.5, .8], vertical_alignment='center')
with marca:
    st.markdown('<div class="wordmark">SONORA<small>ANÁLISIS MUSICAL</small></div>', unsafe_allow_html=True)
with navegacion:
    pagina = st.radio('Navegación', ['Análisis general', 'Segmentación K-Means'],
                      horizontal=True, label_visibility='collapsed', key='pagina')
with filtros:
    numero_filtros = filtros_activos()
    with st.popover(f'Filtros · {numero_filtros}' if numero_filtros else 'Filtros', width='stretch'):
        st.markdown('### Encuentra tu música')
        st.caption('Elige solo lo que te interese. Los cambios se aplican automáticamente.')
        coincidencias = st.empty()
        busqueda = st.text_input('Buscar canción o artista', placeholder='Ejemplo: Taylor Swift', key='busqueda',
                                 help='Escribe parte del nombre y pulsa Enter. No distingue mayúsculas y minúsculas.')
        st.caption('Escribe un nombre y pulsa Enter. No necesitas escribirlo completo ni usar acentos.')
        perfil = st.selectbox('Tipo de sonido', ['Todos los perfiles'] + perfiles, key='perfil_elegido',
                               filter_mode=None,
                               format_func=lambda p: p if p == 'Todos los perfiles' else p.split('. ',1)[-1],
                               help='Son grupos por características del sonido, no géneros musicales.')
        grupos = perfiles if perfil == 'Todos los perfiles' else [perfil]
        if perfil == 'Todos los perfiles':
            st.caption('Incluye todos los sonidos. Estas opciones agrupan canciones por cómo suenan, no por su género.')
        else:
            centro = centros[centros.Perfil.eq(perfil)].iloc[0]
            st.caption('Predominan sonidos acústicos y de menor intensidad.' if centro.acousticness >= .5 else
                       'Predominan sonidos de mayor intensidad y estilos variados.')
        generos = sorted({g.strip() for texto in df.generos for g in texto.split('|')}, key=nombre_genero)
        genero = st.multiselect('Géneros musicales', generos, key='genero',
                                format_func=nombre_genero, select_all=False,
                                placeholder='Busca o elige un género')
        st.caption('Sin selección: todos los géneros. Puedes elegir más de uno y quitarlo con la ×.')
        nivel = st.selectbox('Popularidad', ['Cualquiera', 'Muy populares · 70 a 100',
                              'Popularidad media · 30 a 69', 'Poco conocidas · 0 a 29',
                              'Elegir un rango'], key='nivel_popularidad', filter_mode=None)
        popularidad = {'Cualquiera':(0,100), 'Muy populares · 70 a 100':(70,100),
                       'Popularidad media · 30 a 69':(30,69), 'Poco conocidas · 0 a 29':(0,29)}.get(nivel)
        if popularidad is None:
            popularidad = st.slider('Menos populares ← → Más populares',0,100,(0,100),key='rango_popularidad')
        st.caption('Popularidad registrada en el dataset; no indica si una canción es buena o mala.')
        tipo = st.selectbox('Duración de la canción', ['Cualquier duración', 'Hasta 3 minutos',
                             'Entre 3 y 5 minutos', 'Más de 5 minutos', 'Elegir un rango'], key='tipo_duracion', filter_mode=None)
        duracion = {'Cualquier duración':(0.0,duracion_maxima), 'Hasta 3 minutos':(0.0,3.0),
                    'Entre 3 y 5 minutos':(3.0,5.0), 'Más de 5 minutos':(5.0,duracion_maxima)}.get(tipo)
        if duracion is None:
            duracion = st.slider('Duración mínima y máxima (minutos)',0.0,duracion_maxima,
                                  (0.0,duracion_maxima),step=.5,key='rango_duracion')
        minimo, maximo = duracion
        st.button('Quitar todos los filtros', on_click=restablecer_filtros, width='stretch')
st.divider()

vista = df[df.Perfil.isin(grupos) & df.popularity.between(*popularidad) & df.duracion_min.between(*duracion)].copy()
if tipo == 'Más de 5 minutos':
    vista = vista[vista.duracion_min > 5]
if genero:
    seleccionados = set(genero)
    mascara = vista.generos.map(lambda s: bool(seleccionados.intersection(s.split(' | ')))).astype(bool)
    vista = vista.loc[mascara]
if busqueda.strip():
    texto_busqueda = nombres_busqueda(df.track_name, df.artists)
    terminos = normalizar(busqueda).split()
    for termino in terminos:
        vista = vista.loc[texto_busqueda.loc[vista.index].str.contains(termino, regex=False)]

coincidencias.caption(f'{len(vista):,} canciones encontradas' if len(vista) else 'No hay coincidencias con esta combinación.')

st.title(pagina)
activos = filtros_activos()
st.caption(f'{len(vista):,} de {len(df):,} canciones · {resumen["k_elegido"]} perfiles musicales · '
           + (f'{activos} filtros activos' if activos else 'Colección completa'))
detalle = []
if busqueda.strip():
    detalle.append(f'Búsqueda: {busqueda.strip()}')
if set(grupos) != set(perfiles):
    detalle.append('Sonido: ' + perfil.split('. ',1)[-1])
if genero:
    detalle.append('Géneros: ' + ', '.join(map(nombre_genero,genero)))
if popularidad != (0,100):
    detalle.append(f'Popularidad: {popularidad[0]}–{popularidad[1]}')
if duracion != (0.0,duracion_maxima):
    detalle.append(f'Duración: {minimo:g}–{maximo:g} min')
if detalle:
    st.caption(' · '.join(detalle))
    acciones = []
    if busqueda.strip():
        acciones.append(('Quitar búsqueda', ['busqueda']))
    if perfil != 'Todos los perfiles':
        acciones.append(('Todos los sonidos', ['perfil_elegido']))
    if genero:
        acciones.append(('Todos los géneros', ['genero']))
    if popularidad != (0,100):
        acciones.append(('Cualquier popularidad', ['nivel_popularidad', 'rango_popularidad']))
    if duracion != (0.0,duracion_maxima):
        acciones.append(('Cualquier duración', ['tipo_duracion', 'rango_duracion']))
    for espacio, (texto, claves) in zip(st.columns(len(acciones)), acciones):
        espacio.button(texto, on_click=quitar_filtro, args=(claves,), width='stretch')
    st.button('Limpiar todos los filtros', on_click=restablecer_filtros)

if vista.empty:
    st.info('No encontramos canciones con todos estos criterios. Prueba quitar la búsqueda, elegir todos los géneros o ampliar la duración. También puedes volver a la colección completa.')
    st.button('Ver todas las canciones', on_click=restablecer_filtros)
    st.stop()

a,b,c,d = st.columns(4)
a.metric('Canciones seleccionadas', f'{len(vista):,}')
b.metric('Popularidad promedio', f'{vista.popularity.mean():.1f}', help='Escala de 0 a 100; valor histórico.')
c.metric('Energía promedio', f'{vista.energy.mean():.2f}', help='Escala de 0 a 1.')
d.metric('Tempo promedio', f'{vista.tempo.mean():.0f} BPM')
st.write('')


def mostrar(fig, altura=330):
    fig.update_layout(template='plotly_dark', paper_bgcolor=PALETA['fondo'], plot_bgcolor=PALETA['fondo'],
                      height=altura, margin=dict(l=12,r=12,t=50,b=35),
                      font=dict(family=FUENTE,color=PALETA['secundario'],size=11),
                      title=dict(font=dict(size=15,color=PALETA['texto']),x=0),
                      legend=dict(title_text='',orientation='h',y=-.24,x=0,font=dict(size=10)),
                      colorway=COLORES, bargap=.08,
                      hoverlabel=dict(bgcolor=PALETA['superficie'],bordercolor=PALETA['linea'],
                                      font=dict(family=FUENTE,color=PALETA['texto'],size=12)),
                      hovermode='closest')
    fig.update_xaxes(showgrid=False,zeroline=False,linecolor=PALETA['linea'],automargin=True)
    fig.update_yaxes(gridcolor=PALETA['cuadricula'],zeroline=False,gridwidth=1,automargin=True)
    if fig.data and fig.data[0].type == 'histogram':
        fig.update_yaxes(title_text='Canciones')
    st.plotly_chart(fig, width='stretch', config={'displaylogo':False,'displayModeBar':False,'scrollZoom':False})


if pagina == 'Análisis general':
    izq, der = st.columns([1.15,1], gap='large')
    with izq:
        mostrar(px.histogram(vista, x='energy', nbins=40, title='Distribución de energía',
                             labels=ETIQUETAS, color_discrete_sequence=[COLORES[0]]))
    with der:
        conteo = vista.generos.str.split(' | ', regex=False).explode().value_counts().head(12).rename_axis('Género').reset_index(name='Canciones')
        conteo['Género'] = conteo['Género'].map(nombre_genero)
        mostrar(px.bar(conteo, x='Canciones', y='Género', orientation='h', title='Géneros con más presencia',
                       color_discrete_sequence=[COLORES[1]]).update_yaxes(autorange='reversed'))
        st.caption('Una canción puede aparecer en más de un género; estos conteos no son excluyentes.')
    izq, der = st.columns(2)
    with izq:
        mostrar(px.histogram(vista, x='tempo', nbins=40, title='Distribución del tempo', labels=ETIQUETAS,
                             color_discrete_sequence=[COLORES[0]]))
    with der:
        mostrar(px.histogram(vista, x='duracion_min', nbins=50, title='Duración de las canciones', labels=ETIQUETAS,
                             color_discrete_sequence=[COLORES[1]]))
    with st.expander('Exploración y limpieza del dataset'):
        st.write(f'Original: {resumen["registros_originales"]:,} registros y {resumen["columnas_originales"]} columnas (incluye un índice exportado).')
        st.json({k:resumen[k] for k in ['nulos','duplicados_completos','filas_sin_datos','filas_invalidas','ids_repetidos','atipicos_iqr']})
        st.write('Se elimina el índice exportado, se validan rangos y se excluyen tempos no positivos. Se conserva una fila por track_id y se reúnen sus géneros. Los atípicos válidos se conservan: pueden representar estilos musicales distintos.')
        st.dataframe(df.head(10), hide_index=True)
else:
    st.caption('Los perfiles se mantienen fijos al filtrar. Explora cómo cambia su presencia en la selección.')
    if len(vista) < 10:
        st.info(f'Estás viendo {len(vista)} canción(es). Cada punto representa una canción; con tan pocos datos no se puede apreciar la distribución de los grupos. Quita filtros para comparar más canciones.')
        st.button('Comparar con toda la colección', on_click=restablecer_filtros)
    izq, der = st.columns([1.8,1], gap='large')
    with izq:
        st.markdown('**¿Qué características quieres comparar?**')
        control_x, control_y = st.columns(2)
        variables = list(ETIQUETAS)[:5]
        eje_x = control_x.selectbox('Comparar', variables, index=1,
                                    format_func=ETIQUETAS.get, filter_mode=None, key='comparar_x')
        opciones_y = [c for c in variables if c != eje_x]
        if st.session_state.get('comparar_y') not in opciones_y:
            st.session_state.pop('comparar_y', None)
        eje_y = control_y.selectbox('Con', opciones_y, format_func=ETIQUETAS.get,
                                    filter_mode=None, key='comparar_y')
        explicaciones = {'energy':'Energía: de suave (0) a intensa (1).',
                        'danceability':'Bailabilidad: de menos bailable (0) a más bailable (1).',
                        'acousticness':'Acústica: de menor (0) a mayor carácter acústico (1).',
                        'valence':'Tono emocional: de sonido más melancólico (0) a más positivo (1).',
                        'tempo':'Tempo: velocidad del ritmo en pulsos por minuto (BPM).'}
        st.caption(explicaciones[eje_x] + ' ' + explicaciones[eje_y])
        muestra = vista.sample(min(4000,len(vista)), random_state=42)
        fig = px.scatter(muestra, x=eje_x, y=eje_y, color='Perfil', opacity=.6,
                         hover_name='track_name', hover_data=['artists'], labels=ETIQUETAS,
                         color_discrete_map=dict(zip(perfiles,COLORES)), title='Mapa de canciones')
        if eje_x != 'tempo':
            fig.update_xaxes(range=[0,1])
        if eje_y != 'tempo':
            fig.update_yaxes(range=[0,1])
        mostrar(fig, 410)
        st.caption(f'Se dibujan hasta 4,000 canciones de la selección para mantener la fluidez. El modelo se entrenó con {len(df):,}.')
    with der:
        conteo = vista.Perfil.value_counts().rename_axis('Perfil').reset_index(name='Canciones')
        st.write('')
        mostrar(px.bar(conteo, x='Canciones', y='Perfil', orientation='h',title='Canciones por perfil',
                       color='Perfil', color_discrete_map=dict(zip(perfiles,COLORES)))
                       .update_layout(showlegend=False).update_yaxes(title_text='',tickmode='array',
                           tickvals=conteo.Perfil, ticktext=[p.split('. ',1)[-1].replace(', ', '<br>') for p in conteo.Perfil]),410)
        st.caption('Cada barra cuenta canciones de la selección actual, no de toda la colección.')
    izq, der = st.columns(2)
    medias = vista.groupby('Perfil')[['energy','danceability','acousticness','valence']].mean().reset_index()
    with izq:
        medias = medias.rename(columns=ETIQUETAS)
        mostrar(px.bar(medias.melt(id_vars='Perfil',var_name='Característica',value_name='Promedio'),
                       x='Característica', y='Promedio', color='Perfil', barmode='group',
                       color_discrete_map=dict(zip(perfiles,COLORES)), title='Características medias por grupo'))
    with der:
        mostrar(px.box(vista, x='Perfil', y='popularity', color='Perfil', points=False, labels=ETIQUETAS,
                       color_discrete_map=dict(zip(perfiles,COLORES)), title='Popularidad dentro de cada grupo'))
    st.markdown('### Comparación de los grupos seleccionados')
    estadisticas = vista.groupby('Perfil').agg(Canciones=('track_id','size'), Energía=('energy','mean'),
                     Bailabilidad=('danceability','mean'), Acústica=('acousticness','mean'),
                     Tempo=('tempo','mean'), Popularidad=('popularity','mean'))
    st.dataframe(estadisticas.round(3).reset_index().style
                 .format(precision=3, thousands=',')
                 .apply(color_perfil, axis=1, mapa=dict(zip(perfiles,COLORES))),
                 hide_index=True, width='stretch')
    with st.expander('Estadísticas descriptivas completas de la selección'):
        st.dataframe(vista.groupby('Perfil')[list(ETIQUETAS)].describe().round(3))
    st.markdown('### Qué caracteriza a cada perfil')
    for _, fila in centros[centros.Perfil.isin(grupos)].iterrows():
        st.markdown(f'**{fila.Perfil}** — Energía {fila.energy:.2f}, bailabilidad {fila.danceability:.2f}, acústica {fila.acousticness:.2f} y tempo {fila.tempo:.0f} BPM.')
    st.caption('Los centroides corresponden al modelo completo y se mantienen fijos al filtrar.')
    st.markdown('### Cómo elegimos el número de grupos')
    izq, der = st.columns(2)
    with izq:
        mostrar(px.line(evaluacion,x='K',y='inercia',markers=True,title='Método del codo'))
    with der:
        mostrar(px.line(evaluacion,x='K',y='silhouette',markers=True,title='Silhouette · mayor es mejor'))
    st.write(f'K seleccionado: **{resumen["k_elegido"]}**, por mayor silhouette (**{resumen["silhouette"]:.3f}**) entre cinco configuraciones. Silhouette se calcula sobre una muestra fija de 2,500 canciones.')
    st.dataframe(evaluacion.round(4),hide_index=True)
    st.caption(f'Comparación con K={resumen["comparacion_k"]}: ARI = {resumen["ari_entre_configuraciones"]:.3f}. Mide la coincidencia entre las dos particiones, no su exactitud.')

st.divider()
st.subheader('Catálogo de canciones')
tabla = vista[['track_name','artists','Perfil','generos','popularity','duracion_min','energy','danceability','tempo']].sort_values('popularity',ascending=False)
tabla = tabla.copy()
tabla['generos'] = tabla.generos.map(lambda s: ' | '.join(nombre_genero(g) for g in s.split(' | ')))
st.dataframe(tabla.head(300).rename(columns={'track_name':'Canción','artists':'Artista','generos':'Géneros',**ETIQUETAS}).style.apply(color_perfil, axis=1, mapa=dict(zip(perfiles,COLORES))),
             hide_index=True, width='stretch', height=340,
             column_config={'Duración (min)':st.column_config.NumberColumn(format='%.2f'),
                            'Energía':st.column_config.NumberColumn(format='%.2f'),
                            'Bailabilidad':st.column_config.NumberColumn(format='%.2f'),
                            'Tempo (BPM)':st.column_config.NumberColumn(format='%.1f')})
st.caption('La tabla presenta las primeras 300 canciones ordenadas por popularidad. La descarga incluye toda la selección.')
st.download_button('Descargar selección en CSV', vista.to_csv(index=False).encode('utf-8-sig'), 'seleccion_canciones.csv', 'text/csv')
st.divider()
st.subheader('Hallazgos y recomendaciones')
mas = vista.Perfil.value_counts().idxmax()
energetico = vista.groupby('Perfil').energy.mean().idxmax()
acustico = vista.groupby('Perfil').acousticness.mean().idxmax()
hallazgos, recomendaciones = st.columns(2, gap='large')
with hallazgos:
    st.markdown('**En esta selección**')
    st.write(f'El perfil más frecuente es **{mas}**.')
    st.write(f'La mayor energía media corresponde a **{energetico}**.')
    st.write(f'El mayor carácter acústico corresponde a **{acustico}**.')
with recomendaciones:
    st.markdown('**Para explorar playlists**')
    st.write('Usa los grupos de mayor energía como punto de partida para selecciones activas.')
    st.write('Explora los perfiles acústicos para encontrar música de carácter más suave.')
    st.write('Combina género y popularidad para incorporar variedad y escucha antes de seleccionar.')
with st.expander('Alcance y fuente de los datos'):
    st.write('Los grupos no predicen gustos personales. Las etiquetas describen promedios, no géneros ni emociones de las personas. K-Means favorece grupos compactos y depende de las variables y el escalamiento elegidos. La popularidad es histórica.')
    st.markdown(f'[Spotify Tracks Dataset · Maharshi Pandya]({resumen["fuente"]})')
