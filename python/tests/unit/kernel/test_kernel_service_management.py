# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import Union

import pytest

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.kernel import Kernel
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


@pytest.fixture(scope="function")
def kernel() -> Kernel:
    return Kernel()


@pytest.fixture(scope="function")
def kernel_with_service(kernel: Kernel) -> Kernel:
    service = AIServiceClientBase(service_id="service", ai_model_id="ai_model_id")
    kernel.add_service(service)
    return kernel


def test_kernel(kernel: Kernel):
    assert kernel
    assert kernel.services == {}


def test_kernel_add_service(kernel: Kernel):
    service = AIServiceClientBase(service_id="service", ai_model_id="ai_model_id")
    kernel.add_service(service)
    assert kernel.services == {"service": service}


def test_kernel_add_service_twice(kernel_with_service: Kernel):
    service = AIServiceClientBase(service_id="service", ai_model_id="ai_model_id")
    with pytest.raises(ValueError):
        kernel_with_service.add_service(service)
    assert kernel_with_service.services == {"service": service}


def test_kernel_add_multiple_services(kernel_with_service: Kernel):
    service2 = AIServiceClientBase(service_id="service2", ai_model_id="ai_model_id")
    kernel_with_service.add_service(service2)
    assert kernel_with_service.services["service2"] == service2
    assert len(kernel_with_service.services) == 2


def test_kernel_remove_service(kernel_with_service: Kernel):
    kernel_with_service.remove_service("service")
    assert kernel_with_service.services == {}


def test_kernel_remove_service_error(kernel_with_service: Kernel):
    with pytest.raises(ValueError):
        kernel_with_service.remove_service("service2")


def test_kernel_remove_all_service(kernel_with_service: Kernel):
    kernel_with_service.remove_all_services()
    assert kernel_with_service.services == {}


def test_get_service(kernel_with_service: Kernel):
    service_get = kernel_with_service.get_service("service")
    assert service_get == kernel_with_service.services["service"]


def test_get_services_by_type(kernel_with_service: Kernel):
    service_get = kernel_with_service.get_services_by_type(AIServiceClientBase)
    assert service_get["service"] == kernel_with_service.services["service"]


def test_get_service_with_id_not_found(kernel_with_service: Kernel):
    with pytest.raises(ValueError):
        kernel_with_service.get_service("service2", type=AIServiceClientBase)


def test_get_service_with_type(kernel_with_service: Kernel):
    service_get = kernel_with_service.get_service("service", type=AIServiceClientBase)
    assert service_get == kernel_with_service.services["service"]


def test_get_service_with_multiple_types(kernel_with_service: Kernel):
    service_get = kernel_with_service.get_service("service", type=(AIServiceClientBase, ChatCompletionClientBase))
    assert service_get == kernel_with_service.services["service"]


@pytest.mark.skipif(sys.version_info < (3, 10), reason="This is valid syntax only in python 3.10+.")
def test_get_service_with_multiple_types_union(kernel_with_service: Kernel):
    """This is valid syntax only in python 3.10+. It is skipped for older versions."""
    service_get = kernel_with_service.get_service("service", type=Union[AIServiceClientBase, ChatCompletionClientBase])
    assert service_get == kernel_with_service.services["service"]


def test_get_service_with_type_not_found(kernel_with_service: Kernel):
    with pytest.raises(ValueError):
        kernel_with_service.get_service("service", type=ChatCompletionClientBase)


def test_get_service_no_id(kernel_with_service: Kernel):
    service_get = kernel_with_service.get_service()
    assert service_get == kernel_with_service.services["service"]
