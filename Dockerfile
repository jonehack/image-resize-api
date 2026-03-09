FROM python:3.10

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y gcc

RUN gcc resize.c -o resize -lm

RUN chmod +x resize

RUN pip install -r requirements.txt

CMD ["gunicorn", "-b", "0.0.0.0:8080", "resize_api_server:app"]
