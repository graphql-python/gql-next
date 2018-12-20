from typing import List, AnyStr
from dataclasses import dataclass, field

from graphql import GraphQLSchema, validate, parse, get_operation_ast, visit, Visitor, TypeInfo, TypeInfoVisitor, GraphQLType
from graphql.language import ast


@dataclass
class MappingNode:
    query: str
    node: ast.Node
    name: str
    graphql_type: GraphQLType = None
    parent: 'MappingNode' = None
    children: List['MappingNode'] = field(default_factory=list)
    fragments: List[AnyStr] = field(default_factory=list)

    def __repr__(self):
        return f'{self.name} ({self.graphql_type})'

@dataclass
class ParsedQuery:
    query: str
    parsed: List[MappingNode]


class FieldToTypeMatcherVisitor(Visitor):

    def __init__(self, type_info: TypeInfo, query: str):
        self.type_info = type_info
        self.query = query
        self.root: List[MappingNode] = []
        self.current: MappingNode = None

    # Document
    def enter_operation_definition(self, node, *_args):
        name, operation = node.name, node.operation
        op_name = name.value
        name = f'{operation.value.capitalize()}{op_name}Response'

        operation_root = MappingNode(query=self.query, node=node, name=name)
        self.root.append(operation_root)
        self.current = operation_root
        return node

    def enter_selection_set(self, node, *_):
        self.current = self.current.children[-1] if self.current.children else self.current
        return node

    def leave_selection_set(self, node, *_):
        self.current = self.current.parent
        return node

    # Fragments

    def enter_fragment_definition(self, node, *_):
        # Same as operation definition
        fragment = MappingNode(query=self.query, node=node, name=node.name.value)
        self.root.append(fragment)
        self.current = fragment
        return node

    def enter_fragment_spread(self, node, *_):
        self.current.fragments.append(node.name.value)
        return node

    # def enter_inline_fragment(self, node, *_):
    #     return node

    def leave_inline_fragment(self, node, *_):
        self.current = self.current.children[-1] if self.current.children else self.current
        return node

    # Field

    def enter_field(self, node, *_):
        name = node.alias.value if node.alias else node.name.value
        type_ = self.type_info.get_type()
        new_node = MappingNode(query=self.query, node=node, name=name, graphql_type=type_, parent=self.current)
        # TODO: Nullable fields should go to the end
        self.current.children.append(new_node)
        return node

    def __find_node(self, node: ast.Node, current: MappingNode):
        if current.node == node:
            return current

        for child in current.children:
            result = self.__find_node(node, child)
            if result:
                return result

        return None


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
        visitor = FieldToTypeMatcherVisitor(type_info, query)
        visit(document_ast, TypeInfoVisitor(type_info, visitor))
        result = ParsedQuery(query=query, parsed=visitor.root)
        return result
