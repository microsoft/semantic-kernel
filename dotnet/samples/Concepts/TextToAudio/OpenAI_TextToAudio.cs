// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextToAudio;

namespace TextToAudio;

/// <summary>
/// Represents a class that demonstrates audio processing functionality.
/// </summary>
public sealed class OpenAI_TextToAudio(ITestOutputHelper output) : BaseTest(output)
{
    private const string TextToAudioModel = "tts-1";

    [Fact(Skip = "Uncomment the line to write the audio file output before running this test.")]
    public async Task TextToAudioAsync()
    {
        // Create a kernel with OpenAI text to audio service
        var kernel = Kernel.CreateBuilder()
            .AddOpenAITextToAudio(
                modelId: TextToAudioModel,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var textToAudioService = kernel.GetRequiredService<ITextToAudioService>();

        string sampleText = "Hello, my name is John. I am a software engineer. I am working on a project to convert text to audio.";

        // Set execution settings (optional)
        OpenAITextToAudioExecutionSettings executionSettings = new()
        {
            Voice = "alloy", // The voice to use when generating the audio.
                             // Supported voices are alloy, echo, fable, onyx, nova, and shimmer.
            ResponseFormat = "mp3", // The format to audio in.
                                    // Supported formats are mp3, opus, aac, and flac.
            Speed = 1.0f // The speed of the generated audio.
                         // Select a value from 0.25 to 4.0. 1.0 is the default.
        };

        // Convert text to audio
        AudioContent audioContent = await textToAudioService.GetAudioContentAsync(sampleText, executionSettings);

        // Save audio content to a file
        // await File.WriteAllBytesAsync(AudioFilePath, audioContent.Data!.ToArray());
    }
}
