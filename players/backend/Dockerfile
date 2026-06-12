FROM python:3.11-slim

WORKDIR /players

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend backend
COPY ml ml
COPY data data

ENV PYTHONPATH=/players
EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
