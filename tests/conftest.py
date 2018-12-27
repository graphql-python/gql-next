import os
import pytest
from types import ModuleType

@pytest.fixture
def swapi_schema():
    from gql.utils_schema import load_schema

    if 'SWAPI_SCHEMA' not in globals():
        filename = os.path.join(os.path.dirname(__file__), 'fixtures/swapi-schema.graphql')
        globals()['SWAPI_SCHEMA'] = load_schema(filename)

    return globals()['SWAPI_SCHEMA']


@pytest.fixture
def swapi_parser(swapi_schema):
    from gql.query_parser import QueryParser
    return QueryParser(swapi_schema)


@pytest.fixture
def github_schema():
    from gql.utils_schema import load_schema

    if 'GITHUB_SCHEMA' not in globals():
        filename = os.path.join(os.path.dirname(__file__), 'fixtures/github-schema.graphql')
        globals()['GITHUB_SCHEMA'] = load_schema(filename)

    return globals()['GITHUB_SCHEMA']

@pytest.fixture
def github_parser(github_schema):
    from gql.query_parser import QueryParser
    return QueryParser(github_schema)


@pytest.fixture
def module_compiler():
    def load_module(code, module_name=None):
        compiled = compile(code, '', 'exec')
        module = ModuleType(module_name or 'testmodule')
        exec(compiled, module.__dict__)
        return module

    return load_module
