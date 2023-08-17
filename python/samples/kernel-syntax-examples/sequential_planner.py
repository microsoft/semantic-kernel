# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.core_skills import FileIOSkill, MathSkill, TextSkill, TimeSkill
from semantic_kernel.planning import SequentialPlanner


async def main():
    kernel = sk.Kernel()
    api_key, org_id = sk.openai_settings_from_dot_env()

    kernel.add_chat_service(
        "gpt-3.5", OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
    )
    kernel.import_skill(MathSkill(), "math")
    kernel.import_skill(FileIOSkill(), "fileIO")
    kernel.import_skill(TimeSkill(), "time")
    kernel.import_skill(TextSkill(), "text")

    # create an instance of sequential planner.
    planner = SequentialPlanner(kernel)

    # the ask for which the sequential planner is going to find a relevant function.
    ask = "What day of the week is today, all uppercase?"

    # ask the sequential planner to identify a suitable function from the list of functions available.
    plan = await planner.create_plan_async(goal=ask)

    # ask the sequential planner to execute the identified function.
    result = await plan.invoke_async()

    for step in plan._steps:
        print(step.description, ":", step._state.__dict__)

    print("Expected Answer:")
    print(result)
    """
    Output:
    HELLO ...
    """


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
