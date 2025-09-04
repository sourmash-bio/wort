#!/bin/bash 
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=40:00:00
#SBATCH --mem=20GB
#SBATCH --partition=high2
#SBATCH -A ctbrowngrp
#SBATCH -o slurm_logs/sha256-%j.log

set -exu -o pipefail

cd $SLURM_SUBMIT_DIR

parallel -j16  sha256sum :::: filelists/img_20250829 > filelists/img_20250829.sha256
parallel -j16  sha256sum :::: filelists/genomes_20250829 > filelists/genomes_20250829.sha256
parallel -j16  sha256sum :::: filelists/sra_20250829 > filelists/sra_20250829.sha256
