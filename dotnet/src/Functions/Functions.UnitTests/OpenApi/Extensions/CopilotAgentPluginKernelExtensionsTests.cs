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

public sealed class CopilotAgentPluginKernelExtensionsTests
{
    [Fact]
    public async Task ItCanImportPluginFromCopilotAgentPluginAsync()
    {
        // Act
        var kernel = new Kernel();
        var testPluginsDir = Path.Combine(Directory.GetCurrentDirectory(), "OpenApi", "TestPlugins");
        var manifestFilePath = Path.Combine(testPluginsDir, "messages-apiplugin.json");

        // Arrange
        var plugin = await kernel.ImportPluginFromCopilotAgentPluginAsync("MessagesPlugin", manifestFilePath);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(2, plugin.FunctionCount);
        Assert.Equal(411, plugin["me_sendMail"].Description.Length);
        Assert.Equal(1000, plugin["me_ListMessages"].Description.Length);
    }

    [Fact]
    public async Task ItUsesServerUrlValidationOptionsFromFunctionExecutionParametersAsync()
    {
        // Arrange
        using var handler = new HttpMessageHandlerStub();
        using var httpClient = new HttpClient(handler);
        var kernel = new Kernel();
        var manifestFilePath = Path.Combine(Directory.GetCurrentDirectory(), "OpenApi", "TestPlugins", "messages-apiplugin.json");
        var serverUrl = new Uri("http://api.example.test/v1.0/");
        var parameters = new CopilotAgentPluginParameters
        {
            FunctionExecutionParameters = new()
            {
                ["https://graph.microsoft.com/v1.0"] = new OpenApiFunctionExecutionParameters
                {
                    HttpClient = httpClient,
                    ServerUrlOverride = serverUrl,
                    EnableDynamicPayload = false,
                    EnablePayloadNamespacing = true,
                    ServerUrlValidationOptions = new RestApiOperationServerUrlValidationOptions { AllowedBaseUrls = [serverUrl] }
                }
            }
        };
        var plugin = await kernel.CreatePluginFromCopilotAgentPluginAsync("MessagesPlugin", manifestFilePath, parameters);

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
        var testPluginsDir = Path.Combine(Directory.GetCurrentDirectory(), "OpenApi", "TestPlugins");
        using var document = File.OpenRead(Path.Combine(testPluginsDir, "messages-openapi.yml"));
        using var handler = new HttpMessageHandlerStub(document);
        using var httpClient = new HttpClient(handler);
        var manifest = (await File.ReadAllTextAsync(Path.Combine(testPluginsDir, "messages-apiplugin.json")))
            .Replace("\"messages-openapi.yml\"", "\"http://api.example.test/messages-openapi.yml\"", StringComparison.Ordinal);
        var manifestFilePath = Path.Combine(Path.GetTempPath(), $"{Guid.NewGuid():N}.json");
        await File.WriteAllTextAsync(manifestFilePath, manifest);

        try
        {
            // Act
            var exception = await Assert.ThrowsAsync<InvalidOperationException>(() =>
                new Kernel().CreatePluginFromCopilotAgentPluginAsync("MessagesPlugin", manifestFilePath, new CopilotAgentPluginParameters { HttpClient = httpClient }));

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
