// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Resources;

namespace AudioToText;

/// <summary>
/// Represents a class that demonstrates audio processing functionality.
/// </summary>
public sealed class OpenAI_AudioToText(ITestOutputHelper output) : BaseTest(output)
{
    private const string AudioToTextModel = "whisper-1";
    private const string AudioFilename = "test_audio.wav";

    [Fact(Skip = "Setup and run TextToAudioAsync before running this test.")]
    public async Task AudioToTextAsync()
    {
        // Create a kernel with OpenAI audio to text service
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIAudioToText(
                modelId: AudioToTextModel,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var audioToTextService = kernel.GetRequiredService<IAudioToTextService>();

        // Set execution settings (optional)
        OpenAIAudioToTextExecutionSettings executionSettings = new(AudioFilename)
        {
            Language = "en", // The language of the audio data as two-letter ISO-639-1 language code (e.g. 'en' or 'es').
            Prompt = "sample prompt", // An optional text to guide the model's style or continue a previous audio segment.
                                      // The prompt should match the audio language.
            ResponseFormat = "json", // The format to return the transcribed text in.
                                     // Supported formats are json, text, srt, verbose_json, or vtt. Default is 'json'.
            Temperature = 0.3f, // The randomness of the generated text.
                                // Select a value from 0.0 to 1.0. 0 is the default.
        };

        // Read audio content from a file
        await using var audioFileStream = EmbeddedResource.ReadStream(AudioFilename);
        var audioFileBinaryData = await BinaryData.FromStreamAsync(audioFileStream!);
        AudioContent audioContent = new(audioFileBinaryData, mimeType: null);

        // Convert audio to text
        var textContent = await audioToTextService.GetTextContentAsync(audioContent, executionSettings);

        // Output the transcribed text
        Console.WriteLine(textContent.Text);
    }
}
