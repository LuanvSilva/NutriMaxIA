# Arquitetura do Sistema

## Visão Geral

O NutriMaxIA é estruturado como uma aplicação distribuída que combina processamento assíncrono, banco de dados vetorial e integração com IA generativa. A arquitetura foi projetada para oferecer escalabilidade, responsividade e desacoplamento entre os componentes.

## Componentes Principais

### 1. API RESTful (Flask)

Camada de interface que expõe endpoints HTTP para interação com clientes externos. Responsável por:
- Receber e validar requisições
- Autenticação e autorização
- Programação de tarefas assíncronas
- Exposição dos resultados

### 2. Banco de Dados (PostgreSQL + pgVector)

Armazenamento persistente com capacidade para busca vetorial, utilizado para:
- Dados estruturados dos usuários e planos
- Armazenamento de embeddings e chunks da base de conhecimento
- Rastreamento do status das tarefas assíncronas

### 3. Fila de Tarefas (Redis + Celery)

Sistema de enfileiramento e processamento assíncrono que:
- Gerencia tarefas de longa duração
- Desacopla recebimento de requisições do processamento intensivo
- Oferece recursos de retry e monitoramento

### 4. Workers Celery

Processos responsáveis pela execução efetiva das tarefas, incluindo:
- Recuperação de conhecimento relevante da base de conhecimento
- Formatação de prompts para o LLM
- Geração de planos personalizados
- Armazenamento dos resultados no banco de dados

### 5. Serviço LLM (Google Gemini)

Modelo de linguagem responsável pela geração dos planos, acessado via API externa:
- Recebe prompts estruturados com conhecimento específico
- Realiza inferência sobre os dados do usuário
- Gera conteúdo personalizado seguindo diretrizes específicas

### 6. Base de Conhecimento

Repositório centralizado e versionado de informações técnicas sobre nutrição e treinamento físico:
- Armazenada como chunks com embeddings correspondentes
- Permite recuperação semântica eficiente
- Oferece contexto especializado para o LLM

## Fluxo de Dados

A seguir, descrevemos o fluxo típico de processamento dentro do sistema:

```
1. Cliente submete questionário via API
   │
2. API valida dados e cria tarefa na fila Celery
   │
3. API retorna ID do plano e status inicial ao cliente
   │
4. Worker Celery processa a tarefa assincronamente
   │   ├─ Analisa as necessidades do usuário
   │   ├─ Realiza busca vetorial na base de conhecimento
   │   ├─ Prepara prompt enriquecido com conhecimento relevante
   │   ├─ Envia prompt ao modelo Gemini
   │   ├─ Processa e estrutura a resposta do modelo
   │   └─ Armazena o plano finalizado no banco de dados
   │
5. Cliente consulta status periodicamente via API
   │
6. Cliente recupera o plano finalizado quando status = COMPLETED
```

## Diagrama de Arquitetura

```
┌───────────┐      ┌────────────────┐      ┌──────────────┐
│  Cliente  │◄────►│  API (Flask)   │◄────►│  Banco de    │
└───────────┘      └────────────────┘      │  Dados       │
                         │   ▲             │  PostgreSQL  │
                         │   │             └──────────────┘
                         ▼   │                    ▲
                   ┌─────────────────┐            │
                   │  Redis (Broker) │            │
                   └─────────────────┘            │
                         │   ▲                    │
                         │   │                    │
                         ▼   │                    │
                   ┌─────────────────┐            │
                   │ Celery Worker   │────────────┘
                   └─────────────────┘
                         │   ▲
                         │   │
                         ▼   │
┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│  Base de     │◄──►│ Serviço Geração │◄──►│ API Gemini   │
│ Conhecimento │    │     de Planos   │    │    (LLM)     │
└──────────────┘    └─────────────────┘    └──────────────┘
```

## Principais Classes e Estruturas

### Models

- **User**: Representa um usuário do sistema
- **Plan**: Contém os planos gerados e metadados associados
- **KnowledgeBaseChunk**: Representa um fragmento da base de conhecimento com seu embedding

### Services

- **LLMService**: Encapsula interações com a API Gemini
- **KnowledgeBaseService**: Gerencia carregamento e atualização da base de conhecimento
- **VectorDBService**: Realiza operações de busca vetorial
- **PlanGenerationService**: Orquestra o fluxo de geração de planos

### Tasks

- **PlanTasks**: Define tarefas assíncronas Celery, principalmente `generate_plan_task`

## Considerações Técnicas

### Escalabilidade

- Workers Celery podem ser escalados horizontalmente
- Índices PostgreSQL otimizados para busca eficiente
- Cache Redis para resultados frequentemente acessados

### Segurança

- Autenticação JWT para acesso à API
- Validação de entrada em múltiplas camadas
- Sanitização de dados enviados ao LLM

### Monitoramento

- Logs estruturados em todos os componentes
- Métricas de desempenho para tarefas Celery
- Endpoints de diagnóstico para verificação de saúde

## Escolhas Tecnológicas

- **Flask**: Framework web leve e flexível para Python
- **Celery**: Biblioteca robusta para processamento assíncrono de tarefas
- **PostgreSQL + pgVector**: Banco de dados relacional com capacidade vetorial
- **Redis**: Armazenamento em memória para broker de mensagens
- **Gemini API**: Modelo de linguagem de última geração do Google