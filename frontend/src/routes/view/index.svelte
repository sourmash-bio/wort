<style>
	ul {
		margin: 0 0 1em 0;
		line-height: 1.5;
	}
</style>

<svelte:head>
	<title>View</title>
</svelte:head>

<p>One day there will be a better page here, but for now query signatures
  directly at the address bar. The URL format is</p>
<p>https://wort.oxli.org/view/<strong>db</strong>/<strong>dataset_id</strong></p>
<ul>
  <li><strong>db</strong>: can be 'sra' or 'img'</li>
  <li><strong>dataset_id</strong>: depends on the database.
      For SRA it's the SRA Experiment ID, and for IMG/M it's the taxon OID.</li>
</ul>
