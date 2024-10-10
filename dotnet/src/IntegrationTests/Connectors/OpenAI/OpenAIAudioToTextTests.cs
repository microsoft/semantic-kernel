<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

public sealed class OpenAIAudioToTextTests()
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OpenAIAudioToTextTests>()
        .Build();

    [RetryFact]//(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    public async Task OpenAIAudioToTextTestAsync()
    {
        // Arrange
        const string Filename = "test_audio.wav";

        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAIAudioToText").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIAudioToText(openAIConfiguration.ModelId, openAIConfiguration.ApiKey)
            .Build();

        var service = kernel.GetRequiredService<IAudioToTextService>();

        await using Stream audio = File.OpenRead($"./TestData/{Filename}");
        var audioData = await BinaryData.FromStreamAsync(audio);

        // Act
        var result = await service.GetTextContentAsync(
            new AudioContent(audioData, mimeType: "audio/wav"), 
            new OpenAIAudioToTextExecutionSettings(Filename)
        );
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        var result = await service.GetTextContentAsync(new AudioContent(audioData, mimeType: "audio/wav"), new OpenAIAudioToTextExecutionSettings(Filename));
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        var result = await service.GetTextContentAsync(new AudioContent(audioData, mimeType: "audio/wav"), new OpenAIAudioToTextExecutionSettings(Filename));
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
        var result = await service.GetTextContentAsync(new AudioContent(audioData, mimeType: "audio/wav"), new OpenAIAudioToTextExecutionSettings(Filename));
>>>>>>> main
>>>>>>> Stashed changes

        // Assert
        Assert.Contains("The sun rises in the east and sets in the west.", result.Text, StringComparison.OrdinalIgnoreCase);
    }
}
