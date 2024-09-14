// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AssemblyAI;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.AssemblyAI;

public sealed class AssemblyAIFilesTests : IDisposable
{
    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public AssemblyAIFilesTests(ITestOutputHelper output)
    {
        this._testOutputHelper = new RedirectOutput(output);
        Console.SetOut(this._testOutputHelper);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<AssemblyAIAudioToTextTests>()
            .Build();
    }

    [Fact]
    // [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextTestAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        const string Filename = "test_audio.wav";

        string apiKey = this.GetAssemblyAIApiKey();

        var service = new AssemblyAIFileService(apiKey, httpClient: httpClient);

        await using Stream audio = File.OpenRead($"./TestData/{Filename}");

        // Act
        var result = await service.UploadAsync(audio);

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Uri);
        Assert.Null(result.Data);
    }

    private string GetAssemblyAIApiKey()
    {
        var apiKey = this._configuration["AssemblyAI:ApiKey"];
        if (string.IsNullOrEmpty(apiKey))
        {
            throw new ArgumentException("'AssemblyAI:ApiKey' configuration is required.");
        }

        return apiKey;
    }

    [Fact]
    // [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextWithLocalhostBaseAddressShouldThrowAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        httpClient.BaseAddress = new Uri("https://localhost:9999");
        const string Filename = "test_audio.wav";

        var apiKey = this.GetAssemblyAIApiKey();

        var service = new AssemblyAIFileService(apiKey, httpClient: httpClient);

        await using Stream audio = File.OpenRead($"./TestData/{Filename}");

        // Act & Assert
        var exception = await Assert.ThrowsAsync<HttpOperationException>(
            async () => await service.UploadAsync(audio)
        );
        Assert.Equal(
            "Connection refused (localhost:9999)",
            exception.Message
        );
    }

    public void Dispose()
    {
        this._testOutputHelper.Dispose();
    }
}
