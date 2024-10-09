import pytest

from biobroker.output_processor import TsvOutputProcessor, XlsxOutputProcessor
from biobroker.input_processor import TsvInputProcessor, XlsxInputProcessor
from biobroker.metadata_entity import Biosample

# TODO: Improvement here: load all subclasses of GenericOutputProcessor, fixture 'output_processors' would automatically
#       update


# FIXTURES
@pytest.fixture
def valid_minimal_data():
    return [Biosample({'name': 'python_test', 'other_field': 'other_values', 'release': '2024-08-22T15:27:18.570644Z'})]


@pytest.fixture
def paths():
    return ['valid_minimal.tsv', 'valid_minimal.xlsx']


# Functions
def files_are_equal(path_1, path_2, input_processor) -> bool:
    file_1 = input_processor(path_1).input_data
    file_2 = input_processor(path_2).input_data
    return file_1 == file_2


# Positive tests
@pytest.mark.parametrize('output_processor,path',
                         [(TsvOutputProcessor, 'valid_minimal_test.tsv'),
                          (XlsxOutputProcessor, 'valid_minimal_test.xlsx')])
def test_initialise(output_processor, path):
    output_processor(path)
    assert True

@pytest.mark.parametrize('output_processor,path,input_processor',
                         [(TsvOutputProcessor, 'valid_minimal_test.tsv', TsvInputProcessor),
                          (XlsxOutputProcessor, 'valid_minimal_test.xlsx', XlsxInputProcessor)])
def test_save_pass(valid_minimal_data, output_processor, path, input_processor):
    processor = output_processor(path)
    processor.save(valid_minimal_data)
    assert files_are_equal(processor.path, processor.path.replace('_test', ''), input_processor)

# Negative tests
@pytest.mark.parametrize('output_processor,path',
                        [(TsvOutputProcessor, 'valid_minimal_test.tsv'),
                         (XlsxOutputProcessor, 'valid_minimal_test.xlsx')])
def test_save_fail(valid_minimal_data, path, output_processor):
    processor = output_processor(path)
    with pytest.raises(AttributeError):
        processor.save(valid_minimal_data[0])  # Entities should be a list
