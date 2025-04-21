import os
from app.config import Config

def get_current_kb_version():
    """
    Retorna a versão atual da knowledge base configurada.
    """
    return Config.KB_VERSION