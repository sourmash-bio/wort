#!/bin/bash 
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=01:00:00
#SBATCH --mem=10GB
#SBATCH --partition=bmm
#SBATCH -o slurm_logs/img-%j.log

set -exu -o pipefail

cd $SLURM_SUBMIT_DIR

#find wort-img/ -iname "*.sig" > filelists/img_20250829

RAYON_NUM_THREADS=32 RUST_LOG=info ./branchwater-index manifest -o manifests/img_20250829.csv filelists/img_20250829
