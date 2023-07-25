from plugins.MathPlugin.MathPlugin import MathPlugin

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import (
    AzureTextCompletion,
    OpenAITextCompletion,
)
from semantic_kernel.planning.basic_planner import BasicPlanner


async def main():
    # Initialize the kernel
    kernel = sk.Kernel()

    # Configure AI service used by the kernel. Load settings from the .env file.
    useAzureOpenAI = False
    if useAzureOpenAI:
        deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
        kernel.add_text_completion_service(
            "dv", AzureTextCompletion(deployment, endpoint, api_key)
        )
    else:
        api_key, org_id = sk.openai_settings_from_dot_env()
        kernel.add_text_completion_service(
            "dv", OpenAITextCompletion("text-davinci-003", api_key, org_id)
        )

    planner = BasicPlanner()

    # Import the native functions
    mathPlugin = kernel.import_skill(MathPlugin(), "MathPlugin") # noqa: F841

    ask = "If my investment of 2130.23 dollars increased by 23%, how much would I have after I spent $5 on a latte?"
    plan = await planner.create_plan_async(ask, kernel)

    # Execute the plan
    result = await planner.execute_plan_async(plan, kernel)

    print("Plan results:")
    print(result)


# Run the main function
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
