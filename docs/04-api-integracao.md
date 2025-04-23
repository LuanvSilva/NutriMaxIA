# API e Integração

## Visão Geral

O NutriMaxIA expõe uma API RESTful que permite a integração com sistemas externos, como aplicativos móveis e websites. Esta documentação descreve os endpoints disponíveis e como utilizá-los para interagir com o sistema.

## Autenticação

A API utiliza autenticação baseada em tokens JWT (JSON Web Token):

1. O cliente realiza login e recebe um token JWT
2. Este token deve ser incluído no cabeçalho de todas as requisições subsequentes
3. O formato do cabeçalho é: `Authorization: Bearer {token}`

## Endpoints Principais

### Questionário

#### Submeter Questionário

```
POST /api/v1/questionnaire/submit
```

**Descrição**: Submete um novo questionário para geração de planos.

**Corpo da Requisição**:
```json
{
  "dados_pessoais": {
    "idade": 30,
    "sexo": "M",
    "peso": 80.5,
    "altura": 178,
    "nivel_atividade": "moderado"
  },
  "objetivos": ["hipertrofia", "definicao"],
  "restricoes_alimentares": ["lactose"],
  "condicoes_medicas": ["hipertensao"],
  "preferencias": {
    "alimentos_preferidos": ["frango", "arroz", "batata doce"],
    "alimentos_indesejados": ["brocolis", "berinjela"]
  },
  "treino": {
    "experiencia": "intermediario",
    "dias_disponiveis": 4,
    "tempo_por_sessao": 60,
    "equipamentos_disponiveis": ["academia_completa"]
  }
}
```

**Resposta**:
```json
{
  "status": "success",
  "message": "Questionário recebido, plano em processamento",
  "plan_id": "550e8400-e29b-41d4-a716-446655440000",
  "estimated_time_seconds": 30
}
```

### Planos

#### Verificar Status do Plano

```
GET /api/v1/plans/status/{plan_id}
```

**Descrição**: Verifica o status atual da geração de um plano específico.

**Resposta**:
```json
{
  "status": "success",
  "plan_status": "COMPLETED", // PENDING, PROCESSING, COMPLETED, FAILED
  "progress": 100,
  "message": "Plano gerado com sucesso"
}
```

#### Obter Plano

```
GET /api/v1/plans/{plan_id}
```

**Descrição**: Recupera um plano gerado.

**Resposta**:
```json
{
  "status": "success",
  "plan_data": {
    "plano_alimentar": { /* Dados do plano alimentar */ },
    "plano_treino": { /* Dados do plano de treino */ },
    "avisos_especificos": [ /* Avisos de segurança */ ]
  },
  "generated_at": "2025-04-23T14:30:00Z",
  "kb_version_used": "1.0.0"
}
```

#### Obter Último Plano

```
GET /api/v1/plans/latest
```

**Descrição**: Recupera o plano mais recentemente gerado para o usuário atual.

## Códigos de Status

- **200 OK**: Requisição processada com sucesso
- **201 Created**: Recurso criado com sucesso
- **400 Bad Request**: Erro de validação na requisição
- **401 Unauthorized**: Credenciais de autenticação inválidas ou ausentes
- **403 Forbidden**: Usuário autenticado, mas sem permissão para o recurso
- **404 Not Found**: Recurso não encontrado
- **500 Internal Server Error**: Erro interno do servidor

## Fluxo de Integração

Um fluxo típico para integração com a API do NutriMaxIA é:

1. **Autenticação**: Obter token JWT através do endpoint de login
2. **Submissão do Questionário**: Enviar dados do usuário via endpoint de submissão
3. **Verificação de Status**: Consultar periodicamente o status da geração (polling)
4. **Recuperação do Plano**: Uma vez completo, recuperar o plano gerado
5. **Exibição**: Apresentar os planos nutricional e de treino ao usuário

## Exemplos de Integração

### Exemplo em JavaScript

```javascript
// Submeter questionário
async function submitQuestionnaire(userData, token) {
  const response = await fetch('https://api.nutrimax.com/api/v1/questionnaire/submit', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(userData)
  });
  
  return await response.json();
}

// Verificar status periodicamente
function checkPlanStatus(planId, token, callback) {
  const interval = setInterval(async () => {
    const response = await fetch(`https://api.nutrimax.com/api/v1/plans/status/${planId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const data = await response.json();
    
    if (data.plan_status === 'COMPLETED' || data.plan_status === 'FAILED') {
      clearInterval(interval);
      callback(data);
    }
  }, 5000); // Verificar a cada 5 segundos
}
```

## Considerações de Implementação

- Implementar limitação de requisições (rate limiting) para evitar sobrecarga
- Considerar webhook como alternativa ao polling para notificação de conclusão
- Manter compatibilidade entre versões da API ao evoluir o sistema