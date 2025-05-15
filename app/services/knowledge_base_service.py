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
            
            # Correção na extração dos dados nutricionais
            calorias = food.get('energia_kcal_100g', '') # Acessa diretamente energia_kcal_100g
            macros = food.get('macros_100g', {})
            proteinas = macros.get('proteina_g', '')
            carbos = macros.get('carboidrato_g', '')
            gorduras = macros.get('gordura_total_g', '') # Assumindo que 'gordura_total_g' é o campo correto para gorduras
            
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
            tipo_exercicio = exercise.get('tipo_exercicio', '') # Nome da variável corrigido para consistência
            nivel = exercise.get('nivel_dificuldade', '')
            equipamento = ', '.join(exercise.get('equipamento', []))
            instrucoes = exercise.get('instrucoes_execucao', '')
            
            text = f"""Exercício: {nome}. Músculo Primário: {musculo}. Tipo: {tipo_exercicio}.
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

        # --- NOVA LÓGICA PARA PROCESSAR REGRAS DE NUTRIÇÃO E TREINO ---
        principios_fundamentais = kb_data.get('principios_fundamentais', {})

        # 2. Processar Regras de Nutrição de 'principios_fundamentais.nutricao'
        regras_nutricao_data = principios_fundamentais.get('nutricao', {})
        for nome_regra_nutricao, conteudo_regra_nutricao in regras_nutricao_data.items():
            # Se o conteúdo for um dicionário ou lista, serializa para JSON. Senão, usa como string.
            if isinstance(conteudo_regra_nutricao, (dict, list)):
                texto_conteudo = json.dumps(conteudo_regra_nutricao, ensure_ascii=False, indent=2)
            else:
                texto_conteudo = str(conteudo_regra_nutricao)
            
            chunk_text = f"Regra de Nutrição - {nome_regra_nutricao.replace('_', ' ').title()}:\\n{texto_conteudo}"
            metadata = {
                'type': 'nutrition_rule',
                'subtype': nome_regra_nutricao, # ex: 'calculo_necessidades_energeticas'
                'id': f"nutri_rule_{nome_regra_nutricao}" 
            }
            chunks.append({'chunk_text': chunk_text, 'metadata': metadata})

        # 3. Processar Protocolos de Treino de 'principios_fundamentais.treino'
        protocolos_treino_data = principios_fundamentais.get('treino', {})
        for nome_protocolo_treino, conteudo_protocolo_treino in protocolos_treino_data.items():
            # Lida com a chave "estruturas_divisao_treino (Splits)" e outras
            nome_protocolo_formatado = nome_protocolo_treino.replace('_', ' ').title()
            if "(Splits)" in nome_protocolo_formatado:
                 nome_protocolo_formatado = nome_protocolo_formatado.replace("(Splits)", "Splits")
                 
            if isinstance(conteudo_protocolo_treino, (dict, list)):
                texto_conteudo = json.dumps(conteudo_protocolo_treino, ensure_ascii=False, indent=2)
            else:
                texto_conteudo = str(conteudo_protocolo_treino)

            chunk_text = f"Protocolo de Treino - {nome_protocolo_formatado}:\\n{texto_conteudo}"
            metadata = {
                'type': 'training_protocol',
                'subtype': nome_protocolo_treino, # ex: 'variaveis_treino' ou 'estruturas_divisao_treino (Splits)'
                'id': f"train_proto_{nome_protocolo_treino.split(' ')[0]}" # Id simplificado
            }
            chunks.append({'chunk_text': chunk_text, 'metadata': metadata})
        
        # 4. Processar avisos de segurança (Mantém como está, mas verifica a fonte na KB)
        # A KB parece ter 'protocolos_seguranca_avisos_obrigatorios' no nível raiz.
        avisos_data = kb_data.get('protocolos_seguranca_avisos_obrigatorios', {})
        
        # 4.1. Disclaimers gerais
        disclaimers = avisos_data.get('disclaimers_gerais_saude', [])
        for i, disclaimer in enumerate(disclaimers):
            text = f"Disclaimer de Saúde #{i+1}: {disclaimer}"
            metadata = {'type': 'disclaimer', 'id': f'general_disclaimer_{i+1}'}
            chunks.append({'chunk_text': text, 'metadata': metadata})
        
        # 4.2. Avisos específicos por condição
        avisos_especificos = avisos_data.get('avisos_por_condicao', {}) # Esta chave pode não existir na KB fornecida
                                                                        # A KB tem 'regras_perfil_usuario_mapeamento.condicoes_saude_declaradas'
                                                                        # que contém 'aviso_forte' ou 'acao_imediata'.
                                                                        # Vou adaptar para usar 'condicoes_saude_declaradas' se 'avisos_por_condicao' não existir.

        # Tentativa de obter avisos de segurança da estrutura 'regras_perfil_usuario_mapeamento.condicoes_saude_declaradas'
        # se 'protocolos_seguranca_avisos_obrigatorios.avisos_por_condicao' não estiver populado.
        if not avisos_especificos:
            logger.info("A seção 'protocolos_seguranca_avisos_obrigatorios.avisos_por_condicao' não foi encontrada ou está vazia. Tentando extrair avisos de 'regras_perfil_usuario_mapeamento.condicoes_saude_declaradas'.")
            condicoes_mapeadas = kb_data.get('regras_perfil_usuario_mapeamento', {}).get('condicoes_saude_declaradas', [])
            for cond_map in condicoes_mapeadas:
                condicao_nome = cond_map.get('condicao') 
                aviso = cond_map.get('aviso_forte') or cond_map.get('diretriz') # Prioriza aviso_forte, senão usa diretriz
                acao_imediata = cond_map.get('acao_imediata')

                if condicao_nome and (aviso or acao_imediata == 'referenciar_profissional'):
                    full_warning_text = f"Aviso de Segurança para {condicao_nome}: "
                    if aviso:
                        full_warning_text += aviso
                    if acao_imediata == 'referenciar_profissional':
                        full_warning_text += " Requer atenção profissional imediata. Sugestões da IA podem não ser apropriadas."
                    
                    chunks.append({
                        'chunk_text': full_warning_text.strip(),
                        'metadata': {'type': 'safety_warning', 'condition': condicao_nome, 'id': f'safety_{condicao_nome}'}
                    })
        else: # Processa 'avisos_por_condicao' se existir
            for condicao, aviso_texto in avisos_especificos.items():
                text = f"Aviso de Segurança para {condicao}: {aviso_texto}"
                metadata = {'type': 'safety_warning', 'condition': condicao, 'id': f'safety_direct_{condicao}'}
                chunks.append({'chunk_text': text, 'metadata': metadata})
            
        logger.info(f"Gerados {len(chunks)} chunks para indexação da KB versão {self.kb_version}")
        return chunks

    def generate_embeddings(self, texts):
        if not self.embedding_model:
            raise RuntimeError("Modelo de embedding não inicializado.")
        return self.embedding_model.encode(texts).tolist() # Retorna lista de vetores