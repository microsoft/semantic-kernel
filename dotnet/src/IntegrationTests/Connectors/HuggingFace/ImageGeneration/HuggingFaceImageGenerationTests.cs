// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.ImageGeneration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.HuggingFace.ImageGeneration;

/// <summary>
/// Integration tests for <see cref="HuggingFaceImageGeneration"/>.
/// </summary>
public class HuggingFaceImageGenerationTests
{
    private const string Model = "runwayml/stable-diffusion-v1-5";

    private readonly IConfigurationRoot _configuration;

    public HuggingFaceImageGenerationTests()
    {
        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .Build();
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task RemoteHuggingFaceTextCompletionWithCustomHttpClientAsync()
    {
        // Arrange
        const string Input = "Comic strip about dogs";

        using var httpClient = new HttpClient();
        httpClient.BaseAddress = new Uri("https://api-inference.huggingface.co/models");

        var huggingFaceRemote = new HuggingFaceImageGeneration(Model, apiKey: this.GetApiKey(), httpClient: httpClient);

        // Act
        var remoteResponse = await huggingFaceRemote.GenerateImageAsync(Input, 256, 256);

        // Assert
        Assert.NotNull(remoteResponse);

        Assert.StartsWith(Input, remoteResponse, StringComparison.Ordinal);
        Assert.True(remoteResponse.Length > Input.Length);
    }

    private string GetApiKey()
    {
        return this._configuration.GetSection("HuggingFace:ApiKey").Get<string>()!;
    }
}
