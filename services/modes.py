"""Catálogo del Modo IA."""

MODES = [
    {"id": "todo", "label": "Todo", "blurb": "Conversación general"},
    {"id": "imagenes", "label": "Imágenes", "blurb": "Resultados de imágenes en la web"},
    {"id": "videos", "label": "Videos", "blurb": "Resultados de video"},
    {"id": "noticias", "label": "Noticias", "blurb": "Noticias recientes"},
    {"id": "libros", "label": "Libros", "blurb": "Libros y referencias"},
    {"id": "finanzas", "label": "Finanzas", "blurb": "Información financiera pública"},
]

MODE_HINTS = {
    "todo": "Responde a la consulta general con lo que haya en el contexto.",
    "imagenes": (
        "El usuario busca imágenes. Describe los resultados por su título y enlace. "
        "No afirmes haber visto la imagen."
    ),
    "videos": "El usuario busca videos. Lista título, quién lo publica si consta, y el enlace.",
    "noticias": "Resume las noticias con fuente y fecha si aparece. No inventes titulares.",
    "libros": "Busca libros. Da título, autor si consta y enlace. No inventes bibliografía.",
    "finanzas": (
        "Resume información financiera pública y recuerda que no es una recomendación de inversión."
    ),
}


def mode_label(mode_id: str) -> str:
    for mode in MODES:
        if mode["id"] == mode_id:
            return mode["label"]
    return "Todo"


def normalize_mode(mode_id: str) -> str:
    ids = {mode["id"] for mode in MODES}
    return mode_id if mode_id in ids else "todo"
