import sys
import argparse
import datetime
from Bio import Entrez
import pandas as pd

def main(args):
    # Get yesterday's date
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    day_to_check = yesterday.strftime("%Y/%m/%d")

    Entrez.email = args.email  # Set email address

    # Perform the Biopython search for genomic samples
    query_dna = f'("{day_to_check}"[PDAT] : "3000"[PDAT]) AND "biomol dna"[Properties] NOT amplicon[All Fields] NOT "Metazoa"[orgn:__txid33208] NOT "Streptophyta"[orgn:__txid35493] NOT "METAGENOMIC"[Source]'
    handle_dna = Entrez.esearch(db='sra', term=query_dna, retmax=1000000)
    record_dna = Entrez.read(handle_dna)
    handle_dna.close()

    # Fetch the genomic sample records using Entrez.efetch
    id_list_dna = record_dna["IdList"]
    if not id_list_dna:
        print("No genomic samples found for yesterday.")
    else:
        handle_dna_records = Entrez.efetch(db='sra', id=id_list_dna, rettype='runinfo', retmode='text')
        df_dna = pd.read_csv(handle_dna_records)

        # Save the genomic sample records to a CSV file
        df_dna.to_csv(args.genomes, index=False)
        print(f"Genomic samples saved to: {args.genomes}")

    # Perform the Biopython search for metagenomic samples
    query_metagenomic = f'("{day_to_check}"[PDAT] : "3000"[PDAT]) NOT amplicon[All Fields] AND "METAGENOMIC"[Source]'
    handle_metagenomic = Entrez.esearch(db='sra', term=query_metagenomic, retmax=1000000)
    record_metagenomic = Entrez.read(handle_metagenomic)
    handle_metagenomic.close()

    # Fetch the metagenomic sample records using Entrez.efetch
    id_list_metagenomic = record_metagenomic["IdList"]
    if not id_list_metagenomic:
        print("No metagenomic samples found for yesterday.")
    else:
        handle_metagenomic_records = Entrez.efetch(db='sra', id=id_list_metagenomic, rettype='runinfo', retmode='text')
        df_metagenomic = pd.read_csv(handle_metagenomic_records)

        # Save the metagenomic sample records to a CSV file
        df_metagenomic.to_csv(args.metagenomes, index=False)
        print(f"Metagenomic samples saved to: {args.genomes}")

def cmdline(sys_args):
    "Command line entry point w/argparse action."
    p = argparse.ArgumentParser(description="Download runinfo for metagenomes and genomes released yesterday.")
    p.add_argument('--metagenomes', type=str, help="output file for metagenomes")
    p.add_argument('--genomes', type=str, help="output file for genomes")
    p.add_argument('--email', default='admin@sourmash.bio')
    # Parse command line arguments
    args = p.parse_args()
    # Download sequences for the specified accession
    return main(args)

if __name__ == '__main__':
    returncode = cmdline(sys.argv[1:])
    sys.exit(returncode)
