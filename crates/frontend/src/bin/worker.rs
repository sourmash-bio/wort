// Use `wee_alloc` as the global allocator.
#[global_allocator]
static ALLOC: wee_alloc::WeeAlloc = wee_alloc::WeeAlloc::INIT;

use yew::agent::Threaded;

fn main() {
    wasm_logger::init(wasm_logger::Config::default());
    greyhound_frontend::native_worker::Worker::register();
}
