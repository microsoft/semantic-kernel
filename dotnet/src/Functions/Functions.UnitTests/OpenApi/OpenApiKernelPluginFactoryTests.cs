// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Mime;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using SemanticKernel.Functions.UnitTests.OpenApi.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;
public sealed class OpenApiKernelPluginFactoryTests
{
    /// <summary>
    /// System under test - an instance of OpenApiDocumentParser class.
    /// </summary>
    private readonly OpenApiDocumentParser _sut;

    /// <summary>
    /// OpenAPI function execution parameters.
    /// </summary>
    private readonly OpenApiFunctionExecutionParameters _executionParameters;

    /// <summary>
    /// OpenAPI document stream.
    /// </summary>
    private readonly Stream _openApiDocument;

    /// <summary>
    /// Creates an instance of a <see cref="OpenApiKernelExtensionsTests"/> class.
    /// </summary>
    public OpenApiKernelPluginFactoryTests()
    {
        this._executionParameters = new OpenApiFunctionExecutionParameters() { EnableDynamicPayload = false };

        this._openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV2_0.json");

        this._sut = new OpenApiDocumentParser();
    }

    [Fact]
    public async Task ItCanIncludeOpenApiOperationParameterTypesIntoFunctionParametersViewAsync()
    {
        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", this._openApiDocument, this._executionParameters);

        // Assert
        var setSecretFunction = plugin["SetSecret"];
        Assert.NotNull(setSecretFunction);

        var functionView = setSecretFunction.Metadata;
        Assert.NotNull(functionView);

        var secretNameParameter = functionView.Parameters.First(p => p.Name == "secret_name");
        Assert.NotNull(secretNameParameter.Schema);
        Assert.Equal("string", secretNameParameter.Schema!.RootElement.GetProperty("type").GetString());

        var apiVersionParameter = functionView.Parameters.First(p => p.Name == "api_version");
        Assert.Equal("string", apiVersionParameter.Schema!.RootElement.GetProperty("type").GetString());

        var payloadParameter = functionView.Parameters.First(p => p.Name == "payload");
        Assert.NotNull(payloadParameter.Schema);
        Assert.Equal("object", payloadParameter.Schema!.RootElement.GetProperty("type").GetString());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItUsesServerUrlOverrideIfProvidedAsync(bool removeServersProperty)
    {
        // Arrange
        const string DocumentUri = "http://localhost:3001/openapi.json";
        const string ServerUrlOverride = "https://server-override.com/";

        var openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV3_0.json");

        if (removeServersProperty)
        {
            openApiDocument = OpenApiTestHelper.ModifyOpenApiDocument(openApiDocument, (doc) =>
            {
                doc.Remove("servers");
            });
        }

        using var messageHandlerStub = new HttpMessageHandlerStub(openApiDocument);
        using var httpClient = new HttpClient(messageHandlerStub, false);

        this._executionParameters.HttpClient = httpClient;
        this._executionParameters.ServerUrlOverride = new Uri(ServerUrlOverride);

        var arguments = this.GetFakeFunctionArguments();

        var kernel = new Kernel();

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", new Uri(DocumentUri), this._executionParameters);
        var setSecretFunction = plugin["SetSecret"];

        messageHandlerStub.ResetResponse();

        var result = await kernel.InvokeAsync(setSecretFunction, arguments);

        // Assert
        Assert.NotNull(messageHandlerStub.RequestUri);
        Assert.StartsWith(ServerUrlOverride, messageHandlerStub.RequestUri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData("documentV2_0.json")]
    [InlineData("documentV3_0.json")]
    public async Task ItUsesServerUrlFromOpenApiDocumentAsync(string documentFileName)
    {
        // Arrange
        const string DocumentUri = "http://localhost:3001/openapi.json";
        const string ServerUrlFromDocument = "https://my-key-vault.vault.azure.net/";

        var openApiDocument = ResourcePluginsProvider.LoadFromResource(documentFileName);

        using var messageHandlerStub = new HttpMessageHandlerStub(openApiDocument);
        using var httpClient = new HttpClient(messageHandlerStub, false);

        this._executionParameters.HttpClient = httpClient;

        var arguments = this.GetFakeFunctionArguments();

        var kernel = new Kernel();

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", new Uri(DocumentUri), this._executionParameters);
        var setSecretFunction = plugin["SetSecret"];

        messageHandlerStub.ResetResponse();

        var result = await kernel.InvokeAsync(setSecretFunction, arguments);

        // Assert
        Assert.NotNull(messageHandlerStub.RequestUri);
        Assert.StartsWith(ServerUrlFromDocument, messageHandlerStub.RequestUri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData("http://localhost:3001/openapi.json", "http://localhost:3001/", "documentV2_0.json")]
    [InlineData("http://localhost:3001/openapi.json", "http://localhost:3001/", "documentV3_0.json")]
    [InlineData("https://api.example.com/openapi.json", "https://api.example.com/", "documentV2_0.json")]
    [InlineData("https://api.example.com/openapi.json", "https://api.example.com/", "documentV3_0.json")]
    [SuppressMessage("Design", "CA1054:URI-like parameters should not be strings", Justification = "Required for test data.")]
    public async Task ItUsesOpenApiDocumentHostUrlWhenServerUrlIsNotProvidedAsync(string documentUri, string expectedServerUrl, string documentFileName)
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource(documentFileName);

        using var content = OpenApiTestHelper.ModifyOpenApiDocument(openApiDocument, (doc) =>
        {
            doc.Remove("servers");
            doc.Remove("host");
            doc.Remove("schemes");
        });

        using var messageHandlerStub = new HttpMessageHandlerStub(content);
        using var httpClient = new HttpClient(messageHandlerStub, false);

        this._executionParameters.HttpClient = httpClient;

        var arguments = this.GetFakeFunctionArguments();

        var kernel = new Kernel();

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", new Uri(documentUri), this._executionParameters);
        var setSecretFunction = plugin["SetSecret"];

        messageHandlerStub.ResetResponse();

        var result = await kernel.InvokeAsync(setSecretFunction, arguments);

        // Assert
        Assert.NotNull(messageHandlerStub.RequestUri);
        Assert.StartsWith(expectedServerUrl, messageHandlerStub.RequestUri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ItShouldRespectRunAsyncCancellationTokenOnExecutionAsync()
    {
        // Arrange
        using var messageHandlerStub = new HttpMessageHandlerStub();
        messageHandlerStub.ResponseToReturn.Content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);

        using var httpClient = new HttpClient(messageHandlerStub, false);

        this._executionParameters.HttpClient = httpClient;

        var fakePlugin = new FakePlugin();

        using var registerCancellationToken = new System.Threading.CancellationTokenSource();
        using var executeCancellationToken = new System.Threading.CancellationTokenSource();

        var openApiPlugins = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", this._openApiDocument, this._executionParameters, registerCancellationToken.Token);

        var kernel = new Kernel();

        var arguments = new KernelArguments
        {
            { "secret-name", "fake-secret-name" },
            { "api-version", "fake-api-version" }
        };

        // Act
        registerCancellationToken.Cancel();
        var result = await kernel.InvokeAsync(openApiPlugins["GetSecret"], arguments, executeCancellationToken.Token);

        // Assert
        Assert.NotNull(result);

        var response = result.GetValue<RestApiOperationResponse>();

        //Check original response
        Assert.NotNull(response);
        Assert.Equal("fake-content", response.Content);
    }

    [Fact]
    public async Task ItShouldSanitizeOperationNameAsync()
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV3_0.json");

        using var content = OpenApiTestHelper.ModifyOpenApiDocument(openApiDocument, (doc) =>
        {
            doc["paths"]!["/secrets/{secret-name}"]!["get"]!["operationId"] = "issues/create-mile.stone";
        });

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", content, this._executionParameters);

        // Assert
        Assert.True(plugin.TryGetFunction("IssuesCreatemilestone", out var _));
    }

    [Fact]
    public async Task ItCanIncludeOpenApiDeleteAndPatchOperationsAsync()
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource("repair-service.json");

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("repairServicePlugin", openApiDocument, this._executionParameters);

        // Assert
        Assert.NotNull(plugin);
        var functionsMetadata = plugin.GetFunctionsMetadata();
        Assert.Equal(4, functionsMetadata.Count);
        AssertPayloadParameters(plugin, "updateRepair");
        AssertPayloadParameters(plugin, "deleteRepair");
    }

    [Theory]
    [InlineData("documentV2_0.json")]
    [InlineData("documentV3_0.json")]
    [InlineData("documentV3_1.yaml")]
    public async Task ItShouldReplicateMetadataToOperationAsync(string documentFileName)
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource(documentFileName);

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", openApiDocument, this._executionParameters);

        // Assert Metadata Keys and Values
        Assert.True(plugin.TryGetFunction("OpenApiExtensions", out var function));
        var additionalProperties = function.Metadata.AdditionalProperties;
        Assert.Equal(2, additionalProperties.Count);

        Assert.Contains("method", additionalProperties.Keys);
        Assert.Contains("operation-extensions", additionalProperties.Keys);

        Assert.Equal("GET", additionalProperties["method"]);

        // Assert Operation Extension keys
        var operationExtensions = additionalProperties["operation-extensions"] as Dictionary<string, object?>;
        Assert.NotNull(operationExtensions);
        Dictionary<string, object?> nonNullOperationExtensions = operationExtensions;

        Assert.Equal(8, nonNullOperationExtensions.Count);
        Assert.Contains("x-boolean-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-double-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-integer-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-string-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-date-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-datetime-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-array-extension", nonNullOperationExtensions.Keys);
        Assert.Contains("x-object-extension", nonNullOperationExtensions.Keys);
    }

