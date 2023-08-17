#! /bin/bash -login

set -exu

DAY_TO_CHECK=${1:-yesterday}
day_plain=$(date -d $DAY_TO_CHECK +%Y%m%d)

output_genomes=outputs/${day_plain}.csv
output_metagenomes=outputs_metagenomes/${day_plain}.csv
output_metatranscriptomes=outputs_metatranscriptomes/${day_plain}.csv

submit_csv() {
  docker-compose exec -T web flask shell -c "%run -i machine/wort-web/add_dataset_info.py machine/wort-web/$1"
  pipenv run python submit.py $1 | tee $2/`date +%Y%m%d_%H%M`.submitted
}

docker-compose exec -T web flask shell -c "%run -i machine/wort-web/daily-sra-biopython.py --metagenomes machine/wort-web/${output_metagenomes} --genomes machine/wort-web/${output_genomes} --metatranscriptomes machine/wort-web/${output_metatranscriptomes}"

submit_csv ${output_genomes} logs &
submit_csv ${output_metagenomes} logs_metagenomes &
submit_csv ${output_metatranscriptomes} logs_metatranscriptomes &

wait
