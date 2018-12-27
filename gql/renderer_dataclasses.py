from graphql import GraphQLSchema, GraphQLEnumType

from gql.config import Config
from gql.utils_codegen import CodeChunk
from gql.query_parser import ParsedQuery, ParsedField, ParsedObject, ParsedEnum, ParsedOperation, ParsedVariableDefinition


CLASS_TEMPLATE = """
@dataclass_json
@dataclass(frozen=True)
"""


class DataclassesRenderer:

    def __init__(self, schema: GraphQLSchema, config: Config):
        self.schema = schema
        self.config = config

    def render(self, parsed_query: ParsedQuery):
        # We sort fragment nodes to be first and operations to be last because of dependecies
        buffer = CodeChunk()
        buffer.write('# AUTOGENERATED file. Do not Change!')
        buffer.write('from functools import partial')
        buffer.write('from typing import Any, Callable, Mapping, List')
        buffer.write('from enum import Enum')
        buffer.write('from dataclasses import dataclass, field')
        buffer.write('from dataclasses_json import dataclass_json')
        buffer.write('from gql.clients import Client, AsyncIOClient')
        buffer.write('')

        if self.config.custom_header:
            buffer.write_lines(self.config.custom_header.split('\n'))

        buffer.write('')

        # Enums
        if parsed_query.enums:
            self.__render_enum_field(buffer)
            for enum in parsed_query.enums:
                self.__render_enum(buffer, enum)

        # Iterate in reverse so that operation is last
        for obj in parsed_query.objects[::-1]:
            if isinstance(obj, ParsedObject):
                self.__render_object(parsed_query, buffer, obj)
            elif isinstance(obj, ParsedOperation):
                self.__render_operation(parsed_query, buffer, obj)

        return str(buffer)

    @staticmethod
    def __render_enum_field(buffer: CodeChunk):
        with buffer.write_block('def enum_field(enum_type):'):
            with buffer.write_block('def encode_enum(value):'):
                buffer.write('return value.value')
            buffer.write('')
            with buffer.write_block('def decode_enum(t, value):'):
                buffer.write('return t(value)')

            buffer.write('')
            buffer.write("return field(metadata={'dataclasses_json': {'encoder': encode_enum, 'decoder': partial(decode_enum, enum_type)}})")
            buffer.write('')

    def __render_object(self, parsed_query: ParsedQuery, buffer: CodeChunk, obj: ParsedObject):
        buffer.write('@dataclass_json')
        buffer.write('@dataclass')
        with buffer.write_block(f'class {obj.name}({", ".join(obj.parents)}):'):
            # render child objects
            if not obj.children:
                buffer.write('pass')
            else:
                for child_object in obj.children:
                    self.__render_object(parsed_query, buffer, child_object)

            # render fields
            sorted_fields = sorted(obj.fields, key=lambda f: 1 if f.nullable else 0)
            for field in sorted_fields:
                self.__render_field(parsed_query, buffer, field)

    def __render_operation(self, parsed_query: ParsedQuery, buffer: CodeChunk, parsed_op: ParsedOperation):
        buffer.write('@dataclass_json')
        buffer.write('@dataclass')
        with buffer.write_block(f'class {parsed_op.name}:'):
            buffer.write('__QUERY__ = """')
            buffer.write(parsed_query.query)
            buffer.write('"""')
            buffer.write('')

            # Render children
            for child_object in parsed_op.children:
                self.__render_object(parsed_query, buffer, child_object)

            # operation fields
            buffer.write('')
            buffer.write(f'data: {parsed_op.name}Data = None')
            buffer.write('errors: Any = None')
            buffer.write('')

            # Execution functions
            if parsed_op.variables:
                vars_args = ', '.join([self.__render_variable_definition(var) for var in parsed_op.variables]) + ','
                variables_dict = '{' + ', '.join(f'"{var.name}": {var.name}' for var in parsed_op.variables) + '}'
            else:
                vars_args = ''
                variables_dict = 'None'

            buffer.write('@classmethod')
            with buffer.write_block(f'def execute(cls, {vars_args} on_before_callback: Callable[[Mapping[str, str], Mapping[str, str]], None] = None):'):
                buffer.write(f'client = Client(\'{self.config.schema}\')')
                buffer.write(f'variables = {variables_dict}')
                buffer.write('response_text = client.call(cls.__QUERY__, variables=variables, on_before_callback=on_before_callback)')
                buffer.write('return cls.from_json(response_text)')

            buffer.write('@classmethod')
            with buffer.write_block(f'async def execute_async(cls, {vars_args} on_before_callback: Callable[[Mapping[str, str], Mapping[str, str]], None] = None):'):
                buffer.write(f'client = AsyncClient(\'{self.config.schema}\')')
                buffer.write(f'variables = {variables_dict}')
                buffer.write(f'response_text = await client.call(cls.__QUERY__, variables=variables, on_before_callback=on_before_callback)')
                buffer.write(f'return cls.from_json(response_text)')

            buffer.write('')
            buffer.write('')

    @staticmethod
    def __render_variable_definition(var: ParsedVariableDefinition):
        if not var.nullable:
            return f'{var.name}: {var.type}'

        return f'{var.name}: {var.type} = {var.default_value or "None"}'

    @staticmethod
    def __render_field(parsed_query: ParsedQuery, buffer: CodeChunk, field: ParsedField):
        enum_names = [e.name for e in parsed_query.enums]
        is_enum = field.type in enum_names
        if is_enum:
            buffer.write(f'{field.name}: {field.type} = enum_field({field.type})')
            return

        if field.nullable:
            buffer.write(f'{field.name}: {field.type} = {field.default_value}')
        else:
            buffer.write(f'{field.name}: {field.type}')

    @staticmethod
    def __render_enum(buffer: CodeChunk, enum: ParsedEnum):
        with buffer.write_block(f'class {enum.name}(Enum):'):
            for value_name, value in enum.values.items():
                if isinstance(value, str):
                    value = f"'{value}'"

                buffer.write(f'{value_name} = {value}')

        buffer.write('')
