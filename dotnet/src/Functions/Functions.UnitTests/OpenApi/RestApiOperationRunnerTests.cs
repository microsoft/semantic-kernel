﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Collections.ObjectModel;
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
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Moq;
using SemanticKernel.Functions.UnitTests.OpenApi.TestResponses;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

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

    [Theory]
    [InlineData("POST")]
    [InlineData("PUT")]
    [InlineData("PATCH")]
    [InlineData("DELETE")]
    [InlineData("GET")]
    public async Task ItCanRunCreateAndUpdateOperationsWithJsonPayloadSuccessfullyAsync(string method)
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        var httpMethod = new HttpMethod(method);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            httpMethod,
            "fake-description",
            [],
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

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(payload) },
            { "content-type", "application/json" }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host/fake-path", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);

        Assert.Equal(httpMethod, this._httpMessageHandlerStub.Method);

        Assert.NotNull(this._httpMessageHandlerStub.ContentHeaders);
        Assert.Contains(this._httpMessageHandlerStub.ContentHeaders, h => h.Key == "Content-Type" && h.Value.Contains("application/json; charset=utf-8"));

        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.NotEmpty(messageContent);

        var deserializedPayload = await JsonNode.ParseAsync(new MemoryStream(messageContent));
        Assert.NotNull(deserializedPayload);

        var valueProperty = deserializedPayload["value"]?.ToString();
        Assert.Equal("fake-value", valueProperty);

        var attributesProperty = deserializedPayload["attributes"];
        Assert.NotNull(attributesProperty);

        var enabledProperty = attributesProperty["enabled"]?.AsValue();
        Assert.NotNull(enabledProperty);
        Assert.Equal("true", enabledProperty.ToString());

        Assert.NotNull(result);

        Assert.Equal("fake-content", result.Content);

        Assert.Equal("application/json; charset=utf-8", result.ContentType);

        this._authenticationHandlerMock.Verify(x => x(It.IsAny<HttpRequestMessage>(), It.IsAny<CancellationToken>()), Times.Once);
    }

    [Theory]
    [InlineData("POST")]
    [InlineData("PUT")]
    [InlineData("PATCH")]
    [InlineData("DELETE")]
    [InlineData("GET")]
    public async Task ItCanRunCreateAndUpdateOperationsWithPlainTextPayloadSuccessfullyAsync(string method)
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Text.Plain);

        var httpMethod = new HttpMethod(method);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            httpMethod,
            "fake-description",
            [],
            payload: null
        );

        var arguments = new KernelArguments
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

        Assert.Equal(httpMethod, this._httpMessageHandlerStub.Method);

        Assert.NotNull(this._httpMessageHandlerStub.ContentHeaders);
        Assert.Contains(this._httpMessageHandlerStub.ContentHeaders, h => h.Key == "Content-Type" && h.Value.Contains("text/plain; charset=utf-8"));

        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.NotEmpty(messageContent);

        var payloadText = Encoding.UTF8.GetString(messageContent, 0, messageContent.Length);
        Assert.Equal("fake-input-value", payloadText);

        Assert.NotNull(result);

        Assert.Equal("fake-content", result.Content);

        Assert.Equal("text/plain; charset=utf-8", result.ContentType);

        this._authenticationHandlerMock.Verify(x => x(It.IsAny<HttpRequestMessage>(), It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task ItShouldAddHeadersToHttpRequestAsync()
    {
        // Arrange
        var parameters = new List<RestApiOperationParameter>
        {
            new(name: "X-HS-1", type: "string", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "X-HA-1", type: "array", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "X-HA-2", type: "array", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "X-HB-1", type: "boolean", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "X-HB-2", type: "boolean", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "X-HI-1", type: "integer", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "X-HI-2", type: "integer", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "X-HN-1", type: "number", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "X-HN-2", type: "number", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "X-HD-1", type: "string", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "X-HD-2", type: "string", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "X-HD-3", type: "string", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
        };

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            parameters
        );

        var arguments = new KernelArguments
        {
            ["X-HS-1"] = "fake-header-value",
            ["X-HA-1"] = "[1,2,3]",
            ["X-HA-2"] = new Collection<string>() { "3", "4", "5" },
            ["X-HB-1"] = "true",
            ["X-HB-2"] = false,
            ["X-HI-1"] = "10",
            ["X-HI-2"] = 20,
            ["X-HN-1"] = 5698.4567,
            ["X-HN-2"] = "5698.4567",
            ["X-HD-1"] = "2023-12-06T11:53:36Z",
            ["X-HD-2"] = new DateTime(2023, 12, 06, 11, 53, 36, DateTimeKind.Utc),
            ["X-HD-3"] = new DateTimeOffset(2023, 12, 06, 11, 53, 36, TimeSpan.FromHours(-2)),
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, userAgent: "fake-agent");

        // Act
        await sut.RunAsync(operation, arguments);

        // Assert - 13 headers: 12 from the test and the User-Agent added internally
        Assert.NotNull(this._httpMessageHandlerStub.RequestHeaders);
        Assert.Equal(14, this._httpMessageHandlerStub.RequestHeaders.Count());

        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "User-Agent" && h.Value.Contains("fake-agent"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-HS-1" && h.Value.Contains("fake-header-value"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-HA-1" && h.Value.Contains("1,2,3"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-HA-2" && h.Value.Contains("3,4,5"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-HB-1" && h.Value.Contains("true"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-HB-2" && h.Value.Contains("false"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-HI-1" && h.Value.Contains("10"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-HI-2" && h.Value.Contains("20"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-HN-1" && h.Value.Contains("5698.4567"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-HN-2" && h.Value.Contains("5698.4567"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-HD-1" && h.Value.Contains("2023-12-06T11:53:36Z"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-HD-2" && h.Value.Contains("2023-12-06T11:53:36Z"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-HD-3" && h.Value.Contains("2023-12-06T11:53:36-02:00"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "Semantic-Kernel-Version");
    }

    [Fact]
    public async Task ItShouldAddUserAgentHeaderToHttpRequestIfConfiguredAsync()
    {
        // Arrange
        var parameters = new List<RestApiOperationParameter>
        {
            new(
            name: "fake-header",
            type: "string",
            isRequired: true,
            expand: false,
            location: RestApiOperationParameterLocation.Header,
            style: RestApiOperationParameterStyle.Simple)
        };

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            parameters
        );

        var arguments = new KernelArguments
        {
            { "fake-header", "fake-header-value" }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, "fake-user-agent");

        // Act
        await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestHeaders);
        Assert.Equal(3, this._httpMessageHandlerStub.RequestHeaders.Count());

        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "fake-header" && h.Value.Contains("fake-header-value"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "User-Agent" && h.Value.Contains("fake-user-agent"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "Semantic-Kernel-Version");
    }

    [Fact]
    public async Task ItShouldBuildJsonPayloadDynamicallyAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        List<RestApiOperationPayloadProperty> payloadProperties =
        [
            new("name", "string", true, []),
            new("attributes", "object", false,
            [
                new("enabled", "boolean", false, []),
            ])
        ];

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload
        );

        var arguments = new KernelArguments
        {
            { "name", "fake-name-value" },
            { "enabled", true }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, enableDynamicPayload: true);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.ContentHeaders);
        Assert.Contains(this._httpMessageHandlerStub.ContentHeaders, h => h.Key == "Content-Type" && h.Value.Contains("application/json; charset=utf-8"));

        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.NotEmpty(messageContent);

        var deserializedPayload = await JsonNode.ParseAsync(new MemoryStream(messageContent));
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

        List<RestApiOperationPayloadProperty> payloadProperties =
        [
            new("name", "string", true, []),
            new("attributes", "object", false,
            [
                new("enabled", "boolean", false, []),
                new("cardinality", "number", false, []),
                new("coefficient", "number", false, []),
                new("count", "integer", false, []),
                new("params", "array", false, []),
            ])
        ];

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload
        );

        var arguments = new KernelArguments
        {
            { "name", "fake-string-value" },
            { "enabled", "true" },
            { "cardinality", 8 },
            { "coefficient", "0.8" },
            { "count", 1 },
            { "params", "[1,2,3]" }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, enableDynamicPayload: true);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);

        var deserializedPayload = await JsonNode.ParseAsync(new MemoryStream(messageContent));
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

        List<RestApiOperationPayloadProperty> payloadProperties =
        [
            new("upn", "string", true, []),
            new("receiver", "object", false,
            [
                new("upn", "string", false, []),
                new("alternative", "object", false,
                [
                    new("upn", "string", false, []),
                ]),
            ]),
            new("cc", "object", false,
            [
                new("upn", "string", false, []),
            ])
        ];

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload
        );

        var arguments = new KernelArguments
        {
            { "upn", "fake-sender-upn" },
            { "receiver.upn", "fake-receiver-upn" },
            { "receiver.alternative.upn", "fake-receiver-alternative-upn" },
            { "cc.upn", "fake-cc-upn" }
        };

        var sut = new RestApiOperationRunner(
            this._httpClient,
            this._authenticationHandlerMock.Object,
            enableDynamicPayload: true,
            enablePayloadNamespacing: true);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.ContentHeaders);
        Assert.Contains(this._httpMessageHandlerStub.ContentHeaders, h => h.Key == "Content-Type" && h.Value.Contains("application/json; charset=utf-8"));

        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.NotEmpty(messageContent);

        var deserializedPayload = await JsonNode.ParseAsync(new MemoryStream(messageContent));
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
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload: null
        );

        KernelArguments arguments = new() { { RestApiOperation.PayloadArgumentName, "fake-content" } };

        var sut = new RestApiOperationRunner(
            this._httpClient,
            this._authenticationHandlerMock.Object,
            enableDynamicPayload: true);

        // Act
        var exception = await Assert.ThrowsAsync<KernelException>(async () => await sut.RunAsync(operation, arguments));

        Assert.Contains("No media type is provided", exception.Message, StringComparison.InvariantCulture);
    }

    [Fact]
    public async Task ItShouldThrowExceptionIfContentTypeArgumentIsNotProvidedAsync()
    {
        // Arrange
        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload: null
        );

        KernelArguments arguments = new() { { RestApiOperation.PayloadArgumentName, "fake-content" } };

        var sut = new RestApiOperationRunner(
            this._httpClient,
            this._authenticationHandlerMock.Object,
            enableDynamicPayload: false);

        // Act
        var exception = await Assert.ThrowsAsync<KernelException>(async () => await sut.RunAsync(operation, arguments));

        Assert.Contains("No media type is provided", exception.Message, StringComparison.InvariantCulture);
    }

    [Fact]
    public async Task ItShouldUsePayloadArgumentForPlainTextContentTypeWhenBuildingPayloadDynamicallyAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Text.Plain);

        var payload = new RestApiOperationPayload(MediaTypeNames.Text.Plain, []);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload
        );

        var arguments = new KernelArguments
        {
            { "payload", "fake-input-value" },
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, enableDynamicPayload: true);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.ContentHeaders);
        Assert.Contains(this._httpMessageHandlerStub.ContentHeaders, h => h.Key == "Content-Type" && h.Value.Contains("text/plain; charset=utf-8"));

        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.NotEmpty(messageContent);

        var payloadText = Encoding.UTF8.GetString(messageContent, 0, messageContent.Length);
        Assert.Equal("fake-input-value", payloadText);
    }

    [Theory]
    [InlineData(MediaTypeNames.Text.Plain)]
    [InlineData(MediaTypeNames.Application.Json)]
    public async Task ItShouldUsePayloadAndContentTypeArgumentsIfDynamicPayloadBuildingIsNotRequiredAsync(string contentType)
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Text.Plain);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload: null
        );

        var arguments = new KernelArguments
        {
            { "payload", "fake-input-value" },
            { "content-type", $"{contentType}" },
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, enableDynamicPayload: false);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.ContentHeaders);
        Assert.Contains(this._httpMessageHandlerStub.ContentHeaders, h => h.Key == "Content-Type" && h.Value.Contains($"{contentType}; charset=utf-8"));

        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.NotEmpty(messageContent);

        var payloadText = Encoding.UTF8.GetString(messageContent, 0, messageContent.Length);
        Assert.Equal("fake-input-value", payloadText);
    }

    [Fact]
    public async Task ItShouldBuildJsonPayloadDynamicallyExcludingOptionalParametersIfTheirArgumentsNotProvidedAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        List<RestApiOperationPayloadProperty> payloadProperties =
        [
            new("upn", "string", false, []),
        ];

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload
        );

        var arguments = new KernelArguments();

        var sut = new RestApiOperationRunner(
            this._httpClient,
            this._authenticationHandlerMock.Object,
            enableDynamicPayload: true,
            enablePayloadNamespacing: true);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.NotEmpty(messageContent);

        var deserializedPayload = await JsonNode.ParseAsync(new MemoryStream(messageContent));
        Assert.NotNull(deserializedPayload);

        var senderUpn = deserializedPayload["upn"]?.ToString();
        Assert.Null(senderUpn);
    }

    [Fact]
    public async Task ItShouldBuildJsonPayloadDynamicallyIncludingOptionalParametersIfTheirArgumentsProvidedAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        List<RestApiOperationPayloadProperty> payloadProperties =
        [
            new("upn", "string", false, []),
        ];

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload
        );

        var arguments = new KernelArguments { ["upn"] = "fake-sender-upn" };

        var sut = new RestApiOperationRunner(
            this._httpClient,
            this._authenticationHandlerMock.Object,
            enableDynamicPayload: true,
            enablePayloadNamespacing: true);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.NotEmpty(messageContent);

        var deserializedPayload = await JsonNode.ParseAsync(new MemoryStream(messageContent));
        Assert.NotNull(deserializedPayload);

        var senderUpn = deserializedPayload["upn"]?.ToString();
        Assert.Equal("fake-sender-upn", senderUpn);
    }

    [Fact]
    public async Task ItShouldAddRequiredQueryStringParametersIfTheirArgumentsProvidedAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        var firstParameter = new RestApiOperationParameter(
            "p1",
            "string",
            isRequired: true, //Marking the parameter as required
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

        var secondParameter = new RestApiOperationParameter(
            "p2",
            "integer",
            isRequired: true, //Marking the parameter as required
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            [firstParameter, secondParameter],
            payload: null
        );

        var arguments = new KernelArguments
        {
            { "p1", "v1" },
            { "p2", 28 },
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host/fake-path?p1=v1&p2=28", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);
    }

    [Fact]
    public async Task ItShouldAddNotRequiredQueryStringParametersIfTheirArgumentsProvidedAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        var firstParameter = new RestApiOperationParameter(
            "p1",
            "string",
            isRequired: false, //Marking the parameter as not required
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

        var secondParameter = new RestApiOperationParameter(
            "p2",
            "string",
            isRequired: false, //Marking the parameter as not required
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            [firstParameter, secondParameter],
            payload: null
        );

        var arguments = new KernelArguments
        {
            { "p1", new DateTime(2023, 12, 06, 11, 53, 36, DateTimeKind.Utc) },
            { "p2", "v2" },
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host/fake-path?p1=2023-12-06T11%3a53%3a36Z&p2=v2", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);
    }

    [Fact]
    public async Task ItShouldSkipNotRequiredQueryStringParametersIfNoArgumentsProvidedAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        var firstParameter = new RestApiOperationParameter(
            "p1",
            "string",
            isRequired: false, //Marking the parameter as not required
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

        var secondParameter = new RestApiOperationParameter(
            "p2",
            "string",
            isRequired: true, //Marking the parameter as required
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            [firstParameter, secondParameter],
            payload: null
        );

        var arguments = new KernelArguments
        {
            { "p2", "v2" }, //Providing argument for the required parameter only
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host/fake-path?p2=v2", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);
    }

    [Fact]
    public async Task ItShouldThrowExceptionIfNoArgumentProvidedForRequiredQueryStringParameterAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        var parameter = new RestApiOperationParameter(
            "p1",
            "string",
            isRequired: true, //Marking the parameter as required
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            [parameter],
            payload: null
        );

        var arguments = new KernelArguments(); //Providing no arguments

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act and Assert
        await Assert.ThrowsAsync<KernelException>(() => sut.RunAsync(operation, arguments));
    }

    [Theory]
    [InlineData(MediaTypeNames.Application.Json)]
    [InlineData(MediaTypeNames.Application.Xml)]
    [InlineData(MediaTypeNames.Text.Plain)]
    [InlineData(MediaTypeNames.Text.Html)]
    [InlineData(MediaTypeNames.Text.Xml)]
    [InlineData("text/csv")]
    [InlineData("text/markdown")]
    public async Task ItShouldReadContentAsStringSuccessfullyAsync(string contentType)
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, contentType);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload: null
        );

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { value = "fake-value" }) },
            { "content-type", "application/json" }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("fake-content", result.Content);

        Assert.Equal($"{contentType}; charset=utf-8", result.ContentType);
    }

    [Theory]
    [InlineData("image/jpeg")]
    [InlineData("image/png")]
    [InlineData("image/gif")]
    [InlineData("image/svg+xml")]
    [InlineData("image/bmp")]
    [InlineData("image/x-icon")]
    public async Task ItShouldReadContentAsBytesSuccessfullyAsync(string contentType)
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new ByteArrayContent([00, 01, 02]);
        this._httpMessageHandlerStub.ResponseToReturn.Content.Headers.ContentType = new MediaTypeHeaderValue(contentType);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload: null
        );

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { value = "fake-value" }) },
            { "content-type", "application/json" }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal(new byte[] { 00, 01, 02 }, result.Content);

        Assert.Equal($"{contentType}", result.ContentType);
    }

    [Fact]
    public async Task ItShouldThrowExceptionForUnsupportedContentTypeAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, "fake/type");

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload: null
        );

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { value = "fake-value" }) },
            { "content-type", "application/json" }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act & Assert
        var kernelException = await Assert.ThrowsAsync<KernelException>(() => sut.RunAsync(operation, arguments));
        Assert.Equal("The content type `fake/type` is not supported.", kernelException.Message);
        Assert.Equal("POST", kernelException.Data["http.request.method"]);
        Assert.Equal("https://fake-random-test-host/fake-path", kernelException.Data["url.full"]);
        Assert.Equal("{\"value\":\"fake-value\"}", kernelException.Data["http.request.body"]);
    }

    [Fact]
    public async Task ItShouldReturnRequestUriAndContentAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        List<RestApiOperationPayloadProperty> payloadProperties =
        [
            new("name", "string", true, []),
            new("attributes", "object", false,
            [
                new("enabled", "boolean", false, []),
            ])
        ];

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload
        );

        var arguments = new KernelArguments
        {
            { "name", "fake-name-value" },
            { "enabled", true }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, enableDynamicPayload: true);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(result.RequestMethod);
        Assert.Equal(HttpMethod.Post.Method, result.RequestMethod);
        Assert.NotNull(result.RequestUri);
        Assert.Equal("https://fake-random-test-host/fake-path", result.RequestUri.AbsoluteUri);
        Assert.NotNull(result.RequestPayload);
        Assert.IsType<JsonObject>(result.RequestPayload);
        Assert.Equal("{\"name\":\"fake-name-value\",\"attributes\":{\"enabled\":true}}", ((JsonObject)result.RequestPayload).ToJsonString());
    }

    [Fact]
    public async Task ItShouldHandleNoContentAsync()
    {
        // Arrange
        this._httpMessageHandlerStub!.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.NoContent);

        List<RestApiOperationPayloadProperty> payloadProperties =
        [
            new("name", "string", true, []),
            new("attributes", "object", false,
            [
                new("enabled", "boolean", false, []),
            ])
        ];

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload
        );

        var arguments = new KernelArguments
        {
            { "name", "fake-name-value" },
            { "enabled", true }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, enableDynamicPayload: true);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(result.RequestMethod);
        Assert.Equal(HttpMethod.Post.Method, result.RequestMethod);
        Assert.NotNull(result.RequestUri);
        Assert.Equal("https://fake-random-test-host/fake-path", result.RequestUri.AbsoluteUri);
        Assert.NotNull(result.RequestPayload);
        Assert.IsType<JsonObject>(result.RequestPayload);
        Assert.Equal("{\"name\":\"fake-name-value\",\"attributes\":{\"enabled\":true}}", ((JsonObject)result.RequestPayload).ToJsonString());
    }

    [Fact]
    public async Task ItShouldSetHttpRequestMessageOptionsAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        List<RestApiOperationPayloadProperty> payloadProperties =
        [
            new("name", "string", true, []),
            new("attributes", "object", false,
            [
                new("enabled", "boolean", false, []),
            ])
        ];

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload
        );

        var arguments = new KernelArguments
        {
            { "name", "fake-name-value" },
            { "enabled", true }
        };

        var options = new RestApiOperationRunOptions()
        {
            Kernel = new(),
            KernelFunction = KernelFunctionFactory.CreateFromMethod(() => false),
            KernelArguments = arguments,
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, enableDynamicPayload: true);

        // Act
        var result = await sut.RunAsync(operation, arguments, options);

        // Assert
        var requestMessage = this._httpMessageHandlerStub.RequestMessage;
        Assert.NotNull(requestMessage);
        Assert.True(requestMessage.Options.TryGetValue(OpenApiKernelFunctionContext.KernelFunctionContextKey, out var kernelFunctionContext));
        Assert.NotNull(kernelFunctionContext);
        Assert.Equal(options.Kernel, kernelFunctionContext.Kernel);
        Assert.Equal(options.KernelFunction, kernelFunctionContext.Function);
        Assert.Equal(options.KernelArguments, kernelFunctionContext.Arguments);
    }

    [Fact]
    public async Task ItShouldIncludeRequestDataWhenOperationCanceledExceptionIsThrownAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ExceptionToThrow = new OperationCanceledException();

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            [],
            payload: null
        );

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { value = "fake-value" }) },
            { "content-type", "application/json" }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act & Assert
        var canceledException = await Assert.ThrowsAsync<OperationCanceledException>(() => sut.RunAsync(operation, arguments));
        Assert.Equal("The operation was canceled.", canceledException.Message);
        Assert.Equal("POST", canceledException.Data["http.request.method"]);
        Assert.Equal("https://fake-random-test-host/fake-path", canceledException.Data["url.full"]);
        Assert.Equal("{\"value\":\"fake-value\"}", canceledException.Data["http.request.body"]);
    }

    [Fact]
    public async Task ItShouldUseCustomHttpResponseContentReaderAsync()
    {
        // Arrange
        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            [],
            payload: null
        );

        var expectedCancellationToken = new CancellationToken();

        async Task<object?> ReadHttpResponseContentAsync(HttpResponseContentReaderContext context, CancellationToken cancellationToken)
        {
            Assert.Equal(expectedCancellationToken, cancellationToken);

            return await context.Response.Content.ReadAsStreamAsync(cancellationToken);
        }

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, httpResponseContentReader: ReadHttpResponseContentAsync);

        // Act
        var response = await sut.RunAsync(operation, [], cancellationToken: expectedCancellationToken);

        // Assert
        Assert.IsAssignableFrom<Stream>(response.Content);
    }

    [Fact]
    public async Task ItShouldUseDefaultHttpResponseContentReaderIfCustomDoesNotReturnAnyContentAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            [],
            payload: null
        );

        var readerHasBeenCalled = false;

        Task<object?> ReadHttpResponseContentAsync(HttpResponseContentReaderContext context, CancellationToken cancellationToken)
        {
            readerHasBeenCalled = true;
            return Task.FromResult<object?>(null); // Return null to indicate that no content is returned
        }

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, httpResponseContentReader: ReadHttpResponseContentAsync);

        // Act
        var response = await sut.RunAsync(operation, []);

        // Assert
        Assert.True(readerHasBeenCalled);
        Assert.Equal("fake-content", response.Content);
    }

    [Fact]
    public async Task ItShouldDisposeContentStreamAndHttpResponseContentMessageAsync()
    {
        // Arrange
        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            [],
            payload: null
        );

        HttpResponseMessage? responseMessage = null;
        Stream? contentStream = null;

        async Task<object?> ReadHttpResponseContentAsync(HttpResponseContentReaderContext context, CancellationToken cancellationToken)
        {
            responseMessage = context.Response;
            contentStream = await context.Response.Content.ReadAsStreamAsync(cancellationToken);
            return contentStream;
        }

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, httpResponseContentReader: ReadHttpResponseContentAsync);

        // Act
        var response = await sut.RunAsync(operation, []);

        // Assert
        var stream = Assert.IsAssignableFrom<Stream>(response.Content);
        Assert.True(stream.CanRead);
        Assert.True(stream.CanSeek);

        stream.Dispose();

        // Check that the content stream and the response message are disposed
        Assert.Throws<ObjectDisposedException>(() => responseMessage!.Version = Version.Parse("1.1.1"));
        Assert.False(contentStream!.CanRead);
        Assert.False(contentStream!.CanSeek);
    }

    public class SchemaTestData : IEnumerable<object[]>
    {
        public IEnumerator<object[]> GetEnumerator()
        {
            yield return new object[] {
                    "default",
                    new (string, RestApiOperationExpectedResponse)[] {
                        ("400", new RestApiOperationExpectedResponse("fake-content", "fake-content-type", KernelJsonSchema.Parse(ResourceResponseProvider.LoadFromResource("FakeResponseSchema.json")))),
                        ("default", new RestApiOperationExpectedResponse("Default response content", "application/json", KernelJsonSchema.Parse(ResourceResponseProvider.LoadFromResource("DefaultResponseSchema.json")))),
                    },
            };
            yield return new object[] {
                    "200",
                    new (string, RestApiOperationExpectedResponse)[] {
                        ("200", new RestApiOperationExpectedResponse("fake-content", "fake-content-type", KernelJsonSchema.Parse(ResourceResponseProvider.LoadFromResource("FakeResponseSchema.json")))),
                        ("default", new RestApiOperationExpectedResponse("Default response content", "application/json", KernelJsonSchema.Parse(ResourceResponseProvider.LoadFromResource("DefaultResponseSchema.json")))),
                    },
            };
            yield return new object[] {
                    "2XX",
                    new (string, RestApiOperationExpectedResponse)[] {
                        ("2XX", new RestApiOperationExpectedResponse("fake-content", "fake-content-type", KernelJsonSchema.Parse(ResourceResponseProvider.LoadFromResource("FakeResponseSchema.json")))),
                        ("default", new RestApiOperationExpectedResponse("Default response content", "application/json", KernelJsonSchema.Parse(ResourceResponseProvider.LoadFromResource("DefaultResponseSchema.json")))),
                    },
            };
            yield return new object[] {
                    "2XX",
                    new (string, RestApiOperationExpectedResponse)[] {
                        ("2XX", new RestApiOperationExpectedResponse("fake-content", "fake-content-type", KernelJsonSchema.Parse(ResourceResponseProvider.LoadFromResource("FakeResponseSchema.json")))),
                        ("default", new RestApiOperationExpectedResponse("Default response content", "application/json", KernelJsonSchema.Parse(ResourceResponseProvider.LoadFromResource("DefaultResponseSchema.json")))),
                    },
            };
            yield return new object[] {
                    "200",
                    new (string, RestApiOperationExpectedResponse)[] {
                        ("default", new RestApiOperationExpectedResponse("Default response content", "application/json", KernelJsonSchema.Parse(ResourceResponseProvider.LoadFromResource("DefaultResponseSchema.json")))),
                        ("2XX", new RestApiOperationExpectedResponse("fake-content", "fake-content-type", KernelJsonSchema.Parse(ResourceResponseProvider.LoadFromResource("2XXFakeResponseSchema.json")))),
                        ("200", new RestApiOperationExpectedResponse("fake-content", "fake-content-type", KernelJsonSchema.Parse(ResourceResponseProvider.LoadFromResource("200FakeResponseSchema.json")))),
                    },
            };
        }

        IEnumerator IEnumerable.GetEnumerator() => this.GetEnumerator();
    }

    [Theory]
    [ClassData(typeof(SchemaTestData))]
    public async Task ItShouldReturnExpectedSchemaAsync(string expectedStatusCode, params (string, RestApiOperationExpectedResponse)[] responses)
    {
        var operation = new RestApiOperation(
            "fake-id",
            new RestApiOperationServer("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            [],
            null,
            responses.ToDictionary(item => item.Item1, item => item.Item2)
        );

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, []);

        Assert.NotNull(result);
        var expected = responses.First(r => r.Item1 == expectedStatusCode).Item2.Schema;
        Assert.Equal(JsonSerializer.Serialize(expected), JsonSerializer.Serialize(result.ExpectedSchema));
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
        public HttpRequestHeaders? RequestHeaders => this.RequestMessage?.Headers;

        public HttpContentHeaders? ContentHeaders => this.RequestMessage?.Content?.Headers;

        public byte[]? RequestContent { get; private set; }

        public Uri? RequestUri => this.RequestMessage?.RequestUri;

        public HttpMethod? Method => this.RequestMessage?.Method;

        public HttpRequestMessage? RequestMessage { get; private set; }

        public HttpResponseMessage ResponseToReturn { get; set; }

        public Exception? ExceptionToThrow { get; set; }

        public HttpMessageHandlerStub()
        {
            this.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent("{}", Encoding.UTF8, MediaTypeNames.Application.Json)
            };
        }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            if (this.ExceptionToThrow is not null)
            {
                throw this.ExceptionToThrow;
            }

            this.RequestMessage = request;
            this.RequestContent = request.Content is null ? null : await request.Content.ReadAsByteArrayAsync(cancellationToken);

            return await Task.FromResult(this.ResponseToReturn);
        }
    }
}
