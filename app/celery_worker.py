#!/usr/bin/env python3
"""
Este arquivo configura a instância do Celery para ser usada nos workers.
"""
import os
import sys

# Adicionar o diretório raiz ao path do Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from extensions import celery as celery_app
from config import Config

# Importar as tarefas explicitamente para registrá-las
import tasks.plan_tasks

# Criar uma aplicação Flask minimalista para o Celery
app = Flask(__name__)
app.config.from_object(Config)

# Configurar o Celery com a aplicação Flask
celery_app.conf.update(app.config)

# Esta é a instância que o comando 'celery -A celery_worker.celery' irá procurar
celery = celery_app