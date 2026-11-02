FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install .

# A imagem padrão não executa classificadores. O compose experimental do Kev troca
# somente este argumento de build por uma configuração que aponta para o serviço `kev`.
ARG BACKEND_CONFIG=config.container.ini
COPY ${BACKEND_CONFIG} /app/config.ini

EXPOSE 8000

CMD ["python", "-m", "notas_ia", "api", "--config", "/app/config.ini"]
