#!/usr/bin/env python
import codecs, encodings
import sys
from encodings import utf_8
from io import BytesIO
from tokenize import TokenInfo, NAME, OP

from gql.codec.transform import tokenize_python_stream, untokenize
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

                transformed_tokens.append(TokenInfo(NAME, op_name, token.start, token.end, token.line))
                continue

        transformed_tokens.append(token)
        query_started = False

    result = untokenize(transformed_tokens)
    return result.rstrip()


def gql_transform_string(input: str):
    stream = BytesIO(input.encode('utf-8'))
    return gql_transform(stream)


def gql_decode(input, errors='strict'):
    return utf_8.decode(gql_transform_string(input), errors)


class GQLIncrementalDecoder(utf_8.IncrementalDecoder):
    def decode(self, input, final=False):
        self.buffer += input
        if final:
            buff = self.buffer
            self.buffer = ''
            return super().decode(gql_transform_string(buff), final=True)


class GQLStreamReader(utf_8.StreamReader):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.stream = StringIO(gql_decode(self.stream))


def search_function(encoding):
    if encoding != 'gql': return None
    # Assume utf8 encoding
    utf8 = encodings.search_function('utf8')
    return codecs.CodecInfo(
        name='gql',
        encode=utf8.encode,
        decode=gql_decode,
        incrementalencoder=utf8.incrementalencoder,
        incrementaldecoder=GQLIncrementalDecoder,
        streamreader=GQLStreamReader,
        streamwriter=utf8.streamwriter)

codecs.register(search_function)

_USAGE = """\
Wraps a python command to allow it to recognize pyxl-coded files with
no source modifications.

Usage:
    python -m gql.codec.register -m module.to.run [args...]
    python -m gql.codec.register path/to/script.py [args...]
"""

if __name__ == '__main__':
    script = None
    if len(sys.argv) >= 3 and sys.argv[1] == '-m':
        mode = 'module'
        module = sys.argv[2]
        del sys.argv[1:3]
    elif len(sys.argv) >= 2:
        mode = 'script'
        script = sys.argv[1]
        sys.argv = sys.argv[1:]
    else:
        print(_USAGE)
        sys.exit(1)

    if mode == 'module':
        import runpy
        runpy.run_module(module, run_name='__main__', alter_sys=True)
    elif mode == 'script':
        with open(script) as f:
            global __file__
            __file__ = script
            # Use globals as our "locals" dictionary so that something
            # that tries to import __main__ (e.g. the unittest module)
            # will see the right things.
            exec(f.read() in globals(), globals())
