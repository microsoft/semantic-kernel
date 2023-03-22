// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.Extensions;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;

namespace Microsoft.SemanticKernel.AI.OpenAI.Clients;

/// <summary>
/// An abstract OpenAI Client.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1054:URI-like parameters should not be strings", Justification = "OpenAI users use strings")]
public abstract class OpenAIClientAbstract : IDisposable
{
    /// <summary>
    /// Logger
    /// </summary>
    protected ILogger Log { get; } = NullLogger.Instance;

    /// <summary>
    /// HTTP client
    /// </summary>
    protected HttpClient HTTPClient { get; }

    private readonly HttpClientHandler _httpClientHandler;

    internal OpenAIClientAbstract(ILogger? log = null)
    {
        if (log != null) { this.Log = log; }

        // TODO: allow injection of retry logic, e.g. Polly
        this._httpClientHandler = new() { CheckCertificateRevocationList = true };
        this.HTTPClient = new HttpClient(this._httpClientHandler);
        this.HTTPClient.DefaultRequestHeaders.Add("User-Agent", HTTPUseragent);
    }

    /// <summary>
    /// Asynchronously sends a completion request for the prompt
    /// </summary>
    /// <param name="url">URL for the completion request API</param>
    /// <param name="requestBody">Prompt to complete</param>
    /// <returns>The completed text</returns>
    /// <exception cref="AIException">AIException thrown during the request.</exception>
    protected async Task<string> ExecuteCompleteRequestAsync(string url, string requestBody)
    {
        try
        {
            this.Log.LogDebug("Sending completion request to {0}: {1}", url, requestBody);

            var result = await this.HTTPClient.ExecutePostRequestAsync<CompletionResponse>(new Uri(url), requestBody);
            if (result.Completions.Count < 1)
            {
                throw new AIException(
                    AIException.ErrorCodes.InvalidResponseContent,
                    "Completions not found");
            }

            return result.Completions.First().Text;
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    /// <summary>
    /// Asynchronously sends an embedding request for the text.
    /// </summary>
    /// <param name="url"></param>
    /// <param name="requestBody"></param>
    /// <returns></returns>
    /// <exception cref="AIException"></exception>
    protected async Task<IList<Embedding<float>>> ExecuteEmbeddingRequestAsync(string url, string requestBody)
    {
        try
        {
            var result = await this.HTTPClient.ExecutePostRequestAsync<EmbeddingResponse>(new Uri(url), requestBody);
            if (result.Embeddings.Count < 1)
            {
                throw new AIException(
                    AIException.ErrorCodes.InvalidResponseContent,
                    "Embeddings not found");
            }

            return result.Embeddings.Select(e => new Embedding<float>(e.Values.ToArray())).ToList();
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    /// <summary>
    /// Explicit finalizer called by IDisposable
    /// </summary>
    public void Dispose()
    {
        this.Dispose(true);
        // Request CL runtime not to call the finalizer - reduce cost of GC
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Overridable finalizer for concrete classes
    /// </summary>
    /// <param name="disposing"></param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this.HTTPClient.Dispose();
            this._httpClientHandler.Dispose();
        }
    }

    #region private ================================================================================

    // HTTP user agent sent to remote endpoints
    private const string HTTPUseragent = "Microsoft Semantic Kernel";

    /// <summary>
    /// C# finalizer
    /// </summary>
    ~OpenAIClientAbstract()
    {
        this.Dispose(false);
    }

    #endregion
}
