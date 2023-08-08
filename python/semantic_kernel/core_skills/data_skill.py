# Copyright (c) Microsoft. All rights reserved.

import json
import pandas as pd
from typing import Union, List
from . import CodeSkill
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition import sk_function


class DataSkill:
    """
    Description: A skill that allows the user to query structured data.

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

    def __init__(self, path: Union[str, List[str]]=None, data: Union[pd.DataFrame, 
        List[pd.DataFrame]]=None, mutable: bool=False, verbose: bool=True):
        self.data = data
        self.path = path
        self.mutable = mutable
        self.verbose = verbose

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
                    
        self._prefix = """You are working with a pandas dataframe in Python. You 
        may be working with one or more dataframe. You were given the row and 
        column names of the pandas dataframes earlier. """
        self._suffix = """Answer the question with code only, do not provide any 
        explanation or other text. If it does not seem like you can write code 
        to answer the question, then return "I don't know" as the answer."""
        

    def get_row_column_names(self) -> str:
        """
        Returns the row and column names of pandas dataframes.

        Returns:
            The row and column names of the data tables contained in a prompt.
        """
        if isinstance(self.data, pd.DataFrame):
            prompt = """You are working with one pandas dataframe in Python. The
            names of the columns are, in this order: \n"""
            column_names = ', '.join(map(str, self.data.columns.tolist()))
            row_names = ', '.join(map(str, self.data.index.tolist()))
            prompt += column_names + "\n"
            prompt += "The names of the rows are, in this order: \n"
            prompt += row_names + "\n"
        else:
            count = 1
            num = len(self.data)
            prompt = f"""You are working with {num} pandas dataframes in Python,
            named df1, df2, and so on. """
            for table in self.data:
                prompt += f"The names of the columns of df{count} are, in this order: \n"
                column_names = ', '.join(map(str,table.columns.tolist()))
                prompt += column_names + "\n"
                prompt += f"The names of the rows of df{count} are, in this order: \n"
                row_names = ', '.join(map(str,table.index.tolist())) + "\n"
                prompt += row_names + "\n"
                count +=1
        return prompt
    
    @sk_function(
        description="""Answer a query about the data that does not require 
        data transformation or plotting.""",
        name="query",
        input_description="The question to ask the LLM",
    )
    async def query_async(self, ask: str) -> str:
        """
        Answer a query about the data.

        Args:
            ask -- The question to ask the LLM
        """
        prompt = self._prefix + """You need to write python code that the user can 
        run on their dataframes to answer the question.""" + self._suffix
        pass

    @sk_function(
        description="Transform the data in the pandas dataframe",
        name="transform",
        input_description="The transformation to apply to the data",
    )
    async def transform_async(self, ask: str) -> pd.DataFrame:
        """
        Transform the data in the pandas dataframe.

        Args:
            ask -- The transformation to apply to the data
        """
        prompt = self._prefix + """You need to write python code that will 
        transform the dataframe as the user asked. """ + self._suffix
        pass

    @sk_function(
        description="Plot the data in the pandas dataframe",
        name="plot",
        input_description="The description of the plot to generate",
    )
    async def plot_async(self, ask: str):
        """
        Plot the data in the pandas dataframe.

        Args:
            ask -- The description of the plot to generate
        """
        prompt = self._prefix + """You need to write python code that will plot 
        the data as the user asked. You need to import matplotlib and use nothing
        else for plotting. """ + self._suffix
        pass

    


    


    

    
