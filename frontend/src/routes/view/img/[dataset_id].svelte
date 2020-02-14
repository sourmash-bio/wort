<script context="module">
	export async function preload({ params, query }) {
		const res = await this.fetch(`v1/info/img/${params.dataset_id}.json`);
		const data = await res.json();

		if (res.status === 200) {
			return { dataset: data };
		} else {
			this.error(res.status, data.message);
		}
	}
</script>

<script>
	export let dataset;
</script>

<style>
	.content :global(h2) {
		font-size: 1.4em;
		font-weight: 500;
	}

	.content :global(pre) {
		background-color: #f9f9f9;
		box-shadow: inset 1px 1px 5px rgba(0,0,0,0.05);
		padding: 0.5em;
		border-radius: 2px;
		overflow-x: auto;
	}

	.content :global(pre) :global(code) {
		background-color: transparent;
		padding: 0;
	}

	.content :global(ul) {
		line-height: 1.5;
	}

	.content :global(li) {
		margin: 0 0 0.5em 0;
	}
</style>

<svelte:head>
	<title>{dataset.name}</title>
</svelte:head>

<h1>{dataset.name}</h1>

<ul>
  <li>Dataset: {dataset.name} ({dataset.db})</li>
  <li><a href='{dataset.metadata}'>Metadata</a></li>
  <li><a href='{dataset.link}'>Download link</a></li> 
  <li>IPFS hash (gzipped):<br/> <a href='https://cloudflare-ipfs.com/ipfs/{dataset.ipfs}'>{dataset.ipfs}</a></li>
</ul>
