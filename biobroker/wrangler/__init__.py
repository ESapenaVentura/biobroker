"""
Wrapper submodule. Not a lot to say here - This is just a wrapper to make it easier for users to use basic
library functionality:

- :func:`broker.wrangler.Wrangler.submit`
- Retrieve: :func:`broker.wrangler.Wrangler.retrieve_entities`
- Save: :func:`broker.wrangler.Wrangler.save_results`
"""
from biobroker.wrangler.wrangler import Wrangler

# This lets Sphinx know you want to document package.module.Class as package.Class.
__all__ = ['Wrangler']