FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app

RUN useradd --create-home --uid 10001 agent
COPY src ./src
COPY examples ./examples
COPY deploy ./deploy
COPY README.md ./README.md

USER agent
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 deploy/healthcheck.py

CMD ["python3", "-m", "src.supplychain_tlm.service", "--host", "0.0.0.0", "--port", "8080", "--allow-remote"]
