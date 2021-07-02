from toydsl.ir.ir import Node


class IRNodeVisitor:
    def visit(self, node: Node, **kwargs):
        return self._visit(node, **kwargs)

    def _visit(self, node: Node, **kwargs):
        visitor = self.generic_visit
        if isinstance(node, Node):
            for node_class in node.__class__.__mro__:
                method_name = "visit_" + node_class.__name__
                if hasattr(self, method_name):
                    visitor = getattr(self, method_name)
                    break

        return visitor(node, **kwargs)
