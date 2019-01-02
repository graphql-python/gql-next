from io import BytesIO
from tokenize import tokenize, TokenInfo, NL, NEWLINE, ENCODING, NAME, OP

from gql.config import Config
from gql.query_parser import QueryParser
from gql.renderer_dataclasses import DataclassesRenderer
from gql.utils_schema import load_schema


def get_config():
    if 'CONFIG' not in globals():
        globals()['CONFIG'] = Config.load('.gql.json')

    return globals()['CONFIG']


def get_schema():
    if 'SCHEMA' not in globals():
        config = get_config()
        globals()['SCHEMA'] = load_schema(config.schema)

    return globals()['SCHEMA']


def get_parser() -> QueryParser:
    if 'PARSER' not in globals():
        schema = get_schema()
        globals()['PARSER'] = QueryParser(schema)

    return globals()['PARSER']


def get_renderer() -> DataclassesRenderer:
    if 'RENDERER' not in globals():
        schema = get_schema()
        config = get_config()
        globals()['RENDERER'] = DataclassesRenderer(schema, config, classname_prefix='__')

    return globals()['RENDERER']


def tokenize_python_stream(stream: BytesIO) -> [TokenInfo]:
    return tokenize(stream.readline, )


def tokenize_python_string(value: str) -> [TokenInfo]:
    stream = BytesIO(value.encode('utf-8'))
    return tokenize_python_stream(stream)


def gql_transform(stream: BytesIO):
    tokens = list(tokenize_python_stream(stream))
    transformed_tokens = []

    query_started = False
    for token in tokens:
        if token.type == 1 and token.string == 'gql':  # type NAME
            query_started = True
            continue

        if token.type == 3 and query_started: # type STRING
            query_str = token.string.strip("'''")
            parsed_query = get_parser().parse(query_str)
            rendered = get_renderer().render(parsed_query)

            # verify 2 previous tokens are NAME and OP ('=')
            prev_tokens = transformed_tokens[:-2]
            gql_tokens = transformed_tokens[-2:]

            if gql_tokens[0].type == NAME and gql_tokens[1].type == OP:
                transformed_tokens = prev_tokens

                rendered_token = TokenInfo('CUSTOM', rendered, gql_tokens[0].start, gql_tokens[0].end, gql_tokens[0].line)
                transformed_tokens.append(rendered_token)
                transformed_tokens.append(gql_tokens[0])
                transformed_tokens.append(gql_tokens[1])

                op_name = get_renderer().get_operation_class_name(parsed_query)

                transformed_tokens.append(TokenInfo(NAME, f'{op_name}Namespace.{op_name}', token.start, token.end, token.line))
                continue

        transformed_tokens.append(token)
        query_started = False

    result = untokenize(transformed_tokens)
    return result.rstrip()


def gql_transform_string(input: str):
    stream = BytesIO(input.encode('utf-8'))
    return gql_transform(stream)


def untokenize(tokens: [TokenInfo]) -> str:
    parts = []
    prev_row = 1
    prev_col = 0

    for token in tokens:
        ttype, tvalue, tstart, tend, tline = token
        row, col = tstart

        if ttype == ENCODING:
            continue

        assert row == prev_row, 'Unexpected jump in rows on line:%d: %s' % (row, tline)

        # Add whitespace
        col_offset = col - prev_col
        # assert col_offset >= 0
        if col_offset > 0:
            parts.append(' ' * col_offset)

        parts.append(tvalue)
        prev_row, prev_col = tend

        if ttype in (NL, NEWLINE):
            prev_row += 1
            prev_col = 0

        if ttype == 'CUSTOM':
            parts.append('\n')
            prev_col = 0


    return ''.join(parts)
