// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Utils;

internal sealed class CustomHeadersHandler : DelegatingHandler
{
    private readonly string _headerName;
    private readonly string _headerValue;
    public HttpRequestHeaders? RequestHeaders { get; private set; }

    public HttpContentHeaders? ContentHeaders { get; private set; }

    public byte[]? RequestContent { get; private set; }

    public Uri? RequestUri { get; private set; }

    public HttpMethod? Method { get; private set; }

    public CustomHeadersHandler(string headerName, string headerValue, string testDataFilePath)
    {
        this.InnerHandler = new HttpMessageHandlerStub
        {
            ResponseToReturn = { Content = new StringContent(File.ReadAllText(testDataFilePath)) }
        };
        this._headerName = headerName;
        this._headerValue = headerValue;
    }

    protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, System.Threading.CancellationToken cancellationToken)
    {
        request.Headers.Add(this._headerName, this._headerValue);
        this.Method = request.Method;
        this.RequestUri = request.RequestUri;
        this.RequestHeaders = request.Headers;
        this.RequestContent = request.Content is null ? null : request.Content.ReadAsByteArrayAsync(cancellationToken).Result;

        return base.SendAsync(request, cancellationToken);
    }
}
