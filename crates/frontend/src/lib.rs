#![recursion_limit = "1024"]

pub mod native_worker;

use anyhow::Error;
use web_sys::DragEvent;
use yew::format::Json;
use yew::services::fetch::{FetchService, FetchTask, Request, Response};
use yew::services::reader::{File, FileData, ReaderService, ReaderTask};
use yew::worker::{Bridge, Bridged};
use yew::{html, Callback, ChangeData, Component, ComponentLink, Html, ShouldRender};

use sourmash::index::greyhound::GatherResult;
use sourmash::signature::Signature;

pub struct Model {
    link: ComponentLink<Self>,
    job: Box<dyn Bridge<native_worker::Worker>>,
    ft: Option<FetchTask>,
    sig: Option<Signature>,
    reader: ReaderService,
    tasks: Vec<ReaderTask>,
    gather_result: Vec<GatherResult>,
}

pub enum Msg {
    SendToWorker(FileData),
    Files(Vec<File>),
    SigFromWorker(Vec<u8>),
    FetchData(Vec<u8>),
    FetchReady(Result<Vec<GatherResult>, Error>),
    Ignore,
}

impl Component for Model {
    type Message = Msg;
    type Properties = ();

    fn create(_: Self::Properties, link: ComponentLink<Self>) -> Self {
        let callback = link.callback(|m: native_worker::Response| match m {
            native_worker::Response::Signature(sig) => Msg::SigFromWorker(sig),
        });
        let job = native_worker::Worker::bridge(callback);

        Model {
            link,
            job,
            ft: None,
            sig: None,
            reader: ReaderService::new(),
            tasks: vec![],
            gather_result: vec![],
        }
    }

    fn update(&mut self, msg: Self::Message) -> ShouldRender {
        match msg {
            Msg::SendToWorker(raw_data) => {
                self.job
                    .send(native_worker::Request::ProcessFile(raw_data.content));
            }
            Msg::SigFromWorker(sig) => {
                self.tasks.clear();
                self.link.send_message(Msg::FetchData(sig));
            }
            Msg::FetchData(json) => {
                let callback = self.link.callback(
                    move |response: Response<Json<Result<Vec<GatherResult>, Error>>>| {
                        let (meta, Json(data)) = response.into_parts();
                        println!("META: {:?}, {:?}", meta, data);
                        if meta.status.is_success() {
                            Msg::FetchReady(data)
                        } else {
                            Msg::Ignore // FIXME: Handle this error accordingly.
                        }
                    },
                );
                self.sig = Some(Signature::from_reader(&json[..]).unwrap().swap_remove(0));

                let request = Request::post("/gather").body(Ok(json)).unwrap();
                self.ft = Some(FetchService::fetch_binary(request, callback).unwrap());
            }
            Msg::FetchReady(result) => {
                // TODO: deal with errors
                self.ft = None;
                self.gather_result = result.unwrap();
            }
            Msg::Files(files) => {
                for file in files.into_iter() {
                    let task = {
                        let callback = self.link.callback(Msg::SendToWorker);
                        self.reader.read_file(file, callback).unwrap()
                    };
                    self.tasks.push(task);
                }
            }
            _ => return false,
        }
        true
    }

