# Copyright (c) Microsoft. All rights reserved.
from pytest import fixture, mark, raises

from semantic_kernel import Kernel
from semantic_kernel.exceptions.filter_exceptions import FilterManagementException


@fixture
def custom_filter():
    async def custom_filter(context, next):
        await next(context)

    return custom_filter


@mark.parametrize(
    "filter_type, filter_attr",
    [("function_invocation", "function_invocation_filters"), ("prompt_rendering", "prompt_rendering_filters")],
)
@mark.usefixtures("custom_filter")
class TestKernelFilterExtension:
    def test_add_filter(self, kernel: Kernel, custom_filter, filter_type: str, filter_attr: str):
        kernel.add_filter(filter_type, custom_filter)
        assert len(getattr(kernel, filter_attr)) == 1

    def test_add_multiple_filters(self, kernel: Kernel, custom_filter, filter_type: str, filter_attr: str):
        custom_filter2 = custom_filter
        kernel.add_filter(filter_type, custom_filter)
        kernel.add_filter(filter_type, custom_filter2)
        assert len(getattr(kernel, filter_attr)) == 2

    def test_filter_decorator(self, kernel: Kernel, custom_filter, filter_type: str, filter_attr: str):
        kernel.filter(filter_type)(custom_filter)

        assert len(getattr(kernel, filter_attr)) == 1

    def test_remove_filter(self, kernel: Kernel, custom_filter, filter_type: str, filter_attr: str):
        kernel.add_filter(filter_type, custom_filter)
        assert len(getattr(kernel, filter_attr)) == 1

        kernel.remove_filter(filter_id=id(custom_filter))
        assert len(getattr(kernel, filter_attr)) == 0

    def test_remove_filter_with_type(self, kernel: Kernel, custom_filter, filter_type: str, filter_attr: str):
        kernel.add_filter(filter_type, custom_filter)
        assert len(getattr(kernel, filter_attr)) == 1

        kernel.remove_filter(filter_type=filter_type, filter_id=id(custom_filter))
        assert len(getattr(kernel, filter_attr)) == 0

    def test_remove_filter_by_position(self, kernel: Kernel, custom_filter, filter_type: str, filter_attr: str):
        kernel.add_filter(filter_type, custom_filter)
        assert len(getattr(kernel, filter_attr)) == 1

        kernel.remove_filter(filter_type, position=0)
        assert len(getattr(kernel, filter_attr)) == 0

    def test_remove_filter_without_type(self, kernel: Kernel, custom_filter, filter_type: str, filter_attr: str):
        kernel.add_filter(filter_type, custom_filter)
        assert len(getattr(kernel, filter_attr)) == 1

        kernel.remove_filter(filter_id=id(custom_filter))
        assert len(getattr(kernel, filter_attr)) == 0


def test_unknown_filter_type(kernel: Kernel, custom_filter):
    with raises(FilterManagementException):
        kernel.add_filter("unknown", custom_filter)


def test_remove_filter_fail(kernel: Kernel):
    with raises(FilterManagementException):
        kernel.remove_filter()


def test_remove_filter_fail_position(kernel: Kernel):
    with raises(FilterManagementException):
        kernel.remove_filter(position=0)
