// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
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
}