    fn view(&self) -> Html {
        html! {
          <>
            <header>
              <h2>{"greyhound gather"}</h2>
            </header>

            <div class="columns">
              <div id="files" class="box" ondragover=Callback::from(|e: DragEvent| {e.prevent_default();})>
                <div id="drag-container" class="box">
                  <p>{"Choose a FASTA/Q file to upload. File can be gzip-compressed."}</p>
                  <input type="file" multiple=true onchange=self.link.callback(move |value| {
                    let mut result = Vec::new();
                    if let ChangeData::Files(files) = value {
                        let files = js_sys::try_iter(&files)
                            .unwrap()
                            .unwrap()
                            .into_iter()
                            .map(|v| File::from(v.unwrap()));
                        result.extend(files);
                    }
                    Msg::Files(result)
                  })/>
                </div>

                <div id="progress-container">
                  <div id="progress-bar"></div>
                </div>
                <div class="columns">
                  <div class="box" id="download">
                    <button id="download_btn" type="button" disabled=true>{"Download"}</button>
                  </div>
                </div>

                <div id="results-container">
                  { self.render_results() }
                </div>
              </div>

              <div id="info" class="box">
                <p>
                  {"This is a demo for a system running "}<b>{"gather"}</b>
                  {", an algorithm for decomposing a query into reference datasets."}
                </p>

                <p>
                  <b>{"greyhound"}</b>{" is an optimized approach for running "}<b>{"gather"}</b>
                  {" based on an Inverted Index containing a mapping of hashes to datasets containing them.
                  In this demo the datasets are Scaled MinHash sketches (k=21, scaled=2000)
                  calculated from the "}
                  <a href="https://gtdb.ecogenomic.org/stats">{"31,910 species clusters in the GTDB r95"}</a>{"."}
                </p>

                <p>
                  {"This demo server is hosted on a "}<a href="https://aws.amazon.com/ec2/instance-types/t3/">{"t3.2xlarge"}</a>
                  {" spot instance on AWS, using ~10GB of the RAM for the inverted index + signature caching (for speed).
                  The server is implemented using "}<a href="https://github.com/http-rs/tide">{"tide"}</a>{", "}
                  {"an async web framework written in "}<a href="https://rust-lang.org">{"Rust"}</a>{". "}
                  {"The frontend is implemented in "}<a href="https://yew.rs">{"Yew"}</a>
                  {", a modern Rust framework for creating multi-threaded front-end web apps with "}
                  <a href="https://webassembly.org/">{"WebAssembly"}</a>{"."}
                  {"The frontend calculates the Scaled MinHash sketch in your browser,
                  instead of uploading the full data to the server."}
                </p>

                <p>
                  {"For more info about the methods used in this demo, see:"}
                    <ul>
                      <li>{"gather: "}<a href="https://dib-lab.github.io/2020-paper-sourmash-gather/">{"Lightweight compositional analysis of metagenomes with sourmash gather"}</a>{"."}</li>
                      <li>{"sourmash: "}<a href="https://doi.org/10.12688/f1000research.19675.1">{"Large-scale sequence comparisons with sourmash"}</a>{"."}</li>
                      <li>{"sourmash in the browser: "}<a href="https://blog.luizirber.org/2018/08/27/sourmash-wasm/">{"Oxidizing sourmash: WebAssembly"}</a>{"."}</li>
                      <li>{"Rust and WebAssembly: "}<a href="https://rustwasm.github.io/docs/book/">{"The Rust and WebAssembly book"}</a>{"."}</li>
                    </ul>
                </p>

                <p>
                  {"Additional thanks to the "}<a href="https://github.com/ipfs/js-ipfs/tree/master/examples/browser-exchange-files">
                  {"Exchange files between the browser and other IPFS nodes"}</a>{" example from "}
                  <a href="https://github.com/ipfs/js-ipfs">{"js-ipfs"}</a>{", "}
                  {"from where most of the UI/frontend was adapted."}
                </p>
              </div>
            </div>
          </>
        }
    }

    fn change(&mut self, _props: Self::Properties) -> ShouldRender {
        false
    }
}

impl Model {
    fn render_results(&self) -> Html {
        if self.gather_result.is_empty() {
            html! { <></> }
        } else {
            html! {
              <table>
                <thead>
                  <th>{"overlap"}</th>
                  <th>{"% query"}</th>
                  <th>{"% match"}</th>
                  <th>{"name"}</th>
                </thead>
                <tbody>
                  { self.gather_result.iter().map(|row| self.view_row(row)).collect::<Html>() }
                </tbody>
              </table>
            }
        }
    }

    fn view_row(&self, mdata: &GatherResult) -> Html {
        let base_url = "https://www.ncbi.nlm.nih.gov/assembly/";
        let name = mdata.name();
        let acc = name.split(' ').next().unwrap();

        html! {
          <tr>
            <td>{bp_fmt(mdata.intersect_bp())}</td>
            <td>{format!("{:.1}", mdata.f_orig_query() * 100.)}</td>
            <td>{format!("{:.1}", mdata.f_match() * 100.)}</td>
            <td><a href={ format!("{}{}", base_url, acc) }>{name}</a></td>
          </tr>
        }
    }
}

fn bp_fmt(bp: usize) -> String {
    match bp {
        0..=500 => format!("{:.0} bp", bp),
        501..=500_000 => format!("{:.1} Kbp", bp as f64 / 1e3),
        500_001..=500_000_000 => format!("{:.1} Mbp", bp as f64 / 1e6),
        _ => format!("{:.1} Gbp", bp as f64 / 1e9),
    }
}
