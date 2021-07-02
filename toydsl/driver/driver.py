import functools
import hashlib
import inspect
import os

from toydsl.backend.codegen import CodeGen, ModuleGen
from toydsl.frontend.frontend import parse


def driver(function, filename):
    ir = parse(function)
    code = CodeGen.apply(ir)
    with open(filename, "w") as f:
        f.write(code)
    return ModuleGen.apply(ir.name, filename)


def computation(func):
    @functools.wraps(func)
    def _decorator(definition_func):
        # Get environment variables
        cache_dir = os.getenv("CODE_CACHE_ROOT")
        if cache_dir is None:
            cache_dir = ".codecache"
        os.makedirs(cache_dir, exist_ok=True)
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(str.encode(repr(inspect.getsource(definition_func))))
        result = hash_algorithm.hexdigest()[:10]
        stencil_call = driver(
            definition_func,
            "{cache_dir}/generated_{filename}.py".format(filename=result, cache_dir=cache_dir),
        )
        return stencil_call

    return _decorator(func)
