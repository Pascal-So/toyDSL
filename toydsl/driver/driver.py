import functools
import hashlib
import inspect
import os
import sys
import time
from pathlib import Path

from toydsl.backend.codegen import CodeGen, ModuleGen
from toydsl.backend.codegen_cpp import CodeGenCpp, format_cpp, compile_cpp, setup_code_dir_cpp
from toydsl.frontend.frontend import parse


def driver_cpp(function, hash: str, cache_dir: Path):
    """
    Driver for generating the c++ code, formatting it, compiling it, and loading the
    resulting shared object as a python module.
    """
    code_dir = cache_dir / "cpp_{}".format(hash)
    so_filename = code_dir / "build" / "dslgen.so"

    if True or not os.path.isfile(so_filename):
        # For now we just perform all the generation steps if the .so file
        # is missing. The case where some of the steps have already been
        # performed is rare and we wouldn't save much time anyway.

        start_time = time.perf_counter()

        setup_code_dir_cpp(code_dir)

        ir = parse(function)
        code = CodeGenCpp.apply(ir)
        cpp_filename = code_dir / "dslgen.cpp"

        with open(cpp_filename, "w") as f:
            f.write(code)

        format_cpp(cpp_filename)
        compile_cpp(code_dir)

        end_time = time.perf_counter()
        print("\n\nGenerated, formatted, and compiled C++ code in {:.2f} seconds.".format(end_time - start_time), file=sys.stderr)

    return ModuleGen.apply(ir.name, so_filename)

def driver_python(function, hash: str, cache_dir: Path):
    """
    Driver for generating a module from a parsable function while storing the python module
    in the given cache directory.
    """
    filename = cache_dir / "generated_{hash}.py".format(hash=hash),

    ir = parse(function)
    code = CodeGen.apply(ir)

    # print(CodeGenCpp.apply(ir))

    with open(filename, "w") as f:
        f.write(code)
    return ModuleGen.apply(ir.name, filename)


def set_up_cache_directory() -> str:
    """Searches the system for the CODE_CACHE_ROOT directory and sets it up if necessary"""
    cache_dir = os.getenv("CODE_CACHE_ROOT")
    if cache_dir is None:
        cache_dir = ".codecache"
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def hash_source_code(definition_func) -> str:
    """Hashes the source code of a function to get a unique ID for a target file"""
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(str.encode(repr(inspect.getsource(definition_func))))
    return hash_algorithm.hexdigest()[:10]


def computation(func):
    """Main entrypoint into the DSL.
    Decorating functions with this call will allow for calls to the generated code
    """

    @functools.wraps(func)
    def _decorator(definition_func):
        cache_dir = set_up_cache_directory()
        hash = hash_source_code(definition_func)
        stencil_call = driver_cpp(
            definition_func,
            hash,
            Path(cache_dir)
        )
        return stencil_call

    return _decorator(func)
