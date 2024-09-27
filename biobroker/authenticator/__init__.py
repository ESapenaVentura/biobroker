"""
Authenticator module. This module consists of several classes that can load a username and a password
and retrieve the token needed to validate the requests.

For easiness of use, it also wraps the requests, adding automatically the token to the header, and adding an
extra check in case the token expires.

**Mandatory arguments**:

- username: Username for the authentication service
- password: Password for the authentication service
- base_uri: base uri for the authentication service (Can be provided by subclasses, see WebinApi object for an example)

**Optional arguments**:

- verbose: set to `True` if you want `INFO` and above-level logging events. If not set or set to False, only `WARNING`
  and above will be displayed

**Environment variables**:

- API_ENVIRONMENT: Needs to be set up if you want to set up a 'dev' authenticator. Please note this
  environment variable is shared with the API: this is to avoid inconsistent API/Authenticator combos (And even with
  all these checks and constraints, there will be errors, I'm pretty sure)

**Subclasses of GenericAuthenticator must define the following methods/properties**:

- @token.setter

**Aspects to improve**:

- _request function: Currently, it assumes JWT token generation + authorization "Bearer <token>" in all subclasses.
  if other headers or payloads are necessary for authentication, it needs to be overridden.
"""

from .authenticator import GenericAuthenticator, WebinAuthenticator

__all__ = ['GenericAuthenticator', 'WebinAuthenticator']