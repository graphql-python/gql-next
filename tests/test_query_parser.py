import pytest
from gql.query_parser import QueryParser, AnonymousQueryError, InvalidQueryError


def test_document_parser_fails_on_nameless_op(swapi_schema):
    query = """
        {
          allFilms {
            totalCount
            edges {
              node {
                id
                title
                director
              }
            }
          }
        }
    """

    parser = QueryParser(swapi_schema)

    with pytest.raises(AnonymousQueryError):
        parser.parse(query)


def test_document_parser_fails_invalid_query(swapi_schema):
    query = """
        query ShouldFail {
          allFilms {
            totalCount
            edges {
              node {
                title
                nonExistingField
              }
            }
          }
        }
    """

    parser = QueryParser(swapi_schema)

    with pytest.raises(InvalidQueryError) as excinfo:
        parser.parse(query)

    print(str(excinfo))


def test_document_parse_fragments(swapi_schema):
    """
    Expected result would be something like this:

    ```
    from typing import List
    from dataclasses import dataclass

    @dataclass
    class QueryGetAllFilmsResponse:
        @dataclass
        class AllFilms:

            @dataclass
            class Edge:
                @dataclass
                class Node:
                    id: str
                    title: str
                    director: str

                node: Node

            totalCount: int
            edges: List[Edge]

        allFilms: AllFilms
    ```
    """

    query = """
        query GetAllFilms {
          allFilms {
            count: totalCount
            edges {
              node {
                id
                title
                director
              }
            }
          }
          allHeroes {
            edges {
              node {
                ...HeroFields
              }
            }
          }
        }

        fragment HeroFields on Hero {
            id
            name
        }
    """

    parser = QueryParser(swapi_schema)
    result = parser.parse(query)
    parsed = result.parsed
    assert len(parsed) == 2
    assert parsed[0].name == 'QueryGetAllFilmsResponse'
    assert parsed[1].name == 'HeroFields'

    first_level = parsed[0].children
    assert first_level[0].name == 'allFilms' and first_level[0].graphql_type.name == 'FilmConnection'
    assert first_level[0].children

    sec_level = first_level[0].children
    assert len(sec_level) == 2
    assert sec_level[0].name == 'count' and sec_level[0].graphql_type.name == 'Int'
    assert sec_level[1].name == 'edges' and sec_level[1].graphql_type.of_type.name == 'FilmEdge'

    node = sec_level[1].children[0]
    assert node
    assert node.graphql_type.name == 'Film'
    assert len(node.children) == 3
    assert node.children[0].name == 'id' and node.children[0].graphql_type.of_type.name == 'ID'
    assert node.children[1].name == 'title' and node.children[1].graphql_type.of_type.name == 'String'
    assert node.children[2].name == 'director' and node.children[2].graphql_type.of_type.name == 'String'

    assert first_level[1].name == 'allHeroes' and first_level[1].graphql_type.name == 'HeroConnection'

    sec_level = first_level[1].children
    assert len(sec_level) == 1
    assert sec_level[0].name == 'edges'

    node = sec_level[0].children[0]
    assert node
    assert node.graphql_type.name == 'Hero'

    assert len(node.children) == 0
    assert 'HeroFields' in node.fragments
