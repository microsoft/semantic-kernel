# Copyright (c) Microsoft. All rights reserved.

"""A basic JSON-based planner for the Python Semantic Kernel"""
import json
from semantic_kernel.kernel import Kernel
from semantic_kernel.core_skills.planning.plan import Plan
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.skill_definition import sk_function


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

EmailConnector.EmailTo
description: email the input text to a recipient
args:
- input: the text to email
- recipient: the recipient's email address. Multiple addresses may be included if separated by ';'.

LanguageHelpers.TranslateTo
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
"Tell a joke about cars. Translate it to French"

[OUTPUT]
    {
        "input": "cars",
        "subtasks": [
            {"function": "Joke"},
            {"function": "TranslateTo", "args": {"language": "French"}}
        ]
    }

[AVAILABLE FUNCTIONS] 
WriterSkill.Brainstorm
description: Brainstorm ideas
args:
- input: the input to brainstorm about

ShakespeareSkill.shakespeare
description: Write in Shakespearean style
args:
- input: the input to write about

WriterSkill.EmailTo
description: Write an email to a recipient
args:
- input: the input to write about
- recipient: the recipient's email address.

[GOAL]
"Tomorrow is Valentine's day. I need to come up with a few date ideas. She likes Shakespeare so write using his style.
E-mail these ideas to my significant other"

[OUTPUT]
    {
        "input": "Valentine's Day Date Ideas",
        "subtasks": [
            {"function": "WriterSkill.Brainstorm"},
            {"function": "ShakespeareSkill.shakespeare"},
            {"function": "WriterSkill.EmailTo", "args": {"recipient": "significant_other"}},
            {"function": "translate", "args": {"language": "French"}}
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
    Description: Basic planner for the Semantic Kernel.

    Usage:
        kernel.import_skill(BasicPlanner(), "planner");

    Examples:

    {{planner.create_plan}}
    {{planner.execute_plan}}
    """

    @sk_function(
        description="Creates a plan for the given goal based off the functions that are available in the kernel.",
        name="create_plan",
    )
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
        planner = kernel.create_semantic_function(prompt, max_tokens=1000, temperature=0.8)

        # Get a dictionary of skill names to all native and semantic functions
        native_functions = kernel.skills.get_functions_view()._native_functions
        semantic_functions = kernel.skills.get_functions_view()._semantic_functions
        native_functions.update(semantic_functions)

        # Create a flattened list of all functions
        all_functions = native_functions
        skill_names = list(all_functions.keys())
        all_functions_list = []
        all_functions_dict = {}
        for skill_name in skill_names:
            for f in all_functions[skill_name]:
                function_name = f.name
                all_functions_dict[skill_name + "." + function_name] = f.description

        # Create the [AVAILABLE FUNCTIONS] section of the prompt
        available_functions_string = ""
        for name in list(all_functions_dict.keys()):
            available_functions_string += name + "\n"
            available_functions_string += "description: " + all_functions_dict[name] + "\n"
            available_functions_string += "args:\n"
            # TODO: FIGURE OUT HOW TO GET ARGS FROM FUNCTIONS
            available_functions_string += "\n"

        # Create the context for the planner 
        context = ContextVariables()
        # Add the goal to the context
        context["goal"] = goal
        context["available_functions"] = available_functions_string
        generated_plan = await planner.invoke_with_vars_async(input=context)
        return Plan(prompt=prompt, goal=goal, plan=generated_plan)


    @sk_function(
        description="Given a plan, execute each of the functions within the plan from start to finish and output the result.",
        name="execute_plan",
    )
    async def execute_plan_async(
            self,
            plan: Plan,
            kernel: Kernel
    ) -> str:
        """
        Given a plan, execute each of the functions within the plan
        from start to finish and output the result.
        """
        generated_plan = json.loads(plan.generated_plan.result)

        context = ContextVariables()    
        context["input"] = generated_plan["input"]
        subtasks = generated_plan["subtasks"]

        all_functions = []
        for subtask in subtasks:
            skill_name, function_name = subtask["function"].split(".")
            sk_function = kernel.skills.get_function(skill_name, function_name)
            
            # Get the arguments dictionary for the function
            args = subtask.get("args", None)
            if args:
                for key, value in args.items():
                    context[key] = value
                output = await sk_function.invoke_with_vars_async(input=context)

            else:
                output = await sk_function.invoke_with_vars_async(input=context)

            # Override the input context variable with the output of the function
            context["input"] = output.result

        # At the very end, return the output of the last function
        return output.result