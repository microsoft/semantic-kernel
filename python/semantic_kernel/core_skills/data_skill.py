# Copyright (c) Microsoft. All rights reserved.

import json
import pandas as pd
from typing import Union, List


class DataSkill:
    """
    Description: A skill that allows the user to query structured data.

    Usage:
        kernel.import_skill(DataSkill(), skill_name="DataSkill")
    """
    path: Union[str, List[str]]
    data: Union[pd.DataFrame, List[pd.DataFrame]]

    def __init__(self, path: Union[str, List[str]], data: Union[pd.DataFrame, List[pd.DataFrame]]):
        self.path = path
        self.data = data
