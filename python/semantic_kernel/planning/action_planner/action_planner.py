import os
from logging import Logger
from typing import Optional
from semantic_kernel import Kernel
from semantic_kernel.planning import Plan
from semantic_kernel.utils.null_logger import NullLogger
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase


class ActionPlanner:
    """
    Action Planner allows to select one function out of many, to achieve a given goal.
    The planner implements the Intent Detection pattern, uses the functions registered
    in the kernel to see if there's a relevant one, providing instructions to call the
    function and the rationale used to select it. The planner can also return
    "no function" if nothing relevant is available.
    """

    _stop_sequence: str = "#END-OF-PLAN"
    _skill_name: str = "this"

    _planner_function: SKFunctionBase

    _kernel: Kernel
    _prompt_template: str
    _logger: Logger

    def __init__(
        self,
        kernel: Kernel,
        prompt: Optional[str] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        if kernel is None:
            raise ValueError("Kernel cannot be `None`.")

        self._logger = logger if logger else NullLogger()

        __cur_dir = os.path.dirname(os.path.abspath(__file__))
        __prompt_file = os.path.join(__cur_dir, "skprompt.txt")

        self._prompt_template = prompt if prompt else open(__prompt_file, "r").read()

        self._planner_function = kernel.create_semantic_function(
            skill_name=self._skill_name,
            prompt_template=self._prompt_template,
            max_tokens=1024,
            stop_sequences=[self._stop_sequence],
        )
        kernel.import_skill(self, self._skill_name)

        self._kernel = kernel
        self._context = kernel.create_new_context()

    async def create_plan_async(self) -> Plan:
        pass
