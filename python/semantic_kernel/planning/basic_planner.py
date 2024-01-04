# Copyright (c) Microsoft. All rights reserved.

"""A basic JSON-based planner for the Python Semantic Kernel"""
import json

import regex

from semantic_kernel.kernel import Kernel
from semantic_kernel.orchestration.context_variables import ContextVariables


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

WriterSkill.EmailTo
description: email the input text to a recipient
args:
- input: the text to email
- recipient: the recipient's email address. Multiple addresses may be included if separated by ';'.

WriterSkill.Translate
description: translate the input to another language
args:
- input: the text to translate
- language: the language to translate to

WriterSkill.Summarize
description: summarize input text
args:
- input: the text to summarize

FunSkill.Joke
description: Generate a funny joke
args:
- input: the input to generate a joke about

[GOAL]
"Tell a joke about cars. Translate it to Spanish"

[OUTPUT]
    {
        "input": "cars",
        "subtasks": [
            {"function": "FunSkill.Joke"},
            {"function": "WriterSkill.Translate", "args": {"language": "Spanish"}}
        ]
    }

[AVAILABLE FUNCTIONS]
WriterSkill.Brainstorm
description: Brainstorm ideas
args:
- input: the input to brainstorm about

EdgarAllenPoeSkill.Poe
description: Write in the style of author Edgar Allen Poe
args:
- input: the input to write about

WriterSkill.EmailTo
description: Write an email to a recipient
args:
- input: the input to write about
- recipient: the recipient's email address.

WriterSkill.Translate
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
            {"function": "WriterSkill.Brainstorm"},
            {"function": "EdgarAllenPoeSkill.Poe"},
            {"function": "WriterSkill.EmailTo", "args": {"recipient": "significant_other"}},
            {"function": "WriterSkill.Translate", "args": {"language": "French"}}
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

    def _create_available_functions_string(self, kernel: Kernel) -> str:
        """
        Given an instance of the Kernel, create the [AVAILABLE FUNCTIONS]
        string for the prompt.
        """
        # Get a dictionary of skill names to all native and semantic functions
        native_functions = kernel.skills.get_functions_view().native_functions
        semantic_functions = kernel.skills.get_functions_view().semantic_functions
        native_functions.update(semantic_functions)

        # Create a mapping between all function names and their descriptions
        # and also a mapping between function names and their parameters
        all_functions = native_functions
        skill_names = list(all_functions.keys())
        all_functions_descriptions_dict = {}
        all_functions_params_dict = {}

        for skill_name in skill_names:
            for func in all_functions[skill_name]:
                key = skill_name + "." + func.name
                all_functions_descriptions_dict[key] = func.description
                all_functions_params_dict[key] = func.parameters

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
                available_functions_string += (
                    "- " + param.name + ": " + param_description + "\n"
                )
            available_functions_string += "\n"

        return available_functions_string

    async def create_plan_async(
        self,
        goal: str,
        kernel: Kernel,
        prompt: str = PROMPT,
    ) -> Plan:
        """
        Creates a plan for the given goal based off the functions that
        are available in the kernel.
        """

        # Create the semantic function for the planner with the given prompt
        planner = kernel.create_semantic_function(
            prompt, max_tokens=1000, temperature=0.8
        )

        available_functions_string = self._create_available_functions_string(kernel)

        # Create the context for the planner
        context = ContextVariables()
        # Add the goal to the context
        context["goal"] = goal
        context["available_functions"] = available_functions_string
        generated_plan = await planner.invoke_async(variables=context)
        return Plan(prompt=prompt, goal=goal, plan=generated_plan)

    async def execute_plan_async(self, plan: Plan, kernel: Kernel) -> str:
        """
        Given a plan, execute each of the functions within the plan
        from start to finish and output the result.
        """

        # Filter out good JSON from the result in case additional text is present
        json_regex = r"\{(?:[^{}]|(?R))*\}"
        generated_plan_string = regex.search(
            json_regex, plan.generated_plan.result
        ).group()
        generated_plan = json.loads(generated_plan_string)

        context = ContextVariables()
        context["input"] = generated_plan["input"]
        subtasks = generated_plan["subtasks"]

        for subtask in subtasks:
            skill_name, function_name = subtask["function"].split(".")
            sk_function = kernel.skills.get_function(skill_name, function_name)

            # Get the arguments dictionary for the function
            args = subtask.get("args", None)
            if args:
                for key, value in args.items():
                    context[key] = value
                output = await sk_function.invoke_async(variables=context)

            else:
                output = await sk_function.invoke_async(variables=context)

            # Override the input context variable with the output of the function
            context["input"] = output.result

        # At the very end, return the output of the last function
        return output.result
