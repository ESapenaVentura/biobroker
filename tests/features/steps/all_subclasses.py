from behave import *
import json
import inspect
import os
import sys
sys.path.insert(0, "../../")

from biobroker.api import GenericApi, BsdApi
from biobroker.generic.exceptions import MandatoryFunctionNotSet
from biobroker.input_processor import TsvInputProcessor, XlsxInputProcessor, GenericInputProcessor
from biobroker.metadata_entity import GenericEntity, Biosample
from biobroker.output_processor import TsvOutputProcessor, XlsxOutputProcessor, GenericOutputProcessor
from biobroker.authenticator import WebinAuthenticator


def test_mandatory_methods(instance, list_of_methods):
    for mandatory_method in list_of_methods:
        try:
            method = eval(f"instance.{mandatory_method}")
            signature = inspect.signature(method)
            arguments = ["fakeValue" for _ in range(len(signature.parameters))]
            method(*arguments)
        except MandatoryFunctionNotSet:
            assert False, f"Please set mandatory method {mandatory_method} for subclass"
        except:
            continue

def GenericInputProcessor(input_processor: type[GenericInputProcessor]):
    assert input_processor.input_data

def GenericOutputProcessor(output_processor: type[GenericOutputProcessor]):
    assert output_processor.path

def GenericAuthenticator(authenticator: type[WebinAuthenticator]):
    assert authenticator.base_uri is not None
    assert authenticator.username is not None
    assert authenticator.password is not None
    assert authenticator.auth_endpoint is not None
    assert authenticator.token is not None

def GenericEntity(entity: type[GenericEntity]):
    assert entity.entity is not None
    assert entity.id is not None
    assert entity.accession is not None
    test_mandatory_methods(entity, ('flatten', '__setitem__', '__delitem__', '__contains__'))

def GenericApi(api: type[GenericApi]):
    assert api.authenticator is not None
    assert api.base_uri is not None
    test_mandatory_methods(api, ('_submit', '_sumit_multiple', '_retrieve', '_retrieve_multiple',
                               '_update', '_update_multiple'))


def load_credentials_webin():
    username = os.environ.get('WEBIN_USERNAME')
    password = os.environ.get('WEBIN_PASSWORD')
    assert username and password, f"Username or password missing from environment variables for authenticator with prefix WEBIN"
    return username, password

def load_webin_authenticator():
    return (WebinAuthenticator(*load_credentials_webin()),)

def load_biosample_valid_json():
    with open('assets/valid_minimal.json', 'r') as f:
        value = json.load(f)
    return (value,)


@given('I have a {subclass_object} and its init arguments: {arguments}')
def step_impl(context, subclass_object, arguments):
    context.entity = eval(subclass_object)
    context.args = eval(arguments)
    assert isinstance(context.args, list), "Arguments must be provided as a list"

@when('I load the instance with the arguments')
def step_impl(context):
    # Checking for functions
    load_arguments = []
    for index, arg in enumerate(context.args):
        match arg:
            case "function":
                function = eval(context.args[index + 1])
                load_arguments.extend(function())
                del context.args[index + 1]
            case _:
                load_arguments.append(arg)

    context.loaded_instance = context.entity(*load_arguments)

@then('it should have all mandatory fields and methods from the parent class {parent_class}')
def step_impl(context, parent_class):
    eval(parent_class)(context.loaded_instance)
