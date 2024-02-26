// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextToAudio;
using Resources;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Represents a class that demonstrates audio processing functionality.
/// </summary>
public sealed class Example82_Audio : BaseTest
{
    private const string TextToAudioModel = "tts-1";
    private const string AudioToTextModel = "whisper-1";
    private const string AudioFilename = "test_audio.wav";

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
        AudioContent audioContent = new(audioFileBinaryData);

        // Convert audio to text
        var textContent = await audioToTextService.GetTextContentAsync(audioContent, executionSettings);

        // Output the transcribed text
        this.WriteLine(textContent.Text);
    }

    public Example82_Audio(ITestOutputHelper output) : base(output) { }
}
