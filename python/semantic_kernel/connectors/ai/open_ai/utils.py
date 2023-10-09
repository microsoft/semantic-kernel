from logging import Logger
from typing import Any, Dict, List, Optional

from semantic_kernel import Kernel, SKContext
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.semantic_functions.open_ai_chat_prompt_template import (
    OpenAIChatPromptTemplate,
)
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase


def _describe_function(function: SKFunctionBase) -> Dict[str, str]:
    """Create the object used for function_calling.

    Assumes that arguments for semantic functions are optional, for native functions required.
    """
    func_view = function.describe()
    return {
        "name": f"{func_view.skill_name}-{func_view.name}",
        "description": func_view.description,
        "parameters": {
            "type": "object",
            "properties": {
                param.name: {"description": param.description, "type": param.type_}
                for param in func_view.parameters
            },
            "required": [p.name for p in func_view.parameters if p.required],
        },
    }


def get_function_calling_object(
    kernel: Kernel, filter: Dict[str, List[str]]
) -> List[Dict[str, str]]:
    """Create the object used for function_calling.

    args:
        kernel: the kernel.
        filter: a dictionary with keys
            exclude_skill, include_skill, exclude_function, include_function
            and lists of the required filter.
            The function name should be in the format "skill_name-function_name".
            Using exclude_skill and include_skill at the same time will raise an error.
            Using exclude_function and include_function at the same time will raise an error.
            If using include_* implies that all other function will be excluded.
            Example:
                filter = {
                    "exclude_skill": ["skill1", "skill2"],
                    "include_function": ["skill3-function1", "skill4-function2"],
                    }
                will return only skill3-function1 and skill4-function2.
                filter = {
                    "exclude_function": ["skill1-function1", "skill2-function2"],
                    }
                will return all functions except skill1-function1 and skill2-function2.
        caller_function_name: the name of the function that is calling the other functions.
    returns:
        a filtered list of dictionaries of the functions in the kernel that can be passed to the function calling api.
    """
    include_skill = filter.get("include_skill", None)
    exclude_skill = filter.get("exclude_skill", [])
    include_function = filter.get("include_function", None)
    exclude_function = filter.get("exclude_function", [])
    if include_skill and exclude_skill:
        raise ValueError(
            "Cannot use both include_skill and exclude_skill at the same time."
        )
    if include_function and exclude_function:
        raise ValueError(
            "Cannot use both include_function and exclude_function at the same time."
        )
    if include_skill:
        include_skill = [skill.lower() for skill in include_skill]
    if exclude_skill:
        exclude_skill = [skill.lower() for skill in exclude_skill]
    if include_function:
        include_function = [function.lower() for function in include_function]
    if exclude_function:
        exclude_function = [function.lower() for function in exclude_function]
    result = []
    for (
        skill_name,
        skill,
    ) in kernel.skills.data.items():
        if skill_name in exclude_skill or (
            include_skill and skill_name not in include_skill
        ):
            continue
        for function_name, function in skill.items():
            current_name = f"{skill_name}-{function_name}"
            if current_name in exclude_function or (
                include_function and current_name not in include_function
            ):
                continue
            result.append(_describe_function(function))
    return result


async def execute_function_call(
    kernel: Kernel, function_call: FunctionCall, log: Optional[Logger] = None
) -> str:
    result = await kernel.run_async(
        kernel.func(**function_call.split_name_dict()),
        input_vars=function_call.to_context_variables(),
    )
    if log:
        log.info(f"Function call result: {result}")
    return str(result)


async def chat_completion_with_function_call(
    kernel: Kernel,
    context: SKContext,
    functions: List[Dict[str, str]] = [],
    chat_skill_name: Optional[str] = None,
    chat_function_name: Optional[str] = None,
    chat_function: Optional[SKFunctionBase] = None,
    *,
    log: Optional[Logger] = None,
    **kwargs: Dict[str, Any],
) -> SKContext:
    """Perform a chat completion with auto-executing function calling.

    This is a recursive function that will execute the chat function multiple times,
    at least once to get a first completion, if a function_call is returned,
    the function_call is executed (using the execute_function_call method),
    the result is added to the chat prompt template and another completion is requested,
    by calling the function again, if it returns a function_call, it is executed again,
    until the maximum number of function calls is reached,
    at that time a final completion is done without functions.

    args:
        kernel: the kernel to use.
        context: the context to use.
        functions: the function calling object,
            make sure to use get_function_calling_object method to create it.
        Optional arguments:
            chat_skill_name: the skill name of the chat function.
            chat_function_name: the function name of the chat function.
            chat_function: the chat function, if not provided, it will be retrieved from the kernel.
                make sure to provide either the chat_function or the chat_skill_name and chat_function_name.

            log: the logger to use.
            max_function_calls: the maximum number of function calls to execute, defaults to 5.
            current_call_count: the current number of function calls executed.

    returns:
        the context with the result of the chat completion, just like a regular invoke_async/run_async.
    """
    # check the number of function calls
    max_function_calls = kwargs.get("max_function_calls", 5)
    current_call_count = kwargs.get("current_call_count", 0)
    # get the chat function
    if chat_function is None:
        chat_function = kernel.func(
            skill_name=chat_skill_name, function_name=chat_function_name
        )
    assert isinstance(
        chat_function._chat_prompt_template, OpenAIChatPromptTemplate
    ), "Please make sure to initialize your chat function with the OpenAIChatPromptTemplate class."
    context = await chat_function.invoke_async(
        context=context,
        # when the maximum number of function calls is reached, execute the chat function without Functions.
        functions=[] if current_call_count >= max_function_calls else functions,
    )
    function_call = context.objects.pop("function_call", None)
    # if there is no function_call or if the content is not a FunctionCall object, return the context
    if function_call is None or not isinstance(function_call, FunctionCall):
        return context
    result = await execute_function_call(kernel, function_call, log=log)
    # add the result to the chat prompt template
    chat_function._chat_prompt_template.add_function_response_message(
        name=function_call.name, content=str(result)
    )
    # request another completion
    return await chat_completion_with_function_call(
        kernel,
        chat_function=chat_function,
        functions=functions,
        context=context,
        log=log,
        max_function_calls=max_function_calls,
        current_call_count=current_call_count + 1,
    )
