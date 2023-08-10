# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import List, Union

import pandas as pd

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    OpenAIChatCompletion,
)
from semantic_kernel.core_skills import CodeSkill
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition import sk_function

PROMPT_PREFIX = """The preceding is a summary of the data. There may be more rows."""
PROMPT_SUFFIX = """Write a Python function `process({arg_name})` where 
    {arg_name} {description}.
    This is the function's purpose: {goal}
    Write the function in a Python code block with all necessary imports.
    Do not include any example usage. Do not include any explanation nor 
    decoration. Store the reult in a local variable named `result`."""
GLOBAL_VARS = {'pd': pd}    # must give access to pandas module


class DataSkill:
    """
    Description: A skill that allows the user to query CSV files and pandas
    dataframes.

    Usage:
        data_skill = kernel.import_skill(
        DataSkill(data=df,service=openai_chat_completion), skill_name="data"
        )
        query_async = data_skill["queryAsync"]

        prompt = "How old is Bob?"
        result = await query_async.invoke_async(prompt)
        print(result)
    """

    path: Union[str, List[str]]
    data: Union[pd.DataFrame, List[pd.DataFrame]]
    mutable: bool  # TODO
    verbose: bool  # TODO
    _service: ChatCompletionClientBase
    _chat_settings: ChatRequestSettings
    _code_skill: CodeSkill
    _data_context: str

    def __init__(
        self,
        service: Union[AzureChatCompletion, OpenAIChatCompletion],
        path: Union[str, List[str]] = None,
        data: Union[pd.DataFrame, List[pd.DataFrame]] = None,
        mutable: bool = False,
        verbose: bool = True,
    ):
        self.data = data
        self.path = path
        self.mutable = mutable
        self.verbose = verbose
        self._service = service
        self._chat_settings = ChatRequestSettings(temperature=0.0)
        self._code_skill = CodeSkill(self._service)
        self._data_context = self.get_df_data()

        if isinstance(self.path, str):
            if not self.path.endswith(".csv"):
                raise ValueError("File path must be to a CSV file")
            else:
                if self.data is None:
                    self.data = pd.read_csv(self.path)
                elif isinstance(self.data, pd.DataFrame):
                    self.data = [self.data, pd.read_csv(self.path)]
                elif all(isinstance(item, pd.DataFrame) for item in self.data):
                    self.data.append(pd.read_csv(self.path))
                else:
                    raise ValueError(
                        "Data must be a pandas dataframe or a list of pandas dataframes"
                    )
        if isinstance(self.path, List):
            if self.data is None:
                self.data = []
            elif isinstance(self.data, pd.DataFrame):
                self.data = [self.data]
            elif all(isinstance(item, pd.DataFrame) for item in self.data):
                pass
            else:
                raise ValueError(
                    "Data must be a pandas dataframe or a list of pandas dataframes"
                )
            for file in self.path:
                if not file.endswith(".csv"):
                    raise ValueError("File path must be to a CSV file")
                else:
                    self.data.append(pd.read_csv(file))

    def get_df_data(self, num_rows: int = 3) -> str:
        """
        Returns the first header rows of pandas dataframes in JSON format. The LLM
        needs this information to answer the user's questions about the data.

        Args:
            num_rows {int} -- How many rows from the top to supply, defaults to 5
            Control this to limit token usage, especially with many dataframes. 
            The minimum is 1.

        Returns:
            A prompt containing information on how many dataframes and their headers.
        """
        if num_rows < 1:
            raise ValueError("Must have at least 1 row in each dataframe's header")

        if isinstance(self.data, pd.DataFrame):
            prompt = """You are working with one pandas dataframe in Python with the following header: \n"""
            prompt += self.data.head(num_rows).to_json(orient="records") + "\n"
        else:
            num = len(self.data)
            prompt = f"You are working with a list of {num} pandas dataframes in Python, named df1, df2, and so on.\n"
            for i, table in enumerate(self.data):
                prompt += f"The header of df{i + 1} is: \n"
                prompt += table.head(num_rows).to_json(orient="records") + "\n"
        return prompt

    @sk_function(
        description="""Answer a query about the data that does not require 
        data transformation or plotting.""",
        name="queryAsync",
        input_description="The question to ask the LLM",
    )
    async def query_async(self, ask: str) -> str:
        """
        Answer a query about the data.

        Args:
            ask -- The question to ask the LLM
        """
        if isinstance(self.data, pd.DataFrame):  # If there is only one dataframe
            df = self.data
            local_vars = {"df": df}
            arg = "df"
            description = "is a pandas dataframe"
        else: # If there are multiple dataframes
            local_vars = {}
            arg = ""
            for i, table in enumerate(self.data):
                name = f"df{i + 1}"
                arg += name + ", "
                local_vars[name] = table

            arg = arg[:-2]
            description = "are pandas dataframes"

        # Construct the prompt
        formatted_suffix = PROMPT_SUFFIX.format(
            goal=ask, arg_name=arg, description=description
        )
        prompt = self._data_context + "\n" + PROMPT_PREFIX + formatted_suffix

        max_attempts = 2
        for _ in range(max_attempts):  # If generated code doesn't work, try again
            try:
                # Get Python code as a string to answer the user's question
                code = await self._code_skill.custom_code_async(prompt)

                # Dynamically execute the code on the dataframe(s)
                await self._code_skill.custom_execute_async(code, GLOBAL_VARS, local_vars)

                # Get all dataframes provided by the user
                df_variables = [
                    var_name
                    for var_name in local_vars.keys()
                    if var_name.startswith("df")
                ]
                local_vars.get("process")
                dataframes = [local_vars[var_name] for var_name in df_variables]

                # Get the result of the execution
                result = local_vars["process"](*dataframes)
                break
            except Exception as e:
                print(f"Error occurred: {e}")
                await asyncio.sleep(1)  # Introduce a delay before the next retry
                continue
        else:
            # The loop completed without breaking, meaning all retries failed
            raise AssertionError("Execution failed after 1 retry, aborting")

        if result:
            # Re-format the result with natural language
            prompt = f"""The answer to the user's query was {result}.
            Provide an answer back to the user in natural language.
            User: {ask}
            Bot:
            """
            answer = await self._service.complete_chat_async(
                [("user", prompt)], self._chat_settings
            )
            return answer
        else:
            return ""

    async def transform_async(self, ask: str, context: SKContext) -> pd.DataFrame:
        """
        Transform the data in the pandas dataframe.

        Args:
            ask -- The transformation to apply to the data
        """
        (
            PROMPT_PREFIX
            + """You need to write Python code that will 
        transform the dataframe as the user asked."""
            + PROMPT_SUFFIX
        )
        # TODO
        pass

    @sk_function(
        description="Plot the data in the pandas dataframe",
        name="plotAsync",
        input_description="The description of the plot to generate",
    )
    async def plot_async(self, ask: str, context: SKContext) -> str:
        """
        Plot the data in the pandas dataframe.

        Args:
            ask -- The description of the plot to generate
        """
        (
            PROMPT_PREFIX
            + """You need to write Python code that will plot 
        the data as the user asked. You need to import matplotlib and use nothing
        else for plotting. """
            + PROMPT_SUFFIX
        )
        # TODO
        pass
