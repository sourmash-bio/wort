use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;
use std::path::PathBuf;
use std::sync::Arc;

use sourmash::index::greyhound::{GatherResult, RevIndex};
use sourmash::signature::{Signature, SigsTrait};
use sourmash::sketch::minhash::{max_hash_for_scaled, KmerMinHash};
use sourmash::sketch::Sketch;
use structopt::StructOpt;
use tide::prelude::*;
use tide::{self, Body, Request};

#[derive(StructOpt, Debug)]
struct Cli {
    /// Index to serve
    #[structopt(parse(from_os_str))]
    index_path: PathBuf,

    /// Is the index a list of signatures?
    #[structopt(long = "--from-file")]
    from_file: bool,

    /// ksize
    #[structopt(short = "k", long = "ksize", default_value = "31")]
    ksize: u8,

    /// scaled
    #[structopt(short = "s", long = "scaled", default_value = "1000")]
    scaled: usize,
}

#[derive(Clone)]
struct RevIndexState {
    revindex: Arc<RevIndex>,
}

#[derive(thiserror::Error, Debug)]
enum Error {
    #[error("Signature is not compatible with index")]
    UnsupportedSignature,

    #[error("Sketch is not compatible with index")]
    UnsupportedSketch,

    #[error("Couldn't load the index ({0})")]
    IndexLoading(String),

    #[error("Error during gather ({0})")]
    Gather(String),
}

impl RevIndexState {
    fn load<P: AsRef<Path>>(
        path: P,
        from_file: bool,
        scaled: Option<usize>,
        ksize: Option<u8>,
    ) -> Result<Self, Error> {
        let revindex = if from_file {
            let paths = BufReader::new(
                File::open(path).map_err(|e| Error::IndexLoading(format!("{}", e)))?,
            );
            let sigs: Vec<PathBuf> = paths
                .lines()
                .map(|line| {
                    let mut path = PathBuf::new();
                    path.push(line.unwrap());
                    path
                })
                .collect();

            let max_hash = max_hash_for_scaled(scaled.unwrap() as u64);
            let template_mh = KmerMinHash::builder()
                .num(0u32)
                .ksize(ksize.unwrap() as u32)
                .max_hash(max_hash)
                .build();

            RevIndex::new(&sigs, &Sketch::MinHash(template_mh), 0, None, true)
        } else {
            RevIndex::load(path, None).map_err(|e| Error::IndexLoading(format!("{}", e)))?
        };

        Ok(Self {
            revindex: Arc::new(revindex),
        })
    }

    fn gather(&self, query: Signature) -> Result<Vec<GatherResult>, Error> {
        if let Some(sketch) = query.select_sketch(&self.revindex.template()) {
            if let Sketch::MinHash(mh) = sketch {
                let counter = self.revindex.counter_for_query(&mh);
                Ok(self
                    .revindex
                    .gather(counter, 0, mh)
                    .map_err(|e| Error::Gather(format!("{}", e)))?)
            } else {
                Err(Error::UnsupportedSketch)
            }
        } else {
            Err(Error::UnsupportedSignature)
        }
    }

    fn search(
        &self,
        query: Signature,
        similarity: bool,
        threshold: f64,
    ) -> Result<Vec<String>, Error> {
        if let Some(sketch) = query.select_sketch(&self.revindex.template()) {
            if let Sketch::MinHash(mh) = sketch {
                let counter = self.revindex.counter_for_query(&mh);
                let threshold = (threshold * mh.size() as f64) as usize;
                Ok(self
                    .revindex
                    .search(counter, similarity, threshold)
                    .map_err(|e| Error::Gather(format!("{}", e)))?)
            } else {
                Err(Error::UnsupportedSketch)
            }
        } else {
            Err(Error::UnsupportedSignature)
        }
    }
}

fn parse_sig(raw_data: &[u8]) -> Result<Signature, Error> {
    let sig = Signature::from_reader(&raw_data[..])
        .expect("Error loading sig")
        .swap_remove(0);
    Ok(sig)
}

#[derive(Debug, Deserialize)]
struct Search {
    similarity: bool,
    threshold: f64,
    signature: String,
}

#[async_std::main]
async fn main() -> tide::Result<()> {
    tide::log::start();

    let Cli {
        index_path,
        from_file,
        scaled,
        ksize,
    } = Cli::from_args();

    let mut app = tide::with_state(RevIndexState::load(
        index_path,
        from_file,
        Some(scaled),
        Some(ksize),
    )?);

    app.at("/gather")
        .post(|mut req: Request<RevIndexState>| async move {
            let raw_data = req.body_bytes().await?;
            let sig = parse_sig(&raw_data)?;
            let result = req.state().gather(sig)?;

            Ok(Body::from_json(&result)?)
        });

    app.at("/search")
        .post(|mut req: Request<RevIndexState>| async move {
            let Search {
                similarity,
                threshold,
                signature,
            } = req.body_json().await?;
            let sig = parse_sig(&signature.as_bytes())?;

            let result = req.state().search(sig, similarity, threshold)?;

            Ok(Body::from_json(&result)?)
        });

    app.at("/")
        .get(|_| async { Ok(Body::from_file("../frontend/static/index.html").await?) })
        .serve_dir("../frontend/static")?;
    app.listen("127.0.0.1:8081").await?;

    Ok(())
}
