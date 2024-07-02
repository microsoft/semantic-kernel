// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.Net;
using Azure;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Provides extension methods for the <see cref="ClientResultException"/> class.
/// </summary>
internal static class ClientResultExceptionExtensions
{
    /// <summary>
    /// Converts a <see cref="ClientResultException"/> to an <see cref="HttpOperationException"/>.
    /// </summary>
    /// <param name="exception">The original <see cref="RequestFailedException"/>.</param>
    /// <returns>An <see cref="HttpOperationException"/> instance.</returns>
    public static HttpOperationException ToHttpOperationException(this ClientResultException exception)
    {
        const int NoResponseReceived = 0;

        string? responseContent = null;

        try
        {
            responseContent = exception.GetRawResponse()?.Content?.ToString();
        }
#pragma warning disable CA1031 // Do not catch general exception types
        catch { } // We want to suppress any exceptions that occur while reading the content, ensuring that an HttpOperationException is thrown instead.
#pragma warning restore CA1031

        return new HttpOperationException(
            exception.Status == NoResponseReceived ? null : (HttpStatusCode?)exception.Status,
            responseContent,
            exception.Message,
            exception);
    }
}
