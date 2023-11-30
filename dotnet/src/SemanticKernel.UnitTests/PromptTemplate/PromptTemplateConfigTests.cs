// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Xunit;

namespace SemanticKernel.UnitTests.PromptTemplate;

public class PromptTemplateConfigTests
{
    [Fact]
    public void DeserializingDoNotExpectChatSystemPromptToExist()
    {
        // Arrange
        string configPayload = @"{
            ""max_tokens"": 60,
            ""temperature"": 0.5,
            ""top_p"": 0.0,
            ""presence_penalty"": 0.0,
            ""frequency_penalty"": 0.0
        }";

        // Act
        var requestSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(configPayload);

        // Assert
        Assert.NotNull(requestSettings);
        Assert.NotNull(requestSettings.ChatSystemPrompt);
        Assert.Equal("Assistant is a large language model.", requestSettings.ChatSystemPrompt);
    }

    [Fact]
    public void DeserializingExpectChatSystemPromptToExists()
    {
        // Arrange
        string configPayload = @"{
            ""max_tokens"": 60,
            ""temperature"": 0.5,
            ""top_p"": 0.0,
            ""presence_penalty"": 0.0,
            ""frequency_penalty"": 0.0,
            ""chat_system_prompt"": ""I am a prompt""
        }";

        // Act
        var requestSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(configPayload);

        // Assert
        Assert.NotNull(requestSettings);
        Assert.NotNull(requestSettings.ChatSystemPrompt);
        Assert.Equal("I am a prompt", requestSettings.ChatSystemPrompt);
    }

    [Fact]
    public void DeserializingExpectMultipleModels()
    {
        // Arrange
        string configPayload = @"
{
  ""schema"": 1,
  ""description"": """",
  ""execution_settings"": 
  [
    {
      ""model_id"": ""gpt-4"",
      ""max_tokens"": 200,
      ""temperature"": 0.2,
      ""top_p"": 0.0,
      ""presence_penalty"": 0.0,
      ""frequency_penalty"": 0.0,
      ""stop_sequences"": 
      [
        ""Human"",
        ""AI""
      ]
    },
    {
      ""model_id"": ""gpt-3.5_turbo"",
      ""max_tokens"": 256,
      ""temperature"": 0.3,
      ""top_p"": 0.0,
      ""presence_penalty"": 0.0,
      ""frequency_penalty"": 0.0,
      ""stop_sequences"": 
      [
        ""Human"",
        ""AI""
      ]
    }
  ]
}
        ";

        // Act
        var promptTemplateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.NotNull(promptTemplateConfig.ExecutionSettings);
        Assert.Equal(2, promptTemplateConfig.ExecutionSettings.Count);
    }

    [Fact]
    public void DeserializingExpectCompletion()
    {
        // Arrange
        string configPayload = @"
{
  ""schema"": 1,
  ""description"": """",
  ""execution_settings"": 
  [
    {
      ""model_id"": ""gpt-4"",
      ""max_tokens"": 200,
      ""temperature"": 0.2,
      ""top_p"": 0.0,
      ""presence_penalty"": 0.0,
      ""frequency_penalty"": 0.0,
      ""stop_sequences"": 
      [
        ""Human"",
        ""AI""
      ]
    }
  ]
}
        ";

        // Act
        var promptTemplateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.NotNull(promptTemplateConfig.ExecutionSettings?.FirstOrDefault<PromptExecutionSettings>());
        Assert.Equal("gpt-4", promptTemplateConfig?.ExecutionSettings.FirstOrDefault<PromptExecutionSettings>()?.ModelId);
    }
}
