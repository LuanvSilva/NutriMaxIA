# Geração de Planos Nutricionais e de Treinamento

## Visão Geral do Processo

O NutriMaxIA implementa um sistema avançado de geração de planos que combina Retrieval Augmented Generation (RAG) com inteligência artificial generativa para criar planos personalizados de nutrição e treinamento físico. Este documento detalha o fluxo completo, desde a captura de requisitos do usuário até a entrega do plano final.

## Fluxo de Geração

### 1. Captura de Dados do Usuário

O processo começa com a coleta estruturada de informações do usuário através de um questionário abrangente que aborda:

- **Dados Demográficos**: idade, gênero, altura, peso
- **Objetivos**: perda de peso, ganho muscular, saúde geral, etc.
- **Restrições Alimentares**: alergias, intolerâncias, preferências
- **Histórico Médico**: condições pré-existentes relevantes
- **Nível de Condicionamento**: sedentário, iniciante, intermediário, avançado
- **Preferências de Treinamento**: tipos de exercícios preferidos, disponibilidade de equipamentos
- **Estilo de Vida**: rotina diária, nível de atividade, tempo disponível

### 2. Análise e Contextualização

Uma vez recebidos os dados, o sistema:

1. **Análise Preliminar**: Calcula métricas básicas (IMC, necessidades calóricas estimadas)
2. **Identificação de Tópicos-Chave**: Determina áreas de foco específicas para o plano
3. **Priorização de Requisitos**: Organiza requisitos por importância e relevância

### 3. Busca Vetorial na Base de Conhecimento

O componente RAG realiza consultas semânticas à base de conhecimento para recuperar informações relevantes:

```
query = format_query(user_data, objectives, constraints)
relevant_chunks = vector_db_service.semantic_search(
    query,
    top_k=10,
    min_similarity_threshold=0.75
)
```

A busca vetorial prioriza:
- Conhecimento específico para o perfil do usuário
- Diretrizes aplicáveis aos objetivos declarados
- Recomendações para restrições alimentares ou condições médicas

### 4. Construção do Prompt

Um prompt estruturado é montado combinando:

- **Contexto do Usuário**: Resumo dos dados e requisitos do usuário
- **Conhecimento Relevante**: Chunks recuperados da base de conhecimento
- **Diretrizes de Formatação**: Instruções para o formato esperado do plano
- **Limitações e Considerações**: Parâmetros de segurança e restrições importantes

Exemplo de estrutura do prompt:
```
system_prompt = """
Você é um especialista em nutrição e educação física capacitado para criar planos personalizados.
Sua tarefa é gerar um plano completo com as seguintes seções:

1. Resumo personalizado
2. Plano nutricional detalhado
3. Plano de treinamento físico
4. Recomendações de suplementação (se aplicável)
5. Orientações para acompanhamento e ajustes

Use APENAS as informações fornecidas na base de conhecimento para suas recomendações.
Não invente informações nutricionais ou médicas não suportadas pelo conhecimento fornecido.
"""

user_prompt = f"""
PERFIL DO USUÁRIO:
{formatted_user_data}

OBJETIVOS PRINCIPAIS:
{formatted_objectives}

RESTRIÇÕES E CONSIDERAÇÕES:
{formatted_constraints}

BASE DE CONHECIMENTO RELEVANTE:
{formatted_knowledge_chunks}

Gere um plano completo seguindo a estrutura solicitada.
"""
```

### 5. Geração via Modelo de Linguagem

O sistema utiliza o Google Gemini para gerar o plano personalizado:

1. **Chamada à API**: O prompt estruturado é enviado à API Gemini
2. **Configuração da Geração**:
   - Temperature: 0.3-0.5 (para balancear criatividade e precisão)
   - Top-p: 0.85
   - Modelo: gemini-1.5-pro-latest

### 6. Pós-processamento e Estruturação

Após receber a resposta do LLM, o sistema:

1. **Validação**: Verifica se todas as seções esperadas estão presentes
2. **Formatação**: Estrutura o conteúdo em formato padronizado
3. **Enriquecimento**: Adiciona metadados como fontes e referências
4. **Organização**: Separa o plano em componentes lógicos (nutrição, treinamento, suplementação)

### 7. Armazenamento e Entrega

O plano finalizado é:

1. **Persistido**: Armazenado no banco de dados associado ao usuário
2. **Versionado**: Mantém histórico de versões se houver atualizações
3. **Disponibilizado**: Através de endpoints API específicos

## Componentes Técnicos

### 1. PlanGenerationService

Classe central que orquestra todo o processo de geração:

```python
class PlanGenerationService:
    def __init__(self, llm_service, kb_service, vector_db_service):
        self.llm_service = llm_service
        self.kb_service = kb_service
        self.vector_db_service = vector_db_service
        
    def generate_plan(self, user_data, objectives, constraints):
        # 1. Análise preliminar
        analyzed_data = self._analyze_user_data(user_data)
        
        # 2. Recuperação de conhecimento relevante
        knowledge_chunks = self._retrieve_relevant_knowledge(analyzed_data, objectives, constraints)
        
        # 3. Construção do prompt
        prompt = self._construct_prompt(analyzed_data, objectives, constraints, knowledge_chunks)
        
        # 4. Geração via LLM
        raw_plan = self.llm_service.generate_text(prompt)
        
        # 5. Pós-processamento
        structured_plan = self._structure_plan(raw_plan)
        
        return structured_plan
```

### 2. VectorDBService

Gerencia buscas semânticas na base de conhecimento:

```python
class VectorDBService:
    def semantic_search(self, query, top_k=10, min_similarity_threshold=0.7):
        # Gera embedding para a consulta
        query_embedding = self._generate_embedding(query)
        
        # Recupera chunks similares
        similar_chunks = self._find_similar_chunks(query_embedding, top_k, min_similarity_threshold)
        
        return similar_chunks
```

### 3. LLMService

Encapsula a interação com a API do Google Gemini:

```python
class LLMService:
    def generate_text(self, prompt, temperature=0.4, top_p=0.85):
        # Configuração do modelo e parâmetros
        model_config = {
            "temperature": temperature,
            "top_p": top_p,
            "max_output_tokens": 8192,
        }
        
        # Chamada à API do modelo
        response = self._call_gemini_api(prompt, model_config)
        
        return response.text
```

## Garantia de Qualidade

### Validação de Planos

Cada plano gerado passa por verificações automáticas para garantir:

1. **Completude**: Todas as seções necessárias estão presentes
2. **Consistência**: Recomendações são coerentes entre si
3. **Conformidade**: Alinhamento com diretrizes nutricionais e de treinamento
4. **Personalização**: Adequação ao perfil e objetivos específicos do usuário

### Sistema de Feedback

O sistema incorpora um mecanismo de feedback que:

1. Coleta avaliações dos usuários sobre os planos
2. Identifica padrões em planos bem avaliados vs. mal avaliados
3. Utiliza esse feedback para ajustar parâmetros de geração

## Considerações Éticas e Limitações

- **Disclaimer Médico**: Os planos incluem avisos claros de que não substituem orientação médica profissional
- **Limites de Personalização**: O sistema reconhece cenários que requerem supervisão especializada
- **Transparência**: Todas as recomendações são respaldadas por informações da base de conhecimento

## Futuras Melhorias

1. **Refinamento Iterativo**: Permitir ajustes incrementais aos planos com base no progresso
2. **Personalização Avançada**: Incorporar mais variáveis para personalização (genética, microbioma)
3. **Monitoramento de Adesão**: Integrar rastreamento de aderência ao plano
4. **Análise de Resultados**: Correlacionar características dos planos com resultados obtidos