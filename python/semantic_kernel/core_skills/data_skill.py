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
                self.data = pd.read_csv(self.path)
        if isinstance(self.path, List):
            if self.data is None: self.data = []
            for file in self.path:
                if not file.endswith(".csv"):
                    raise ValueError("File path must be to a CSV file")
                else:
                    self.data.append(pd.read_csv(file))

    def get_row_column_names(self) -> str:
        """
        Returns the column names of the data table.

        Args:
            context: Contains the data table

        Returns:
            The column names of the data table
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

    


    


    

    
