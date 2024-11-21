from behave import *
import os
import json

import sys
sys.path.insert(0, "../../")


from biobroker.authenticator import WebinAuthenticator
from biobroker.api import BsdApi
from biobroker.api.exceptions import StructuredDataError
from biobroker.metadata_entity import Biosample

import mock

def load_accessioned_entity(file_name, times, metadata_entity):
    with open(f"assets/{file_name}") as f:
        content = metadata_entity(json.load(f))
    return content if times == 1 else [content] * times

def load_credentials(prefix):
    username = os.environ.get(f'{prefix}_USERNAME')
    password = os.environ.get(f'{prefix}_PASSWORD')
    assert username and password, f"Username or password missing from environment variables for authenticator with prefix {prefix}"
    return username, password

@given("all the API classes and their corresponding authenticator")
def preload_instances(context):
    context.instances = {}
    for subclass_api, subclass_authenticator, prefix in (('BsdApi', 'WebinAuthenticator', 'WEBIN'),):
        subclass_api_object = eval(subclass_api)
        subclass_authenticator_object = eval(subclass_authenticator)
        os.environ['API_ENVIRONMENT'] = "dev"
        subclass_authenticator_instance = subclass_authenticator_object(*load_credentials(prefix))
        context.instances[subclass_api] = subclass_api_object(subclass_authenticator_instance)
        assert "dev" in context.instances[subclass_api].base_uri


@given("{length} {metadata_entity} filled with content from {metadata_json_path}")
def submit(context, length, metadata_entity, metadata_json_path):
    context.length = int(length)
    context.metadata_entity_subclass = eval(metadata_entity)
    with open(metadata_json_path, 'r') as f:
        context.entity_metadata_json = json.load(f)
    context.metadata_entity = [eval(metadata_entity)(context.entity_metadata_json)] * context.length

@when("an API instance named {api_instance_name} is used to submit it to the archive")
def submit(context, api_instance_name):
    context.api_subclass_instance = context.instances[api_instance_name]
    function_to_mock = f"biobroker.api.{api_instance_name}._submit"
    if context.length > 1:
        function_to_mock += "_multiple"
    with mock.patch(function_to_mock) as mocked_submit_function:
        accessioned_entities = load_accessioned_entity(f"accessioned_{api_instance_name}_entity.json", context.length,
                                                       context.metadata_entity_subclass)
        # Accessioned entities = [Biosample(accesioned.json) * length]
        mocked_submit_function.return_value = accessioned_entities # [Biosample(accessioned.json)]
        context.submitted_entities = context.api_subclass_instance.submit(context.metadata_entity)

@then("we get a list of entities with the expected length and the accession set up")
def submit(context):
    assert len(context.submitted_entities) == context.length, "Expected length and number of submitted entities does not match"
    for entity in context.submitted_entities:
        assert entity.accession == "SAMEA131439753"

@then("retrieving those entities by accession should result in the exact same entities")
def retrieve(context):
    accessions = [entity.accession for entity in context.submitted_entities]
    retrieved_entities = context.api_subclass_instance.retrieve(accessions)
    assert all([context.submitted_entities[i].entity == retrieved_entities[i].entity
                for i in range(len(retrieved_entities))])

@when("An API instance named {api_instance_name} is used to update the entity")
def update(context, api_instance_name):
    context.api_instance_name = api_instance_name
    context.api_subclass_instance = context.instances[api_instance_name]
    function_to_mock = f"biobroker.api.{api_instance_name}._update"
    if context.length > 1:
        function_to_mock += "_multiple"
    with mock.patch(function_to_mock) as mocked_update_function:
        context.accessioned_entities = load_accessioned_entity(f"accessioned_{api_instance_name}_entity.json", context.length,
                                                       context.metadata_entity_subclass)
        mocked_update_function.return_value = context.accessioned_entities
        context.updated_entities = context.api_subclass_instance.update(context.metadata_entity)

@then("we get a list of entities with the expected length and the updated metadata")
def update(context):
    assert len(context.updated_entities) == context.length
    original_acessioned = context.accessioned_entities if isinstance(context.accessioned_entities, list) else [context.accessioned_entities]
    assert all([original_acessioned[i] is context.updated_entities[i] for i in range(len(context.updated_entities))])

@given("an invalid structured data object")
def struc_data_negative(context):
    with open('assets/structured_data_invalid.json', 'r') as f:
        context.structured_data = json.load(f)

@when("the structured data is submitted to Biosamples")
def struc_data_negative(context):
    biosamples_api = context.instances['BsdApi']
    try:
        biosamples_api.submit_structured_data(context.structured_data)
        assert False, "This method call should raise an error"
    except StructuredDataError as e:
        context.error = e

@then("it should raise an error with the expected error messages")
def struc_data_negative(context):
    assert "accession" in context.error.message
    assert "data-->0-->webinSubmissionAccountId" in context.error.message
    assert "data-->0-->content-->0-->resistancePhenotype" in context.error.message
    assert "data-->0-->content-->0-->platform" in context.error.message

@given("a valid structured data object with an invalid accession")
def struc_data_invalid_acc(context):
    with open('assets/structured_data_invalid_accession.json', 'r') as f:
        context.structured_data = json.load(f)

@then("it should raise an error regarding the accession")
def struc_data_invalid_acc(context):
    assert "accession: Value provided must match pattern" in context.error.message
    assert context.error.message.count('\n\t-') == 1, "Only accession error should be raised"