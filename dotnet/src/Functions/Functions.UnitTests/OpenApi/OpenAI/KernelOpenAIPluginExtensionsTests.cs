// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Moq;
using SemanticKernel.Functions.UnitTests.OpenApi.TestPlugins;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi.OpenAI;

public sealed class KernelOpenAIPluginExtensionsTests : IDisposable
{
    /// <summary>
    /// OpenAPI document stream.
    /// </summary>
    private readonly Stream _openApiDocument;

    /// <summary>
    /// Kernel instance.
    /// </summary>
    private readonly Kernel _kernel;

    /// <summary>
    /// Creates an instance of a <see cref="KernelOpenAIPluginExtensionsTests"/> class.
    /// </summary>
    public KernelOpenAIPluginExtensionsTests()
    {
        this._kernel = new Kernel();

        this._openApiDocument = ResourcePluginsProvider.LoadFromResource("documentV2_0.json");
    }

    [Fact]
    public async Task ItUsesOauthFromOpenAiPluginManifestWhenFetchingOpenApiSpecAsync()
    {
        await this.ItRunsTestAsync("ai-plugin.json");
    }

    [Fact]
    public async Task ItUsesHttpAuthFromOpenAiPluginManifestWhenFetchingOpenApiSpecAsync()
    {
        await this.ItRunsTestAsync("ai-plugin2.json");
    }

    private async Task ItRunsTestAsync(string resourceName)
    {
        //Arrange
        using var reader = new StreamReader(ResourcePluginsProvider.LoadFromResource(resourceName), Encoding.UTF8);
        JsonNode openAIDocumentContent = JsonNode.Parse(await reader.ReadToEndAsync())!;
        var actualOpenAIAuthConfig =
            openAIDocumentContent["auth"].Deserialize<OpenAIAuthenticationConfig>(
                new JsonSerializerOptions
                {
                    Converters = { new JsonStringEnumConverter(JsonNamingPolicy.SnakeCaseLower) },
                })!;

        using var openAiDocument = ResourcePluginsProvider.LoadFromResource(resourceName);
        using var messageHandlerStub = new HttpMessageHandlerStub(this._openApiDocument);

        using var httpClient = new HttpClient(messageHandlerStub, false);
        var authCallbackMock = new Mock<OpenAIAuthenticateRequestAsyncCallback>();
        var executionParameters = new OpenAIFunctionExecutionParameters { HttpClient = httpClient, AuthCallback = authCallbackMock.Object };

        var pluginName = "fakePlugin";

        //Act
        var plugin = await this._kernel.ImportPluginFromOpenAIAsync(pluginName, openAiDocument, executionParameters);

        //Assert
        var setSecretFunction = plugin["SetSecret"];
        Assert.NotNull(setSecretFunction);

        authCallbackMock.Verify(target => target.Invoke(
            It.IsAny<HttpRequestMessage>(),
            It.Is<string>(expectedPluginName => expectedPluginName == pluginName),
            It.Is<OpenAIAuthenticationConfig>(expectedOpenAIAuthConfig => expectedOpenAIAuthConfig.Scope == actualOpenAIAuthConfig!.Scope),
            It.IsAny<CancellationToken>()),
        Times.Exactly(1));
    }

    public void Dispose()
    {
        this._openApiDocument.Dispose();
    }
}
