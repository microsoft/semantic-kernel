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

    def __init__(self, path: Union[str, List[str]]=None, data: Union[pd.DataFrame, List[pd.DataFrame]]=None):
        self.data = data
        self.path = path
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

    


    


    

    
