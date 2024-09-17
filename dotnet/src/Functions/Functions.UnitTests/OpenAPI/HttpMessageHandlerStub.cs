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

    public Func<HttpRequestMessage, HttpResponseMessage> ResponseToReturnProvider { get; set; }

    public HttpMessageHandlerStub()
    {
        this.ResponseToReturnProvider = (_) =>
        {
            var response = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
            response.Content = new StringContent("{}", Encoding.UTF8, MediaTypeNames.Application.Json);
            return response;
        };
    }

    public HttpMessageHandlerStub(Stream responseToReturn)
    {
        this.ResponseToReturnProvider = (_) =>
        {
            var response = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
            response.Content = new StreamContent(responseToReturn);
            return response;
        };
    }

    public HttpMessageHandlerStub(HttpContent content)
    {
        this.ResponseToReturnProvider = (_) =>
        {
            var response = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
            response.Content = content;
            return response;
        };
    }

    public HttpMessageHandlerStub(Func<HttpRequestMessage, HttpResponseMessage> responseToReturn)
    {
        this.ResponseToReturnProvider = responseToReturn;
    }

    public void ResetResponse()
    {
        this.ResponseToReturnProvider = (_) =>
        {
            var response = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
            response.Content = new StringContent("{}", Encoding.UTF8, MediaTypeNames.Application.Json);
            return response;
        };
    }

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        this.Method = request.Method;
        this.RequestUri = request.RequestUri;
        this.RequestHeaders = request.Headers;
        this.RequestContent = request.Content == null ? null : await request.Content.ReadAsByteArrayAsync(cancellationToken);
        this.ContentHeaders = request.Content?.Headers;

        return await Task.FromResult(this.ResponseToReturnProvider(request));
    }
}
