FROM python:3.8

RUN apt-get update && apt-get install -y --no-install-recommends wget

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "/scripts/main.py"]
