# Copyright (c) Microsoft. All rights reserved.

import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    ("module_name", "class_name", "package_name", "extra_name", "method_name", "load_directly"),
    [
        (
            "semantic_kernel.connectors.ai.hugging_face.hf_prompt_execution_settings",
            "HuggingFacePromptExecutionSettings",
            "transformers",
            "hugging_face",
            "get_generation_config",
            True,
        ),
        (
            "semantic_kernel.connectors.ai.onnx.services.onnx_gen_ai_completion_base",
            "OnnxGenAICompletionBase",
            "onnxruntime_genai",
            "onnx",
            "",
            False,
        ),
    ],
)
def test_missing_optional_dependency_names_install_extra(
    module_name: str,
    class_name: str,
    package_name: str,
    extra_name: str,
    method_name: str,
    load_directly: bool,
) -> None:
    script = """
import importlib
import importlib.abc
import importlib.util
from pathlib import Path
import sys

class MissingDependencyFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == sys.argv[3] or fullname.startswith(f"{sys.argv[3]}."):
            raise ModuleNotFoundError(f"No module named '{sys.argv[3]}'", name=sys.argv[3])
        return None

sys.meta_path.insert(0, MissingDependencyFinder())
try:
    if sys.argv[6] == "True":
        package_spec = importlib.util.find_spec("semantic_kernel")
        module_path = Path(package_spec.origin).parent.joinpath(*sys.argv[1].split(".")[1:]).with_suffix(".py")
        module_spec = importlib.util.spec_from_file_location("optional_dependency_module", module_path)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
    else:
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
        [
            sys.executable,
            "-c",
            script,
            module_name,
            class_name,
            package_name,
            extra_name,
            method_name,
            str(load_directly),
        ],
        capture_output=True,
        check=True,
        text=True,
    )

    assert package_name.replace("_", "-") in result.stdout
    assert f"semantic-kernel[{extra_name}]" in result.stdout
