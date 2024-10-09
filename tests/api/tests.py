import pytest

from biobroker.api import BsdApi
from biobroker.authenticator import GenericAuthenticator
from biobroker.metadata_entity import GenericEntity


"""
-----------------------------------------------------------------------------------------------------------------------
Template for the TEST files. I recommend dividing the test files in 3 sections:

- Fixture/parametrization. I recommend initialising the objects here, unless it's needed by the test
- Utilitary functions
- Actual tests. Aside from testing functionality of the classes, I recommend adding a first test to initialize the 
  class. You'd be surprised!
-----------------------------------------------------------------------------------------------------------------------
"""

class MockEntity:
    def __init__(self):
        self.entity = [{"name": "one_sample_value"}]


class MockAuthenticator:
    token = "Bearer FakeToken"

    def post(self, url: str, payload: dict):
        """
        POST a payload to a URL

        :param url: URL to POST
        :param payload: JSON payload
        :return: response
        """
        return self._request(url, "POST", payload)

    def _request(self, url, method, payload: dict, mock=requests_mock):
        match method:
            case "GET":
                return [{"name": "one_sample_value"}]
            case "POST":
                return payload
            case "PUT":
                return payload
            case "DELETE":
                return url


"""
Insert fixtures below
"""

@pytest.fixture
def api_object() -> BsdApi:
    return BsdApi

@pytest.fixture
def mock_auth(mocker) -> MockAuthenticator:
    mocker.patch.object(GenericAuthenticator, '__new__', return_value = MockAuthenticator())
    return GenericAuthenticator()


@pytest.fixture
def mock_entity(mocker) -> MockEntity:
    mocker.patch.object(GenericEntity, '__new__', return_value = MockEntity())
    return GenericEntity()


@pytest.fixture
def minimal_json_response():
    return [{"name": "one_sample_value"}]

"""
Insert utility functions below
"""

def base_properties_set(api):
    return all([api.authenticator, api.base_uri, api.logger])




"""
Insert test functions below
"""
# Tests
@pytest.mark.parametrize('mock_auth,api_object', [(mock_auth, BsdApi)])
def test_initialize(mock_auth, api_object):
    api = BsdApi(mock_auth, verbose=False)
    assert base_properties_set(api)


def test_submit(minimal_json_response, mock_entity, mock_auth, api_object):
    api = BsdApi(mock_auth, verbose=False)
    assert api.submit([mock_entity]) == minimal_json_response

