// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.HuggingFace.TextGeneration;

/// <summary>
/// Integration tests for <see cref="HuggingFaceTextGenerationService"/>.
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

        var huggingFaceLocal = new HuggingFaceTextGenerationService(Model, endpoint: Endpoint);
        var huggingFaceRemote = new HuggingFaceTextGenerationService(Model, apiKey: this.GetApiKey());

        // Act
        var localResponse = await huggingFaceLocal.GetTextContentAsync(Input);
        var remoteResponse = await huggingFaceRemote.GetTextContentAsync(Input);

        // Assert
        Assert.NotNull(localResponse.Text);
        Assert.NotNull(remoteResponse.Text);

        Assert.StartsWith(Input, localResponse.Text, StringComparison.Ordinal);
        Assert.StartsWith(Input, remoteResponse.Text, StringComparison.Ordinal);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task RemoteHuggingFaceTextGenerationWithCustomHttpClientAsync()
    {
        // Arrange
        const string Input = "This is test";

        using var httpClient = new HttpClient();
        httpClient.BaseAddress = new Uri("https://api-inference.huggingface.co/models");

        var huggingFaceRemote = new HuggingFaceTextGenerationService(Model, apiKey: this.GetApiKey(), httpClient: httpClient);

        // Act
        var remoteResponse = await huggingFaceRemote.GetTextContentAsync(Input);

        // Assert
        Assert.NotNull(remoteResponse.Text);

        Assert.StartsWith(Input, remoteResponse.Text, StringComparison.Ordinal);
    }

    private string GetApiKey()
    {
        return this._configuration.GetSection("HuggingFace:ApiKey").Get<string>()!;
    }
}
