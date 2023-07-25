from plugins.MathPlugin.MathPlugin import MathPlugin
from plugins.OrchestratorPlugin.OrchestratorPlugin import OrchestratorPlugin

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import (
    AzureTextCompletion,
    OpenAITextCompletion,
)


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

    pluginsDirectory = "./plugins"

    # Import the semantic functions
    kernel.import_semantic_skill_from_directory(pluginsDirectory, "OrchestratorPlugin")
    kernel.import_semantic_skill_from_directory(pluginsDirectory, "SummarizeSkill")

    # Import the native functions
    mathPlugin = kernel.import_skill(MathPlugin(), "MathPlugin") # noqa: F841
    orchestratorPlugin = kernel.import_skill(
        OrchestratorPlugin(kernel), "OrchestratorPlugin"
    )

    # Make a request that runs the Sqrt function
    result1 = await orchestratorPlugin["route_request"].invoke_async(
        "What is the square root of 634?"
    )
    print(result1["input"])

    # Make a request that runs the Add function
    result2 = await orchestratorPlugin["route_request"].invoke_async(
        "What is 42 plus 1513?"
    )
    print(result2["input"])


# Run the main function
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
