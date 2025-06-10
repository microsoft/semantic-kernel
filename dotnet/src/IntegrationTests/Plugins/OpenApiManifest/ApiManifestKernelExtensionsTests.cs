// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins.OpenApiManifest;

public sealed class ApiManifestKernelExtensionsTests
{
    private readonly string _testPluginsDir;
    private readonly Kernel _kernel;

    public ApiManifestKernelExtensionsTests()
    {
        this._testPluginsDir = Path.Combine(Directory.GetCurrentDirectory(), "Plugins", "OpenApiManifest");
        this._kernel = new Kernel();
    }

    [Fact]
    public async Task ItCanCreatePluginFromApiManifestAsync()
    {
        // Act
        var manifestFilePath = Path.Combine(this._testPluginsDir, "example-apimanifest.json");

        // Arrange
        var plugin = await this._kernel.CreatePluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(3, plugin.FunctionCount);
    }

    [Fact]
    public async Task ItCanCreatePluginFromApiManifestWithDescriptionParameterAsync()
    {
        // Act
        var manifestFilePath = Path.Combine(this._testPluginsDir, "example-apimanifest.json");
        var description = "My plugin description";

        // Arrange
        var plugin = await this._kernel.CreatePluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath, description);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(description, plugin.Description);
    }

    [Fact]
    public async Task ItCanCreatePluginFromApiManifestWithEmptyDescriptionParameterAsync()
    {
        // Act
        var manifestFilePath = Path.Combine(this._testPluginsDir, "example-apimanifest.json");

        // Arrange
        var plugin = await this._kernel.CreatePluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath, description: null);

        // Assert
        Assert.NotNull(plugin);
        Assert.Empty(plugin.Description);
    }

    [Fact]
    public async Task ItCanImportPluginFromApiManifestAsync()
    {
        // Act
        var manifestFilePath = Path.Combine(this._testPluginsDir, "example-apimanifest.json");

        // Arrange
        var plugin = await this._kernel.ImportPluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.Single(this._kernel.Plugins);
    }

    [Fact]
    public async Task ItCanImportPluginFromApiManifestWithDescriptionParameterAsync()
    {
        // Act
        var manifestFilePath = Path.Combine(this._testPluginsDir, "example-apimanifest.json");
        var description = "My plugin description";

        // Arrange
        var plugin = await this._kernel.ImportPluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath, description);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(description, plugin.Description);
    }

    [Fact]
    public async Task ItCanImportPluginFromApiManifestWithLocalAndRemoteApiDescriptionUrlAsync()
    {
        // Act
        var manifestFilePath = Path.Combine(this._testPluginsDir, "example-apimanifest-local.json");

        // Arrange
        var plugin = await this._kernel.ImportPluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(2, plugin.FunctionCount);
    }

    [Fact]
    // Verify that functions are correctly imported
    public async Task VerifyPluginFunctionsFromApiManifestAsync()
    {
        // Act
        var manifestFilePath = Path.Combine(this._testPluginsDir, "example-apimanifest-local.json");

        // Arrange
        var plugin = await this._kernel.ImportPluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(2, plugin.FunctionCount);

        // Assert functions imported from local openapi.json
        Assert.True(plugin.Contains("listRepairs"));
        Assert.Contains(plugin["listRepairs"].Metadata.AdditionalProperties, static p => p.Key == "method" && p.Value?.ToString() == "GET");

        // Assert functions imported from remote openapi.json
        Assert.True(plugin.Contains("directoryObject_GetDirectoryObject"));
        Assert.Contains(plugin["directoryObject_GetDirectoryObject"].Metadata.AdditionalProperties, static p => p.Key == "method" && p.Value?.ToString() == "GET");
    }
}
