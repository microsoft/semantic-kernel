from semantic_kernel import Kernel
from semantic_kernel.services.ai_service_selector import AIServiceSelector


def test_kernel_init_with_ai_service_selector():
    ai_service_selector = AIServiceSelector()
    kernel = Kernel(ai_service_selector=ai_service_selector)
    assert kernel.ai_service_selector is not None
