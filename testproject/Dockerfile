FROM python:3.6.6-alpine3.8
ENV PYTHONUNBUFFERED 1

RUN apk update

RUN mkdir /code
WORKDIR /code

ADD ./testproject/requirements/common.txt /code/
ADD ./testproject/requirements/default.txt /code/
ADD ./trench /trench/trench
ADD ./setup.py /trench/
ADD ./README.rst /trench/

RUN pip install --upgrade pip
RUN pip install -r default.txt
RUN pip install -e /trench

ADD ./testproject /code/
