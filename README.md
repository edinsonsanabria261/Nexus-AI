# 🛡️ NexusSec AI - Chatbot de Ciberseguridad

Chatbot especializado en ciberseguridad que **aprende de la web pública en tiempo real**.

Proyecto de **Edinson** · 2026

---

## ✨ Características (v0.1)

- ✅ Especializado en ciberseguridad (OWASP, pentesting, forense, hardening, etc.)
- ✅ Búsqueda en tiempo real en la web (DuckDuckGo - gratis)
- ✅ Lectura de páginas web para obtener información actualizada
- ✅ Modelo potente y gratuito (Groq - Llama 3.3 70B)
- ✅ Interfaz moderna con Streamlit
- ✅ Totalmente personalizable
- ✅ Preparado para añadir RAG (base de conocimiento propia)

---

## 🚀 Cómo empezar (paso a paso)

### 1. Clonar o descargar el proyecto

```bash
git clone https://github.com/edinsonsanabria261/Chat-2026.git
# o crea un repo nuevo y sube estos archivos
cd cybersec-chatbot
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Conseguir API Key de Groq (gratis)

1. Entra a → [https://console.groq.com](https://console.groq.com)
2. Crea una cuenta (con Google o GitHub)
3. Ve a **API Keys** → Create API Key
4. Copia la clave (empieza por `gsk_...`)

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita el archivo `.env` y pega tu clave:

```env
GROQ_API_KEY=gsk_tu_clave_real_aqui
GROQ_MODEL=llama-3.3-70b-versatile
BOT_NAME=NexusSec AI
OWNER_NAME=Edinson
```

### 5. Ejecutar

```bash
streamlit run app.py
```

Se abrirá automáticamente en `http://localhost:8501`

---

## 📁 Estructura del proyecto

```
cybersec-chatbot/
├── app.py                  # Aplicación principal (Streamlit)
├── config.py               # Configuración y System Prompt
├── requirements.txt
├── .env.example
├── tools/
│   └── web_search.py       # Búsqueda y lectura de páginas web
├── rag/
│   └── embeddings.py       # Preparado para RAG (Fase 2)
├── knowledge/              # Aquí pondrás tus PDFs y documentos
└── data/                   # Vectorstore FAISS (se crea solo)
```

---

## 🛣️ Roadmap del proyecto

| Fase | Estado | Descripción |
|------|--------|-----------|
| **v0.1** | ✅ Listo | Chat + búsqueda web en tiempo real |
| **v0.2** | 🔜 | RAG con PDFs y documentos propios |
| **v0.3** | 🔜 | Herramientas (CVE lookup, whois, etc.) |
| **v0.4** | 🔜 | Integración con portal Nexus-Sec |
| **v0.5** | 🔜 | Fine-tuning de modelo pequeño |

---

## ☁️ Despliegue gratis

### Opción A - Streamlit Community Cloud (recomendada)
1. Sube el proyecto a GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta el repo y despliega
4. En Secrets agrega tu `GROQ_API_KEY`

### Opción B - Render
Ya tienes experiencia con Render. Solo configura el Build Command:
```
pip install -r requirements.txt
```
Start Command:
```
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

---

## ⚠️ Notas importantes

- El free tier de Groq es muy generoso, pero tiene límites de rate.
- La búsqueda web es gratuita y sin API key (DuckDuckGo).
- Nunca subas el archivo `.env` a GitHub.

---

Hecho con ❤️ para el ecosistema **Nexus-Sec**
