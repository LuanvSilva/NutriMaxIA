from flask import Blueprint, jsonify
# Removi importações de JWT para facilitar testes
from app.extensions import db
from app.models import GeneratedPlan
import logging

logger = logging.getLogger(__name__)
plans_bp = Blueprint('plans', __name__, url_prefix='/api/v1/plans')

@plans_bp.route('/latest', methods=['GET'])
def get_latest_plan():
    # Usar ID de teste fixo para desenvolvimento
    user_id = "00000000-0000-0000-0000-000000000001"
    logger.info(f"Buscando último plano para usuário de teste {user_id}")

    latest_plan = GeneratedPlan.query.filter_by(user_id=user_id)\
                                      .order_by(GeneratedPlan.generated_at.desc())\
                                      .first()

    if not latest_plan:
        logger.info(f"Nenhum plano encontrado para usuário de teste")
        return jsonify({"message": "Nenhum plano encontrado."}), 404

    if latest_plan.generation_status == 'PENDING' or latest_plan.generation_status == 'PROCESSING':
        logger.info(f"Plano {latest_plan.id} ainda está sendo gerado para usuário {user_id}")
        return jsonify({
            "plan_id": str(latest_plan.id),
            "status": latest_plan.generation_status,
            "message": "Seu plano ainda está sendo processado. Por favor, tente novamente em alguns instantes."
        }), 202 # Accepted ou 200 OK com status
    elif latest_plan.generation_status == 'FAILED':
         logger.warning(f"Último plano {latest_plan.id} falhou para usuário {user_id}")
         return jsonify({
            "plan_id": str(latest_plan.id),
            "status": latest_plan.generation_status,
            "message": "Houve um erro ao gerar seu último plano. Por favor, tente submeter o questionário novamente ou contate o suporte.",
            "error": latest_plan.error_message # Opcional, talvez não expor diretamente
         }), 500 # Internal Server Error ou outro apropriado

    # Se COMPLETED, retornar o plano (usar schema para serializar)
    # return plan_schema.dump(latest_plan), 200
    # Exemplo simplificado:
    return jsonify({
        "plan_id": str(latest_plan.id),
        "status": latest_plan.generation_status,
        "generated_at": latest_plan.generated_at.isoformat() if latest_plan.generated_at else None,
        "kb_version": latest_plan.kb_version_used,
        "plan_nutricional": latest_plan.plan_nutritional_json,
        "plan_treino": latest_plan.plan_training_json,
        "avisos": latest_plan.warnings_json
    }), 200

@plans_bp.route('/status/<plan_id>', methods=['GET'])
def get_plan_status(plan_id):
    # Não verificar o usuário para testes
    plan = db.session.get(GeneratedPlan, plan_id)

    if not plan:
        logger.warning(f"Plano {plan_id} não encontrado")
        return jsonify({"message": "Plano não encontrado"}), 404

    return jsonify({
        "plan_id": str(plan.id),
        "status": plan.generation_status,
        "error": plan.error_message if plan.generation_status == 'FAILED' else None
    }), 200