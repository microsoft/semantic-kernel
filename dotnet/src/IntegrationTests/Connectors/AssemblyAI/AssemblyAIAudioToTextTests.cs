// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AssemblyAI;
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

    [Fact]
    // [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextTestAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        const string Filename = "test_audio.wav";

        string apiKey = this.GetAssemblyAIApiKey();

        var service = new AssemblyAIAudioToTextService(apiKey, httpClient: httpClient);

        await using Stream audio = File.OpenRead($"./TestData/{Filename}");
        var audioData = await BinaryData.FromStreamAsync(audio);

        // Act
        var result = await service.GetTextContentsAsync(new AudioContent(audioData));

        // Assert
        Console.WriteLine(result[0].Text);
        Assert.Contains("The sun rises in the east and sets in the west.", result[0].Text, StringComparison.OrdinalIgnoreCase);
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
    public async Task AssemblyAIAudioToTextWithPollingIntervalTestAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        const string Filename = "test_audio.wav";

        var apiKey = this.GetAssemblyAIApiKey();

        var service = new AssemblyAIAudioToTextService(apiKey, httpClient: httpClient);

        await using Stream audio = File.OpenRead($"./TestData/{Filename}");
        var audioData = await BinaryData.FromStreamAsync(audio);

        // Act
        var result = await service.GetTextContentsAsync(
            new AudioContent(audioData),
            new AssemblyAIAudioToTextExecutionSettings
            {
                PollingInterval = TimeSpan.FromMilliseconds(750)
            }
        );

        // Assert
        Console.WriteLine(result[0].Text);
        Assert.Contains("The sun rises in the east and sets in the west.", result[0].Text, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    // [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextWithStreamTestAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        const string Filename = "test_audio.wav";

        var apiKey = this.GetAssemblyAIApiKey();

        var fileService = new AssemblyAIFileService(apiKey, httpClient: httpClient);
        var sttService = new AssemblyAIAudioToTextService(apiKey, httpClient: httpClient);

        await using Stream audioStream = File.OpenRead($"./TestData/{Filename}");
        var audioData = await fileService.UploadAsync(audioStream);
        // Act
        var result = await sttService.GetTextContentsAsync(audioData);

        // Assert
        Console.WriteLine(result[0].Text);
        Assert.Contains("The sun rises in the east and sets in the west.", result[0].Text, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    // [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextWithUriTestAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();

        var apiKey = this.GetAssemblyAIApiKey();

        var service = new AssemblyAIAudioToTextService(apiKey, httpClient: httpClient);

        // Act
        var result = await service.GetTextContentsAsync(
            new AudioContent(new Uri("https://storage.googleapis.com/aai-docs-samples/nbc.mp3"))
        );

        // Assert
        Assert.Contains(
            "There's the traditional red blue divide you're very familiar with. But there's a lot more below the surface going on in both parties. Let's set the table.",
            result[0].Text,
            StringComparison.Ordinal
        );
        Console.WriteLine(result[0].Text);
    }

    [Fact]
    // [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextWithFileUriShouldThrowTestAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();

        var apiKey = this.GetAssemblyAIApiKey();

        var service = new AssemblyAIAudioToTextService(apiKey, httpClient: httpClient);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(
            async () => await service.GetTextContentsAsync(new AudioContent(new Uri("file://C:/file.mp3")))
        );
    }

    [Fact]
    // [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextWithLanguageParamTestAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        const string Filename = "test_audio.wav";

        var apiKey = this.GetAssemblyAIApiKey();

        var fileService = new AssemblyAIFileService(apiKey, httpClient: httpClient);
        var sttService = new AssemblyAIAudioToTextService(apiKey, httpClient: httpClient);

        await using Stream audioStream = File.OpenRead($"./TestData/{Filename}");
        var audioData = await fileService.UploadAsync(audioStream);
        var textExecutionSettings = new PromptExecutionSettings
        {
            ExtensionData = new Dictionary<string, object>
            {
                ["language_code"] = "en_us"
            }
        };

        // Act
        var result = await sttService.GetTextContentsAsync(audioData, textExecutionSettings);

        // Assert
        Console.WriteLine(result[0].Text);
        Assert.Contains("The sun rises in the east and sets in the west.", result[0].Text, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    // [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextWithUnknownParamShouldThrowAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        const string Filename = "test_audio.wav";

        var apiKey = this.GetAssemblyAIApiKey();

        var fileService = new AssemblyAIFileService(apiKey, httpClient: httpClient);
        var sttService = new AssemblyAIAudioToTextService(apiKey, httpClient: httpClient);

        await using Stream audioStream = File.OpenRead($"./TestData/{Filename}");
        var audioData = await fileService.UploadAsync(audioStream);
        var textExecutionSettings = new PromptExecutionSettings
        {
            ExtensionData = new Dictionary<string, object>
            {
                ["unknown_key"] = "unknown_value"
            }
        };

        // Act & Assert
        await Assert.ThrowsAsync<HttpOperationException>(
            async () => await sttService.GetTextContentsAsync(audioData, textExecutionSettings)
        );
    }

    [Fact]
    // [Fact(Skip = "This test is for manual verification.")]
    public async Task AssemblyAIAudioToTextWithLocalhostBaseAddressShouldThrowAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        httpClient.BaseAddress = new Uri("https://localhost:9999");

        var apiKey = this.GetAssemblyAIApiKey();

        var sttService = new AssemblyAIAudioToTextService(apiKey, httpClient: httpClient);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<HttpOperationException>(
            async () => await sttService.GetTextContentsAsync(new AudioContent(new Uri("http://localhost")))
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
