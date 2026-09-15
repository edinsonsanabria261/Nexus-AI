"""
Módulo universal de extracción y segmentación de archivos (PDF, DOCX, XLSX, Código, Texto) para Nexus-AI
"""

import io
from pypdf import PdfReader
import docx2txt
import openpyxl

def process_and_index_file(file_contents: bytes, filename: str) -> int:
    """
    Procesa un archivo binario de CUALQUIER formato común (PDF, Word, Excel, Código), 
    extrae su texto y lo indexa semánticamente en Supabase usando la API externa de embeddings.
    """
    file_bytes_stream = io.BytesIO(file_contents)
    text_by_page = []
    fn_lower = filename.lower()
    
    # 1. EXTRACTOR MULTIFORMATO INTELIGENTE
    if fn_lower.endswith('.pdf'):
        try:
            reader = PdfReader(file_bytes_stream)
            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_by_page.append((page_text, page_num))
        except Exception as e:
            print(f"[file_processor] Error leyendo PDF ({filename}): {e}")
            return 0
            
    elif fn_lower.endswith('.docx') or fn_lower.endswith('.doc'):
        try:
            text = docx2txt.process(file_bytes_stream)
            if text and text.strip():
                text_by_page.append((text, 1))
        except Exception as e:
            print(f"[file_processor] Error leyendo Word ({filename}): {e}")
            return 0

    elif fn_lower.endswith('.xlsx'):
        try:
            wb = openpyxl.load_workbook(file_bytes_stream, data_only=True)
            excel_text_parts = []
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                excel_text_parts.append(f"--- Hoja: {sheet} ---")
                for row in ws.iter_rows(values_only=True):
                    row_text = "\t".join([str(cell) for cell in row if cell is not None])
                    if row_text.strip():
                        excel_text_parts.append(row_text)
            full_excel_text = "\n".join(excel_text_parts)
            if full_excel_text.strip():
                text_by_page.append((full_excel_text, 1))
        except Exception as e:
            print(f"[file_processor] Error leyendo Excel ({filename}): {e}")
            return 0
    else:
        plain_text = ""
        encodings_to_try = ["utf-8", "latin-1", "iso-8859-15", "cp1252"]
        for enc in encodings_to_try:
            try:
                plain_text = file_contents.decode(enc)
                break
            except UnicodeDecodeError:
                continue
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

    # 2. SEGMENTACIÓN SEMÁNTICA (CHUNKING) Y CARGA A SUPABASE
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
            
            import tools.memory as memory_module
            sb = memory_module.get_supabase()
            
            if sb:
                try:
                    # Llamamos a la nueva función externa que no consume RAM de tu Render
                    embedding_vector = memory_module.obtener_embedding_externo(formatted_content)
                    
                    if embedding_vector:
                        data = {
                            "content": formatted_content,
                            "source": "file_upload",
                            "tags": tags_info,
                            "embedding": embedding_vector,
                            "filename": filename,
                            "page_number": int(page_num)
                        }
                        sb.table("knowledge").insert(data).execute()
                        saved_chunks += 1
                except Exception as ex:
                    print(f"[file_processor] Error inyectando chunk en Supabase: {ex}")

    return saved_chunks
