FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[all]"
COPY knowledge ./knowledge
COPY skills ./skills

ENV KB_KNOWLEDGE_DIR=/app/knowledge
EXPOSE 8000
CMD ["quant-kb", "serve", "--host", "0.0.0.0", "--port", "8000"]

