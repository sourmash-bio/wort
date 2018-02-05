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
| | |              +----+                                 |   redis       |
+-+ |              |                                      |               |
  +-+              |                                      +---------------+
    +--------------+                                      |               |
                                                          |   db          |
                                                          |               |
                                                          +---------------+
```

Three routes:
- /compute/<sra_id>
  - defined in `wort.blueprints.compute.views`
  - starts the celery task `compute` (defined in `wort.blueprints.compute.tasks`)
    * checks if the file already exists in S3, and return if it does.
	* if not, run a shell script (`fastq-dump + sourmash`)
	* after finishing successfully, upload the file to S3
- /viewer/<sra_id>
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
	we can mark it as 'unverified' initially
