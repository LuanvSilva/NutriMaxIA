-- Habilitar a extensão pgvector (necessário para vetores de embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabela de academias
CREATE TABLE IF NOT EXISTS academias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(120) NOT NULL,
    cnpj VARCHAR(18) UNIQUE,
    contato_email VARCHAR(120),
    contato_telefone VARCHAR(20),
    plano_assinatura_id VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'ativo',
    codigo_acesso_membros VARCHAR(10) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_academias_codigo_acesso ON academias(codigo_acesso_membros);

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- Alterado de 128 para 255 caracteres
    academia_id UUID NOT NULL REFERENCES academias(id),
    status VARCHAR(20) NOT NULL DEFAULT 'ativo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    CONSTRAINT uq_user_email_academia UNIQUE(email, academia_id)
);
CREATE INDEX IF NOT EXISTS ix_usuarios_academia_id ON usuarios(academia_id);

-- Tabela de respostas de questionários
CREATE TABLE IF NOT EXISTS questionario_respostas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    answers_json JSONB NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    kb_version_used VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS ix_questionario_respostas_user_id ON questionario_respostas(user_id);
CREATE INDEX IF NOT EXISTS ix_questionario_respostas_kb_version ON questionario_respostas(kb_version_used);

-- Tabela de planos gerados
CREATE TABLE IF NOT EXISTS planos_gerados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    questionnaire_id UUID NOT NULL REFERENCES questionario_respostas(id) ON DELETE CASCADE,
    plan_nutritional_json JSONB,
    plan_training_json JSONB,
    warnings_json JSONB,
    generation_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    generated_at TIMESTAMP,
    error_message TEXT,
    kb_version_used VARCHAR(50),
    task_id VARCHAR(100),
    CONSTRAINT uq_planos_questionnaire_id UNIQUE(questionnaire_id)
);
CREATE INDEX IF NOT EXISTS ix_planos_gerados_user_id ON planos_gerados(user_id);
CREATE INDEX IF NOT EXISTS ix_planos_gerados_questionnaire_id ON planos_gerados(questionnaire_id);
CREATE INDEX IF NOT EXISTS ix_planos_gerados_status ON planos_gerados(generation_status);
CREATE INDEX IF NOT EXISTS ix_planos_gerados_kb_version ON planos_gerados(kb_version_used);
CREATE INDEX IF NOT EXISTS ix_planos_gerados_task_id ON planos_gerados(task_id);

-- Tabela para chunks da knowledge base (com suporte a vetores)
CREATE TABLE IF NOT EXISTS kb_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_version VARCHAR(50) NOT NULL,
    chunk_text TEXT NOT NULL,
    metadata_json JSONB,
    embedding vector(384) -- Ajuste a dimensão conforme o modelo utilizado (384 para all-MiniLM-L6-v2)
);
CREATE INDEX IF NOT EXISTS ix_kb_chunks_kb_version ON kb_chunks(kb_version);
CREATE INDEX IF NOT EXISTS ix_kb_chunks_metadata ON kb_chunks USING gin(metadata_json);

-- Criar índice vetorial para busca eficiente por similaridade
-- Este comando cria um índice HNSW (Hierarchical Navigable Small World) que é mais eficiente para buscas de similaridade
CREATE INDEX IF NOT EXISTS ix_kb_chunks_embedding_hnsw ON kb_chunks USING hnsw(embedding vector_cosine_ops);

-- Alternativa: Índice IVFFlat, que é mais rápido para construção mas um pouco menos eficiente nas buscas
-- CREATE INDEX IF NOT EXISTS ix_kb_chunks_embedding_ivf ON kb_chunks USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);

-- Inserir uma academia de exemplo
INSERT INTO academias (nome, cnpj, contato_email, contato_telefone, codigo_acesso_membros)
VALUES ('Academia Fitness Exemplo', '12.345.678/0001-90', 'contato@academiaexemplo.com', '(11) 98765-4321', 'ABC123')
ON CONFLICT DO NOTHING;

-- Inserir um usuário administrador de exemplo
-- Senha: admin123 (hash gerado para exemplo)
INSERT INTO usuarios (nome, email, password_hash, academia_id)
SELECT 'Administrador', 'admin@example.com', 
       'pbkdf2:sha256:150000$lLj1JoiN$dd3e4398ff5baaea2654be516285fb7e2a39f8897ac2fed736637cd9195a0713', 
       id 
FROM academias 
WHERE nome = 'Academia Fitness Exemplo'
ON CONFLICT DO NOTHING;