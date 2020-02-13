// Ordinarily, you'd generate this data from markdown files in your
// repo, or fetch them from a database of some kind. But in order to
// avoid unnecessary dependencies in the starter template, and in the
// service of obviousness, we're just going to leave it here.

// This file is called `_posts.js` rather than `posts.js`, because
// we don't want to create an `/blog/posts` route — the leading
// underscore tells Sapper not to do that.

const datasets = [
	{
    name: 'DRR013902',
    db: 'SRA',
    metadata: 'https://trace.ncbi.nlm.nih.gov/Traces/sra/?run=DRR013902',
    link: 'https://wort.oxli.org/v1/view/sra/DRR013902',
    ipfs: 'zDMZof1kwPfcBkVd1Bf9v8L8SVVZ3669HPxx2yvE8NXrG9UmKW4Y'
	},
];

export default datasets;
