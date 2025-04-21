from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from celery import Celery
import os

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
jwt = JWTManager()

# Inicialização tardia do Celery para evitar importação circular
celery = Celery(__name__)

# Usar variáveis de ambiente diretamente aqui para evitar a importação circular com Config
broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
celery.conf.update(broker_url=broker_url, result_backend=result_backend)

def init_celery(app):
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery