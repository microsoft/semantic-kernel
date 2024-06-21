// Copyright (c) Microsoft. All rights reserved.

/* Phase 01
This class was imported and adapted from the System.ClientModel Unit Tests.
https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/core/System.ClientModel/tests/TestFramework/Mocks/MockPipelineResponse.cs
*/

using System;
using System.ClientModel;
using System.ClientModel.Primitives;

namespace SemanticKernel.Connectors.OpenAI.UnitTests;

public class MockPipelineRequest : PipelineRequest
{
    private string _method;
    private Uri? _uri;
    private BinaryContent? _content;
    private readonly PipelineRequestHeaders _headers;

    private bool _disposed;

    public MockPipelineRequest()
    {
        this._headers = new MockRequestHeaders();
        this._method = "GET";
    }

    protected override BinaryContent? ContentCore
    {
        get => this._content;
        set => this._content = value;
    }

    protected override PipelineRequestHeaders HeadersCore
        => this._headers;

    protected override string MethodCore
    {
        get => this._method;
        set => this._method = value;
    }

    protected override Uri? UriCore
    {
        get => this._uri;
        set => this._uri = value;
    }

    public sealed override void Dispose()
    {
        this.Dispose(true);

        GC.SuppressFinalize(this);
    }

    protected void Dispose(bool disposing)
    {
        if (disposing && !this._disposed)
        {
            var content = this._content;
            if (content != null)
            {
                this._content = null;
                content.Dispose();
            }

            this._disposed = true;
        }
    }
}
