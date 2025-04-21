# app/models.py
import sys
import os

# Adicionar o diretório atual ao path do Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from sqlalchemy.dialects.postgresql import JSONB, UUID
from pgvector.sqlalchemy import Vector # Importar tipo Vector
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index # Para índices

# Definir a dimensão diretamente aqui por simplicidade ou buscar da config
# Se usar all-MiniLM-L6-v2: 384
# Se usar text-embedding-ada-002 da OpenAI: 1536
# Se usar outro, ajuste a dimensão
EMBEDDING_DIMENSION = 384 # Ajuste conforme seu modelo de embedding

class Academia(db.Model):
    __tablename__ = 'academias'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = db.Column(db.String(120), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=True) # CNPJ formatado
    contato_email = db.Column(db.String(120))
    contato_telefone = db.Column(db.String(20))
    plano_assinatura_id = db.Column(db.String(50)) # Pode ser FK para outra tabela no futuro
    status = db.Column(db.String(20), default='ativo', nullable=False)
    codigo_acesso_membros = db.Column(db.String(10), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuarios = db.relationship('User', backref='academia', lazy=True)

class User(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    academia_id = db.Column(UUID(as_uuid=True), db.ForeignKey('academias.id'), nullable=False)
    status = db.Column(db.String(20), default='ativo', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    questionnaire_responses = db.relationship('QuestionnaireResponse', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    generated_plans = db.relationship('GeneratedPlan', backref='user', lazy='dynamic', cascade="all, delete-orphan")

    # Índice único por email dentro de uma academia
    __table_args__ = (db.UniqueConstraint('email', 'academia_id', name='uq_user_email_academia'),)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class QuestionnaireResponse(db.Model):
    __tablename__ = 'questionario_respostas'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True)
    answers_json = db.Column(JSONB, nullable=False)
    submitted_at = db.Column(db.DateTime, server_default=db.func.now())
    kb_version_used = db.Column(db.String(50), index=True)

    generated_plan = db.relationship('GeneratedPlan', backref='questionnaire', uselist=False) # One-to-one

class GeneratedPlan(db.Model):
    __tablename__ = 'planos_gerados'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True)
    questionnaire_id = db.Column(UUID(as_uuid=True), db.ForeignKey('questionario_respostas.id', ondelete='CASCADE'), nullable=False, unique=True, index=True) # Garante um plano por questionário
    plan_nutritional_json = db.Column(JSONB)
    plan_training_json = db.Column(JSONB)
    warnings_json = db.Column(JSONB)
    generation_status = db.Column(db.String(50), default='PENDING', nullable=False, index=True)
    generated_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text, nullable=True)
    kb_version_used = db.Column(db.String(50), index=True)
    task_id = db.Column(db.String(100), nullable=True, index=True) # Para rastrear a tarefa Celery

class KnowledgeBaseChunk(db.Model):
    __tablename__ = 'kb_chunks'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kb_version = db.Column(db.String(50), nullable=False, index=True)
    chunk_text = db.Column(db.Text, nullable=False)
    metadata_json = db.Column(JSONB, index=True) # Usar GIN index para JSONB
    embedding = db.Column(Vector(EMBEDDING_DIMENSION)) # Certifique-se que EMBEDDING_DIMENSION está correto

    # Adicionar índices para busca mais eficiente
    __table_args__ = (
        Index('ix_kb_chunks_metadata', metadata_json, postgresql_using='gin'),
        # O índice para a coluna de vetor geralmente é adicionado manualmente
        # via SQL após a criação da tabela, pois depende do tipo específico (HNSW, IVFFlat)
        # Ex: CREATE INDEX ON kb_chunks USING hnsw (embedding vector_cosine_ops);
        # OU CREATE INDEX ON kb_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        # Flask-Migrate pode não gerar isso automaticamente.
    )