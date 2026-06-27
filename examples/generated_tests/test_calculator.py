import importlib.util
import sys
from pathlib import Path

TARGET_FILE = Path('D:\\TestFlow\\examples\\calculator.py')


def _load_target_module():
    spec = importlib.util.spec_from_file_location('calculator', TARGET_FILE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def test_add_is_callable():
    module = _load_target_module()
    assert callable(module.add)

def test_divide_is_callable():
    module = _load_target_module()
    assert callable(module.divide)
