// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.SemanticFunctions;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.SemanticFunctions;

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
        var requestSettings = JsonSerializer.Deserialize<OpenAIRequestSettings>(configPayload);

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
        var requestSettings = JsonSerializer.Deserialize<OpenAIRequestSettings>(configPayload);

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
  ""models"": 
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
        Assert.NotNull(promptTemplateConfig.ModelSettings);
        Assert.Equal(2, promptTemplateConfig.ModelSettings.Count);
    }

    [Fact]
    public void DeserializingExpectCompletion()
    {
        // Arrange
        string configPayload = @"
{
  ""schema"": 1,
  ""description"": """",
  ""models"": 
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
#pragma warning disable CS0618 // Ensure backward compatibility
        Assert.NotNull(promptTemplateConfig.Completion);
        Assert.Equal("gpt-4", promptTemplateConfig.Completion.ModelId);
#pragma warning restore CS0618 // Ensure backward compatibility
    }
}
