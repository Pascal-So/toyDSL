from __future__ import annotations

import toydsl.ir.ir as ir
import subprocess
import shutil
import os
from pathlib import Path
from toydsl.ir.visitor import IRNodeVisitor
import importlib.util

def load_cpp_module(so_filename: Path):
    """
    Load the python module from the .so file.

    https://stackoverflow.com/a/67692
    """

    spec = importlib.util.spec_from_file_location("dslgen", so_filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def format_cpp(cpp_filename: Path):
    """
    Format the generated C++ source code to make it prettier to look at.

    This doesn't change anything about the generated module, but it's
    useful to have readable code when debugging the code generator.
    """

    clang_format_installed = shutil.which("clang-format") is not None
    if clang_format_installed:
        subprocess.call(["clang-format", "-i", cpp_filename])

def compile_cpp(code_dir: Path, build_type: str = "Release"):
    """
    Compile the generated C++ code using CMake.
    """

    build_dir = code_dir / "build"
    os.makedirs(build_dir, exist_ok=True)

    ret = subprocess.call(["cmake", "..", "-DCMAKE_BUILD_TYPE={}".format(build_type)], cwd=build_dir)
    if ret != 0:
        raise Exception("CMake failed. build directory: {dir}. return code: {ret}. build type: {build_type}".format(dir=build_dir, ret=ret, build_type=build_type))

    ret = subprocess.call(["make", "-j", "VERBOSE=1"], cwd=build_dir)
    if ret != 0:
        raise Exception("make failed. build directory: {dir}. return code: {ret}".format(dir=build_dir, ret=ret))

def setup_code_dir_cpp(code_dir: Path):
    """
    Create the directory where the generated C++ code should end up
    and populate it with the required files.

    The required files are copied from the `cpp` directory adjacent to
    this `backend` directory.
    """
    global dir_name
    dir_name = str(code_dir).split("/")[1]
    os.makedirs(code_dir, exist_ok=True)

    backend_dir = Path(__file__).parent
    cpp_dir = backend_dir.parent / "cpp"
    shutil.copyfile(cpp_dir / "CMakeLists.txt", code_dir / "CMakeLists.txt")
    shutil.copyfile(cpp_dir / ".clang-format", code_dir / ".clang-format")


def offset_to_string(offset: ir.AccessOffset) -> str:
    """
    Converts the offset of a FieldAccess to a string with the proper indexing
    """
    return (
        "[(idx_i + "
        + str(offset.offsets[0])
        + ") + (idx_j + "
        + str(offset.offsets[1])
        + ")*dim2 + (idx_k + "
        + str(offset.offsets[2])
        + ")*dim3]"
    )

def create_loop(loop_variable: str, extents: ir.AxisInterval) -> str:
    assert loop_variable in ["i", "j", "k"]

    def create_offset(offset: ir.Offset):
        side = "start" if offset.level == ir.LevelMarker.START else "end"
        return "{}_{} + {}".format(side, loop_variable, offset.offset)

    return "for (std::size_t {var} = {start}; {var} < {end}; ++{var})".format(
        start=create_offset(extents.start),
        end=create_offset(extents.end),
        var="idx_{}".format(loop_variable)
    )

def create_vertical_loop(vertical_domain: ir.VerticalDomain) -> str:
    return create_loop("k", vertical_domain.extents)

def create_horizontal_loop(
    loop_variable: str, horizontal_domain: ir.HorizontalDomain
) -> str:
    assert loop_variable in ["i", "j"]

    index = 0 if loop_variable == "i" else 1
    extents = horizontal_domain.extents[index]

    return create_loop(loop_variable, extents)

def generate_converter(arg_name: str):
    return "auto {a} = reinterpret_cast<scalar_t*>({a}_np.get_data());".format(a=arg_name)

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

    # ---- Visitor handlers ----
    def generic_visit(self, node: ir.Node, **kwargs) -> None:
        """
        Each visit needs to do something in code-generation, there can't be a default visit
        """
        raise RuntimeError("Invalid IR node: {}".format(node))

    def visit_LiteralExpr(self, node: ir.LiteralExpr) -> str:
        return node.value

    def visit_FieldAccessExpr(self, node: ir.FieldAccessExpr) -> str:
        return node.name + offset_to_string(node.offset)

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
        vertical_loop = [create_vertical_loop(node)]
        vertical_loop.append("{")
        for stmt in node.body:
            lines_of_code = self.visit(stmt)
            for line in lines_of_code:
                vertical_loop.append(line)
        vertical_loop.append("}")

        return vertical_loop

    def visit_HorizontalDomain(self, node: ir.HorizontalDomain) -> List[str]:
        inner_loop = [create_horizontal_loop("j", node)]
        inner_loop.append("{")
        for stmt in node.body:
            inner_loop.append(self.visit(stmt))
        inner_loop.append("}")

        outer_loop = [create_horizontal_loop("i", node)]
        outer_loop.append("{")
        for line in inner_loop:
            outer_loop.append(line)
        outer_loop.append("}")

        return outer_loop

    def visit_IR(self, node: ir.IR) -> str:
        scope = ["""#include <boost/python.hpp>
            #include <boost/python/numpy.hpp>

            #include "../../include/tsc_x86.h"

            namespace np = boost::python::numpy;

            using scalar_t = double;
            using numpy_t = np::ndarray;
            using bounds_t = boost::python::list;

            std::int64_t {name}({array_args}, {bounds}) {{
                const auto start_cycle = start_tsc();

                const std::size_t num_runs = 1000;
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

                return stop_tsc(start_cycle);
            }}

            BOOST_PYTHON_MODULE(dslgen) {{
                Py_Initialize();
                np::initialize();
                boost::python::def("{name}", {name});
            }}
        """.format(name=node.name))

        return "\n".join(scope)
