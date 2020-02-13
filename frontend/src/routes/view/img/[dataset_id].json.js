import datasets from './_datasets.js';

const lookup = new Map();
datasets.forEach(post => {
	lookup.set(post.name, JSON.stringify(post));
});

export function get(req, res, next) {
	const { dataset_id } = req.params;

	if (lookup.has(dataset_id)) {
		res.writeHead(200, {
			'Content-Type': 'application/json'
		});

		res.end(lookup.get(dataset_id));
	} else {
		res.writeHead(404, {
			'Content-Type': 'application/json'
		});

		res.end(JSON.stringify({
			message: `Not found`
		}));
	}
}
