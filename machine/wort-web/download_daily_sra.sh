#! /bin/bash -login

set -exu

DAY_TO_CHECK=${1:-yesterday}

day_slash=$(date -d $DAY_TO_CHECK +%Y/%m/%d)
day_plain=$(date -d $DAY_TO_CHECK +%Y%m%d)

output=outputs/${day_plain}.csv
output_metagenomes=outputs_metagenomes/${day_plain}.csv

wget -O ${output} 'http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term=("'${day_slash}'"[PDAT] : "'${day_slash}'"[PDAT]) AND "biomol dna"[Properties] NOT amplicon[All Fields] NOT "Metazoa"[orgn:__txid33208] NOT "Streptophyta"[orgn:__txid35493] NOT "metagenomic"[Source]'

wget -O ${output_metagenomes} 'http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term=("'${day_slash}'"[PDAT] : "'${day_slash}'"[PDAT]) NOT amplicon[All Fields] AND "METAGENOMIC"[Source]'

/usr/local/bin/docker-compose exec -T web flask shell -c "%run -i integrations/add_dataset_info.py integrations/${output}"
/home/ubuntu/.local/bin/pipenv run python submit.py ${output} | tee logs/`date +%Y%m%d_%H%M`.submitted

/usr/local/bin/docker-compose exec -T web flask shell -c "%run -i integrations/add_dataset_info.py integrations/${output_metagenomes}"
/home/ubuntu/.local/bin/pipenv run python submit.py ${output_metagenomes} | tee logs_metagenomes/`date +%Y%m%d_%H%M`.submitted
