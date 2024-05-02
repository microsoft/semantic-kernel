// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Net.Http;
using Azure.AI.OpenAI.Assistants;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIAssistantConfiguration"/>.
/// </summary>
public class OpenAIAssistantConfigurationTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void VerifyOpenAIAssistantConfigurationInitialState()
    {
        OpenAIAssistantConfiguration config = new(apiKey: "testkey");

        Assert.Equal("testkey", config.ApiKey);
        Assert.Null(config.Endpoint);
        Assert.Null(config.HttpClient);
        Assert.Null(config.Version);
    }

    /// <summary>
    /// Verify assignment.
    /// </summary>
    [Fact]
    public void VerifyOpenAIAssistantConfigurationAssignment()
    {
        using HttpClient client = new();

        OpenAIAssistantConfiguration config =
            new(apiKey: "testkey", endpoint: "https://localhost")
            {
                HttpClient = client,
                Version = AssistantsClientOptions.ServiceVersion.V2024_02_15_Preview,
            };

        Assert.Equal("testkey", config.ApiKey);
        Assert.Equal("https://localhost", config.Endpoint);
        Assert.NotNull(config.HttpClient);
        Assert.Equal(AssistantsClientOptions.ServiceVersion.V2024_02_15_Preview, config.Version);
    }

    /// <summary>
    /// Verify secure endpoint.
    /// </summary>
    [Fact]
    public void VerifyOpenAIAssistantConfigurationThrows()
    {
        using HttpClient client = new();

        Assert.Throws<ArgumentException>(
            () => new OpenAIAssistantConfiguration(apiKey: "testkey", endpoint: "http://localhost"));
    }
}
