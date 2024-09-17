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
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Functions.OpenAPI.OpenApi;
using Microsoft.SemanticKernel.Orchestration;
using Moq;
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
    public async Task ItUsesAuthFromOpenAiPluginManifestWhenFetchingOpenApiSpecAsync()
    {
        //Arrange
        using var messageHandlerStub = new HttpMessageHandlerStub((HttpRequestMessage message) =>
        {
            if (message!.RequestUri!.AbsoluteUri == "https://fake-random-test-host/openai_manifest.json")
            {
                var response = new HttpResponseMessage();
                response.Content = new StreamContent(ResourcePluginsProvider.LoadFromResource("ai-plugin.json"));
                return response;
            }

            if (message!.RequestUri!.AbsoluteUri == "https://fake-random-test-host/openapi.json")
            {
                var response = new HttpResponseMessage();
                response.Content = new StreamContent(this._openApiDocument);
                return response;
            }

            throw new SKException($"Unexpected url - {message!.RequestUri!.AbsoluteUri}");
        });

        using var httpClient = new HttpClient(messageHandlerStub, false);

        var providerActualArguments = new List<OpenAIAuthenticationManifest?>();

        var authCallbackMock = new Mock<AuthenticateRequestAsyncCallback>();

        var authCallbackProviderMock = new Mock<AuthenticateCallbackProvider>();
        authCallbackProviderMock
            .Setup(p => p.Invoke(It.IsAny<OpenAIAuthenticationManifest>()))
            .Callback<OpenAIAuthenticationManifest>(c => providerActualArguments.Add(c))
            .Returns(authCallbackMock.Object);

        //Act
        var plugin = await this._kernel.ImportPluginFunctionsAsync(
            "fakePlugin",
            new Uri("https://fake-random-test-host/openai_manifest.json"),
            new OpenApiFunctionExecutionParameters { HttpClient = httpClient, AuthenticateCallbackProvider = authCallbackProviderMock.Object });

        //Assert
        var setSecretFunction = plugin["SetSecret"];
        Assert.NotNull(setSecretFunction);

        //Check provider is called two times: first time with null when loading the OpenAI manifest document and the second time with auth config when loading the OpenAPI document.
        authCallbackProviderMock.Verify(target => target.Invoke(It.IsAny<OpenAIAuthenticationManifest>()), Times.Exactly(2));
        Assert.Equal(2, providerActualArguments.Count);
        Assert.Null(providerActualArguments[0]);
        Assert.Equal("https://vault.azure.net/.default", providerActualArguments[1]?.Scope);

        authCallbackMock.Verify(target => target.Invoke(It.IsAny<HttpRequestMessage>()), Times.Exactly(2));
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

    [Fact]
    public async Task ItShouldConvertPluginComplexResponseToStringToSaveItInContextAsync()
    {
        //Arrange
        using var content = new StringContent("fake-content", Encoding.UTF8, MediaTypeNames.Application.Json);
        using var messageHandlerStub = new HttpMessageHandlerStub(content);

        using var httpClient = new HttpClient(messageHandlerStub, false);

        var executionParameters = new OpenApiFunctionExecutionParameters();
        executionParameters.HttpClient = httpClient;

        var fakePlugin = new FakePlugin();

        var openApiPlugins = await this._kernel.ImportPluginFunctionsAsync("fakePlugin", this._openApiDocument, executionParameters);
        var fakePlugins = this._kernel.ImportFunctions(fakePlugin);

        var kernel = KernelBuilder.Create();

        var arguments = new ContextVariables();
        arguments.Add("secret-name", "fake-secret-name");
        arguments.Add("api-version", "fake-api-version");

        //Act
        var res = await kernel.RunAsync(arguments, openApiPlugins["GetSecret"], fakePlugins["DoFakeAction"]);

        //Assert
        Assert.NotNull(res);

        var openApiPluginResult = res.FunctionResults.FirstOrDefault();
        Assert.NotNull(openApiPluginResult);

        var result = openApiPluginResult.GetValue<RestApiOperationResponse>();

        //Check original response
        Assert.NotNull(result);
        Assert.Equal("fake-content", result.Content);

        //Check the response, converted to a string indirectly through an argument passed to a fake plugin that follows the OpenApi plugin in the pipeline since there's no direct access to the context.
        Assert.Equal("fake-content", fakePlugin.ParameterValueFakeMethodCalledWith);
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

    private sealed class FakePlugin
    {
        public string? ParameterValueFakeMethodCalledWith { get; private set; }

        [SKFunction]
        public void DoFakeAction(string parameter)
        {
            this.ParameterValueFakeMethodCalledWith = parameter;
        }
    }

    #endregion
}
