# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


def test_kernel_parameter_metadata_init():
    metadata = KernelParameterMetadata(
        name="test",
        description="description",
        is_required=True,
        type="str",
        default_value="default",
    )

    assert metadata.name == "test"
    assert metadata.description == "description"
    assert metadata.is_required is True
    assert metadata.default_value == "default"
