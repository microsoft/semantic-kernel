// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi.Extensions;
public sealed class ApiManifestKernelExtensionsTests
{
    [Fact]
    public async Task ItCanCreatePluginFromApiManifestAsync()
    {
        // Act
        var kernel = new Kernel();
        var testPluginsDir = Path.Combine(Directory.GetCurrentDirectory(), "OpenApi", "TestPlugins");
        var manifestFilePath = Path.Combine(testPluginsDir, "example-apimanifest.json");

        // Arrange
        var plugin = await kernel.CreatePluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(3, plugin.FunctionCount);
    }

    [Fact]
    public async Task ItCanCreatePluginFromApiManifestWithDescriptionParameterAsync()
    {
        // Act
        var kernel = new Kernel();
        var testPluginsDir = Path.Combine(Directory.GetCurrentDirectory(), "OpenApi", "TestPlugins");
        var manifestFilePath = Path.Combine(testPluginsDir, "example-apimanifest.json");
        var description = "My plugin description";

        // Arrange
        var plugin = await kernel.CreatePluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath, description);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(description, plugin.Description);
    }

    [Fact]
    public async Task ItCanCreatePluginFromApiManifestWithEmptyDescriptionParameterAsync()
    {
        // Act
        var kernel = new Kernel();
        var testPluginsDir = Path.Combine(Directory.GetCurrentDirectory(), "OpenApi", "TestPlugins");
        var manifestFilePath = Path.Combine(testPluginsDir, "example-apimanifest.json");

        // Arrange
        var plugin = await kernel.CreatePluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath, description: null);

        // Assert
        Assert.NotNull(plugin);
        Assert.Empty(plugin.Description);
    }

    [Fact]
    public async Task ItCanImportPluginFromApiManifestAsync()
    {
        // Act
        var kernel = new Kernel();
        var testPluginsDir = Path.Combine(Directory.GetCurrentDirectory(), "OpenApi", "TestPlugins");
        var manifestFilePath = Path.Combine(testPluginsDir, "example-apimanifest.json");

        // Arrange
        var plugin = await kernel.ImportPluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.Single(kernel.Plugins);
    }

    [Fact]
    public async Task ItCanImportPluginFromApiManifestWithDescriptionParameterAsync()
    {
        // Act
        var kernel = new Kernel();
        var testPluginsDir = Path.Combine(Directory.GetCurrentDirectory(), "OpenApi", "TestPlugins");
        var manifestFilePath = Path.Combine(testPluginsDir, "example-apimanifest.json");
        var description = "My plugin description";

        // Arrange
        var plugin = await kernel.ImportPluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath, description);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(description, plugin.Description);
    }
}
