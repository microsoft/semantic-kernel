# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel as sk
import asyncio
import semantic_kernel.connectors.ai.google_palm as sk_gp
from typing import Tuple


kernel = sk.Kernel()
apikey = sk.google_palm_settings_from_dot_env()
palm_text_embed = sk_gp.GooglePalmTextEmbedding(
        "models/embedding-gecko-001", apikey
)
kernel.add_text_embedding_generation_service("gecko", palm_text_embed)
palm_chat_completion = sk_gp.GooglePalmChatCompletion(
        "models/chat-bison-001", apikey
)
kernel.add_chat_service("models/chat-bison-001", palm_chat_completion)
kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())
kernel.import_skill(sk.core_skills.TextMemorySkill())

async def populate_memory(kernel: sk.Kernel) -> None:
    # Add some documents to the semantic memory
    await kernel.memory.save_information_async(
        "aboutMe", id="info1", text="My name is Andrea"
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info2", text="I currently work as a tour guide"
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info3", text="My favorite hobby is hiking"
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info4", text="I visitied Iceland last year."
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info5", text="My family is from New York"
    )
 
async def search_memory_examples(kernel: sk.Kernel) -> None:
    questions = [
        "what's my name",
        "what is my favorite hobby?",
        "where's my family from?",
        "where did I travel last year?",
        "what do I do for work",
    ]

    for question in questions:
        print(f"Question: {question}")
        result = await kernel.memory.search_async("aboutMe", question)
        print(f"Answer: {result}\n")

async def setup_chat_with_memory(
    kernel: sk.Kernel,
) -> Tuple[sk.SKFunctionBase, sk.SKContext]:
    """
    When using Google PaLM to chat with memories, a chat prompt template is 
    essential; otherwise, the kernel will send text prompts to the Google PaLM 
    chat service. Unfortunately, when a text prompt includes memory, chat 
    history, and the user's current message, PaLM often struggles to comprehend 
    the user's message. To address this issue, the prompt containing memory is
    incorporated into the chat prompt template as a system message.  
    Note that this is only an issue for the chat service; the text service
    does not require a chat prompt template.
    """
    sk_prompt = """
    ChatBot can have a conversation with you about any topic.
    It can give explicit instructions or say 'I don't know' if
    it does not have an answer.

    Information about me, from previous conversations:
    - {{$fact1}} {{recall $fact1}}
    - {{$fact2}} {{recall $fact2}}
    - {{$fact3}} {{recall $fact3}}
    - {{$fact4}} {{recall $fact4}}
    - {{$fact5}} {{recall $fact5}}

    """.strip()

    prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
        max_tokens=2000, temperature=0.7, top_p=0.8
    )
    prompt_template = sk.ChatPromptTemplate(  # Create the chat prompt template
        "{{$user_input}}", kernel.prompt_template_engine, prompt_config
    )
    prompt_template.add_system_message(sk_prompt) # Add the memory as a system message
    function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
    chat_func = kernel.register_semantic_function(None, "ChatWithMemory", function_config)

    context = kernel.create_new_context()
    context["fact1"] = "what is my name?"
    context["fact2"] = "what is my favorite hobby?"
    context["fact3"] = "where's my family from?"
    context["fact4"] = "where did I travel last year?"
    context["fact5"] = "what do I do for work?"

    context[sk.core_skills.TextMemorySkill.COLLECTION_PARAM] = "aboutMe"
    context[sk.core_skills.TextMemorySkill.RELEVANCE_PARAM] = 0.6

    context["chat_history"] = ""

    return chat_func, context

async def chat(
    kernel: sk.Kernel, chat_func: sk.SKFunctionBase, context: sk.SKContext
) -> bool:
    try:
        user_input = input("User:> ")
        context["user_input"] = user_input
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    answer = await kernel.run_async(chat_func, input_vars=context.variables)
    context["chat_history"] += f"\nUser:> {user_input}\nChatBot:> {answer}\n"

    print(f"ChatBot:> {answer}")
    return True

async def main() -> None:
    await populate_memory(kernel)
    await search_memory_examples(kernel)
    chat_func, context = await setup_chat_with_memory(kernel)
    print("Begin chatting (type 'exit' to exit):\n")
    chatting = True
    while chatting:
        chatting = await chat(kernel, chat_func, context)

if __name__ == "__main__":
    asyncio.run(main())