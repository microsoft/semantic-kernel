// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Experimental.Agents.Internal;

/// <summary>
/// Placeholder context.
/// </summary>
internal sealed class OpenAIRestContext(string endpoint, string apiKey, string? version, Func<HttpClient>? clientFactory = null)
{
    private static readonly HttpClient s_defaultOpenAIClient = new();

    /// <summary>
    /// The service API key.
    /// </summary>
    public string ApiKey { get; } = apiKey;

    /// <summary>
    /// The service endpoint.
    /// </summary>
    public string Endpoint { get; } = endpoint;

    /// <summary>
    /// Is the version defined?
    /// </summary>
    public bool HasVersion { get; } = !string.IsNullOrEmpty(version);

    /// <summary>
    /// The optional API version.
    /// </summary>
    public string? Version { get; } = version;

    /// <summary>
    /// Accessor for the http client.
    /// </summary>
    public HttpClient GetHttpClient() => this._clientFactory.Invoke();

    private readonly Func<HttpClient> _clientFactory = clientFactory ??= () => s_defaultOpenAIClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIRestContext"/> class.
    /// </summary>
    public OpenAIRestContext(string endpoint, string apiKey, Func<HttpClient>? clientFactory = null)
        : this(endpoint, apiKey, version: null, clientFactory)
    { }
}
