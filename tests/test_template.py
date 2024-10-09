import pytest


"""
-----------------------------------------------------------------------------------------------------------------------
Template for the TEST files. I recommend dividing the test files in 3 sections:

- Fixture/parametrization. I recommend initialising the objects here, unless it's needed by the test
- Utilitary functions
- Actual tests. Aside from testing functionality of the classes, I recommend adding a first test to initialize the 
  class. You'd be surprised!
-----------------------------------------------------------------------------------------------------------------------
"""

"""
Insert fixtures below
"""

@pytest.fixture
def example_fixture_list() -> list:
    return ["1", "2", "3"]

@pytest.fixture
def example_fixture_string() -> str:
    return "1"


"""
Insert utility functions below
"""

def string_in_list(lst, string):
    return string in lst


"""
Insert test functions below
"""
# Tests
def test_save_method(valid_minimal_data, output_processor):
    output_processor.save(valid_minimal_data)
    assert files_are_equal(output_processor.path, output_processor.path.replace('_test', ''))

