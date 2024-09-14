// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;

namespace SemanticKernel.Connectors.AssemblyAI.UnitTests;

internal sealed class MultipleHttpMessageHandlerStub : DelegatingHandler
{
    private int _callIteration = 0;

    public List<HttpRequestHeaders?> RequestHeaders { get; private set; }

    public List<HttpContentHeaders?> ContentHeaders { get; private set; }

    public List<byte[]?> RequestContents { get; private set; }

    public List<Uri?> RequestUris { get; private set; }

    public List<HttpMethod?> Methods { get; private set; }

    public List<HttpResponseMessage> ResponsesToReturn { get; set; }

    public MultipleHttpMessageHandlerStub()
    {
        this.RequestHeaders = [];
        this.ContentHeaders = [];
        this.RequestContents = [];
        this.RequestUris = [];
        this.Methods = [];
        this.ResponsesToReturn = [];
    }

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        this._callIteration++;

        this.Methods.Add(request.Method);
        this.RequestUris.Add(request.RequestUri);
        this.RequestHeaders.Add(request.Headers);
        this.ContentHeaders.Add(request.Content?.Headers);

        var content = request.Content == null ? null : await request.Content.ReadAsByteArrayAsync(cancellationToken).ConfigureAwait(false);

        this.RequestContents.Add(content);

        return await Task.FromResult(this.ResponsesToReturn[this._callIteration - 1]).ConfigureAwait(false);
    }
}
