# Copyright (c) Microsoft. All rights reserved.

"""A basic JSON-based planner for the Python Semantic Kernel"""

import json

import regex

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


class Plan:
    """A simple plan object for the Semantic Kernel"""

    def __init__(self, prompt: str, goal: str, plan: str):
        self.prompt = prompt
        self.goal = goal
        self.generated_plan = plan

    def __str__(self):
        return f"Prompt: {self.prompt}\nGoal: {self.goal}\nPlan: {self.generated_plan}"

    def __repr__(self):
        return str(self)


PROMPT = """
You are a planner for the Semantic Kernel.
Your job is to create a properly formatted JSON plan step by step, to satisfy the goal given.
Create a list of subtasks based off the [GOAL] provided.
Each subtask must be from within the [AVAILABLE FUNCTIONS] list. Do not use any functions that are not in the list.
Base your decisions on which functions to use from the description and the name of the function.
Sometimes, a function may take arguments. Provide them if necessary.
The plan should be as short as possible.
For example:

[AVAILABLE FUNCTIONS]
EmailConnector.LookupContactEmail
description: looks up the a contact and retrieves their email address
args:
- name: the name to look up

WriterPlugin.EmailTo
description: email the input text to a recipient
args:
- input: the text to email
- recipient: the recipient's email address. Multiple addresses may be included if separated by ';'.

WriterPlugin.Translate
description: translate the input to another language
args:
- input: the text to translate
- language: the language to translate to

WriterPlugin.Summarize
description: summarize input text
args:
- input: the text to summarize

FunPlugin.Joke
description: Generate a funny joke
args:
- input: the input to generate a joke about

[GOAL]
"Tell a joke about cars. Translate it to Spanish"

[OUTPUT]
    {
        "input": "cars",
        "subtasks": [
            {"function": "FunPlugin.Joke"},
            {"function": "WriterPlugin.Translate", "args": {"language": "Spanish"}}
        ]
    }

[AVAILABLE FUNCTIONS]
WriterPlugin.Brainstorm
description: Brainstorm ideas
args:
- input: the input to brainstorm about

EdgarAllenPoePlugin.Poe
description: Write in the style of author Edgar Allen Poe
args:
- input: the input to write about

WriterPlugin.EmailTo
description: Write an email to a recipient
args:
- input: the input to write about
- recipient: the recipient's email address.

WriterPlugin.Translate
description: translate the input to another language
args:
- input: the text to translate
- language: the language to translate to

[GOAL]
"Tomorrow is Valentine's day. I need to come up with a few date ideas.
She likes Edgar Allen Poe so write using his style.
E-mail these ideas to my significant other. Translate it to French."

[OUTPUT]
    {
        "input": "Valentine's Day Date Ideas",
        "subtasks": [
            {"function": "WriterPlugin.Brainstorm"},
            {"function": "EdgarAllenPoePlugin.Poe"},
            {"function": "WriterPlugin.EmailTo", "args": {"recipient": "significant_other"}},
            {"function": "WriterPlugin.Translate", "args": {"language": "French"}}
        ]
    }

[AVAILABLE FUNCTIONS]
{{$available_functions}}

[GOAL]
{{$goal}}

[OUTPUT]
"""


class BasicPlanner:
    """
    Basic JSON-based planner for the Semantic Kernel.
    """

    def __init__(self, service_id: str) -> None:
        self.service_id = service_id

    def _create_available_functions_string(self, kernel: Kernel) -> str:
        """
        Given an instance of the Kernel, create the [AVAILABLE FUNCTIONS]
        string for the prompt.
        """
        # Get a dictionary of plugin names to all native and semantic functions
        if not kernel.plugins:
            return ""
        all_functions = {
            f"{func.plugin_name}.{func.name}": func for func in kernel.plugins.get_list_of_function_metadata()
        }
        all_functions_descriptions_dict = {key: func.description for key, func in all_functions.items()}
        all_functions_params_dict = {key: func.parameters for key, func in all_functions.items()}

        # Create the [AVAILABLE FUNCTIONS] section of the prompt
        available_functions_string = ""
        for name in list(all_functions_descriptions_dict.keys()):
            available_functions_string += name + "\n"
            description = all_functions_descriptions_dict[name]
            available_functions_string += "description: " + description + "\n"
            available_functions_string += "args:\n"

            # Add the parameters for each function
            parameters = all_functions_params_dict[name]
            for param in parameters:
                if not param.description:
                    param_description = ""
                else:
                    param_description = param.description
                available_functions_string += "- " + param.name + ": " + param_description + "\n"
            available_functions_string += "\n"

        return available_functions_string

    async def create_plan(
        self,
        goal: str,
        kernel: Kernel,
        prompt: str = PROMPT,
    ) -> Plan:
        """
        Creates a plan for the given goal based off the functions that
        are available in the kernel.
        """
        exec_settings = PromptExecutionSettings(
            service_id=self.service_id,
            max_tokens=1000,
            temperature=0.8,
        )

        prompt_template_config = PromptTemplateConfig(
            template=prompt,
            execution_settings=exec_settings,
        )

        # Create the prompt function for the planner with the given prompt
        planner = kernel.create_function_from_prompt(
            plugin_name="PlannerPlugin",
            function_name="CreatePlan",
            prompt_template_config=prompt_template_config,
        )

        available_functions_string = self._create_available_functions_string(kernel)

        generated_plan = await planner.invoke(
            kernel, KernelArguments(goal=goal, available_functions=available_functions_string)
        )
        return Plan(prompt=prompt, goal=goal, plan=generated_plan)

    async def execute_plan(self, plan: Plan, kernel: Kernel) -> str:
        """
        Given a plan, execute each of the functions within the plan
        from start to finish and output the result.
        """

        # Filter out good JSON from the result in case additional text is present
        json_regex = r"\{(?:[^{}]|(?R))*\}"
        generated_plan_string = regex.search(json_regex, str(plan.generated_plan.value)).group()

        # TODO: there is some silly escape chars affecting the result of plan.generated_plan.value
        # There should be \n only but they are showing up as \\n
        encoded_bytes = generated_plan_string.encode("utf-8")
        decoded_string = encoded_bytes.decode("unicode_escape")

        generated_plan = json.loads(decoded_string)

        arguments = KernelArguments(input=generated_plan["input"])
        subtasks = generated_plan["subtasks"]

        for subtask in subtasks:
            plugin_name, function_name = subtask["function"].split(".")
            kernel_function = kernel.plugins[plugin_name][function_name]

            # Get the arguments dictionary for the function
            args = subtask.get("args", None)
            if args:
                for key, value in args.items():
                    arguments[key] = value
                output = await kernel_function.invoke(kernel, arguments)

            else:
                output = await kernel_function.invoke(kernel, arguments)

            # Override the input context variable with the output of the function
            arguments["input"] = str(output)

        # At the very end, return the output of the last function
        return str(output)
