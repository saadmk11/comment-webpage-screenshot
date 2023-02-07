FROM python:3.8

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN git config --global --add safe.directory /github/workspace

CMD ["python", "/scripts/main.py"]
