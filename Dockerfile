FROM python:3.12-slim

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

# Upgrade pip and install dependencies
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK data to a specific directory
ENV NLTK_DATA=/app/nltk_data
RUN mkdir -p /app/nltk_data && \
    python -m nltk.downloader -d /app/nltk_data punkt punkt_tab wordnet

COPY . /app

EXPOSE 80


CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]