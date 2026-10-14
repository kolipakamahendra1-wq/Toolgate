FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV TOOLGATE_DATA_DIR=/srv/data LLM_BASE_URL=http://host.docker.internal:11434
EXPOSE 8030
CMD ["uvicorn", "app.main:create_default", "--factory", "--host", "0.0.0.0", "--port", "8030"]
