import sys
import os

# Adicionar o diretório atual ao path do Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import ma
from models import QuestionnaireResponse, GeneratedPlan

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