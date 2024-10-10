# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Callable, Dict, Optional
import semantic_kernel, autogen


class AutoGenPlanner:
    """(Demo) Semantic Kernel planner using Conversational Programming via AutoGen.

    AutoGenPlanner leverages OpenAI Function Calling and AutoGen agents to solve
    a task using only the Plugins loaded into Semantic Kernel. SK Plugins are
    automatically shared with AutoGen, so you only need to load the Plugins in SK
    with the usual `kernel.import_skill(...)` syntax. You can use native and
    semantic functions without any additional configuration. Currently the integration
    is limited to functions with a single string parameter. The planner has been
    tested with GPT 3.5 Turbo and GPT 4. It always used 3.5 Turbo with OpenAI,
    just for performance and cost reasons.
    """

    import datetime
    from typing import List, Dict

    ASSISTANT_PERSONA = f"""Only use the functions you have been provided with.
Do not ask the user to perform other actions than executing the functions.
Use the functions you have to find information not available.
Today's date is: {datetime.date.today().strftime("%B %d, %Y")}.
Reply TERMINATE when the task is done.
"""

    def __init__(self, kernel: semantic_kernel.Kernel, llm_config: Dict = None):
        """
        Args:
            kernel: an instance of Semantic Kernel, with plugins loaded.
            llm_config: a dictionary with the following keys:
                - type: "openai" or "azure"
                - openai_api_key: OpenAI API key
                - azure_api_key: Azure API key
                - azure_deployment: Azure deployment name
                - azure_endpoint: Azure endpoint
        """
        super().__init__()
        self.kernel = kernel
        self.llm_config = llm_config

    def create_assistant_agent(
        self, name: str, persona: str = ASSISTANT_PERSONA
    ) -> autogen.AssistantAgent:
        """
        Create a new AutoGen Assistant Agent.
        Args:
            name (str): the name of the agent
            persona (str): the LLM system message defining the agent persona,
                in case you want to customize it.
        """
        return autogen.AssistantAgent(
            name=name, system_message=persona, llm_config=self.__get_autogen_config()
        )

    def create_user_agent(
        self,
        name: str,
        max_auto_reply: Optional[int] = None,
        human_input: Optional[str] = "ALWAYS",
    ) -> autogen.UserProxyAgent:
        """
        Create a new AutoGen User Proxy Agent.
        Args:
            name (str): the name of the agent
            max_auto_reply (int): the maximum number of consecutive auto replies.
                default to None (no limit provided).
            human_input (str): the human input mode. default to "ALWAYS".
                Possible values are "ALWAYS", "TERMINATE", "NEVER".
                (1) When "ALWAYS", the agent prompts for human input every time a message is received.
                    Under this mode, the conversation stops when the human input is "exit",
                    or when is_termination_msg is True and there is no human input.
                (2) When "TERMINATE", the agent only prompts for human input only when a termination message is received or
                    the number of auto reply reaches the max_consecutive_auto_reply.
                (3) When "NEVER", the agent will never prompt for human input. Under this mode, the conversation stops
                    when the number of auto reply reaches the max_consecutive_auto_reply or when is_termination_msg is True.
        """
        return autogen.UserProxyAgent(
            name=name,
            human_input_mode=human_input,
            max_consecutive_auto_reply=max_auto_reply,
            function_map=self.__get_function_map(),
        )

    def __get_autogen_config(self):
        """
        Get the AutoGen LLM and Function Calling configuration.
        """
        if self.llm_config:
            if self.llm_config["type"] == "openai":
                if (
                    not self.llm_config["openai_api_key"]
                    or self.llm_config["openai_api_key"] == "sk-..."
                ):
                    raise Exception("OpenAI API key is not set")
                return {
                    "functions": self.__get_function_definitions(),
                    "config_list": [
                        {
                            "model": "gpt-3.5-turbo",
                            "api_key": self.llm_config["openai_api_key"],
                        }
                    ],
                }
            if self.llm_config["type"] == "azure":
                if (
                    not self.llm_config["azure_api_key"]
                    or not self.llm_config["azure_deployment"]
                    or not self.llm_config["azure_endpoint"]
                ):
                    raise Exception("Azure OpenAI API configuration is incomplete")
                return {
                    "functions": self.__get_function_definitions(),
                    "config_list": [
                        {
                            "model": self.llm_config["azure_deployment"],
                            "api_type": "azure",
                            "api_key": self.llm_config["azure_api_key"],
                            "api_base": self.llm_config["azure_endpoint"],
                            "api_version": "2023-08-01-preview",
                        }
                    ],
                }

        raise ValueError(f"Invalid LLM type provided. Expected 'openai' or 'azure', but got '{self.llm_type}'. Please check your configuration.")

    def __get_function_definitions(self) -> List:
        """
        Get the list of function definitions for OpenAI Function Calling.
        """
        functions = []
        sk_functions = self.kernel.skills.get_functions_view()
        for ns in {**sk_functions.native_functions, **sk_functions.semantic_functions}:
            for f in sk_functions.native_functions[ns]:
                functions.append(
                    {
                        "name": f.name,
                        "description": f.description,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                p.name: {"description": p.description, "type": p.type_}
                                for p in f.parameters
                            },
                            "required": [p.name for p in f.parameters],
                        },
                    }
                )
        return functions

    def __get_function_map(self) -> Dict:
        """
        Get the function map for AutoGen Function Calling.
        """
        function_map = {}
        sk_functions = self.kernel.skills.get_functions_view()
        for ns in {**sk_functions.native_functions, **sk_functions.semantic_functions}:
            for f in sk_functions.native_functions[ns]:
                function_map[f.name] = SKFunctionWrapper(
                    self.kernel.skills.get_function(f.skill_name, f.name)
                )
        return function_map


class SKFunctionWrapper:
    """
    Wrapper for SK functions to be used with AutoGen Function Calling.
    This wrapper is designed for functions that accept a single string parameter.
    """
    """
    Wrapper for SK functions to be used with AutoGen Function Calling.
    """

    _function: Callable[..., str]

    def __init__(self, delegate_function: Callable):
        self._function = delegate_function

    def __call__(self, **kwargs: Dict[str, Any]) -> str:
        variables = semantic_kernel.ContextVariables()
        for k, v in kwargs.items():
            variables[k] = v
        return self._function(variables=variables)
