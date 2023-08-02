#! /bin/bash -login

set -exu

DAY_TO_CHECK=${1:-yesterday}

day_slash=$(date -d $DAY_TO_CHECK +%Y/%m/%d)
day_plain=$(date -d $DAY_TO_CHECK +%Y%m%d)

output=outputs/${day_plain}.csv
output_metagenomes=outputs_metagenomes/${day_plain}.csv

# Perform the EDirect search for genomic samples
esearch -db sra -query "(${day_slash}[PDAT] : 3000[PDAT]) AND biomol dna[Properties] NOT amplicon[All Fields] NOT Metazoa[orgn:__txid33208] NOT Streptophyta[orgn:__txid35493] NOT METAGENOMIC[Source]" | efetch -format runinfo -mode text > ${output}

# Perform the EDirect search for metagenomic samples
esearch -db sra -query "(${day_slash}[PDAT] : 3000[PDAT]) NOT amplicon[All Fields] AND METAGENOMIC[Source]" | efetch -format runinfo -mode text > ${output_metagenomes}

echo "DNA samples saved to: ${output}"
echo "Metagenomic samples saved to: ${output_metagenomes}"

/usr/local/bin/docker-compose exec -T web flask shell -c "%run -i machine/wort-web/add_dataset_info.py machine/wort-web/${output}"
/home/ubuntu/.local/bin/pipenv run python submit.py ${output} | tee logs/`date +%Y%m%d_%H%M`.submitted

/usr/local/bin/docker-compose exec -T web flask shell -c "%run -i machine/wort-web/add_dataset_info.py machine/wort-web/${output_metagenomes}"
/home/ubuntu/.local/bin/pipenv run python submit.py ${output_metagenomes} | tee logs_metagenomes/`date +%Y%m%d_%H%M`.submitted
