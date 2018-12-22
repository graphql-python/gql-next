import pytest
from deepdiff import DeepDiff
from dataclasses import asdict
from gql.query_parser import QueryParser, ParsedQuery, ParsedOperation, ParsedObject, ParsedField, ParsedVariableDefinition, AnonymousQueryError, InvalidQueryError


def test_parser_fails_on_nameless_op(swapi_schema):
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


def test_parser_fails_invalid_query(swapi_schema):
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


def test_parser_query(swapi_schema):
    query = """
        query GetFilm {
          returnOfTheJedi: film(id: "1") {
            title
            director
          }
        }
    """

    parser = QueryParser(swapi_schema)
    parsed = parser.parse(query)

    expected = asdict(ParsedQuery(
        query=query,
        objects=[
            ParsedOperation(
                name='GetFilm',
                type='query',
                children=[
                    ParsedObject(
                        name='GetFilmData',
                        fields=[
                            ParsedField(name='returnOfTheJedi', type='Film', nullable=True)
                        ],
                        children=[
                            ParsedObject(
                                name='Film',
                                fields=[
                                    ParsedField(name='title', type='str', nullable=False),
                                    ParsedField(name='director', type='str', nullable=False),
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    ))

    parsed_dict = asdict(parsed)

    assert bool(parsed)
    assert parsed_dict == expected, str(DeepDiff(parsed_dict, expected))


def test_parser_query_inline_fragment(swapi_schema):
    query = """
        query GetFilm {
          returnOfTheJedi: film(id: "1") {
            ... on Film {
                title
                director
            }
          }
        }
    """

    parser = QueryParser(swapi_schema)
    parsed = parser.parse(query)

    expected = asdict(ParsedQuery(
        query=query,
        objects=[
            ParsedOperation(
                name='GetFilm',
                type='query',
                children=[
                    ParsedObject(
                        name='GetFilmData',
                        fields=[
                            ParsedField(name='returnOfTheJedi', type='Film', nullable=True)
                        ],
                        children=[
                            ParsedObject(
                                name='Film',
                                fields=[
                                    ParsedField(name='title', type='str', nullable=False),
                                    ParsedField(name='director', type='str', nullable=False),
                                ]
                            )
                        ],
                    )
                ]
            )
        ]
    ))

    parsed_dict = asdict(parsed)

    assert bool(parsed)
    assert parsed_dict == expected, str(DeepDiff(parsed_dict, expected))


def test_parser_query_fragment(swapi_schema):
    query = """
        query GetFilm {
          returnOfTheJedi: film(id: "1") {
            id
            ...FilmFields
          }
        }

        fragment FilmFields on Film {
            title
            director
        }
    """

    parser = QueryParser(swapi_schema)
    parsed = parser.parse(query)

    expected = asdict(ParsedQuery(
        query=query,
        objects=[
            ParsedOperation(
                name='GetFilm',
                type='query',
                children=[
                    ParsedObject(
                        name='GetFilmData',
                        fields=[
                            ParsedField(name='returnOfTheJedi', type='Film', nullable=True)
                        ],
                        children=[
                            ParsedObject(
                                name='Film',
                                parents=['FilmFields'],
                                fields=[
                                    ParsedField(name='id', type='str', nullable=False),
                                ]
                            )
                        ],
                    ),
                ]
            ),
            ParsedObject(
                name='FilmFields',
                fields=[
                    ParsedField(name='title', type='str', nullable=False),
                    ParsedField(name='director', type='str', nullable=False),
                ],
            )
        ]
    ))

    parsed_dict = asdict(parsed)

    assert bool(parsed)
    assert parsed_dict == expected, str(DeepDiff(parsed_dict, expected))


def test_parser_query_complex_fragment(swapi_schema):
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

    parser = QueryParser(swapi_schema)
    parsed = parser.parse(query)

    expected = asdict(ParsedQuery(
        query=query,
        objects=[
            ParsedOperation(
                name='GetPerson',
                type='query',
                children=[
                    ParsedObject(
                        name='GetPersonData',
                        fields=[
                            ParsedField(name='luke', type='Person', nullable=True)
                        ],
                        children=[
                            ParsedObject(
                                name='Person',
                                parents=['CharacterFields'],
                                fields=[]
                            )
                        ],
                    ),
                ]
            ),
            ParsedObject(
                name='CharacterFields',
                fields=[
                    ParsedField(name='name', type='str', nullable=False),
                    ParsedField(name='home', type='Planet', nullable=False),
                ],
                children=[
                    ParsedObject(
                        name='Planet',
                        fields=[
                            ParsedField(name='name', type='str', nullable=False),
                        ]
                    )
                ]
            )
        ]
    ))

    parsed_dict = asdict(parsed)

    assert bool(parsed)
    assert parsed_dict == expected, str(DeepDiff(parsed_dict, expected))


def test_parser_query_with_variables(swapi_schema):
    query = """
        query GetFilm($theFilmID: ID!) {
          returnOfTheJedi: film(id: $theFilmID) {
            title
            director
          }
        }
    """

    parser = QueryParser(swapi_schema)
    parsed = parser.parse(query)

    expected = asdict(ParsedQuery(
        query=query,
        objects=[
            ParsedOperation(
                name='GetFilm',
                type='query',
                variables=[
                    ParsedVariableDefinition(name='theFilmID', type='str', nullable=False)
                ],
                children=[
                    ParsedObject(
                        name='GetFilmData',
                        fields=[
                            ParsedField(name='returnOfTheJedi', type='Film', nullable=True)
                        ],
                        children=[
                            ParsedObject(
                                name='Film',
                                fields=[
                                    ParsedField(name='title', type='str', nullable=False),
                                    ParsedField(name='director', type='str', nullable=False),
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    ))

    parsed_dict = asdict(parsed)

    assert bool(parsed)
    assert parsed_dict == expected, str(DeepDiff(parsed_dict, expected))


def test_connection_query(swapi_schema):
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
    parsed = parser.parse(query)

    expected = asdict(ParsedQuery(
        query=query,
        objects=[
            ParsedOperation(
                name='GetAllFilms',
                type='query',
                children=[
                    ParsedObject(
                        name='GetAllFilmsData',
                        fields=[
                            ParsedField(name='allFilms', type='FilmConnection', nullable=True),
                            ParsedField(name='allHeroes', type='HeroConnection', nullable=True)
                        ],
                        children=[
                            ParsedObject(
                                name='FilmConnection',
                                fields=[
                                    ParsedField(name='count', type='int', nullable=True),
                                    ParsedField(name='edges', type='List[FilmEdge]', nullable=True),
                                ],
                                children=[
                                    ParsedObject(
                                        name='FilmEdge',
                                        fields=[
                                            ParsedField(name='node', type='Film', nullable=True)
                                        ],
                                        children=[
                                            ParsedObject(
                                                name='Film',
                                                fields=[
                                                    ParsedField(name='id', type='str', nullable=False),
                                                    ParsedField(name='title', type='str', nullable=False),
                                                    ParsedField(name='director', type='str', nullable=False)
                                                ]
                                            )
                                        ]
                                    )

                                ]
                            ),
                            ParsedObject(
                                name='HeroConnection',
                                fields=[
                                    ParsedField(name='edges', type='List[HeroEdge]', nullable=True),
                                ],
                                children=[
                                    ParsedObject(
                                        name='HeroEdge',
                                        fields=[
                                            ParsedField(name='node', type='Hero', nullable=True)
                                        ],
                                        children=[
                                            ParsedObject(
                                                name='Hero',
                                                parents=['HeroFields'],
                                                fields=[]
                                            )
                                        ]
                                    )

                                ]
                            ),
                        ],
                    ),
                ]
            ),
            ParsedObject(
                name='HeroFields',
                fields=[
                    ParsedField(name='id', type='str', nullable=False),
                    ParsedField(name='name', type='str', nullable=False),
                ],
            )
        ]
    ))

    parsed_dict = asdict(parsed)

    assert bool(parsed)
    assert parsed_dict == expected, str(DeepDiff(parsed_dict, expected))
