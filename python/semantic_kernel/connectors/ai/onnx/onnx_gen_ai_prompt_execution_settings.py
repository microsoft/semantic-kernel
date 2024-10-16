# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class OnnxGenAIPromptExecutionSettings(PromptExecutionSettings):
    """OnnxGenAI prompt execution settings."""

    diversity_penalty: float | None = Field(None, ge=0.0, le=1.0)
    do_sample: bool = False
    early_stopping: bool = True
    length_penalty: float | None = Field(None, ge=0.0, le=1.0)
    max_length: int = Field(3072, gt=0)
    min_length: int | None = Field(None, gt=0)
    no_repeat_ngram_size: int = 0
    num_beams: int | None = Field(None, gt=0)
    num_return_sequences: int | None = Field(None, gt=0)
    past_present_share_buffer: int = True
    repetition_penalty: float | None = Field(None, ge=0.0, le=1.0)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    top_k: int | None = Field(None, gt=0)
    top_p: float | None = Field(None, ge=0.0, le=1.0)
