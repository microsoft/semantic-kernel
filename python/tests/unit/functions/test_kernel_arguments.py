from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments


def test_kernel_arguments():
    kargs = KernelArguments()
    assert kargs is not None
    assert kargs.execution_settings == {}
    assert not kargs.keys()


def test_kernel_arguments_with_input():
    kargs = KernelArguments(input=10)
    assert kargs is not None
    assert kargs["input"] == 10


def test_kernel_arguments_with_input_get():
    kargs = KernelArguments(input=10)
    assert kargs is not None
    assert kargs.get("input", None) == 10
    assert not kargs.get("input2", None)


def test_kernel_arguments_keys():
    kargs = KernelArguments(input=10)
    assert kargs is not None
    assert list(kargs.keys()) == ["input"]


def test_kernel_arguments_with_execution_settings():
    test_pes = PromptExecutionSettings(service_id="test")
    kargs = KernelArguments(settings=[test_pes])
    assert kargs is not None
    assert kargs.execution_settings == {"test": test_pes}
