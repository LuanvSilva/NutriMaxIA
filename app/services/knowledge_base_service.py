import json
from app.config import Config
import os
import logging
from sentence_transformers import SentenceTransformer # Exemplo de modelo de embedding

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self, kb_version):
        self.kb_version = kb_version
        self.kb_file_path = self._get_kb_file_path(kb_version)
        self.knowledge_base = self._load_kb()
        # Inicializar modelo de embedding aqui para ser usado no chunking/vetorização e busca
        # Considerar carregar apenas uma vez (singleton ou cache) para performance
        try:
            self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL_NAME)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            # Verificar se a dimensão corresponde ao campo Vector no model
            if self.embedding_dim != 384: # Exemplo, ajustar conforme modelo e DB
                 logger.warning(f"Dimensão do modelo ({self.embedding_dim}) difere do esperado (384)")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo de embedding {Config.EMBEDDING_MODEL_NAME}: {e}")
            self.embedding_model = None


    def _get_kb_file_path(self, version):
        # Lógica para encontrar o arquivo JSON correto baseado na versão
        # Exemplo simples:
        filename = f"knowledge_base_v{version}.json"
        path = os.path.join(os.path.dirname(__file__), '..', 'kb', filename)
        if not os.path.exists(path):
            # Tenta o path padrão se a versão específica não for encontrada
             path = Config.KB_FILE_PATH
             if not os.path.exists(path):
                  raise FileNotFoundError(f"Arquivo da Base de Conhecimento não encontrado: {filename} ou {Config.KB_FILE_PATH}")
        return path


    def _load_kb(self):
        try:
            with open(self.kb_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar Base de Conhecimento ({self.kb_file_path}): {e}")
            raise

    def get_mandatory_disclaimers(self):
        # Acessa a seção de disclaimers no JSON carregado
        return self.knowledge_base.get('protocolos_seguranca_avisos_obrigatorios', {}).get('disclaimers_gerais_saude', [])

    def get_all_chunks_for_indexing(self):
        # Lógica para percorrer o self.knowledge_base e dividi-lo em chunks
        # Retorna uma lista de dicionários: [{'chunk_text': '...', 'metadata': {...}}, ...]
        # Esta lógica pode ser complexa dependendo da estrutura do JSON
        chunks = []
        kb_data = self.knowledge_base

        # Exemplo simplificado para alimentos:
        for food in kb_data.get('bibliotecas_dados_detalhadas', {}).get('alimentos', []):
            text = f"Alimento: {food.get('nome_pt', '')}. Grupo: {food.get('grupo_alimentar', '')}. Descrição: {food.get('observacoes', '')}. Tags: {', '.join(food.get('tags', []))}"
            metadata = {'type': 'food', 'id': food.get('id'), 'tags': food.get('tags', [])}
            chunks.append({'chunk_text': text, 'metadata': metadata})

        # Exemplo simplificado para exercícios:
        for exercise in kb_data.get('bibliotecas_dados_detalhadas', {}).get('exercicios', []):
             text = f"Exercício: {exercise.get('nome_pt', '')}. Músculo Primário: {exercise.get('musculo_primario', '')}. Tipo: {exercise.get('tipo_exercicio')}. Nível: {exercise.get('nivel_dificuldade')}. Equipamento: {', '.join(exercise.get('equipamento',[]))}"
             metadata = {'type': 'exercise', 'id': exercise.get('id'), 'muscle_group': exercise.get('musculo_primario'), 'level': exercise.get('nivel_dificuldade'), 'equipment': exercise.get('equipamento', [])}
             chunks.append({'chunk_text': text, 'metadata': metadata})


        # ... Adicionar lógica para chunking de princípios, regras, etc. ...

        return chunks

    def generate_embeddings(self, texts):
        if not self.embedding_model:
            raise RuntimeError("Modelo de embedding não inicializado.")
        return self.embedding_model.encode(texts).tolist() # Retorna lista de vetores