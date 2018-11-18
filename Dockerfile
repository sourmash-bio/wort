FROM python:3.7.1-slim-stretch

RUN groupadd user && \
    useradd --create-home --home-dir /home/user -g user -s /bin/bash user

WORKDIR /app/wort

ADD Pipfile Pipfile.lock wortapp.py pyproject.toml ./

RUN pip install pipenv flit
RUN apt-get update && \
    apt-get install -y build-essential libcurl4-openssl-dev libssl-dev && \
    pipenv install --system --deploy && \
    apt-get remove -y build-essential libssl-dev && \
    apt-get autoremove -y

COPY wort wort
COPY config config

RUN FLIT_ROOT_INSTALL=1 flit install --symlink

USER user

CMD gunicorn -b 0.0.0.0:5000 --access-logfile - "wort.app:create_app()"
