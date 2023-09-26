// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planners.UnitTests.XunitHelpers;
using Moq;
using Xunit;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Planners.UnitTests;
#pragma warning restore IDE0130 // Namespace does not match folder structure

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
        var kernel = new Mock<IKernel>();

        var variables = new ContextVariables();
        var functions = new FunctionCollection();
        var cancellationToken = default(CancellationToken);

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

        var kernelContext = new Mock<IKernelExecutionContext>();
        kernelContext.SetupGet(x => x.Functions).Returns(functions);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(kernelContext.Object, variables);
        var config = InitializeConfig(t);
        var semanticQuery = "test";

        // Act
        var result = await context.Functions.GetAvailableFunctionsAsync(config, semanticQuery, null, cancellationToken);

        // Assert
        Assert.NotNull(result);
        memory.Verify(
            x => x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Never);

        config.SemanticMemoryConfig = new();

        // Act
        result = await context.Functions.GetAvailableFunctionsAsync(config, semanticQuery, null, cancellationToken);

        // Assert
        Assert.NotNull(result);
        memory.Verify(
            x => x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Never);

        config.SemanticMemoryConfig = new() { Memory = memory.Object };

        // Act
        result = await context.Functions.GetAvailableFunctionsAsync(config, semanticQuery, null, cancellationToken);

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
        var kernel = new Mock<IKernel>();
        var variables = new ContextVariables();
        var cancellationToken = default(CancellationToken);

        // Arrange FunctionView
        var functionMock = new Mock<ISKFunction>();
        var functionView = new FunctionView("functionName", "pluginName", "description");
        var nativeFunctionView = new FunctionView("nativeFunctionName", "pluginName", "description");
        var functionsView = new List<FunctionView>() { functionView, nativeFunctionView };

        // Arrange Mock Memory and Result
        var functions = new Mock<IFunctionCollection>();
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

        functions.Setup(x => x.TryGetFunction(It.IsAny<string>(), It.IsAny<string>(), out It.Ref<ISKFunction?>.IsAny)).Returns(true);
        functions.Setup(x => x.GetFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(functionMock.Object);
        functions.Setup(x => x.GetFunctionViews()).Returns(functionsView);

        var kernelContext = new Mock<IKernelExecutionContext>();
        kernelContext.SetupGet(x => x.Functions).Returns(functions.Object);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(kernelContext.Object, variables);
        var config = InitializeConfig(t);
        var semanticQuery = "test";

        // Act
        var result = (await context.Functions.GetAvailableFunctionsAsync(config, semanticQuery, null, cancellationToken)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Count);
        Assert.Equal(functionView, result[0]);

        // Arrange update IncludedFunctions
        config.SemanticMemoryConfig = new() { Memory = memory.Object };
        config.SemanticMemoryConfig.IncludedFunctions.UnionWith(new List<(string, string)> { ("pluginName", "nativeFunctionName") });

        // Act
        result = (await context.Functions.GetAvailableFunctionsAsync(config, semanticQuery)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Count); // IncludedFunctions should be added to the result
        Assert.Equal(functionView, result[0]);
        Assert.Equal(nativeFunctionView, result[1]);
    }

    [Theory]
    [InlineData(typeof(ActionPlannerConfig))]
    [InlineData(typeof(SequentialPlannerConfig))]
    [InlineData(typeof(StepwisePlannerConfig))]
    public async Task CanCallGetAvailableFunctionsWithFunctionsWithRelevancyAsync(Type t)
    {
        // Arrange
        var kernel = new Mock<IKernel>();

        var variables = new ContextVariables();
        var cancellationToken = default(CancellationToken);

        // Arrange FunctionView
        var functionMock = new Mock<ISKFunction>();
        var functionView = new FunctionView("functionName", "pluginName", "description");
        var nativeFunctionView = new FunctionView("nativeFunctionName", "pluginName", "description");
        var functionsView = new List<FunctionView>() { functionView, nativeFunctionView };

        // Arrange Mock Memory and Result
        var functions = new Mock<IFunctionCollection>();
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

        functions.Setup(x => x.TryGetFunction(It.IsAny<string>(), It.IsAny<string>(), out It.Ref<ISKFunction?>.IsAny)).Returns(true);
        functions.Setup(x => x.GetFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(functionMock.Object);
        functions.Setup(x => x.GetFunctionViews()).Returns(functionsView);

        var kernelContext = new Mock<IKernelExecutionContext>();
        kernelContext.SetupGet(k => k.LoggerFactory).Returns(TestConsoleLogger.LoggerFactory);
        kernelContext.SetupGet(x => x.Functions).Returns(functions.Object);

        // Arrange GetAvailableFunctionsAsync parameters
        var context = new SKContext(kernelContext.Object, variables);
        var config = InitializeConfig(t);
        config.SemanticMemoryConfig = new() { RelevancyThreshold = 0.78, Memory = memory.Object };
        var semanticQuery = "test";

        // Act
        var result = (await context.Functions.GetAvailableFunctionsAsync(config, semanticQuery, null, cancellationToken)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(functionView, result[0]);

        // Arrange update IncludedFunctions
        config.SemanticMemoryConfig.IncludedFunctions.UnionWith(new List<(string, string)> { ("pluginName", "nativeFunctionName") });

        // Act
        result = (await context.Functions.GetAvailableFunctionsAsync(config, semanticQuery)).ToList();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Count); // IncludedFunctions should be added to the result
        Assert.Equal(functionView, result[0]);
        Assert.Equal(nativeFunctionView, result[1]);
    }

    [Theory]
    [InlineData(typeof(ActionPlannerConfig))]
    [InlineData(typeof(SequentialPlannerConfig))]
    [InlineData(typeof(StepwisePlannerConfig))]
    public async Task CanCallGetAvailableFunctionsAsyncWithDefaultRelevancyAsync(Type t)
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var kernelContext = new Mock<IKernelExecutionContext>();

        var variables = new ContextVariables();
        var functions = new FunctionCollection();
        var cancellationToken = default(CancellationToken);

        kernelContext.SetupGet(x => x.Functions).Returns(functions);

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
        var context = new SKContext(kernelContext.Object, variables);
        var config = InitializeConfig(t);
        config.SemanticMemoryConfig = new() { RelevancyThreshold = 0.78, Memory = memory.Object };
        var semanticQuery = "test";

        // Act
        var result = await context.Functions.GetAvailableFunctionsAsync(config, semanticQuery, null, cancellationToken);

        // Assert
        Assert.NotNull(result);
        memory.Verify(
            x => x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once);
    }
}
