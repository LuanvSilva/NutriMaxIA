import json
import sys
import os

# Adicionar o diretório raiz ao path do Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
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
        """
        Gera chunks da base de conhecimento para indexação eficiente.
        Cada seção da KB é processada de maneira específica para maximizar 
        a qualidade da recuperação.
        """
        chunks = []
        kb_data = self.knowledge_base
        
        # 1. Bibliotecas de dados detalhados
        biblioteca = kb_data.get('bibliotecas_dados_detalhadas', {})
        
        # 1.1. Processar alimentos
        for food in biblioteca.get('alimentos', []):
            nome = food.get('nome_pt', '')
            grupo = food.get('grupo_alimentar', '')
            descricao = food.get('observacoes', '')
            tags = ', '.join(food.get('tags', []))
            calorias = food.get('informacao_nutricional', {}).get('calorias_por_100g', '')
            proteinas = food.get('informacao_nutricional', {}).get('proteinas_g', '')
            carbos = food.get('informacao_nutricional', {}).get('carboidratos_g', '')
            gorduras = food.get('informacao_nutricional', {}).get('gorduras_g', '')
            
            text = f"""Alimento: {nome}. Grupo: {grupo}.
Informações nutricionais por 100g: Calorias: {calorias}, Proteínas: {proteinas}g, Carboidratos: {carbos}g, Gorduras: {gorduras}g. 
Descrição: {descricao}. Tags: {tags}"""
            
            metadata = {
                'type': 'food',
                'id': food.get('id'),
                'grupo': grupo,
                'tags': food.get('tags', [])
            }
            chunks.append({'chunk_text': text, 'metadata': metadata})

        # 1.2. Processar exercícios
        for exercise in biblioteca.get('exercicios', []):
            nome = exercise.get('nome_pt', '')
            musculo = exercise.get('musculo_primario', '')
            tipo = exercise.get('tipo_exercicio', '')
            nivel = exercise.get('nivel_dificuldade', '')
            equipamento = ', '.join(exercise.get('equipamento', []))
            instrucoes = exercise.get('instrucoes_execucao', '')
            
            text = f"""Exercício: {nome}. Músculo Primário: {musculo}. Tipo: {tipo}.
Nível: {nivel}. Equipamento: {equipamento}.
Instruções: {instrucoes}"""
            
            metadata = {
                'type': 'exercise',
                'id': exercise.get('id'),
                'muscle_group': musculo,
                'level': nivel,
                'equipment': exercise.get('equipamento', [])
            }
            chunks.append({'chunk_text': text, 'metadata': metadata})

        # 2. Processar regras de nutrição
        regras_nutricao = kb_data.get('regras_nutricao', {})
        
        # 2.1. Cálculos calóricos e macronutrientes
        calculos = regras_nutricao.get('calculos_caloricos_e_macronutrientes', {})
        for calculo_key, calculo_value in calculos.items():
            if isinstance(calculo_value, dict):
                text = f"Regra de Cálculo Nutricional - {calculo_key}: {json.dumps(calculo_value, ensure_ascii=False)}"
                metadata = {'type': 'nutrition_rule', 'subtype': 'calculation', 'id': calculo_key}
                chunks.append({'chunk_text': text, 'metadata': metadata})
            elif isinstance(calculo_value, str):
                text = f"Regra de Cálculo Nutricional - {calculo_key}: {calculo_value}"
                metadata = {'type': 'nutrition_rule', 'subtype': 'calculation', 'id': calculo_key}
                chunks.append({'chunk_text': text, 'metadata': metadata})

        # 2.2. Restrições alimentares
        restricoes = regras_nutricao.get('restricoes_alimentares', {})
        for restricao_key, restricao_value in restricoes.items():
            if isinstance(restricao_value, dict) or isinstance(restricao_value, list):
                text = f"Restrição Alimentar - {restricao_key}: {json.dumps(restricao_value, ensure_ascii=False)}"
            else:
                text = f"Restrição Alimentar - {restricao_key}: {restricao_value}"
            metadata = {'type': 'nutrition_rule', 'subtype': 'restriction', 'id': restricao_key}
            chunks.append({'chunk_text': text, 'metadata': metadata})

        # 3. Processar protocolos de treino
        protocolos_treino = kb_data.get('protocolos_treino', {})
        
        for protocolo_key, protocolo_value in protocolos_treino.items():
            if isinstance(protocolo_value, dict) or isinstance(protocolo_value, list):
                text = f"Protocolo de Treino - {protocolo_key}: {json.dumps(protocolo_value, ensure_ascii=False)}"
            else:
                text = f"Protocolo de Treino - {protocolo_key}: {protocolo_value}"
            metadata = {'type': 'training_protocol', 'id': protocolo_key}
            chunks.append({'chunk_text': text, 'metadata': metadata})

        # 4. Processar avisos de segurança
        avisos = kb_data.get('protocolos_seguranca_avisos_obrigatorios', {})
        
        # 4.1. Disclaimers gerais
        disclaimers = avisos.get('disclaimers_gerais_saude', [])
        for i, disclaimer in enumerate(disclaimers):
            text = f"Disclaimer de Saúde #{i+1}: {disclaimer}"
            metadata = {'type': 'disclaimer', 'id': f'general_{i}'}
            chunks.append({'chunk_text': text, 'metadata': metadata})
        
        # 4.2. Avisos específicos
        avisos_especificos = avisos.get('avisos_por_condicao', {})
        for condicao, aviso in avisos_especificos.items():
            text = f"Aviso de Segurança para {condicao}: {aviso}"
            metadata = {'type': 'safety_warning', 'condition': condicao}
            chunks.append({'chunk_text': text, 'metadata': metadata})
            
        logger.info(f"Gerados {len(chunks)} chunks para indexação da KB versão {self.kb_version}")
        return chunks

    def generate_embeddings(self, texts):
        if not self.embedding_model:
            raise RuntimeError("Modelo de embedding não inicializado.")
        return self.embedding_model.encode(texts).tolist() # Retorna lista de vetores