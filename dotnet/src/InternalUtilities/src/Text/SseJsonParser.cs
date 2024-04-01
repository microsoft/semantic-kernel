// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Runtime.CompilerServices;
using System.Threading;

namespace Microsoft.SemanticKernel.Text;

/// <summary>
/// Provides methods to parse Server-Sent Events (SSE) data from a stream.
/// </summary>
/// <remarks>
/// <a href="https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream">SSE specification</a>
/// </remarks>
[ExcludeFromCodeCoverage]
internal static class SseJsonParser
{
    /// <summary>
    /// Parses Server-Sent Events (SSE) data asynchronously from a stream.
    /// </summary>
    /// <param name="stream">The stream containing the SSE data.</param>
    /// <param name="parser">The function to parse each <see cref="SseLine"/> into an <see cref="SseData"/> object.</param>
    /// <param name="cancellationToken">A cancellation token to stop the parsing process.</param>
    /// <remarks><paramref name="stream"/> will be disposed immediately once enumeration is complete.</remarks>
    /// <returns>An asynchronous enumerable sequence of <see cref="SseData"/> objects.</returns>
    public static async IAsyncEnumerable<SseData> ParseAsync(
        Stream stream,
        Func<SseLine, SseData?> parser,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        try
        {
            using SseReader sseReader = new(stream);
            while (!cancellationToken.IsCancellationRequested)
            {
                SseLine? sseLine = await sseReader.ReadSingleDataEventAsync(cancellationToken).ConfigureAwait(false);
                if (sseLine == null)
                {
                    break; // end of stream
                }

                ReadOnlyMemory<char> value = sseLine.Value.FieldValue;
                if (value.Span.SequenceEqual("[DONE]".AsSpan()))
                {
                    break;
                }

                var sseData = parser(sseLine.Value);
                if (sseData != null)
                {
                    yield return sseData;
                }
            }
        }
        finally
        {
            // Always dispose the stream immediately once enumeration is complete for any reason
#if NETCOREAPP3_0_OR_GREATER
            await stream.DisposeAsync().ConfigureAwait(false);
#else
            stream.Dispose();
#endif
        }
    }
}
