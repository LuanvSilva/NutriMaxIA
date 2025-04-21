# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-forte'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost/nutritrain_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configurações para APIs externas
    # OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') # Comentado/Removido
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') # Nova chave

    # Configurações Celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'

    # Configurações RAG
    EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
    EMBEDDING_DIM = 384 # Dimensão para o modelo acima
    VECTOR_DB_SEARCH_K = 5
    KB_FILE_PATH = os.path.join(os.path.dirname(__file__), 'kb', 'knowledge_base_v1.0.0.json') # Ajuste a versão se necessário
    KB_VERSION = "1.0.0" # Gerenciar versionamento

    # Configurações específicas do LLM
    LLM_PROVIDER = "google" # Adicionado para facilitar a troca futura
    GEMINI_MODEL_NAME = os.environ.get('GEMINI_MODEL_NAME', 'gemini-1.5-flash') # Ou 'gemini-pro' ou versão mais recente
    # Parâmetros de geração (podem ser ajustados)
    LLM_TEMPERATURE = 0.3
    LLM_MAX_OUTPUT_TOKENS = 4096 # Ajuste conforme necessidade e limites do modelo

    # Configurações de segurança do Gemini (ajuste conforme necessário)
    # BLOCK_NONE, BLOCK_ONLY_HIGH, BLOCK_MEDIUM_AND_ABOVE, BLOCK_LOW_AND_ABOVE
    GEMINI_SAFETY_SETTINGS = {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_MEDIUM_AND_ABOVE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_MEDIUM_AND_ABOVE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_MEDIUM_AND_ABOVE',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_MEDIUM_AND_ABOVE',
    }