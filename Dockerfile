
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tesseract Arabic language data for OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-ara && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000 8501
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 & streamlit run app.py --server.address 0.0.0.0"]
