// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
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

        AzureOpenAIAudioToTextExecutionSettings audioExecutionSettings = AzureOpenAIAudioToTextExecutionSettings.FromExecutionSettings(executionSettings)!;
        AudioTranscriptionOptions audioOptions = AudioOptionsFromExecutionSettings(audioExecutionSettings);

        Verify.ValidFilename(audioExecutionSettings?.Filename);

        using var memoryStream = new MemoryStream(input.Data!.Value.ToArray());

        AudioTranscription responseData = (await RunRequestAsync(() => this.Client.GetAudioClient(this.DeploymentName).TranscribeAudioAsync(memoryStream, audioExecutionSettings?.Filename, audioOptions)).ConfigureAwait(false)).Value;

        return [new(responseData.Text, this.DeploymentName, metadata: GetResponseMetadata(responseData))];
    }

    /// <summary>
    /// Converts <see cref="AzureOpenAIAudioToTextExecutionSettings"/> to <see cref="AudioTranscriptionOptions"/> type.
    /// </summary>
    /// <param name="executionSettings">Instance of <see cref="AzureOpenAIAudioToTextExecutionSettings"/>.</param>
    /// <returns>Instance of <see cref="AudioTranscriptionOptions"/>.</returns>
    private static AudioTranscriptionOptions AudioOptionsFromExecutionSettings(AzureOpenAIAudioToTextExecutionSettings executionSettings)
        => new()
        {
            Granularities = ConvertToAudioTimestampGranularities(executionSettings!.Granularities),
            Language = executionSettings.Language,
            Prompt = executionSettings.Prompt,
            Temperature = executionSettings.Temperature,
            ResponseFormat = ConvertResponseFormat(executionSettings.ResponseFormat)
        };

    private static AudioTimestampGranularities ConvertToAudioTimestampGranularities(IEnumerable<AzureOpenAIAudioToTextExecutionSettings.TimeStampGranularities>? granularities)
    {
        AudioTimestampGranularities result = AudioTimestampGranularities.Default;

        if (granularities is not null)
        {
            foreach (var granularity in granularities)
            {
                var openAIGranularity = granularity switch
                {
                    AzureOpenAIAudioToTextExecutionSettings.TimeStampGranularities.Word => AudioTimestampGranularities.Word,
                    AzureOpenAIAudioToTextExecutionSettings.TimeStampGranularities.Segment => AudioTimestampGranularities.Segment,
                    _ => AudioTimestampGranularities.Default
                };

                result |= openAIGranularity;
            }
        }

        return result;
    }

    private static Dictionary<string, object?> GetResponseMetadata(AudioTranscription audioTranscription)
        => new(3)
        {
            [nameof(audioTranscription.Language)] = audioTranscription.Language,
            [nameof(audioTranscription.Duration)] = audioTranscription.Duration,
            [nameof(audioTranscription.Segments)] = audioTranscription.Segments
        };

    private static AudioTranscriptionFormat? ConvertResponseFormat(AzureOpenAIAudioToTextExecutionSettings.AudioTranscriptionFormat? responseFormat)
    {
        if (responseFormat is null)
        {
            return null;
        }

        return responseFormat switch
        {
            AzureOpenAIAudioToTextExecutionSettings.AudioTranscriptionFormat.Simple => AudioTranscriptionFormat.Simple,
            AzureOpenAIAudioToTextExecutionSettings.AudioTranscriptionFormat.Verbose => AudioTranscriptionFormat.Verbose,
            AzureOpenAIAudioToTextExecutionSettings.AudioTranscriptionFormat.Vtt => AudioTranscriptionFormat.Vtt,
            AzureOpenAIAudioToTextExecutionSettings.AudioTranscriptionFormat.Srt => AudioTranscriptionFormat.Srt,
            _ => throw new NotSupportedException($"The audio transcription format '{responseFormat}' is not supported."),
        };
    }
}
