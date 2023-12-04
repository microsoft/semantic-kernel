// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.AI.TextGeneration;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextGeneration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.HuggingFace.TextGeneration;

/// <summary>
/// Integration tests for <see cref="HuggingFaceTextGeneration"/>.
/// </summary>
public sealed class HuggingFaceTextGenerationTests
{
    private const string Endpoint = "http://localhost:5000/completions";
    private const string Model = "gpt2";

    private readonly IConfigurationRoot _configuration;

    public HuggingFaceTextGenerationTests()
    {
        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .Build();
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task HuggingFaceLocalAndRemoteTextGenerationAsync()
    {
        // Arrange
        const string Input = "This is test";

        var huggingFaceLocal = new HuggingFaceTextGeneration(Model, endpoint: Endpoint);
        var huggingFaceRemote = new HuggingFaceTextGeneration(Model, apiKey: this.GetApiKey());

        // Act
        var localResponse = await huggingFaceLocal.CompleteAsync(Input);
        var remoteResponse = await huggingFaceRemote.CompleteAsync(Input);

        // Assert
        Assert.NotNull(localResponse);
        Assert.NotNull(remoteResponse);

        Assert.StartsWith(Input, localResponse, StringComparison.Ordinal);
        Assert.StartsWith(Input, remoteResponse, StringComparison.Ordinal);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task RemoteHuggingFaceTextGenerationWithCustomHttpClientAsync()
    {
        // Arrange
        const string Input = "This is test";

        using var httpClient = new HttpClient();
        httpClient.BaseAddress = new Uri("https://api-inference.huggingface.co/models");

        var huggingFaceRemote = new HuggingFaceTextGeneration(Model, apiKey: this.GetApiKey(), httpClient: httpClient);

        // Act
        var remoteResponse = await huggingFaceRemote.CompleteAsync(Input);

        // Assert
        Assert.NotNull(remoteResponse);

        Assert.StartsWith(Input, remoteResponse, StringComparison.Ordinal);
    }

    private string GetApiKey()
    {
        return this._configuration.GetSection("HuggingFace:ApiKey").Get<string>()!;
    }
}
