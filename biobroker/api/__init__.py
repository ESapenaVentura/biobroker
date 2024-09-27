"""
API module. This module consists of several classes whose function is to provide with the necessary endpoints
for interacting with the archival services.

The main functions are to submit, retrieve with an accession, and update with an accession; However, as many
methods can be added as necessary.

**Mandatory arguments**:

- authenticator: Subclass of GenericAuthenticator
- base_uri: base uri for the archive's API (Can be automatically set-up by subclasses, see BsdApi object for an example)

**Optional arguments**:

- verbose: set to `True` if you want `INFO` and above-level logging events. If not set or set to False, only `WARNING`
  and above will be displayed

**Environment variables**:

- API_ENVIRONMENT: Needs to be set up if you want to set up a 'dev' authenticator. Please note this
  environment variable is shared with the Authenticator: this is to avoid inconsistent API/Authenticator combos (And
  even with all these checks and constraints, there will be errors, I'm pretty sure)

**Subclasses of GenericApi must define the following methods/properties**:

- _submit: Function called by `submit` when only one entity is sent to `submit`
- _submit_multiple: Function called by `submit` when multiple entities are sent to `submit`
- Same with `retrieve` and `update`.
"""

from .api import GenericApi, BsdApi

# This lets Sphinx know you want to document package.module.Class as package.Class.
__all__ = ['GenericApi', 'BsdApi']