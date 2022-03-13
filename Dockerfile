FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install software-properties-common -y && \
    add-apt-repository ppa:deadsnakes/ppa
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends build-essential python3 python3-dev python3-pip libpq-dev

WORKDIR /app
COPY . /app

RUN pip3 install -r requirements.txt

ENV LANG=C.UTF-8
CMD python3 ./src/main.py
