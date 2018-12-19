import pytest
from gql.utils_codegen import CodeGenerator


def test_codegen_write_simple_strings(module_compiler):
    gen = CodeGenerator()
    gen.write('def sum(a, b):')
    gen.indent()
    gen.write('return a + b')

    code = str(gen)

    m = module_compiler(code)
    assert m.sum(2, 3) == 5


def test_codegen_write_template_strings_args(module_compiler):
    gen = CodeGenerator()
    gen.write('def {0}(a, b):', 'sum')
    gen.indent()
    gen.write('return a + b')

    code = str(gen)

    m = module_compiler(code)
    assert m.sum(2, 3) == 5


def test_codegen_write_template_strings_kwargs(module_compiler):
    gen = CodeGenerator()
    gen.write('def {method}(a, b):', method='sum')
    gen.indent()
    gen.write('return a + b')

    code = str(gen)

    m = module_compiler(code)
    assert m.sum(2, 3) == 5


def test_codegen_block(module_compiler):
    gen = CodeGenerator()
    gen.write('def sum(a, b):')
    with gen.block():
        gen.write('return a + b')

    code = str(gen)

    m = module_compiler(code)
    assert m.sum(2, 3) == 5


def test_codegen_write_block(module_compiler):
    gen = CodeGenerator()
    with gen.write_block('def {name}(a, b):', name='sum'):
        gen.write('return a + b')

    code = str(gen)

    m = module_compiler(code)
    assert m.sum(2, 3) == 5


def test_codegen_write_lines(module_compiler):
    lines = [
        '@staticmethod',
        'def sum(a, b):'
        '    return a + b'
    ]
    gen = CodeGenerator()
    gen.write('class Math:')
    gen.indent()
    gen.write_lines(lines)

    code = str(gen)

    m = module_compiler(code)
    assert m.Math.sum(2, 3) == 5
