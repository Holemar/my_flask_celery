FROM python:3.11

COPY . /src
WORKDIR /src

RUN pip3 install -r requirements.txt

CMD ["python3", "main.py", "-m", "api"]

