// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Provides the default HttpClientHandler instance for HTTP requests.
/// </summary>
internal static class HttpHandlerProvider
{
    /// <summary>
    /// Gets the default HttpClientHandler instance.
    /// </summary>
    internal static HttpClientHandler Default { get; } = new HttpClientHandler() { CheckCertificateRevocationList = true };
}
