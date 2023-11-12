// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Context for interacting with OpenAI REST API.
/// </summary>
public interface IOpenAIRestContext
{
    /// <summary>
    /// The OpenAI API key.
    /// </summary>
    string ApiKey { get; }

    /// <summary>
    /// Access an <see cref="HttpClient"/> to use for OpenAI REST API calls.
    /// </summary>
    /// <remarks>
    /// Play nicely with IHttpClientFactory and respect IDisposable.
    /// </remarks>
    HttpClient GetHttpClient();
}
