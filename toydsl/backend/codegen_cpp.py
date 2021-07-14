from __future__ import annotations

import toydsl.ir.ir as ir
from toydsl.ir.visitor import IRNodeVisitor

class CodeGenCpp(IRNodeVisitor):
    """
    The code-generation module that traverses the IR and generates code form it.
    """

    @classmethod
    def apply(cls: CodeGen, ir: ir.IR) -> str:
        """
        Entrypoint for the code generation, applying this to an IR returns a formatted function for that IR
        """
        codegen = cls()
        return codegen.visit(ir)

    @staticmethod
    def offset_to_string(offset: ir.AccessOffset) -> str:
        """
        Converts the offset of a FieldAccess to a string with the proper indexing
        """
        return (
            "(idx_i + "
            + str(offset.offsets[0])
            + ", idx_j + "
            + str(offset.offsets[1])
            + ", idx_k + "
            + str(offset.offsets[2])
            + ")"
        )

    @staticmethod
    def create_vertical_loop(vertical_domain: ir.VerticalDomain) -> str:
        start_idx = int(vertical_domain.extents.start.level)
        start_string = "k[{start_idx}]+{offset}".format(
            start_idx=start_idx, offset=vertical_domain.extents.start.offset
        )
        end_idx = int(vertical_domain.extents.end.level)
        end_string = "k[{end_idx}]+{offset}".format(
            end_idx=end_idx, offset=vertical_domain.extents.end.offset
        )
        return "for (std::size_t idx_k = {}; idx_k < {}; ++idx_k)".format(start_string, end_string)

    @staticmethod
    def create_horizontal_loop(
        loop_variable: str, horizontal_domain: ir.HorizontalDomain
    ) -> str:
        assert loop_variable in ["i", "j"]
        index = 0 if loop_variable == "i" else 1
        startidx = int(horizontal_domain.extents[index].start.level)
        start = "{loop_variable}[{startidx}]+{offset}".format(
            startidx=startidx,
            offset=horizontal_domain.extents[index].start.offset,
            loop_variable=loop_variable,
        )
        endidx = int(horizontal_domain.extents[index].end.level)
        end = "{loop_variable}[{endidx}]+{offset}".format(
            endidx=endidx,
            offset=horizontal_domain.extents[index].end.offset,
            loop_variable=loop_variable,
        )
        return "for (std::size_t {var} = {start}; {var} < {end}; ++{var})".format(
            start=start, end=end, var="idx_{}".format(loop_variable)
        )

    # ---- Visitor handlers ----
    def generic_visit(self, node: ir.Node, **kwargs) -> None:
        """
        Each visit needs to do something in code-generation, there can't be a default visit
        """
        raise RuntimeError("Invalid IR node: {}".format(node))

    def visit_LiteralExpr(self, node: ir.LiteralExpr) -> str:
        return node.value

    def visit_FieldAccessExpr(self, node: ir.FieldAccessExpr) -> str:
        return node.name + self.offset_to_string(node.offset)

    def visit_AssignmentStmt(self, node: ir.AssignmentStmt) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        return "{} = {};".format(left, right)

    def visit_BinaryOp(self, node: ir.BinaryOp) -> str:
        return self.visit(node.left) + node.operator + self.visit(node.right)

    def visit_VerticalDomain(self, node: ir.VerticalDomain) -> List[str]:
        vertical_loop = [self.create_vertical_loop(node)]
        vertical_loop.append("{")
        for stmt in node.body:
            lines_of_code = self.visit(stmt)
            for line in lines_of_code:
                vertical_loop.append(line)
        vertical_loop.append("}")

        return vertical_loop

    def visit_HorizontalDomain(self, node: ir.HorizontalDomain) -> List[str]:
        inner_loop = [self.create_horizontal_loop("j", node)]
        inner_loop.append("{")
        for stmt in node.body:
            inner_loop.append(self.visit(stmt))
        inner_loop.append("}")

        outer_loop = [self.create_horizontal_loop("i", node)]
        outer_loop.append("{")
        for line in inner_loop:
            outer_loop.append(line)
        outer_loop.append("}")

        return outer_loop

    @staticmethod
    def create_argument_list(args: List[str]) -> List:


    def visit_IR(self, node: ir.IR) -> str:
        args =

        scope = ["""
            using numpy_t = boost::python::numpy::ndarray;
            using bounds_t = std::array<std::size_t, 2>;
            void {name}({array_args}, {bounds}) {{
                {converters}
        """.format(
            name=node.name,
            array_args=", ".join(["numpy_t &{}_np".format(arg) for arg in node.api_signature]),
            bounds=", ".join(["bounds_t const& {}".format(axis) for axis in ["i", "j", "k"]])
        )]

        for stmt in node.body:
            scope.extend(self.visit(stmt))

        scope.append("}")

        return "\n".join(scope)
