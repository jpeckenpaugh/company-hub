FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl
RUN curl -fsSL https://opencode.ai/install | bash
RUN mkdir -p /app/opencode

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt "uvicorn[standard]==0.52.4"

EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/backend"]
