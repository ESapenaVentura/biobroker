from behave import *

import json
import pandas as pd

import sys
sys.path.insert(0, "../../")

from biobroker.output_processor import TsvOutputProcessor, XlsxOutputProcessor, GenericOutputProcessor
from biobroker.metadata_entity import Biosample


@given('an instance of {output_processor} and a {metadata_entity} subclass loaded with the content in {valid_minimal_json}')
def save_method(context, output_processor, metadata_entity, valid_minimal_json):
    context.output_processor_class = eval(output_processor)
    with open(valid_minimal_json, 'r') as f:
        context.metadata_entity = eval(metadata_entity)(json.load(f))


@when('I save the entity as {output_file_path}')
def save_method(context, output_file_path):
    context.output_file_path = output_file_path
    context.output_processor = context.output_processor_class(output_file_path)
    context.output_processor.save([context.metadata_entity])

@then('the output should be equal to {test_file_path}')
def save_method(context, test_file_path):
    kwargs = {}
    match test_file_path:
        case x if x.endswith('tsv'):
            reader_function = pd.read_csv
            kwargs['delimiter'] = '\t'
        case x if x.endswith('xlsx'):
            reader_function = pd.read_excel
            kwargs['engine'] = 'openpyxl'
        case _:
            assert False, "Please create test for this file extension"

    dataframe_from_test = reader_function(context.output_file_path, **kwargs)
    dataframe_from_assets = reader_function(test_file_path, **kwargs)
    assert len(dataframe_from_test.columns.values) == len(dataframe_from_assets.columns.values), "Different number of columns"
    colnames = set(dataframe_from_test.columns.values) | set(dataframe_from_assets.columns.values)
    differences = [dataframe_from_assets[column].values.sort() == dataframe_from_test[column].values.sort() for column in colnames]
    assert all(differences), "Values are different"