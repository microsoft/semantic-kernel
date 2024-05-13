// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Text;

/// <summary>
/// Provides a reader for Server-Sent Events (SSE) data.
/// </summary>
/// <remarks>
/// <a href="https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream">SSE specification</a>
/// </remarks>
[ExcludeFromCodeCoverage]
internal sealed class SseReader(Stream stream) : IDisposable
{
    private readonly Stream _stream = stream;
    private readonly StreamReader _reader = new(stream);
    private string? _lastEventName;

    public SseLine? ReadSingleDataEvent()
    {
        while (this.ReadLine() is { } line)
        {
            if (line.IsEmpty)
            {
                this._lastEventName = null;
                continue;
            }

            if (line.IsComment)
            {
                continue;
            }

            if (line.FieldName.Span.SequenceEqual("event".AsSpan()))
            {
                // Save the last event name
                this._lastEventName = line.FieldValue.ToString();
                continue;
            }

            if (!line.FieldName.Span.SequenceEqual("data".AsSpan()))
            {
                // Skip non-data fields
                continue;
            }

            if (!line.IsValueEmpty)
            {
                // Return data field
                return line;
            }
        }

        return null;
    }

    public async Task<SseLine?> ReadSingleDataEventAsync(CancellationToken cancellationToken)
    {
        while (await this.ReadLineAsync(cancellationToken).ConfigureAwait(false) is { } line)
        {
            if (line.IsEmpty)
            {
                this._lastEventName = null;
                continue;
            }

            if (line.IsComment)
            {
                continue;
            }

            if (line.FieldName.Span.SequenceEqual("event".AsSpan()))
            {
                // Save the last event name
                this._lastEventName = line.FieldValue.ToString();
                continue;
            }

            if (!line.FieldName.Span.SequenceEqual("data".AsSpan()))
            {
                // Skip non-data fields
                continue;
            }

            if (!line.IsValueEmpty)
            {
                // Return data field
                return line;
            }
        }

        return null;
    }

    private SseLine? ReadLine()
    {
        string? lineText = this._reader.ReadLine();
        if (lineText is null)
        {
            return null;
        }

        if (lineText.Length == 0)
        {
            return SseLine.Empty;
        }

        if (this.TryParseLine(lineText, out SseLine line))
        {
            return line;
        }

        return null;
    }

    private async Task<SseLine?> ReadLineAsync(CancellationToken cancellationToken)
    {
        string? lineText = await this._reader.ReadLineAsync(
#if NET
            cancellationToken
#endif
            ).ConfigureAwait(false);

        if (lineText is null)
        {
            return null;
        }

        if (lineText.Length == 0)
        {
            return SseLine.Empty;
        }

        if (this.TryParseLine(lineText, out SseLine line))
        {
            return line;
        }

        return null;
    }

    private bool TryParseLine(string lineText, out SseLine line)
    {
        if (lineText.Length == 0)
        {
            line = default;
            return false;
        }

        ReadOnlySpan<char> lineSpan = lineText.AsSpan();
        int colonIndex = lineSpan.IndexOf(':');
        ReadOnlySpan<char> fieldValue = colonIndex >= 0 ? lineSpan.Slice(colonIndex + 1) : string.Empty.AsSpan();

        bool hasSpace = fieldValue.Length > 0 && fieldValue[0] == ' ';
        line = new SseLine(lineText, colonIndex, hasSpace, this._lastEventName);
        return true;
    }

    public void Dispose()
    {
        this._reader.Dispose();
        this._stream.Dispose();
    }
}
