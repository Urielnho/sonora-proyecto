# SONORA

Explorador de canciones y segmentación musical mediante K-Means. Proyecto integrador de la tercera unidad de **Extracción de Conocimiento en Bases de Datos**, grupo **IDGS-9-1**.

## Integrantes

- Uriel Ochoa Mora
- José Armando Monreal Gámez
- Álvaro Aloisses Rodríguez Vera

## Ejecutar

Abre una terminal dentro de la carpeta del proyecto.

Se probó con **Python 3.14**. No requiere cuenta de Spotify, claves de API ni descargar audio. Se incluyen el dataset y los resultados; después de instalar las dependencias el dashboard trabaja con archivos locales.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run codigo/app.py --server.address localhost --server.port 8501
```

Abre **http://localhost:8501** y mantén la terminal abierta. Para detenerlo pulsa **Ctrl+C**. Si el puerto está ocupado, sustituye `8501` por `8502` en el comando y en la dirección. En Linux o macOS utiliza `.venv/bin/python` en lugar de `.venv\Scripts\python.exe`.

### Repetir el análisis

No es necesario para abrir el dashboard. Para regenerar el dataset procesado, las métricas y las gráficas:

```powershell
.venv\Scripts\python.exe codigo/analisis.py
```

Puede tardar varios minutos según el equipo. Después reinicia el dashboard para cargar los archivos actualizados.

## Cómo usar el dashboard

**Análisis general:** cuatro indicadores (cantidad de canciones, popularidad, energía y tempo), distribuciones de energía, géneros, tempo y duración, y revisión de la limpieza.

**Segmentación K-Means:** dispersión, canciones por grupo, comparación de características, popularidad, estadísticas, centroides y evaluación de cinco valores de K.

En **Filtros** puedes buscar por canción o artista, elegir un tipo de sonido, seleccionar géneros y ajustar popularidad y duración. Se actualiza automáticamente; después de escribir una búsqueda pulsa Enter. La búsqueda admite nombres incompletos y sin acentos.

- Sin géneros seleccionados se incluyen todos. Puedes seleccionar varios.
- Los nombres comunes se muestran en español sin alterar los identificadores del dataset.
- Cada filtro se puede quitar por separado; también puedes restablecer toda la colección.
- Los ejes permiten comparar dos características distintas y explican sus escalas.
- La tabla presenta hasta 300 canciones y la dispersión hasta 4,000. Los indicadores consideran toda la selección.
- La descarga CSV incluye todas las canciones filtradas.
- Los filtros no entrenan de nuevo el modelo ni cambian los centroides.

## Datos y limpieza

Fuente: [Spotify Tracks Dataset de Maharshi Pandya](https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset).

[Descarga original](https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/main/dataset.csv).

La fuente declara licencia BSD; consulta su ficha para conocer las condiciones. Se comparten datos tabulares, no archivos de audio.

El original contiene **114,000 filas y 21 columnas**, incluyendo un índice exportado que se elimina.

| Tratamiento | Registros |
| --- | ---: |
| Duplicados completos eliminados | 450 |
| Fila sin información necesaria eliminada | 1 |
| Valores no válidos excluidos | 157 |
| Filas adicionales del mismo track_id eliminadas | 23,809 |
| Canciones únicas para el análisis | **89,583** |

Se validan tipos numéricos, rangos de las características entre 0 y 1, popularidad entre 0 y 100, y duración y tempo positivos. Se conserva una fila por canción y se reúnen sus géneros en `generos`. Se cuentan los atípicos con IQR, pero se conservan los válidos porque pueden representar estilos reales.

## Modelo y resultados

Se agrupa usando `danceability` (bailabilidad), `energy` (intensidad), `acousticness` (carácter acústico), `valence` (tono musical) y `tempo` (BPM). **StandardScaler** evita que el tempo domine por su escala. Género, artista y popularidad no se usan para entrenar.

Se evalúan K de 2 a 6 con semilla 42 y 10 inicializaciones. Se elige el mayor silhouette en una muestra fija de 2,500 canciones; el entrenamiento utiliza todas las canciones limpias. También se guardan inercia, iteraciones y ARI para comparar dos particiones.

| K | Silhouette |
| --- | ---: |
| **2** | **0.306** |
| 3 | 0.247 |
| 4 | 0.230 |
| 5 | 0.222 |
| 6 | 0.202 |

El modelo elegido realizó **17 iteraciones**. Silhouette no es un porcentaje de exactitud.

| Perfil | Canciones | Energía media | Acústica media | Tempo medio |
| --- | ---: | ---: | ---: | ---: |
| Acústicas de energía baja | 27,201 | 0.343 | 0.737 | 110.1 BPM |
| Mixtas de energía alta | 62,382 | 0.763 | 0.150 | 127.6 BPM |

Los nombres describen los promedios del grupo y no son géneros oficiales. La herramienta apoya la exploración de playlists, pero no predice gustos individuales. Los grupos dependen de las variables y de la configuración. La popularidad es histórica y no se consulta en vivo.

## Estructura

```text
.streamlit/config.toml           Configuración visual
codigo/app.py                   Dashboard
codigo/analisis.py              Limpieza, entrenamiento y evaluación
codigo/identidad.py             Estilos compartidos
codigo/filtros.py               Traducciones y búsqueda
datos/canciones_original.csv    Dataset original
resultados/                     Dataset agrupado, estadísticas y gráficas
requirements.txt                Versiones utilizadas
```

Para explorar el proyecto ejecuta Streamlit siguiendo las instrucciones anteriores.
