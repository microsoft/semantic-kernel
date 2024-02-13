// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Associate a response stream with its parent response for parity in life-cycle management.
/// </summary>
[SuppressMessage("Performance", "CA1812:Avoid uninstantiated internal classes", Justification = "This class is an internal utility.")]
internal sealed class HttpResponseStream : Stream
{
    private readonly Stream _stream;
    private readonly HttpResponseMessage _response;

    public override bool CanRead => this._stream.CanRead;

    public override bool CanSeek => this._stream.CanSeek;

    public override bool CanWrite => this._stream.CanWrite;

    public override long Length => this._stream.Length;

    public override long Position { get => this._stream.Position; set => this._stream.Position = value; }

    public override void Flush()
    {
        this._stream.Flush();
    }

    public override int Read(byte[] buffer, int offset, int count)
    {
        return this._stream.Read(buffer, offset, count);
    }

    public override long Seek(long offset, SeekOrigin origin)
    {
        return this._stream.Seek(offset, origin);
    }

    public override void SetLength(long value)
    {
        this._stream.SetLength(value);
    }

    public override void Write(byte[] buffer, int offset, int count)
    {
        this._stream.Write(buffer, offset, count);
    }

    public HttpResponseStream(Stream stream, HttpResponseMessage response)
    {
        this._stream = stream;
        this._response = response;
    }

    protected override void Dispose(bool disposing)
    {
        base.Dispose(disposing);

        if (disposing)
        {
            this._stream.Dispose();
            this._response.Dispose();
        }
    }
}
