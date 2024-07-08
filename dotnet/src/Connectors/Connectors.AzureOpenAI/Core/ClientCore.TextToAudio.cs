// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using OpenAI.Audio;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with Azure OpenAI services.
/// </summary>
internal partial class ClientCore
{
    /// <summary>
    /// Generates an image with the provided configuration.
    /// </summary>
    /// <param name="prompt">Prompt to generate the image</param>
    /// <param name="executionSettings">Text to Audio execution settings for the prompt</param>
    /// <param name="modelId">Azure OpenAI model id</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Url of the generated image</returns>
    internal async Task<IReadOnlyList<AudioContent>> GetAudioContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        string? modelId,
        CancellationToken cancellationToken)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        AzureOpenAITextToAudioExecutionSettings audioExecutionSettings = AzureOpenAITextToAudioExecutionSettings.FromExecutionSettings(executionSettings);

        var (responseFormat, mimeType) = GetGeneratedSpeechFormatAndMimeType(audioExecutionSettings.ResponseFormat);

        SpeechGenerationOptions options = new()
        {
            ResponseFormat = responseFormat,
            Speed = audioExecutionSettings.Speed,
        };

        var deploymentOrModel = this.GetModelId(audioExecutionSettings, modelId);

        ClientResult<BinaryData> response = await RunRequestAsync(() => this.Client.GetAudioClient(deploymentOrModel).GenerateSpeechFromTextAsync(prompt, GetGeneratedSpeechVoice(audioExecutionSettings?.Voice), options, cancellationToken)).ConfigureAwait(false);

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

    private static (GeneratedSpeechFormat Format, string MimeType) GetGeneratedSpeechFormatAndMimeType(string? format)
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

    private string GetModelId(AzureOpenAITextToAudioExecutionSettings executionSettings, string? modelId)
    {
        return
            !string.IsNullOrWhiteSpace(modelId) ? modelId! :
            !string.IsNullOrWhiteSpace(executionSettings.ModelId) ? executionSettings.ModelId! :
            this.DeploymentNameOrModelId;
    }
}
