#!/bin/bash

set -ex

mkdir -p update_logs/

# using s5cmd
pixi exec s5cmd --stat --json sync --size-only 's3://wort-sra/*' wort-sra/ &> update_logs/"$(date +%Y%m%d)_sra" &
pixi exec s5cmd --stat --json sync --size-only 's3://wort-genomes/*' wort-genomes/ &> update_logs/"$(date +%Y%m%d)_genomes" &
pixi exec s5cmd --stat --json sync --size-only 's3://wort-img/*' wort-img/ &> update_logs/"$(date +%Y%m%d)_img" &
wait
