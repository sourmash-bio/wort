#! /bin/bash -login

set -exu

DAY_TO_CHECK=${1:-yesterday}

day_plain=$(date -d $DAY_TO_CHECK +%Y%m%d)

output_genomes=outputs/${day_plain}.csv
output_metagenomes=outputs_metagenomes/${day_plain}.csv

conda activate biopython
python daily-sra-biopython.py --metagenomes ${output_metagenomes} --genomes ${output_genomes}

docker-compose exec -T web flask shell -c "%run -i machine/wort-web/add_dataset_info.py machine/wort-web/${output_genomes}"
pipenv run python submit.py ${output_genomes} | tee logs/`date +%Y%m%d_%H%M`.submitted

docker-compose exec -T web flask shell -c "%run -i machine/wort-web/add_dataset_info.py machine/wort-web/${output_metagenomes}"
pipenv run python submit.py ${output_metagenomes} | tee logs_metagenomes/`date +%Y%m%d_%H%M`.submitted
