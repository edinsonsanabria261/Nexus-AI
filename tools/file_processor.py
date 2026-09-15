"""
Módulo avanzado de extracción y segmentación de archivos (PDF, Código, Texto) para Nexus-AI
"""

import io
from pypdf import PdfReader

def process_and_index_file(file_contents: bytes, filename: str) -> int:
    """
    Procesa un archivo binario, extrae su texto por páginas y lo indexa semánticamente en Supabase.
    Devuelve la cantidad de bloques guardados con éxito.
    """
    text_by_page = []
    
    # 1. Extracción de contenido según el tipo de archivo
    if filename.lower().endswith('.pdf'):
        try:
            pdf_file = io.BytesIO(file_contents)
            reader = PdfReader(pdf_file)
            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_by_page.append((page_text, page_num))
        except Exception as e:
            print(f"[file_processor] Error leyendo PDF ({filename}): {e}")
            return 0
    else:
        # Asumimos archivos de texto plano (.py, .txt, .json, .md, etc.)
        try:
            plain_text = file_contents.decode("utf-8", errors="ignore")
            if plain_text.strip():
                text_by_page.append((plain_text, 1))
        except Exception as e:
            print(f"[file_processor] Error leyendo archivo de texto ({filename}): {e}")
            return 0

    if not text_by_page:
        return 0

    # 2. Segmentación en bloques semánticos (Chunking) con solapamiento
    # Dividimos en bloques pequeños para que la búsqueda por vectores sea ultra precisa
    chunk_size = 600
    overlap = 150
    saved_chunks = 0

    for content, page_num in text_by_page:
        words = content.split()
        # Reagrupamos las palabras en bloques con solapamiento
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text.strip()) < 20:
                continue
                
            # Agregamos contexto visual al fragmento para que la IA sepa su origen
            formatted_content = f"[Archivo: {filename} | Pág: {page_num}]\n{chunk_text}"
            
            # 3. Guardamos en la memoria semántica usando las funciones existentes
            tags_info = f"file_upload:{filename}"
            
            # CORRECCIÓN DE IMPORTACIÓN: Importamos el módulo completo para evitar el ImportError
            import tools.memory as memory_module
            sb = memory_module.get_supabase()
            
            if sb:
                try:
                    # Accedemos de forma directa y segura al modelo y sus funciones sin colisiones
                    embedding_vector = memory_module.model.encode(formatted_content).tolist()
                    data = {
                        "content": formatted_content,
                        "source": "file_upload",
                        "tags": tags_info,
                        "embedding": embedding_vector,
                        "filename": filename,
                        "page_number": page_num
                    }
                    sb.table("knowledge").insert(data).execute()
                    saved_chunks += 1
                except Exception as ex:
                    print(f"[file_processor] Error inyectando chunk: {ex}")

    return saved_chunks
