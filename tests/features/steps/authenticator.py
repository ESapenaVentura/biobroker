from behave import *
import dotenv
import os
import re

from biobroker.authenticator import WebinAuthenticator, GenericAuthenticator

def load_credentials(prefix):
    values = dotenv.dotenv_values(".env")
    assert values, f"'.env' file must be present in the folder, with {prefix}_USERNAME and {prefix}_PASSWORD"
    return values[f'{prefix}_USERNAME'], values[f'{prefix}_PASSWORD']

@given("a {auth} and a set of credentials loaded from '.env' with prefix {prefix}")
def step_impl(context, auth, prefix):
    context.authenticator = eval(auth)
    context.username, context.password = load_credentials(prefix)

@when("I load the instance")
def step_impl(context):
    os.environ['API_ENVIRONMENT'] = "dev"
    context.authenticator_instance = context.authenticator(context.username, context.password)

@then("the auth endpoint should point to development")
def step_impl(context):
    assert "dev" in context.authenticator_instance.base_uri, "Auth endpoint should point to dev for tests"

@then("the token should conform to pattern {pattern}")
def step_impl(context, pattern):
    assert re.match(pattern, context.authenticator_instance.token), "Returned token does not match expected pattern"
