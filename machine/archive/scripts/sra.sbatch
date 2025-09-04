#!/bin/bash 
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=100:00:00
#SBATCH --mem=200GB
#SBATCH --partition=high2
#SBATCH -A ctbrowngrp
#SBATCH -o slurm_logs/sra-%j.log

set -exu -o pipefail

cd $SLURM_SUBMIT_DIR

#find wort-sra/ -iname "*.sig" > filelists/sra_20250829

RAYON_NUM_THREADS=32 RUST_LOG=info ./branchwater-index manifest -o manifests/sra_20250829.csv filelists/sra_20250829
