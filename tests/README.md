# Tests

This folder contains the unit tests and an integration test for the different implementations so far.

The tests are written using the Behave suite (https://behave.readthedocs.io/en/latest/), to try and provide with a set
of tests any human with no prior code knowledge can, at least, read.

Unit tests are run on each PR that directly involves the code; these tests don't fully interact with the archives' APIs*

Integration tests do create new entities in the archives (In the dev environments) using credentials: As such, they will
be triggered either with Cron jobs or manually. This is to avoid small changes creating a ton of entities on the 
archives.

*Aside from getting a token; I don't consider this a high risk action, so I don't mind the tests doing that to be as 
accurate as possible.

With the Behave suite, tests are divided in ~2 files:
- A feature file, containing the test written in [Gherkin language](https://behave.readthedocs.io/en/latest/gherkin/#chapter-gherkin)
- A python file within the `steps` folder, containing the code to carry the tests.

