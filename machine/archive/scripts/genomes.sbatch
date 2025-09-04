#!/bin/bash 
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=40:00:00
#SBATCH --mem=20GB
#SBATCH --partition=high2
#SBATCH -A ctbrowngrp
#SBATCH -o slurm_logs/genomes-%j.log

set -exu -o pipefail

cd $SLURM_SUBMIT_DIR

#find wort-genomes/ -iname "*.sig" > filelists/genomes_20250829

RAYON_NUM_THREADS=16 RUST_LOG=info ./branchwater-index manifest -o manifests/genomes_20250829.csv filelists/genomes_20250829
