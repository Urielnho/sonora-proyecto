from pathlib import Path
import tomllib

# la configuracion de streamlit es la fuente de la paleta principal
config = tomllib.loads((Path(__file__).resolve().parents[1] / '.streamlit/config.toml').read_text(encoding='utf-8'))['theme']
PALETA = {
    'fondo': config['backgroundColor'],
    'superficie': config['secondaryBackgroundColor'],
    'texto': config['textColor'],
    'coral': config['primaryColor'],
    'secundario': '#A8A8AD',
    'linea': '#303239',
    'cuadricula': '#22242B',
}
COLORES = config['chartCategoricalColors']
FUENTE = 'Inter, "Segoe UI", Arial, sans-serif'


def color_perfil(fila, mapa):
    # una marca de color discreta vincula las tablas con las graficas
    estilos = [''] * len(fila)
    if 'Perfil' in fila.index:
        estilos[list(fila.index).index('Perfil')] = f'color: {mapa.get(fila["Perfil"], PALETA["texto"])}; font-weight: 600'
    elif fila.name in mapa:
        estilos = [f'border-left: 2px solid {mapa[fila.name]}'] + estilos[1:]
    return estilos
