FROM python:3.11-slim

WORKDIR /app

COPY . .

# Install only the runtime dependencies used by server.py.
RUN pip install --no-cache-dir \
    fastapi==0.110.1 \
    uvicorn==0.25.0 \
    python-dotenv==1.2.1 \
    motor==3.3.1 \
    pymongo==4.5.0 \
    pydantic==2.12.5 \
    reportlab==4.4.10 \
    python-multipart==0.0.22

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
