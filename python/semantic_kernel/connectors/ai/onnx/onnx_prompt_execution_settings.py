# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class OnnxPromptExecutionSettings(PromptExecutionSettings):
    """Onnx prompt execution settings."""

    diversity_penalty: float = 0.0
    do_sample: bool = False
    early_stopping: bool = True
    length_penalty: float = 1.0
    max_length: int = 4096
    min_length: int = 0
    no_repeat_ngram_size: int = 0
    num_beams: int = 1
    num_return_sequences: int = 1
    past_present_share_buffer: int = True
    repetition_penalty: float = 1.0
    temperature: float = 1.0
    top_k: int = 1
    top_p: float = 1.0
