"""Finds the methods, constructors and fields of a Java file, including their line range.

Methods are identified by their signature (name + parameter types), so
overloaded methods stay distinguishable. Fields are identified by their name,
e.g. "LEIHFRIST_TAGE". Members of inner classes get the inner class as prefix
("Entry.getKey()"). Uses tree-sitter, which also copes with files that do not
fully compile.
"""

import tree_sitter_java
from tree_sitter import Language, Node, Parser

from app.models import JavaField, JavaMethod

_parser = Parser(Language(tree_sitter_java.language()))

METHOD_NODE_TYPES = ("method_declaration", "constructor_declaration")
TYPE_NODE_TYPES = ("class_declaration", "interface_declaration", "enum_declaration", "record_declaration")


def parse_members(source: str) -> tuple[list[JavaMethod], list[JavaField]]:
    tree = _parser.parse(source.encode("utf-8"))
    methods: list[JavaMethod] = []
    fields: list[JavaField] = []
    collect_members(tree.root_node, methods, fields, type_names=[])
    return methods, fields


def parse_methods(source: str) -> list[JavaMethod]:
    return parse_members(source)[0]


def collect_members(node: Node, methods: list[JavaMethod], fields: list[JavaField], type_names: list[str]) -> None:
    prefix = "".join(f"{inner}." for inner in type_names[1:])

    if node.type in METHOD_NODE_TYPES:
        name = node.child_by_field_name("name").text.decode()
        parameter_types = read_parameter_types(node.child_by_field_name("parameters"))
        methods.append(
            JavaMethod(
                name=name,
                signature=f"{prefix}{name}({', '.join(parameter_types)})",
                is_constructor=node.type == "constructor_declaration",
                # tree-sitter counts from 0, editors count from 1
                start_line=node.start_point.row + 1,
                end_line=node.end_point.row + 1,
            )
        )
        # Methods of anonymous classes inside this method are not listed separately.
        return

    if node.type == "field_declaration":
        # "int a = 1, b = 2;" declares two names in one line, they are kept together.
        names = [
            child.child_by_field_name("name").text.decode()
            for child in node.named_children
            if child.type == "variable_declarator"
        ]
        fields.append(
            JavaField(
                name=prefix + ", ".join(names),
                declaration=node.text.decode(),
                start_line=node.start_point.row + 1,
                end_line=node.end_point.row + 1,
            )
        )
        return

    if node.type == "object_creation_expression":
        return  # anonymous class in an initializer, see above

    if node.type in TYPE_NODE_TYPES:
        type_names = type_names + [node.child_by_field_name("name").text.decode()]

    for child in node.named_children:
        collect_members(child, methods, fields, type_names)


def read_parameter_types(parameters: Node) -> list[str]:
    types = []
    for parameter in parameters.named_children:
        if parameter.type == "formal_parameter":
            types.append(parameter.child_by_field_name("type").text.decode())
        elif parameter.type == "spread_parameter":  # varargs, e.g. "String... names"
            type_node = next(child for child in parameter.named_children if child.type != "modifiers")
            types.append(type_node.text.decode() + "...")
    return types
