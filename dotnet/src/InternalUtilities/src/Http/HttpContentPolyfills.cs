// Copyright (c) Microsoft. All rights reserved.

#if !NET5_0_OR_GREATER

using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace System.Net.Http;

[ExcludeFromCodeCoverage]
internal static class HttpContentPolyfills
{
    internal static Task<string> ReadAsStringAsync(this HttpContent httpContent, CancellationToken cancellationToken)
        => httpContent.ReadAsStringAsync();

    internal static Task<Stream> ReadAsStreamAsync(this HttpContent httpContent, CancellationToken cancellationToken)
        => httpContent.ReadAsStreamAsync();

    internal static Task<byte[]> ReadAsByteArrayAsync(this HttpContent httpContent, CancellationToken cancellationToken)
        => httpContent.ReadAsByteArrayAsync();
}

#endif
