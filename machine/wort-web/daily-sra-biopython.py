import sys
import argparse
import datetime
from Bio import Entrez
import pandas as pd

def main(args):
    day_to_check = args.start.strftime("%Y/%m/%d")
    Entrez.email = args.email  # Set email address

    # Perform the Biopython search for genomic samples
    query_dna = f'("{day_to_check}"[PDAT] : "3000"[PDAT]) AND "biomol dna"[Properties] NOT amplicon[All Fields] NOT "Metazoa"[orgn:__txid33208] NOT "Streptophyta"[orgn:__txid35493] NOT "METAGENOMIC"[Source]'
    query_metagenomic = f'("{day_to_check}"[PDAT] : "3000"[PDAT]) NOT amplicon[All Fields] AND "METAGENOMIC"[Source]'
    query_metatranscriptomic = f'("{day_to_check}"[PDAT] : "3000"[PDAT]) NOT amplicon[All Fields] AND "METATRANSCRIPTOMIC"[Source]'

    download_entrez(query_dna, args.genomes, "genomic")
    download_entrez(query_metagenomic, args.metagenomes, "metagenomic")
    download_entrez(query_metatranscriptomic, args.metatranscriptomes, "metatranscriptomic")


def download_entrez(query, output, data_type="genomic"):
    handle = Entrez.esearch(db='sra', term=query, retmax=10000)
    record = Entrez.read(handle)
    handle.close()

    # Fetch the genomic sample records using Entrez.efetch
    id_list = record["IdList"]
    if not id_list:
        print(f"No {data_type} samples found for yesterday.")
    else:
        handle_records = Entrez.efetch(db='sra', id=id_list, rettype='runinfo', retmode='text')
        df = pd.read_csv(handle_records)

        # Save the genomic sample records to a CSV file
        df.to_csv(output, index=False)
        print(f"{data_type} samples saved to: {output}")


if __name__ == '__main__':
    # Get yesterday's date
    yesterday = datetime.date.today() - datetime.timedelta(days=1)

    p = argparse.ArgumentParser(description="Download runinfo for metagenomes, metatranscriptomics, and genomes released yesterday.")
    p.add_argument('--metagenomes', type=str, help="output file for metagenomes")
    p.add_argument('--genomes', type=str, help="output file for genomes")
    p.add_argument('--metatranscriptomes', type=str, help="output file for metatranscriptomes")
    p.add_argument('--email', default='admin@sourmash.bio')
    p.add_argument('--start', default=yesterday, type=datetime.date.fromisoformat)
    # Parse command line arguments
    args = p.parse_args()

    # Download sequences for the specified accession
    sys.exit(main(args))
