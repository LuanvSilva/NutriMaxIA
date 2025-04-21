from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from celery import Celery
import os
from sqlalchemy import MetaData

# Criar um objeto MetaData com as convenções adequadas
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)

# Inicializar SQLAlchemy com extend_existing=True
db = SQLAlchemy(metadata=metadata)

# Configurar tabelas para extend_existing
def setup_sqlalchemy_tables():
    from sqlalchemy import event
    
    @event.listens_for(db.metadata, 'before_create')
    def receive_before_create(target, connection, **kw):
        for table in target.tables.values():
            table.extend_existing = True

setup_sqlalchemy_tables()

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