// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using Azure;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Provides extension methods for the <see cref="RequestFailedException"/> class.
/// </summary>
public static class RequestFailedExceptionExtensions
{
    /// <summary>
    /// Converts a <see cref="RequestFailedException"/> to an <see cref="HttpOperationException"/>.
    /// </summary>
    /// <param name="original">The original <see cref="RequestFailedException"/> object.</param>
    /// <returns>An <see cref="HttpOperationException"/> instance.</returns>
    public static HttpOperationException ToHttpOperationException(this RequestFailedException original)
    {
        const int NoResponseReceived = 0;

        return new HttpOperationException(
            original.Status == NoResponseReceived ? null : (HttpStatusCode?)original.Status,
            null,
            original.Message,
            original);
    }
}
