#!/bin/bash

set -ex

# using s5cmd
pixi exec s5cmd ls s3://wort-genomes/sigs/ > filelists/genomes_20250829.s3 &
pixi exec s5cmd ls s3://wort-img/sigs/ > filelists/img_20250829.s3 &
pixi exec s5cmd ls s3://wort-sra/sigs/ > filelists/sra_20250829.s3 &

wait
