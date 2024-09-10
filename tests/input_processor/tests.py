import pytest

from broker.input_processor import TsvInputProcessor
from broker.input_processor import XlsxInputProcessor


@pytest.fixture
def valid_minimal_input():
    return [{'name': 'python_test', 'other_field': 'other_value'}]


@pytest.fixture
def valid_minimal_tsv():
    return TsvInputProcessor(input_data='valid_minimal.tsv')


@pytest.fixture
def valid_minimal_xlsx():
    return XlsxInputProcessor(input_data='valid_minimal.xlsx')


def test_loading_input_tsv(valid_minimal_input, valid_minimal_tsv):
    assert valid_minimal_input == valid_minimal_tsv.input_data


def test_loading_input_xlsx(valid_minimal_input, valid_minimal_xlsx):
    assert valid_minimal_input == valid_minimal_xlsx.input_data
