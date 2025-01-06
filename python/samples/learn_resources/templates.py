# Copyright (c) Microsoft. All rights reserved.

import asyncio
from functools import reduce

from samples.sk_service_configurator import add_service
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.prompt_template import InputVariable, PromptTemplateConfig

# Initialize the kernel
kernel = Kernel()

# Add the service to the kernel
# use_chat: True to use chat completion, False to use text completion
kernel = add_service(kernel=kernel, use_chat=True)

# An ideal prompt for this is {{$history}}{{$request}} as those
# get cleanly parsed into a new chat_history object while invoking
# the function. Another possibility is create the prompt as {{$history}}
# and make sure to add the user message to the history before invoking.
chat_function = kernel.add_function(
    plugin_name="Conversation",
    function_name="Chat",
    description="Chat with the assistant",
    prompt_template_config=PromptTemplateConfig(
        template="{{$history}}{{$request}}",
        description="Chat with the assistant",
        input_variables=[
            InputVariable(name="request", description="The user input", is_required=True),
            InputVariable(
                name="history",
                description="The history of the conversation",
                is_required=True,
                allow_dangerously_set_content=True,
            ),
        ],
    ),
)

choices = ["ContinueConversation", "EndConversation"]
chat_function_intent = kernel.add_function(
    plugin_name="Conversation",
    function_name="getIntent",
    description="Chat with the assistant",
    template_format="handlebars",
    prompt_template_config=PromptTemplateConfig(
        template="""
            <message role="system">Instructions: What is the intent of this request?
            Do not explain the reasoning, just reply back with the intent. If you are unsure, reply with {{choices[0]}}.
            Choices: {{choices}}.</message>

            {{#each few_shot_examples}}
                {{#each this.messages}}
                    {{#message role=role}}
                    {{~content~}}
                    {{/message}}
                {{/each}}
            {{/each}}

            {{#each chat_history.messages}}
                {{#message role=role}}
                {{~content~}}
                {{/message}}
            {{/each}}

            <message role="user">{{request}}</message>
            <message role="system">Intent:</message>
            """,
        description="Chat with the assistant",
        template_format="handlebars",
        input_variables=[
            InputVariable(name="request", description="The user input", is_required=True),
            InputVariable(
                name="chat_history",
                description="The history of the conversation",
                is_required=True,
                allow_dangerously_set_content=True,
            ),
            InputVariable(
                name="choices",
                description="The choices for the user to select from",
                is_required=True,
                allow_dangerously_set_content=True,
            ),
            InputVariable(
                name="few_shot_examples",
                description="The few shot examples to help the user",
                is_required=True,
                allow_dangerously_set_content=True,
            ),
        ],
    ),
)
few_shot_examples = [
    ChatHistory(
        messages=[
            ChatMessageContent(
                role=AuthorRole.USER, content="Can you send a very quick approval to the marketing team?"
            ),
            ChatMessageContent(role=AuthorRole.SYSTEM, content="Intent:"),
            ChatMessageContent(role=AuthorRole.ASSISTANT, content="ContinueConversation"),
        ]
    ),
    ChatHistory(
        messages=[
            ChatMessageContent(role=AuthorRole.USER, content="Thanks, I'm done for now"),
            ChatMessageContent(role=AuthorRole.SYSTEM, content="Intent:"),
            ChatMessageContent(role=AuthorRole.ASSISTANT, content="EndConversation"),
        ]
    ),
]


async def main():
    # Create the history
    history = ChatHistory()

    while True:
        try:
            request = input("User:> ")
        except (KeyboardInterrupt, EOFError):
            break

        result = await kernel.invoke(
            plugin_name="Conversation",
            function_name="getIntent",
            request=request,
            history=history,
            choices=choices,
            few_shot_examples=few_shot_examples,
        )
        if str(result) == "EndConversation":
            break

        result = kernel.invoke_stream(
            plugin_name="Conversation",
            function_name="Chat",
            request=request,
            history=history,
        )
        all_chunks = []
        print("Assistant:> ", end="")
        async for chunk in result:
            if isinstance(chunk[0], StreamingChatMessageContent) and chunk[0].role == AuthorRole.ASSISTANT:
                all_chunks.append(chunk[0])
                print(str(chunk[0]), end="")
        print()

        history.add_user_message(request)
        history.add_assistant_message(str(reduce(lambda x, y: x + y, all_chunks)))

    print("\n\nExiting chat...")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
