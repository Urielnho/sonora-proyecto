import unicodedata

# nombres visibles; los identificadores originales del dataset se conservan
GENEROS_ES = {
    'acoustic':'Acústica', 'alternative':'Alternativa', 'alt-rock':'Rock alternativo',
    'ambient':'Ambiental', 'brazil':'Brasileña', 'british':'Británica',
    'children':'Infantil (children)', 'kids':'Infantil (kids)', 'classical':'Clásica',
    'comedy':'Comedia', 'chill':'Relajante', 'dance':'Dance / bailable',
    'electronic':'Electrónica', 'electro':'Electro', 'edm':'Electrónica bailable (EDM)',
    'french':'Francesa', 'german':'Alemana', 'guitar':'Guitarra', 'happy':'Alegre',
    'indian':'De la India', 'iranian':'Iraní', 'j-dance':'Dance japonés',
    'j-idol':'Ídolos japoneses', 'j-pop':'Pop japonés', 'j-rock':'Rock japonés',
    'k-pop':'Pop coreano (K-pop)', 'latin':'Latina (latin)', 'latino':'Latina (latino)',
    'malay':'Malaya', 'mandopop':'Pop en mandarín', 'cantopop':'Pop en cantonés',
    'opera':'Ópera', 'party':'Fiesta', 'pop-film':'Pop de películas',
    'psych-rock':'Rock psicodélico', 'r-n-b':'R&B', 'reggaeton':'Reguetón',
    'romance':'Romántica', 'sad':'Melancólica', 'show-tunes':'Teatro musical',
    'singer-songwriter':'Cantautores', 'songwriter':'Compositores',
    'sleep':'Para dormir', 'spanish':'Española', 'study':'Para estudiar',
    'swedish':'Sueca', 'turkish':'Turca', 'world-music':'Músicas del mundo',
    'goth':'Gótica', 'minimal-techno':'Techno minimalista',
    'progressive-house':'House progresivo', 'synth-pop':'Pop de sintetizadores',
    'mpb':'Música popular brasileña (MPB)', 'forro':'Forró',
}


def nombre_genero(valor):
    return GENEROS_ES.get(valor, valor.replace('-', ' ').title())


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', texto.casefold())
                   if not unicodedata.combining(c)).strip()
