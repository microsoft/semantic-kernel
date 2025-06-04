// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Text;

/// <summary>
/// Internal class for parsing Server-Sent Events (SSE) data from a stream.
/// </summary>
/// <remarks>
/// This is specialized parser for Server-Sent Events (SSE) data that is formatted as JSON.<br/>
/// If you need to parse non-structured json streaming data, use <see cref="StreamJsonParser"/> instead.<br/>
/// <a href="https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream">SSE specification</a><br/>
/// This class is thread-safe.
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
    internal static async IAsyncEnumerable<SseData> ParseAsync(
        Stream stream,
        Func<SseLine, SseData?> parser,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        try
        {
            using SseReader sseReader = new(stream);
            while (!cancellationToken.IsCancellationRequested)
            {
                SseLine? sseLine = await sseReader.ReadSingleDataEventAsync(cancellationToken).ConfigureAwait(false);
                if (sseLine is null)
                {
                    break; // end of stream
                }

                ReadOnlyMemory<char> value = sseLine.Value.FieldValue;
                if (value.Span.SequenceEqual("[DONE]".AsSpan()))
                {
                    break;
                }

                var sseData = parser(sseLine.Value);
                if (sseData is not null)
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

    /// <summary>
    /// Parses Server-Sent Events (SSE) data asynchronously from a stream and deserializes the data into the specified type.
    /// </summary>
    /// <typeparam name="T">The type to deserialize the data into.</typeparam>
    /// <param name="stream">The stream containing the SSE data.</param>
    /// <param name="cancellationToken">A cancellation token to stop the parsing process.</param>
    /// <returns>An asynchronous enumerable sequence of deserialized objects of type <typeparamref name="T"/>.</returns>
    internal static async IAsyncEnumerable<T> ParseAsync<T>(Stream stream, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await foreach (var sseData in ParseAsync(stream, DeserializeTargetType, cancellationToken).ConfigureAwait(false))
        {
            yield return (T)sseData.Data;
        }

        static SseData? DeserializeTargetType(SseLine sseLine)
        {
            var obj = JsonSerializer.Deserialize<T>(sseLine.FieldValue.Span, JsonOptionsCache.ReadPermissive);
            return new SseData(sseLine.EventName, obj!);
        }
    }
}
