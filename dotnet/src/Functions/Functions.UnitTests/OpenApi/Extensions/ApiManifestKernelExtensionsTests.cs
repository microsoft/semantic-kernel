// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public sealed class ApiManifestKernelExtensionsTests
{
    private static readonly string s_testPluginsDir = Path.Combine(Directory.GetCurrentDirectory(), "OpenApi", "TestPlugins");

    [Fact]
    public async Task ItUsesServerUrlValidationOptionsFromFunctionExecutionParametersAsync()
    {
        // Arrange
        using var handler = new HttpMessageHandlerStub();
        using var httpClient = new HttpClient(handler);
        var kernel = new Kernel();
        var serverUrl = new Uri("http://api.example.test/v1.0/");
        var parameters = new ApiManifestPluginParameters(functionExecutionParameters: new()
        {
            ["messages"] = new OpenApiFunctionExecutionParameters
            {
                HttpClient = httpClient,
                ServerUrlOverride = serverUrl,
                EnableDynamicPayload = false,
                EnablePayloadNamespacing = true,
                ServerUrlValidationOptions = new RestApiOperationServerUrlValidationOptions { AllowedBaseUrls = [serverUrl] }
            }
        });
        var plugin = await kernel.CreatePluginFromApiManifestAsync("MessagesPlugin", Path.Combine(s_testPluginsDir, "messages-apimanifest.json"), parameters);

        // Act
        await kernel.InvokeAsync(plugin["me_ListMessages"]);

        // Assert
        Assert.NotNull(handler.RequestUri);
        Assert.StartsWith(serverUrl.AbsoluteUri, handler.RequestUri.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ItRejectsUnsupportedDocumentUrisAsync()
    {
        // Arrange
        using var document = File.OpenRead(Path.Combine(s_testPluginsDir, "messages-openapi.yml"));
        using var handler = new HttpMessageHandlerStub(document);
        using var httpClient = new HttpClient(handler);
        var manifest = (await File.ReadAllTextAsync(Path.Combine(s_testPluginsDir, "messages-apimanifest.json")))
            .Replace("\"messages-openapi.yml\"", "\"http://api.example.test/messages-openapi.yml\"", StringComparison.Ordinal);
        var manifestFilePath = Path.Combine(Path.GetTempPath(), $"{Guid.NewGuid():N}.json");
        await File.WriteAllTextAsync(manifestFilePath, manifest);

        try
        {
            // Act
            var exception = await Assert.ThrowsAsync<InvalidOperationException>(() =>
                new Kernel().CreatePluginFromApiManifestAsync("MessagesPlugin", manifestFilePath, new ApiManifestPluginParameters(httpClient)));

            // Assert
            Assert.Null(handler.RequestUri);
            Assert.Contains("scheme 'http' is not allowed", exception.Message, StringComparison.Ordinal);
        }
        finally
        {
            File.Delete(manifestFilePath);
        }
    }
}
