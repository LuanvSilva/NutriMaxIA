# NutriMaxIA

Sistema inteligente para geração de planos nutricionais e de treinamento personalizados, utilizando Retrieval-Augmented Generation (RAG) e o modelo Gemini do Google.

## Sobre o Projeto

O NutriMaxIA utiliza inteligência artificial avançada para criar planos de nutrição e treinamento físico personalizados com base em:

- Dados antropométricos e pessoais
- Objetivos específicos
- Restrições alimentares e médicas
- Preferências pessoais
- Disponibilidade de equipamentos e tempo

O sistema integra uma base de conhecimento especializada em nutrição e treinamento físico, garantindo que os planos gerados sigam diretrizes científicas e melhores práticas do setor.

## Principais Características

- **Sistema RAG (Retrieval-Augmented Generation)**: combina recuperação eficiente de conhecimento técnico com geração usando IA
- **Processamento Assíncrono**: geração de planos em background usando Celery
- **Banco de Dados Vetorial**: armazenamento de conhecimento com busca semântica usando pgVector
- **IA Generativa**: utiliza o modelo Gemini do Google para geração de planos personalizados
- **API RESTful**: permite integração com aplicações frontend e sistemas externos
- **Versionamento da Base de Conhecimento**: rastreabilidade e evolução consistente

## Documentação

1. [Arquitetura do Sistema](docs/01-arquitetura.md) - Visão geral dos componentes e fluxo de dados
2. [Serviço de Geração de Planos](docs/02-geracao-planos.md) - Como os planos são gerados e estruturados
3. [Base de Conhecimento e Sistema RAG](docs/03-base-conhecimento.md) - Estrutura da KB e sistema de recuperação
4. [API e Integração](docs/04-api-integracao.md) - Endpoints, autenticação e fluxos de integração
5. [Implantação e Operação](docs/05-implantacao-operacao.md) - Como implantar, configurar e monitorar o sistema

## Guia de Início Rápido

### Pré-requisitos

- Python 3.9+
- PostgreSQL 14+ com extensão pgVector
- Redis 6+
- Chave API do Google Cloud (Gemini)

### Instalação Rápida com Docker

1. Clone o repositório
```bash
git clone https://github.com/sua-organizacao/nutrimax-ia.git
cd nutrimax-ia
```

2. Configure o arquivo `.env` com suas credenciais (veja `.env.example`)

3. Inicie os contêineres
```bash
docker-compose up -d
```

4. Acesse a API em `http://localhost:5000`

### Testando a API

Você pode testar um exemplo de submissão de questionário:

```bash
curl -X POST http://localhost:5000/api/v1/questionnaire/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d @app/example_request.json
```

## Arquitetura da Solução

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

## Contribuição

Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Contato

Para questões sobre o sistema, entre em contato com:
- Email: contato@nutrimax.com