    [Fact]
    public async Task ItShouldHandleEmptyOperationNameAsync()
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV3_0.json");

        using var content = OpenApiTestHelper.ModifyOpenApiDocument(openApiDocument, (doc) =>
        {
            doc["paths"]!["/secrets/{secret-name}"]!["get"]!["operationId"] = "";
        });

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", content, this._executionParameters);

        // Assert
        Assert.Equal(5, plugin.Count());
        Assert.True(plugin.TryGetFunction("GetSecretsSecretname", out var _));
    }

    [Fact]
    public async Task ItShouldHandleNullOperationNameAsync()
    {
        // Arrange
        var openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV3_0.json");

        using var content = OpenApiTestHelper.ModifyOpenApiDocument(openApiDocument, (doc) =>
        {
            doc["paths"]!["/secrets/{secret-name}"]!["get"]!.AsObject().Remove("operationId");
        });

        // Act
        var plugin = await OpenApiKernelPluginFactory.CreateFromOpenApiAsync("fakePlugin", content, this._executionParameters);

        // Assert
        Assert.Equal(5, plugin.Count());
        Assert.True(plugin.TryGetFunction("GetSecretsSecretname", out var _));
    }

    [Fact]
    public void Dispose()
    {
        this._openApiDocument.Dispose();
    }

    #region private ================================================================================

    private static void AssertPayloadParameters(KernelPlugin plugin, string functionName)
    {
        Assert.True(plugin.TryGetFunction(functionName, out var function));
        Assert.NotNull(function.Metadata.Parameters);
        Assert.Equal(2, function.Metadata.Parameters.Count);
        Assert.Equal("payload", function.Metadata.Parameters[0].Name);
        Assert.Equal("content_type", function.Metadata.Parameters[1].Name);
    }

    private KernelArguments GetFakeFunctionArguments()
    {
        return new KernelArguments
        {
            ["secret-name"] = "fake-secret-name",
            ["api-version"] = "7.0",
            ["X-API-Version"] = 6,
            ["payload"] = "fake-payload"
        };
    }

    private sealed class FakePlugin
    {
        public string? ParameterValueFakeMethodCalledWith { get; private set; }

        [KernelFunction]
        public void DoFakeAction(string parameter)
        {
            this.ParameterValueFakeMethodCalledWith = parameter;
        }
    }

    #endregion

}
