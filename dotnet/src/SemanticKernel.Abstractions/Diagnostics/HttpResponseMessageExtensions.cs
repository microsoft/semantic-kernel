// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Diagnostics;
using System.Net.Http;
using Microsoft.Extensions.Logging;

/// <summary>
/// Provides extension methods for <see cref="HttpResponseMessage"/>.
/// </summary>
public static class HttpResponseMessageExtensions
{
    /// <summary>
    /// Ensures that the HTTP response was successful; otherwise, throws an <see cref="HttpOperationException"/>.
    /// </summary>
    /// <param name="response">The <see cref="HttpResponseMessage"/> to check for success.</param>
    /// <param name="responseContent">Optional. The content of the HTTP response.</param>
    /// <param name="logger">Optional. The logger to use for logging errors.</param>
    public static void EnsureSuccess(this HttpResponseMessage response, string? responseContent = null, ILogger? logger = null)
    {
        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            logger?.LogError(e, "HTTP request failed: {0} {1} {2}", response.StatusCode, e.Message, responseContent);
            throw new HttpOperationException(response.StatusCode, responseContent, e.Message, e);
        }
    }
}
