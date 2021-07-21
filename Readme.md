# Toy DSL for weather and climate models

Requirements:

* cmake >= 3.14
* make
* python >= 3.6
* boost 1.76
* clang-format (optional)

## Building / Running

Disclaimer: the following instructions work on my machine where `wheel` is not installed, a different setup might be required if your pip doesn't fall back to the legacy `setup.py install`.

```bash
cd /path/to/toyDSL

python -m venv venv
. venv/bin/activate
pip install numpy black
pip install .

PYTHONPATH=$PYTHONPATH:$PWD python example/basic_function.py
```
