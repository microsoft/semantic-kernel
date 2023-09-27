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
        var kernel = new KernelBuilder().Build();

        // Act
        TestHelpers.ImportAllSamplePlugins(kernel);

        // Assert
        Assert.NotNull(kernel.Functions);
        var functionViews = kernel.Functions.GetFunctionViews();
        Assert.NotNull(functionViews);
        Assert.Equal(48, functionViews.Count); // currently we have 48 sample plugin functions
        functionViews.ToList().ForEach(view =>
        {
            var function = kernel.Functions.GetFunction(view.PluginName, view.Name);
            Assert.NotNull(function);
            Assert.NotNull(function.RequestSettings);
            Assert.True(function.RequestSettings.ExtensionData.ContainsKey("max_tokens"));
        });
    }

    [Fact]
    // Including this to ensure backward compatability as tools like Prompt Factory still use the old format
    public void CanLoadSampleSkillsCompletions()
    {
        // Arrange
        var kernel = new KernelBuilder().Build();

        // Act
        TestHelpers.ImportAllSampleSkills(kernel);

        // Assert
        Assert.NotNull(kernel.Functions);
        var functionViews = kernel.Functions.GetFunctionViews();
        Assert.NotNull(functionViews);
        Assert.Equal(48, functionViews.Count); // currently we have 48 sample plugin functions
        functionViews.ToList().ForEach(view =>
        {
            var function = kernel.Functions.GetFunction(view.PluginName, view.Name);
            Assert.NotNull(function);
            Assert.NotNull(function.RequestSettings);
            Assert.True(function.RequestSettings.ExtensionData.ContainsKey("max_tokens"));
        });
    }
}
