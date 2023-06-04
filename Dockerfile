FROM ubuntu:20.04

USER root

COPY ./src/ /app/money_flow

RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN pip3 install -r /app/money_flow/requirements.txt

WORKDIR /app/money_flow
CMD ["python3", "-m", "main.py"]