FROM node:22-alpine AS web-builder

WORKDIR /web
COPY web/package*.json ./
RUN npm ci
COPY web ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[all]"
COPY knowledge ./knowledge
COPY skills ./skills
COPY --from=web-builder /web/dist ./web/dist

ENV KB_KNOWLEDGE_DIR=/app/knowledge
ENV KB_WEB_DIR=/app/web/dist
EXPOSE 8000
CMD ["quant-kb", "serve", "--host", "0.0.0.0", "--port", "8000"]
