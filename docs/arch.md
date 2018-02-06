# Architecture

## Initial prototype

```
                            +----+
                            |    +------------------------------------------------+
                        +---> S3 <---------+                                      |
                        |   |    |         | Viewer                               |
                        |   +----+         |              +---------------+       |
                        |                  |              | wort.oxli.org |       |
                        |                  |              +---------------+       |
+-------+               |                  +--------------+               +-------v-------> HTTP response
|Workers|               |                                 |   web         |
+--------------+        |                        +--------+               <---------------+ HTTP request
| +--------------+      |          compute       |        +---------------+
| | +--------------+    |          (celery delay)+-------->               |
| | | shell/       +----+                                 |   redis       |
+-+ | snakemake    |                             +--------+               |
  +-+              <-----------------------------+        +---------------+
    +--------------+         grab next job to run         |               |
                                                          |   db          |
                                                          |               |
                                                          +---------------+
```

Three routes:
- /compute/<sra_id>
  - defined in [`wort.blueprints.compute.views`][4]
  - starts the celery task [`compute`][5] (defined in [`wort.blueprints.compute.tasks`][6])
    * checks if the file already exists in S3, stop if it does.
	* if not, run a shell script (`fastq-dump + sourmash`)
	* after finishing successfully, upload the file to S3
- /viewer/<sra_id>
  - defined in [`wort.blueprints.viewer.views`][7]
  - shows a signature (calculated from the SRA)
  - for now just generating a [pre-signed URL from S3][8] and redirecting
    * might 404 because the sig is not there yet
  - raw JSON is not very friendly,
    how to make it pretty but still support programmatic access to the JSON file
	and display HTML if in browser?
- /submit
  - entry point for submitting signatures. It must do:
    * validation
	  - is this a signature?
	  - does it point to a valid public URL?
	  - ideally should also send to a 'verifier',
	    a worker that makes sure it is the same signature when recalculated.
  - (half assed implementation, doesn't do much yet)

## Future/TODO/ideas

- the 'verifier'
  * we can mark a submitted signature as 'unverified' initially but make it
	available in the `viewer` (with caveats)
- viewer
  * I want to support [hypothesis annotations][3] of signatures.
    They said it's possible to annotate JSON files,
	as long as they have a canonical URL.
	Options for canonical URL:
	  - IPFS hash?
	  - wort.oxli.org URL?
- submit
  * very basic upload page now,
  * upload is for calculated signatures, not raw data!
  * want to use [`soursigs-dnd`][0],
    [`sourmash-node`][1],
	[`sourmash-rust` compiled to wasm][2] eventually to allow raw data upload
	(calculated on the client side)
- the /search route
  * entry point for using `search`, `gather`, `lca` and `lca gather`
  * 'delayed' execution (once a job start return to result page,
    but will have results only when job finishes)
  * ~heavyweight, will need more resources?


[0]: https://github.com/luizirber/soursigs-dnd
[1]: https://github.com/luizirber/sourmash-node
[2]: https://github.com/luizirber/sourmash-rust
[3]: https://hypothes.is
[4]: https://github.com/luizirber/wort/blob/eb0005fd187b19fd504454f7a3f419063c541d35/wort/blueprints/compute/views.py#L11
[5]: https://github.com/luizirber/wort/blob/eb0005fd187b19fd504454f7a3f419063c541d35/wort/blueprints/compute/tasks.py#L13
[6]: https://github.com/luizirber/wort/blob/eb0005fd187b19fd504454f7a3f419063c541d35/wort/blueprints/compute/tasks.py
[7]: https://github.com/luizirber/wort/blob/eb0005fd187b19fd504454f7a3f419063c541d35/wort/blueprints/viewer/views.py#L8
[8]: https://github.com/luizirber/wort/blob/eb0005fd187b19fd504454f7a3f419063c541d35/wort/blueprints/viewer/views.py#L14
