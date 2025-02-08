FROM ghcr.io/prefix-dev/pixi:0.40.3 AS build

WORKDIR /app

COPY . .

RUN --mount=type=cache,target=/root/.cache/rattler/cache,sharing=private pixi install

RUN pixi run build-wheel

RUN pixi run -e web postinstall-prod
RUN pixi shell-hook -e web > /shell-hook-web
RUN echo 'exec "$@"' >> /shell-hook-web

RUN pixi run -e worker postinstall-prod
RUN pixi shell-hook -e worker > /shell-hook-worker
RUN echo 'exec "$@"' >> /shell-hook-worker

#--------------------

FROM ubuntu:24.04 AS web

# only copy the production environment into prod container
COPY --from=build /app/.pixi/envs/web /app/.pixi/envs/web
COPY --from=build /shell-hook-web /shell-hook

RUN groupadd user && \
    useradd --create-home --home-dir /home/user -g user -s /bin/bash user

USER user

COPY wortapp.py /app
COPY config/ /app/config
COPY migrations/ /app/migrations

WORKDIR /app

ENTRYPOINT ["/bin/bash", "/shell-hook"]
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--access-logfile", "-", "'wortapp:create_app()'"]

#--------------------

FROM ubuntu:24.04 AS worker

# only copy the production environment into prod container
COPY --from=build /app/.pixi/envs/worker /app/.pixi/envs/worker
COPY --from=build /shell-hook-worker /shell-hook

RUN groupadd user && \
    useradd --create-home --home-dir /home/user -g user -s /bin/bash user

COPY wortapp.py /app
COPY config/ /app/config

WORKDIR /app

USER user

# Configure sra-toolkit to disable cache
RUN mkdir ~/.ncbi

RUN echo '## auto-generated configuration file - DO NOT EDIT ##''' >> ~/.ncbi/user-settings.mkfg
RUN echo '' >> ~/.ncbi/user-settings.mkfg
RUN echo '/LIBS/GUID = "7737545d-30d4-4d05-875a-2c562df521d5"' >> ~/.ncbi/user-settings.mkfg
RUN echo '/config/default = "false"' >> ~/.ncbi/user-settings.mkfg
RUN echo '/libs/vdb/quality = "ZR"' >> ~/.ncbi/user-settings.mkfg
RUN echo '/libs/cloud/accept_aws_charges = "false"' >> ~/.ncbi/user-settings.mkfg
RUN echo '/libs/cloud/report_instance_identity = "false"' >> ~/.ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/apps/file/volumes/flatAd = "."' >> ~/.ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/apps/refseq/volumes/refseqAd = "."' >> ~/.ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/apps/sra/volumes/sraAd = "."' >> ~/.ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/apps/sraPileup/volumes/ad = "."' >> ~/.ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/apps/sraRealign/volumes/ad = "."' >> ~/.ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/apps/wgs/volumes/wgsAd = "."' >> ~/.ncbi/user-settings.mkfg
RUN echo '/repository/user/ad/public/root = "."' >> ~/.ncbi/user-settings.mkfg
RUN echo '/repository/user/default-path = "/home/user/ncbi"' >> ~/.ncbi/user-settings.mkfg
RUN echo '/repository/user/main/public/cache-disabled = "true"' >> ~/.ncbi/user-settings.mkfg
RUN echo '/tools/prefetch/download_to_cache = "false"' >> ~/.ncbi/user-settings.mkfg

ENV RAYON_NUM_THREADS=3
ENTRYPOINT ["/bin/bash", "/shell-hook"]
CMD ["celery", "-A", "wort.blueprints.compute.tasks", "worker", "-Q", "compute_small,compute_medium,genomes", "--without-gossip", "--without-mingle", "--without-heartbeat", "-l", "INFO", "-c", "1"]
