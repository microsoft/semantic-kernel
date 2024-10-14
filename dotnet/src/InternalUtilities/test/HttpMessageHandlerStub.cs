﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Mime;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

#pragma warning disable CA1812 // Internal class that is apparently never instantiated; this class is compiled in tests projects
internal sealed class HttpMessageHandlerStub : DelegatingHandler
#pragma warning restore CA1812 // Internal class that is apparently never instantiated
{
    public HttpRequestHeaders? RequestHeaders { get; private set; }

    public HttpContentHeaders? ContentHeaders { get; private set; }

    public byte[]? RequestContent { get; private set; }

    public Uri? RequestUri { get; private set; }

    public HttpMethod? Method { get; private set; }

    public HttpResponseMessage ResponseToReturn { get; set; }

    public Queue<HttpResponseMessage> ResponseQueue { get; } = new();
    public byte[]? FirstMultipartContent { get; private set; }

    public HttpMessageHandlerStub()
    {
        this.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("{}", Encoding.UTF8, MediaTypeNames.Application.Json),
        };
    }

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        this.Method = request.Method;
        this.RequestUri = request.RequestUri;
        this.RequestHeaders = request.Headers;
        this.RequestContent = request.Content is null ? null : await request.Content.ReadAsByteArrayAsync(cancellationToken);

        if (request.Content is MultipartContent multipartContent)
        {
            this.FirstMultipartContent = await multipartContent.First().ReadAsByteArrayAsync(cancellationToken);
        }

        this.ContentHeaders = request.Content?.Headers;

        HttpResponseMessage response =
            this.ResponseQueue.Count == 0 ?
                this.ResponseToReturn :
                this.ResponseToReturn = this.ResponseQueue.Dequeue();

        return await Task.FromResult(response);
    }

    /// <summary>
    /// Converts the binary request content to a string using the specified encoding.
    /// </summary>
    /// <param name="encoding">Specifies the encoding to use. If not specified, defaults to UTF-8.</param>
    /// <returns> The request content as a string.</returns>
    public string? GetRequestContentAsString(Encoding? encoding = null)
    {
        encoding ??= Encoding.UTF8;

        return this.RequestContent is null ? null : encoding.GetString(this.RequestContent);
    }
}
