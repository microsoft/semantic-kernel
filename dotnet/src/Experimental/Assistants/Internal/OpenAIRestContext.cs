// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Internal;

/// <summary>
/// Placeholder context.
/// </summary>
internal sealed class OpenAIRestContext
{
    /// <inheritdoc/>
    public string ApiKey { get; }

    /// <inheritdoc/>
    public HttpClient GetHttpClient() => this._clientFactory.Invoke();

    private readonly Func<HttpClient> _clientFactory;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIRestContext"/> class.
    /// </summary>
    public OpenAIRestContext(string apiKey, Func<HttpClient>? clientFactory = null)
    {
        this._clientFactory = clientFactory ??= () => new HttpClient();

        this.ApiKey = apiKey;
    }
}
