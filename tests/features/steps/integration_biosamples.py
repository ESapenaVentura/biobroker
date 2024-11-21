from behave import *
import os

import sys
sys.path.insert(0, "../../")

from biobroker.api.exceptions import BiosamplesValidationError
from biobroker.input_processor import XlsxInputProcessor
from biobroker.output_processor import XlsxOutputProcessor
from biobroker.authenticator import WebinAuthenticator
from biobroker.api import BsdApi
from biobroker.metadata_entity import Biosample

import os

def load_credentials(prefix):
    username = os.environ.get(f'{prefix}_USERNAME')
    password = os.environ.get(f'{prefix}_PASSWORD')
    assert username and password, f"Username or password missing from environment variables for authenticator with prefix {prefix}"
    return username, password

@given("an input excel file and all the biobroker entities set up")
def load_everything(context):
    os.environ['API_ENVIRONMENT'] = "dev"
    context.excel_file_path = 'assets/valid_minimal.xlsx'
    context.input_processor = XlsxInputProcessor(context.excel_file_path)
    context.output_processor = XlsxOutputProcessor('output.xlsx')
    context.authenticator = WebinAuthenticator(*load_credentials('WEBIN'))
    context.api = BsdApi(context.authenticator)
    context.samples = context.input_processor.process(Biosample)

@when("I submit using the BsdApi")
def submit(context):
    context.submitted_samples = context.api.submit(context.samples)

@then("the samples should be correctly submitted")
def submit(context):
    assert isinstance(context.submitted_samples, list)
    assert all([isinstance(entity, Biosample) for entity in context.submitted_samples])
    assert all([entity.accession is not None for entity in context.submitted_samples])

@then("I can save it again as an excel file")
def save(context):
    context.output_processor.save(context.submitted_samples)
    assert os.path.isfile('output.xlsx')
    os.remove('output.xlsx')

@when("I add checklist ERC000017 to the sample and submit")
def submit_checklist_error(context):
    context.samples[0]['checklist'] = 'ERC000017'
    try:
        context.api.submit(context.samples)
        assert False, "Shouldn't be allowed to be submitted"
    except Exception as e:
        context.error = e

@then("the sample should raise errors related to the checklist")
def submit_checklist_error(context):
    assert isinstance(context.error, BiosamplesValidationError)

@when("I modify the metadata to contain the mandatory fields for the checklist")
def submit_checklist_pass(context):
    context.samples[0]['project name'] = "Your fake project"
    context.samples[0]['organism'] = "Homo sapiens"
    context.samples[0]['collection date'] = "2024-09-01"
    context.samples[0]['geographic location (country and/or sea)'] = "Mediterranean Sea"
    context.samples[0]['geographic location (latitude)'] = 1.2234
    context.samples[0]['geographic location (longitude)'] = 7.21
    context.samples[0]['broad-scale environmental context'] = "United Kingdom weather"
    context.samples[0]['local environmental context'] = "Mostly rainy"
    context.samples[0]['environmental medium'] = "Please read my plant"