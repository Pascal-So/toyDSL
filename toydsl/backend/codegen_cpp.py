from __future__ import annotations
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, List

import toydsl.ir.ir as ir
from toydsl.ir.visitor import IRNodeVisitor

def load_cpp_module(so_filename: Path):
    """
    Load the python module from the .so file.

    https://stackoverflow.com/a/67692
    """

    spec = importlib.util.spec_from_file_location("dslgen", so_filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def format_cpp(cpp_filename: Path, cmake_dir: Path):
    """
    Format the generated C++ source code to make it prettier to look at.

    This doesn't change anything about the generated module, but it's
    useful to have readable code when debugging the code generator.
    """

    clang_format_installed = shutil.which("clang-format") is not None
    if clang_format_installed:
        subprocess.call([
            "clang-format",
            "-i",
            cpp_filename.resolve()
        ], cwd=cmake_dir)

def compile_cpp(code_dir: Path, cmake_dir: Path, build_type: str = "Release"):
    """
    Compile the generated C++ code using CMake.
    """

    build_dir = code_dir / "build"
    os.makedirs(build_dir, exist_ok=True)

    ret = subprocess.call([
        "cmake",
        cmake_dir.resolve(),
        "-DCMAKE_BUILD_TYPE={}".format(build_type),
        "-DSOURCE_DIR={}".format(code_dir.resolve()),
        "-B{}".format(build_dir.resolve())
    ], cwd=build_dir)
    if ret != 0:
        raise Exception("CMake failed. build directory: {dir}. return code: {ret}. build type: {build_type}".format(dir=build_dir, ret=ret, build_type=build_type))

    ret = subprocess.call(["make", "-j", "VERBOSE=1"], cwd=build_dir)
    if ret != 0:
        raise Exception("make failed. build directory: {dir}. return code: {ret}".format(dir=build_dir, ret=ret))

def offset_to_string(offset: ir.AccessOffset, unroll_offset: int = 0) -> str:
    """
    Converts the offset of a FieldAccess to a 1-dimensional array access with the proper indexing
    """
    return "[(idx_i + {i}) + (idx_j + {j})*dim2 + (idx_k + {k})*dim3 + {unroll_offset}]".format(
        i=offset.offsets[0],
        j=offset.offsets[1],
        k=offset.offsets[2],
        unroll_offset=unroll_offset
    )

def create_loop_header(loop_variable: str, extents: List[str], stride: int = 1) -> str:
    assert loop_variable in ["i", "j", "k"]

    return "for (std::size_t {var} = {start}; {var} <= {end} - {stride}; {var} += {stride})".format(
        start=extents[0],
        end=extents[1],
        var="idx_{}".format(loop_variable),
        stride=stride
    )

def create_extents(extents: ir.AxisInterval, loop_variable: str) -> List[str]:
    def create_offset(offset: ir.Offset):
        side = "start" if offset.level == ir.LevelMarker.START else "end"
        return "{}_{} + {}".format(side, loop_variable, offset.offset)

    return [
        create_offset(extents.start),
        create_offset(extents.end)
    ]

def generate_converter(arg_name: str):
    return "auto {a} = reinterpret_cast<scalar_t*>({a}_np.get_data());".format(a=arg_name)

class CodeGenCpp(IRNodeVisitor):
    """
    The code-generation module that traverses the IR and generates code form it.
    """
    def __init__(self):
        # The private variables here are properties that count for certain subtrees of the AST.
        # Any visitor can modify them to influence all the visitors in the subtree below
        # itself, but note that the setter of the variable is responsible to return it to
        # its previous value when the subtree has been processed.

        self._repetitions = 1 # how many times should statements be executed
        self._unroll_offset = 0 # indexes the repeated statements in an unrolled loop

    @classmethod
    def apply(cls: CodeGenCpp, ir: ir.IR) -> str:
        """
        Entrypoint for the code generation, applying this to an IR returns a formatted function for that IR
        """
        codegen = cls()
        return codegen.visit(ir)

    # ---- Visitor handlers ----
    def generic_visit(self, node: Any, **kwargs) -> None:
        """
        Each visit needs to do something in code-generation, there can't be a default visit
        """
        raise RuntimeError("Invalid IR node: {}".format(node))

    def visit_LiteralExpr(self, node: ir.LiteralExpr) -> str:
        return node.value

    def visit_FieldAccessExpr(self, node: ir.FieldAccessExpr) -> str:
        return node.name + offset_to_string(node.offset, self._unroll_offset)

    def visit_AssignmentStmt(self, node: ir.AssignmentStmt) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        return "{} = {};".format(left, right)

    def visit_BinaryOp(self, node: ir.BinaryOp) -> str: # TODO : Do not strip out the brackets
        assert(node.operator),"Unknown operator"
        # Keep the commented lines bellow, it might be useful later
        # if node.operator == "+":
        #     op_string = "+"
        # elif node.operator == "-":
        #     op_string = "-"
        # elif node.operator == "*":
        #     op_string = "*"
        # elif node.operator == "/":
        #     op_string = "/"
        # elif node.operator == "**":
        #     op_string = "**"
        # elif node.operator == "%":
        #     op_string = "%"
        # else:
        #     assert(False),"Operator has been defined in frontend.py only"
        if node.operator == "**":
            binaryOp_str = "pow("+self.visit(node.left) + "," + self.visit(node.right) + ")"
        else:
            binaryOp_str = self.visit(node.left) + node.operator + self.visit(node.right)
        return binaryOp_str

    def visit_VerticalDomain(self, node: ir.VerticalDomain) -> List[str]:
        vertical_loop = [create_loop_header("k", create_extents(node.extents, "k"))]
        vertical_loop.append("{")
        for stmt in node.body:
            lines_of_code = self.visit(stmt)
            for line in lines_of_code:
                vertical_loop.append(line)
        vertical_loop.append("}")

        return vertical_loop

    def visit_HorizontalDomain(self, node: ir.HorizontalDomain) -> List[str]:
        unroll_factor = 4

        inner_extents = create_extents(node.extents[0], "i")
        inner_loop = []

        self._repetitions *= unroll_factor
        inner_loop.append(create_loop_header("i", inner_extents, self._repetitions))
        inner_loop.append("{")
        inner_loop.extend(self.visit(node.body))
        inner_loop.append("}")
        self._repetitions //= unroll_factor

        if unroll_factor > 1:
            inner_extents[0] = "{e} - ({e} - ({s})) % {r}".format(
                s=inner_extents[0],
                e=inner_extents[1],
                r=unroll_factor
            )

            inner_loop.append(create_loop_header("i", inner_extents, self._repetitions))
            inner_loop.append("{")
            inner_loop.extend(self.visit(node.body))
            inner_loop.append("}")

        outer_loop = [create_loop_header("j", create_extents(node.extents[1], "j"))]
        outer_loop.append("{")
        for line in inner_loop:
            outer_loop.append(line)
        outer_loop.append("}")

        return outer_loop

    def visit_list_of_Stmt(self, nodes: List[ir.Stmt]) -> List[str]:
        res = []

        previous_unroll_offset = self._unroll_offset
        reps = self._repetitions
        self._repetitions = 1

        for i in range(reps):
            self._unroll_offset = i
            for stmt in nodes:
                res.append(self.visit(stmt))

        self._repetitions = reps
        self._unroll_offset = previous_unroll_offset

        return res

    def visit_IR(self, node: ir.IR) -> str:
        scope = ["""#include <boost/python.hpp>
            #include <boost/python/numpy.hpp>
            #include <tsc_x86.h>

            namespace np = boost::python::numpy;

            using scalar_t = double;
            using numpy_t = np::ndarray;
            using bounds_t = boost::python::list;

            double {name}({array_args}, {bounds}) {{
                const std::size_t num_runs = 1000;

                const auto start_cycle = start_tsc();

                for (std::size_t ii = 0; ii < num_runs; ii++){{
                    {converters}

                    const std::size_t start_i = boost::python::extract<std::size_t>(i[0]);
                    const std::size_t end_i = boost::python::extract<std::size_t>(i[1]);
                    const std::size_t start_j = boost::python::extract<std::size_t>(j[0]);
                    const std::size_t end_j = boost::python::extract<std::size_t>(j[1]);
                    const std::size_t start_k = boost::python::extract<std::size_t>(k[0]);
                    const std::size_t end_k = boost::python::extract<std::size_t>(k[1]);

                    const std::size_t dim2 = (end_i - start_i);
                    const std::size_t dim3 = dim2 * (end_j - start_j);
        """.format(
            name=node.name,
            array_args=", ".join(["numpy_t &{}_np".format(arg) for arg in node.api_signature]),
            bounds=", ".join(["const bounds_t &{}".format(axis) for axis in ["i", "j", "k"]]),
            converters="\n".join(map(generate_converter, node.api_signature))
        )]

        for stmt in node.body:
            scope.extend(self.visit(stmt))

        scope.append("""
                }}

                return (double) stop_tsc(start_cycle)/num_runs;
            }}

            BOOST_PYTHON_MODULE(dslgen) {{
                Py_Initialize();
                np::initialize();
                boost::python::def("{name}", {name});
            }}
        """.format(name=node.name))

        return "\n".join(scope)
