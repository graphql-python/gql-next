import pytest
from gql.query_parser import QueryParser
from gql.renderer_dataclasses import DataclassesRenderer

@pytest.fixture
def swapi_dataclass_renderer(swapi_schema):
    return DataclassesRenderer(swapi_schema)


def test_document_parser_simple_query(swapi_dataclass_renderer, swapi_parser, module_compiler):
    """
    Expect code to render:
    ```
        @dataclass_json
        @dataclass(frozen=True)
        class QueryGetFilm:


            @dataclass_json
            @dataclass(frozen=True)
            class QueryGetFilmResponse():


                @dataclass_json
                @dataclass(frozen=True)
                class Film():

                    title: str
                    director: str


                returnOfTheJedi: Film = None


            data: QueryGetFilmResponse = None
            errors: Any = None
    ```
    """

    query = """
        query GetFilm {
          returnOfTheJedi: film(id: "1") {
            title
            director
          }
        }
    """

    parsed = swapi_parser.parse(query)
    rendered = swapi_dataclass_renderer.render(parsed)
    print(rendered)

    m = module_compiler(rendered)
    response = m.QueryGetFilm.from_json("""
    {
        "data": {
            "returnOfTheJedi": {
                "title": "Return of the Jedi",
                "director": "George Lucas"
            }
        }
    }
    """)

    assert response

    data = response.data
    assert data.returnOfTheJedi.title == 'Return of the Jedi'
    assert data.returnOfTheJedi.director == 'George Lucas'


def test_document_parser_query_with_fragment(swapi_parser, swapi_dataclass_renderer, module_compiler):
    """

        @dataclass_json
        @dataclass(frozen=True)
        class FilmFields():
            title: str
            director: str

        @dataclass_json
        @dataclass(frozen=True)
        class QueryGetFilm:

            @dataclass_json
            @dataclass(frozen=True)
            class QueryGetFilmResponse():

                @dataclass_json
                @dataclass(frozen=True)
                class Film(FilmFields):
                    openingCrawl: str

                returnOfTheJedi: Film = None

            data: QueryGetFilmResponse = None
            errors: Any = None
    """
    query = """
        query GetFilm {
          returnOfTheJedi: film(id: "1") {
            ...FilmFields
            openingCrawl

          }
        }

        fragment FilmFields on Film {
            title
            director
        }
    """

    parsed = swapi_parser.parse(query)
    rendered = swapi_dataclass_renderer.render(parsed)

    m = module_compiler(rendered)
    response = m.QueryGetFilm.from_json("""
    {
        "data": {
            "returnOfTheJedi": {
                "title": "Return of the Jedi",
                "director": "George Lucas",
                "openingCrawl": "la la la"
            }
        }
    }
    """)

    assert response

    data = response.data
    assert data.returnOfTheJedi.title == 'Return of the Jedi'
    assert data.returnOfTheJedi.director == 'George Lucas'
    assert data.returnOfTheJedi.openingCrawl == 'la la la'


def test_document_parser_query_with_complex_fragment(swapi_parser, swapi_dataclass_renderer, module_compiler):
    """
        ```
        @dataclass_json
        @dataclass(frozen=True)
        class CharacterFields():
            name: str

            @dataclass_json
            @dataclass(frozen=True)
            class Planet():
                name: str

            home: Planet

        @dataclass_json
        @dataclass(frozen=True)
        class QueryGetPerson:

            @dataclass_json
            @dataclass(frozen=True)
            class QueryGetFilmResponse():

                @dataclass_json
                @dataclass(frozen=True)
                class Person(CharacterFields):
                    pass

                luke: Person = None

            data: QueryGetFilmResponse = None
            errors: Any = None
        ```
    """
    query = """
        query GetPerson {
          luke: character(id: "luke") {
            ...CharacterFields
          }
        }

        fragment CharacterFields on Person {
            name

            home: homeworld {
                name
            }
        }
    """

    parsed = swapi_parser.parse(query)
    rendered = swapi_dataclass_renderer.render(parsed)

    m = module_compiler(rendered)
    response = m.QueryGetPerson.from_json("""
    {
        "data": {
            "luke": {
                "name": "Luke Skywalker",
                "home": {
                    "name": "Arakis"
                }
            }
        }
    }
    """)

    assert response

    data = response.data
    assert data.luke.name == 'Luke Skywalker'
    assert data.luke.home.name == 'Arakis'


def test_document_parser_query_with_complex_inline_fragment(swapi_parser, swapi_dataclass_renderer, module_compiler):
    """
    '''
        @dataclass_json
        @dataclass(frozen=True)
        class QueryGetPerson:

            @dataclass_json
            @dataclass(frozen=True)
            class QueryGetPersonResponse():

                @dataclass_json
                @dataclass(frozen=True)
                class Person():
                    name: str

                    @dataclass_json
                    @dataclass(frozen=True)
                    class Planet():
                        name: str

                    home: Planet

                luke: Person = None

            data: QueryGetPersonResponse = None
            errors: Any = None
    '''
    """
    query = """
        query GetPerson {
          luke: character(id: "luke") {
            ... on Person {
              name
              home: homeworld {
                name
              }
            }
          }
        }
    """

    parsed = swapi_parser.parse(query)
    rendered = swapi_dataclass_renderer.render(parsed)

    m = module_compiler(rendered)
    response = m.QueryGetPerson.from_json("""
        {
            "data": {
                "luke": {
                    "name": "Luke Skywalker",
                    "home": {
                        "name": "Arakis"
                    }
                }
            }
        }
        """)

    assert response

    data = response.data
    assert data.luke.name == 'Luke Skywalker'
    assert data.luke.home.name == 'Arakis'
