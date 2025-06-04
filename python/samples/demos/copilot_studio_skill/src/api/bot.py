# Copyright (c) Microsoft. All rights reserved.

from adapter import AdapterWithErrorHandler

# Custom classes to handle errors and claims validation
from auth import AllowedCallersClaimsValidator
from botbuilder.core import MemoryStorage, MessageFactory, TurnContext
from botbuilder.integration.aiohttp import ConfigurationBotFrameworkAuthentication
from botbuilder.schema import (
    Activity,
    EndOfConversationCodes,
    InputHints,
)
from botframework.connector.auth import AuthenticationConfiguration
from config import config

# This is the SK agent that will be used to handle the conversation
from sk_conversation_agent import agent
from teams import Application, ApplicationOptions
from teams.state import TurnState

from semantic_kernel.contents import ChatHistory

# This is required for bot to work as Copilot Skill,
# not adding a claims validator will result in an error
claims_validator = AllowedCallersClaimsValidator(config)
auth = AuthenticationConfiguration(tenant_id=config.APP_TENANTID, claims_validator=claims_validator.claims_validator)

# Create the bot application
# We use the Teams Application class to create the bot application,
# then we added a custom adapter for skill errors handling.
bot = Application[TurnState](
    ApplicationOptions(
        bot_app_id=config.APP_ID,
        storage=MemoryStorage(),
        # CANNOT PASS A DICT HERE; MUST PASS A CLASS WITH APP_ID, APP_PASSWORD, AND APP_TENANTID ATTRIBUTES
        adapter=AdapterWithErrorHandler(ConfigurationBotFrameworkAuthentication(config, auth_configuration=auth)),
    )
)


@bot.before_turn
async def setup_chathistory(context: TurnContext, state: TurnState):
    chat_history = state.conversation.get("chat_history") or ChatHistory()

    state.conversation["chat_history"] = chat_history

    return state


@bot.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    user_message = context.activity.text

    # Get the chat_history from the conversation state
    chat_history: ChatHistory = state.conversation.get("chat_history")

    # Add the new user message
    chat_history.add_user_message(user_message)

    # Get the response from the semantic kernel agent (v1.22.0 and later)
    sk_response = await agent.get_response(history=chat_history, user_input=user_message)

    # Store the updated chat_history back into conversation state
    state.conversation["chat_history"] = chat_history

    # Send the response back to the user
    # NOTE in the context of a Copilot Skill,
    # the response is sent as a Response from /api/messages endpoint
    await context.send_activity(MessageFactory.text(sk_response, input_hint=InputHints.ignoring_input))

    # Skills must send an EndOfConversation activity to indicate the conversation is complete
    # NOTE: this is a simple example, in a real skill you would likely want to send this
    # only when the user has completed their task
    end = Activity.create_end_of_conversation_activity()
    end.code = EndOfConversationCodes.completed_successfully
    await context.send_activity(end)

    return True
