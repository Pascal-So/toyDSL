import functools
import hashlib
import inspect
import os

from toydsl.backend.codegencpp import CodeGen, ModuleGen
from toydsl.frontend.frontend import parse


def driver(function, filename):
    """
    Driver for generating a module from a parsable function while storing the python module in a given file
    """
    ir = parse(function)
    code = CodeGen.apply(ir)
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
        stencil_call = driver(
            definition_func,
            "{cache_dir}/generated_{hash}.cpp".format(hash=hash, cache_dir=cache_dir),
        )
        return stencil_call

    return _decorator(func)
