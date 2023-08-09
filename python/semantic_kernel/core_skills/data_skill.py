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
        data_skill = kernel.import_skill(
        DataSkill(data=df,service=openai_chat_completion), skill_name="data"
        )
        prompt = "How old is Bob?"
        query_async = data_skill["queryAsync"]
        result = await query_async.invoke_async(prompt)
        print(result)
    """
    path: Union[str, List[str]]
    data: Union[pd.DataFrame, List[pd.DataFrame]]
    mutable: bool #TODO
    verbose: bool #TODO
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
                elif all(isinstance(item, pd.DataFrame) for item in self.data): self.data.append(pd.read_csv(self.path))
                else:
                    raise ValueError("Data must be a pandas dataframe or a list of pandas dataframes")
        if isinstance(self.path, List):
            if self.data is None: self.data = []
            elif isinstance(self.data, pd.DataFrame): self.data = [self.data]
            elif all(isinstance(item, pd.DataFrame) for item in self.data): pass
            else:
                raise ValueError("Data must be a pandas dataframe or a list of pandas dataframes")
            for file in self.path:
                if not file.endswith(".csv"):
                    raise ValueError("File path must be to a CSV file")
                else:
                    self.data.append(pd.read_csv(file))

        self._prefix = """You were given the first five rows of each pandas 
        dataframe earlier. There may be more rows. """
        self._suffix = """Write a Python function `process({arg_name})` where 
        {arg_name} {description}.
        This is the function's purpose: {goal}
        Write the function in a Python code block with all necessary imports. 
        Do not include any example usage. Do not include any explanation nor 
        decoration. Store the reult in a local variable named `result`."""

    def get_df_data(self) -> str:
        """
        Returns the first 5 rows of pandas dataframes in JSON format. The LLM
        needs this information to answer the user's questions about the data.

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
            prompt = f"""You are working with a list of {num} pandas dataframes 
            in Python, named df1, df2, and so on. """
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
        prompt = context + "\n" + self._prefix
        if isinstance(self.data, pd.DataFrame): #If there is only one dataframe
            df=self.data
            local_vars = {'df': df}
            arg = "df"
            description = "is a pandas dataframe"
        else: #If there are multiple dataframes
            count = 1
            local_vars = {}
            arg = ""
            for table in self.data:
                name = f"df{count}"
                arg += name + ", "
                local_vars[name] = table
                count += 1
            arg = arg[:-2]
            description = "are pandas dataframes"

        formatted_suffix = self._suffix.format(goal=ask, arg_name=arg, description=description)
        prompt = context + "\n" + self._prefix + """You need to write plain Python 
        code that the user can run on their dataframes.""" + formatted_suffix
        max_retry = 1
        for _ in range(max_retry): #If generated code doesn't work, try again
            try:
                #Get python code as a string to answer the user's question
                code = await self._code_skill.custom_code_async(prompt) 
                #Dynamically execute the code on the dataframe(s)
                await self._code_skill.custom_execute_async(code, local_vars=local_vars) 
                #Get all dataframes provided by the user
                df_variables = [var_name for var_name in local_vars.keys() if var_name.startswith('df')]
                process_function = local_vars.get('process')
                dataframes = [local_vars[var_name] for var_name in df_variables]
                #Get the result of the execution
                result = local_vars['process'](*dataframes)
                break
            except Exception as e:
                print(f"Error occurred: {e}")
                continue
                await asyncio.sleep(1) #Introduce a delay before the next retry
        else:
            # The loop completed without breaking, meaning all retries failed
            raise AssertionError("Execution failed after 1 retry")
        
        if result:
            #Re-format the result with natural language
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
        else:
            return ""
   
    async def transform_async(self, ask: str, context: SKContext) -> pd.DataFrame:
        """
        Transform the data in the pandas dataframe.

        Args:
            ask -- The transformation to apply to the data
        """
        prompt = self._prefix + """You need to write python code that will 
        transform the dataframe as the user asked."""  + self._suffix
        #TODO
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
        #TODO
        pass
    

    


    


    

    
