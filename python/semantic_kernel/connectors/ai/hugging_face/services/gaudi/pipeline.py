import os
import sys

import torch
from transformers import TextGenerationPipeline

from .config import Config

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


class GaudiTextGenerationPipeline(TextGenerationPipeline):
    def __init__(self, config, logger, warmup_on_init=True):
        """Initialize the GaudiTextGenerationPipeline.
        
        Args:
            config: Config object containing model and generation parameters
            logger: Logger for logging information
            warmup_on_init: Whether to run warmup during initialization
        """
        from .utils import initialize_model

        # Ensure we have a Config object
        if not isinstance(config, Config):
            from .config import dict_to_config
            config = dict_to_config(config)
        
        # Initialize the model directly with the Config object
        self.model, _, self.tokenizer, self.generation_config = initialize_model(config, logger)

        self.task = config.task
        self.device = config.device

        if config.do_sample:
            self.generation_config.temperature = config.temperature
            self.generation_config.top_p = config.top_p

        self.max_padding_length = config.max_input_tokens if config.max_input_tokens > 0 else 100
        self.use_hpu_graphs = config.use_hpu_graphs
        self.profiling_steps = config.profiling_steps
        self.profiling_warmup_steps = config.profiling_warmup_steps
        self.profiling_record_shapes = config.profiling_record_shapes

        if warmup_on_init:
            import habana_frameworks.torch.hpu as torch_hpu

            logger.info("Graph compilation...")

            warmup_prompt = ["Here is my prompt"] * config.batch_size
            for _ in range(config.warmup):
                _ = self(warmup_prompt)
            torch_hpu.synchronize()

    def __call__(self, prompt):
        use_batch = isinstance(prompt, list)

        if use_batch:
            model_inputs = self.tokenizer.batch_encode_plus(
                prompt, return_tensors="pt", max_length=self.max_padding_length, padding="max_length", truncation=True
            )
        else:
            model_inputs = self.tokenizer.encode_plus(
                prompt, return_tensors="pt", max_length=self.max_padding_length, padding="max_length", truncation=True
            )

        for t in model_inputs:
            if torch.is_tensor(model_inputs[t]):
                model_inputs[t] = model_inputs[t].to(self.device)

        output = self.model.generate(
            **model_inputs,
            generation_config=self.generation_config,
            lazy_mode=True,
            hpu_graphs=self.use_hpu_graphs,
            profiling_steps=self.profiling_steps,
            profiling_warmup_steps=self.profiling_warmup_steps,
            profiling_record_shapes=self.profiling_record_shapes,
        ).cpu()

        if use_batch:
            output_text = self.tokenizer.batch_decode(output, skip_special_tokens=True)
        else:
            output_text = self.tokenizer.decode(output[0], skip_special_tokens=True)

        return output_text
