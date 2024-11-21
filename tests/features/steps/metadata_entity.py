from behave import *
import json

import sys
sys.path.insert(0, "../../")

from biobroker.metadata_entity import Biosample

@given("all the metadata entity classes")
def metadata_entity(context):
    context.instances = {}
    for subclass_entity, metadata_json_path in (('Biosample', 'assets/accessioned_BsdApi_entity.json'),):
        subclass_entity_object = eval(subclass_entity)
        with open(metadata_json_path, 'r') as f:
            context.instances[subclass_entity] = subclass_entity_object(json.load(f))


@given("a {metadata_entity}")
def flatten(context, metadata_entity):
    context.metadata_entity_name = metadata_entity
    context.metadata_entity = context.instances[metadata_entity]

@when("the flatten method is called")
def flatten(context):
    context.flattened_return = context.metadata_entity.flatten()

@then("it should result in a non-nested dictionary")
def flatten(context):
    assert all([not isinstance(value, dict) for value in context.flattened_return.values()])

@when("I add a set of key:value pairs")
def add_values(context):
    context.metadata_entity['key'] = 'value'
    context.metadata_entity['status'] = 'PUBLIC'

@then("they should be loaded in the entity in the proper place")
def add_values(context):
    match context.metadata_entity_name:
        case "Biosample":
            assert context.metadata_entity.entity['characteristics'].get('key') == [{'text': 'value'}]
            assert context.metadata_entity.entity.get('status') == 'PUBLIC'
        case _:
            assert False, f"This test needs to be set up for {context.metadata_entity_name}"

@when("I delete a value")
def delete_values(context):
    del context.metadata_entity['release']

@then("it should be deleted from the entity")
def delete_values(context):
    match context.metadata_entity_name:
        case "Biosample":
            assert context.metadata_entity.entity.get('release') is None
        case _:
            assert False, f"This test needs to be set up for {context.metadata_entity_name}"

@when("I add a valid relationship")
def valid_relationship(context):
    context.metadata_entity.add_relationship(source="SAMEA131439753", target="SAMEA1234533", relationship="derived_from")

@then("it should be loaded at the root, under 'relationships'")
def valid_relationship(context):
    assert isinstance(context.metadata_entity.entity.get('relationships'), list)
    assert context.metadata_entity['relationships'] == [{
            "source": "SAMEA131439753",
            "target": "SAMEA1234533",
            "type": "derived_from"
        }]

@when("I add a valid external reference")
def valid_external_reference(context):
    external_reference = "https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_example_1"
    context.metadata_entity.add_external_reference(external_reference)

@then("it should be loaded at the root, under 'external_references'")
def valid_external_reference(context):
    assert isinstance(context.metadata_entity.entity.get('externalReferences'), list)
    assert context.metadata_entity['externalReferences'] == [{"url": "https://www.ebi.ac.uk/biosamples/docs/references/api/submit#_example_1"}]