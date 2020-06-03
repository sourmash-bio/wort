use std::error::Error as _;

use clap::{load_yaml, App};
use dialoguer::{Input, Password};
use eyre::{eyre, Result};
use reqwest::StatusCode;
use serde::Deserialize;

const BASEURL: &'static str = "https://wort.oxli.org/v1";
const SERVICENAME: &'static str = "wort";

#[derive(Debug, Deserialize)]
struct Response {
    status: String,
}

fn view(db: &str, dataset_id: &str) -> Result<()> {
    let url = format!("{}/view/{}/{}", BASEURL, db, dataset_id);
    let mut res = reqwest::blocking::get(&url)?;
    std::io::copy(&mut res, &mut std::io::stdout())?;
    Ok(())
}

fn compute(db: String, dataset_id: String, token: &str) -> Result<()> {
    let url = format!("{}/compute/{}/{}", BASEURL, db, dataset_id);

    let client = reqwest::blocking::Client::new();
    let res = client.post(&url).bearer_auth(token).send()?;
    println!("{}", res.json::<Response>()?.status);
    Ok(())
}

fn submit(db: String, dataset_id: String, token: &str, filename: &str) -> Result<()> {
    let form = reqwest::blocking::multipart::Form::new().file("file", filename)?;

    let url = format!("{}/submit/{}/{}", BASEURL, db, dataset_id);

    let client = reqwest::blocking::Client::new();
    let res = client
        .post(&url)
        .bearer_auth(token)
        .multipart(form)
        .send()?;
    println!("{}", res.json::<Response>()?.status);
    Ok(())
}

fn get_remote_token(username: &str, password: &str) -> Result<String> {
    let client = reqwest::blocking::Client::new();

    let url = format!("{}/auth/tokens", BASEURL);

    let resp = client
        .post(&url)
        .basic_auth(username, Some(password))
        .send()?;

    let status = resp.status();

    if status == StatusCode::UNAUTHORIZED {
        // TODO: return proper error
    }

    let token = resp.text().unwrap();
    Ok(token)
}

fn get_saved_token() -> Result<String> {
    let keyring = keyring::Keyring::new(&SERVICENAME, "token");
    Ok(String::from(
        keyring
            .get_password()
            .map_err(|_| eyre!("Unable to get password"))?,
    ))
}

fn main() -> Result<()> {
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
        Some("compute") => {
            let cmd = m.subcommand_matches("compute").unwrap();

            let token = match cmd.value_of("token") {
                Some(n) => n.into(),
                None => get_saved_token()?,
            };

            compute(
                cmd.value_of("database").unwrap().into(),
                cmd.value_of("dataset_id").unwrap().into(),
                &token,
            )
        }
        Some("submit") => {
            let cmd = m.subcommand_matches("submit").unwrap();

            let token = match cmd.value_of("token") {
                Some(n) => n.into(),
                None => get_saved_token()?,
            };

            submit(
                cmd.value_of("database").unwrap().into(),
                cmd.value_of("dataset_id").unwrap().into(),
                &token,
                cmd.value_of("signature").unwrap(),
            )
        }
        Some("login") => {
            let cmd = m.subcommand_matches("login").unwrap();

            let username: String = match cmd.value_of("username") {
                Some(n) => n.into(),
                None => Input::new().with_prompt("Username").interact()?,
            };

            let password: String = match cmd.value_of("password") {
                Some(n) => n.into(),
                None => Password::new().with_prompt("Password").interact()?,
            };

            let token = get_remote_token(&username, &password)?;

            let keyring = keyring::Keyring::new(&SERVICENAME, "token");
            keyring
                .set_password(&token)
                .map_err(|e| eyre!("Unable to set password: {}", e.source().unwrap()))?;

            Ok(())
        }
        Some(c) => Err(eyre!("Unknown subcommand {}", c)),
        None => Err(eyre!("Subcommand missing!")),
    }
}
