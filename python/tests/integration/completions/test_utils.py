# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from semantic_kernel.connectors.ai.onnx import OnnxGenAIChatCompletion
from semantic_kernel.prompt_template import PromptTemplateConfig

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


async def retry(func, retries=20):
    min_delay = 2
    max_delay = 7
    for i in range(retries):
        try:
            return await func()
        except Exception as e:
            logger.error(f"Retry {i + 1}: {e}")
            if i == retries - 1:  # Last retry
                raise
            await asyncio.sleep(max(min(i, max_delay), min_delay))
    return None


def setup_onnx_gen_ai_chat_completion():
    prompt = """{% for message in messages %}
                    {% if message['content'] is not string %}
                        {{'<|image_1|>'}}
                    {% else %}
                        {% if message['role'] == 'system' %}
                            {{'<|system|>\n' + message['content'] + '<|end|>\n'}}
                        {% elif message['role'] == 'user' %}
                            {{'<|user|>\n' + message['content'] + '<|end|>\n'}}
                        {% elif message['role'] == 'assistant' %}
                            {{'<|assistant|>\n' + message['content'] + '<|end|>\n' }}
                        {% endif %}
                    {% endif %}
                {% endfor %}
                <|assistant|>"""

    prompt_template_config = PromptTemplateConfig(template=prompt, template_format="jinja2")
    return OnnxGenAIChatCompletion(prompt_template_config)
