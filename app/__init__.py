# app/__init__.py
from flask import Flask
from app.config import Config
from app.extensions import db, ma, migrate, jwt, init_celery

# Importar modelos no nível principal do módulo para evitar importações circulares
# mas somente após as extensões serem definidas
from app import models

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
    from app.routes.questionnaire import questionnaire_bp
    from app.routes.plans import plans_bp
    
    # Registrar Blueprints
    app.register_blueprint(questionnaire_bp)
    app.register_blueprint(plans_bp)
    
    # Registrar comandos CLI
    from app.commands import register_commands
    register_commands(app)

    return app