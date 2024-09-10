import pytest

from broker.output_processor import TsvOutputProcessor, XlsxOutputProcessor
from broker.metadata_entity import Biosample


@pytest.fixture
def valid_minimal_data():
    return [Biosample({'name': 'python_test', 'other_field': 'other_value'})]


def test_save(valid_minimal_data):



