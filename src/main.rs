#[macro_use]
extern crate clap;
extern crate dialoguer;
extern crate keyring;
extern crate reqwest;
#[macro_use]
extern crate serde_derive;

use std::error::Error;

use clap::App;
use dialoguer::{Input, PasswordInput};

const BASEURL: &'static str = "https://wort.oxli.org/v1";
const SERVICENAME: &'static str = "wort";

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
    let form = reqwest::multipart::Form::new().file("file", filename)?;

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

fn get_remote_token(username: &str, password: &str) -> Result<String, Box<Error>> {
    let client = reqwest::Client::new();

    let url = format!("{}/auth/tokens", BASEURL);

    let mut resp = client
        .post(&url)
        .basic_auth(username, Some(password))
        .send()?;
    let token = resp.text().unwrap();
    println!("{:?}\n{:?}", resp, token);
    Ok(token)
}

fn get_saved_token() -> Result<String, Box<Error>> {
    let keyring = keyring::Keyring::new(&SERVICENAME, "token");
    Ok(String::from(keyring.get_password()?))
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
                None => PasswordInput::new().with_prompt("Password").interact()?,
            };

            let token = get_remote_token(&username, &password)?;

            let keyring = keyring::Keyring::new(&SERVICENAME, "token");
            keyring.set_password(&token)?;

            Ok(())
        }
        None => Ok(()), // TODO: should be error
        _ => Ok(()),    // TODO: should be error
    }
}
