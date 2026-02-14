# Copyright (c) Microsoft. All rights reserved.

import importlib.util
import sys
import types
from pathlib import Path


def _load_types_compat_module():
    module_name = "sk_openai_types_compat_test_module"
    module_path = (
        Path(__file__).resolve().parents[5] / "semantic_kernel" / "connectors" / "ai" / "open_ai" / "_types_compat.py"
    )
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_openai_types_compat_uses_omit_when_available(monkeypatch):
    fake_openai = types.ModuleType("openai")
    fake_types = types.ModuleType("openai._types")

    class DummyOmit:
        pass

    omit_marker = object()
    fake_types.FileTypes = str
    fake_types.Omit = DummyOmit
    fake_types.omit = omit_marker
    fake_openai._types = fake_types

    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    monkeypatch.setitem(sys.modules, "openai._types", fake_types)

    compat = _load_types_compat_module()

    assert compat.Omit is DummyOmit
    assert compat.omit is omit_marker


def test_openai_types_compat_falls_back_to_not_given(monkeypatch):
    fake_openai = types.ModuleType("openai")
    fake_types = types.ModuleType("openai._types")

    class DummyNotGiven:
        pass

    not_given_marker = object()
    fake_types.FileTypes = str
    fake_types.NotGiven = DummyNotGiven
    fake_types.NOT_GIVEN = not_given_marker
    fake_openai._types = fake_types

    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    monkeypatch.setitem(sys.modules, "openai._types", fake_types)

    compat = _load_types_compat_module()

    assert compat.Omit is DummyNotGiven
    assert compat.omit is not_given_marker
