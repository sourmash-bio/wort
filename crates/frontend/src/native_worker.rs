use serde::{Deserialize, Serialize};
use yew::worker::*;

use needletail::{parse_fastx_reader, Sequence};
use sourmash::cmd::ComputeParameters;
use sourmash::signature::Signature;

#[derive(Serialize, Deserialize, Debug)]
pub enum Request {
    ProcessFile(Vec<u8>),
}

#[derive(Serialize, Deserialize, Debug)]
pub enum Response {
    Signature(Vec<u8>),
}

pub enum Msg {}

pub struct Worker {
    link: AgentLink<Worker>,
}

impl Agent for Worker {
    type Reach = Public<Self>;
    type Message = Msg;
    type Input = Request;
    type Output = Response;

    fn create(link: AgentLink<Self>) -> Self {
        Worker { link }
    }

    fn update(&mut self, _msg: Self::Message) {}

    fn handle_input(&mut self, msg: Self::Input, who: HandlerId) {
        match msg {
            Request::ProcessFile(content) => {
                let (mut reader, _) = niffler::send::get_reader(Box::new(&content[..])).unwrap();

                let params = ComputeParameters::builder()
                    .ksizes(vec![21])
                    .num_hashes(0)
                    .scaled(2000)
                    .build();
                let mut sig = Signature::from_params(&params);

                let mut parser = parse_fastx_reader(&mut reader).unwrap();
                while let Some(record) = parser.next() {
                    let record = record.unwrap();
                    let norm_seq = record.normalize(true);
                    sig.add_sequence(&norm_seq, true).unwrap();
                }
                let json = serde_json::to_vec(&[&sig]).unwrap();
                self.link.respond(who, Response::Signature(json));
            }
        }
    }

    fn name_of_resource() -> &'static str {
        "worker.js"
    }
}
