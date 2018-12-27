from typing import Any, List, Mapping, Union, cast
from dataclasses import dataclass, field

from graphql import GraphQLSchema, validate, parse, get_operation_ast, visit, Visitor, TypeInfo, TypeInfoVisitor, \
    GraphQLNonNull, is_scalar_type, GraphQLList, OperationDefinitionNode, NonNullTypeNode, TypeNode, GraphQLEnumType, \
    is_enum_type


@dataclass
class ParsedField:
    name: str
    type: str
    nullable: bool
    default_value: Any = None


@dataclass
class ParsedObject:
    name: str
    fields: List[ParsedField] = field(default_factory=list)
    parents: List[str] = field(default_factory=list)
    children: List['ParsedObject'] = field(default_factory=list)


@dataclass
class ParsedEnum:
    name: str
    values: Mapping[str, Any]


@dataclass
class ParsedVariableDefinition:
    name: str
    type: str
    nullable: bool
    default_value: Any = None


@dataclass
class ParsedOperation:
    name: str
    type: str
    variables: List[ParsedVariableDefinition] = field(default_factory=list)
    children: List[ParsedObject] = field(default_factory=list)


NodeT = Union[ParsedOperation, ParsedObject]


@dataclass
class ParsedQuery:
    query: str
    objects: List[NodeT] = field(default_factory=list)
    enums: List[ParsedEnum] = field(default_factory=list)


class FieldToTypeMatcherVisitor(Visitor):

    def __init__(self, schema: GraphQLSchema, type_info: TypeInfo, query: str):
        self.schema = schema
        self.type_info = type_info
        self.query = query
        self.parsed = ParsedQuery(query=self.query)
        self.dfs_path: List[ParsedObject] = []

    def push(self, obj: NodeT):
        self.dfs_path.append(obj)

    def pull(self) -> NodeT:
        return self.dfs_path.pop()

    @property
    def current(self) -> ParsedObject:
        return self.dfs_path[-1]

    # Document
    def enter_operation_definition(self, node: OperationDefinitionNode, *_args):
        name, operation = node.name, node.operation

        variables = []
        for var in node.variable_definitions:
            ptype, nullable, _ = self.__variable_type_to_python(var.type)
            variables.append(ParsedVariableDefinition(
                name=var.variable.name.value,
                type=ptype,
                nullable=nullable,
                default_value=var.default_value.value if var.default_value else None,
            ))

        parsed_op = ParsedOperation(
            name=name.value,
            type=str(operation.value),
            variables=variables,
            children=[
                ParsedObject(name=f'{name.value}Data')
            ]
        )

        self.parsed.objects.append(parsed_op)  # pylint:disable=no-member
        self.push(parsed_op)
        self.push(parsed_op.children[0])  # pylint:disable=unsubscriptable-object

        return node

    # def enter_selection_set(self, node, *_):
    #     return node

    def leave_selection_set(self, node, *_):
        self.pull()
        return node

    # Fragments

    def enter_fragment_definition(self, node, *_):
        # Same as operation definition
        obj = ParsedObject(
            name=node.name.value
        )
        self.parsed.objects.append(obj)  # pylint:disable=no-member
        self.push(obj)
        return node

    def enter_fragment_spread(self, node, *_):
        self.current.parents.append(node.name.value)
        return node

    # def enter_inline_fragment(self, node, *_):
    #     return node
    #
    # def leave_inline_fragment(self, node, *_):
    #     return node

    # Field

    def enter_field(self, node, *_):
        name = node.alias.value if node.alias else node.name.value
        graphql_type = self.type_info.get_type()
        python_type, nullable, underlying_graphql_type = self.__scalar_type_to_python(graphql_type)

        parsed_field = ParsedField(
            name=name,
            type=python_type,
            nullable=nullable,
        )

        self.current.fields.append(parsed_field)  # TODO: nullables should go to the end

        if not is_scalar_type(underlying_graphql_type):
            if is_enum_type(underlying_graphql_type):
                enum_type = cast(GraphQLEnumType, self.schema.type_map[underlying_graphql_type.name])
                name = enum_type.name
                if not any(e.name == name for e in self.parsed.enums):  # pylint:disable=not-an-iterable
                    parsed_enum = ParsedEnum(
                        name=enum_type.name,
                        values={name: value.value or name for name, value in enum_type.values.items()}
                    )
                    self.parsed.enums.append(parsed_enum)  # pylint:disable=no-member
            else:
                obj = ParsedObject(
                    name=str(underlying_graphql_type)
                )

                self.current.children.append(obj)
                self.push(obj)

        return node

    @staticmethod
    def __scalar_type_to_python(scalar):
        nullable = True
        if isinstance(scalar, GraphQLNonNull):
            nullable = False
            scalar = scalar.of_type

        mapping = {
            'ID': 'str',
            'String': 'str',
            'Int': 'int',
            'Float': 'float',
            'Boolean': 'bool',
            'DateTime': 'DateTime'
        }

        if isinstance(scalar, GraphQLList):
            scalar = scalar.of_type
            mapping = f'List[{mapping.get(str(scalar), str(scalar))}]'
        else:
            mapping = mapping.get(str(scalar), str(scalar))

        return mapping, nullable, scalar

    @staticmethod
    def __variable_type_to_python(var_type: TypeNode):
        nullable = True
        if isinstance(var_type, NonNullTypeNode):
            nullable = False
            var_type = var_type.type

        mapping = {
            'ID': 'str',
            'String': 'str',
            'Int': 'int',
            'Float': 'float',
            'Boolean': 'bool',
            'DateTime': 'DateTime'
        }

        mapping = mapping.get(var_type.name.value, var_type.name.value)
        return mapping, nullable, var_type


class AnonymousQueryError(Exception):
    def __init__(self):
        super().__init__('All queries must be named')


class InvalidQueryError(Exception):
    def __init__(self, errors):
        self.errors = errors
        message = '\n'.join(str(err) for err in errors)
        super().__init__(message)


class QueryParser:
    def __init__(self, schema: GraphQLSchema):
        self.schema = schema
        self.__jinja2_env = None

    def parse(self, query: str, should_validate: bool = True) -> ParsedQuery:
        document_ast = parse(query)
        operation = get_operation_ast(document_ast)

        if not operation.name:
            raise AnonymousQueryError()

        if should_validate:
            errors = validate(self.schema, document_ast)
            if errors:
                raise InvalidQueryError(errors)

        type_info = TypeInfo(self.schema)
        visitor = FieldToTypeMatcherVisitor(self.schema, type_info, query)
        visit(document_ast, TypeInfoVisitor(type_info, visitor))
        result = visitor.parsed
        return result
