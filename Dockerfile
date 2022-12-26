# Build decoct
FROM rust:1-slim-bullseye as builder
RUN cargo install --git https://github.com/luizirber/decoct --rev 630f5a773e6df22a33dafc3d744e39735c055328

# Build worker image
FROM python:3.10.9-slim-bullseye as base

RUN groupadd user && \
    useradd --create-home --home-dir /home/user -g user -s /bin/bash user

WORKDIR /home/user

#--------------------

FROM base as python-deps

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential libcurl4-openssl-dev libssl-dev curl

RUN python3 -m venv /home/user/.venv

COPY requirements.txt ./

RUN . /home/user/.venv/bin/activate && pip install -r requirements.txt

RUN curl --output sratoolkit.tar.gz https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/3.0.2/sratoolkit.3.0.2-ubuntu64.tar.gz
RUN tar xf sratoolkit.tar.gz

#--------------------

FROM base as web

COPY --from=python-deps /home/user/.venv /home/user/.venv

WORKDIR /app/wort

ADD wortapp.py pyproject.toml ./

COPY wort wort
COPY config config

RUN . /home/user/.venv/bin/activate && pip install flit && FLIT_ROOT_INSTALL=1 flit install --symlink

USER user

ENV PATH "/home/user/.venv/bin:$PATH"
CMD . /home/user/.venv/bin/activate && gunicorn -b 0.0.0.0:5000 --access-logfile - "wort.app:create_app()"

#--------------------

FROM base as worker

COPY --from=builder /usr/local/cargo/bin/decoct /usr/local/bin/sourmash
COPY --from=python-deps /home/user/sratoolkit.3.0.2-ubuntu64/bin /home/user/sratoolkit.3.0.2-ubuntu64/bin
COPY --from=python-deps /home/user/.venv /home/user/.venv

ENV PATH "/home/user/.venv/bin:$PATH"

ENV PATH "$PATH:/home/user/sratoolkit.3.0.2-ubuntu64/bin"

# needed for celery[sqs]
RUN apt-get update
RUN apt-get install -y --no-install-recommends libcurl4-openssl-dev libssl-dev

USER user

# Configure sra-toolkit to disable cache
RUN mkdir .ncbi

RUN echo '## auto-generated configuration file - DO NOT EDIT ##''' >> .ncbi/user-settings.mkfg
RUN echo '' >> .ncbi/user-settings.mkfg
RUN echo '/LIBS/GUID = "7737545d-30d4-4d05-875a-2c562df521d5"' >> .ncbi/user-settings.mkfg
RUN echo '/config/default = "false"' >> .ncbi/user-settings.mkfg
RUN echo '/libs/cloud/accept_aws_charges = "false"' >> .ncbi/user-settings.mkfg
RUN echo '/libs/cloud/report_instance_identity = "true"' >> .ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/apps/file/volumes/flatAd = "."' >> .ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/apps/refseq/volumes/refseqAd = "."' >> .ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/apps/sra/volumes/sraAd = "."' >> .ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/apps/sraPileup/volumes/ad = "."' >> .ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/apps/sraRealign/volumes/ad = "."' >> .ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/root = "."' >> .ncbi/user-settings.mkfg
RUN echo '/repository/user/default-path = "/root/ncbi"' >> .ncbi/user-settings.mkfg
RUN echo '/repository/user/main/public/cache-disabled = "true"' >> .ncbi/user-settings.mkfg

COPY wort wort
COPY config config

ENV RAYON_NUM_THREADS 3
CMD celery -A wort.blueprints.compute.tasks worker -Q compute_small,compute_medium,genomes --without-gossip --without-mingle --without-heartbeat -l INFO -c 1
