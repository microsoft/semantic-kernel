# Copyright (c) Microsoft. All rights reserved.

import json
import pandas as pd
from typing import Union, List
from . import CodeSkill
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition import sk_function
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    OpenAIChatCompletion,
)
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings

class DataSkill:
    """
    Description: A skill that allows the user to query CSV files and pandas 
    dataframes.

    Usage:
        kernel.import_skill(DataSkill(), skill_name="DataSkill")
        context = sk.ContextVariables()
        context["data_summary"] = data_skill.get_row_column_names()
    """
    path: Union[str, List[str]]
    data: Union[pd.DataFrame, List[pd.DataFrame]]
    mutable: bool
    verbose: bool
    _prefix: str
    _suffix: str
    _service: ChatCompletionClientBase
    _chat_settings: ChatRequestSettings
    _code_skill: CodeSkill

    def __init__(self, service: Union[AzureChatCompletion, OpenAIChatCompletion],
        path: Union[str, List[str]]=None, data: Union[pd.DataFrame, List[pd.DataFrame]]=None, 
        mutable: bool=False, verbose: bool=True,
        ):
        self.data = data
        self.path = path
        self.mutable = mutable
        self.verbose = verbose
        self._service = service
        self._chat_settings = ChatRequestSettings(temperature=0.0)
        self._code_skill = CodeSkill(self._service)

        if isinstance(self.path, str):
            if not self.path.endswith(".csv"):
                raise ValueError("File path must be to a CSV file")
            else:
                if self.data is None: self.data = pd.read_csv(self.path)
                elif isinstance(self.data, pd.DataFrame): self.data = [self.data, pd.read_csv(self.path)]
                elif isinstance(self.data, List[pd.DataFrame]): self.data.append(pd.read_csv(self.path))
                else:
                    raise ValueError("Data must be a pandas dataframe or a list of pandas dataframes")
        if isinstance(self.path, List):
            if self.data is None: self.data = []
            elif isinstance(self.data, pd.DataFrame): self.data = [self.data]
            elif isinstance(self.data, List[pd.DataFrame]): pass
            else:
                raise ValueError("Data must be a pandas dataframe or a list of pandas dataframes")
            for file in self.path:
                if not file.endswith(".csv"):
                    raise ValueError("File path must be to a CSV file")
                else:
                    self.data.append(pd.read_csv(file))

        self._prefix = """You were given the first five rows of each pandas 
        dataframe earlier. There may be more rows. """
        self._suffix = """Write a Python function `process(df)` where df is a
        pandas dataframe.
        This is the function's purpose: {goal}
        Write the function in a Python code block with all necessary imports. 
        Do not include any example usage. Do not include any explanation nor 
        decoration."""
                

    def get_df_data(self) -> str:
        """
        Returns the first 5 rows of pandas dataframes in JSON format.

        Returns:
            The row and column names of the data tables contained in a prompt.
        """
        if isinstance(self.data, pd.DataFrame):
            prompt = """You are working with one pandas dataframe in Python. 
            These are the first 5 rows, in JSON format: \n"""
            prompt += self.data.head().to_json(orient="records") + "\n"
        else:
            count = 1
            num = len(self.data)
            prompt = f"""You are working with {num} pandas dataframes in Python,
            named df1, df2, and so on. """
            for table in self.data:
                prompt += f"The first 5 rows of df{count} are, in this order: \n"
                prompt += table.head().to_json(orient="records") + "\n"
                count += 1
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
        context = self.get_df_data()
        formatted_suffix = self._suffix.format(goal=ask)
        prompt = context + "\n" + self._prefix + """You need to write plain Python 
        code that the user can run on their dataframes.""" + formatted_suffix 
        code = await self._code_skill.custom_code_async(prompt) #Get python code as a string
        df=self.data
        local_vars = {'df': df}
        await self._code_skill.custom_execute_async(code, local_vars=local_vars) #Dynamically execute the code on the dataframe
        result = local_vars['process'](local_vars['df'])
        prompt = "The answer to the user's question is: " + str(result)
        prompt += f"""You need to provide the answer back to the user with 
        natural language.
        User: {ask}
        Bot:
        """
        answer = await self._service.complete_chat_async(
            [("user", prompt)], self._chat_settings
        )
        return answer
    
   
    async def transform_async(self, ask: str, context: SKContext) -> pd.DataFrame:
        """
        Transform the data in the pandas dataframe.

        Args:
            ask -- The transformation to apply to the data
        """
        prompt = self._prefix + """You need to write python code that will 
        transform the dataframe as the user asked."""  + self._suffix
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
        prompt = self._prefix + """You need to write python code that will plot 
        the data as the user asked. You need to import matplotlib and use nothing
        else for plotting. """ + self._suffix
        pass
    

    


    


    

    
