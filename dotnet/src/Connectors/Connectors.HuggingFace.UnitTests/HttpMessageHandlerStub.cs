// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests;

internal sealed class HttpMessageHandlerStub : DelegatingHandler
{
    public HttpRequestHeaders? RequestHeaders { get; private set; }

    public HttpContentHeaders? ContentHeaders { get; private set; }

    public byte[]? RequestContent { get; private set; }

    public Uri? RequestUri { get; private set; }

    public HttpMethod? Method { get; private set; }

    public HttpResponseMessage ResponseToReturn { get; set; }

    public HttpMessageHandlerStub()
    {
        this.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("{}", Encoding.UTF8, "application/json")
        };
    }

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        this.Method = request.Method;
        this.RequestUri = request.RequestUri;
        this.RequestHeaders = request.Headers;
        if (request.Content is not null)
        {
#pragma warning disable CA2016 // Forward the 'CancellationToken' parameter to methods; overload doesn't exist on .NET Framework
            this.RequestContent = await request.Content.ReadAsByteArrayAsync();
#pragma warning restore CA2016
        }

        this.ContentHeaders = request.Content?.Headers;

        return await Task.FromResult(this.ResponseToReturn);
    }
}
