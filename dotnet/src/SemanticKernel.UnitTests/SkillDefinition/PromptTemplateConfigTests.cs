// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.SemanticFunctions;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public class PromptTemplateConfigTests
{
    [Fact]
    public void DeserializingDontExpectChatSystemPromptToExists()
    {
        // Arrange
        string configPayload = @"{
          ""schema"": 1,
          ""description"": ""Turn a scenario into a creative or humorous excuse to send your boss"",
          ""type"": ""completion"",
          ""completion"": {
            ""max_tokens"": 60,
            ""temperature"": 0.5,
            ""top_p"": 0.0,
            ""presence_penalty"": 0.0,
            ""frequency_penalty"": 0.0
          }
        }";

        // Act
        var templateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(templateConfig);
        Assert.Null(templateConfig.Completion.ChatSystemPrompt);
    }

    [Fact]
    public void DeserializingExpectChatSystemPromptToExists()
    {
        // Arrange
        string configPayload = @"{
          ""schema"": 1,
          ""description"": ""Turn a scenario into a creative or humorous excuse to send your boss"",
          ""type"": ""completion"",
          ""completion"": {
            ""max_tokens"": 60,
            ""temperature"": 0.5,
            ""top_p"": 0.0,
            ""presence_penalty"": 0.0,
            ""frequency_penalty"": 0.0,
            ""chat_system_prompt"": ""I am a prompt""
          }
        }";

        // Act
        var templateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);

        // Assert
        Assert.NotNull(templateConfig);
        Assert.NotNull(templateConfig.Completion.ChatSystemPrompt);
        Assert.Equal("I am a prompt", templateConfig.Completion.ChatSystemPrompt);
    }
}
