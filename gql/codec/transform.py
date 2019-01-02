from io import BytesIO
from tokenize import tokenize, TokenInfo, NL, NEWLINE, ENCODING


def tokenize_python_stream(stream: BytesIO) -> [TokenInfo]:
    return tokenize(stream.readline, )


def tokenize_python_string(value: str) -> [TokenInfo]:
    stream = BytesIO(value.encode('utf-8'))
    return tokenize_python_stream(stream)


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
