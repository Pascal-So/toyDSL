from __future__ import annotations

import importlib
import sys
from typing import List

import black

import toydsl.ir.ir as ir
from toydsl.ir.visitor import IRNodeVisitor


class TextBlock:
    def __init__(
        self,
        *,
        indent_level: int = 0,
        indent_size: int = 4,
        indent_char: str = " ",
        end_line: str = "\n",
    ) -> None:
        self.indent_level = indent_level
        self.indent_size = indent_size
        self.indent_char = indent_char
        self.end_line = end_line
        self.lines: List[str] = []

    def append(self, new_line):
        self.lines.append(self.indent_str + new_line)

    @property
    def indent_str(self) -> str:
        return self.indent_char * (self.indent_level * self.indent_size)

    def indent(self, steps: int = 1) -> TextBlock:
        self.indent_level += steps
        return self


class CodeGen(IRNodeVisitor):
    """
    The code-generation module that traverses the IR and generates code form it
    """

    @classmethod
    def apply(cls: CodeGen, ir: ir.IR) -> str:
        """
        entrypoint for the code generation
        """
        codegen = cls()
        return codegen.visit(ir)

    @staticmethod
    def offset_to_string(offset):
        """
        Converts the offset of a FieldAccess to a string with the proper indexing
        """
        return (
            "[idx_i + "
            + str(offset.offsets[0])
            + ",idx_j + "
            + str(offset.offsets[1])
            + ",idx_k + "
            + str(offset.offsets[2])
            + "]"
        )

    # ---- Visitor handlers ----
    def generic_visit(self, node: ir.Node, **kwargs):
        raise RuntimeError("Invalid IR node: {}".format(node))

    def visit_LiteralExpr(self, node: ir.LiteralExpr):
        return node.value

    def visit_FieldAccessExpr(self, node: ir.FieldAccessExpr):
        return node.name + self.offset_to_string(node.offset)

    def visit_AssignmentStmt(self, node: ir.AssignmentStmt):
        return self.visit(node.left) + "=" + self.visit(node.right)

    def visit_BinaryOp(self, node: ir.BinaryOp):
        return self.visit(node.left) + node.operator + self.visit(node.right)

    def visit_VerticalDomain(self, node: ir.VerticalDomain):
        body_sources = TextBlock()
        startidx = 0 if node.extents.start.level == ir.LevelMarker.START else -1
        start = "k[{startidx}]+{offset}".format(
            startidx=startidx, offset=node.extents.start.offset
        )
        endidx = 0 if node.extents.end.level == ir.LevelMarker.START else -1
        end = "k[{endidx}]+{offset}".format(endidx=endidx, offset=node.extents.end.offset)
        body_sources.append("for idx_k in range({condition}):".format(condition=start + "," + end))
        body_sources.indent()
        for stmt in node.body:
            lines_of_code = self.visit(stmt)
            for line in lines_of_code:
                body_sources.append(line)

        return body_sources.lines

    def visit_HorizontalDomain(self, node: ir.HorizontalDomain):
        outer_loop = TextBlock()
        startidx = 0 if node.extents[0].start.level == ir.LevelMarker.START else -1
        start = "i[{startidx}]+{offset}".format(
            startidx=startidx, offset=node.extents[0].start.offset
        )
        endidx = 0 if node.extents[0].end.level == ir.LevelMarker.START else -1
        end = "i[{endidx}]+{offset}".format(endidx=endidx, offset=node.extents[0].end.offset)
        outer_loop.append("for idx_i in range({condition}):".format(condition=start + "," + end))
        outer_loop.indent()

        inner_loop = TextBlock()
        startidx = 0 if node.extents[1].start.level == ir.LevelMarker.START else -1
        start = "j[{startidx}]+{offset}".format(
            startidx=startidx, offset=node.extents[1].start.offset
        )
        endidx = 0 if node.extents[1].end.level == ir.LevelMarker.START else -1
        end = "j[{endidx}]+{offset}".format(endidx=endidx, offset=node.extents[1].end.offset)
        inner_loop.append("for idx_j in range({condition}):".format(condition=start + "," + end))
        inner_loop.indent()
        for stmt in node.body:
            inner_loop.append(self.visit(stmt))

        for line in inner_loop.lines:
            outer_loop.append(line)

        return outer_loop.lines

    def visit_IR(self, node: ir.IR):
        scope = TextBlock()
        function_def = "def {name}({args},i,j,k):".format(
            name=node.name, args=", ".join(node.api_signature)
        )
        scope.append(function_def)
        scope.indent()

        for stmt in node.body:
            vertical_regions = self.visit(stmt)
            for line in vertical_regions:
                scope.append(line)
        final = "\n".join(scope.lines)
        black_mode = black.FileMode(
            target_versions={black.TargetVersion.PY36, black.TargetVersion.PY37},
            line_length=100,
            string_normalization=True,
        )
        formatted_source = black.format_str(final, mode=black_mode)
        return formatted_source


class ModuleGen:
    def __init__(self):
        pass

    @classmethod
    def apply(cls, qualified_name, file_path):
        module_gen = cls()
        return module_gen.make_function_from_file(qualified_name, file_path)

    def make_function_from_file(self, qualified_name, file_path):
        module = self.make_module_from_file(qualified_name, file_path)
        return getattr(module, qualified_name)

    def make_module_from_file(self, qualified_name, file_path, *, public_import=False):
        """Import module from file.

        References:
        https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
        https://stackoverflow.com/a/43602645

        """
        try:
            spec = importlib.util.spec_from_file_location(qualified_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if public_import:
                sys.modules[qualified_name] = module
                package_name = getattr(module, "__package__", "")
                if not package_name:
                    package_name = ".".join(qualified_name.split(".")[:-1])
                    setattr(module, "__package__", package_name)
                components = package_name.split(".")
                module_name = qualified_name.split(".")[-1]

                if components[0] in sys.modules:
                    parent = sys.modules[components[0]]
                    for i, current in enumerate(components[1:]):
                        parent = getattr(parent, current, None)
                        if not parent:
                            break
                    else:
                        setattr(parent, module_name, module)

        except Exception as e:
            print(e)
            module = None

        return module
