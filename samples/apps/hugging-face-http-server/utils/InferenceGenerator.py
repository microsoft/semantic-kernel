# Copyright (c) Microsoft. All rights reserved.

import os

import torch

# The model used to get the tokenizer can be a little arbitrary
# since the tokenizers are common within the same model type


class InferenceGenerator:
    def __init__(self, model_name):
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
