FROM python:3.6.4-slim-stretch

RUN groupadd user && \
    useradd --create-home --home-dir /home/user -g user -s /bin/bash user

WORKDIR /home/user

ADD Pipfile.lock wort/ pyproject.toml config/ ./

RUN pip install pipenv flit
RUN apt-get update && \
    apt-get install -y build-essential libcurl4-openssl-dev && \
    pipenv install --system --deploy --ignore-pipfile && \
    apt-get remove -y build-essential && \
    apt-get autoremove -y

RUN flit --symlink

USER user
