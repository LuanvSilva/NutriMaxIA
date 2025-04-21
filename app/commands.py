import sys
import os
import click
from flask.cli import with_appcontext
from sqlalchemy import text

# Adicionar o diretório atual ao path do Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from services.knowledge_base_service import KnowledgeBaseService
from services.vector_db_service import VectorDBService
from config import Config

def register_commands(app):
    """Registra comandos CLI personalizados para a aplicação Flask"""
    
    @app.cli.command("init-db")
    @with_appcontext
    def init_db():
        """Executa o script SQL para inicializar o banco de dados"""
        try:
            # Caminho para o arquivo SQL
            sql_file = os.path.join(os.path.dirname(__file__), 'init-db.sql')
            
            # Le o conteúdo do arquivo
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            # Executa as queries
            db.session.execute(text(sql))
            db.session.commit()
            
            click.echo('Banco de dados inicializado com sucesso!')
            
        except Exception as e:
            db.session.rollback()
            click.echo(f'Erro ao inicializar o banco de dados: {e}', err=True)
    
    @app.cli.command("index-kb")
    @with_appcontext
    def index_kb():
        """Indexa a knowledge base no banco de dados vetorial"""
        try:
            # Usar a versão configurada
            kb_version = Config.KB_VERSION
            click.echo(f'Iniciando indexação da knowledge base versão {kb_version}...')
            
            # Inicializa o serviço e executa a indexação
            vector_db_service = VectorDBService(kb_version)
            vector_db_service.index_kb_chunks()
            
            click.echo('Indexação concluída com sucesso!')
            
        except Exception as e:
            click.echo(f'Erro ao indexar a knowledge base: {e}', err=True)
    
    @app.cli.command("create-user")
    @click.argument("nome")
    @click.argument("email")
    @click.argument("senha")
    @click.argument("academia_id")
    @with_appcontext
    def create_user(nome, email, senha, academia_id):
        """Cria um novo usuário no banco de dados"""
        from models import User
        
        try:
            # Cria o usuário
            user = User(
                nome=nome,
                email=email,
                academia_id=academia_id
            )
            user.set_password(senha)
            
            # Salva no banco
            db.session.add(user)
            db.session.commit()
            
            click.echo(f'Usuário {email} criado com sucesso!')
            
        except Exception as e:
            db.session.rollback()
            click.echo(f'Erro ao criar usuário: {e}', err=True)