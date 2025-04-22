#!/usr/bin/env python3
"""
Este arquivo configura a instância do Celery para ser usada nos workers.
"""
import os
import sys

# Adicionar o diretório raiz ao path do Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from extensions import celery as celery_app, db
from config import Config

# Criar uma aplicação Flask minimalista para o Celery
flask_app = Flask(__name__)
flask_app.config.from_object(Config)

# Inicializar o SQLAlchemy com o app Flask
db.init_app(flask_app)

# Configurar o Celery para usar este app
celery_app.conf.update(flask_app.config)

class ContextTask(celery_app.Task):
    """Classe de tarefa personalizada que garante que as tarefas sejam executadas 
    dentro de um contexto de aplicação Flask."""
    
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)

# Substitui a classe Task padrão pelo nosso ContextTask personalizado
celery_app.Task = ContextTask

# Importar as tarefas explicitamente para registrá-las
import tasks.plan_tasks

# Esta é a instância que o comando 'celery -A celery_worker.celery' irá procurar
celery = celery_app