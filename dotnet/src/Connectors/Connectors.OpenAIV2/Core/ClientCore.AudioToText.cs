// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Text;
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
    /// <param name="input">Input audio to generate the text</param>
    /// <param name="executionSettings">Audio-to-text execution settings for the prompt</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Url of the generated image</returns>
    internal async Task<IReadOnlyList<TextContent>> GetTextFromAudioContentsAsync(
        AudioContent input,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken)
    {
        if (!input.CanRead)
        {
            throw new ArgumentException("The input audio content is not readable.", nameof(input));
        }

        OpenAIAudioToTextExecutionSettings? audioExecutionSettings = OpenAIAudioToTextExecutionSettings.FromExecutionSettings(executionSettings);
        AudioTranscriptionOptions? audioOptions = AudioOptionsFromExecutionSettings(executionSettings);

        Verify.ValidFilename(audioExecutionSettings?.Filename);

        var memoryStream = new MemoryStream(input.Data!.Value.ToArray());

        AudioTranscription responseData = (await RunRequestAsync(() => this.Client.GetAudioClient(this.ModelId).TranscribeAudioAsync(memoryStream, audioExecutionSettings?.Filename, audioOptions)).ConfigureAwait(false)).Value;

        return [new(responseData.Text, this.ModelId, metadata: GetResponseMetadata(responseData))];
    }

    /// <summary>
    /// Converts <see cref="PromptExecutionSettings"/> to <see cref="AudioTranscriptionOptions"/> type.
    /// </summary>
    /// <param name="executionSettings">Instance of <see cref="PromptExecutionSettings"/>.</param>
    /// <returns>Instance of <see cref="AudioTranscriptionOptions"/>.</returns>
    private static AudioTranscriptionOptions? AudioOptionsFromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return new AudioTranscriptionOptions();
        }

        if (executionSettings is OpenAIAudioToTextExecutionSettings settings)
        {
            return new AudioTranscriptionOptions
            {
                Granularities = ConvertToAudioTimestampGranularities(settings.Granularities),
                Language = settings.Language,
                Prompt = settings.Prompt,
                Temperature = settings.Temperature
            };
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var openAIExecutionSettings = JsonSerializer.Deserialize<OpenAIAudioToTextExecutionSettings>(json, JsonOptionsCache.ReadPermissive);

        if (openAIExecutionSettings is not null)
        {
            return new AudioTranscriptionOptions
            {
                Granularities = ConvertToAudioTimestampGranularities(openAIExecutionSettings.Granularities),
                Language = openAIExecutionSettings.Language,
                Prompt = openAIExecutionSettings.Prompt,
                Temperature = openAIExecutionSettings.Temperature
            };
        }

        throw new ArgumentException($"Invalid execution settings, cannot convert to {nameof(OpenAIAudioToTextExecutionSettings)}", nameof(executionSettings));
    }

    private static AudioTimestampGranularities ConvertToAudioTimestampGranularities(IEnumerable<OpenAIAudioToTextExecutionSettings.TimeStampGranularities>? granularity)
    {
        return granularity?.FirstOrDefault() switch
        {
            OpenAIAudioToTextExecutionSettings.TimeStampGranularities.Default => AudioTimestampGranularities.Default,
            OpenAIAudioToTextExecutionSettings.TimeStampGranularities.Word => AudioTimestampGranularities.Word,
            OpenAIAudioToTextExecutionSettings.TimeStampGranularities.Segment => AudioTimestampGranularities.Segment,
            _ => AudioTimestampGranularities.Default
        };
    }

    private static Dictionary<string, object?> GetResponseMetadata(AudioTranscription audioTranscription)
        => new(3)
        {
            [nameof(audioTranscription.Language)] = audioTranscription.Language,
            [nameof(audioTranscription.Duration)] = audioTranscription.Duration,
            [nameof(audioTranscription.Segments)] = audioTranscription.Segments
        };
}
