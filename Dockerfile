FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /django_tally
WORKDIR /django_tally
ADD . /django_tally
