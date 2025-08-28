# wort

wort is a repository for sourmash signatures, currently focused on
indexing microbial datasets from public datasets like the
[NCBI Sequence Read Archive](https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?)
and the [JGI Integrated Microbial Genomes and Microbiomes](https://img.jgi.doe.gov/)

Here are some example pages for these datasets:
  - SRA: <a href='/view/sra/DRR013902/'>DRR013902</a></li>
  - IMG: <a href='/view/img/2522125045'>2728369338</a></li>

For more info check the <a href='https://github.com/luizirber/2018-biods'>poster</a>
presented at [Biological Data Science 2018](https://meetings.cshl.edu/meetings.aspx?meet=DATA&year=18).

## Environment setup

This repository uses environment files referenced by docker-compose:
- env.production (for the web and db services)
- iam/wort_s3.env (for the Celery worker’s AWS access)

Quick start:
1) Copy the example env files and edit as needed:
```
cp env.production.example env.production
cp iam/wort_s3.env.example iam/wort_s3.env
```
   - If the iam directory is missing (it is gitignored by default), you can create it and bootstrap the env file with:
```
bash scripts/setup_iam.sh
```
2) Set valid AWS credentials in iam/wort_s3.env (ACCESS_KEY_ID, SECRET_ACCESS_KEY, DEFAULT_REGION) with permissions for S3 (wort-results, wort-sra, wort-genomes) and SQS. The web service does not require these credentials to start; only the Celery worker needs them.
3) Optionally adjust env.production (DATABASE_URL, POSTGRES_* values, SECRET_KEY) for your setup.

To run locally with Docker:

```
docker compose up --build
```

The web UI will be available on http://localhost:8082/.

### Running database migrations
- One-off (recommended; honors ENTRYPOINT so PATH is set):
```
docker compose run --rm web python -m flask db upgrade
```
- If your stack is already up and you prefer exec (note: ENTRYPOINT isn’t re-run, so PATH may miss python):
```
# Use the full Pixi-managed Python path
docker compose exec web /app/.pixi/envs/web/bin/python -m flask db upgrade
```

If you see “Flask not found” or “python: executable file not found in $PATH”, see Troubleshooting below.

### Troubleshooting: Postgres container complains about missing superuser password

If you see an error like:

  Error: Database is uninitialized and superuser password is not specified.
  You must specify POSTGRES_PASSWORD to a non-empty value for the superuser.

This comes from the official Postgres image validating its required env vars during the first initialization. Fix it by one of the following:
- Ensure env.production sets a non-empty POSTGRES_PASSWORD (the default provided here is `wort`).
- For local development only, you can allow trust authentication by setting POSTGRES_HOST_AUTH_METHOD=trust in env.production (already included). Do NOT use this in production.

Important: If Postgres has already initialized its data directory, changing env vars won’t re-run initdb. To reinitialize with the new env vars, stop and remove containers and the data volume:

```
# WARNING: this deletes your local Postgres data in ./data/postgres-data
docker compose down -v
rm -rf data/postgres-data
docker compose up --build
```

This should resolve the startup error.

### Troubleshooting: “Flask not found” inside the web container
This usually means the `flask` console script is not on PATH for your shell inside the running container. Use the module form which is robust:
```
docker compose run --rm web python -m flask db upgrade
```
If using exec on an already running container (ENTRYPOINT not re-run), use the full path:
```
docker compose exec web /app/.pixi/envs/web/bin/python -m flask db upgrade
```

### Troubleshooting: “python: executable file not found in $PATH”
`docker compose exec` attaches without the ENTRYPOINT shell-hook, so PATH may not include the Pixi environment. Either use `run` (recommended) or the full Python path:
```
docker compose exec web /app/.pixi/envs/web/bin/python --version
```
If Python is missing, rebuild the image:
```
docker compose build web && docker compose up -d web
```

### Notes on AWS credentials
- Only the Celery worker requires AWS credentials (for SQS and S3). The web service can start without them.
- Place credentials in `iam/wort_s3.env` (use the example file to get started) and ensure the IAM user/role can access:
  - S3 buckets: `wort-results`, `wort-sra`, `wort-genomes`
  - SQS queues with prefix `wort-`

([wort][0] is the next step in whisky fabrication after mashing)

[0]: https://en.wikipedia.org/wiki/Wort
