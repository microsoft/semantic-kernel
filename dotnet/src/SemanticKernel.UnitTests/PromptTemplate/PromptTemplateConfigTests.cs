// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
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
        var settings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(configPayload);

        // Assert
        Assert.NotNull(settings);
        Assert.NotNull(settings.ChatSystemPrompt);
        Assert.Equal("Assistant is a large language model.", settings.ChatSystemPrompt);
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
        var settings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(configPayload);

        // Assert
        Assert.NotNull(settings);
        Assert.NotNull(settings.ChatSystemPrompt);
        Assert.Equal("I am a prompt", settings.ChatSystemPrompt);
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
}";

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
}";

        // Act
        var promptTemplateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.NotNull(promptTemplateConfig.ExecutionSettings?.FirstOrDefault<PromptExecutionSettings>());
        Assert.Equal("gpt-4", promptTemplateConfig?.ExecutionSettings.FirstOrDefault<PromptExecutionSettings>()?.ModelId);
    }

    [Fact]
    public void DeserializingExpectInputVariables()
    {
        // Arrange
        string configPayload = @"
{
  ""description"": ""function description"",
  ""input_variables"":
    [
        {
            ""name"": ""input variable name"",
            ""description"": ""input variable description"",
            ""default"": ""default value"",
            ""is_required"": true
        }
    ]
}";

        // Act
        var promptTemplateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.NotNull(promptTemplateConfig.InputVariables);
        Assert.Single(promptTemplateConfig.InputVariables);
        Assert.Equal("input variable name", promptTemplateConfig.InputVariables[0].Name);
        Assert.Equal("input variable description", promptTemplateConfig.InputVariables[0].Description);
        Assert.Equal("default value", promptTemplateConfig.InputVariables[0].Default);
        Assert.True(promptTemplateConfig.InputVariables[0].IsRequired);
    }

    [Fact]
    public void DeserializingExpectOutputVariable()
    {
        // Arrange
        string configPayload = @"
{
  ""description"": ""function description"",
  ""output_variable"": 
    {
        ""description"": ""output variable description""
    }
}";

        // Act
        var promptTemplateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(promptTemplateConfig);
        Assert.NotNull(promptTemplateConfig.OutputVariable);
        Assert.Equal("output variable description", promptTemplateConfig.OutputVariable.Description);
    }
}
