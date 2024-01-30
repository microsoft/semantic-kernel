// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

/// <summary>
/// Represents a factory for creating HttpRequestMessage instances.
/// </summary>
internal interface IHttpRequestFactory
{
    /// <summary>
    /// Creates a new instance of HttpRequestMessage based on the provided requestData.
    /// </summary>
    /// <param name="requestData">The object containing the data for the HTTP request.</param>
    /// <param name="endpoint"></param>
    /// <returns>A new instance of HttpRequestMessage.</returns>
    HttpRequestMessage CreatePost(object requestData, Uri endpoint);
}
