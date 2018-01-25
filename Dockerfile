FROM python:3.6.4-slim-stretch

RUN groupadd user && \
    useradd --create-home --home-dir /home/user -g user -s /bin/bash user

WORKDIR /home/user

ADD Pipfile.lock wort/ pyproject.toml config/ ./

RUN pip install pipenv flit
RUN pipenv install --system --deploy --ignore-pipfile
RUN flit --symlink

USER user
