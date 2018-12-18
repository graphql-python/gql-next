from typing import List, AnyStr
from dataclasses import dataclass, field

from graphql import GraphQLSchema, parse, get_operation_ast, visit, Visitor, TypeInfo, TypeInfoVisitor, GraphQLType
from graphql.language import ast


@dataclass
class MappingNode:
    node: ast.Node
    name: str
    graphql_type: GraphQLType = None
    parent: 'MappingNode' = None
    children: List['MappingNode'] = field(default_factory=list)
    fragments: List[AnyStr] = field(default_factory=list)

    def __repr__(self):
        return f'{self.name} ({self.graphql_type})'


class FieldToTypeMatcherVisitor(Visitor):

    def __init__(self, type_info: TypeInfo):
        self.type_info = type_info
        self.root: List[MappingNode] = []
        self.current: MappingNode = None

    # Document
    def enter_operation_definition(self, node, *_args):
        name, op, selection_set = node.name, node.operation, node.selection_set
        op_name = name.value
        name = f'{op.value.capitalize()}{op_name}Response'

        operation_root = MappingNode(node=node, name=name)
        self.root.append(operation_root)
        self.current = operation_root
        return node

    def enter_selection_set(self, node, key, parent, path, ancestors):
        self.current = self.current.children[-1] if self.current.children else self.current
        return node

    def leave_selection_set(self, node, key, parent, path, ancestors):
        self.current = self.current.parent
        return node

    # Fragments

    def enter_fragment_definition(self, node, *_args):
        # Same as operation definition
        fragment = MappingNode(node=node, name=node.name.value)
        self.root.append(fragment)
        self.current = fragment
        return node

    def enter_fragment_spread(self, node, key, parent, path, ancestors):
        self.current.fragments.append(node.name.value)
        return node

    def enter_inline_fragment(self, node, key, parent, path, ancestors):
        return node

    def leave_inline_fragment(self, node, key, parent, path, ancestors):
        self.current = self.current.children[-1] if self.current.children else self.current
        return node

    # Field

    def enter_field(self, node, key, parent, path, ancestors):
        name = node.alias.value if node.alias else node.name.value
        type_ = self.type_info.get_type()
        new_node = MappingNode(node=node, name=name, graphql_type=type_, parent=self.current)
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


class QueryParser:
    def __init__(self, schema: GraphQLSchema):
        self.schema = schema
        self.__jinja2_env = None

    def parse(self, query: str) -> MappingNode:
        document_ast = parse(query)
        operation = get_operation_ast(document_ast)

        if not operation.name.value:
            raise Exception('All queries must be named')

        type_info = TypeInfo(self.schema)

        visitor = FieldToTypeMatcherVisitor(type_info)
        visit(document_ast, TypeInfoVisitor(type_info, visitor), )
        return visitor.root
