// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Mime;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.WebApi.Rest;
using Microsoft.SemanticKernel.Connectors.WebApi.Rest.Model;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Connectors.WebApi.Rest;

public sealed class RestApiOperationRunnerTests : IDisposable
{
    /// <summary>
    /// A mock instance of the authentication callback.
    /// </summary>
    private readonly Mock<AuthenticateRequestAsyncCallback> _authenticationHandlerMock;

    /// <summary>
    /// An instance of HttpMessageHandlerStub class used to get access to various properties of HttpRequestMessage sent by HTTP client.
    /// </summary>
    private readonly HttpMessageHandlerStub _httpMessageHandlerStub;

    /// <summary>
    /// An instance of HttpClient class used by the tests.
    /// </summary>
    private readonly HttpClient _httpClient;

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationRunnerTests"/> class.
    /// </summary>
    public RestApiOperationRunnerTests()
    {
        this._authenticationHandlerMock = new Mock<AuthenticateRequestAsyncCallback>();

        this._httpMessageHandlerStub = new HttpMessageHandlerStub();

        this._httpClient = new HttpClient(this._httpMessageHandlerStub);
    }

    [Fact]
    public async Task ItCanRunCrudOperationWithJsonPayloadSuccessfullyAsync()
    {
        // Arrange
        List<RestApiOperationPayloadProperty> payloadProperties = new()
        {
            new("value", "string", true, new List<RestApiOperationPayloadProperty>(), "fake-value-description"),
            new("attributes", "object", false, new List<RestApiOperationPayloadProperty>()
            {
                new("enabled", "boolean", false, new List<RestApiOperationPayloadProperty>(), "fake-enabled-description"),
            })
        };

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

        var operation = new RestApiOperation(
            "fake-id",
            "https://fake-random-test-host",
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            new Dictionary<string, string>(),
            payload
        );

        var arguments = new Dictionary<string, string>();
        arguments.Add("value", "fake-value");
        arguments.Add("enabled", "true");

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host/fake-path", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);

        Assert.Equal(HttpMethod.Post, this._httpMessageHandlerStub.Method);

        Assert.NotNull(this._httpMessageHandlerStub.ContentHeaders);
        Assert.Contains(this._httpMessageHandlerStub.ContentHeaders, h => h.Key == "Content-Type" && h.Value.Contains("application/json; charset=utf-8"));

        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.True(messageContent.Length != 0);

        var deserializedPayload = JsonNode.Parse(new MemoryStream(messageContent));
        Assert.NotNull(deserializedPayload);

        var valueProperty = deserializedPayload["value"]?.ToString();
        Assert.Equal("fake-value", valueProperty);

        var attributesProperty = deserializedPayload["attributes"];
        Assert.NotNull(attributesProperty);

        var enabledProperty = attributesProperty["enabled"]?.AsValue();
        Assert.NotNull(enabledProperty);
        Assert.Equal("true", enabledProperty.ToString());

        this._authenticationHandlerMock.Verify(x => x(It.IsAny<HttpRequestMessage>()), Times.Once);
    }

    [Fact]
    public async Task ItShouldAddHeadersToHttpRequestAsync()
    {
        // Arrange
        var headers = new Dictionary<string, string>();
        headers.Add("fake-header", string.Empty);

        var operation = new RestApiOperation(
            "fake-id",
            "https://fake-random-test-host",
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            headers
        );

        var arguments = new Dictionary<string, string>();
        arguments.Add("fake-header", "fake-header-value");

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestHeaders);
        Assert.Single(this._httpMessageHandlerStub.RequestHeaders);

        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "fake-header" && h.Value.Contains("fake-header-value"));
    }

    /// <summary>
    /// Disposes resources used by this class.
    /// </summary>
    public void Dispose()
    {
        this._httpMessageHandlerStub.Dispose();

        this._httpClient.Dispose();
    }

    private class HttpMessageHandlerStub : DelegatingHandler
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
