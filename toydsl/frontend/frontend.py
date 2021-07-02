import ast
import inspect
import textwrap
import types
from typing import Any

import toydsl.ir.ir as ir
from toydsl.ir.ir import IR, AxisInterval, HorizontalDomain, LevelMarker, Offset, VerticalDomain


class IndexGen(ast.NodeVisitor):
    def __init__(self) -> None:
        self.offset = None
        self.sign = None

    @classmethod
    def apply(cls, node):
        foo = cls()
        intervals = []
        if isinstance(node, ast.Slice):
            intervals.append(foo.visit(node))
        else:
            for dim in node.dims:
                intervals.append(foo.visit(dim))
        return intervals

    def visit_Slice(self, node: ast.Slice) -> Any:
        self.offset = Offset()
        self.visit(node.lower)
        lower = self.offset
        self.offset = Offset()
        self.visit(node.upper)
        upper = self.offset
        return AxisInterval(lower, upper)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id == "end":
            self.offset.level = LevelMarker.END
        else:
            self.offset.level = LevelMarker.START

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        if isinstance(node.op, ast.Add):
            self.sign = 1
        else:
            self.sign = -1
        self.visit(node.left)
        self.visit(node.right)

    def visit_Constant(self, node: ast.Constant) -> Any:
        self.offset.offset += self.sign * node.value


class ArgumentParser(ast.NodeVisitor):
    @classmethod
    def apply(cls, node):
        parser = cls()
        return parser.visit(node)

    def visit_arg(self, node: ast.arg) -> Any:
        # TODO: check the type_comment?
        return node.arg


class LanguageParser(ast.NodeVisitor):
    def __init__(self):
        self._IR = IR()
        self._scope = self._IR
        self._parent = [None]

    def visit_Constant(self, node: ast.Constant):
        return ir.LiteralExpr(value=str(node.value))

    def visit_Name(self, node: ast.Name) -> Any:
        symbol = node.id
        return ir.FieldAccessExpr(name=symbol, offset=ir.AccessOffset(0, 0, 0))

    def visit_Subscript(self, node: ast.Subscript) -> Any:
        offset = ir.AccessOffset(
            node.slice.value.elts[0].value,
            node.slice.value.elts[1].value,
            node.slice.value.elts[2].value,
        )
        return ir.FieldAccessExpr(name=node.value.id, offset=offset)

    def visit_Assign(self, node: ast.Assign) -> Any:
        assert len(node.targets) == 1
        lhs = self.visit(node.targets[0])
        rhs = self.visit(node.value)
        assign = ir.AssignmentStmt()
        assign.left = lhs
        assign.right = rhs
        self._scope.body.append(assign)
        pass

    def visit_With(self, node: ast.With) -> Any:
        if isinstance(node.items[0].context_expr, ast.Subscript):
            if node.items[0].context_expr.value.id == "Vertical":
                self._parent.append(self._scope)
                index = IndexGen.apply(node.items[0].context_expr.slice)
                self._scope.body.append(VerticalDomain())
                self._scope.body[-1].extents = index[-1]
                self._scope = self._scope.body[-1]
                for stmt in node.body:
                    self.visit(stmt)
                self._scope = self._parent.pop()
            elif node.items[0].context_expr.value.id == "Horizontal":
                index = IndexGen.apply(node.items[0].context_expr.slice)
                self._parent.append(self._scope)
                self._scope.body.append(HorizontalDomain(index))
                self._scope = self._scope.body[-1]
                for stmt in node.body:
                    self.visit(stmt)
                self._scope = self._parent.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self._IR.name = node.name
        for arg in node.args.args:
            self._IR.api_signature.append(ArgumentParser.apply(arg))
        for element in node.body:
            self.visit(element)


def parse(function):
    p = LanguageParser()
    source = inspect.getsource(function)
    funcAST = ast.parse(source)
    p.visit(funcAST)
    return p._IR
