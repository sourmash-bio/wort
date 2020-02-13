<script>
  import FileUpload from "../components/FileUpload.svelte";
  let files = [];
</script>

<svelte:head>
	<title>Compute</title>
</svelte:head>

<h1>Compute</h1>

<FileUpload bind:files={files}>
	<p slot="help1">Svelte wants you to select some files.</p>
</FileUpload>
