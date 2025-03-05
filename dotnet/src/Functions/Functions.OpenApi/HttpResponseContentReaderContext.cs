// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents the context for HTTP response content reader.
/// </summary>
[Experimental("SKEXP0040")]
public sealed class HttpResponseContentReaderContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="HttpResponseContentReaderContext"/> class.
    /// </summary>
    /// <param name="request">HTTP request message.</param>
    /// <param name="response">HTTP response message.</param>
    internal HttpResponseContentReaderContext(HttpRequestMessage request, HttpResponseMessage response)
    {
        this.Request = request;
        this.Response = response;
    }

    /// <summary>
    /// The HTTP request message.
    /// </summary>
    public HttpRequestMessage Request { get; }

    /// <summary>
    /// The HTTP response message.
    /// </summary>
    public HttpResponseMessage Response { get; }
}
