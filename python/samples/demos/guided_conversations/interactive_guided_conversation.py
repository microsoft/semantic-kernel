# Copyright (c) Microsoft. All rights reserved.

"""Run this interactive guided conversation script to test out the teaching scenario!
The teaching artifact, rules, conversation flow, context, and resource constraint can all be modified to
fit your needs & try out new scenarios!
"""

import asyncio

from pydantic import BaseModel, Field
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from guided_conversation.plugins.guided_conversation_agent import GuidedConversation
from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit


# Artifact - The artifact is like a form that the agent must complete throughout the conversation.
# It can also be thought of as a working memory for the agent.
# We allow any valid Pydantic BaseModel class to be used.
class MyArtifact(BaseModel):
    student_poem: str = Field(description="The acrostic poem written by the student.")
    initial_feedback: str = Field(description="Feedback on the student's final revised poem.")
    final_feedback: str = Field(description="Feedback on how the student was able to improve their poem.")
    inappropriate_behavior: list[str] = Field(
        description="""List any inappropriate behavior the student attempted while chatting with you. \
It is ok to leave this field Unanswered if there was none."""
    )


# Rules - These are the do's and don'ts that the agent should follow during the conversation.
rules = [
    "DO NOT write the poem for the student."
    "Terminate the conversation immediately if the students asks for harmful or inappropriate content.",
]

# Conversation Flow (optional) - This defines in natural language the steps of the conversation.
conversation_flow = """1. Start by explaining interactively what an acrostic poem is.
2. Then give the following instructions for how to go ahead and write one:
    1. Choose a word or phrase that will be the subject of your acrostic poem.
    2. Write the letters of your chosen word or phrase vertically down the page.
    3. Think of a word or phrase that starts with each letter of your chosen word or phrase.
    4. Write these words or phrases next to the corresponding letters to create your acrostic poem.
3. Then give the following example of a poem where the word or phrase is HAPPY:
    Having fun with friends all day,
    Awesome games that we all play.
    Pizza parties on the weekend,
    Puppies we bend down to tend,
    Yelling yay when we win the game
4. Finally have the student write their own acrostic poem using the word or phrase of their choice. Encourage them to be creative and have fun with it.
After they write it, you should review it and give them feedback on what they did well and what they could improve on.
Have them revise their poem based on your feedback and then review it again.
"""

# Context (optional) - This is any additional information or the circumstances the agent is in that it should be aware of.
# It can also include the high level goal of the conversation if needed.
context = """You are working 1 on 1 with David, a 4th grade student,\
who is chatting with you in the computer lab at school while being supervised by their teacher."""


# Resource Constraints (optional) - This defines the constraints on the conversation such as time or turns.
# It can also help with pacing the conversation,
# For example, here we have set an exact time limit of 10 turns which the agent will try to fill.
resource_constraint = ResourceConstraint(
    quantity=10,
    unit=ResourceConstraintUnit.TURNS,
    mode=ResourceConstraintMode.EXACT,
)


async def main() -> None:
    """Main function to interactively run a guided conversation.

    The user can chat with this teaching agent until:
    1. The user types 'exit' to end the conversation.
    2. There's a KeyboardInterrupt or EOFError.
    3. The conversation ends. This can be due to the agent ending the conversation, which will happen if the resource constraint is met, the artifact is complete, or the conversation just isn't making progress (user is not cooperative).
    """

    kernel = Kernel()
    service_id = "gc_main"
    chat_service = AzureChatCompletion(
        service_id=service_id,
        deployment_name="gpt-4o-2024-05-13",
        api_version="2024-05-01-preview",
    )
    kernel.add_service(chat_service)

    guided_conversation_agent = GuidedConversation(
        kernel=kernel,
        artifact=MyArtifact,
        conversation_flow=conversation_flow,
        context=context,
        rules=rules,
        resource_constraint=resource_constraint,
        service_id=service_id,
    )

    # Step the conversation to start the conversation with the agent
    result = await guided_conversation_agent.step_conversation()
    print(f"Assistant: {result.ai_message}")

    while True:
        try:
            # Get user input
            user_input = input("User: ")
        except KeyboardInterrupt:
            print("\n\nExiting chat...")
            return
        except EOFError:
            print("\n\nExiting chat...")
            return
        if user_input == "exit":
            print("\n\nExiting chat...")
            return
        else:
            # Step the conversation to get the agent's reply
            result = await guided_conversation_agent.step_conversation(user_input=user_input)
            print(f"Assistant: {result.ai_message}")
            if result.is_conversation_over:
                return


if __name__ == "__main__":
    asyncio.run(main())
