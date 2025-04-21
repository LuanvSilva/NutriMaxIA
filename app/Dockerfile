# Use uma imagem base Python apropriada
FROM python:3.10-slim

# Configuração de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py

# Defina o diretório de trabalho dentro do container
WORKDIR /app

# Copie o arquivo de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante do código da aplicação para o diretório de trabalho
COPY . .

# Exponha a porta que o Flask usará
EXPOSE 5001

# Comando padrão para rodar a aplicação
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]