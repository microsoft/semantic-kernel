# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.prompt_template import PromptTemplateConfig

jinja_template = """
    {% for message in messages %}
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

prompt_template = PromptTemplateConfig(
    template=jinja_template,
    name="chat",
    template_format="jinja2",
)

broken_jinja_prompt = "This is a test with a {{broken jinja template}}"

broken_prompt_template = PromptTemplateConfig(template=broken_jinja_prompt, name="chat", template_format="jinja2")

gen_ai_config = {"model": {"test": "test"}}

gen_ai_config_vision = {"model": {"vision": "test"}}
