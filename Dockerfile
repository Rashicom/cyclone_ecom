FROM python:3

ENV PYTHONUNBUFFERED 1

WORKDIR /cyclone

ADD . /cyclone

COPY ./requirements.txt /cyclone/requirements.txt

RUN pip install -r requirements.txt

COPY . /cyclone
