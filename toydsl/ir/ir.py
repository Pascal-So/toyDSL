from __future__ import annotations

import enum
from typing import List


@enum.unique
class LevelMarker(enum.Enum):
    START = 0
    END = -1

    def __str__(self):
        return self.name


class Node:
    pass


class Offset:
    def __init__(self, level=LevelMarker.START, offset=0):
        self.level = level
        self.offset = offset


class AxisInterval:
    def __init__(self, start=Offset(), end=Offset()):
        self.start = start
        self.end = end


class HorizontalDomain(Node):
    def __init__(self, extents=[AxisInterval(), AxisInterval()]):
        self.body = []
        self.extents = extents


class VerticalDomain(Node):
    def __init__(self, extents=AxisInterval()):
        self.body = []
        self.extents = extents


class AccessOffset:
    offsets: List[int]

    def __init__(self, i, j, k):
        self.offsets = []
        self.offsets.append(i)
        self.offsets.append(j)
        self.offsets.append(k)

    def __str__(self):
        return (
            "["
            + str(self.offsets[0])
            + ","
            + str(self.offsets[1])
            + ","
            + str(self.offsets[2])
            + "]"
        )


@enum.unique
class DataType(enum.IntEnum):
    """Data type identifier."""

    # IDs from gt4py
    INVALID = -1
    AUTO = 0
    DEFAULT = 1
    BOOL = 10
    INT8 = 11
    INT16 = 12
    INT32 = 14
    INT64 = 18
    FLOAT32 = 104
    FLOAT64 = 108


class Expr(Node):
    pass


class Stmt(Node):
    pass


class LiteralExpr(Expr):
    value: str
    dtype: DataType

    def __init__(self, value: str, dtype=DataType.FLOAT64):
        self.value = value
        self.dtype = dtype


class FieldAccessExpr(Expr):
    name: str
    offset: AccessOffset

    def __init__(self, name, offset):
        self.name = name
        self.offset = offset


class AssignmentStmt(Stmt):
    left: Expr
    right: Expr


class IfStmt(Stmt):
    condition: Expr
    true_body: List[Stmt]
    false_body: List[Stmt]


class BinaryOp(Expr):
    left: Expr
    right: Expr
    operator: str


class FieldDecl(Stmt):
    pass


class IR(Node):
    def __init__(self):
        self.name = ""
        self.body = []
        self.api_signature = []
