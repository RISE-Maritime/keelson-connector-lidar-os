FROM python:3.11-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY . .

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

RUN apt-get update && apt-get install -y libgl1 && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["python", "bin/main.py"]

CMD ["-r", "rise"]