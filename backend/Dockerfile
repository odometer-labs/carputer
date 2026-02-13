FROM python:3.13 AS builder

RUN pip3 install uv==0.10.2

ENV PATH="/usr/local/bin:$PATH" 

COPY geotracker /opt/geotracker

WORKDIR /opt/geotracker

RUN uv run --group dev pytest

RUN uv build --wheel

# TODO install on a slim image and setup application to run

# FROM python:3.13

# ENV SERVER_PORT=3000

