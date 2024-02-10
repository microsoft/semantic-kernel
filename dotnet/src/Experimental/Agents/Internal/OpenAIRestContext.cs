// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Specialized;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Experimental.Agents.Internal;

/// <summary>
/// Placeholder context.
/// </summary>
internal sealed class OpenAIRestContext
{
    private static readonly HttpClient s_defaultOpenAIClient = new();

    /// <summary>
    /// $$$
    /// </summary>
    public string ApiKey { get; }

    /// <summary>
    /// $$$
    /// </summary>
    public string Endpoint { get; }

    /// <summary>
    /// $$$
    /// </summary>
    public bool HasVersion { get; }

    /// <summary>
    /// $$$
    /// </summary>
    public string? Version { get; }

    /// <summary>
    /// $$$
    /// </summary>
    public HttpClient GetHttpClient() => this._clientFactory.Invoke();

    private readonly Func<HttpClient> _clientFactory;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIRestContext"/> class.
    /// </summary>
    public OpenAIRestContext(string endpoint, string apiKey, Func<HttpClient>? clientFactory = null)
        : this(endpoint, apiKey, version: null, clientFactory)
    {
        // Nothing to do...
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIRestContext"/> class.
    /// </summary>
    public OpenAIRestContext(string endpoint, string apiKey, string? version, Func<HttpClient>? clientFactory = null)
    {
        this._clientFactory = clientFactory ??= () => s_defaultOpenAIClient;

        this.ApiKey = apiKey;
        this.Endpoint = endpoint;
        this.HasVersion = !string.IsNullOrEmpty(version);
        this.Version = version;
    }
}
