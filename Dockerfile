FROM python:3.8.13-slim-buster

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 80


CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]