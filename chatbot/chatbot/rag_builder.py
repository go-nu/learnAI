import sys
import time
import threading
from pathlib import Path


def _run_build(rag_config_id):
    from django.conf import settings
    from .models import RagConfig
    try:
        rag = RagConfig.objects.get(id=rag_config_id)
    except RagConfig.DoesNotExist:
        return
    rag.status = RagConfig.STATUS_PROCESSING
    rag.error_message = ''
    rag.save(update_fields=['status', 'error_message'])
    start = time.time()
    try:
        BASE_DIR = Path(settings.BASE_DIR)
        if str(BASE_DIR) not in sys.path:
            sys.path.insert(0, str(BASE_DIR))
        import rag_pdf_tables as rpt
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        source_path = BASE_DIR / rag.source_file_path
        result_dir = str(BASE_DIR / 'rag_db' / str(rag.rag_id))
        text_docs, table_docs = rpt.load_pdf_with_tables(str(source_path))
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag.chunk_size,
            chunk_overlap=rag.chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""],
        )
        split_docs = splitter.split_documents(text_docs)
        for i, chunk in enumerate(split_docs):
            chunk.metadata["chunk_id"] = i
        all_docs = split_docs + table_docs
        rag.chunk_count = len(all_docs)
        rag.save(update_fields=['chunk_count'])
        embeddings = rpt.get_bge_m3_embeddings()
        rpt.build_vectordb(all_docs, embeddings, persist_dir=result_dir)
        elapsed = int((time.time() - start) * 1000)
        rag.status = RagConfig.STATUS_READY
        rag.result_file_path = f'rag_db/{rag.rag_id}'
        rag.build_time_ms = elapsed
        rag.save(update_fields=['status', 'result_file_path', 'build_time_ms', 'error_message'])
    except Exception as exc:
        elapsed = int((time.time() - start) * 1000)
        try:
            rag.refresh_from_db()
            rag.status = RagConfig.STATUS_ERROR
            rag.error_message = str(exc)[:2000]
            rag.build_time_ms = elapsed
            rag.save(update_fields=['status', 'error_message', 'build_time_ms'])
        except Exception:
            pass


def build_rag_async(rag_config_id):
    t = threading.Thread(target=_run_build, args=(rag_config_id,), daemon=True)
    t.start()
