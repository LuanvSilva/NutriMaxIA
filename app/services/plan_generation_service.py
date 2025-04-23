import json
import logging
import sys
import os

# Adicionar o diretório raiz ao path do Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.knowledge_base_service import KnowledgeBaseService
from services.vector_db_service import VectorDBService
from services.llm_service import LLMService
from config import Config

logger = logging.getLogger(__name__)

class PlanGenerationService:
    def __init__(self, kb_version=None):
        self.kb_version = kb_version or Config.KB_VERSION
        self.kb_service = KnowledgeBaseService(self.kb_version) # Para carregar disclaimers, etc.
        self.vector_db_service = VectorDBService(self.kb_version)
        self.llm_service = LLMService()
        self.output_template = {
            "plano_alimentar": {
                "calorias_diarias": 0,
                "macronutrientes": {
                    "proteinas_g": 0,
                    "carboidratos_g": 0,
                    "gorduras_g": 0
                },
                "refeicoes": []
            },
            "plano_treino": {
                "dias_semana": [],
                "nivel": "",
                "objetivo": "",
                "observacoes": ""
            },
            "avisos_especificos": []
        }

    def _create_query_from_user_data(self, user_data):
        """
        Cria consultas contextuais baseadas nos dados do usuário.
        Gera consultas específicas para diferentes aspectos do plano.
        """
        # Extração de dados do usuário
        objetivo = user_data.get('objetivo_principal', 'saude geral')
        nivel = user_data.get('nivel_experiencia_treino', 'iniciante')
        restricoes = user_data.get('restricoes_alimentares', [])
        preferencias = user_data.get('preferencias_alimentares', [])
        idade = user_data.get('idade', 30)
        sexo = user_data.get('sexo', '')
        peso = user_data.get('peso_kg', 70)
        altura = user_data.get('altura_cm', 170)
        
        # Verificar condições especiais
        condicoes_especiais = user_data.get('condicoes_especiais', [])
        
        # Construção de consulta de dieta
        diet_query = f"Plano alimentar para {sexo} de {idade} anos, {peso}kg, {altura}cm, "
        diet_query += f"{nivel} em treino, com objetivo de {objetivo}. "
        
        if restricoes:
            diet_query += f"Restrições alimentares: {', '.join(restricoes)}. "
            
        if preferencias:
            diet_query += f"Preferências alimentares: {', '.join(preferencias)}. "
            
        if condicoes_especiais:
            diet_query += f"Condições especiais: {', '.join(condicoes_especiais)}. "
            
        # Construção de consulta de treino
        training_query = f"Plano de treino para {nivel} com objetivo de {objetivo}. "
        training_query += f"Sexo: {sexo}, idade: {idade}, peso: {peso}kg, altura: {altura}cm. "
        
        if condicoes_especiais:
            training_query += f"Considerar condições especiais: {', '.join(condicoes_especiais)}. "
        
        # Combinar as consultas para recuperar informações relevantes
        # Usando uma única consulta combinada para aumentar a variedade de resultados
        combined_query = f"{diet_query} {training_query}"
        
        logger.debug(f"Query gerada: {combined_query}")
        return combined_query

    def _build_prompt(self, user_data, relevant_chunks):
        # Constrói o prompt final para o LLM
        context = "\n\n".join([chunk['chunk_text'] for chunk in relevant_chunks])

        # Instruções DETALHADAS e REFORÇADAS para o Gemini
        instructions = f"""
        **Instrução Crítica:** Sua única e exclusiva saída DEVE SER um objeto JSON válido, começando com '{{' e terminando com '}}'. Não inclua NENHUM texto antes ou depois do JSON, nem use blocos de código como ```json.

        **Sua Tarefa:** Você é um assistente especialista em nutrição e treino para academias no Brasil. Gere SUGESTÕES de plano alimentar e de treino INICIAIS com base ESTRITAMENTE nas informações do usuário e no CONTEXTO FORNECIDO abaixo.

        **Regras Essenciais:**
        1.  **Use APENAS o CONTEXTO FORNECIDO.** Não invente informações, alimentos, exercícios ou regras. Se algo não estiver no contexto, omita essa parte ou indique explicitamente a falta de informação *dentro do JSON de resposta*, se permitido pelo schema.
        2.  **Siga RIGOROSAMENTE** as regras de cálculo, faixas de macronutrientes, listas de alimentos permitidos/proibidos e estruturas de treino descritas no contexto.
        3.  **Respeite TODAS as restrições e preferências** do usuário (alergias, intolerâncias, vegetarianismo, etc.) encontradas nos dados do usuário e mapeadas pelas regras no contexto.
        4.  **Priorize a SEGURANÇA.** Inclua avisos relevantes DO CONTEXTO na seção 'avisos_especificos' do JSON, se aplicável à situação do usuário.
        5.  **Formato OBRIGATÓRIO:** Sua resposta DEVE ser APENAS um objeto JSON válido, sem comentários ou texto adicional, seguindo EXATAMENTE o schema abaixo:
            ```json
            {self.output_template}
            ```

        **Contexto da Base de Conhecimento (Fonte Exclusiva de Informação):**
        ---
        {context}
        ---

        **Dados do Usuário:**
        ---
        {json.dumps(user_data, indent=2, ensure_ascii=False)}
        ---

        **JSON de Resposta (Plano Sugerido - Comece com '{{' e termine com '}}'):**
        """ # Removido o ```json no final para evitar confusão da IA
        return instructions

    def _parse_and_validate_llm_response(self, response_text):
        # Tenta parsear o JSON da resposta do LLM
        # Valida contra o schema `self.output_template`
        # Separa plano_nutricional, plano_treino, warnings (se houver)
        # Retorna (plan_nutricional, plan_treino, warnings) ou lança erro se inválido
        # Placeholder:
        try:
            # Remover potenciais ```json ... ``` que a IA pode adicionar
            if response_text.strip().startswith("```json"):
                response_text = response_text.strip()[7:-3].strip()
            elif response_text.strip().startswith("```"):
                 response_text = response_text.strip()[3:-3].strip()

            parsed_json = json.loads(response_text)
            # TODO: Implementar validação de schema aqui (ex: usando jsonschema)
            plan_nutricional = parsed_json.get('plano_alimentar')
            plan_treino = parsed_json.get('plano_treino')
            warnings = parsed_json.get('avisos_especificos', []) # Avisos que a IA pode ter gerado do contexto
            return plan_nutricional, plan_treino, warnings
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON da IA: {e}\nResposta recebida:\n{response_text[:500]}...")
            raise ValueError("Resposta da IA não está em formato JSON válido.")
        except Exception as e:
            logger.error(f"Erro ao parsear/validar resposta da IA: {e}")
            raise ValueError(f"Erro ao processar resposta da IA: {e}")


    def _add_mandatory_disclaimers(self, generated_warnings):
        # Carrega os disclaimers obrigatórios da KB e os adiciona
        mandatory_disclaimers = self.kb_service.get_mandatory_disclaimers()
        # Evita duplicatas se a IA já incluiu algum por conta própria
        final_warnings = list(set(generated_warnings + mandatory_disclaimers))
        return final_warnings

    def generate_plan(self, user_data):
        """
        Gera um plano completo (nutricional e treino) para o usuário com base nos dados fornecidos.
        
        Args:
            user_data: Dicionário com informações do usuário
            
        Returns:
            Tupla com (plano_nutricional, plano_treino, avisos)
            
        Raises:
            ValueError: Se não houver dados suficientes ou ocorrer erro de validação
            ConnectionError: Se houver falha na comunicação com serviços externos
        """
        try:
            # 1. Criar consulta a partir dos dados do usuário
            query = self._create_query_from_user_data(user_data)
            
            # 2. Preparar filtros baseados em dados do usuário
            filters = {}
            
            # Filtros para restrições alimentares
            restricoes = user_data.get('restricoes_alimentares', [])
            condicoes = user_data.get('condicoes_especiais', [])
            
            # 3. Buscar chunks relevantes com diferentes estratégias para máxima cobertura
            
            # 3.1 Busca geral para contexto amplo
            relevant_chunks = self.vector_db_service.search(query, k=Config.VECTOR_DB_SEARCH_K)
            
            # 3.2 Busca específica para restrições alimentares (se houver)
            if restricoes:
                restricao_query = f"Restrições alimentares: {', '.join(restricoes)}"
                restriction_chunks = self.vector_db_service.search(
                    restricao_query, 
                    k=2,
                    filters={'type': 'nutrition_rule', 'subtype': 'restriction'}
                )
                relevant_chunks.extend(restriction_chunks)
            
            # 3.3 Busca específica para condições especiais (se houver)
            if condicoes:
                for condicao in condicoes:
                    condicao_query = f"Aviso de segurança para {condicao}"
                    safety_chunks = self.vector_db_service.search(
                        condicao_query,
                        k=2,
                        filters={'type': 'safety_warning'}
                    )
                    relevant_chunks.extend(safety_chunks)
            
            # 3.4 Verificar se temos chunks suficientes
            if not relevant_chunks:
                raise ValueError("Não foi possível encontrar informações relevantes na base de conhecimento.")
                
            # Remover potenciais duplicatas
            unique_chunks = []
            chunk_ids = set()
            for chunk in relevant_chunks:
                if chunk['id'] not in chunk_ids:
                    chunk_ids.add(chunk['id'])
                    unique_chunks.append(chunk)
            
            logger.info(f"Recuperados {len(unique_chunks)} chunks únicos para geração do plano")
            
            # 4. Construir o prompt
            prompt = self._build_prompt(user_data, unique_chunks)
            logger.debug(f"Prompt enviado para LLM: {prompt[:300]}...")
            
            # 5. Chamar a API do LLM com retry
            max_retries = 2
            current_retry = 0
            
            while current_retry <= max_retries:
                try:
                    raw_llm_response = self.llm_service.call_llm(prompt)
                    break
                except Exception as e:
                    current_retry += 1
                    if current_retry > max_retries:
                        logger.error(f"Falha após {max_retries} tentativas: {e}")
                        raise ConnectionError(f"Falha na comunicação com o serviço de IA após {max_retries} tentativas.")
                    logger.warning(f"Erro na tentativa {current_retry}, tentando novamente: {e}")
            
            # 6. Parsear, validar e adicionar disclaimers
            plan_nutricional, plan_treino, generated_warnings = self._parse_and_validate_llm_response(raw_llm_response)
            final_warnings = self._add_mandatory_disclaimers(generated_warnings)
            
            # 7. Log de sucesso e retorno
            logger.info(f"Plano gerado com sucesso: {len(plan_nutricional.get('refeicoes', []))} refeições, " 
                       f"{len(plan_treino.get('dias_semana', []))} dias de treino, {len(final_warnings)} avisos")
            
            return plan_nutricional, plan_treino, final_warnings
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro no formato JSON: {e}")
            raise ValueError(f"Erro ao processar resposta do serviço de IA: {e}")
            
        except ValueError as e:
            logger.error(f"Erro de validação: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Erro inesperado: {e}", exc_info=True)
            raise ValueError(f"Erro ao gerar plano: {str(e)}")