// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.OpenAI;
using Moq;
using SemanticKernel.Functions.UnitTests.OpenAPI.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenAPI.OpenAI;

public sealed class KernelOpenAIPluginExtensionsTests : IDisposable
{
    /// <summary>
    /// OpenAPI document stream.
    /// </summary>
    private readonly Stream _openApiDocument;

    /// <summary>
    /// IKernel instance.
    /// </summary>
    private readonly IKernel _kernel;

    /// <summary>
    /// Creates an instance of a <see cref="KernelOpenAIPluginExtensionsTests"/> class.
    /// </summary>
    public KernelOpenAIPluginExtensionsTests()
    {
        this._kernel = KernelBuilder.Create();

        this._openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV2_0.json");
    }

    [Fact]
    public async Task ItUsesAuthFromOpenAiPluginManifestWhenFetchingOpenApiSpecAsync()
    {
        //Arrange
        using var reader = new StreamReader(ResourcePluginsProvider.LoadFromResource("ai-plugin.json"), Encoding.UTF8);
        JsonNode openAIDocumentContent = JsonNode.Parse(await reader.ReadToEndAsync())!;
        var actualOpenAIAuthConfig = openAIDocumentContent["auth"].Deserialize<OpenAIAuthenticationConfig>()!;

        using var openAiDocument = ResourcePluginsProvider.LoadFromResource("ai-plugin.json");
        using var messageHandlerStub = new HttpMessageHandlerStub(this._openApiDocument);

        using var httpClient = new HttpClient(messageHandlerStub, false);
        var authCallbackMock = new Mock<OpenAIAuthenticateRequestAsyncCallback>();
        var executionParameters = new OpenAIFunctionExecutionParameters { HttpClient = httpClient, AuthCallback = authCallbackMock.Object };

        var pluginName = "fakePlugin";

        //Act
        var plugin = await this._kernel.ImportOpenAIPluginFunctionsAsync(pluginName, openAiDocument, executionParameters);

        //Assert
        var setSecretFunction = plugin["SetSecret"];
        Assert.NotNull(setSecretFunction);

        authCallbackMock.Verify(target => target.Invoke(
            It.IsAny<HttpRequestMessage>(),
            It.Is<string>(expectedPluginName => expectedPluginName == pluginName),
            It.Is<OpenAIAuthenticationConfig>(expectedOpenAIAuthConfig => expectedOpenAIAuthConfig.Scope == actualOpenAIAuthConfig.Scope)),
        Times.Exactly(1));
    }

    public void Dispose()
    {
        this._openApiDocument.Dispose();
    }
}
