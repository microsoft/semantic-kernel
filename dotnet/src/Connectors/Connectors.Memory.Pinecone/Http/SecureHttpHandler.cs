// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http;

[Obsolete("This class is deprecated and will be removed in one of the next SK SDK versions. Please use custom HTTP client to finely adjust its properties/behavior.")]
internal static class HttpHandlers
{
    public static HttpClientHandler CheckCertificateRevocation { get; } = new()
    {
        CheckCertificateRevocationList = false,
        AllowAutoRedirect = true
    };
}
