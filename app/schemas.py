from app.extensions import ma
from app.models import QuestionnaireResponse, GeneratedPlan

class QuestionnaireSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = QuestionnaireResponse
        include_fk = True
        load_instance = True

class GeneratedPlanSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GeneratedPlan
        include_fk = True
        load_instance = True