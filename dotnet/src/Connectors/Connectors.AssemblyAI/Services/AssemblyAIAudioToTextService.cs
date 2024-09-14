// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Connectors.AssemblyAI.Core;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.AssemblyAI;

/// <summary>
/// AssemblyAI speech-to-text service.
/// </summary>
public sealed class AssemblyAIAudioToTextService : IAudioToTextService
{
    private readonly AssemblyAIClient _client;

    /// <summary>
    /// Attributes is not used by AssemblyAIAudioToTextService.
    /// </summary>
    public IReadOnlyDictionary<string, object?> Attributes => new Dictionary<string, object?>();

    /// <summary>
    /// Creates an instance of the <see cref="AssemblyAIAudioToTextService"/> with an AssemblyAI API key.
    /// </summary>
    /// <param name="apiKey">AssemblyAI API key</param>
    /// <param name="endpoint">Optional endpoint uri including the port where AssemblyAI server is hosted</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the AssemblyAI API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public AssemblyAIAudioToTextService(
        string apiKey,
        Uri? endpoint = null,
        public AssemblyAIAudioToTextService(string apiKey) : this(apiKey, null, null, null) {}
        public AssemblyAIAudioToTextService(string apiKey, Uri? endpoint = null, HttpClient? httpClient = null) : this(apiKey, endpoint, httpClient, null)
    )
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        this._client = new AssemblyAIClient(
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            endpoint: endpoint,
            apiKey: apiKey,
            logger: loggerFactory?.CreateLogger(this.GetType()));
    }

    /// <inheritdoc />
    public async Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        AudioContent content,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken
    )
    {
        Verify.NotNull(content);

        string uploadUrl;
        if (content.Data is { IsEmpty: false })
        {
            await this._client.UploadFileAsync(content.Data.Value, cancellationToken).ConfigureAwait(false);
        }
        else if (content.Uri is not null)
        {
            // to prevent unintentional file uploads by injection attack
            if (content.Uri.IsFile)
            {
                throw new ArgumentException("File URI is not allowed due to security concerns. Use `AudioContent.Stream` or `AudioContent.File` to transcribe a local file instead.");
            {
                throw new ArgumentException("File URI is not allowed. Use `AudioContent.Stream` or `AudioContent.File` to transcribe a local file instead.");
            }

            uploadUrl = content.Uri.ToString();
        }
        else
        {
            throw new ArgumentException("AudioContent doesn't have any content.", nameof(content));
        }

        var transcriptId = await this._client.CreateTranscriptAsync(uploadUrl, executionSettings, cancellationToken)
            .ConfigureAwait(false);
        var transcript = await this._client.WaitForTranscriptToProcessAsync(transcriptId, executionSettings, cancellationToken)
            .ConfigureAwait(false);

        return [
            new TextContent(
                text: transcript.GetProperty("text").GetString(),
                modelId: null,
                // TODO: change to typed object when AAI SDK is shipped
                innerContent: transcript,
                encoding: Encoding.UTF8,
                metadata: null)
            ];
    }
}
