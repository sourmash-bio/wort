<script>
  let sourmash_lib = import("sourmash/sourmash.js");

  import FileReadStream from "filestream/read";
  import {FASTQStream, FASTQValidator} from "fastqstream";
  import * as Fasta from "fasta-parser";

  import "zlib";
  import * as peek from "peek-stream";
  import * as through from "through2";
  import "pumpify";

  import ProgressBar from "@okrad/svelte-progressbar";

  let series = [0];

  let bar;

  const updateBar = values => {
    values.forEach((v, i) => {if (bar) {bar.updatePerc(v, i)}});
  };

  async function downloadFile(url, destFilePath) {
    let source = await fetch(url).body;
    let sink = fs.createWriteStream(destFilePath, { mode: 0o755 });
    await pipeline(source, sink);
    sink.destroy()
  }

  export let multiple = false;
  export let files = [];

  async function handleChange(e) {
    files = Array.from(e.target.files);
    var file = files[0];

    var reader = new FileReadStream(file)
    var loaded = 0
    var size = file.size

    reader.reader.onprogress = function (data) {
      loaded += data.loaded
      updateBar([(loaded/size) * 100])
    }

    let sourmash = await sourmash_lib
    var mh = new sourmash.KmerMinHash(10, 21, false, 42, 0, true)
    //var mh = new sourmash.Signature()

    var fqstream = new FASTQStream()
    var validate = new FASTQValidator()

    validate.on('data', function (data) {
      mh.add_sequence_js(data.seq)
    })
      .on('end', function (data) {
        updateBar([100])
        console.log(mh.to_json())
      })

    reader.pipe(fqstream).pipe(validate)
  }
</script>

<input type="file" {multiple} on:change={handleChange} />
<slot name="help">
  <p >Select some files.</p>
</slot>
<slot name="filelist">
  <table>
    <thead>
      <tr>
        <th>Name</th>
        <th>Size</th>
        <th>Progress</th>
      </tr>
    </thead>
    <tbody>
      {#each files as f, i (i)}
        <tr>
          <td>{f.name}</td>
          <td>{f.size}</td>
          <td><ProgressBar {series} bind:this={bar} /></td>
        </tr>
      {/each}
    </tbody>
  </table>
</slot>
