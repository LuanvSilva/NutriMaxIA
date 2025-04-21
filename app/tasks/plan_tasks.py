from app.extensions import celery, db
from app.models import GeneratedPlan, QuestionnaireResponse
from app.services.plan_generation_service import PlanGenerationService
import logging
from datetime import datetime


logger = logging.getLogger(__name__)

# Define o nome explícito da tarefa para compatibilidade com chamadas existentes
@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.plan_tasks.generate_plan_task')
def generate_plan_task(self, plan_id):
    logger.info(f"Iniciando geração do plano para plan_id: {plan_id}")
    plan = db.session.get(GeneratedPlan, plan_id)
    if not plan or plan.generation_status != 'PENDING':
        logger.warning(f"Plano {plan_id} não encontrado ou não está pendente.")
        return

    try:
        plan.generation_status = 'PROCESSING'
        db.session.commit()

        questionnaire = db.session.get(QuestionnaireResponse, plan.questionnaire_id)
        if not questionnaire:
            raise ValueError("Questionário associado não encontrado.")

        user_data = questionnaire.answers_json
        kb_version = plan.kb_version_used # Usa a versão da KB salva no plano

        generation_service = PlanGenerationService(kb_version=kb_version) # Passa a versão
        plan_nutricional, plan_treino, warnings = generation_service.generate_plan(user_data)

        # Atualiza o registro do plano com os resultados
        plan.plan_nutritional_json = plan_nutricional
        plan.plan_training_json = plan_treino
        plan.warnings_json = warnings
        plan.generation_status = 'COMPLETED'
        plan.generated_at = datetime.utcnow()
        db.session.commit()
        logger.info(f"Plano {plan_id} gerado com sucesso.")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao gerar plano {plan_id}: {e}", exc_info=True)
        plan.generation_status = 'FAILED'
        plan.error_message = str(e)
        db.session.commit()
        # Lógica de retentativa do Celery pode ser ativada aqui
        # self.retry(exc=e)
        # Ou notificar o usuário/admin sobre a falha