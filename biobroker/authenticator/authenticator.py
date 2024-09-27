import os
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from biobroker.authenticator.exceptions import WrongUserOrPassword, UsernameNotValid
from biobroker.generic.exceptions import MandatoryFunctionNotSet
from biobroker.generic.logger import set_up_logger


class GenericAuthenticator:
    """
    Generic authenticator class. Defines the expected functions and properties of all subclasses. Some must be
    overridden.

    :param base_uri: Base URI for the request to retrieve the token.
    :param username: Username required for authentication.
    :param password: Password required for authentication.
    :param verbose: Boolean indicating if the logger should be verbose.
    """
    def __init__(self, base_uri: str, username: str, password: str, verbose: bool = False):
        self.base_uri = base_uri

        self.username = username
        self.password = password
        self.auth_endpoint = ""
        self.logger = set_up_logger(self, verbose=verbose)

    @property
    def auth_endpoint(self):
        """
        Name of the endpoint to authenticate

        :return: string
        """
        return self._auth_endpoint

    @auth_endpoint.setter
    def auth_endpoint(self, endpoint):
        raise MandatoryFunctionNotSet(self.logger)

    @property
    def token(self):
        """
        Token property

        :return: Bearer <token>
        """
        return f"Bearer {self._token}"

    @token.setter
    def token(self, _):
        """
        SUBCLASSES ARE REQUIRED TO OVERRIDE THIS SETTER. A subclass must define this property, with the decorator
        @GenericAuthenticator.token.setter

        :param _:
        :return:
        """
        raise MandatoryFunctionNotSet(self.logger)

    # All functions below are wrappers for requests.get/put/patch/delete/post
    def _request(self, url, method, payload: dict) -> requests.Response:
        """
        Handle all requests. If token is expired, reload token and try again. If this results in another error, it will
        be risen.

        :param url: URL to REQUEST
        :param method: Method for the REQUEST
        :param payload: Optional payload, for POST/PUT/PATCH methods
        :return:
        """
        s = requests.Session()
        retries = Retry(total=5, backoff_factor=1)
        s.mount('https://', HTTPAdapter(max_retries=retries))

        r = s.request(url=url, method=method, json=payload, headers={'Authorization': self.token,
                                                                     'Content-Type': 'application/json'},
                      )

        if r.status_code == 401:
            self.logger.warning(f"{method} request returned status code {r.status_code}. "
                                "Refreshing token and trying again.")
            self.token = (self.username, self.password)
            r = s.request(url=url, method=method, json=payload, headers={'Authorization': self.token,
                                                                         'Content-Type': 'application/json'},
                          )
        return r

    def get(self, url: str) -> requests.Response:
        """
        GET a url

        :param url: URL to GET
        :return: response
        """
        return self._request(url, "GET", {})

    def post(self, url: str, payload: dict) -> requests.Response:
        """
        POST a payload to a URL

        :param url: URL to POST
        :param payload: JSON payload
        :return: response
        """
        return self._request(url, "POST", payload)

    def delete(self, url: str) -> requests.Response:
        """
        DELETE an entity on a URL

        :param url: URL to send the DELETE request
        :return: response
        """
        return self._request(url, "DELETE", {})

    def put(self, url: str, payload: dict) -> requests.Response:
        """
        PUT a payload to an URL

        :param url:
        :param payload:
        :return: response
        """
        return self._request(url, "PUT", payload)

    def patch(self, url: str, payload: dict) -> requests.Response:
        """
        PATCH a payload to a URL

        :param url:
        :param payload:
        :return: response
        """
        return self._request(url, "PATCH", payload)


class WebinAuthenticator(GenericAuthenticator):
    """
    Webin authenticator. Retrieves a token from the Webin service.

    :param username: Webin username. Must start with "Webin-"
    :param password: Webin password.
    """
    def __init__(self, username: str, password: str, verbose: bool = False):
        environment = 'dev' if 'dev' == os.environ.get('API_ENVIRONMENT', '') else ''
        base_uri = "https://www.ebi.ac.uk/ena/submit/webin/auth".replace('www', f"www{environment}")

        super().__init__(base_uri, username, password, verbose)
        self.validate_username(username)
        self.auth_endpoint = "token"
        self.token = ""
        self.logger.info(f"WebinAuthenticator set up successfully. Base uri: {self.base_uri}")

    @GenericAuthenticator.auth_endpoint.setter
    def auth_endpoint(self, endpoint: str):
        """Authentication endpoint setter"""
        self._auth_endpoint = os.path.join(self.base_uri, endpoint)

    @GenericAuthenticator.token.setter
    def token(self, _):
        """
        Token setter for property. Returns a token from the ENA Webin service.

        :param _: Leave blank or pass None
        :return:
        """
        self.logger.info(f"Generating token for user {self.username}")
        r = requests.post(f"{self.auth_endpoint}", json={
            "authRealms": [
                "ENA"
            ],
            "password": self.password,
            "username": self.username
        })
        if r.status_code == 401:
            raise WrongUserOrPassword(self.username, self.password, self.logger)
        else:
            r.raise_for_status()
            self._token = r.text

    # Validation methods
    def validate_username(self, username: str):
        """
        Validate a username. For webin, all usernames start with `Webin-`. Can raise
        :exc:`~biobroker.authenticator.exceptions.UsernameNotValid`

        :param username: Webin username.
        :return:
        """
        if not username.startswith("Webin-"):
            raise UsernameNotValid(username, self.logger)
