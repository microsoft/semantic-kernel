﻿// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi.Extensions;
public sealed class ApiManifestKernelExtensionsTests
{
    private const string SkipReason = "Failing intermittently in the integration pipeline with a 429 HTTP status code. To be migrated to the integration tests project.";

    [Fact(Skip = SkipReason)]
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

    [Fact(Skip = SkipReason)]
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

    [Fact(Skip = SkipReason)]
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

    [Fact(Skip = SkipReason)]
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

    [Fact(Skip = SkipReason)]
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

    [Fact(Skip = SkipReason)]
    public async Task ItCanImportPluginFromApiManifestWithLocalAndRemoteApiDescriptionUrlAsync()
    {
        // Act
        var kernel = new Kernel();
        var testPluginsDir = Path.Combine(Directory.GetCurrentDirectory(), "OpenApi", "TestPlugins");
        var manifestFilePath = Path.Combine(testPluginsDir, "example-apimanifest-local.json");

        // Arrange
        var plugin = await kernel.ImportPluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(2, plugin.FunctionCount);
    }

    [Fact(Skip = SkipReason)]
    // Verify that functions are correctly imported
    public async Task VerifyPluginFunctionsFromApiManifestAsync()
    {
        // Act
        var kernel = new Kernel();
        var testPluginsDir = Path.Combine(Directory.GetCurrentDirectory(), "OpenApi", "TestPlugins");
        var manifestFilePath = Path.Combine(testPluginsDir, "example-apimanifest-local.json");

        // Arrange
        var plugin = await kernel.ImportPluginFromApiManifestAsync("ApiManifestPlugin", manifestFilePath);

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
