FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and data dependencies
COPY backend ./backend
COPY data ./data

EXPOSE 8000

ENV PYTHONPATH=/app
ENV PORT=8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]
