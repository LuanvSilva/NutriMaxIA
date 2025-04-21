import sys
import os

# Configurar path do Python para encontrar módulos locais
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request, jsonify
from extensions import db
from models import QuestionnaireResponse, GeneratedPlan, Academia, User
from schemas import QuestionnaireSchema
from tasks.plan_tasks import generate_plan_task
from utils.helpers import get_current_kb_version
import uuid
import logging
from sqlalchemy import text
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)
questionnaire_bp = Blueprint('questionnaire', __name__, url_prefix='/api/v1/questionnaires')
questionnaire_schema = QuestionnaireSchema()

@questionnaire_bp.route('', methods=['POST'])
def submit_questionnaire():
    json_data = request.get_json()
    if not json_data:
        logger.warning("Recebida requisição POST sem corpo JSON.")
        return jsonify({"message": "No input data provided"}), 400

    # Usar um ID de usuário fixo para testes
    test_user_id = "00000000-0000-0000-0000-000000000001"
    test_academy_id = "00000000-0000-0000-0000-000000000000"
    
    # Verificar e criar a academia e usuário de teste se não existir
    try:
        # Verificar se a academia existe
        academy = db.session.query(Academia).filter_by(id=test_academy_id).first()
        if not academy:
            logger.info("Creating test academy...")
            academy = Academia(
                id=uuid.UUID(test_academy_id),
                nome="Academia Teste",
                cnpj="00.000.000/0001-00",
                contato_email="test@teste.com",
                contato_telefone="(00) 00000-0000",
                codigo_acesso_membros="TEST123",
                status="ativo"
            )
            db.session.add(academy)
            db.session.flush()

        # Verificar se o usuário existe
        user = db.session.query(User).filter_by(id=test_user_id).first()
        if not user:
            logger.info("Creating test user...")
            # Use a simpler hashing method that produces a shorter hash
            password_hash = generate_password_hash("senha123", method='pbkdf2:sha256')
            
            user = User(
                id=uuid.UUID(test_user_id),
                nome="Usuário Teste",
                email="usuario.teste@example.com",
                academia_id=uuid.UUID(test_academy_id),
                password_hash=password_hash,  # Set the hash directly instead of using set_password()
                status="ativo"
            )
            db.session.add(user)
            db.session.flush()
            
        user_id = test_user_id
        logger.info(f"Processando questionário para o usuário de teste: {user_id}")
    
    except Exception as e:
        logger.error(f"Erro ao criar dados de teste: {str(e)}")
        return jsonify({"message": "Error creating test data", "error": str(e)}), 500

    # Verificação de Red Flags
    if json_data.get('health_history', {}).get('has_renal_disease', False):
         logger.info(f"Red flag (doença renal) detectada. Abortando geração.")
         return jsonify({
             "message": "Recomendação Importante",
             "details": "Com base nas suas respostas, recomendamos fortemente que consulte um médico ou nutricionista antes de iniciar qualquer plano. Não podemos gerar um plano automatizado neste caso."
         }), 400

    try:
        # Salvar a resposta do questionário
        kb_version = get_current_kb_version()
        new_response = QuestionnaireResponse(
            user_id=user_id,
            answers_json=json_data,
            kb_version_used=kb_version
        )
        db.session.add(new_response)
        db.session.commit()  # Commit primeiro para garantir que o ID será gerado
        db.session.refresh(new_response)

        # Criar um registro de plano pendente
        new_plan = GeneratedPlan(
            user_id=user_id,
            questionnaire_id=new_response.id,
            generation_status='PENDING',
            kb_version_used=kb_version
        )
        db.session.add(new_plan)
        db.session.commit()
        logger.info(f"Questionário e registro de plano (ID: {new_plan.id}) salvos com sucesso.")

        # Disparar tarefa assíncrona para gerar o plano
        task = generate_plan_task.delay(str(new_plan.id))
        logger.info(f"Tarefa Celery disparada: {task.id}")

        return jsonify({
            "message": "Questionário recebido. Seu plano está sendo gerado.",
            "plan_id": str(new_plan.id)
        }), 202

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao processar questionário: {str(e)}", exc_info=True)
        return jsonify({
            "message": "Erro interno ao processar o questionário",
            "error": str(e)  # Incluir detalhes do erro para facilitar debug
        }), 500
