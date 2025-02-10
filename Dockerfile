FROM python:3.12-slim

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

# Upgrade pip and install dependencies
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 80


CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]