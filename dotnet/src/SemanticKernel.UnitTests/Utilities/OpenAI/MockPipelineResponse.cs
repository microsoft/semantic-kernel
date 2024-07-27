// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace SemanticKernel.UnitTests.Utilities.OpenAI;

public class MockPipelineResponse : PipelineResponse
{
    private int _status;
    private string _reasonPhrase;
    private Stream? _contentStream;
    private BinaryData? _bufferedContent;

    private readonly PipelineResponseHeaders _headers;

    private bool _disposed;

    public MockPipelineResponse(int status = 0, string reasonPhrase = "")
    {
        this._status = status;
        this._reasonPhrase = reasonPhrase;
        this._headers = new MockResponseHeaders();
    }

    public override int Status => this._status;

    public void SetStatus(int value) => this._status = value;

    public override string ReasonPhrase => this._reasonPhrase;

    public void SetReasonPhrase(string value) => this._reasonPhrase = value;

    public void SetContent(byte[] content)
    {
        this.ContentStream = new MemoryStream(content, 0, content.Length, false, true);
    }

    public MockPipelineResponse SetContent(string content)
    {
        this.SetContent(Encoding.UTF8.GetBytes(content));
        return this;
    }

    public override Stream? ContentStream
    {
        get => this._contentStream;
        set => this._contentStream = value;
    }

    public override BinaryData Content
    {
        get
        {
            if (this._contentStream is null)
            {
                return new BinaryData(Array.Empty<byte>());
            }

            if (this.ContentStream is not MemoryStream memoryContent)
            {
                throw new InvalidOperationException("The response is not buffered.");
            }

            if (memoryContent.TryGetBuffer(out ArraySegment<byte> segment))
            {
                return new BinaryData(segment.AsMemory());
            }
            return new BinaryData(memoryContent.ToArray());
        }
    }

    protected override PipelineResponseHeaders HeadersCore
        => this._headers;

    public sealed override void Dispose()
    {
        this.Dispose(true);

        GC.SuppressFinalize(this);
    }

    protected void Dispose(bool disposing)
    {
        if (disposing && !this._disposed)
        {
            Stream? content = this._contentStream;
            if (content != null)
            {
                this._contentStream = null;
                content.Dispose();
            }

            this._disposed = true;
        }
    }

    public override BinaryData BufferContent(CancellationToken cancellationToken = default)
    {
        if (this._bufferedContent is not null)
        {
            return this._bufferedContent;
        }

        if (this._contentStream is null)
        {
            this._bufferedContent = new BinaryData(Array.Empty<byte>());
            return this._bufferedContent;
        }

        MemoryStream bufferStream = new();
        this._contentStream.CopyTo(bufferStream);
        this._contentStream.Dispose();
        this._contentStream = bufferStream;

        // Less efficient FromStream method called here because it is a mock.
        // For intended production implementation, see HttpClientTransportResponse.
        this._bufferedContent = BinaryData.FromStream(bufferStream);
        return this._bufferedContent;
    }

    public override async ValueTask<BinaryData> BufferContentAsync(CancellationToken cancellationToken = default)
    {
        if (this._bufferedContent is not null)
        {
            return this._bufferedContent;
        }

        if (this._contentStream is null)
        {
            this._bufferedContent = new BinaryData(Array.Empty<byte>());
            return this._bufferedContent;
        }

        MemoryStream bufferStream = new();

        await this._contentStream.CopyToAsync(bufferStream, cancellationToken).ConfigureAwait(false);
        await this._contentStream.DisposeAsync().ConfigureAwait(false);

        this._contentStream = bufferStream;

        // Less efficient FromStream method called here because it is a mock.
        // For intended production implementation, see HttpClientTransportResponse.
        this._bufferedContent = BinaryData.FromStream(bufferStream);
        return this._bufferedContent;
    }
}
