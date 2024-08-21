# Copyright (c) Microsoft. All rights reserved.
import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from semantic_kernel.connectors.ai.onnx import OnnxGenAIPromptExecutionSettings, OnnxGenAITextCompletion
from semantic_kernel.contents import TextContent
from semantic_kernel.exceptions import ServiceInitializationError


def test_onnx_chat_completion_with_invalid_model():
    with pytest.raises(ServiceInitializationError):
        OnnxGenAITextCompletion(ai_model_path="/invalid_path")
    

gen_ai_config = {
    "model": {
        "test": "test"
    }
}

gen_ai_config_vision = {
    "model": {
        "vision": "test"
    }
}
        

@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch('onnxruntime_genai.Model')
@patch('onnxruntime_genai.Tokenizer')
@pytest.mark.asyncio
async def test_onnx_text_completion(gen_ai_config, model, tokenizer):
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = ['H', 'e', 'l', 'l', 'o']
    
    text_completion = OnnxGenAITextCompletion(ai_model_path="test")
    with patch.object(
        text_completion,
        '_generate_next_token',
        return_value=generator_mock
        ):
        completed_text: TextContent = await text_completion.get_text_content(
            prompt="test",
            settings=OnnxGenAIPromptExecutionSettings()
        )
        
    assert completed_text.text == 'Hello'
    

@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch('onnxruntime_genai.Model')
@patch('onnxruntime_genai.Tokenizer')
@pytest.mark.asyncio
async def test_onnx_text_completion_streaming(gen_ai_config, model, tokenizer):
    
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = ['H', 'e', 'l', 'l', 'o']
    
    text_completion = OnnxGenAITextCompletion(ai_model_path="test")
    completed_text: str = ""
    with patch.object(
        text_completion,
        '_generate_next_token',
        return_value=generator_mock
        ):
        async for chunk in text_completion.get_streaming_text_content(
            prompt="test",
            settings=OnnxGenAIPromptExecutionSettings()
        ):
            completed_text += chunk.text
        
    assert completed_text == 'Hello'
