//! A basic chat application with logs demonstrating libp2p and the gossipsub protocol.
//!
//! Using two terminal windows, start two instances. Type a message in either terminal and hit return: the
//! message is sent and printed in the other terminal. Close with Ctrl-c.
//!
//! You can of course open more terminal windows and add more participants.
//! Dialing any of the other peers will propagate the new participant to all
//! chat members and everyone will receive all messages.
//!
//! In order to get the nodes to connect, take note of the listening address of the first
//! instance and start the second with this address as the first argument. In the first terminal
//! window, run:
//!
//! ```sh
//! cargo run --example gossipsub-chat
//! ```
//!
//! It will print the PeerId and the listening address, e.g. `Listening on
//! "/ip4/0.0.0.0/tcp/24915"`
//!
//! In the second terminal window, start a new instance of the example with:
//!
//! ```sh
//! cargo run --example gossipsub-chat -- /ip4/127.0.0.1/tcp/24915
//! ```
//!
//! The two nodes should then connect.

use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::time::Duration;
use std::{
    error::Error,
    task::{Context, Poll},
};

use async_std::{io, task};
use env_logger::{Builder, Env};
use futures::prelude::*;
use libp2p::gossipsub::protocol::MessageId;
use libp2p::gossipsub::{GossipsubEvent, GossipsubMessage, MessageAuthenticity, Topic};
use libp2p::{gossipsub, identity, PeerId};

fn main() -> Result<(), Box<dyn Error>> {
    Builder::from_env(Env::default().default_filter_or("info")).init();

    // Create a random PeerId
    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = PeerId::from(local_key.public());
    println!("Local peer id: {:?}", local_peer_id);

    // Set up an encrypted TCP Transport over the Mplex and Yamux protocols
    let transport = libp2p::build_development_transport(local_key.clone())?;

    // Create a Gossipsub topic
    let topic = Topic::new("test-net".into());

    // Create a Swarm to manage peers and events
    let mut swarm = {
        // to set default parameters for gossipsub use:
        // let gossipsub_config = gossipsub::GossipsubConfig::default();

        // To content-address message, we can take the hash of message and use it as an ID.
        let message_id_fn = |message: &GossipsubMessage| {
            let mut s = DefaultHasher::new();
            message.data.hash(&mut s);
            MessageId::from(s.finish().to_string())
        };

        // set custom gossipsub
        let gossipsub_config = gossipsub::GossipsubConfigBuilder::new()
            .heartbeat_interval(Duration::from_secs(10))
            .message_id_fn(message_id_fn) // content-address messages. No two messages of the
            //same content will be propagated.
            .build();
        // build a gossipsub network behaviour
        let mut gossipsub =
            gossipsub::Gossipsub::new(MessageAuthenticity::Signed(local_key), gossipsub_config);
        gossipsub.subscribe(topic.clone());
        libp2p::Swarm::new(transport, gossipsub, local_peer_id)
    };

    // Listen on all interfaces and whatever port the OS assigns
    libp2p::Swarm::listen_on(&mut swarm, "/ip4/0.0.0.0/tcp/0".parse().unwrap()).unwrap();

    // Reach out to another node if specified
    if let Some(to_dial) = std::env::args().nth(1) {
        let dialing = to_dial.clone();
        match to_dial.parse() {
            Ok(to_dial) => match libp2p::Swarm::dial_addr(&mut swarm, to_dial) {
                Ok(_) => println!("Dialed {:?}", dialing),
                Err(e) => println!("Dial {:?} failed: {:?}", dialing, e),
            },
            Err(err) => println!("Failed to parse address to dial: {:?}", err),
        }
    }

    // Read full lines from stdin
    let mut stdin = io::BufReader::new(io::stdin()).lines();

    // Kick it off
    let mut listening = false;
    task::block_on(future::poll_fn(move |cx: &mut Context<'_>| {
        loop {
            if let Err(e) = match stdin.try_poll_next_unpin(cx)? {
                Poll::Ready(Some(line)) => swarm.publish(&topic, line.as_bytes()),
                Poll::Ready(None) => panic!("Stdin closed"),
                Poll::Pending => break,
            } {
                println!("Publish error: {:?}", e);
            }
        }

        loop {
            match swarm.poll_next_unpin(cx) {
                Poll::Ready(Some(gossip_event)) => match gossip_event {
                    GossipsubEvent::Message(peer_id, id, message) => println!(
                        "Got message: {} with id: {} from peer: {:?}",
                        String::from_utf8_lossy(&message.data),
                        id,
                        peer_id
                    ),
                    _ => {}
                },
                Poll::Ready(None) | Poll::Pending => break,
            }
        }

        if !listening {
            for addr in libp2p::Swarm::listeners(&swarm) {
                println!("Listening on {:?}", addr);
                listening = true;
            }
        }

        Poll::Pending
    }))
}

/*
use std::path::Path;
use std::sync::Arc;

use greyhound_core::RevIndex;
use sourmash::signature::{Signature, SigsTrait};
use sourmash::sketch::Sketch;
use tide::prelude::*;
use tide::{self, Body, Request};

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
    fn load<P: AsRef<Path>>(path: P) -> Result<Self, Error> {
        let revindex =
            RevIndex::load(path, None).map_err(|e| Error::IndexLoading(format!("{}", e)))?;
        Ok(Self {
            revindex: Arc::new(revindex),
        })
    }

    fn gather(&self, query: Signature) -> Result<Vec<String>, Error> {
        if let Some(sketch) = query.select_sketch(&self.revindex.template()) {
            if let Sketch::MinHash(mh) = sketch {
                let counter = self.revindex.counter_for_query(&mh);
                Ok(self
                    .revindex
                    .gather(counter, 0)
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
    let path = "data/genbank_bacteria.json.gz";
    let mut app = tide::with_state(RevIndexState::load(path)?);

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

    app.listen("127.0.0.1:8080").await?;
    Ok(())
}
*/
