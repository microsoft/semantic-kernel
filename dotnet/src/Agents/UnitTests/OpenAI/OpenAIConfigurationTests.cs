// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Net.Http;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIConfiguration"/>.
/// </summary>
public class OpenAIConfigurationTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void VerifyOpenAIAssistantConfigurationInitialState()
    {
        OpenAIConfiguration config = OpenAIConfiguration.ForOpenAI(apiKey: "testkey");

        Assert.Equal("testkey", config.ApiKey);
        Assert.Null(config.Endpoint);
        Assert.Null(config.HttpClient);
    }

    /// <summary>
    /// Verify assignment.
    /// </summary>
    [Fact]
    public void VerifyOpenAIAssistantConfigurationAssignment()
    {
        using HttpClient client = new();

        OpenAIConfiguration config = OpenAIConfiguration.ForOpenAI(apiKey: "testkey", endpoint: new Uri("https://localhost"), client);

        Assert.Equal("testkey", config.ApiKey);
        Assert.NotNull(config.Endpoint);
        Assert.Equal("https://localhost/", config.Endpoint.ToString());
        Assert.NotNull(config.HttpClient);
    }

    // %%% MORE
}
