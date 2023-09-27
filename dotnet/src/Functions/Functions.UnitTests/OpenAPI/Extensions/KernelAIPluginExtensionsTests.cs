// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Functions.OpenAPI.OpenApi;
using Microsoft.SemanticKernel.Orchestration;
using SemanticKernel.Functions.UnitTests.OpenAPI.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenAPI.Extensions;

public sealed class KernelAIPluginExtensionsTests : IDisposable
{
    /// <summary>
    /// System under test - an instance of OpenApiDocumentParser class.
    /// </summary>
    private readonly OpenApiDocumentParser _sut;

    /// <summary>
    /// OpenAPI document stream.
    /// </summary>
    private readonly Stream _openApiDocument;

    /// <summary>
    /// IKernel instance.
    /// </summary>
    private readonly IKernel _kernel;

    /// <summary>
    /// Creates an instance of a <see cref="KernelAIPluginExtensionsTests"/> class.
    /// </summary>
    public KernelAIPluginExtensionsTests()
    {
        this._kernel = KernelBuilder.Create();

        this._openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV2_0.json");

        this._sut = new OpenApiDocumentParser();
    }

    [Fact]
    public async Task ItCanIncludeOpenApiOperationParameterTypesIntoFunctionParametersViewAsync()
    {
        //Act
        var plugin = await this._kernel.ImportPluginFunctionsAsync("fakePlugin", this._openApiDocument);

        //Assert
        var setSecretFunction = plugin["SetSecret"];
        Assert.NotNull(setSecretFunction);

        var functionView = setSecretFunction.Describe();
        Assert.NotNull(functionView);

        var secretNameParameter = functionView.Parameters.First(p => p.Name == "secret_name");
        Assert.Equal(ParameterViewType.String, secretNameParameter.Type);

        var apiVersionParameter = functionView.Parameters.First(p => p.Name == "api_version");
        Assert.Equal("string", apiVersionParameter?.Type?.ToString());

        var payloadParameter = functionView.Parameters.First(p => p.Name == "payload");
        Assert.Equal(ParameterViewType.Object, payloadParameter.Type);
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

        var executionParameters = new OpenApiFunctionExecutionParameters { HttpClient = httpClient, ServerUrlOverride = new Uri(ServerUrlOverride) };
        var variables = this.GetFakeContextVariables();

        // Act
        var plugin = await this._kernel.ImportPluginFunctionsAsync("fakePlugin", new Uri(DocumentUri), executionParameters);
        var setSecretFunction = plugin["SetSecret"];

        messageHandlerStub.ResetResponse();

        var result = await this._kernel.RunAsync(setSecretFunction, variables);

        // Assert
        Assert.NotNull(setSecretFunction);

        var functionView = setSecretFunction.Describe();
        Assert.NotNull(functionView);

        var serverUrlParameter = functionView.Parameters.First(p => p.Name == "server_url");
        Assert.Equal(ServerUrlOverride, serverUrlParameter.DefaultValue);

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

        var executionParameters = new OpenApiFunctionExecutionParameters { HttpClient = httpClient };
        var variables = this.GetFakeContextVariables();

        // Act
        var plugin = await this._kernel.ImportPluginFunctionsAsync("fakePlugin", new Uri(DocumentUri), executionParameters);
        var setSecretFunction = plugin["SetSecret"];

        messageHandlerStub.ResetResponse();

        var result = await this._kernel.RunAsync(setSecretFunction, variables);

        // Assert
        Assert.NotNull(setSecretFunction);

        var functionView = setSecretFunction.Describe();
        Assert.NotNull(functionView);

        var serverUrlParameter = functionView.Parameters.First(p => p.Name == "server_url");
        Assert.Equal(ServerUrlFromDocument, serverUrlParameter.DefaultValue);

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

        var executionParameters = new OpenApiFunctionExecutionParameters { HttpClient = httpClient };
        var variables = this.GetFakeContextVariables();

        // Act
        var plugin = await this._kernel.ImportPluginFunctionsAsync("fakePlugin", new Uri(documentUri), executionParameters);
        var setSecretFunction = plugin["SetSecret"];

        messageHandlerStub.ResetResponse();

        var result = await this._kernel.RunAsync(setSecretFunction, variables);

        // Assert
        Assert.NotNull(setSecretFunction);

        var functionView = setSecretFunction.Describe();
        Assert.NotNull(functionView);

        var serverUrlParameter = functionView.Parameters.First(p => p.Name == "server_url");
        Assert.Equal(expectedServerUrl, serverUrlParameter.DefaultValue);

        Assert.NotNull(messageHandlerStub.RequestUri);
        Assert.StartsWith(expectedServerUrl, messageHandlerStub.RequestUri.AbsoluteUri, StringComparison.Ordinal);
    }

    public void Dispose()
    {
        this._openApiDocument.Dispose();
    }

    #region private ================================================================================

    private ContextVariables GetFakeContextVariables()
    {
        var variables = new ContextVariables();

        variables["secret-name"] = "fake-secret-name";
        variables["api-version"] = "fake-api-version";
        variables["X-API-Version"] = "fake-api-version";
        variables["payload"] = "fake-payload";

        return variables;
    }

    #endregion
}
