# Copyright (c) Microsoft. All rights reserved.

import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    ("module_name", "class_name", "package_name", "extra_name", "method_name"),
    [
        (
            "semantic_kernel.connectors.ai.hugging_face.hf_prompt_execution_settings",
            "HuggingFacePromptExecutionSettings",
            "transformers",
            "hugging_face",
            "get_generation_config",
        ),
        (
            "semantic_kernel.connectors.ai.onnx.services.onnx_gen_ai_completion_base",
            "OnnxGenAICompletionBase",
            "onnxruntime_genai",
            "onnx",
            "",
        ),
    ],
)
def test_missing_optional_dependency_names_install_extra(
    module_name: str,
    class_name: str,
    package_name: str,
    extra_name: str,
    method_name: str,
) -> None:
    script = """
import importlib
import importlib.abc
import sys

class MissingDependencyFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == sys.argv[3] or fullname.startswith(f"{sys.argv[3]}."):
            raise ModuleNotFoundError(f"No module named '{sys.argv[3]}'", name=sys.argv[3])
        return None

sys.meta_path.insert(0, MissingDependencyFinder())
try:
    module = importlib.import_module(sys.argv[1])
    connector = getattr(module, sys.argv[2])() if sys.argv[5] else getattr(module, sys.argv[2])("unused")
    if sys.argv[5]:
        getattr(connector, sys.argv[5])()
except ImportError as exc:
    print(exc)
else:
    raise AssertionError("Expected an ImportError for the blocked optional dependency")
"""
    result = subprocess.run(
        [sys.executable, "-c", script, module_name, class_name, package_name, extra_name, method_name],
        capture_output=True,
        check=True,
        text=True,
    )

    assert package_name.replace("_", "-") in result.stdout
    assert f"semantic-kernel[{extra_name}]" in result.stdout
