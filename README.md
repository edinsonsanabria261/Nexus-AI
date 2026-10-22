# NexusSec AI

Asistente empresarial con Modo IA y foco de ciberseguridad defensiva.

## Modo IA

- Todo
- Imágenes
- Videos
- Noticias
- Libros
- Finanzas

En Todo puedes activar o no los resultados de la web. En el resto de modos la búsqueda se hace sola. Debajo de la respuesta quedan los enlaces usados.

Consultas directas, sin pasar por el modelo: `cve CVE-2024-1234`, `whois ejemplo.com`, `dns ejemplo.com`, `ip 1.1.1.1`, `headers https://ejemplo.com`, `hash texto`.

Para guardar una nota: `recuerda esto: el texto`.

## Qué hace y qué no hace

Ayuda a explicar defensa, a leer un CVE para parchear y a revisar código señalando el fallo y la corrección.

No escribe exploits, malware, payloads ni planes de ataque. Tampoco es un asesor de inversión.

## Estructura

```
app.py                  # arranque
config.py               # claves y prompt
ui/                     # diseño: tema, barra, mensajes
services/               # modo, sesión y respuesta
tools/                  # web, memoria, historial, archivos, consultas
rag/embeddings.py       # FAISS local, todavía no conectado al chat
sql/schema.sql          # tablas de Supabase
```

## Arranque

```bash
git clone https://github.com/edinsonsanabria261/Nexus-AI.git
cd Nexus-AI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

En Supabase, ejecuta `sql/schema.sql` antes de usar memoria, historial o carga de archivos.

## Despliegue

Streamlit Community Cloud o Render.

Build:

```
pip install -r requirements.txt
```

Start:

```
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

La clave de Groq va en los secretos del servicio, no en el repositorio.

## Seguridad y hardening

- Se valida que las URLs consultadas sean públicas y no apunten a hosts locales o privados.
- La memoria y el contenido generado se sanitizan antes de almacenarse o reutilizarse en un prompt.
- La web se consulta con límites de longitud y validación de host para reducir riesgo de prompt injection y abuso de acceso a servicios locales.
- Los comandos directos (`whois`, `dns`, `ip`, `headers`) rechazan entradas no válidas o privadas.
