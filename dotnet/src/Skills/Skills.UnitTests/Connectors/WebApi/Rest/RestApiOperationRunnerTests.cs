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
using Microsoft.SemanticKernel.Skills.OpenAPI;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;
using Moq;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.Connectors.WebApi.Rest;

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
    public async Task ItCanRunCreateAndUpdateOperationsWithJsonPayloadSuccessfullyAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        var payloadMetadata = new RestApiOperationPayload(MediaTypeNames.Application.Json, new List<RestApiOperationPayloadProperty>());

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            new Dictionary<string, string>(),
            payloadMetadata
        );

        var payload = new
        {
            value = "fake-value",
            attributes = new
            {
                enabled = true
            }
        };

        var arguments = new Dictionary<string, string>
        {
            { "payload", System.Text.Json.JsonSerializer.Serialize(payload) }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, arguments);

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

        Assert.NotNull(result);

        var contentProperty = result["content"]?.ToString();
        Assert.Equal("fake-content", contentProperty);

        var contentTypeProperty = result["contentType"]?.ToString();
        Assert.Equal("application/json; charset=utf-8", contentTypeProperty);

        this._authenticationHandlerMock.Verify(x => x(It.IsAny<HttpRequestMessage>()), Times.Once);
    }

    [Fact]
    public async Task ItCanRunCreateAndUpdateOperationsWithPlainTextPayloadSuccessfullyAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Text.Plain);

        var payload = new RestApiOperationPayload(MediaTypeNames.Text.Plain, new List<RestApiOperationPayloadProperty>(), "fake-description");

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            new Dictionary<string, string>(),
            payload
        );

        var arguments = new Dictionary<string, string>
        {
            { "payload", "fake-input-value" }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host/fake-path", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);

        Assert.Equal(HttpMethod.Post, this._httpMessageHandlerStub.Method);

        Assert.NotNull(this._httpMessageHandlerStub.ContentHeaders);
        Assert.Contains(this._httpMessageHandlerStub.ContentHeaders, h => h.Key == "Content-Type" && h.Value.Contains("text/plain; charset=utf-8"));

        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.True(messageContent.Length != 0);

        var payloadText = System.Text.Encoding.UTF8.GetString(messageContent, 0, messageContent.Length);
        Assert.Equal("fake-input-value", payloadText);

        Assert.NotNull(result);

        var contentProperty = result["content"]?.ToString();
        Assert.Equal("fake-content", contentProperty);

        var contentTypeProperty = result["contentType"]?.ToString();
        Assert.Equal("text/plain; charset=utf-8", contentTypeProperty);

        this._authenticationHandlerMock.Verify(x => x(It.IsAny<HttpRequestMessage>()), Times.Once);
    }

    [Fact]
    public async Task ItShouldAddHeadersToHttpRequestAsync()
    {
        // Arrange
        var headers = new Dictionary<string, string>
        {
            { "fake-header", string.Empty }
        };

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            new List<RestApiOperationParameter>(),
            headers
        );

        var arguments = new Dictionary<string, string>
        {
            { "fake-header", "fake-header-value" }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        await sut.RunAsync(operation, arguments);

        // Assert - 2 headers: 1 from the test and the useragent added internally
        Assert.NotNull(this._httpMessageHandlerStub.RequestHeaders);
        Assert.Equal(2, this._httpMessageHandlerStub.RequestHeaders.Count());

        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "fake-header" && h.Value.Contains("fake-header-value"));
    }

    [Fact]
    public async Task ItShouldAddUserAgentHeaderToHttpRequestIfConfiguredAsync()
    {
        // Arrange
        var headers = new Dictionary<string, string>
        {
            { "fake-header", string.Empty }
        };

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            new List<RestApiOperationParameter>(),
            headers
        );

        var arguments = new Dictionary<string, string>
        {
            { "fake-header", "fake-header-value" }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, "fake-user-agent");

        // Act
        await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestHeaders);
        Assert.Equal(2, this._httpMessageHandlerStub.RequestHeaders.Count());

        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "fake-header" && h.Value.Contains("fake-header-value"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "User-Agent" && h.Value.Contains("fake-user-agent"));
    }

    [Fact]
    public async Task ItShouldUsePayloadAndContentTypeArgumentsIfPayloadMetadataIsMissingAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            new Dictionary<string, string>()
        );

        var payload = new
        {
            value = "fake-value",
            attributes = new
            {
                enabled = true
            }
        };

        var arguments = new Dictionary<string, string>
        {
            { "payload", System.Text.Json.JsonSerializer.Serialize(payload) },
            { "content-type", "application/json" }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
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
            this.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent("{}", Encoding.UTF8, MediaTypeNames.Application.Json)
            };
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
