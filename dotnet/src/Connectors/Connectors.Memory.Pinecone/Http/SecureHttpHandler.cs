// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http;

internal static class HttpHandlers
{
    public static HttpClientHandler CheckCertificateRevocation { get; } = new()
    {
        CheckCertificateRevocationList = false,
        AllowAutoRedirect = true
    };
}
