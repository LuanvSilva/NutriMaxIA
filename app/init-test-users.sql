-- Initialize test academy and user for development
-- This should be executed AFTER init-db.sql which creates the tables

-- Check if the Academia test record exists, if not create it
INSERT INTO academias (id, nome, cnpj, contato_email, contato_telefone, status, codigo_acesso_membros, created_at, updated_at)
SELECT 
  '00000000-0000-0000-0000-000000000000'::uuid, 
  'Academia Teste', 
  '00.000.000/0001-00', 
  'test@teste.com', 
  '(00) 00000-0000', 
  'ativo', 
  'TEST123', 
  NOW(), 
  NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM academias WHERE id = '00000000-0000-0000-0000-000000000000'::uuid
);

-- Check if the User test record exists, if not create it
INSERT INTO usuarios (id, nome, email, password_hash, academia_id, status, created_at)
SELECT 
  '00000000-0000-0000-0000-000000000001'::uuid, 
  'Usuario Teste', 
  'test@user.com', 
  -- Using a simpler hash that fits within the column size
  'pbkdf2:sha256:150000$abcdef$1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef', 
  '00000000-0000-0000-0000-000000000000'::uuid, 
  'ativo', 
  NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM usuarios WHERE id = '00000000-0000-0000-0000-000000000001'::uuid
);