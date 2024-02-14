// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Contents;
using Microsoft.SemanticKernel.TextToAudio;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Represents a class that demonstrates audio processing functionality.
/// </summary>
public sealed class Example28_Audio : BaseTest
{
    private const string TextToAudioModel = "tts-1";
    private const string AudioToTextModel = "whisper-1";
    private const string AudioFilePath = "input.wav";

    [Fact(Skip = "Needs setup.")]
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

        // Convert text to audio
        AudioContent audioContent = await textToAudioService.GetAudioContentAsync(sampleText);

        // Save audio content to a file
        // await File.WriteAllBytesAsync("output.wav", audioContent.Data.ToArray());
    }

    [Fact(Skip = "Setup audio file input before running this test.")]
    public async Task AudioToTextAsync()
    {
        // Create a kernel with OpenAI audio to text service
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIAudioToText(
                modelId: AudioToTextModel,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var audioToTextService = kernel.GetRequiredService<IAudioToTextService>();

        // Read audio content from a file
        ReadOnlyMemory<byte> audioData = await File.ReadAllBytesAsync(AudioFilePath);
        AudioContent audioContent = new(new BinaryData(audioData));

        // Convert audio to text
        var textContent = await audioToTextService.GetTextContentAsync(audioContent);

        // Output the transcribed text
        this.WriteLine(textContent.Text);
    }

    public Example28_Audio(ITestOutputHelper output) : base(output) { }
}
