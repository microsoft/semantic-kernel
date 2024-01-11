#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Gemini.Abstract;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core.Gemini.Common;

/// <summary>
/// Represents a client for interacting with the text generation gemini model.
/// </summary>
internal class GeminiTextGenerationClient : GeminiClient, IGeminiTextGenerationClient
{
    private readonly IStreamJsonParser _streamJsonParser;
    private readonly string _modelId;

    /// <summary>
    /// Represents a client for interacting with the text generation gemini model.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="configuration">Gemini configuration instance containing API key and other configuration options</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="endpointProvider">Endpoints provider for gemini rest api or gemini vertex ai</param>
    /// <param name="streamJsonParser">Response streaming json parser (optional)</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GeminiTextGenerationClient(
        HttpClient httpClient,
        GeminiConfiguration configuration,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            httpRequestFactory: httpRequestFactory,
            endpointProvider: endpointProvider,
            logger: logger)
    {
        VerifyModelId(configuration);

        this._modelId = configuration.ModelId!;
        this._streamJsonParser = streamJsonParser ?? new GeminiStreamJsonParser();
    }

    /// <inheritdoc/>
    public virtual async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        var endpoint = this.EndpointProvider.GetTextGenerationEndpoint(this._modelId);
        var geminiRequest = CreateGeminiRequest(prompt, executionSettings);
        using var httpRequestMessage = this.HTTPRequestFactory.CreatePost(geminiRequest, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return this.DeserializeAndProcessTextResponse(body);
    }

    /// <inheritdoc/>
    public virtual async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        var endpoint = this.EndpointProvider.GetStreamTextGenerationEndpoint(this._modelId);
        var geminiRequest = CreateGeminiRequest(prompt, executionSettings);
        using var httpRequestMessage = this.HTTPRequestFactory.CreatePost(geminiRequest, endpoint);

        using var response = await this.SendRequestAndGetResponseStreamAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        foreach (var streamingTextContent in this.ProcessTextResponseStream(responseStream, cancellationToken))
        {
            yield return streamingTextContent;
        }
    }

    #region PRIVATE METHODS

    private static void VerifyModelId(GeminiConfiguration configuration)
    {
        Verify.NotNullOrWhiteSpace(configuration?.ModelId, $"{nameof(configuration)}.{nameof(configuration.ModelId)}");
    }

    private IEnumerable<StreamingTextContent> ProcessTextResponseStream(
        Stream responseStream,
        CancellationToken cancellationToken)
    {
        foreach (var geminiResponse in this.ProcessResponseStream(responseStream, cancellationToken))
        {
            foreach (var textContent in this.ProcessTextResponse(geminiResponse))
            {
                yield return GetStreamingTextContentFromTextContent(textContent);
            }
        }
    }

    private IEnumerable<GeminiResponse> ProcessResponseStream(
        Stream responseStream,
        CancellationToken cancellationToken)
    {
        foreach (string json in this._streamJsonParser.Parse(responseStream))
        {
            yield return DeserializeResponse<GeminiResponse>(json);
        }
    }

    private List<TextContent> DeserializeAndProcessTextResponse(string body)
    {
        var geminiResponse = DeserializeResponse<GeminiResponse>(body);
        return this.ProcessTextResponse(geminiResponse);
    }

    private List<TextContent> ProcessTextResponse(GeminiResponse geminiResponse)
    {
        var textContents = geminiResponse.Candidates.Select(candidate => new TextContent(
            text: candidate.Content.Parts[0].Text,
            modelId: this._modelId,
            innerContent: candidate,
            metadata: GetResponseMetadata(geminiResponse, candidate))).ToList();
        this.LogUsageMetadata((GeminiMetadata)textContents[0].Metadata!);
        return textContents;
    }

    private static StreamingTextContent GetStreamingTextContentFromTextContent(TextContent textContent)
        => new(
            text: textContent.Text,
            modelId: textContent.ModelId,
            innerContent: textContent.InnerContent,
            metadata: textContent.Metadata,
            choiceIndex: ((GeminiMetadata)textContent.Metadata!).Index);

    #endregion
}
