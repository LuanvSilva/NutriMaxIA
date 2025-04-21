import sys
import os

# Adicionar o diretório raiz ao path do Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from models import KnowledgeBaseChunk
from sqlalchemy import text
from services.knowledge_base_service import KnowledgeBaseService # Para gerar embedding da query
import logging

logger = logging.getLogger(__name__)

class VectorDBService:
    def __init__(self, kb_version):
        self.kb_version = kb_version
        # Compartilha o mesmo modelo de embedding carregado pelo KnowledgeBaseService
        # Idealmente, injetar via dependency injection ou usar um singleton
        self.kb_service = KnowledgeBaseService(kb_version) # Reutiliza para o embedding_model

    def index_kb_chunks(self):
        """Processa a KB e insere/atualiza os chunks e embeddings no DB."""
        if not self.kb_service.embedding_model:
             logger.error("Modelo de embedding não disponível para indexação.")
             return

        logger.info(f"Iniciando indexação da KB versão {self.kb_version}")
        chunks_data = self.kb_service.get_all_chunks_for_indexing()
        texts_to_embed = [chunk['chunk_text'] for chunk in chunks_data]

        if not texts_to_embed:
            logger.warning("Nenhum chunk encontrado para indexar.")
            return

        embeddings = self.kb_service.generate_embeddings(texts_to_embed)

        # Limpar chunks antigos desta versão (opcional, mas recomendado)
        db.session.query(KnowledgeBaseChunk).filter_by(kb_version=self.kb_version).delete()
        db.session.commit()

        # Inserir novos chunks
        new_chunks = []
        for i, chunk_info in enumerate(chunks_data):
            new_chunk = KnowledgeBaseChunk(
                kb_version=self.kb_version,
                chunk_text=chunk_info['chunk_text'],
                metadata_json=chunk_info['metadata'],
                embedding=embeddings[i]
            )
            new_chunks.append(new_chunk)

        db.session.add_all(new_chunks)
        db.session.commit()
        logger.info(f"Indexação da KB versão {self.kb_version} concluída. {len(new_chunks)} chunks adicionados.")


    def search(self, query_text, k=5, filters=None):
        """Busca os k chunks mais similares à query_text, com filtros opcionais."""
        if not self.kb_service.embedding_model:
             logger.error("Modelo de embedding não disponível para busca.")
             return []

        query_embedding = self.kb_service.generate_embeddings([query_text])[0]

        # Exemplo de consulta com pgvector (usando distância de cosseno)
        # 1 - (embedding <=> query_embedding) é a similaridade de cosseno
        # A cláusula WHERE pode ser usada para filtros nos metadados
        # É crucial ter um índice vetorial (ex: IVFFlat ou HNSW) na coluna 'embedding' para performance
        sql_query = text("""
            SELECT id, chunk_text, metadata_json, 1 - (embedding <=> :query_embedding) AS similarity
            FROM knowledge_base_chunk
            WHERE kb_version = :kb_version
            -- Aqui podem entrar filtros adicionais baseados em 'filters' e metadata_json
            -- Exemplo: AND metadata_json->>'type' = :type_filter
            ORDER BY embedding <=> :query_embedding
            LIMIT :k
        """)

        params = {
            "query_embedding": str(query_embedding), # pgvector espera string ou lista
            "kb_version": self.kb_version,
            "k": k
        }
        # Adicionar parâmetros de filtro se 'filters' for fornecido

        results = db.session.execute(sql_query, params).fetchall()

        # Formatar resultados
        relevant_chunks = [
            {"id": str(row.id), "chunk_text": row.chunk_text, "metadata": row.metadata_json, "similarity": row.similarity}
            for row in results
        ]
        logger.debug(f"Busca vetorial para '{query_text[:50]}...' retornou {len(relevant_chunks)} chunks.")
        return relevant_chunks