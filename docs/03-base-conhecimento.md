# Base de Conhecimento e Sistema RAG

## Visão Geral

O NutriMaxIA utiliza uma abordagem de Retrieval-Augmented Generation (RAG) para garantir que os planos gerados sejam baseados em conhecimento técnico específico sobre nutrição e treinamento. Este documento descreve como a base de conhecimento é estruturada e como o sistema de recuperação funciona.

## Base de Conhecimento

### Estrutura

A base de conhecimento é armazenada em formato JSON e dividida em "chunks" temáticos, cada um contendo um fragmento específico de conhecimento. Os chunks são categorizados por tipo e subtipo, facilitando a recuperação seletiva.

```json
{
  "version": "1.0.0",
  "chunks": [
    {
      "id": "nutrition-001",
      "type": "nutrition_rule",
      "subtype": "macronutrient_calculation",
      "content": "Para pessoas visando hipertrofia, a ingestão de proteínas recomendada é de 1.6 a 2.2g por kg de peso corporal..."
    },
    // Outros chunks...
  ]
}
```

### Tipos de Conteúdo

- **nutrition_rule**: Regras e diretrizes nutricionais
- **training_protocol**: Protocolos de treinamento
- **restriction_guideline**: Orientações para restrições alimentares
- **medical_condition**: Considerações para condições médicas específicas
- **food_database**: Informações sobre alimentos específicos
- **disclaimer**: Avisos e disclaimers legais/médicos

## Sistema de Recuperação Vetorial

### VectorDBService

Este serviço gerencia a interação com o banco de dados vetorial, permitindo buscas semânticas por similaridade:

1. **Indexação**: Cada chunk de conhecimento é transformado em um embedding vetorial
2. **Armazenamento**: Os vetores são armazenados na tabela `kb_chunks` usando pgvector
3. **Recuperação**: Consultas são convertidas em embeddings e usadas para busca por similaridade

### Exemplo de Fluxo de Busca

```python
# Exemplo simplificado do funcionamento interno
query = "dieta para ganho de massa muscular"
query_embedding = embedding_model.encode(query)
similar_chunks = vector_db.query(
    vector=query_embedding,
    k=5,  # número de resultados
    filters={"type": "nutrition_rule"}  # filtros opcionais
)
```

## Integração com o Modelo de IA

O conhecimento recuperado é integrado ao prompt enviado ao modelo de IA (Gemini):

1. Informações do usuário são analisadas para identificar suas necessidades específicas
2. Consultas relevantes são construídas com base nessas necessidades
3. Chunks de conhecimento mais similares são recuperados
4. O prompt é estruturado para instruir o modelo a usar apenas esse conhecimento recuperado
5. O modelo gera o plano com base nas diretrizes do conhecimento especializado

## Versionamento da Base de Conhecimento

### Controle de Versões

A base de conhecimento é versionada (atualmente na versão 1.0.0) para garantir:

- Rastreabilidade: Cada plano gerado registra qual versão da KB foi utilizada
- Evolução: Atualizações podem ser feitas mantendo compatibilidade com versões anteriores
- Auditoria: Possibilidade de comparar resultados entre diferentes versões

### Processo de Atualização

Para atualizar a base de conhecimento:

1. Criar um novo arquivo JSON com versão incrementada
2. Processar e indexar os chunks no banco de dados
3. Atualizar a configuração `KB_VERSION` para apontar para a nova versão
4. O sistema passará automaticamente a utilizar a nova versão para novas gerações de plano