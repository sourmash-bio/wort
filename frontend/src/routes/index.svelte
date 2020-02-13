<style>
	h1, figure, p {
		text-align: center;
		margin: 0 auto;
	}

	h1 {
		font-size: 2.8em;
		text-transform: uppercase;
		font-weight: 700;
		margin: 0 0 0.5em 0;
	}

	figure {
		margin: 0 0 1em 0;
	}

	img {
		width: 100%;
		max-width: 400px;
		margin: 0 0 1em 0;
	}

	p {
		margin: 1em auto;
	}

	ul {
		margin: 1em 1em 1em 1em;
		line-height: 1.5;
	}

  .warning {
    background-color: darkred;
    color: white;
    padding-left: 3.5rem;
    padding-right: 3.5rem;
    padding-top: 1rem;
    padding-bottom: 1rem;
    border-radius: 1rem;
  }

	@media (min-width: 480px) {
		h1 {
			font-size: 4em;
		}
	}
</style>

<svelte:head>
	<title>wort</title>
</svelte:head>

<figure class="warning">
<p>Reminder: wort is very alpha, so
  please be patient =] (and report issues/feature requests on
  <a href='https://github.com/dib-lab/wort/issues/'> GitHub</a>
</p>
</figure>

<p>
Welcome to wort! It's a database for sourmash signatures, currently focused on
indexing microbial datasets from
<a href='https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?'>NCBI Sequence Read Archive</a>
and the <a href='https://img.jgi.doe.gov/'>JGI Integrated Microbial Genomes and Microbiomes</a> portals.
</p>

<p> Here are some example pages for these datasets: </p>
<ul>
  <li>SRA: <a href='/view/sra/DRR013902/'>DRR013902</a></li>
  <li>IMG: <a href='/view/img/2522125045'>2728369338</a></li>
</ul>

<p>For more info check the <a href='https://github.com/luizirber/2018-biods'>poster</a>
  presented at <a
    href='https://meetings.cshl.edu/meetings.aspx?meet=DATA&year=18'>Biological
    Data Science 2018</a>.
</p>

<p>Also check the <a href='https://github.com/dib-lab/wort'>GitHub</a>
  repository, where we keep track of code, issues and feature requests.
</p>
