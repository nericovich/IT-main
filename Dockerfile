FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV BUNKER_GM_PASSWORD=YA2077
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501"]
