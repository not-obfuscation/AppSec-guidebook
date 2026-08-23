"""Загрузка проверяемого модуля: по умолчанию code.py.

Чтобы прогнать те же проверки против образцового решения:
    LAB_TARGET=solution.py python hack.py
"""

import importlib.util
import os
import pathlib


def load():
    name = os.environ.get("LAB_TARGET", "code.py")
    path = pathlib.Path(__file__).resolve().parent / name
    spec = importlib.util.spec_from_file_location("lab_target", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return name, module
