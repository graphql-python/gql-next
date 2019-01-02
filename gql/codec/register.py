#!/usr/bin/env python
import codecs
import encodings
import sys
from encodings import utf_8
from io import BytesIO

from gql.codec.transform import gql_transform, gql_transform_string


def gql_decode(input, errors='strict'):
    return utf_8.decode(input)
    # return utf_8.decode(gql_transform_string(input), errors)


class GQLIncrementalDecoder(utf_8.IncrementalDecoder):
    def decode(self, input: bytes, final: bool=False):
        self.buffer += input
        if final:
            buff = self.buffer
            self.buffer = ''
            return gql_transform(BytesIO(buff))


class GQLStreamReader(utf_8.StreamReader):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.stream = BytesIO(gql_decode(self.stream))


def search_function(encoding):
    if encoding != 'gql':
        return None

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
        with open(script, encoding='gql') as f:
            global __file__
            __file__ = script
            # Use globals as our "locals" dictionary so that something
            # that tries to import __main__ (e.g. the unittest module)
            # will see the right things.
            code = f.read()
            print(code)
            exec(code, globals())
