// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Planning.UnitTests;

public class ReadOnlyFunctionCollectionExtensionsTests
{
    private static PlannerConfigBase InitializeConfig(Type t)
    {
        PlannerConfigBase? config = Activator.CreateInstance(t) as PlannerConfigBase;
        Assert.NotNull(config);
        return config;
    }

    private async IAsyncEnumerable<T> GetAsyncEnumerableAsync<T>(IEnumerable<T> results)
    {
        foreach (T result in results)
        {
            yield return await Task.FromResult(result);
        }
    }

    [Theory]
    [InlineData(typeof(ActionPlannerConfig))]
    [InlineData(typeof(SequentialPlannerConfig))]
    [InlineData(typeof(StepwisePlannerConfig))]
    public async Task CanCallGetAvailableFunctionsWithNoFunctionsAsync(Type t)
    {
        // Arrange
        var plugins = new KernelPluginCollection();
        var cancellationToken = default(CancellationToken);
        var kernel = new Kernel(new Mock<IServiceProvider>().Object, plugins);

        // Arrange Mock Memory and Result
        var memory = new Mock<ISemanticTextMemory>();
        var memoryQueryResult = new MemoryQueryResult(
            new MemoryRecordMetadata(
                isReference: false,
                id: "id",
                text: "text",
                description: "description",
                externalSourceName: "sourceName",
                additionalMetadata: "value"),
            relevance: 0.8,
            embedding: null);
        IAsyncEnumerable<MemoryQueryResult> asyncEnumerable = this.GetAsyncEnumerableAsync(new[] { memoryQueryResult });
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        var serviceProvider = new Mock<IServiceProvider>();
        var serviceSelector = new Mock<IAIServiceSelector>();

        // Arrange GetAvailableFunctionsAsync parameters
        var config = InitializeConfig(t);
        var semanticQuery = "test";

        // Act
        var result = await kernel.Plugins.GetAvailableFunctionsAsync(config, semanticQuery, null, cancellationToken);

        // Assert
        Assert.NotNull(result);
        memory.Verify(
            x => x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Never);

        config.SemanticMemoryConfig = new();

        // Act
        result = await kernel.Plugins.GetAvailableFunctionsAsync(config, semanticQuery, null, cancellationToken);

        // Assert
        Assert.NotNull(result);
        memory.Verify(
            x => x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Never);

        config.SemanticMemoryConfig = new() { Memory = memory.Object };

        // Act
        result = await kernel.Plugins.GetAvailableFunctionsAsync(config, semanticQuery, null, cancellationToken);

        // Assert
        Assert.NotNull(result);
        memory.Verify(
            x => x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Theory]
    [InlineData(typeof(ActionPlannerConfig))]
    [InlineData(typeof(SequentialPlannerConfig))]
    [InlineData(typeof(StepwisePlannerConfig))]
    public async Task CanCallGetAvailableFunctionsWithFunctionsAsync(Type t)
    {
        // Arrange
        var cancellationToken = default(CancellationToken);

        // Arrange Mock Memory and Result
        var plugins = new KernelPluginCollection()
        {
            new KernelPlugin("pluginName", new[]
            {
                KernelFunctionFactory.CreateFromMethod(() => { }, "functionName", "description"),
                KernelFunctionFactory.CreateFromMethod(() => { }, "nativeFunctionName", "description"),
            }),
        };
        var functionView = new KernelFunctionMetadata(plugins["pluginName"]["functionName"].Metadata) { PluginName = "pluginName" };
        var nativeFunctionView = new KernelFunctionMetadata(plugins["pluginName"]["nativeFunctionName"].Metadata) { PluginName = "pluginName" };

        var kernel = new Kernel(new Mock<IServiceProvider>().Object, plugins);

        var memoryQueryResult =
            new MemoryQueryResult(
                new MemoryRecordMetadata(
                    isReference: false,
                    id: functionView.ToFullyQualifiedName(),
                    text: "text",
                    description: "description",
                    externalSourceName: "sourceName",
                    additionalMetadata: "value"),
                relevance: 0.8,
                embedding: null);
        var asyncEnumerable = this.GetAsyncEnumerableAsync(new[] { memoryQueryResult });
        var memory = new Mock<ISemanticTextMemory>();
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        var serviceProvider = new Mock<IServiceProvider>();
        var serviceSelector = new Mock<IAIServiceSelector>();

        // Arrange GetAvailableFunctionsAsync parameters
        var config = InitializeConfig(t);
        var semanticQuery = "test";

        // Act
        var result = (await kernel.Plugins.GetAvailableFunctionsAsync(config, semanticQuery, null, cancellationToken)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Count);
        Assert.Equivalent(functionView, result[0]);

        // Arrange update IncludedFunctions
        config.SemanticMemoryConfig = new() { Memory = memory.Object };
        config.SemanticMemoryConfig.IncludedFunctions.UnionWith(new List<(string, string)> { ("pluginName", "nativeFunctionName") });

        // Act
        result = (await kernel.Plugins.GetAvailableFunctionsAsync(config, semanticQuery)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Count); // IncludedFunctions should be added to the result
        Assert.Equivalent(functionView, result[0]);
        Assert.Equivalent(nativeFunctionView, result[1]);
    }

    [Theory]
    [InlineData(typeof(ActionPlannerConfig))]
    [InlineData(typeof(SequentialPlannerConfig))]
    [InlineData(typeof(StepwisePlannerConfig))]
    public async Task CanCallGetAvailableFunctionsWithFunctionsWithRelevancyAsync(Type t)
    {
        // Arrange
        var cancellationToken = default(CancellationToken);

        // Arrange Mock Memory and Result
        var plugins = new KernelPluginCollection()
        {
            new KernelPlugin("pluginName", new[]
            {
                KernelFunctionFactory.CreateFromMethod(() => { }, "functionName", "description"),
                KernelFunctionFactory.CreateFromMethod(() => { }, "nativeFunctionName", "description"),
            }),
        };

        var kernel = new Kernel(new Mock<IServiceProvider>().Object, plugins);

        var functionView = new KernelFunctionMetadata(plugins["pluginName"]["functionName"].Metadata) { PluginName = "pluginName" };
        var nativeFunctionView = new KernelFunctionMetadata(plugins["pluginName"]["nativeFunctionName"].Metadata) { PluginName = "pluginName" };

        var memoryQueryResult =
            new MemoryQueryResult(
                new MemoryRecordMetadata(
                    isReference: false,
                    id: functionView.ToFullyQualifiedName(),
                    text: "text",
                    description: "description",
                    externalSourceName: "sourceName",
                    additionalMetadata: "value"),
                relevance: 0.8,
                embedding: null);
        var asyncEnumerable = this.GetAsyncEnumerableAsync(new[] { memoryQueryResult });
        var memory = new Mock<ISemanticTextMemory>();
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        var serviceProvider = new Mock<IServiceProvider>();
        var serviceSelector = new Mock<IAIServiceSelector>();

        // Arrange GetAvailableFunctionsAsync parameters
        var config = InitializeConfig(t);
        config.SemanticMemoryConfig = new() { RelevancyThreshold = 0.78, Memory = memory.Object };
        var semanticQuery = "test";

        // Act
        var result = (await kernel.Plugins.GetAvailableFunctionsAsync(config, semanticQuery, null, cancellationToken)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equivalent(functionView, result[0]);

        // Arrange update IncludedFunctions
        config.SemanticMemoryConfig.IncludedFunctions.UnionWith(new List<(string, string)> { ("pluginName", "nativeFunctionName") });

        // Act
        result = (await kernel.Plugins.GetAvailableFunctionsAsync(config, semanticQuery)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Count); // IncludedFunctions should be added to the result
        Assert.Equivalent(functionView, result[0]);
        Assert.Equivalent(nativeFunctionView, result[1]);
    }

    [Theory]
    [InlineData(typeof(ActionPlannerConfig))]
    [InlineData(typeof(SequentialPlannerConfig))]
    [InlineData(typeof(StepwisePlannerConfig))]
    public async Task CanCallGetAvailableFunctionsAsyncWithDefaultRelevancyAsync(Type t)
    {
        // Arrange
        var serviceProvider = new Mock<IServiceProvider>();
        var serviceSelector = new Mock<IAIServiceSelector>();

        var plugins = new KernelPluginCollection();
        var cancellationToken = default(CancellationToken);

        var kernel = new Kernel(new Mock<IServiceProvider>().Object, plugins);

        // Arrange Mock Memory and Result
        var memory = new Mock<ISemanticTextMemory>();
        var memoryQueryResult =
            new MemoryQueryResult(
                new MemoryRecordMetadata(
                    isReference: false,
                    id: "id",
                    text: "text",
                    description: "description",
                    externalSourceName: "sourceName",
                    additionalMetadata: "value"),
                relevance: 0.8,
                embedding: null);
        var asyncEnumerable = this.GetAsyncEnumerableAsync(new[] { memoryQueryResult });
        memory.Setup(x =>
                x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        // Arrange GetAvailableFunctionsAsync parameters
        var config = InitializeConfig(t);
        config.SemanticMemoryConfig = new() { RelevancyThreshold = 0.78, Memory = memory.Object };
        var semanticQuery = "test";

        // Act
        var result = await kernel.Plugins.GetAvailableFunctionsAsync(config, semanticQuery, null, cancellationToken);

        // Assert
        Assert.NotNull(result);
        memory.Verify(
            x => x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once);
    }
}
