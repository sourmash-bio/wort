FROM python:3.6.4-slim-stretch

RUN groupadd user && \
    useradd --create-home --home-dir /home/user -g user -s /bin/bash user

WORKDIR /home/user

ADD Pipfile.lock ./

RUN pip install pipenv
RUN pipenv install --system --deploy --ignore-pipfile

USER user

#COPY soursigs soursigs
#
#CMD celery -A soursigs -l INFO -c 1 worker
