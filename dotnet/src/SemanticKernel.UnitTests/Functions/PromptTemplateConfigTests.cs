// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

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
}
