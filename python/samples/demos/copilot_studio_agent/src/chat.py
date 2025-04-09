# Copyright (c) Microsoft. All rights reserved.

import logging

import chainlit as cl
from dotenv import load_dotenv
from product_advisor import ProductAdvisor

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logging.getLogger("direct_line_agent").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

product_advisor_agent = ProductAdvisor()


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("agent_threads", {})


@cl.on_message
async def on_message(message: cl.Message):
    # Get threads from session
    agent_threads = cl.user_session.get("agent_threads", {})
    thread = agent_threads.get(product_advisor_agent.id)

    final_response = None
    async for response in product_advisor_agent.invoke(messages=message.content, thread=thread):
        if response:
            # Send each message as it comes in
            await cl.Message(content=response.message.content, author=product_advisor_agent.name).send()
            final_response = response

    # Update thread in session
    agent_threads[product_advisor_agent.id] = final_response.thread
    cl.user_session.set("agent_threads", agent_threads)
