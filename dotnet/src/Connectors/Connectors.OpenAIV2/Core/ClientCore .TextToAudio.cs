// Copyright (c) Microsoft. All rights reserved.

/* 
Phase 02

- This class was created focused in the Image Generation using the SDK client instead of the own client in V1.
- Added Checking for empty or whitespace prompt.
- Removed the format parameter as this is never called in V1 code. Plan to implement it in the future once we change the ITextToImageService abstraction, using PromptExecutionSettings.
- Allow custom size for images when the endpoint is not the default OpenAI v1 endpoint.
*/

using System;
using System.ClientModel;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using OpenAI.Audio;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with OpenAI services.
/// </summary>
internal partial class ClientCore
{
    /// <summary>
    /// Generates an image with the provided configuration.
    /// </summary>
    /// <param name="prompt">Prompt to generate the image</param>
    /// <param name="executionSettings">Text to Audio execution settings for the prompt</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Url of the generated image</returns>
    internal async Task<IReadOnlyList<AudioContent>> GetAudioContentAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        OpenAITextToAudioExecutionSettings? audioExecutionSettings = OpenAITextToAudioExecutionSettings.FromExecutionSettings(executionSettings);
        var (responseFormat, mimeType) = GetGeneratedSpeechFormatAndMimeType(audioExecutionSettings?.ResponseFormat);
        SpeechGenerationOptions options = new()
        {
            ResponseFormat = responseFormat,
            Speed = audioExecutionSettings?.Speed,
        };

        ClientResult<BinaryData> response = await RunRequestAsync(() => this.Client.GetAudioClient(this.ModelId).GenerateSpeechFromTextAsync(prompt, GetGeneratedSpeechVoice(audioExecutionSettings?.Voice), options, cancellationToken)).ConfigureAwait(false);

        return [new AudioContent(response.Value.ToArray(), mimeType)];
    }

    private static GeneratedSpeechVoice GetGeneratedSpeechVoice(string? voice)
        => voice?.ToUpperInvariant() switch
        {
            "ALLOY" => GeneratedSpeechVoice.Alloy,
            "ECHO" => GeneratedSpeechVoice.Echo,
            "FABLE" => GeneratedSpeechVoice.Fable,
            "ONYX" => GeneratedSpeechVoice.Onyx,
            "NOVA" => GeneratedSpeechVoice.Nova,
            "SHIMMER" => GeneratedSpeechVoice.Shimmer,
            _ => throw new NotSupportedException($"The voice '{voice}' is not supported."),
        };

    private static (GeneratedSpeechFormat, string) GetGeneratedSpeechFormatAndMimeType(string? format)
        => format?.ToUpperInvariant() switch
        {
            "WAV" => (GeneratedSpeechFormat.Wav, "audio/wav"),
            "MP3" => (GeneratedSpeechFormat.Mp3, "audio/mpeg"),
            "OPUS" => (GeneratedSpeechFormat.Opus, "audio/opus"),
            "FLAC" => (GeneratedSpeechFormat.Flac, "audio/flac"),
            "AAC" => (GeneratedSpeechFormat.Aac, "audio/aac"),
            "PCM" => (GeneratedSpeechFormat.Pcm, "audio/l16"),
            _ => throw new NotSupportedException($"The format '{format}' is not supported.")
        };
}
