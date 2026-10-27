# Dockerfile - Pipeline de Evidencias Explicativas
#
# Imagem base: Python 3.12 slim
# Dependencias: build-essential, gcc, g++, netcat-openbsd
# Script de espera: aguarda MySQL estar disponivel antes de executar
# Comando padrao: executa o benchmark com imagens do diretorio images/

FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo fonte
COPY . .

# Criar diretorio de assets
RUN mkdir -p assets

# Criar script de espera para MySQL (evita problemas de CRLF do Windows)
# Usa /usr/local/bin para nao ser sobrescrito pelo volume mount em /app
RUN printf '#!/bin/sh\n\necho "Aguardando MySQL em $1:3306..."\n\nwhile ! nc -z "$1" 3306; do\n    sleep 1\ndone\n\necho "MySQL disponivel!"\n\nshift\nexec "$@"\n' > /usr/local/bin/wait-for-mysql.sh && chmod +x /usr/local/bin/wait-for-mysql.sh

# Configurar entrypoint e comando padrao
ENTRYPOINT ["/usr/local/bin/wait-for-mysql.sh", "mysql"]
CMD ["python", "src/benchmark.py", "--input", "images/", "--output", "reports/"]
