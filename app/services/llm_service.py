# services/llm_service.py
import google.generativeai as genai
import sys
import os

# Adicionar o diretório raiz ao path do Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
import logging
import json # Para tentar corrigir JSON malformado

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("Chave da API Google Gemini não configurada.")
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            # Configurações de geração podem ser definidas aqui ou na chamada
            self.generation_config = genai.types.GenerationConfig(
                # candidate_count=1, # Geralmente queremos apenas 1 resposta
                # stop_sequences=['...'], # Se precisar parar em sequências específicas
                max_output_tokens=Config.LLM_MAX_OUTPUT_TOKENS,
                temperature=Config.LLM_TEMPERATURE
                # top_p=0.9, # Outros parâmetros de amostragem (opcional)
                # top_k=40   # Outros parâmetros de amostragem (opcional)
            )
            # Mapeia as strings de configuração para os enums da API
            self.safety_settings = {
                 genai.types.HarmCategory[key]: genai.types.HarmBlockThreshold[value]
                 for key, value in Config.GEMINI_SAFETY_SETTINGS.items()
            }

            self.model = genai.GenerativeModel(
                model_name=Config.GEMINI_MODEL_NAME,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            logger.info(f"Serviço LLM inicializado com o modelo Gemini: {Config.GEMINI_MODEL_NAME}")
        except Exception as e:
            logger.error(f"Falha ao configurar a API do Google Gemini: {e}", exc_info=True)
            raise RuntimeError(f"Não foi possível inicializar o serviço Gemini: {e}")

    def _clean_response_text(self, text):
        """Tenta limpar a resposta para extrair um JSON válido."""
        text = text.strip()
        # Remove ```json ... ``` ou ``` ... ``` se presentes
        if text.startswith("```json"):
            text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
        elif text.startswith("```"):
            text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

        # Tenta encontrar o primeiro '{' e o último '}'
        start_index = text.find('{')
        end_index = text.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            return text[start_index:end_index+1].strip()
        else:
            # Se não encontrar JSON claro, retorna o texto original para tentativa de parse
            return text.strip()


    def call_llm(self, prompt):
        """Chama a API do Gemini para gerar a resposta."""
        logger.debug(f"Enviando prompt para Gemini (modelo: {Config.GEMINI_MODEL_NAME}). Tamanho: {len(prompt)} chars.")
        try:
            # Para Gemini, o prompt é geralmente passado diretamente
            response = self.model.generate_content(prompt)

            # Tratamento de resposta bloqueada por segurança
            if not response.candidates:
                 # Tentar acessar 'prompt_feedback' para entender o motivo do bloqueio
                 block_reason = "Não especificado (sem candidatos)"
                 try:
                     if response.prompt_feedback and response.prompt_feedback.block_reason:
                         block_reason = response.prompt_feedback.block_reason.name
                     logger.warning(f"Resposta do Gemini bloqueada. Razão: {block_reason}")
                 except Exception:
                     logger.warning("Resposta do Gemini bloqueada, não foi possível obter a razão exata.")
                 raise ValueError(f"A resposta foi bloqueada devido a políticas de segurança: {block_reason}. Revise o prompt ou as configurações de segurança.")


            # Extrair o texto da resposta
            # Gemini pode retornar múltiplas partes, concatenamos se necessário
            raw_response_text = "".join(part.text for part in response.candidates[0].content.parts)

            logger.info(f"Chamada à API Gemini bem-sucedida. Modelo: {Config.GEMINI_MODEL_NAME}")
            # Tentativa de limpeza básica antes de retornar
            cleaned_response = self._clean_response_text(raw_response_text)
            logger.debug(f"Resposta limpa do Gemini (pré-parse): {cleaned_response[:500]}...")
            return cleaned_response

        except ValueError as ve: # Erro de segurança ou outro ValueError da nossa lógica
            logger.error(f"Erro de valor durante a chamada Gemini: {ve}")
            raise ve # Re-lança para ser tratado no serviço de geração
        except Exception as e:
            # Captura erros mais genéricos da API ou da biblioteca
            logger.error(f"Erro inesperado ao chamar Gemini API: {e}", exc_info=True)
            # Aqui podemos tentar identificar tipos específicos de erro se necessário
            # from google.api_core import exceptions as google_exceptions
            # if isinstance(e, google_exceptions.PermissionDenied): # Exemplo
            #     raise ConnectionError("Erro de permissão com a API Gemini. Verifique a chave.")
            raise RuntimeError(f"Erro inesperado ao comunicar com o serviço Gemini: {e}")