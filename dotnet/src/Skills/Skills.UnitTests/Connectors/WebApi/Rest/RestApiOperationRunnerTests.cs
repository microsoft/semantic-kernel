// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Mime;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
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

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            new Dictionary<string, string>(),
            payload: null
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

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            new Dictionary<string, string>(),
            payload: null
        );

        var arguments = new Dictionary<string, string>
        {
            { "payload", "fake-input-value" },
            { "content-type", "text/plain"}
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
    public async Task ItShouldBuildJsonPayloadDynamicallyAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        List<RestApiOperationPayloadProperty> payloadProperties = new()
        {
            new("name", "string", true, new List<RestApiOperationPayloadProperty>()),
            new("attributes", "object", false, new List<RestApiOperationPayloadProperty>()
            {
                new("enabled", "boolean", false, new List<RestApiOperationPayloadProperty>()),
            })
        };

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

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

        var arguments = new Dictionary<string, string>();
        arguments.Add("name", "fake-name-value");
        arguments.Add("enabled", "true");

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, buildPayloadDynamically: true);

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

        var name = deserializedPayload["name"]?.ToString();
        Assert.Equal("fake-name-value", name);

        var attributes = deserializedPayload["attributes"];
        Assert.NotNull(attributes);

        var enabled = attributes["enabled"]?.ToString();
        Assert.NotNull(enabled);
        Assert.Equal("true", enabled);
    }

    [Fact]
    public async Task ItShouldBuildJsonPayloadDynamicallyUsingPayloadMetadataDataTypesAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        List<RestApiOperationPayloadProperty> payloadProperties = new()
        {
            new("name", "string", true, new List<RestApiOperationPayloadProperty>()),
            new("attributes", "object", false, new List<RestApiOperationPayloadProperty>()
            {
                new("enabled", "boolean", false, new List<RestApiOperationPayloadProperty>()),
                new("cardinality", "number", false, new List<RestApiOperationPayloadProperty>()),
                new("coefficient", "number", false, new List<RestApiOperationPayloadProperty>()),
                new("count", "integer", false, new List<RestApiOperationPayloadProperty>()),
                new("params", "array", false, new List<RestApiOperationPayloadProperty>()),
            })
        };

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

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

        var arguments = new Dictionary<string, string>();
        arguments.Add("name", "fake-string-value");
        arguments.Add("enabled", "true");
        arguments.Add("cardinality", "8");
        arguments.Add("coefficient", "0.8");
        arguments.Add("count", "1");
        arguments.Add("params", "[1,2,3]");

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, buildPayloadDynamically: true);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);

        var deserializedPayload = JsonNode.Parse(new MemoryStream(messageContent));
        Assert.NotNull(deserializedPayload);

        var name = deserializedPayload["name"]?.GetValue<JsonElement>();
        Assert.NotNull(name);
        Assert.Equal(JsonValueKind.String, name.Value.ValueKind);
        Assert.Equal("fake-string-value", name.ToString());

        var attributes = deserializedPayload["attributes"];
        Assert.True(attributes is JsonObject);

        var enabled = attributes["enabled"]?.GetValue<JsonElement>();
        Assert.NotNull(enabled);
        Assert.Equal(JsonValueKind.True, enabled.Value.ValueKind);

        var cardinality = attributes["cardinality"]?.GetValue<JsonElement>();
        Assert.NotNull(cardinality);
        Assert.Equal(JsonValueKind.Number, cardinality.Value.ValueKind);
        Assert.Equal("8", cardinality.Value.ToString());

        var coefficient = attributes["coefficient"]?.GetValue<JsonElement>();
        Assert.NotNull(coefficient);
        Assert.Equal(JsonValueKind.Number, coefficient.Value.ValueKind);
        Assert.Equal("0.8", coefficient.Value.ToString());

        var count = attributes["count"]?.GetValue<JsonElement>();
        Assert.NotNull(count);
        Assert.Equal(JsonValueKind.Number, coefficient.Value.ValueKind);
        Assert.Equal("1", count.Value.ToString());

        var parameters = attributes["params"];
        Assert.NotNull(parameters);
        Assert.True(parameters is JsonArray);
    }

    [Fact]
    public async Task ItShouldBuildJsonPayloadDynamicallyResolvingArgumentsByFullNamesAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        List<RestApiOperationPayloadProperty> payloadProperties = new()
        {
            new("upn", "string", true, new List<RestApiOperationPayloadProperty>()),
            new("receiver", "object", false, new List<RestApiOperationPayloadProperty>()
            {
                new("upn", "string", false, new List<RestApiOperationPayloadProperty>()),
                new("alternative", "object", false, new List<RestApiOperationPayloadProperty>()
                {
                    new("upn", "string", false, new List<RestApiOperationPayloadProperty>()),
                }),
            }),
            new("cc", "object", false, new List<RestApiOperationPayloadProperty>()
            {
                new("upn", "string", false, new List<RestApiOperationPayloadProperty>()),
            })
        };

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

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

        var arguments = new Dictionary<string, string>();
        arguments.Add("upn", "fake-sender-upn");
        arguments.Add("receiver.upn", "fake-receiver-upn");
        arguments.Add("receiver.alternative.upn", "fake-receiver-alternative-upn");
        arguments.Add("cc.upn", "fake-cc-upn");

        var sut = new RestApiOperationRunner(
            this._httpClient,
            this._authenticationHandlerMock.Object,
            buildPayloadDynamically: true,
            resolvePayloadArgumentsByFullName: true);

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

        //Sender props
        var senderUpn = deserializedPayload["upn"]?.ToString();
        Assert.Equal("fake-sender-upn", senderUpn);

        //Receiver props
        var receiver = deserializedPayload["receiver"];
        Assert.NotNull(receiver);

        var receiverUpn = receiver["upn"]?.AsValue();
        Assert.NotNull(receiverUpn);
        Assert.Equal("fake-receiver-upn", receiverUpn.ToString());

        var alternative = receiver["alternative"];
        Assert.NotNull(alternative);

        var alternativeUpn = alternative["upn"]?.AsValue();
        Assert.NotNull(alternativeUpn);
        Assert.Equal("fake-receiver-alternative-upn", alternativeUpn.ToString());

        //CC props
        var carbonCopy = deserializedPayload["cc"];
        Assert.NotNull(carbonCopy);

        var ccUpn = carbonCopy["upn"]?.AsValue();
        Assert.NotNull(ccUpn);
        Assert.Equal("fake-cc-upn", ccUpn.ToString());
    }

    [Fact]
    public async Task ItShouldThrowExceptionIfPayloadMetadataDoesNotHaveContentTypeAsync()
    {
        // Arrange
        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            new Dictionary<string, string>(),
            payload: null
        );

        var arguments = new Dictionary<string, string>();

        var sut = new RestApiOperationRunner(
            this._httpClient,
            this._authenticationHandlerMock.Object,
            buildPayloadDynamically: true);

        // Act
        var exception = await Assert.ThrowsAsync<SKException>(async () => await sut.RunAsync(operation, arguments));

        Assert.Contains("No content type is provided", exception.Message, StringComparison.InvariantCulture);
    }

    [Fact]
    public async Task ItShouldThrowExceptionIfContentTypeArgumentIsNotProvidedAsync()
    {
        // Arrange
        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            new Dictionary<string, string>(),
            payload: null
        );

        var arguments = new Dictionary<string, string>();

        var sut = new RestApiOperationRunner(
            this._httpClient,
            this._authenticationHandlerMock.Object,
            buildPayloadDynamically: false);

        // Act
        var exception = await Assert.ThrowsAsync<SKException>(async () => await sut.RunAsync(operation, arguments));

        Assert.Contains("No content type is provided", exception.Message, StringComparison.InvariantCulture);
    }

    [Fact]
    public async Task ItShouldUsePayloadArgumentForPlainTextContentTypeWhenBuildingPayloadDynamicallyAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Text.Plain);

        var payload = new RestApiOperationPayload(MediaTypeNames.Text.Plain, new List<RestApiOperationPayloadProperty>());

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
            { "payload", "fake-input-value" },
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, buildPayloadDynamically: true);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.ContentHeaders);
        Assert.Contains(this._httpMessageHandlerStub.ContentHeaders, h => h.Key == "Content-Type" && h.Value.Contains("text/plain; charset=utf-8"));

        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.True(messageContent.Length != 0);

        var payloadText = System.Text.Encoding.UTF8.GetString(messageContent, 0, messageContent.Length);
        Assert.Equal("fake-input-value", payloadText);
    }

    [Theory]
    [InlineData(MediaTypeNames.Text.Plain)]
    [InlineData(MediaTypeNames.Application.Json)]
    public async Task ItShouldUsePayloadAndContentTypeArgumentsIfDynamicPayloadBuildingIsNotRequired(string contentType)
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Text.Plain);

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            new Dictionary<string, string>(),
            payload: null
        );

        var arguments = new Dictionary<string, string>
        {
            { "payload", "fake-input-value" },
            { "content-type", $"{contentType}" },
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, buildPayloadDynamically: false);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.ContentHeaders);
        Assert.Contains(this._httpMessageHandlerStub.ContentHeaders, h => h.Key == "Content-Type" && h.Value.Contains($"{contentType}; charset=utf-8"));

        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.True(messageContent.Length != 0);

        var payloadText = System.Text.Encoding.UTF8.GetString(messageContent, 0, messageContent.Length);
        Assert.Equal("fake-input-value", payloadText);
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
