# app/__init__.py
import sys
import os

# Configurar path do Python para encontrar módulos locais
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
# Use importações relativas para compatibilidade entre Flask e Celery
from config import Config
from extensions import db, ma, migrate, jwt, init_celery

# Importar modelos no nível principal do módulo para evitar importações circulares
# mas somente após as extensões serem definidas
import models

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensões
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    celery = init_celery(app)
    app.celery = celery

    # Importar e registrar Blueprints
    from routes.questionnaire import questionnaire_bp
    from routes.plans import plans_bp
    
    # Registrar Blueprints
    app.register_blueprint(questionnaire_bp)
    app.register_blueprint(plans_bp)
    
    # Registrar comandos CLI
    from commands import register_commands
    register_commands(app)

    return app