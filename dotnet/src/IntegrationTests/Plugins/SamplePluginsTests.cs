// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins;
public class SamplePluginsTests
{
    [Fact]
    public void CanLoadSamplePluginsRequestSettings()
    {
        // Arrange
        var kernel = new Kernel();

        // Act
        TestHelpers.ImportAllSamplePlugins(kernel);

        // Assert
        Assert.NotNull(kernel.Plugins);
        var metadata = kernel.Plugins.GetFunctionsMetadata();
        Assert.NotNull(metadata);
        Assert.Equal(48, metadata.Count); // currently we have 48 sample plugin functions
        metadata.ToList().ForEach(function =>
        {
            Assert.NotNull(kernel.Plugins.GetFunction(function.PluginName, function.Name));
        });
    }

    [Fact]
    // Including this to ensure backward compatibility as tools like Prompt Factory still use the old format
    public void CanLoadSampleSkillsCompletions()
    {
        // Arrange
        var kernel = new Kernel();

        // Act
        TestHelpers.ImportAllSampleSkills(kernel);

        // Assert
        Assert.NotNull(kernel.Plugins);
        var metadata = kernel.Plugins.GetFunctionsMetadata();
        Assert.NotNull(metadata);
        Assert.Equal(48, metadata.Count); // currently we have 48 sample plugin functions
        metadata.ToList().ForEach(function =>
        {
            Assert.NotNull(kernel.Plugins.GetFunction(function.PluginName, function.Name));
        });
    }
}
