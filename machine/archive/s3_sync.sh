#!/bin/bash

set -ex

DATE="${1:-$(date +%Y%m%d)}"

mkdir -p update_logs/

# using s5cmd
5cmd --stat --json sync --size-only 's3://wort-sra/*' wort-sra/ &> update_logs/"${DATE}_sra" &
s5cmd --stat --json sync --size-only 's3://wort-genomes/*' wort-genomes/ &> update_logs/"${DATE}_genomes" &
s5cmd --stat --json sync --size-only 's3://wort-img/*' wort-img/ &> update_logs/"${DATE}_img" &
wait
