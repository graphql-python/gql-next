#!/usr/bin/env python
import os
import sys
import codecs
import encodings
from encodings import utf_8
from io import BytesIO

from gql.codec.transform import gql_transform
from gql.query_parser import InvalidQueryError


def gql_decode(value, **_):
    decoded, decoded_length = utf_8.decode(value)
    decoded = decoded.replace('# coding: gql', '')
    try:
        bio = BytesIO(decoded.encode('utf-8'))
        result = gql_transform(bio)
        return result, decoded_length
    except InvalidQueryError:
        raise
    except Exception as ex:
        return decoded, decoded_length


class GQLIncrementalDecoder(utf_8.IncrementalDecoder):
    def decode(self, input: bytes, final: bool = False):  # pylint:disable=redefined-builtin
        self.buffer += input
        if final:
            buff = self.buffer
            self.buffer = ''
            buff = buff.decode('utf-8')
            buff = buff.replace('# coding: gql', '')
            buff = buff.encode('utf-8')
            result = gql_transform(BytesIO(buff))
            return result

        return None


class GQLStreamReader(utf_8.StreamReader):
    # pylint:disable=abstract-method

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.stream = BytesIO(gql_decode(self.stream))


def search_function(encoding):
    if encoding not in ('gql', 'graphql', 'pygql'):
        return None

    # Assume utf8 encoding
    utf8 = encodings.search_function('utf8')
    return codecs.CodecInfo(
        name=encoding,
        encode=utf8.encode,
        decode=gql_decode,
        incrementalencoder=utf8.incrementalencoder,
        incrementaldecoder=GQLIncrementalDecoder,
        streamreader=GQLStreamReader,
        streamwriter=utf8.streamwriter
    )


import gql.codec.fast_register

_USAGE = """\
Wraps a python command to allow it to recognize GraphQL-coded files with
no source modifications.

Usage:
    python -m gql.codec.register -m module.to.run [args...]
    python -m gql.codec.register path/to/script.py [args...]
"""


def main():
    # pylint:disable=exec-used,redefined-builtin,global-statement
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
        with open(script) as file:
            global __file__
            __file__ = script
            # Use globals as our "locals" dictionary so that something
            # that tries to import __main__ (e.g. the unittest module)
            # will see the right things.
            code = file.read()
            print(code)
            exec(code, globals())


if __name__ == '__main__':
    main()
