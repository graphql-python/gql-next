import pytest
from gql.codec import register

from gql.config import Config
from gql.renderer_dataclasses import DataclassesRenderer

EXAMPLE = """
# Use gql'<query>'
GetFilm = gql'''
    query GetFilm {
      film(id: "1") {
        title
        director
      }
    }
'''

result = GetFilm.execute()
film = result.data.film
"""

@pytest.fixture(autouse=True)
def mock_codec_config(swapi_schema, swapi_parser, mocker):
    renderer = DataclassesRenderer(swapi_schema, Config(schema='schemaurl', documents=''), classname_prefix='__')

    mocker.patch.object(register, 'get_schema', return_value=swapi_schema)
    mocker.patch.object(register, 'get_parser', return_value=swapi_parser)
    mocker.patch.object(register, 'get_renderer', return_value=renderer)


def test_gql_transform_string():
    x = register.gql_transform_string(EXAMPLE)
    assert x
