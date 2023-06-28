import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAITextCompletion
from Plugins.MathPlugin import MathPlugin


async def old_main():
    kernel = sk.Kernel()

    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_text_completion_service(
        "dv", OpenAITextCompletion("text-davinci-003", api_key)
    )

    plugins_directory = "./Plugins"

    orchestrator_plugin = kernel.import_semantic_skill_from_directory(
        plugins_directory, "OrchestratorPlugin"
    )

    get_intent_function = orchestrator_plugin["GetIntent"]

    context = kernel.create_new_context()
    context["input"] = "Yes"
    context[
        "history"
    ] = """Bot: How can I help you?
    User: My team just hit a major milestone and I would like to send them a message to congratulate them.
    Bot:Would you like to send an email?
    """
    context["options"] = "SendEmail, ReadEmail, SendMeeting, RsvpToMeeting, SendChat"

    result = get_intent_function(context=context)

    print(result)


async def main():
    kernel = sk.Kernel()
    math_plugin = kernel.import_skill(MathPlugin(), skill_name="math_plugin")
    sqrt = math_plugin["square_root"]
    add = math_plugin["add"]

    # Run the square root function
    print(await sqrt.invoke_async(64))

    context = kernel.create_new_context()
    context["input"] = "3"
    context["number2"] = "7"
    print(await add.invoke_async(context=context))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
