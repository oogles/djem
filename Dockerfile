FROM python:3.10-slim-trixie
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get -y install nano make

WORKDIR /opt/app

COPY dev_requirements.txt /opt/app/dev_requirements.txt

RUN pip3 install -r dev_requirements.txt
