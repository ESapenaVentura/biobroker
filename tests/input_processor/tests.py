import pytest

from biobroker.input_processor import TsvInputProcessor
from biobroker.input_processor import XlsxInputProcessor


@pytest.fixture
def valid_minimal_input():
    return [{'name': 'python_test', 'other_field': 'other_values', 'release': '2024-08-22T15:27:18.570644Z'}]


@pytest.fixture
def field_map():
    return {'other_field': 'Another_name_for_field'}


@pytest.fixture
def valid_transformed_data():
    return [{'name': 'python_test', 'Another_name_for_field': 'other_values', 'release': '2024-08-22T15:27:18.570644Z'}]


pytestmark = pytest.mark.parametrize('input_path,input_processor', [('valid_minimal.tsv', TsvInputProcessor),
                                                                    ('valid_minimal.xlsx', XlsxInputProcessor)])


def test_initialise(input_path, input_processor):
    input_processor(input_path)
    assert True


def test_content_loading(valid_minimal_input, input_path, input_processor):
    input_content = input_processor(input_path).input_data
    assert valid_minimal_input == input_content


def test_transform_method(input_path, input_processor, field_map, valid_transformed_data):
    processor = input_processor(input_path)
    processor.transform(field_map)
    transformed_content = processor.input_data
    assert valid_transformed_data == transformed_content