// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Mime;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace SemanticKernel.Functions.UnitTests.OpenAPI;

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
        this.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        this.ResponseToReturn.Content = new StringContent("{}", Encoding.UTF8, MediaTypeNames.Application.Json);
    }

    public HttpMessageHandlerStub(Stream responseToReturn)
    {
        this.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        this.ResponseToReturn.Content = new StreamContent(responseToReturn);
    }

    public void ResetResponse()
    {
        this.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        this.ResponseToReturn.Content = new StringContent("{}", Encoding.UTF8, MediaTypeNames.Application.Json);
    }

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        this.Method = request.Method;
        this.RequestUri = request.RequestUri;
        this.RequestHeaders = request.Headers;
        this.RequestContent = request.Content == null ? null : await request.Content.ReadAsByteArrayAsync(cancellationToken);
        this.ContentHeaders = request.Content?.Headers;

        return await Task.FromResult(this.ResponseToReturn);
    }
}
