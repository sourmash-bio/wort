#[macro_use]
extern crate clap;
extern crate reqwest;
#[macro_use]
extern crate serde_derive;
extern crate flate2;

use std::error::Error;
use std::fs::File;
use std::io::{BufReader, Read};

use clap::App;
use flate2::bufread::GzEncoder;
use flate2::Compression;
use reqwest::multipart::{Form, Part};

const BASEURL: &'static str = "https://wort.oxli.org/v1";

#[derive(Debug, Deserialize)]
struct Response {
    status: String,
}

fn view(db: &str, dataset_id: &str) -> Result<(), Box<Error>> {
    let url = format!("{}/view/{}/{}", BASEURL, db, dataset_id);
    let mut res = reqwest::get(&url)?;
    std::io::copy(&mut res, &mut std::io::stdout())?;
    Ok(())
}

fn submit(db: String, dataset_id: String, token: &str, filename: &str) -> Result<(), Box<Error>> {
    TODO: gzip compress before sending
    let f = std::fs::File::open(filename)?;
    let b = BufReader::new(f);
    let mut gz = GzEncoder::new(b, Compression::best());
    let mut buf = Vec::new();
    gz.read_to_end(&mut buf)?;
    let file = Part::reader(&buf[..]).mime_str("application/gzip")?;

    let form = Form::new().part("file", file);

    let url = format!("{}/submit/{}/{}", BASEURL, db, dataset_id);

    let client = reqwest::Client::new();
    let mut res = client
        .post(&url)
        .bearer_auth(token)
        .multipart(form)
        .send()?;
    println!("{}", res.json::<Response>()?.status);
    Ok(())
}

fn main() -> Result<(), Box<Error>> {
    let yml = load_yaml!("wort.yml");
    let m = App::from_yaml(yml).get_matches();

    match m.subcommand_name() {
        Some("view") => {
            let cmd = m.subcommand_matches("view").unwrap();
            view(
                cmd.value_of("database").unwrap(),
                cmd.value_of("dataset_id").unwrap(),
            )
        }
        Some("submit") => {
            let cmd = m.subcommand_matches("submit").unwrap();
            submit(
                cmd.value_of("database").unwrap().into(),
                cmd.value_of("dataset_id").unwrap().into(),
                cmd.value_of("token").unwrap(),
                cmd.value_of("signature").unwrap(),
            )
        }
        None => Ok(()), // TODO: should be error
        _ => Ok(()),    // TODO: should be error
    }
}
