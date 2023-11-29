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
        var pluginsMetadata = kernel.Plugins.GetPluginsMetadata();
        Assert.NotNull(pluginsMetadata);
        Assert.Equal(11, pluginsMetadata.Count); // currently we have 11 sample plugins
        pluginsMetadata.ToList().ForEach(pluginMetadata =>
        {
            pluginMetadata.FunctionsMetadata.ToList().ForEach(functionMetadata =>
            {
                Assert.NotNull(kernel.Plugins.GetFunction(pluginMetadata.Name, functionMetadata.Name));
            });
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
        var pluginsMetadata = kernel.Plugins.GetPluginsMetadata();
        Assert.NotNull(pluginsMetadata);
        Assert.Equal(11, pluginsMetadata.Count); // currently we have 11 sample plugins
        pluginsMetadata.ToList().ForEach(pluginMetadata =>
        {
            pluginMetadata.FunctionsMetadata.ToList().ForEach(functionMetadata =>
            {
                Assert.NotNull(kernel.Plugins.GetFunction(pluginMetadata.Name, functionMetadata.Name));
            });
        });
    }
}
