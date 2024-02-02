from semantic_kernel.functions.kernel_arguments import KernelArguments


def test_kernel_arguments():
    kargs = KernelArguments()
    assert kargs is not None
    assert kargs.execution_settings is None
    assert not kargs.keys()
