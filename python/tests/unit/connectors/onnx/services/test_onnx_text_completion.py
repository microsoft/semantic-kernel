# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import MagicMock, patch

import pytest

from semantic_kernel.connectors.ai.onnx import OnnxTextCompletion, OnnxTextPromptExecutionSettings
from semantic_kernel.contents import TextContent
from semantic_kernel.exceptions import ServiceInitializationError


def test_onnx_chat_completion_with_invalid_model():
    with pytest.raises(ServiceInitializationError):
        OnnxTextCompletion(ai_model_path="/invalid_path")
        

@patch('onnxruntime_genai.Model')
@patch('onnxruntime_genai.Tokenizer')
@pytest.mark.asyncio
async def test_onnx_text_completion(model, tokenizer):
    
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = ['H', 'e', 'l', 'l', 'o']
    
    text_completion = OnnxTextCompletion(ai_model_path="test")
    with patch.object(
        text_completion,
        '_generate_next_token',
        return_value=generator_mock
        ):
        completed_text: TextContent = await text_completion.get_text_content(
            prompt="test",
            settings=OnnxTextPromptExecutionSettings()
        )
        
    assert completed_text.text == 'Hello'
    

@patch('onnxruntime_genai.Model')
@patch('onnxruntime_genai.Tokenizer')
@pytest.mark.asyncio
async def test_onnx_text_completion_streaming(model, tokenizer):
    
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = ['H', 'e', 'l', 'l', 'o']
    
    text_completion = OnnxTextCompletion(ai_model_path="test")
    completed_text: str = ""
    with patch.object(
        text_completion,
        '_generate_next_token',
        return_value=generator_mock
        ):
        async for chunk in text_completion.get_streaming_text_content(
            prompt="test",
            settings=OnnxTextPromptExecutionSettings()
        ):
            completed_text += chunk.text
        
    assert completed_text == 'Hello'
