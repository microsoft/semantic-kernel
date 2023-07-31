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

    plugins_directory = "./plugins"

    # Import the OrchestratorPlugin and SummarizeSkill from the plugins directory.
    orchestrator_plugin = kernel.import_semantic_skill_from_directory(
        plugins_directory, "OrchestratorPlugin"
    )
    summarization_plugin = kernel.import_semantic_skill_from_directory(  # noqa: F841
        plugins_directory, "SummarizeSkill"
    )
    get_intent_function = orchestrator_plugin["GetIntent"]

    # Create a new context and set the input, history, and options variables.
    context = kernel.create_new_context()
    context["input"] = "Yes"
    context[
        "history"
    ] = """Bot: How can I help you?
    User: My team just hit a major milestone and I would like to send them a message to congratulate them.
    Bot:Would you like to send an email?"""
    context["options"] = "SendEmail, ReadEmail, SendMeeting, RsvpToMeeting, SendChat"

    # Run the Summarize function with the context.
    result = get_intent_function(context=context)

    print(result)


# Run the main function
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
