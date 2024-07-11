# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.sk_pydantic import PydanticField
from semantic_kernel.skill_definition import sk_function


class WaitSkill(PydanticField):
    """
    WaitSkill provides a set of functions to wait for a certain amount of time.

    Usage:
        kernel.import_skill(WaitSkill(), skill_name="wait")

    Examples:
        {{wait.seconds 5}} => Wait for 5 seconds
    """

    @sk_function(description="Wait for a certain number of seconds.")
    async def wait(self, seconds_text: str):
        try:
            seconds = max(float(seconds_text), 0)
        except ValueError:
            raise ValueError("seconds text must be a number")
        await asyncio.sleep(seconds)
