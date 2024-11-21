from behave import *
import os
import re

import sys
sys.path.insert(0, "../../")

from biobroker.authenticator import WebinAuthenticator, GenericAuthenticator

def load_credentials(prefix):
    username = os.environ.get(f'{prefix}_USERNAME')
    password = os.environ.get(f'{prefix}_PASSWORD')
    assert username and password, f"Username or password missing from environment variables for authenticator with prefix {prefix}"
    return username, password

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
