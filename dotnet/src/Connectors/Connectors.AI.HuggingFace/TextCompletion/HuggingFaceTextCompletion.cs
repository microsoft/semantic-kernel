// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;

/// <summary>
/// HuggingFace text completion service.
/// </summary>
public sealed class HuggingFaceTextCompletion : HuggingFaceClientBase, ITextCompletion
{
    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    public HuggingFaceTextCompletion(Uri endpoint, string model) : base(endpoint, model)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// Using HuggingFace API for service call, see https://huggingface.co/docs/api-inference/index.
    /// </summary>
    /// <param name="model">The name of the model to use for text completion.</param>
    /// <param name="apiKey">The API key for accessing the Hugging Face service.</param>
    /// <param name="httpClient">The HTTP client to use for making API requests. If not specified, a default client will be used.</param>
    /// <param name="endpoint">The endpoint URL for the Hugging Face service.
    /// If not specified, the base address of the HTTP client is used. If the base address is not available, a default endpoint will be used.</param>
    public HuggingFaceTextCompletion(string model, string? apiKey = null, HttpClient? httpClient = null, string? endpoint = null) : base(model, apiKey, httpClient, endpoint)
    {
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, string> Attributes => this.ClientAttributes;

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string text,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        return await this.ExecuteGetCompletionsAsync(text, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<T> GetStreamingContentAsync<T>(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var result in await this.ExecuteGetCompletionsAsync(prompt, cancellationToken).ConfigureAwait(false))
        {
            cancellationToken.ThrowIfCancellationRequested();
            // Gets the non streaming content and returns as one complete result
            var content = await result.GetCompletionAsync(cancellationToken).ConfigureAwait(false);

            // If the provided T is a string, return the completion as is
            if (typeof(T) == typeof(string))
            {
                yield return (T)(object)content;
                continue;
            }

            // If the provided T is an specialized class of StreamingContent interface
            if (typeof(T) == typeof(StreamingTextContent) ||
                typeof(T) == typeof(StreamingContent))
            {
                yield return (T)(object)new StreamingTextContent(content, 1, result);
            }

            throw new NotSupportedException($"Type {typeof(T)} is not supported");
        }
    }

    #region private ================================================================================

    private async Task<IReadOnlyList<TextCompletionResult>> ExecuteGetCompletionsAsync(string text, CancellationToken cancellationToken = default)
    {
        var completionRequest = new TextCompletionRequest
        {
            Input = text
        };

        using var response = await this.SendPostRequestAsync(completionRequest, cancellationToken).ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        List<TextCompletionResponse>? completionResponse = JsonSerializer.Deserialize<List<TextCompletionResponse>>(body);

        if (completionResponse is null)
        {
            throw new KernelException("Unexpected response from model")
            {
                Data = { { "ResponseData", body } },
            };
        }

        return completionResponse.ConvertAll(c => new TextCompletionResult(c));
    }

    #endregion
}
