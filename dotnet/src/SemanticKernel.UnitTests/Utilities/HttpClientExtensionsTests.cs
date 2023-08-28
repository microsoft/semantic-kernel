// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Headers;
using System.Net.Http;
using System.Net.Mime;
using System.Text;
using System.Threading.Tasks;
using System.Threading;
using System;
using Xunit;
using Microsoft.SemanticKernel.Diagnostics;
using System.Net;

namespace SemanticKernel.UnitTests.Utilities;

public sealed class HttpClientExtensionsTests : IDisposable
{
    /// <summary>
    /// An instance of HttpMessageHandlerStub class used to get access to various properties of HttpRequestMessage sent by HTTP client.
    /// </summary>
    private readonly HttpMessageHandlerStub _httpMessageHandlerStub;

    /// <summary>
    /// An instance of HttpClient class used by the tests.
    /// </summary>
    private readonly HttpClient _httpClient;

    /// <summary>
    /// Creates an instance of a <see cref="HttpClientExtensionsTests"/> class.
    /// </summary>
    public HttpClientExtensionsTests()
    {
        this._httpMessageHandlerStub = new HttpMessageHandlerStub();

        this._httpClient = new HttpClient(this._httpMessageHandlerStub);
    }

    [Fact]
    public async Task ShouldReturnHttpResponseForSuccessefulRequestAsync()
    {
        //Arrange
        using var requestMessage = new HttpRequestMessage(HttpMethod.Get, "https://fake-random-test-host");

        //Act
        using var responseMessage = await this._httpClient.SendAndCheckSuccessAsync(requestMessage, CancellationToken.None);

        //Assert
        Assert.NotNull(responseMessage);

        Assert.Equal(HttpMethod.Get, this._httpMessageHandlerStub.Method);

        Assert.NotNull(this._httpMessageHandlerStub.ResponseToReturn);
        Assert.Equal(System.Net.HttpStatusCode.OK, this._httpMessageHandlerStub.ResponseToReturn.StatusCode);
    }

    [Fact]
    public async Task ShouldThrowHttpOperationExceptionForFailedRequestAsync()
    {
        //Arrange
        this._httpMessageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.InternalServerError);
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("{\"details\": \"fake-response-content\"}", Encoding.UTF8, MediaTypeNames.Application.Json);

        using var requestMessage = new HttpRequestMessage(HttpMethod.Get, "https://fake-random-test-host");

        //Act
        var exception = await Assert.ThrowsAsync<HttpOperationException>(() => this._httpClient.SendAndCheckSuccessAsync(requestMessage, CancellationToken.None));

        //Assert
        Assert.NotNull(exception);

        Assert.Equal(HttpStatusCode.InternalServerError, exception.StatusCode);

        Assert.Equal("Response status code does not indicate success: 500 (Internal Server Error).", exception.Message);

        Assert.Equal("{\"details\": \"fake-response-content\"}", exception.ResponseContent);

        Assert.True(exception.InnerException is HttpRequestException);
    }

    /// <summary>
    /// Disposes resources used by this class.
    /// </summary>
    public void Dispose()
    {
        this._httpMessageHandlerStub.Dispose();

        this._httpClient.Dispose();
    }

    private sealed class HttpMessageHandlerStub : DelegatingHandler
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
}
