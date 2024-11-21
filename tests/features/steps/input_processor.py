from behave import *

import json

import sys
sys.path.insert(0, "../../")

from biobroker.input_processor import TsvInputProcessor, XlsxInputProcessor, GenericInputProcessor
from biobroker.metadata_entity import Biosample


@given('an instance of {input_processor} loaded with an {input_file}')
def step_load(context, input_processor, input_file):
    context.input_processor = eval(input_processor)(input_file)

@when('I have a JSON file with the same content')
def step_load_json(context):
    with open('assets/valid_minimal.json', 'r') as f:
        context.valid_minimal_json = json.load(f)

@then('the input_data must be the same as the JSON file')
def compare(context):
    assert context.input_processor.input_data[0] == context.valid_minimal_json

@when('I call the transform function on the data with a map')
def transform(context):
    context.input_processor.transform({'other_field': 'new_field'})

@then("the input_data key 'other_field' must be named 'new_field'")
def transform(context):
    assert context.input_processor.input_data[0].get('other_field') is None
    assert context.input_processor.input_data[0].get('new_field') is not None


# Feature: Integration

@when('I call the process method providing with a {metadata_entity_class} class')
def process(context, metadata_entity_class):
    context.entity_class = eval(metadata_entity_class)
    context.processed_data = context.input_processor.process(context.entity_class)[0]

@then('it should result in a valid Metadata Entity')
def process(context):
    assert isinstance(context.processed_data, context.entity_class)
    assert context.processed_data.id is not None
    assert context.processed_data.accession is not None