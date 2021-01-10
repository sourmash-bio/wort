all: app worker

#MODE=debug
MODE=release

app:
	cargo build --release --target wasm32-unknown-unknown --bin greyhound_frontend
	#cargo build --target wasm32-unknown-unknown --bin greyhound_frontend 
	wasm-bindgen \
		--target web \
		--no-typescript \
		--out-dir static/ \
		--out-name app \
		../target/wasm32-unknown-unknown/${MODE}/greyhound_frontend.wasm

worker:
	cargo build --release --target wasm32-unknown-unknown --bin greyhound_worker
	#cargo build --target wasm32-unknown-unknown --bin greyhound_worker
	wasm-bindgen \
		--target no-modules \
		--no-typescript \
		--out-dir static/ \
		--out-name worker \
		../target/wasm32-unknown-unknown/${MODE}/greyhound_worker.wasm
