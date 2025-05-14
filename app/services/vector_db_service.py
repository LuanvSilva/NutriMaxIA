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
        """
        Realiza busca vetorial por similaridade e aplica filtros opcionais.
        
        Args:
            query_text: Texto de consulta para buscar chunks similares
            k: Número de resultados a retornar
            filters: Dicionário com filtros a aplicar nos metadados
                    Exemplos: 
                    - {'type': 'food'} -> metadata_json->>'type' = 'food'
                    - {'tags': ['lowcarb', 'keto']} -> metadata_json->'tags' ? 'lowcarb' OR metadata_json->'tags' ? 'keto'
        
        Returns:
            Lista de chunks relevantes com seus metadados e similaridade
        """
        if not self.kb_service.embedding_model:
            logger.error("Modelo de embedding não disponível para busca.")
            return []

        try:
            # Gerar embedding da consulta
            query_embedding = self.kb_service.generate_embeddings([query_text])[0]
            
            # Construir a base da consulta SQL com conversão explícita para o tipo VECTOR
            base_query = """
                SELECT id, chunk_text, metadata_json, 1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
                FROM kb_chunks
                WHERE kb_version = :kb_version
                {filter_conditions}
                ORDER BY embedding <=> CAST(:query_embedding AS vector)
                LIMIT :k
            """
            
            params = {
                "query_embedding": query_embedding,
                "kb_version": self.kb_version,
                "k": k
            }
            
            # Adicionar condições de filtro, se houver
            filter_conditions = ""
            if filters and isinstance(filters, dict):
                filter_clauses = []
                
                for key, value in filters.items():
                    if isinstance(value, list):
                        # Para valores em lista, usamos condição IN ou contains @> para arrays JSON
                        filter_param = f"filter_{key}"
                        if key == 'tags' or key == 'equipment':
                            # Para campos que são arrays no JSON, usamos o operador ? (contains)
                            or_conditions = []
                            for i, item in enumerate(value):
                                param_name = f"{filter_param}_{i}"
                                params[param_name] = item
                                or_conditions.append(f"metadata_json->'tags' ? :{param_name}")
                            
                            if or_conditions:
                                filter_clauses.append(f"({' OR '.join(or_conditions)})")
                        else:
                            # Para campos regulares, usamos IN
                            params[filter_param] = value
                            filter_clauses.append(f"metadata_json->>'{key}' IN (:{filter_param})")
                    else:
                        # Para valores simples, usamos igualdade
                        filter_param = f"filter_{key}"
                        params[filter_param] = value
                        filter_clauses.append(f"metadata_json->>'{key}' = :{filter_param}")
                
                if filter_clauses:
                    filter_conditions = "AND " + " AND ".join(filter_clauses)
            
            # Construir a consulta final
            final_query = text(base_query.format(filter_conditions=filter_conditions))
            
            # Executar a consulta
            results = db.session.execute(final_query, params).fetchall()
            
            # Formatar resultados
            relevant_chunks = []
            for row in results:
                chunk = {
                    "id": str(row.id),
                    "chunk_text": row.chunk_text,
                    "metadata": row.metadata_json, 
                    "similarity": float(row.similarity)
                }
                relevant_chunks.append(chunk)
            
            logger.debug(f"Busca para '{query_text[:50]}...' retornou {len(relevant_chunks)} chunks" +
                        (f" com filtros: {filters}" if filters else ""))
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Erro na busca vetorial: {str(e)}", exc_info=True)
            return []