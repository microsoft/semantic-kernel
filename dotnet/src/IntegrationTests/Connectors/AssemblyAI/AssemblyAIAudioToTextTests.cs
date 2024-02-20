// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.AssemblyAI;
using Microsoft.SemanticKernel.Contents;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.AssemblyAI;

public sealed class AssemblyAIAudioToTextTests : IDisposable
{
    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public AssemblyAIAudioToTextTests(ITestOutputHelper output)
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

    // [Fact]
    [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextTestAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        const string Filename = "test_audio.wav";

        var apiKey = this._configuration["AssemblyAI:ApiKey"] ??
                     throw new ArgumentException("'AssemblyAI:ApiKey' configuration is required.");

        var service = new AssemblyAIAudioToTextService(apiKey, httpClient);

        await using Stream audio = File.OpenRead($"./TestData/{Filename}");
        var audioData = await BinaryData.FromStreamAsync(audio);

        // Act
        var result = await service.GetTextContentAsync(new AudioContent(audioData));

        // Assert
        Assert.Equal(
            "The sun rises in the east and sets in the west. This simple fact has been observed by humans for thousands of years.",
            result.Text
        );
    }

    // [Fact]
    [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextWithStreamTestAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        const string Filename = "test_audio.wav";

        var apiKey = this._configuration["AssemblyAI:ApiKey"] ??
                     throw new ArgumentException("'AssemblyAI:ApiKey' configuration is required.");

        var service = new AssemblyAIAudioToTextService(apiKey, httpClient);

        await using Stream audio = File.OpenRead($"./TestData/{Filename}");

        // Act
        var result = await service.GetTextContentAsync(audio);

        // Assert
        Assert.Equal(
            "The sun rises in the east and sets in the west. This simple fact has been observed by humans for thousands of years.",
            result.Text
        );
    }

    // [Fact]
    [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextWithLanguageParamTestAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        const string Filename = "test_audio.wav";

        var apiKey = this._configuration["AssemblyAI:ApiKey"] ??
                     throw new ArgumentException("'AssemblyAI:ApiKey' configuration is required.");

        var service = new AssemblyAIAudioToTextService(apiKey, httpClient);

        await using Stream audio = File.OpenRead($"./TestData/{Filename}");
        var textExecutionSettings = new AssemblyAIAudioToTextExecutionSettings
        {
            ExtensionData = new Dictionary<string, object>
            {
                ["language_code"] = "en_us"
            }
        };

        // Act
        var result = await service.GetTextContentAsync(audio);

        // Assert
        Assert.Equal(
            "The sun rises in the east and sets in the west. This simple fact has been observed by humans for thousands of years.",
            result.Text
        );
    }

    // [Fact]
    [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextWithUnknownParamShouldThrowAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        const string Filename = "test_audio.wav";

        var apiKey = this._configuration["AssemblyAI:ApiKey"] ??
                     throw new ArgumentException("'AssemblyAI:ApiKey' configuration is required.");

        var service = new AssemblyAIAudioToTextService(apiKey, httpClient);

        await using Stream audio = File.OpenRead($"./TestData/{Filename}");
        var textExecutionSettings = new AssemblyAIAudioToTextExecutionSettings
        {
            ExtensionData = new Dictionary<string, object>
            {
                ["unknown_key"] = "unknown_value"
            }
        };

        // Act & Assert
        var exception = await Assert.ThrowsAsync<AssemblyAIApiException>(
            async () => await service.GetTextContentAsync(audio, textExecutionSettings)
        );
        Assert.Equal(
            "Failed to create transcript Reason: Invalid endpoint schema, please refer to documentation for examples.",
            exception.Message
        );
    }

    public void Dispose()
    {
        this._testOutputHelper.Dispose();
    }
}
