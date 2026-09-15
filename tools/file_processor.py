"""
Módulo avanzado de extracción y segmentación de archivos (PDF, Código, Texto) para Nexus-AI
"""

import io
from pypdf import PdfReader

def process_and_index_file(file_contents: bytes, filename: str) -> int:
    """
    Procesa un archivo binario, extrae su texto por páginas y lo indexa semánticamente en Supabase.
    Devuelve la cantidad de bloques guardados con éxito. Incorpora tolerancia a fallos de codificación.
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
        # SISTEMA COMPLETO DE TOLERANCIA PARA ARCHIVOS DE TEXTO Y CÓDIGO
        plain_text = ""
        # Lista de codificaciones a probar de forma secuencial si falla la primera
        encodings_to_try = ["utf-8", "latin-1", "iso-8859-15", "cp1252"]
        
        for enc in encodings_to_try:
            try:
                plain_text = file_contents.decode(enc)
                break  # Si tiene éxito, rompemos el bucle
            except UnicodeDecodeError:
                continue  # Si falla, intenta con la siguiente codificación
                
        # Si todo falla, forzamos decodificación ignorando caracteres rotos
        if not plain_text:
            try:
                plain_text = file_contents.decode("utf-8", errors="ignore")
            except Exception:
                print(f"[file_processor] Error fatal de decodificación en {filename}")
                return 0

        if plain_text.strip():
            text_by_page.append((plain_text, 1))

    if not text_by_page:
        return 0

    # 2. Segmentación en bloques semánticos (Chunking) con solapamiento
    chunk_size = 600
    overlap = 150
    saved_chunks = 0

    for content, page_num in text_by_page:
        words = content.split()
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text.strip()) < 20:
                continue
                
            formatted_content = f"[Archivo: {filename} | Pág: {page_num}]\n{chunk_text}"
            tags_info = f"file_upload:{filename}"
            
            # Importación segura bajo demanda del módulo de memoria
            import tools.memory as memory_module
            sb = memory_module.get_supabase()
            
            if sb:
                try:
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
                    print(f"[file_processor] Error inyectando chunk en Supabase: {ex}")

    return saved_chunks
