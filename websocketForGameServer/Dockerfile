FROM python:3.12-alpine

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8500

CMD ["python", "gameServer.py"]
