# Universal ERP Demo — Railway / Docker
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY frontend/dist /app/frontend/dist

ENV PYTHONPATH=/app/backend
ENV SERVE_FRONTEND=true
ENV FRONTEND_DIST_DIR=/app/frontend/dist
ENV ENVIRONMENT=demo
ENV PRODUCT_MODE=erp-demo
ENV ACCEPT_INZ_SSO=false
ENV PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "uvicorn erp.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
