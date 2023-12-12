// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
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

        Assert.Equal("fake-content", result.Content);

        Assert.Equal("application/json; charset=utf-8", result.ContentType);

        this._authenticationHandlerMock.Verify(x => x(It.IsAny<HttpRequestMessage>(), It.IsAny<CancellationToken>()), Times.Once);
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

        Assert.Equal(HttpMethod.Post, this._httpMessageHandlerStub.Method);

        Assert.NotNull(this._httpMessageHandlerStub.ContentHeaders);
        Assert.Contains(this._httpMessageHandlerStub.ContentHeaders, h => h.Key == "Content-Type" && h.Value.Contains("text/plain; charset=utf-8"));

        var messageContent = this._httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.True(messageContent.Length != 0);

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
            new(name: "X-H1", type: "string", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "X-H2", type: "array", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple)
        };

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            parameters
        );

        var arguments = new KernelArguments
        {
            ["X-H1"] = "fake-header-value",
            ["X-H2"] = "[1,2,3]"
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, userAgent: "fake-agent");

        // Act
        await sut.RunAsync(operation, arguments);

        // Assert - 3 headers: 2 from the test and the User-Agent added internally
        Assert.NotNull(this._httpMessageHandlerStub.RequestHeaders);
        Assert.Equal(3, this._httpMessageHandlerStub.RequestHeaders.Count());

        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "User-Agent" && h.Value.Contains("fake-agent"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-H1" && h.Value.Contains("fake-header-value"));
        Assert.Contains(this._httpMessageHandlerStub.RequestHeaders, h => h.Key == "X-H2" && h.Value.Contains("1,2,3"));
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
            new Uri("https://fake-random-test-host"),
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
            payload
        );

        var arguments = new KernelArguments();
        arguments.Add("name", "fake-name-value");
        arguments.Add("enabled", "true");

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, enableDynamicPayload: true);

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
            payload
        );

        var arguments = new KernelArguments();
        arguments.Add("name", "fake-string-value");
        arguments.Add("enabled", "true");
        arguments.Add("cardinality", "8");
        arguments.Add("coefficient", "0.8");
        arguments.Add("count", "1");
        arguments.Add("params", "[1,2,3]");

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object, enableDynamicPayload: true);

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
            payload
        );

        var arguments = new KernelArguments();
        arguments.Add("upn", "fake-sender-upn");
        arguments.Add("receiver.upn", "fake-receiver-upn");
        arguments.Add("receiver.alternative.upn", "fake-receiver-alternative-upn");
        arguments.Add("cc.upn", "fake-cc-upn");

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
            payload: null
        );

        var arguments = new KernelArguments();

        var sut = new RestApiOperationRunner(
            this._httpClient,
            this._authenticationHandlerMock.Object,
            enableDynamicPayload: true);

        // Act
        var exception = await Assert.ThrowsAsync<KernelException>(async () => await sut.RunAsync(operation, arguments));

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
            payload: null
        );

        var arguments = new KernelArguments();

        var sut = new RestApiOperationRunner(
            this._httpClient,
            this._authenticationHandlerMock.Object,
            enableDynamicPayload: false);

        // Act
        var exception = await Assert.ThrowsAsync<KernelException>(async () => await sut.RunAsync(operation, arguments));

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
        Assert.True(messageContent.Length != 0);

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
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
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
        Assert.True(messageContent.Length != 0);

        var payloadText = Encoding.UTF8.GetString(messageContent, 0, messageContent.Length);
        Assert.Equal("fake-input-value", payloadText);
    }

    [Fact]
    public async Task ItShouldBuildJsonPayloadDynamicallyExcludingOptionalParametersIfTheirArgumentsNotProvidedAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        List<RestApiOperationPayloadProperty> payloadProperties = new()
        {
            new("upn", "string", false, new List<RestApiOperationPayloadProperty>()),
        };

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
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
        Assert.True(messageContent.Length != 0);

        var deserializedPayload = JsonNode.Parse(new MemoryStream(messageContent));
        Assert.NotNull(deserializedPayload);

        var senderUpn = deserializedPayload["upn"]?.ToString();
        Assert.Null(senderUpn);
    }

    [Fact]
    public async Task ItShouldBuildJsonPayloadDynamicallyIncludingOptionalParametersIfTheirArgumentsProvidedAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        List<RestApiOperationPayloadProperty> payloadProperties = new()
        {
            new("upn", "string", false, new List<RestApiOperationPayloadProperty>()),
        };

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            payload
        );

        var arguments = new KernelArguments();
        arguments.Add("upn", "fake-sender-upn");

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
        Assert.True(messageContent.Length != 0);

        var deserializedPayload = JsonNode.Parse(new MemoryStream(messageContent));
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
            "string",
            isRequired: true, //Marking the parameter as required
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            new List<RestApiOperationParameter>() { firstParameter, secondParameter },
            payload: null
        );

        var arguments = new KernelArguments
        {
            { "p1", "v1" },
            { "p2", "v2" },
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host/fake-path?p1=v1&p2=v2", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);
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
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            new List<RestApiOperationParameter>() { firstParameter, secondParameter },
            payload: null
        );

        var arguments = new KernelArguments
        {
            { "p1", "v1" },
            { "p2", "v2" },
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host/fake-path?p1=v1&p2=v2", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);
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
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            new List<RestApiOperationParameter>() { firstParameter, secondParameter },
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
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            new List<RestApiOperationParameter>() { parameter },
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
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
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
        this._httpMessageHandlerStub.ResponseToReturn.Content = new ByteArrayContent(new byte[] { 00, 01, 02 });
        this._httpMessageHandlerStub.ResponseToReturn.Content.Headers.ContentType = new MediaTypeHeaderValue(contentType);

        var operation = new RestApiOperation(
            "fake-id",
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
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
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            payload: null
        );

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { value = "fake-value" }) },
            { "content-type", "application/json" }
        };

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act & Assert
        await Assert.ThrowsAsync<KernelException>(() => sut.RunAsync(operation, arguments));
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
            new Uri("https://fake-random-test-host"),
            "fake-path",
            HttpMethod.Get,
            "fake-description",
            new List<RestApiOperationParameter>(),
            null,
            responses.ToDictionary(item => item.Item1, item => item.Item2)
        );

        var sut = new RestApiOperationRunner(this._httpClient, this._authenticationHandlerMock.Object);

        // Act
        var result = await sut.RunAsync(operation, new KernelArguments());

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
