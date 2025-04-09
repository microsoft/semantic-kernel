# Copyright (c) Microsoft. All rights reserved.

import logging
import sys

import chainlit as cl
from agents.tagline_agent import TaglineGenerator
from dotenv import load_dotenv

load_dotenv(override=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)

# Set log levels for specific libraries that might be too verbose
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

agent = TaglineGenerator()


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("agent_threads", {})


@cl.on_message
async def on_message(message: cl.Message):
    # Get threads from session
    agent_threads = cl.user_session.get("agent_threads", {})
    thread = agent_threads.get(agent.id)

    final_response = None
    async for response in agent.invoke(messages=message.content, thread=thread):
        if response:
            # Send each message as it comes in
            await cl.Message(content=response.message.content, author=agent.name).send()
            final_response = response

    # Update thread in session
    if final_response is not None:
        agent_threads[agent.id] = final_response.thread
        cl.user_session.set("agent_threads", agent_threads)
