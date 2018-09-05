#[macro_use]
extern crate clap;
extern crate reqwest;

use std::error::Error;

use clap::App;

fn viewer(db: &str, dataset_id: &str) -> Result<(), Box<Error>> {
    let url = format!("https://wort.oxli.org/view/{}/{}", db, dataset_id);
    let mut res = reqwest::get(&url)?;
    std::io::copy(&mut res, &mut std::io::stdout())?;
    Ok(())
}

fn main() {
    let yml = load_yaml!("wort.yml");
    let m = App::from_yaml(yml).get_matches();

    if let Some(cmd) = m.subcommand_matches("viewer") {
        viewer(
            cmd.value_of("database").unwrap(),
            cmd.value_of("dataset_id").unwrap(),
        );
    }
}
