# Archive

This machine contains a local copy of all wort signatures,
synced from AWS S3 buckets.

```
.
├── branchwater-index
├── filelists
│   ├── genomes_20250829
│   ├── img_20250829
│   └── sra_20250829
├── manifests
│   ├── genomes_20250829.csv
│   ├── img_20250829.csv
│   └── sra_20250829.csv
├── s3_sync.sh
├── scripts
│   ├── csv_to_parquet.py
│   ├── genomes.sbatch
│   ├── img.sbatch
│   └── sra.sbatch
├── slurm_logs/
├── update_logs/
│   ├── 20250825_genomes
│   ├── 20250825_img
│   └── 20250825_sra
├── wort-genomes
│   └── sigs
├── wort-img
│   └── sigs
└── wort-sra
    └── sigs
```

## The `s3_sync.sh` script

## Updating manifests

