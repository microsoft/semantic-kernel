# Copyright (c) Microsoft. All rights reserved.

from transformers import AutoModelForCausalLM, AutoTokenizer

from . import InferenceGenerator

# The model used to get the tokenizer can be a little arbitrary
# since the tokenizers are common within the same model type


class CompletionGenerator(InferenceGenerator.InferenceGenerator):
    def __init__(self, model_name):
        super().__init__(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

    def perform_inference(self, prompt, context, max_tokens):
        model = AutoModelForCausalLM.from_pretrained(self.model_name, is_decoder=True)
        model.to(self.device)

        encodings = self.tokenizer.encode_plus(
            text=prompt, text_pair=context, truncation=True, return_tensors="pt"
        )

        generated_ids = model.generate(
            encodings.input_ids,
            max_length=max_tokens,
            # num_beams = 5,
            # temperature = 0.8,
            no_repeat_ngram_size=4,
            early_stopping=True,
        )

        return (
            self.tokenizer.decode(generated_ids[0]),
            encodings.input_ids.numel(),
            len(generated_ids[0]),
        )
