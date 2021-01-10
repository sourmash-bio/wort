use std::cmp;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};

use log::info;
use structopt::StructOpt;

use rayon::prelude::*;
use sourmash::index::greyhound::RevIndex;
use sourmash::signature::{Signature, SigsTrait};
use sourmash::sketch::minhash::{max_hash_for_scaled, KmerMinHash};
use sourmash::sketch::Sketch;

#[derive(StructOpt, Debug)]
enum Cli {
    Gather {
        /// Query signature
        #[structopt(parse(from_os_str))]
        query_path: PathBuf,

        /// Precomputed index or list of reference signatures
        #[structopt(parse(from_os_str))]
        siglist: PathBuf,

        /// ksize
        #[structopt(short = "k", long = "ksize", default_value = "31")]
        ksize: u8,

        /// scaled
        #[structopt(short = "s", long = "scaled", default_value = "1000")]
        scaled: usize,

        /// threshold_bp
        #[structopt(short = "t", long = "threshold_bp", default_value = "50000")]
        threshold_bp: usize,

        /// The path for output
        #[structopt(parse(from_os_str), short = "o", long = "output")]
        output: Option<PathBuf>,

        /// Is the index a list of signatures?
        #[structopt(long = "--from-file")]
        from_file: bool,

        /// Delay loading queries into memory
        #[structopt(long = "--lazy")]
        lazy: bool,

        /// Preload reference signatures into memory
        #[structopt(long = "--preload")]
        preload: bool,
    },
    Index {
        /// The path for output
        #[structopt(parse(from_os_str))]
        output: PathBuf,

        /// List of reference signatures
        #[structopt(parse(from_os_str))]
        siglist: PathBuf,

        /// ksize
        #[structopt(short = "k", long = "ksize", default_value = "31")]
        ksize: u8,

        /// scaled
        #[structopt(short = "s", long = "scaled", default_value = "1000")]
        scaled: usize,
    },
}

fn read_paths<P: AsRef<Path>>(paths_file: P) -> Result<Vec<PathBuf>, Box<dyn std::error::Error>> {
    let paths = BufReader::new(File::open(paths_file)?);
    Ok(paths
        .lines()
        .map(|line| {
            let mut path = PathBuf::new();
            path.push(line.unwrap());
            path
        })
        .collect())
}

fn build_template(ksize: u8, scaled: usize) -> Sketch {
    let max_hash = max_hash_for_scaled(scaled as u64);
    let template_mh = KmerMinHash::builder()
        .num(0u32)
        .ksize(ksize as u32)
        .max_hash(max_hash)
        .build();
    Sketch::MinHash(template_mh)
}

fn index<P: AsRef<Path>>(
    siglist: P,
    template: Sketch,
    output: P,
) -> Result<(), Box<dyn std::error::Error>> {
    info!("Loading siglist");
    let index_sigs = read_paths(siglist)?;
    info!("Loaded {} sig paths in siglist", index_sigs.len());

    let revindex = RevIndex::new(&index_sigs, &template, 0, None, false);

    info!("Saving index");
    let wtr = niffler::to_path(
        output,
        niffler::compression::Format::Gzip,
        niffler::compression::Level::One,
    )?;
    serde_json::to_writer(wtr, &revindex)?;

    Ok(())
}

fn gather<P: AsRef<Path>>(
    queries_file: P,
    siglist: P,
    template: Sketch,
    threshold_bp: usize,
    output: Option<P>,
    from_file: bool,
    lazy: bool,
    preload: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    info!("Loading queries");

    let queries_path = read_paths(queries_file)?;

    let mut queries = vec![];
    let mut threshold = usize::max_value();
    if !lazy || from_file {
        for query_path in &queries_path {
            let query_sig = Signature::from_path(query_path)?;
            let mut query = None;
            for sig in &query_sig {
                if let Some(sketch) = sig.select_sketch(&template) {
                    if let Sketch::MinHash(mh) = sketch {
                        query = Some(mh.clone());
                        // TODO: deal with mh.size() == 0
                        let t = threshold_bp / (cmp::max(mh.size(), 1) * mh.scaled() as usize);
                        threshold = cmp::min(threshold, t);
                    }
                }
            }
            if let Some(q) = query {
                queries.push(q);
            } else {
                todo!("throw error, some sigs were not valid")
            };
        }
    }

    info!("Loaded {} query signatures", queries_path.len());

    // Step 1: filter and prepare a reduced RevIndex for all queries
    let revindex = if from_file {
        info!("Loading siglist");
        let search_sigs = read_paths(siglist)?;
        info!("Loaded {} sig paths in siglist", search_sigs.len());

        RevIndex::new(&search_sigs, &template, threshold, Some(&queries), preload)
    } else {
        if lazy {
            RevIndex::load(siglist, None)
        } else {
            RevIndex::load(siglist, Some(&queries))
        }?
    };

    let outdir: PathBuf = if let Some(p) = output {
        p.as_ref().into()
    } else {
        let mut path = PathBuf::new();
        path.push("outputs");
        path
    };
    std::fs::create_dir_all(&outdir)?;

    // Step 2: Gather using the RevIndex and a specific Counter for each query
    queries_path.par_iter().enumerate().for_each(|(i, query)| {
        let query = if lazy {
            let query_sig = Signature::from_path(query).unwrap();
            let mut query = None;
            for sig in &query_sig {
                if let Some(sketch) = sig.select_sketch(&template) {
                    if let Sketch::MinHash(mh) = sketch {
                        if mh.size() == 0 {
                            return;
                        }
                        query = Some(mh.clone());
                    }
                }
            }
            query.unwrap()
        } else {
            queries[i].clone()
        };

        info!("Build counter for query");
        let counter = revindex.counter_for_query(&query);
        let threshold = threshold_bp / (query.size() * query.scaled() as usize);

        info!("Starting gather");
        let matches = revindex.gather(counter, threshold, &query).unwrap();

        info!("Saving {} matches", matches.len());
        let mut path = outdir.clone();
        path.push(queries_path[i].file_name().unwrap());

        let mut out = BufWriter::new(File::create(path).unwrap());
        for m in matches {
            writeln!(out, "{}", m.filename().as_str()).unwrap();
        }
        info!("Finishing query {:?}", queries_path[i]);
    });

    info!("Finished");
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    match Cli::from_args() {
        Cli::Gather {
            query_path,
            siglist,
            ksize,
            scaled,
            threshold_bp,
            output,
            from_file,
            lazy,
            preload,
        } => {
            let template = build_template(ksize, scaled);

            gather(
                query_path,
                siglist,
                template,
                threshold_bp,
                output,
                from_file,
                lazy,
                preload,
            )?
        }
        Cli::Index {
            output,
            siglist,
            ksize,
            scaled,
        } => {
            let template = build_template(ksize, scaled);

            index(siglist, template, output)?
        }
    };

    Ok(())
}
