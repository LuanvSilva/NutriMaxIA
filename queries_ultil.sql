-- Exibir todos os planos gerados, ordenados por data de criação
SELECT id, user_id, generation_status, generated_at, kb_version_used 
FROM planos_gerados 
ORDER BY generated_at DESC;

-- Contar planos por status
SELECT generation_status, COUNT(*) 
FROM planos_gerados 
GROUP BY generation_status;

-- Verificar planos pendentes ou em processamento
SELECT id, user_id, generation_status, task_id 
FROM planos_gerados 
WHERE generation_status IN ('PENDING', 'PROCESSING');

-- Verificar planos com falha e seus motivos
SELECT id, user_id, generated_at, error_message 
FROM planos_gerados 
WHERE generation_status = 'FAILED';


-- Listar todos os questionários submetidos
SELECT id, user_id, submitted_at, kb_version_used 
FROM questionario_respostas 
ORDER BY submitted_at DESC;

-- Ver detalhes de um questionário específico (incluindo o JSON completo)
SELECT id, user_id, answers_json, submitted_at 
FROM questionario_respostas 
WHERE id = 'UUID_DO_QUESTIONARIO';

-- Listar todos os usuários
SELECT id, nome, email, academia_id, status, created_at 
FROM usuarios;

-- Listar todas as academias
SELECT id, nome, cnpj, status, codigo_acesso_membros 
FROM academias;

-- Juntar usuários com suas academias
SELECT u.id, u.nome, u.email, a.nome as academia_nome, u.status 
FROM usuarios u 
JOIN academias a ON u.academia_id = a.id;



-- Juntar questionários com seus planos gerados
SELECT q.id as questionario_id, 
       p.id as plano_id, 
       q.submitted_at, 
       p.generation_status, 
       p.generated_at 
FROM questionario_respostas q 
LEFT JOIN planos_gerados p ON q.id = p.questionnaire_id 
ORDER BY q.submitted_at DESC;


-- Ver todos os chunks da base de conhecimento
SELECT id, kb_version, LEFT(chunk_text, 100) as texto_preview 
FROM kb_chunks 
ORDER BY kb_version;

-- Contar chunks por versão da KB
SELECT kb_version, COUNT(*) 
FROM kb_chunks 
GROUP BY kb_version;

-- Buscar chunks específicos (exemplo: que contém a palavra "proteína")
SELECT id, kb_version, chunk_text 
FROM kb_chunks 
WHERE chunk_text ILIKE '%proteína%';



-- Contagem de registros por tabela principal
SELECT 'academias' as tabela, COUNT(*) as registros FROM academias
UNION
SELECT 'usuarios', COUNT(*) FROM usuarios
UNION
SELECT 'questionario_respostas', COUNT(*) FROM questionario_respostas
UNION
SELECT 'planos_gerados', COUNT(*) FROM planos_gerados
UNION
SELECT 'kb_chunks', COUNT(*) FROM kb_chunks
ORDER BY registros DESC;