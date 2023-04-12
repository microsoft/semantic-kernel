# Copyright (c) Microsoft. All rights reserved.

import torch
from transformers import AutoModel, AutoTokenizer

from . import InferenceGenerator


class EmbeddingGenerator(InferenceGenerator.InferenceGenerator):
    def __init__(self, model_name):
        super().__init__(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[
            0
        ]  # First element of model_output contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).float()
        x = torch.sum(token_embeddings * input_mask_expanded, 1)
        y = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return x / y

    def perform_inference(self, sentences):
        model = AutoModel.from_pretrained(self.model_name)
        model.to(self.device)

        encodings = self.tokenizer(
            sentences, padding=True, truncation=True, return_tensors="pt"
        )

        model_output = model(**encodings)
        embeddings = self._mean_pooling(model_output, encodings["attention_mask"])
        return embeddings, encodings.input_ids.numel()
