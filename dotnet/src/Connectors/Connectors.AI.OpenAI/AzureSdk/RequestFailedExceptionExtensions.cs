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
    /// <param name="exception">The original <see cref="RequestFailedException"/>.</param>
    /// <returns>An <see cref="HttpOperationException"/> instance.</returns>
    public static HttpOperationException ToHttpOperationException(this RequestFailedException exception)
    {
        const int NoResponseReceived = 0;

        return new HttpOperationException(
            exception.Status == NoResponseReceived ? null : (HttpStatusCode?)exception.Status,
            exception.Message,
            exception.Message,
            exception);
    }
}
